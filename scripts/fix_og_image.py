#!/usr/bin/env python3
"""Fix Open Graph / Twitter image URLs in the ExFlow export.

Two problems after export:
  1. og:image URLs are localized to relative paths (images/...). The Open
     Graph protocol requires absolute URLs — social scrapers won't resolve
     relative ones, so shares show no image.
  2. Pages without a per-page OG image carry content="" — scrapers then pick
     nothing or a random inline image.

Rewrite relative og:image/twitter:image URLs to absolute ones on the
production origin, and point empty ones at the site-wide default OG image
(the one exported by Webflow). Idempotent.
"""

import re
import sys
from pathlib import Path

ORIGIN = "https://because.ventures"
DEFAULT_OG_PATH = "images/open-20graph-20image.png"

META_RE = re.compile(
    r'(<meta content=")([^"]*)(" (?:property="og:image"|name="twitter:image")/?>)'
)


def absolutize(url: str) -> str:
    if url == "":
        return f"{ORIGIN}/{DEFAULT_OG_PATH}"
    if url.startswith(("http://", "https://")):
        return url
    return f"{ORIGIN}/{url.lstrip('./')}" if not url.startswith("../") else (
        f"{ORIGIN}/{url.removeprefix('../')}"
    )


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    if not (root / DEFAULT_OG_PATH).is_file():
        print(f"WARN: default OG image {DEFAULT_OG_PATH} missing; "
              "empty og:image tags will still be filled with its URL")
    changed = 0
    for page in sorted(root.rglob("*.html")):
        html = page.read_text(encoding="utf-8")
        new = META_RE.sub(
            lambda m: f"{m.group(1)}{absolutize(m.group(2))}{m.group(3)}", html
        )
        if new != html:
            page.write_text(new, encoding="utf-8")
            changed += 1
    print(f"{changed} page(s) updated with absolute og/twitter image URLs")


if __name__ == "__main__":
    main()
