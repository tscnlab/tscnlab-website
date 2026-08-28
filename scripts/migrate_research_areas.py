from pathlib import Path
from urllib.parse import urljoin, urlparse
import html as html_lib

import requests
from bs4 import BeautifulSoup

BASE = "https://www.tscnlab.org"
URL = f"{BASE}/research/research-areas"

OUT = Path("research/research-areas.html")
IMG_DIR = Path("assets/images/research-areas")
IMG_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def fetch(url):
    response = session.get(url, timeout=40)
    response.raise_for_status()
    return response


def clean_text(element):
    if not element:
        return ""
    return " ".join(element.get_text(" ", strip=True).split())


def get_image_src(img):
    if not img:
        return None

    return (
        img.get("data-src")
        or img.get("data-image")
        or img.get("src")
    )


def download_image(src, name):
    if not src:
        return None

    url = urljoin(BASE, src)
    suffix = Path(urlparse(url).path).suffix.lower()

    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"

    filename = f"{name}{suffix}"
    target = IMG_DIR / filename

    if not target.exists():
        print(f"Downloading {filename}")
        target.write_bytes(fetch(url).content)

    return f"/assets/images/research-areas/{filename}"


def escape(value):
    return html_lib.escape(value or "", quote=True)


soup = BeautifulSoup(fetch(URL).text, "html.parser")
main = soup.find("main") or soup.body


# --------------------------------------------------
# Research areas
# --------------------------------------------------

area_titles = [
    "Mechanisms underlying photoreception",
    "Circadian modulation of vision",
    "Natural scene statistics",
    "Meta-science and reproducibility",
    "Circadian and sleep data science",
    "Optimising light exposure, circadian and sleep health",
]

areas = []

for index, expected_title in enumerate(area_titles, start=1):
    heading = None

    for candidate in main.find_all(["h1", "h2", "h3", "h4", "p"]):
        if clean_text(candidate) == expected_title:
            heading = candidate
            break

    if not heading:
        print(f"WARNING: area not found: {expected_title}")
        continue

    question = ""

    for candidate in heading.find_all_next(["p", "h1", "h2", "h3", "h4"]):
        candidate_text = clean_text(candidate)

        if not candidate_text:
            continue

        if candidate_text in area_titles:
            break

        if candidate.name == "p":
            question = candidate_text
            break

    img = heading.find_previous("img")
    src = get_image_src(img)

    local_image = download_image(
        src,
        f"area-{index:02d}"
    )

    areas.append({
        "title": expected_title,
        "question": question,
        "image": local_image,
    })


# --------------------------------------------------
# Research facilities
# --------------------------------------------------

facility_text = (
    "At the Cyberneum at the Max Planck Institute for "
    "Biological Cybernetics, we have experimental facilities "
    "for evening and circadian studies for running three "
    "participants in parallel."
)

facility_image = None

facility_heading = None

for candidate in main.find_all(["h1", "h2", "h3", "h4", "p"]):
    if clean_text(candidate) == "Research facilities":
        facility_heading = candidate
        break

if facility_heading:
    image_candidate = facility_heading.find_next("img")

    if image_candidate:
        facility_image = download_image(
            get_image_src(image_candidate),
            "research-facilities"
        )


# --------------------------------------------------
# Research showcase
# --------------------------------------------------

showcase_image = None
showcase_url = None

showcase_heading = None

for candidate in main.find_all(["h1", "h2", "h3", "h4", "p"]):
    if clean_text(candidate) == "Research showcase":
        showcase_heading = candidate
        break

if showcase_heading:
    link = showcase_heading.find_next("a", href=True)

    if link:
        showcase_url = urljoin(BASE, link.get("href"))

        img = link.find("img")

        if not img:
            img = link.find_next("img")

        if img:
            showcase_image = download_image(
                get_image_src(img),
                "research-showcase"
            )


# --------------------------------------------------
# Funding images
# --------------------------------------------------

funding_images = []

funding_heading = None

for candidate in main.find_all(["h1", "h2", "h3", "h4", "p"]):
    if clean_text(candidate) == "Funding":
        funding_heading = candidate
        break

if funding_heading:
    seen = set()

    for img in funding_heading.find_all_next("img"):
        if img.find_parent("footer"):
            break

        src = get_image_src(img)

        if not src:
            continue

        canonical = src.split("?")[0]

        if canonical in seen:
            continue

        seen.add(canonical)

        local = download_image(
            src,
            f"funding-{len(funding_images) + 1:02d}"
        )

        if local:
            funding_images.append(local)

        if len(funding_images) >= 3:
            break


# --------------------------------------------------
# Build HTML
# --------------------------------------------------

parts = []

parts.append("""---
layout: default
title: Research areas
permalink: /research/research-areas/
---

<div id="top"></div>

<main class="research-areas-page shell">

  <p class="research-breadcrumb">
    Research &gt; <span>Research areas</span>
  </p>

  <h1>Research areas</h1>

  <section class="research-area-grid">
""")


for area in areas:
    image_html = ""

    if area["image"]:
        image_html = (
            '<img src="{{ \''
            + area["image"]
            + '\' | relative_url }}" alt="'
            + escape(area["title"])
            + '">'
        )

    parts.append(
        """
    <article class="research-area-card">
      {image}
      <h2>{title}</h2>
      <div class="research-area-rule"></div>
      <p>{question}</p>
    </article>
""".format(
            image=image_html,
            title=escape(area["title"]),
            question=escape(area["question"]),
        )
    )


parts.append("""
  </section>

  <section class="research-details-grid">
""")


facility_image_html = ""

if facility_image:
    facility_image_html = (
        '<img src="{{ \''
        + facility_image
        + '\' | relative_url }}" '
        + 'alt="Research facilities">'
    )


parts.append(
    """
    <article class="research-detail-card">
      <h2>Research facilities</h2>

      {image}

      <p>{text}</p>
    </article>
""".format(
        image=facility_image_html,
        text=escape(facility_text),
    )
)


parts.append("""
    <article class="research-detail-card">
      <h2>Equipment</h2>

      <p>To support our research, we use the following equipment:</p>

      <ul class="equipment-list">
        <li>Light measurements</li>
        <li>Sleep-wake characterisation</li>
        <li>Physiological measurements</li>
        <li>EEG</li>
        <li>Stimulus presentation</li>
      </ul>
    </article>
""")


parts.append("""
    <article class="research-detail-card">
      <h2>Research showcase</h2>
""")


if showcase_image:
    showcase_img_html = (
        '<img src="{{ \''
        + showcase_image
        + '\' | relative_url }}" '
        + 'alt="Research showcase">'
    )

    if showcase_url:
        parts.append(
            '<a href="'
            + escape(showcase_url)
            + '">'
            + showcase_img_html
            + '</a>'
        )
    else:
        parts.append(showcase_img_html)


parts.append("""
    </article>

    <article class="research-detail-card">
      <h2>Funding</h2>

      <div class="funding-logos">
""")


for image in funding_images:
    parts.append(
        '<img src="{{ \''
        + image
        + '\' | relative_url }}" alt="">'
    )


parts.append("""
      </div>
    </article>

  </section>

</main>
""")


OUT.write_text(
    "".join(parts),
    encoding="utf-8"
)


print()
print("Migration complete")
print("------------------")
print(f"Research areas: {len(areas)}")
print(f"Facility image: {'yes' if facility_image else 'no'}")
print(f"Showcase image: {'yes' if showcase_image else 'no'}")
print(f"Funding images: {len(funding_images)}")
print(f"Written to: {OUT}")
