import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

BASE = "https://www.tscnlab.org"

PAGES = [
    {
        "url": f"{BASE}/research/research-areas",
        "output": Path("research/research-areas.html"),
        "permalink": "/research/research-areas/",
        "title": "Research areas",
        "slug": "research-areas",
    },
    {
        "url": f"{BASE}/research/preregistrations",
        "output": Path("research/preregistrations.html"),
        "permalink": "/research/preregistrations/",
        "title": "Preregistrations",
        "slug": "preregistrations",
    },
    {
        "url": f"{BASE}/collaborations",
        "output": Path("collaborations.html"),
        "permalink": "/collaborations/",
        "title": "Collaborations",
        "slug": "collaborations",
    },
    {
        "url": f"{BASE}/equipment-support",
        "output": Path("equipment-support.html"),
        "permalink": "/equipment-support/",
        "title": "Equipment support",
        "slug": "equipment-support",
    },
]

IMAGE_DIR = Path("assets/images/research")
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


def image_source(img):
    if not img:
        return None

    return (
        img.get("data-src")
        or img.get("data-image")
        or img.get("src")
    )


def is_global_asset(src):
    if not src:
        return True

    value = src.lower()

    return any(
        token in value
        for token in [
            "logo_with_text",
            "youtube.png",
            "mpi-kyb",
            "/tum.png",
        ]
    )


def download_image(src, page_slug, index):
    if not src:
        return None

    url = urljoin(BASE, src)

    suffix = Path(urlparse(url).path).suffix.lower()

    if suffix not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
    }:
        suffix = ".jpg"

    filename = f"{page_slug}-{index:02d}{suffix}"
    target = IMAGE_DIR / filename

    if not target.exists():
        target.write_bytes(fetch(url).content)

    return f"/assets/images/research/{filename}"


def main_content(soup):
    candidates = [
        soup.select_one("main"),
        soup.select_one(".Main-content"),
        soup.select_one("#page"),
        soup.body,
    ]

    return next(
        (candidate for candidate in candidates if candidate),
        None
    )


def should_skip(element):
    if element.find_parent(["header", "footer", "nav"]):
        return True

    classes = " ".join(element.get("class", []))

    blocked_classes = [
        "header",
        "footer",
        "navigation",
        "mobile-menu",
        "blog-meta",
    ]

    if any(value in classes.lower() for value in blocked_classes):
        return True

    text = clean_text(element)

    if text in {
        "Back to top",
        "Imprint",
        "Data Privacy Policy",
        "Open Menu",
        "Close Menu",
    }:
        return True

    return False


def render_inline_links(element):
    for a in element.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        label = clean_text(a)

        replacement = soup.new_tag("a", href=href)
        replacement.string = label
        a.replace_with(replacement)

    return str(element)


def extract_blocks(soup, page_slug):
    root = main_content(soup)

    if not root:
        return []

    blocks = []
    seen_images = set()
    image_index = 1

    for element in root.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "p",
            "ul",
            "ol",
            "blockquote",
            "img",
        ],
        recursive=True,
    ):
        if should_skip(element):
            continue

        if element.name == "img":
            src = image_source(element)

            if not src or is_global_asset(src):
                continue

            canonical = urljoin(BASE, src).split("?")[0]

            if canonical in seen_images:
                continue

            seen_images.add(canonical)

            local = download_image(
                src,
                page_slug,
                image_index,
            )

            if local:
                blocks.append(
                    f'''<figure class="research-page-image">
  <img src="{{{{ '{local}' | relative_url }}}}" alt="{element.get("alt", "")}">
</figure>'''
                )

                image_index += 1

            continue

        if element.find_parent(
            ["h1", "h2", "h3", "h4", "p", "ul", "ol", "blockquote"]
        ):
            continue

        value = clean_text(element)

        if not value:
            continue

        if value.startswith("Research >"):
            continue

        if element.name == "h1":
            # Page title is rendered by our layout.
            continue

        if element.name in {"h2", "h3", "h4"}:
            blocks.append(
                f"<{element.name}>{value}</{element.name}>"
            )

        elif element.name == "blockquote":
            blocks.append(
                f"<blockquote>{element.decode_contents()}</blockquote>"
            )

        elif element.name in {"ul", "ol"}:
            blocks.append(str(element))

        else:
            blocks.append(
                f"<p>{element.decode_contents()}</p>"
            )

    return blocks


for page in PAGES:
    print(f"Migrating {page['url']}")

    try:
        response = fetch(page["url"])
    except Exception as exc:
        print(f"  FAILED: {exc}")
        continue

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    blocks = extract_blocks(
        soup,
        page["slug"],
    )

    page["output"].parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output = f"""---
layout: research-page
title: "{page['title']}"
permalink: {page['permalink']}
---

""" + "\n\n".join(blocks) + "\n"

    page["output"].write_text(
        output,
        encoding="utf-8",
    )

    print(
        f"  created {page['output']} "
        f"({len(blocks)} blocks)"
    )
