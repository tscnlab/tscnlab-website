import json
from pathlib import Path

RAW_DIR = Path("data/news-raw")
POST_DIR = Path("_posts")

POST_DIR.mkdir(parents=True, exist_ok=True)


def yaml_quote(value):
    value = str(value or "")
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    return f'"{value}"'


def render_content(blocks):
    output = []

    image_number = 0

    for block in blocks:
        kind = block["type"]

        if kind == "image":
            image_number += 1

            alt = block.get("alt") or ""

            output.append(
                '<figure class="article-figure">\n'
                f'  <img src="{{{{ \'{block["src"]}\' | relative_url }}}}" '
                f'alt="{alt}">\n'
                '</figure>'
            )

        elif kind == "h2":
            output.append(
                f'<h2>{block["text"]}</h2>'
            )

        elif kind == "h3":
            output.append(
                f'<h3>{block["text"]}</h3>'
            )

        elif kind == "blockquote":
            output.append(
                f'<blockquote>{block["text"]}</blockquote>'
            )

        elif kind == "ul":
            output.append(
                f'<p>{block["text"]}</p>'
            )

        elif kind == "ol":
            output.append(
                f'<p>{block["text"]}</p>'
            )

        else:
            output.append(
                f'<p>{block["text"]}</p>'
            )

    return "\n\n".join(output)


articles = []

for path in RAW_DIR.glob("*.json"):
    if path.name == "index.json":
        continue

    article = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not article.get("date"):
        print(f"Skipping {path.name}: no date")
        continue

    articles.append(article)

articles.sort(
    key=lambda article: article["date"]
)

for article in articles:
    lines = [
        "---",
        "layout: post",
        f"title: {yaml_quote(article['title'])}",
        f"date: {article['date']}",
        f"author: {yaml_quote(article.get('author', ''))}",
        f"excerpt_text: {yaml_quote(article.get('excerpt', ''))}",
        f"source_url: {yaml_quote(article.get('source_url', ''))}",
    ]

    if article.get("featured_image"):
        lines.append(
            f"image: {yaml_quote(article['featured_image'])}"
        )

    lines += [
        "---",
        "",
        render_content(article["content"]),
        ""
    ]

    filename = (
        POST_DIR
        / f"{article['date']}-{article['slug']}.md"
    )

    filename.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(f"Created {filename}")

print(f"Generated {len(articles)} posts.")
