#!/usr/bin/env python3
"""List all available SVG icon filenames from temp_icons/ directory.

Extracts author/filename.svg pairs from the nested temp_icons structure
and writes them to a sorted text file for reference.
"""

from pathlib import Path

BASE = Path(__file__).parent.parent
TEMP_ICONS = BASE / "temp_icons"
OUT_FILE = BASE / "available_icons.txt"


def main() -> int:
    if not TEMP_ICONS.exists():
        print(f"ERROR: temp_icons directory not found at {TEMP_ICONS}")
        return 1

    icons = []
    for svg_path in TEMP_ICONS.rglob("*.svg"):
        # Extract author/filename.svg from the nested path
        # e.g. temp_icons/icons/ffffff/000000/1x1/lorc/dragon-head.svg
        parts = svg_path.parts
        try:
            # Find the "1x1" directory, then author and filename follow
            idx = parts.index("1x1")
            author = parts[idx + 1]
            filename = parts[idx + 2]
            icon_ref = f"{author}/{filename}"
            icons.append(icon_ref)
        except (ValueError, IndexError):
            continue

    icons = sorted(set(icons))

    OUT_FILE.write_text(f"# {len(icons)} available icons from temp_icons/\n# Format: author/filename.svg\n\n")
    OUT_FILE.write_text("\n".join(icons) + "\n")

    print(f"Written {len(icons)} icon references to {OUT_FILE}")

    # Summary by author
    authors: dict[str, int] = {}
    for icon in icons:
        author = icon.split("/")[0]
        authors[author] = authors.get(author, 0) + 1

    print(f"\nTop authors by icon count:")
    for author, count in sorted(authors.items(), key=lambda x: -x[1])[:10]:
        print(f"  {author}: {count}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
