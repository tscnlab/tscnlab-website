from pathlib import Path
from urllib.request import Request, urlopen
import re

URL = "https://raw.githubusercontent.com/tscnlab/MissionStatement/main/MissionStatement_Current.md"
OUT = Path("_mission/mission-statement.md")

OUT.parent.mkdir(parents=True, exist_ok=True)

req = Request(
    URL,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urlopen(req) as response:
    content = response.read().decode("utf-8")

# The source Markdown already contains "# Mission Statement".
# The Jekyll layout provides the page title, so remove only that first H1
# to avoid rendering the title twice.
content = re.sub(
    r"^\s*#\s+Mission Statement\s*\n+",
    "",
    content,
    count=1,
    flags=re.IGNORECASE
)

front_matter = """---
layout: mission-statement
title: Mission Statement
permalink: /mission-statement/
---

"""

OUT.write_text(
    front_matter + content,
    encoding="utf-8"
)

print(f"Updated {OUT}")