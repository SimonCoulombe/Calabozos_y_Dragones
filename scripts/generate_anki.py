#!/usr/bin/env python3
"""Generate Anki decks (.apkg) from vocabulary CSVs.

One deck per child defined in config.yaml.
Each card: front = Spanish word + icon, back = French translation + TTS audio.
"""

import csv
import hashlib
import sys
from pathlib import Path

import genanki
import yaml

BASE = Path(__file__).parent.parent
VOCAB_DIR = BASE / "vocabulary"
CONFIG_FILE = BASE / "config.yaml"

SESSION_NAMES = {
    "01": "Tema 1 — ¿Quién eres tú ?",
    "02": "Tema 2 — La Tienda",
    "03": "Tema 3 — El Camino",
    "04": "Tema 4 — La Misión",
    "05": "Tema 5 — La Mazmorra",
    "06": "Tema 6 — El Jefe",
}

CARD_CSS = """
.card {
  font-family: 'Georgia', serif;
  font-size: 18px;
  text-align: center;
  background: #f5ead0;
  color: #2c1a0e;
  padding: 20px;
}
.spanish { font-size: 28px; font-weight: bold; color: #5c1a00; margin-bottom: 10px; }
.french  { font-size: 22px; color: #2c1a0e; margin-top: 10px; }
.category { font-size: 12px; color: #7a3a10; font-style: italic; margin-top: 5px; }
.example { font-size: 14px; color: #5c3a1e; font-style: italic; margin-top: 8px; }
.icon img { width: 80px; height: 80px; margin-bottom: 10px; }
"""

FRONT_TEMPLATE = """
<div class="card">
  <div class="icon">{{Icon}}</div>
  <div class="spanish">{{Spanish}}</div>
  <div class="category">{{Category}}</div>
  {{Audio}}  <!-- This will include the audio field here -->
</div>
"""

BACK_TEMPLATE = """
{{FrontSide}}
<hr>
<div class="card">
  <div class="french">{{French}}</div>
  <div class="example">{{Example}}</div>

</div>
"""


def stable_id(text: str) -> int:
    """Generate a stable integer ID from a string (fits in Anki's int range)."""
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)


def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_words() -> list[dict]:
    """Load all vocabulary CSVs (session and reference), tagged with source."""
    words = []
    csv_files = sorted(VOCAB_DIR.glob("theme_*.csv")) + sorted(VOCAB_DIR.glob("reference_*.csv"))
    for p in csv_files:
        is_session = p.stem.startswith("theme_")
        num = p.stem.split("_")[1] if is_session else None
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("spanish", "").strip():
                    words.append({
                        "spanish": row["spanish"].strip(),
                        "french": row.get("french", "").strip(),
                        "category": row.get("category", "").strip(),
                        "icon": row.get("icon", "").strip(),
                        "tags": [t.strip() for t in row.get("tags", "").split(",") if t.strip()],
                        "notes": row.get("notes", "").strip(),
                        "session": num,
                        "session_name": SESSION_NAMES.get(num, f"Tema {num}") if num else p.stem,
                    })
    return words


def get_audio_and_icon(
    word: dict,
    config: dict,
    audio_dir: Path,
    skip_tts: bool = False,
) -> tuple[str, str, bytes | None, str | None]:
    """Return (audio_field_html, icon_field_html, icon_png_bytes, icon_filename) for this word."""
    from fetch_icons import icon_to_png_bytes

    audio_html = ""
    icon_html = ""

    safe = word['spanish'].replace(' ', '_').replace('/', '-')
    safe = ''.join(c for c in safe if c.isalnum() or c in '_-áéíóúüñÁÉÍÓÚÜÑ')
    audio_filename = f"{safe}.wav"
    audio_path = audio_dir / audio_filename

    if not skip_tts and audio_path.exists():
        audio_html = f"[sound:{audio_filename}]"

    icon_ref = word["icon"].strip() or config["images"].get("fallback_icon")
    if config["images"]["provider"] == "game_icons" and icon_ref and "/" in icon_ref:
        png_bytes = icon_to_png_bytes(icon_ref)
        if png_bytes:
            safe_name = icon_ref.replace("/", "_").replace(".svg", "")
            icon_filename = f"icon_{safe_name}.png"
            icon_html = f'<img src="{icon_filename}">'
            return audio_html, icon_html, png_bytes, icon_filename

    return audio_html, icon_html, None, None


def build_deck(child: dict, words: list[dict], config: dict, out_dir: Path, audio_dir: Path, skip_tts: bool = False) -> Path:
    deck_id = stable_id(f"calabozos-{child['id']}")
    model_id = stable_id(f"model-calabozos-v1")

    model = genanki.Model(
        model_id,
        "Calabozos Card",
        fields=[
            {"name": "Spanish"},
            {"name": "French"},
            {"name": "Category"},
            {"name": "Example"},
            {"name": "Audio"},
            {"name": "Icon"},
            {"name": "Session"},
        ],
        templates=[
            {
                "name": "ES → FR",
                "qfmt": FRONT_TEMPLATE,
                "afmt": BACK_TEMPLATE,
            }
        ],
        css=CARD_CSS,
    )

    deck_name = child.get("anki_deck_name", f"Calabozos - {child['id']}")
    deck = genanki.Deck(deck_id, deck_name)

    media_files: list[str] = []
    seen: set[str] = set()
    icon_cache: dict[str, bytes] = {}

    for word in words:
        if word["spanish"] in seen:
            continue
        seen.add(word["spanish"])

        audio_html, icon_html, png_bytes, icon_filename = get_audio_and_icon(word, config, audio_dir, skip_tts=skip_tts)

        if png_bytes and icon_filename:
            icon_path = audio_dir / icon_filename
            if not icon_path.exists():
                icon_path.write_bytes(png_bytes)
            if str(icon_path) not in media_files:
                media_files.append(str(icon_path))

        safe_for_path = word['spanish'].replace(' ', '_').replace('/', '-')
        safe_for_path = ''.join(c for c in safe_for_path if c.isalnum() or c in '_-áéíóúüñÁÉÍÓÚÜÑ')
        audio_path = audio_dir / f"{safe_for_path}.wav"
        if audio_path.exists() and str(audio_path) not in media_files:
            media_files.append(str(audio_path))

        def sanitize_tag(t: str) -> str:
            return t.replace(" ", "_").replace("—", "").replace("?", "").strip("_")

        tags = [sanitize_tag(word["session_name"])] + [sanitize_tag(t) for t in word["tags"] if t]

        note = genanki.Note(
            model=model,
            fields=[
                word["spanish"],
                word["french"],
                word["category"],
                word["notes"],
                audio_html,
                icon_html,
                word["session_name"],
            ],
            tags=[t for t in tags if t],
        )
        deck.add_note(note)

    child_id = child["id"]
    out_path = out_dir / f"calabozos_{child_id}.apkg"
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(str(out_path))
    return out_path


def main() -> int:
    skip_tts = "--no-tts" in sys.argv

    config = load_config()
    out_dir = BASE / config["output"]["anki_dir"]
    audio_dir = BASE / config["output"]["audio_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    words = load_all_words()
    if not words:
        print("ERROR: no vocabulary words loaded — check your session CSV files")
        return 1

    print(f"Loaded {len(words)} words from vocabulary CSVs")
    if skip_tts:
        print("TTS disabled — cards will have no audio")

    for child in config.get("children", []):
        print(f"Building deck for {child['id']} ({child.get('name', 'unnamed')})...")
        out_path = build_deck(child, words, config, out_dir, audio_dir, skip_tts=skip_tts)
        print(f"  ANKI  →  {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
