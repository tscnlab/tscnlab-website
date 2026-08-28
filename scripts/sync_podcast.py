import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.tscnlab.org"
URL = BASE + "/podcast"

OUT = Path("_data/podcast.json")
IMAGE_DIR = Path("assets/images/podcast")

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


def fetch(url):
    response = session.get(url, timeout=40)
    response.raise_for_status()
    return response


def clean_text(element):
    if not element:
        return ""

    return " ".join(
        element.get_text(" ", strip=True).split()
    )


def image_src(img):
    if not img:
        return None

    return (
        img.get("data-src")
        or img.get("data-image")
        or img.get("src")
    )


def slugify(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def download_image(src, filename_base):
    if not src:
        return None

    url = urljoin(BASE, src)

    suffix = Path(
        urlparse(url).path
    ).suffix.lower()

    if suffix not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }:
        suffix = ".jpg"

    filename = filename_base + suffix
    target = IMAGE_DIR / filename

    if not target.exists():
        print("Downloading:", url)
        target.write_bytes(
            fetch(url).content
        )

    return "/assets/images/podcast/" + filename


html = fetch(URL).text
soup = BeautifulSoup(html, "html.parser")

main = soup.find("main") or soup.body


# --------------------------------------------------
# Platform links
# --------------------------------------------------

platforms = []

platform_domains = {
    "open.spotify.com": "Spotify",
    "podcasts.apple.com": "Apple Podcasts",
    "podcast.de": "podcast.de",
    "wissenschaftspodcasts.de": "Wissenschaftspodcasts",
}

for link in main.find_all("a", href=True):
    href = link["href"]

    for domain, name in platform_domains.items():
        if domain in href:
            if not any(
                p["url"] == href
                for p in platforms
            ):
                platforms.append({
                    "name": name,
                    "url": href,
                })


# --------------------------------------------------
# Platform logos
# --------------------------------------------------

platform_logo_patterns = {
    "spotify": "Spotify",
    "apple": "Apple Podcasts",
    "podcast.de": "podcast.de",
    "wissenschaft": "Wissenschaftspodcasts",
}

platform_logos = {}

for img in main.find_all("img"):
    src = image_src(img)

    if not src:
        continue

    lower = src.lower()

    for pattern, name in platform_logo_patterns.items():
        if pattern in lower:
            local = download_image(
                src,
                "platform-" + slugify(name)
            )

            platform_logos[name] = local


for platform in platforms:
    platform["image"] = platform_logos.get(
        platform["name"]
    )



# Force known platform logo assets where Squarespace naming is ambiguous.
known_platform_logos = {
    "Wissenschaftspodcasts": (
        "https://images.squarespace-cdn.com/content/v1/"
        "63305b1689502f4882626e0f/"
        "f98b3bf0-5563-497e-a5ad-7c4fb64cae0f/"
        "logo-wisspod.png?format=100w"
    )
}

for platform in platforms:
    name = platform.get("name")

    if name in known_platform_logos:
        platform["image"] = download_image(
            known_platform_logos[name],
            "platform-" + slugify(name)
        )


# --------------------------------------------------
# Episode entries
# --------------------------------------------------

episodes = []
seen_urls = set()

for link in main.find_all("a", href=True):
    href = link["href"]

    absolute = urljoin(BASE, href)
    parsed = urlparse(absolute)

    if not parsed.path.startswith("/podcast/"):
        continue

    if parsed.path.rstrip("/") == "/podcast":
        continue

    if absolute in seen_urls:
        continue

    # Find a reasonably small ancestor containing both
    # episode title/link and corresponding image.
    container = None

    for parent in link.parents:
        if parent == main:
            break

        images = parent.find_all("img")

        if images:
            container = parent
            break

    title = clean_text(link)

    if not title or len(title) < 5:
        if container:
            title_candidates = container.find_all(
                ["h2", "h3", "h4", "p"]
            )

            for candidate in title_candidates:
                value = clean_text(candidate)

                if (
                    "Episode" in value
                    or "Spotlight" in value
                    or "Mini-Series" in value
                    or "Live episode" in value
                ):
                    title = value
                    break

    if not title:
        continue

    img = None

    if container:
        img = container.find("img")

    if not img:
        # fallback: nearest previous episode artwork
        img = link.find_previous("img")

    src = image_src(img)

    local_image = None

    if src:
        local_image = download_image(
            src,
            "episode-" + slugify(
                parsed.path.rstrip("/").split("/")[-1]
            )
        )

    episodes.append({
        "title": title,
        "url": absolute,
        "image": local_image,
        "source_image": src,
    })

    seen_urls.add(absolute)


# --------------------------------------------------
# Some Squarespace cards expose artwork/title without
# an internal episode link. Pick those up as well.
# --------------------------------------------------

known_titles = {
    e["title"]
    for e in episodes
}

episode_keywords = (
    "episode",
    "spotlight",
    "mini-series",
    "season",
)

