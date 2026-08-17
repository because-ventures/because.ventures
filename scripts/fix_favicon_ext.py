#!/usr/bin/env python3
"""Fix the site icons that ExFlow exports as SVG content in .png files.

ExFlow downloads the Webflow favicon/webclip correctly, but the sources are
SVGs and it saves them as images/favicon.png and images/app-icon.png. Served
as image/png with SVG payloads, browsers render nothing. Rather than serving
the SVGs (unsupported by Safari and iOS webclips), we keep pre-rendered real
PNGs in scripts/assets/ — favicon-32.png and apple-touch-icon.png — copy them
into images/, and point every page's <link> icon tags at them.

Master copies live in scripts/assets/ so an ExFlow re-sync of images/ cannot
clobber them. Idempotent: copies overwrite identically and the href rewrite
is a no-op once applied.
"""

import re
import shutil
import sys
from pathlib import Path

ICONS = {
    # link-href stem -> committed real-PNG asset
    "favicon": "favicon-32.png",
    "app-icon": "apple-touch-icon.png",
}
LINK_RE = re.compile(
    r'(<link href=")((?:\.\./)*images/)(favicon|app-icon)\.(?:png|svg)(")'
)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    assets = root / "scripts" / "assets"
    for asset in ICONS.values():
        src = assets / asset
        if not src.is_file():
            raise SystemExit(f"missing master asset {src}")
        shutil.copyfile(src, root / "images" / asset)
        print(f"copied {src} -> images/{asset}")

    changed = 0
    for page in sorted(root.rglob("*.html")):
        html = page.read_text(encoding="utf-8")
        new = LINK_RE.sub(
            lambda m: f"{m.group(1)}{m.group(2)}{ICONS[m.group(3)]}{m.group(4)}",
            html,
        )
        if new != html:
            page.write_text(new, encoding="utf-8")
            changed += 1
    print(f"{changed} page(s) updated to reference real PNG icons")


if __name__ == "__main__":
    main()
