#!/usr/bin/env python3
"""Pre-generate all TTS audio files for all vocabulary words.

Useful to run separately before generate_anki.py to check TTS quality
or to pre-cache audio on a machine with Piper access.
"""

import csv
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).parent.parent
VOCAB_DIR = BASE / "vocabulary"
CONFIG_FILE = BASE / "config.yaml"


def main() -> int:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    tts = config["tts"]
    audio_dir = BASE / config["output"]["audio_dir"]
    audio_dir.mkdir(parents=True, exist_ok=True)

    from tts_piper import synthesize_to_wav

    words: list[str] = []
    csv_files = sorted(VOCAB_DIR.glob("session_*.csv")) + sorted(VOCAB_DIR.glob("reference_*.csv"))
    for p in csv_files:
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                w = row.get("spanish", "").strip()
                if w:
                    words.append(w)

    words = list(dict.fromkeys(words))  # deduplicate, preserve order
    print(f"Generating audio for {len(words)} unique Spanish words...")

    ok = skipped = failed = 0
    for word in words:
        safe = word.replace(' ', '_').replace('/', '-')
        safe = ''.join(c for c in safe if c.isalnum() or c in '_-áéíóúüñÁÉÍÓÚÜÑ')
        filename = f"{safe}.wav"
        out_path = audio_dir / filename
        if out_path.exists():
            skipped += 1
            continue
        success = synthesize_to_wav(word, out_path, tts["host"], tts["port"],
                                    skip_on_failure=tts.get("skip_on_failure", True))
        if success:
            ok += 1
        else:
            failed += 1
            print(f"  FAILED: {word!r}")

    print(f"  {ok} generated, {skipped} already cached, {failed} failed")
    print(f"  Audio files in: {audio_dir}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
