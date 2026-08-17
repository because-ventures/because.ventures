#!/usr/bin/env python3
"""Fix SVG icons that ExFlow exports with a .png extension.

ExFlow downloads the Webflow favicon/webclip correctly, but saves the SVG
sources as images/favicon.png and images/app-icon.png. Served as image/png,
browsers refuse to render the SVG payload, so no favicon shows. Copy each
SVG-content .png icon to a .svg twin and point the <link> tags at it.

Idempotent: re-copies from the (possibly re-synced) .png source and the
href rewrite is a no-op once applied.
"""

import re
import shutil
import sys
from pathlib import Path

ICONS = ["favicon.png", "app-icon.png"]
LINK_RE = re.compile(
    r'(<link href=")((?:\.\./)*images/)(favicon|app-icon)\.png(")'
)


def is_svg(path: Path) -> bool:
    head = path.read_bytes()[:200].lstrip()
    return head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in head)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    fixed_icons = set()
    for name in ICONS:
        src = root / "images" / name
        if src.is_file() and is_svg(src):
            dst = src.with_suffix(".svg")
            shutil.copyfile(src, dst)
            fixed_icons.add(Path(name).stem)
            print(f"copied {src} -> {dst}")

    if not fixed_icons:
        print("no SVG-content .png icons found; nothing to do")
        return

    changed = 0
    for page in sorted(root.rglob("*.html")):
        html = page.read_text(encoding="utf-8")
        new = LINK_RE.sub(
            lambda m: (
                f"{m.group(1)}{m.group(2)}{m.group(3)}.svg{m.group(4)}"
                if m.group(3) in fixed_icons
                else m.group(0)
            ),
            html,
        )
        if new != html:
            page.write_text(new, encoding="utf-8")
            changed += 1
    print(f"{changed} page(s) updated to reference .svg icons")


if __name__ == "__main__":
    main()
