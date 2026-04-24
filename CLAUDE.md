# Calabozos y Dragones

Spanish D&D learning campaign for French-speaking children, run by a Spanish-speaking DM.

## Project Purpose

Two French-speaking kids (ages ~10) are learning Spanish through a D&D campaign with a Spanish teacher who loves D&D. This repo contains:
- Vocabulary word lists per session (CSV)
- Grammar reference tables (YAML)
- Scripts to generate Anki flashcard decks (with TTS audio) and a PDF reference book
- DM session guides and pre-session bridging stories

## Directory Layout

```
vocabulary/          CSV word lists per session + grammar YAML files
content/sessions/    DM guides for each session (Markdown)
content/stories/     Pre-session bridging stories (Markdown)
scripts/             Python generation scripts
templates/           HTML/CSS template for PDF
assets/icons/        Cached game-icons.net SVGs
output/              Generated files (gitignored)
```

## Key Commands

```bash
make validate   # check all CSVs and YAMLs for errors
make pdf        # generate output/pdfs/livre_aventurier.pdf
make anki       # generate output/anki/*.apkg for each child
make all        # validate + pdf + anki
```

## Configuration

Edit `config.yaml` to change:
- Piper TTS server address/port/voice
- Child names and deck names
- Output directories

## Vocabulary CSV Format

All session word lists are CSV files with columns:
`spanish,french,category,icon,tags,notes`

- `icon`: slug from game-icons.net (e.g. `sword`, `visored-helm`, `potion`) — see `all_icons.txt` for the full list of available icon slugs
- `tags`: comma-separated, used to filter cards
- Blank rows at the bottom are for adding new words

## Grammar YAML Format

Grammar files use a structured format for conjugation tables — see `vocabulary/grammar/ser_estar.yaml` for the canonical example.

## Piper TTS

Spanish voice runs at `192.168.2.15:10201` (Wyoming protocol, voice `es_MX-claude-high`).
French voice (for reference) runs at `192.168.2.15:10200`.
If TTS server is unreachable, Anki cards are generated without audio (`skip_on_failure: true`).

## Workflow After Each Session

1. DM or parent opens the relevant session CSV on GitHub and adds new words to blank rows
2. Run `make all` to regenerate PDF and Anki decks
3. Share updated PDF via Google Drive; send `.apkg` to child's AnkiDroid
