#!/usr/bin/env python3
"""Update icon column in all vocabulary CSVs from 'filename' to 'author/filename.svg'.

Author mapping is embedded directly to avoid dependency on fetch_icons.
"""

import csv
import sys
from pathlib import Path

# Embedded author mapping (kept for offline use)
ICON_AUTHORS = {
    "sword": "delapouite",
    "daggers": "lorc",
    "bow-arrow": "delapouite",
    "battle-axe": "lorc",
    "magic-wand": "lorc",
    "shield": "sbed",
    "visored-helm": "lorc",
    "breastplate": "lorc",
    "boots": "lorc",
    "cloak": "lucasms",
    "potion": "lorc",
    "torch": "delapouite",
    "rope-coil": "delapouite",
    "treasure-map": "lorc",
    "bread": "delapouite",
    "coins": "delapouite",
    "gold-bar": "willdabeast",
    "open-chest": "skoll",
    "shop": "delapouite",
    "merchant": "delapouite",
    "eye": "delapouite",
    "ear": "lorc",
    "pine-tree": "lorc",
    "river": "delapouite",
    "mountain-road": "delapouite",
    "path-distance": "delapouite",
    "cave-entrance": "delapouite",
    "bridge": "lorc",
    "door-handle": "delapouite",
    "sword-clash": "lorc",
    "shield-reflect": "lorc",
    "dice-twenty-faces": "lorc",
    "goblin": "caro-asercion",
    "thief": "delapouite",
    "half-heart": "lorc",
    "heart-plus": "zeromancer",
    "dungeon-gate": "delapouite",
    "bear-trap": "lorc",
    "key": "sbed",
    "corridor": "lorc",
    "return-arrow": "lorc",
    "curved-arrow": "delapouite",
    "straight-arrow": "delapouite",
    "daemon-skull": "lorc",
    "skeleton-inside": "lorc",
    "troll": "skoll",
    "magic-swirl": "lorc",
    "fire": "sbed",
    "frozen-ring": "delapouite",
    "sound-waves": "skoll",
    "water-drop": "sbed",
    "magnifying-glass": "lorc",
    "scroll-quill": "delapouite",
    "conversation-bubbles": "lorc",
    "world-map": "delapouite",
    "person": "delapouite",
    "persons": "delapouite",
    "wizard-staff": "lorc",
    "boss-key": "delapouite",
    "white-flag": "delapouite",
    "trophy": "lorc",
    "victory-hand": "lorc",
    "castle": "delapouite",
    "barrel": "delapouite",
    "compass": "lorc",
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
    "biceps": "delapouite",
    "brain": "lorc",
    "angel-wings": "lorc",
    "power-lightning": "lorc",
    "pointed-hat": "lorc",
    "dwarf-king": "kier-heyl",
    "ogre": "delapouite",
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
    "footprint": "lorc",
    "swords-power": "delapouite",
    "night-sleep": "delapouite",
    "hidden": "lorc",
    "juggler": "lorc",
    "meditation": "lorc",
    "dark": "lorc",
    "helping-hand": "lorc",
    "two-shadows": "lorc",
    "letter": "delapouite",
    "discussion": "delapouite",
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
    "anchor": "lorc",
    "axe-sword": "delapouite",
    "bat": "skoll",
    "bear-face": "sparker",
    "bed": "delapouite",
    "book": "lorc",
    "cave": "lorc",
    "chains": "lorc",
    "chest": "delapouite",
    "city": "delapouite",
    "crossbow": "carl-olsen",
    "demon-skull": "lorc",
    "door": "delapouite",
    "dragon-head": "lorc",
    "druid-sign": "lorc",
    "dungeon": "lorc",
    "elf-ear": "delapouite",
    "exclamación": "lorc",
    "exit-door": "delapouite",
    "forest": "delapouite",
    "grass": "delapouite",
    "island": "delapouite",
    "lightning-storm": "lorc",
    "lizard": "delapouite",
    "mace": "lorc",
    "mail-shirt": "lorc",
    "mountain": "delapouite",
    "music-spell": "lorc",
    "pentacle": "skoll",
    "plate-armor": "lorc",
    "poison": "sbed",
    "poison-gas": "lorc",
    "rat": "delapouite",
    "recycle": "lorc",
    "road": "delapouite",
    "sand-dune": "delapouite",
    "skull-crack": "lorc",
    "spear": "lorc",
    "spider-face": "carl-olsen",
    "stone-wall": "delapouite",
    "sun": "lorc",
    "tavern": "lorc",
    "tower": "delapouite",
    "trap": "lorc",
    "village": "delapouite",
    "wave": "delapouite",
    "waves": "lorc",
    "wolf-head": "lorc",
    "zweihander": "lorc",
    "bone-mace": "delapouite",
    "caveman": "delapouite",
    "chainsaw": "delapouite",
    "city-car": "delapouite",
    "dark-squad": "lorc",
    "egg-eye": "delapouite",
    "laser-warning": "lorc",
    "lizardman": "lorc",
    "love-letter": "delapouite",
    "mantrap": "lorc",
    "mountains": "lorc",
    "nose-side": "delapouite",
    "notebook": "delapouite",
    "pear": "delapouite",
    "potion-ball": "lorc",
    "spears": "lorc",
    "swordman": "cathelineau",
    "tavern-sign": "delapouite",
    "tv-tower": "delapouite",
}

VOCAB_DIR = Path(__file__).parent.parent / "vocabulary"


def update_csv(csv_path: Path) -> int:
    """Update icon column in a CSV file. Returns number of icons updated."""
    rows = []
    updated = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            icon = row.get("icon", "").strip()
            if not icon:
                rows.append(row)
                continue
            if "/" not in icon:
                author = ICON_AUTHORS.get(icon, "delapouite")
                row["icon"] = f"{author}/{icon}.svg"
                updated += 1
            else:
                cur_author, fname = icon.split("/", 1)
                icon_name = fname.replace(".svg", "")
                expected_author = ICON_AUTHORS.get(icon_name)
                if expected_author and cur_author != expected_author:
                    row["icon"] = f"{expected_author}/{fname}"
                    updated += 1
            rows.append(row)

    if updated:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Updated {updated} icons in {csv_path.name}")

    return updated


def main() -> int:
    total = 0
    for csv_file in sorted(VOCAB_DIR.glob("*.csv")):
        total += update_csv(csv_file)
    print(f"\nTotal: {total} icons updated across all CSVs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
