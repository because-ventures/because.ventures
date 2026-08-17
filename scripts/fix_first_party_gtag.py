#!/usr/bin/env python3
"""Rewrite Webflow's first-party Google tag loaders to the public gtag.js loader.

Webflow injects GA in "first-party mode": the gtag.js library is served from
opaque relative paths (e.g. /0oarx4usxq70.../TqHubSEZ...) that only exist on
Webflow's own hosting. On an ExFlow static export (GitHub Pages) those paths
404 and the tag never fires. This script swaps them for the standard
https://www.googletagmanager.com/gtag/js loader, using the measurement ID
already present in the page's google_tags_first_party bootstrap snippet.

Idempotent: once rewritten, the proxied tags are gone and reruns are no-ops.
"""

import re
import sys
from pathlib import Path

BOOTSTRAP_RE = re.compile(r"\[(?:'|\")(?:[A-Z]+-[A-Z0-9-]+)(?:'|\")[^\]]*\]")
ID_RE = re.compile(r"['\"]([A-Z]+-[A-Z0-9-]+)['\"]")
PROXIED_SCRIPT_RE = re.compile(
    r'<script async(?:="")? src="/[A-Za-z0-9_-]{30,}/[A-Za-z0-9_-]{20,}"></script>'
)


def pick_loader_id(ids):
    # Prefer a GA4/Google-tag ID; UA is shut down and cannot be a loader.
    for tag_id in ids:
        if tag_id.startswith(("G-", "GT-", "AW-", "DC-")):
            return tag_id
    return ids[0] if ids else None


def fix_file(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    if "google_tags_first_party" not in html:
        return False
    proxied = PROXIED_SCRIPT_RE.findall(html)
    if not proxied:
        return False

    bootstrap = BOOTSTRAP_RE.search(html)
    ids = ID_RE.findall(bootstrap.group(0)) if bootstrap else []
    loader_id = pick_loader_id(ids)
    if not loader_id:
        print(f"WARN {path}: proxied scripts found but no tag ID; skipping")
        return False

    loader = (
        f'<script async src="https://www.googletagmanager.com/gtag/js'
        f'?id={loader_id}"></script>'
    )
    html = html.replace(proxied[0], loader, 1)
    for extra in proxied[1:]:
        html = html.replace(extra, "", 1)
    path.write_text(html, encoding="utf-8")
    print(f"fixed {path} -> {loader_id} ({len(proxied)} proxied script(s))")
    return True


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    changed = sum(fix_file(p) for p in sorted(root.rglob("*.html")))
    print(f"{changed} file(s) rewritten")


if __name__ == "__main__":
    main()
