# Calabozos y Dragones 🐉

Spanish D&D learning campaign for French-speaking children, run by a Spanish-speaking DM.

## What is this?

Two French-speaking kids (~age 10) are learning Spanish through a D&D campaign with a Spanish teacher who loves D&D. This repo contains:

- **Vocabulary word lists** per theme (CSV — editable directly in GitHub's web UI)
- **Grammar reference tables** (YAML — conjugation tables, verb lists)
- **Scripts** to generate Anki cloze-deletion flashcard decks (with TTS audio) and a PDF reference book
- **DM session guides** and pre-session bridging stories

## Download

The latest PDF reference book and Anki decks are automatically generated and deployed to GitHub Pages:

- **[GitHub Pages — PDF + Anki Decks](https://simoncoulombe.github.io/Calabozos_y_Dragones/)**

## Quick Start

```bash
# First time — create the Python virtual environment
make setup

# Generate everything
make all        # validate + PDF + Anki decks

# Or individually
make validate   # check all CSVs and YAMLs for errors
make pdf        # output/pdfs/livre_aventurier.pdf
make anki       # output/anki/calabozos_child_1.apkg + child_2.apkg
make audio      # pre-generate all TTS audio (run before make anki)
make icons      # pre-cache game-icons.net SVGs (optional)
```

> **Note:** The virtual environment is created in `~/.local/share/calabozos-venv` because this repo may live on an exFAT drive (no symlinks). Override with `make pdf VENV=~/my-venv`.

> **Note:** If your system's default `python3` is old (e.g. 3.8), create the venv manually with a newer Python:
> ```bash
> /opt/python/3.12.11/bin/python3 -m venv ~/.local/share/calabozos-venv
> ~/.local/share/calabozos-venv/bin/pip install --upgrade pip
> ~/.local/share/calabozos-venv/bin/pip install -r requirements.txt
> ```

## Anki Card Format (Cloze Deletion)

Each card tests Spanish recall with a visible French hint:

**FRONT:**
> (épée) El guerrero saca su **\_\_\_\_\_** del cinturón.

**BACK:**
> **espada**
> El guerrero saca su espada del cinturón.
> *Le guerrier sort son épée de la ceinture.*
> 🔊 audio of the full Spanish sentence (when available)

See [CLOZE ANKI DATA GENERATION SPEC v5.md](CLOZE%20ANKI%20DATA%20GENERATION%20SPEC%20v5.md) for full details.

## Vocabulary CSV Format

All session word lists are CSV files with columns:

```
spanish,french,category,icon,tags,notes,cloze,french_sentence
```

| Column | Description |
|--------|-------------|
| `spanish` | Target word or phrase. May include gender pairs: `el mago / la maga` |
| `french` | French translation. May include gender variants: `le magicien / la magicienne` |
| `category` | Grouping label (e.g. `clases`, `atributos`, `armas`) |
| `icon` | Slug from game-icons.net (e.g. `lorc/magic-swirl.svg`) |
| `tags` | Comma-separated, used to filter cards |
| `notes` | Full natural D&D-style Spanish sentence (no markup). Used for PDF and TTS audio. |
| `cloze` | Anki cloze field: `(french_hint) sentence with {{c1::target}} word.` |
| `french_sentence` | Full French translation of the `notes` sentence |

### Editing Vocabulary (no coding needed)

Open any `vocabulary/theme_XX_*.csv` or `vocabulary/reference_*.csv` file on GitHub — it displays as an interactive table. Click the pencil icon to edit. Add words to the blank rows at the bottom. Commit. Then run `make all` to regenerate.

A GitHub Actions workflow automatically validates all files on every push (green ✓ / red ✗).

## Directory Layout

```
vocabulary/
  theme_01_quien_eres.csv       ← Theme 1: character creation, identity
  theme_02_la_tienda.csv        ← Theme 2: shopping, equipment
  theme_03_el_camino.csv        ← Theme 3: travel, directions, senses
  theme_04_la_mision.csv        ← Theme 4: quest, NPCs, key phrases
  theme_05_la_mazmorra.csv      ← Theme 5: dungeon exploration
  theme_06_el_jefe.csv          ← Theme 6: boss fight, victory/defeat
  reference_adjectives.csv      ← Possessives, adjectives, adverbs
  reference_colors.csv          ← Colors with adjective agreement
  reference_enemies.csv         ← Monsters by challenge rating
  reference_equipment.csv       ← Weapons, armor, gear
  reference_lugares.csv         ← Places and locations
  reference_mis_palabras.csv    ← Core gameplay words (aventura, tesoro…)
  reference_numbers.csv         ← Numbers 1–20 with D&D context
  reference_races.csv           ← All races + classes
  reference_spells.csv          ← Spells + magic schools
  grammar/
    ser_estar.yaml              ← SER vs ESTAR conjugation tables
    ir_poder_hay.yaml           ← IR, PODER, HAY
    hacer_tener.yaml            ← HACER and TENER
    regular_verbs.yaml          ← -AR / -ER / -IR pattern + examples
    dnd_verbs.yaml              ← D&D verb list by category

content/
  sessions/                     ← DM guides per session (Markdown)
  stories/                      ← Pre-session bridging stories (Markdown)

scripts/
  generate_pdf.py               ← CSV + YAML → WeasyPrint PDF
  generate_anki.py              ← CSV → Anki cloze .apkg (supports --no-tts, --only)
  generate_audio.py             ← Batch pre-generate TTS audio
  tts_piper.py                  ← Wyoming-protocol Piper TTS client
  fetch_icons.py                ← Cache game-icons.net SVGs → PNG
  validate.py                   ← Validate all CSV + YAML files
  update_csv_icons.py           ← Assign icons to CSV rows
  list_icons.py                 ← List all available icons
  patch_audio_silence.py        ← One-time: add silence padding to WAVs

templates/
  livre_aventurier.html         ← Jinja2 + WeasyPrint HTML/CSS template

output/                         ← Generated files (gitignored)
  pdfs/livre_aventurier.pdf
  anki/calabozos_child_1.apkg
  anki/calabozos_child_2.apkg
  audio/*.wav
  icons/icon_*.png
```

## Configuration

Edit `config.yaml`:

```yaml
tts:
  host: "192.168.2.15"
  port: 10201                   # Spanish Piper voice (es_MX-claude-high)
  skip_on_failure: true         # generate cards without audio if TTS unreachable

children:
  - id: child_1
    name: ""                    # fill in the child's name
    anki_deck_name: "Calabozos - Enfant 1"
  - id: child_2
    name: ""
    anki_deck_name: "Calabozos - Enfant 2"
```

## TTS (Piper Wyoming)

Audio is generated by a local [Piper](https://github.com/rhasspy/piper) TTS server:

- **Spanish** → `192.168.2.15:10201` (voice: `es_MX-claude-high`)
- **French** (reference only) → `192.168.2.15:10200`

If the server is unreachable, Anki cards are still generated without audio (`skip_on_failure: true`). Use `--no-tts` flag to skip audio entirely.

## Workflow After Each Session

1. DM or parent opens the session CSV on GitHub → adds new words to blank rows
2. Fill in `notes` (Spanish sentence), `cloze` (with `{{c1::target}}` + French hint), and `french_sentence`
3. Update `progress/child_N_progress.yaml` with words the child owned vs. struggled with
4. Run `make all` to regenerate PDF and Anki decks
5. Share updated PDF via Google Drive; send `.apkg` to child's AnkiDroid

## The "Spanish Superpower" Rule

> If you attempt an action in Spanish → roll **two dice, take the higher** (advantage).
> Full correct sentence → the DM may give a flat +2 or +3 bonus.
> Wrong Spanish → no penalty, roll normally.

This makes speaking Spanish a strategic advantage, never a punishment.

## Studying with Anki

1. Import `output/anki/calabozos_child_1.apkg` into Anki desktop or AnkiDroid
2. Click **Study Now** on the deck
3. Card front shows a Spanish sentence with a blank and a French hint
4. Think of the missing Spanish word → **Show Answer**
5. Rate yourself: Again / Hard / Good / Easy

Anki's spaced repetition will resurface words the child struggles with more often.

The French sentence on the back helps learn vocabulary in context — even words you weren't being tested on.