for img in main.find_all("img"):
    src = image_src(img)

    if not src:
        continue

    alt = clean_text(img.get("alt")) if False else (img.get("alt") or "").strip()

    # Search nearby text if alt is empty.
    nearby = ""

    parent = img.parent

    if parent:
        for candidate in parent.find_all_next(
            ["h2", "h3", "h4", "p"],
            limit=4
        ):
            value = clean_text(candidate)

            if any(
                keyword in value.lower()
                for keyword in episode_keywords
            ):
                nearby = value
                break

    title = alt or nearby

    if not title:
        continue

    if not any(
        keyword in title.lower()
        for keyword in episode_keywords
    ):
        continue

    if title in known_titles:
        continue

    lower_src = src.lower()

    if any(x in lower_src for x in [
        "logo",
        "youtube",
        "tum.",
        "mpi",
    ]):
        continue

    local_image = download_image(
        src,
        "artwork-" + str(len(episodes) + 1).zfill(2)
    )

    link = img.find_parent("a", href=True)

    url = (
        urljoin(BASE, link["href"])
        if link
        else None
    )

    episodes.append({
        "title": title,
        "url": url,
        "image": local_image,
        "source_image": src,
    })

    known_titles.add(title)


# --------------------------------------------------
# Sort newest-looking seasons first.
# We preserve source order as much as possible.
# --------------------------------------------------



# --------------------------------------------------
# Episode groups
# --------------------------------------------------

def episode_group(title, source_image=""):
    value = (title or "").lower()
    image = (source_image or "").lower()

    if "interacting with daylight" in value:
        return "Interacting with Daylight"

    if (
        value.startswith("spotlight:")
        or value.startswith("live episode:")
    ):
        return "Spotlights & Live"

    # Prefer explicit season information in artwork filenames.
    for season in (4, 3, 2, 1):
        patterns = [
            f"s0{season}e",
            f"s{season}e",
            f"season-{season}",
            f"season{season}",
            f"season_{season}",
        ]

        if any(pattern in image for pattern in patterns):
            return f"Season {season}"

    return None


current_group = "Season 4"

for episode in episodes:
    title = episode.get("title", "")
    lower = title.lower()

    # Distinctive first episodes mark season boundaries on the source page.
    if "tick-tock trouble" in lower:
        current_group = "Season 3"

    elif lower.startswith("spotlight:") or lower.startswith("live episode:"):
        current_group = "Spotlights & Live"

    elif "cave studies and fruit flies" in lower:
        current_group = "Season 2"

    elif "light exposure" in lower and "why should we care" in lower:
        current_group = "Season 1"

    elif "interacting with daylight" in lower:
        current_group = "Interacting with Daylight"

    detected = episode_group(
        title,
        episode.get("source_image", "")
    )

    episode["group"] = detected or current_group


group_order = [
    "Season 4",
    "Season 3",
    "Spotlights & Live",
    "Season 2",
    "Season 1",
    "Interacting with Daylight",
]

episode_groups = []

for group_name in group_order:
    group_episodes = [
        episode
        for episode in episodes
        if episode.get("group") == group_name
    ]

    if group_episodes:
        episode_groups.append({
            "name": group_name,
            "episodes": group_episodes,
        })


# --------------------------------------------------
# Trailer audio
# --------------------------------------------------

trailers = []
seen_audio = set()

for audio in main.select(".sqs-audio-embed[data-asset-url]"):
    audio_url = audio.get("data-asset-url")
    title = audio.get("data-title") or ""

    if not audio_url or audio_url in seen_audio:
        continue

    if "Trailer" not in title:
        continue

    seen_audio.add(audio_url)

    match = re.search(r"Season\s+(\d+)", title, re.I)
    season = int(match.group(1)) if match else 0

    artwork = None

    # Find the nearest preceding season artwork.
    for img in audio.find_all_previous("img"):
        src = image_src(img)
        if not src:
            continue

        alt = (img.get("alt") or "").lower()
        lower_src = src.lower()

        if (
            f"season {season}" in alt
            or f"s0{season}" in lower_src
            or f"season-{season}" in lower_src
            or f"season{season}" in lower_src
        ):
            artwork = download_image(
                src,
                f"trailer-season-{season}"
            )
            break

    trailers.append({
        "season": season,
        "title": title,
        "audio": audio_url,
        "artwork": artwork,
    })

trailers.sort(
    key=lambda item: item["season"],
    reverse=True
)


# Keep Spotify first, matching the original site.
platform_order = {
    "Spotify": 0,
    "Apple Podcasts": 1,
    "podcast.de": 2,
    "Wissenschaftspodcasts": 3,
}

platforms.sort(
    key=lambda p: platform_order.get(p["name"], 99)
)


data = {
    "title": "Light O’Clock",
    "subtitle": "A podcast on light and your body clock",
    "tagline": (
        "We break down the science behind circadian rhythms "
        "so you can be enlightened."
    ),
    "description": (
        "In each podcast episode, we chat with experts in the field "
        "about a variety of topics, spanning from the effects of light "
        "on our biology and how it can be used for the treatment of "
        "psychiatric disorders and beyond."
    ),
    "platforms": platforms,
    "trailers": trailers,
    "episode_groups": episode_groups,
    "episodes": episodes,
}

OUT.write_text(
    json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print()
print("Podcast sync complete")
print("---------------------")
print("Platforms:", len(platforms))
print("Trailers:", len(trailers))
print("Episodes/cards:", len(episodes))
print("Groups:")
for group in episode_groups:
    print(f"  {group['name']}: {len(group['episodes'])}")
print("Written:", OUT)
