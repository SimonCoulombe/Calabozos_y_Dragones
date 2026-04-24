#!/usr/bin/env python3
"""Fetch and cache SVG icons from game-icons.net.

Icons are stored in assets/icons/<author>/<slug>.svg.
The function returns a PNG bytes object for embedding in Anki cards.
"""

import logging
import sys
from pathlib import Path

import requests

BASE = Path(__file__).parent.parent
ICONS_DIR = BASE / "assets" / "icons"

log = logging.getLogger(__name__)

GAME_ICONS_BASE = "https://raw.githubusercontent.com/game-icons/icons/master/{author}/{slug}.svg"


def fetch_icon(icon_ref: str, force: bool = False) -> Path | None:
    """Download icon SVG to cache. Returns local path or None on failure.

    icon_ref is 'author/filename.svg'.
    """
    author, filename = icon_ref.split("/", 1)
    slug = filename.replace(".svg", "")

    dest = ICONS_DIR / f"{author}/{slug}.svg"
    if dest.exists() and not force:
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    url = GAME_ICONS_BASE.format(author=author, slug=slug)
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            dest.write_bytes(resp.content)
            log.info("Fetched icon: %s/%s", author, slug)
            return dest
    except Exception as e:
        log.debug("Could not fetch icon %r from %s: %s", slug, author, e)

    log.debug("Could not fetch icon %r", slug)
    return None


def icon_to_png_bytes(icon_ref: str, size: int = 64) -> bytes | None:
    """Return PNG bytes for an icon, fetching from game-icons.net if needed."""
    import cairosvg

    svg_path = fetch_icon(icon_ref)
    if svg_path is None:
        return None

    try:
        return cairosvg.svg2png(url=str(svg_path), output_width=size, output_height=size)
    except Exception as e:
        log.debug("Could not convert icon %r to PNG: %s", icon_ref, e)
        return None


def prefetch_all() -> None:
    """Download all icons referenced in vocabulary CSVs."""
    import csv

    vocab_dir = BASE / "vocabulary"
    icon_refs: set[str] = set()

    for csv_file in list(vocab_dir.glob("theme_*.csv")) + list(vocab_dir.glob("reference_*.csv")):
        with open(csv_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                icon_ref = row.get("icon", "").strip()
                if icon_ref:
                    icon_refs.add(icon_ref)

    print(f"Fetching {len(icon_refs)} icons...")
    ok = 0
    for icon_ref in sorted(icon_refs):
        result = fetch_icon(icon_ref)
        if result:
            ok += 1
        else:
            print(f"  MISSING: {icon_ref}")
    print(f"  {ok}/{len(icon_refs)} icons cached in {ICONS_DIR}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    prefetch_all()
