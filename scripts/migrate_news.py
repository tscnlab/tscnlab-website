import json
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.tscnlab.org"
FIRST_PAGE = f"{BASE}/news"

RAW_DIR = Path("data/news-raw")
IMAGE_DIR = Path("assets/images/news")

RAW_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


def fetch(url):
    response = session.get(url, timeout=40)
    response.raise_for_status()
    return response


def soup_for(url):
    return BeautifulSoup(fetch(url).text, "html.parser")


def clean_text(element):
    if not element:
        return ""

    return " ".join(
        element.get_text(" ", strip=True).split()
    )


def slugify(value):
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)

    return value.strip("-")


def image_source(image):
    if not image:
        return None

    return (
        image.get("data-src")
        or image.get("data-image")
        or image.get("src")
    )


def download_image(src, slug, kind, index=1):
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
        ".gif",
    }:
        suffix = ".jpg"

    filename = f"{slug}-{kind}-{index:02d}{suffix}"
    target = IMAGE_DIR / filename

    if not target.exists():
        print(f"    downloading {kind}: {url}")
        target.write_bytes(fetch(url).content)

    return f"/assets/images/news/{filename}"


def normalize_date(value):
    match = re.search(
        r"(\d{1,2})/(\d{1,2})/(\d{2})",
        value or ""
    )

    if not match:
        return None

    month = int(match.group(1))
    day = int(match.group(2))
    year = 2000 + int(match.group(3))

    return f"{year:04d}-{month:02d}-{day:02d}"


def older_posts_url(soup):
    for link in soup.find_all("a", href=True):
        if clean_text(link).lower() == "older posts":
            return urljoin(BASE, link["href"])

    return None


def extract_listing_entries(soup):
    entries = []

    for article in soup.select("article.blog-item"):
        title_link = article.select_one(
            ".blog-title a[href^='/news/']"
        )

        if not title_link:
            continue

        article_url = urljoin(
            BASE,
            title_link["href"]
        )

        title = clean_text(title_link)

        date_element = article.select_one(
            ".blog-meta-primary .blog-date"
        )

        date = normalize_date(
            clean_text(date_element)
        )

        author_element = article.select_one(
            ".blog-meta-primary .blog-author"
        )

        author = clean_text(author_element)

        excerpt_element = article.select_one(
            ".blog-excerpt"
        )

        excerpt = clean_text(excerpt_element)

        image_element = article.select_one(
            ".blog-image-wrapper img"
        )

        featured_remote = image_source(
            image_element
        )

        entries.append({
            "url": article_url,
            "title": title,
            "date": date,
            "author": author,
            "excerpt": excerpt,
            "featured_remote": featured_remote,
        })

    return entries


def crawl_archive():
    current_url = FIRST_PAGE
    visited = set()
    posts = {}

    page_number = 1

    while (
        current_url
        and current_url not in visited
    ):
        print()
        print(
            f"Archive page {page_number}: "
            f"{current_url}"
        )

        visited.add(current_url)

        soup = soup_for(current_url)

        entries = extract_listing_entries(
            soup
        )

        print(
            f"  found {len(entries)} posts"
        )

        for entry in entries:
            posts[entry["url"]] = entry

        current_url = older_posts_url(soup)
        page_number += 1

        time.sleep(0.15)

    return list(posts.values())


def article_author(soup):
    for node in soup.find_all(
        string=re.compile(r"Written By", re.I)
    ):
        parent = node.parent

        if not parent:
            continue

        link = parent.find("a")

        if link:
            value = clean_text(link)

            if value:
                return value

        next_link = parent.find_next("a")

        if next_link:
            value = clean_text(next_link)

            if value and len(value) < 100:
                return value

    return ""


def article_root(soup):
    return (
        soup.find("article")
        or soup.find("main")
        or soup.body
    )


def is_global_image(src):
    if not src:
        return True

    value = src.lower()

    return any(
        blocked in value
        for blocked in [
            "logo_with_text",
            "youtube.png",
            "mpi-kyb",
            "/tum.png",
        ]
    )


def extract_article_content(root, slug):
    if not root:
        return []

    blocks = []
    seen_images = set()
    image_index = 1

    elements = root.find_all(
        [
            "p",
            "h2",
            "h3",
            "blockquote",
            "ul",
            "ol",
            "img",
        ],
        recursive=True,
    )

    for element in elements:
        if element.find_parent(
            ["header", "footer", "nav"]
        ):
            continue

        if element.name == "img":
            src = image_source(element)

            if not src or is_global_image(src):
                continue

            canonical = urljoin(
                BASE,
                src
            ).split("?")[0]

            if canonical in seen_images:
                continue

            seen_images.add(canonical)

            local = download_image(
                src,
                slug,
                "inline",
                image_index,
            )

            if local:
                blocks.append({
                    "type": "image",
                    "src": local,
                    "remote_src": src,
                    "alt": element.get("alt", ""),
                })

                image_index += 1

            continue

        if element.find_parent([
            "p",
            "h2",
            "h3",
            "blockquote",
            "ul",
            "ol",
        ]):
            continue

        value = clean_text(element)

        if not value:
            continue

        if value.startswith("Written By"):
            continue

        if value in {
            "Previous",
            "Next",
            "Back to top",
            "Imprint",
            "Data Privacy Policy",
        }:
            continue

        blocks.append({
            "type": element.name,
            "text": value,
        })

    return blocks


listing_entries = crawl_archive()

print()
print("=" * 60)
print(
    f"Found {len(listing_entries)} "
    "unique news posts"
)
print("=" * 60)

articles = []

for index, listing in enumerate(
    listing_entries,
    start=1,
):
    url = listing["url"]

    print()
    print(
        f"[{index}/{len(listing_entries)}] "
        f"{url}"
    )

    slug = slugify(
        urlparse(url)
        .path
        .rstrip("/")
        .split("/")[-1]
    )

    soup = soup_for(url)

    title_element = soup.find("h1")

    title = (
        clean_text(title_element)
        or listing["title"]
    )

    featured_remote = listing.get(
        "featured_remote"
    )

    featured_image = None

    if featured_remote:
        featured_image = download_image(
            featured_remote,
            slug,
            "featured",
            1,
        )

    content = extract_article_content(
        article_root(soup),
        slug,
    )

    author = (
        article_author(soup)
        or listing.get("author", "")
    )

    article = {
        "title": title,
        "slug": slug,
        "source_url": url,
        "date": listing.get("date"),
        "author": author,
        "excerpt": listing.get(
            "excerpt",
            ""
        ),
        "featured_image": featured_image,
        "featured_remote": featured_remote,
        "content": content,
    }

    output_path = (
        RAW_DIR / f"{slug}.json"
    )

    output_path.write_text(
        json.dumps(
            article,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    articles.append(article)

    inline_images = sum(
        1
        for block in content
        if block["type"] == "image"
    )

    print(
        "  featured:",
        featured_remote or "NONE"
    )

    print(
        "  inline images:",
        inline_images
    )

    time.sleep(0.15)


(RAW_DIR / "index.json").write_text(
    json.dumps(
        articles,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print()
print("Migration complete.")
print(f"Articles: {len(articles)}")

print(
    "Featured images:",
    sum(
        bool(article["featured_image"])
        for article in articles
    )
)
