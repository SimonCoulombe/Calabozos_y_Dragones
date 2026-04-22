#!/usr/bin/env python3
"""Fetch and cache SVG icons from game-icons.net.

Icons are stored in assets/icons/<slug>.svg.
The function returns a PNG bytes object for embedding in Anki cards.
"""

import logging
import sys
from pathlib import Path

import requests
import yaml

BASE = Path(__file__).parent.parent
ICONS_DIR = BASE / "assets" / "icons"
CONFIG_FILE = BASE / "config.yaml"

log = logging.getLogger(__name__)

GAME_ICONS_BASE = "https://raw.githubusercontent.com/game-icons/icons/master/{author}/originals/svg/{slug}.svg"

ICON_AUTHORS: dict[str, str] = {
    "sword": "delapouite",
    "daggers": "lorc",
    "bow-arrow": "lorc",
    "battle-axe": "lorc",
    "magic-wand": "lorc",
    "shield": "delapouite",
    "visored-helm": "lorc",
    "breastplate": "lorc",
    "boots": "delapouite",
    "cloak": "lorc",
    "potion": "lorc",
    "torch": "delapouite",
    "rope-coil": "lorc",
    "treasure-map": "lorc",
    "bread": "lorc",
    "coins": "delapouite",
    "gold-bar": "lorc",
    "open-chest": "lorc",
    "shop": "lorc",
    "merchant": "delapouite",
    "eye": "delapouite",
    "ear": "lorc",
    "pine-tree": "delapouite",
    "river": "lorc",
    "mountain-road": "lorc",
    "path-distance": "lorc",
    "cave-entrance": "lorc",
    "bridge": "delapouite",
    "door-handle": "delapouite",
    "sword-clash": "lorc",
    "shield-reflect": "lorc",
    "dice-twenty-faces": "lorc",
    "goblin": "lorc",
    "thief": "delapouite",
    "half-heart": "lorc",
    "heart-plus": "lorc",
    "dungeon-gate": "lorc",
    "bear-trap": "lorc",
    "key": "delapouite",
    "corridor": "lorc",
    "return-arrow": "delapouite",
    "curved-arrow": "delapouite",
    "straight-arrow": "delapouite",
    "daemon-skull": "lorc",
    "skeleton-inside": "lorc",
    "troll": "lorc",
    "magic-swirl": "lorc",
    "fire": "lorc",
    "frozen-ring": "lorc",
    "sound-waves": "lorc",
    "water-drop": "delapouite",
    "magnifying-glass": "delapouite",
    "scroll-quill": "lorc",
    "conversation-bubbles": "lorc",
    "world-map": "delapouite",
    "person": "delapouite",
    "persons": "delapouite",
    "wizard-staff": "lorc",
    "boss-key": "lorc",
    "white-flag": "delapouite",
    "trophy": "delapouite",
    "victory-hand": "lorc",
    "castle": "delapouite",
    "barrel": "delapouite",
    "compass": "delapouite",
    "d4": "delapouite",
    "d6": "delapouite",
    "d8": "delapouite",
    "d10": "delapouite",
    "d12": "delapouite",
    "d20": "delapouite",
    "dice-one": "lorc",
    "dice-two": "lorc",
    "dice-three": "lorc",
    "dice-four": "lorc",
    "dice-five": "lorc",
    "dice-six": "lorc",
    "help": "delapouite",
    "backpack": "delapouite",
    "biceps": "lorc",
    "brain": "lorc",
    "angel-wings": "lorc",
    "power-lightning": "lorc",
    "pointed-hat": "lorc",
    "dwarf-king": "lorc",
    "ogre": "lorc",
    "fairy": "lorc",
    "run": "lorc",
    "hood": "lorc",
    "holy-grail": "lorc",
    "wish": "lorc",
    "check-mark": "delapouite",
    "warning": "lorc",
    "map-pin": "delapouite",
    "snail": "lorc",
    "sprint": "lorc",
    "footprint": "delapouite",
    "swords-power": "lorc",
    "night-sleep": "lorc",
    "hidden": "lorc",
    "juggler": "lorc",
    "meditation": "lorc",
    "dark": "lorc",
    "helping-hand": "lorc",
    "two-shadows": "lorc",
    "letter": "delapouite",
    "discussion": "lorc",
    "uncertainty": "lorc",
    "anvil-impact": "lorc",
    "wood-beam": "lorc",
    "resize-up": "delapouite",
    "resize-down": "delapouite",
    "exclamation": "lorc",
    "evil-minion": "lorc",
    "shopping-cart": "delapouite",
    "nose": "lorc",
    "arrow-cursor": "delapouite",
    "person-silhouette": "delapouite",
}


def icon_path(slug: str) -> Path:
    return ICONS_DIR / f"{slug}.svg"


def fetch_icon(slug: str, force: bool = False) -> Path | None:
    """Download icon SVG to cache. Returns local path or None on failure."""
    dest = icon_path(slug)
    if dest.exists() and not force:
        return dest

    author = ICON_AUTHORS.get(slug, "delapouite")
    url = GAME_ICONS_BASE.format(author=author, slug=slug)

    try:
        resp = requests.get(url, timeout=3)
        resp.raise_for_status()
        ICONS_DIR.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        log.info("Fetched icon: %s", slug)
        return dest
    except Exception as e:
        log.debug("Could not fetch icon %r: %s", slug, e)
        return None


def icon_to_png_bytes(slug: str, size: int = 64) -> bytes | None:
    """Return PNG bytes for an icon, fetching from game-icons.net if needed."""
    import cairosvg

    svg_path = fetch_icon(slug)
    if svg_path is None:
        # Try fallback only if it's already cached — don't make another network call
        fallback = icon_path("help")
        svg_path = fallback if fallback.exists() else None

    if svg_path is None:
        return None

    try:
        return cairosvg.svg2png(url=str(svg_path), output_width=size, output_height=size)
    except Exception as e:
        log.debug("Could not convert icon %r to PNG: %s", slug, e)
        return None


def prefetch_all() -> None:
    """Download all icons referenced in vocabulary CSVs."""
    import csv

    vocab_dir = BASE / "vocabulary"
    slugs: set[str] = set()

    for csv_file in vocab_dir.glob("theme_*.csv"):
        with open(csv_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                slug = row.get("icon", "").strip()
                if slug:
                    slugs.add(slug)

    print(f"Fetching {len(slugs)} icons...")
    ok = 0
    for slug in sorted(slugs):
        result = fetch_icon(slug)
        if result:
            ok += 1
        else:
            print(f"  MISSING: {slug}")
    print(f"  {ok}/{len(slugs)} icons cached in {ICONS_DIR}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    prefetch_all()
