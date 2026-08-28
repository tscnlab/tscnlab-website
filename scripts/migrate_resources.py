import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE = "https://www.tscnlab.org"

URL_2025 = f"{BASE}/seminar"
URL_2024 = f"{BASE}/seminar-20244"
URL_TALKS = f"{BASE}/resources/recorded-talks"

OUT = Path("_data/resources.json")
IMAGE_DIR = Path("assets/images/resources")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; TSCN migration)"
})


def fetch(url):
    print("Fetching:", url)
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def image_src(img):
    if not img:
        return None

    for attr in (
        "data-src",
        "data-image",
        "data-image-focal-point",
        "src",
    ):
        value = img.get(attr)
        if value and not value.startswith("data:"):
            return urljoin(BASE, value)

    srcset = img.get("srcset") or img.get("data-srcset")
    if srcset:
        first = srcset.split(",")[0].strip().split(" ")[0]
        return urljoin(BASE, first)

    return None


def safe_name(value):
    value = clean(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "image"


def download_image(url, basename):
    if not url:
        return None

    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()

    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"

    target = IMAGE_DIR / f"{safe_name(basename)}{ext}"

    if not target.exists():
        print("Downloading image:", url)
        r = fetch(url)
        target.write_bytes(r.content)

    return "/" + target.as_posix()


def find_link(soup, text=None, domain=None):
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        label = clean(a.get_text(" ", strip=True))

        if text and text.lower() not in label.lower():
            continue

        if domain and domain not in href:
            continue

        return href

    return None


# ---------------------------------------------------------
# 2025 seminar
# ---------------------------------------------------------

soup25 = BeautifulSoup(fetch(URL_2025).text, "html.parser")

speakers = []

speaker_re = re.compile(
    r"^(Monday,\s+.+?\d{4}\s+\d{1,2}:\d{2}\s+\w+)\s*\|\s*"
    r"(.+?)\s+\((.+)\)$"
)

for node in soup25.find_all(["p", "div"]):
    text = clean(node.get_text(" ", strip=True))

    m = speaker_re.match(text)

    if m:
        item = {
            "datetime": m.group(1),
            "name": clean(m.group(2)),
            "affiliation": clean(m.group(3)),
        }

        if item not in speakers:
            speakers.append(item)


# Fallback because Squarespace sometimes splits inline markup strangely.
if not speakers:
    expected = [
        ("Monday, 28 April 2025 17:00 CEST", "Achim Kramer",
         "Charité – Universitätsmedizin Berlin"),
        ("Monday, 5 May 2025 17:00 CEST", "Takuma Morimoto",
         "University of Oxford"),
        ("Monday, 12 May 2025 17:00 CEST", "William Tuten",
         "University of California, Berkeley"),
        ("Monday, 19 May 2025 17:00 CEST", "Lisa Ostrin",
         "University of Houston"),
        ("Monday, 2 June 2025 10:00 CEST", "Pauline Kang",
         "UNSW Sydney"),
        ("Monday, 16 June 2025 17:00 CEST", "Annegret Dahlmann-Noor",
         "Moorfields Eye Hospital & UCL"),
        ("Monday, 23 June 2025 10:00 CEST", "Raymond Najjar",
         "National University of Singapore"),
        ("Monday, 7 July 2025 17:00 CEST", "Catherine Manning",
         "University of Birmingham"),
        ("Monday, 14 July 2025 17:00 CEST", "Kyriaki Papantoniou",
         "Medical University of Vienna"),
    ]

    speakers = [
        {
            "datetime": date,
            "name": name,
            "affiliation": affiliation,
        }
        for date, name, affiliation in expected
    ]


register25 = None

for a in soup25.find_all("a", href=True):
    if "register" in clean(a.get_text()).lower():
        register25 = urljoin(BASE, a["href"])
        break


seminar_2025 = {
    "title": "Current Topics in Visual & Circadian Neuroscience",
    "subtitle": "Spring/summer 2025",
    "description": (
        'The Seminar Series "Current Topics in Visual & Circadian Neuroscience" '
        "is organised by the Translational Sensory & Circadian Neuroscience "
        "Unit (MPS/TUM/TUMCREATE) led by Prof. Dr. Manuel Spitschan. "
        "The 60-minute (45 min. talk + 15 min. Q&A/discussion) graduate-level "
        "seminars are free to join and take place via Zoom."
    ),
    "speakers": speakers,
    "timezone": "0800 PDT | 1100 EDT | 1600 BST | 1700 CEST | 2300 SGT | 0000 JST | 0100 AEST",
    "register_url": register25,
}


# ---------------------------------------------------------
# 2024 seminar
# ---------------------------------------------------------

soup24 = BeautifulSoup(fetch(URL_2024).text, "html.parser")

poster_url = None

# Prefer image around the content area.
for img in soup24.find_all("img"):
    src = image_src(img)

    if src and "CurrentTopics_Spring2024" in src:
        poster_url = src
        break

# Exact live asset fallback.
if not poster_url:
    poster_url = (
        "https://images.squarespace-cdn.com/content/v1/"
        "63305b1689502f4882626e0f/"
        "980bc041-7333-4b53-b506-e1c1d1aaa27d/"
        "CurrentTopics_Spring2024.png"
    )

poster_local = download_image(
    poster_url,
    "current-topics-sleep-circadian-health-spring-2024"
)

register24 = None

for a in soup24.find_all("a", href=True):
    if "register" in clean(a.get_text()).lower():
        register24 = urljoin(BASE, a["href"])
        break


seminar_2024 = {
    "title": "Current Topics in Sleep & Circadian Health",
    "subtitle": "Non-image-forming effects of light (Spring 2024)",
    "description": (
        'The Seminar Series "Current Topics in Sleep & Circadian Health" '
        "is organised by the Translational Sensory & Circadian Neuroscience "
        "Unit (MPS/TUM/TUMCREATE) led by Prof. Dr. Manuel Spitschan. "
        "The 60-minute (45 min. talk + 15 min. Q&A/discussion) graduate-level "
        "seminars are free to join and take place via Zoom."
    ),
    "image": poster_local,
    "register_url": register24,
}


# ---------------------------------------------------------
# Recorded talks
# ---------------------------------------------------------

soup_talks = BeautifulSoup(fetch(URL_TALKS).text, "html.parser")

playlist_specs = [
    {
        "title": "Current Topics in Sleep & Circadian Health",
        "years": "2022–",
        "needle": "PLzoZGn0-37XqNkZXJ1B6FoFiDzxyDnEID",
    },
    {
        "title": "Hot Topics in Health Psychology",
        "years": "2022–",
        "needle": "PLzoZGn0-37XpxmGyOOEQNTA9BXm5i0Z9s",
    },
    {
        "title": "TUM Integrative Physiology Seminar",
        "years": "2022–",
        "needle": "PLzoZGn0-37Xrs700nHFmtzSgc1FIG46dC",
    },
    {
        "title": "Integrative Chronobiology & Visual Neuroscience Seminar",
        "years": "2022",
        "needle": "PLzoZGn0-37XoIJCJEdQPUvTCgYB0Nx1oM",
    },
]


def nearest_image(anchor):
    node = anchor

    # Search increasingly larger card/container parents.
    for _ in range(8):
        if node is None:
            break

        if hasattr(node, "find"):
            img = node.find("img")
            src = image_src(img)

            if src:
                return src

        node = node.parent

    return None


# Sometimes the image and title are sibling Squarespace blocks.
# Collect page content images too as an ordered fallback.
content_images = []

for img in soup_talks.find_all("img"):
    src = image_src(img)

    if not src:
        continue

    if src in content_images:
        continue

    # Ignore tiny logos / obvious site chrome.
    lower = src.lower()
    if any(x in lower for x in [
        "youtube.png",
        "tum.png",
        "mpi-kyb",
    ]):
        continue

    content_images.append(src)


playlists = []

for index, spec in enumerate(playlist_specs, start=1):
    anchor = None

    for a in soup_talks.find_all("a", href=True):
        href = urljoin(BASE, a["href"])

        if spec["needle"] in href:
            anchor = a
            break

    if not anchor:
        print("WARNING: playlist link not found:", spec["title"])
        continue

    url = urljoin(BASE, anchor["href"])
    img_url = nearest_image(anchor)

    # If Squarespace separated image/title into adjacent blocks, map
    # the first four useful content images by visual order.
    if not img_url and index - 1 < len(content_images):
        img_url = content_images[index - 1]

    local_img = download_image(
        img_url,
        f"recorded-talks-{index}"
    )

    playlists.append({
        "title": spec["title"],
        "years": spec["years"],
        "url": url,
        "image": local_img,
    })


recorded_talks = {
    "title": "Recorded talks",
    "description": (
        "When we host a talk, we generally record the talk and make it "
        "available. Over time, we hope to build a free-to-watch library "
        "of cutting-edge research talks."
    ),
    "intro": "The following playlists aggregate the talks by talk series.",
    "playlists": playlists,
}


# ---------------------------------------------------------
# Final JSON
# ---------------------------------------------------------

data = {
    "seminar_2025": seminar_2025,
    "seminar_2024": seminar_2024,
    "recorded_talks": recorded_talks,
}

OUT.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n"
)

print()
print("Resources migration complete")
print("----------------------------")
print("2025 speakers:", len(speakers))
print("2024 poster:", poster_local)
print("Recorded-talk playlists:", len(playlists))
print("Written:", OUT)
