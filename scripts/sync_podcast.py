import argparse
import html
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from base64 import b64encode
from collections import defaultdict
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import unquote, urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_data/podcast_episodes.json"
FEED = "https://tscnunit.podcaster.eu/lightoclock.rss"
APPLE = "https://itunes.apple.com/lookup?" + urlencode(
    {"id": "1732012771", "country": "us", "entity": "podcastEpisode", "limit": 100}
)
SPOTIFY = "https://api.spotify.com/v1/shows/6ahsTtsDAMjDyArgcQQ2hm/episodes?market=DE&limit=50"


def fetch(url, headers=None, data=None):
    with urlopen(Request(url, headers=headers or {}, data=data), timeout=30) as response:
        return response.read()


def spotify_episodes():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Spotify credentials unavailable. Keeping saved Spotify links.", file=sys.stderr)
        return []

    credentials = b64encode(f"{client_id}:{client_secret}".encode()).decode()
    token = json.loads(fetch(
        "https://accounts.spotify.com/api/token",
        {"Authorization": f"Basic {credentials}"},
        b"grant_type=client_credentials",
    ))["access_token"]
    episodes = []
    url = SPOTIFY
    while url:
        page = json.loads(fetch(url, {"Authorization": f"Bearer {token}"}))
        episodes.extend(page["items"])
        url = page["next"]
    return episodes


def optional_catalog(name, load):
    try:
        return load()
    except (URLError, TimeoutError, ValueError, KeyError) as error:
        print(f"{name} lookup failed: {error}. Keeping saved links.", file=sys.stderr)
        return []


def title_key(title):
    title = unicodedata.normalize("NFKC", html.unescape(title)).casefold()
    return "".join(character for character in title if character.isalnum())


def audio_key(url):
    parts = urlsplit(url)
    return parts.hostname, unquote(parts.path)


def unique_links(rows):
    links = defaultdict(set)
    for key, url in rows:
        if url:
            links[key].add(url)
    return {key: next(iter(urls)) for key, urls in links.items() if len(urls) == 1}


def group_for(title, season):
    if title.casefold().startswith("interacting with daylight mini-series"):
        return "Interacting with Daylight"
    if season:
        return f"Season {int(season)}"
    return "Spotlights & Live"


def build_catalog(feed, apple, spotify, previous):
    apple_links = unique_links(
        (audio_key(item["episodeUrl"]), item.get("trackViewUrl"))
        for item in apple if item.get("episodeUrl")
    )
    spotify_links = unique_links(
        ((title_key(item["name"]), item["release_date"]), item.get("external_urls", {}).get("spotify"))
        for item in spotify if item.get("name") and item.get("release_date")
    )
    saved = {
        entry["id"]: entry
        for entry in previous.get("trailers", []) + [
            entry for group in previous.get("episode_groups", []) for entry in group["episodes"]
        ]
    }
    groups = defaultdict(list)
    trailers = []
    seen = set()
    items = ET.fromstring(feed).findall("./channel/item")
    if not items:
        raise ValueError("The podcast feed contains no episodes.")

    for item in items:
        episode_id = item.findtext("guid", "").strip()
        title = html.unescape(item.findtext("title", "")).strip()
        audio = item.find("enclosure").get("url") if item.find("enclosure") is not None else None
        if not episode_id or episode_id in seen or not title or not audio:
            raise ValueError(f"Invalid or duplicate feed entry: {title or episode_id}")
        seen.add(episode_id)

        date = parsedate_to_datetime(item.findtext("pubDate")).date().isoformat()
        image = item.find("{*}image")
        season = item.findtext("{*}season")
        saved_links = saved.get(episode_id, {})
        entry = {
            "id": episode_id,
            "title": title,
            "date": date,
            "image": image.get("href") if image is not None else None,
            "audio": audio,
            "spotify": spotify_links.get((title_key(title), date)) or saved_links.get("spotify"),
            "apple": apple_links.get(audio_key(audio)) or saved_links.get("apple"),
        }
        if item.findtext("{*}episodeType") == "trailer":
            trailers.append(entry)
        else:
            group = group_for(title, season)
            if season:
                entry["title"] = re.sub(r"^Season \d+\s*[–—-]\s*", "", title, flags=re.IGNORECASE)
            groups[group].append(entry)

    seasons = sorted(
        (group for group in groups if group.startswith("Season ")),
        key=lambda group: int(group.split()[1]),
        reverse=True,
    )
    order = seasons + ["Spotlights & Live", "Interacting with Daylight"]
    return {
        "trailers": sorted(trailers, key=lambda entry: entry["date"], reverse=True),
        "episode_groups": [
            {"name": group, "episodes": sorted(groups[group], key=lambda entry: entry["date"])}
            for group in order if groups[group]
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed", type=Path)
    parser.add_argument("--apple", type=Path)
    parser.add_argument("--spotify", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    feed = args.feed.read_bytes() if args.feed else fetch(FEED)
    apple = json.loads(args.apple.read_bytes())["results"] if args.apple else optional_catalog(
        "Apple Podcasts", lambda: json.loads(fetch(APPLE))["results"]
    )
    spotify = json.loads(args.spotify.read_bytes())["items"] if args.spotify else optional_catalog(
        "Spotify", spotify_episodes
    )
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    catalog = build_catalog(feed, apple, spotify, previous)
    entries = catalog["trailers"] + [
        entry for group in catalog["episode_groups"] for entry in group["episodes"]
    ]
    for platform in ("spotify", "apple"):
        missing = [entry["title"] for entry in entries if not entry[platform]]
        if missing:
            print(f"Missing {platform} links: {', '.join(missing)}", file=sys.stderr)
    print(f"{len(entries)} entries, including {len(catalog['trailers'])} trailers")
    if not args.dry_run:
        temporary = OUTPUT.with_suffix(".tmp")
        temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(OUTPUT)


if __name__ == "__main__":
    main()
