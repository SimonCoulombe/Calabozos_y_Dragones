#!/usr/bin/env python3
"""Generate Anki cloze-deletion decks (.apkg) from vocabulary CSVs.

New format (v2): uses cloze model with french hint on front, french sentence on back.
Supports --only PATTERN to filter CSVs, --no-tts to skip audio.
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
.cloze-sentence { font-size: 22px; color: #2c1a0e; margin-bottom: 12px; line-height: 1.5; }
.spanish-word { font-size: 28px; font-weight: bold; color: #5c1a00; margin: 10px 0; }
.full-sentence { font-size: 18px; color: #2c1a0e; margin: 8px 0; }
.french-sentence { font-size: 16px; color: #5c3a1e; font-style: italic; margin: 8px 0; }
.category { font-size: 12px; color: #7a3a10; font-style: italic; margin-top: 5px; }
.icon img { width: 64px; height: 64px; margin-bottom: 8px; }
.cloze { font-weight: bold; color: #5c1a00; }
"""

# Cloze front: show the cloze sentence (with blank + french hint)
FRONT_TEMPLATE = """
<div class="card">
  <div class="icon">{{Icon}}</div>
  <div class="cloze-sentence">{{cloze:Text}}</div>
  <div class="category">{{Category}}</div>
</div>
"""

# Cloze back: answer + full spanish sentence + french sentence + audio
BACK_TEMPLATE = """
<div class="card">
  <div class="icon">{{Icon}}</div>
  <div class="cloze-sentence">{{cloze:Text}}</div>
  <div class="category">{{Category}}</div>
  <hr>
  <div class="spanish-word">{{Spanish}}</div>
  <div class="full-sentence">{{FullSentence}}</div>
  <div class="french-sentence">{{FrenchSentence}}</div>
  {{Audio}}
</div>
"""


def stable_id(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)


def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_words(only_pattern: str | None = None) -> list[dict]:
    """Load vocabulary CSVs, optionally filtered by pattern."""
    words = []
    csv_files = sorted(VOCAB_DIR.glob("theme_*.csv")) + sorted(VOCAB_DIR.glob("reference_*.csv"))

    for p in csv_files:
        if only_pattern and only_pattern not in p.stem:
            continue
        is_session = p.stem.startswith("theme_")
        num = p.stem.split("_")[1] if is_session else None
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                spanish = row.get("spanish", "").strip()
                cloze = row.get("cloze", "").strip()
                if not spanish:
                    continue
                # Skip rows without cloze data (old format CSVs)
                if only_pattern and not cloze:
                    continue
                words.append({
                    "spanish": spanish,
                    "french": row.get("french", "").strip(),
                    "category": row.get("category", "").strip(),
                    "icon": row.get("icon", "").strip(),
                    "tags": [t.strip() for t in row.get("tags", "").split(",") if t.strip()],
                    "notes": row.get("notes", "").strip(),
                    "cloze": cloze,
                    "french_sentence": row.get("french_sentence", "").strip(),
                    "session": num,
                    "session_name": SESSION_NAMES.get(num, f"Tema {num}") if num else p.stem,
                })
    return words


def get_audio_and_icon(
    word: dict,
    config: dict,
    audio_dir: Path,
    icons_dir: Path,
    skip_tts: bool = False,
) -> tuple[str, str, list[str]]:
    """Return (audio_field_html, icon_field_html, media_files_to_add)."""
    media = []
    audio_html = ""
    icon_html = ""

    # Audio: based on notes (full sentence)
    safe = word['spanish'].replace(' ', '_').replace('/', '-')
    safe = ''.join(c for c in safe if c.isalnum() or c in '_-áéíóúüñÁÉÍÓÚÜÑ')
    audio_filename = f"{safe}.wav"
    audio_path = audio_dir / audio_filename
    if not skip_tts and audio_path.exists():
        audio_html = f"[sound:{audio_filename}]"
        if str(audio_path) not in media:
            media.append(str(audio_path))

    # Icon: try to load from cache, skip gracefully if missing
    icon_ref = word["icon"] or config["images"].get("fallback_icon", "")
    if config["images"]["provider"] == "game_icons" and icon_ref and "/" in icon_ref:
        try:
            from fetch_icons import icon_to_png_bytes
            png_bytes = icon_to_png_bytes(icon_ref)
            if png_bytes:
                safe_name = icon_ref.replace("/", "_").replace(".svg", "")
                icon_filename = f"icon_{safe_name}.png"
                icon_path = icons_dir / icon_filename
                if not icon_path.exists():
                    icon_path.write_bytes(png_bytes)
                icon_html = f'<img src="{icon_filename}">'
                if str(icon_path) not in media:
                    media.append(str(icon_path))
        except Exception:
            pass  # icons not available, skip

    return audio_html, icon_html, media


def build_deck(child: dict, words: list[dict], config: dict, out_dir: Path, audio_dir: Path, icons_dir: Path, skip_tts: bool = False) -> Path:
    deck_id = stable_id(f"calabozos-{child['id']}")
    model_id = stable_id("model-calabozos-cloze-v2")

    model = genanki.Model(
        model_id,
        "Calabozos Cloze v2",
        fields=[
            {"name": "Text"},            # cloze sentence with {{c1::}} markup + french hint
            {"name": "Spanish"},         # target word/phrase
            {"name": "FullSentence"},    # notes = full spanish sentence
            {"name": "FrenchSentence"},  # french translation of the sentence
            {"name": "Audio"},
            {"name": "Icon"},
            {"name": "Category"},
            {"name": "Session"},
        ],
        templates=[{
            "name": "Cloze ES→FR",
            "qfmt": FRONT_TEMPLATE,
            "afmt": BACK_TEMPLATE,
        }],
        css=CARD_CSS,
        model_type=genanki.Model.CLOZE,
    )

    deck_name = child.get("anki_deck_name", f"Calabozos - {child['id']}")
    deck = genanki.Deck(deck_id, deck_name)

    media_files: list[str] = []
    seen: set[str] = set()

    for word in words:
        if word["spanish"] in seen:
            continue
        seen.add(word["spanish"])

        if not word.get("cloze"):
            continue

        audio_html, icon_html, word_media = get_audio_and_icon(word, config, audio_dir, icons_dir, skip_tts=skip_tts)
        for m in word_media:
            if m not in media_files:
                media_files.append(m)

        def sanitize_tag(t: str) -> str:
            return t.replace(" ", "_").replace("—", "").replace("?", "").strip("_")

        tags = [sanitize_tag(word["session_name"])] + [sanitize_tag(t) for t in word["tags"] if t]

        note = genanki.Note(
            model=model,
            fields=[
                word["cloze"],
                word["spanish"],
                word["notes"],
                word["french_sentence"],
                audio_html,
                icon_html,
                word["category"],
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

    only_pattern = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        if idx + 1 < len(sys.argv):
            only_pattern = sys.argv[idx + 1]

    config = load_config()
    out_dir = BASE / config["output"]["anki_dir"]
    audio_dir = BASE / config["output"]["audio_dir"]
    icons_dir = BASE / "output" / "icons"
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)

    words = load_words(only_pattern)
    if not words:
        print("ERROR: no vocabulary words loaded — check your CSV files")
        return 1

    print(f"Loaded {len(words)} words" + (f" (filter: {only_pattern})" if only_pattern else ""))
    if skip_tts:
        print("TTS disabled — cards will have no audio")

    for child in config.get("children", []):
        print(f"Building deck for {child['id']}...")
        out_path = build_deck(child, words, config, out_dir, audio_dir, icons_dir, skip_tts=skip_tts)
        print(f"  ANKI  →  {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
