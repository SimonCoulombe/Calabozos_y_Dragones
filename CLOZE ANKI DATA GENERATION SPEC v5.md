CLOZE ANKI DATA GENERATION SPEC v5

GOAL
Transform Spanish → French D&D vocabulary CSVs into Anki cloze-deletion flashcard decks.

Each card tests Spanish word recall (production) with:
- a visible French meaning cue on the front
- a full French sentence translation on the back
- one canonical D&D sentence per concept
- deterministic cloze matching (no NLP guessing)


═══════════════════════════════════════════════════
CSV FORMAT
═══════════════════════════════════════════════════

spanish,french,category,icon,tags,notes,cloze,french_sentence

COLUMN DEFINITIONS

  spanish       Target word/phrase. May include gender pairs: el mago / la maga
  french        French translation. May include gender variants: le magicien / la magicienne
  category      Grouping label (clases, atributos, armas, etc.)
  icon          game-icons.net slug (e.g. lorc/magic-swirl.svg). UI only.
  tags          Comma-separated metadata for filtering
  notes         Full natural D&D-style Spanish sentence. NO cloze markup.
                Used for: PDF output, TTS audio generation.
  cloze         French hint + cloze sentence. This IS the Anki "Text" field.
                Format: (french_hint) Sentence with {{c1::target}} word.
  french_sentence  Full French translation of the notes sentence.


═══════════════════════════════════════════════════
CLOZE COLUMN FORMAT
═══════════════════════════════════════════════════

The cloze column contains Anki {{c1::}} markup directly in the CSV.
French hint goes FIRST so the learner sees it immediately.

  (french_hint) Rest of the sentence with {{c1::target}} word.

EXAMPLES:

  Single word:
    (épée) El guerrero saca su {{c1::espada}} del cinturón.

  Multi-word expression:
    (classe d'armure) Mi {{c1::clase de armadura}} es quince.

  Verb:
    (je suis) {{c1::Soy}} una guerrera elfa.

  Phrase:
    (d'où es-tu ?) {{c1::¿De dónde eres?}} — Soy de las montañas.

  Gender pair (sentence uses one form):
    (magicienne) La {{c1::maga}} elfa lanza un hechizo.

ONLY use {{c1::}} — never {{c2::}} or other cloze numbers. One blank per card.


═══════════════════════════════════════════════════
ANKI CARD LAYOUT
═══════════════════════════════════════════════════

FRONT:
  [icon]
  (épée) El guerrero saca su _____ del cinturón.
  [category]

BACK:
  [icon]
  (épée) El guerrero saca su espada del cinturón.
  [category]
  ───────────────────
  espada                                    ← bold, large
  El guerrero saca su espada del cinturón.  ← full Spanish sentence
  Le guerrier sort son épée de la ceinture. ← full French sentence (italic)
  🔊 [audio of full Spanish sentence]       ← when .wav available


═══════════════════════════════════════════════════
ANKI MODEL (genanki)
═══════════════════════════════════════════════════

Model type:   genanki.Model.CLOZE
Model name:   "Calabozos Cloze v2"
Model ID:     stable_id("model-calabozos-cloze-v2")

Fields:
  Text            ← cloze column (contains {{c1::}} markup + french hint)
  Spanish         ← spanish column
  FullSentence    ← notes column
  FrenchSentence  ← french_sentence column
  Audio           ← [sound:filename.wav] or empty
  Icon            ← <img src="icon_*.png"> or empty
  Category        ← category column
  Session         ← derived from filename (e.g. "Tema 1 — ¿Quién eres tú ?")

Front template uses: {{cloze:Text}}, {{Icon}}, {{Category}}
Back template uses:  {{cloze:Text}}, {{Spanish}}, {{FullSentence}}, {{FrenchSentence}}, {{Audio}}


═══════════════════════════════════════════════════
GENDER PAIR RULES
═══════════════════════════════════════════════════

When spanish contains "el X / la Y" (gender pair):
  - Keep as ONE CSV row
  - Pick ONE gender for the example sentence (randomly or consistently)
  - Cloze wraps ONLY the noun, not the article:
      El {{c1::guerrero}} humano protege al grupo.
  - The spanish field keeps both forms: el guerrero / la guerrera
  - The french field keeps both: le guerrier / la guerrière

For single-gender nouns:
  - Include article in cloze when it appears in the sentence:
      Voy a comprar {{c1::el equipo}} en el mercado.
  - Omit article when sentence doesn't use it:
      Tengo trece de {{c1::fuerza}}.

Adjectives with gender pairs (bueno / buena, peligroso / peligrosa):
  - One row, pick one form for the sentence
  - Adjective must agree with the sentence subject


═══════════════════════════════════════════════════
CLOZE MATCHING RULES
═══════════════════════════════════════════════════

1. EXACT MATCH ONLY — the target word/phrase in the cloze must appear
   identically in the notes sentence. No fuzzy matching.

2. MULTI-WORD EXPRESSIONS — match the full contiguous token sequence:
   {{c1::puntos de golpe}}  not  {{c1::puntos}} de {{c1::golpe}}

3. ARTICLE INCLUSION — if the article is part of the expression in the
   spanish field, include it: {{c1::la clase de armadura}}

4. ONE CLOZE PER CARD — only {{c1::}} is used. Never c2, c3, etc.

5. SENTENCE MUST CONTAIN TARGET — if the exact target word doesn't appear
   in the sentence, rewrite the sentence. Never guess or force a match.
   Common pitfalls:
   - "mi personaje" does NOT match "el personaje"
   - "jugadores" (plural) does NOT match "el jugador" (singular)
   - "la clase de armadura (CA)" — drop the parenthetical from spanish field


═══════════════════════════════════════════════════
AUDIO RULES
═══════════════════════════════════════════════════

- Audio is generated from the `notes` column ONLY (full sentence, no cloze markup)
- Audio files: output/audio/{safe_spanish}.wav
- Use --no-tts to skip audio entirely
- If TTS server unreachable, cards generate without audio (skip_on_failure: true)


═══════════════════════════════════════════════════
FILE ORGANIZATION
═══════════════════════════════════════════════════

  output/audio/*.wav          ← TTS audio files
  output/icons/icon_*.png     ← Converted icon PNGs (NOT in audio dir)
  output/anki/*.apkg          ← Generated Anki decks
  output/pdfs/*.pdf           ← Generated PDF reference book


═══════════════════════════════════════════════════
SCRIPT USAGE
═══════════════════════════════════════════════════

  # Via Makefile:
  make anki                              # all CSVs, with TTS
  make anki ANKI_FLAGS="--no-tts"        # all CSVs, no audio

  # Direct script:
  PYTHONPATH=scripts python scripts/generate_anki.py --no-tts --only theme_01
  PYTHONPATH=scripts python scripts/generate_anki.py --no-tts
  PYTHONPATH=scripts python scripts/generate_anki.py

  --only PATTERN    Filter CSV files (e.g. --only theme_01, --only reference_colors)
  --no-tts          Skip audio entirely


═══════════════════════════════════════════════════
TIPS AND TRICKS FOR IMPLEMENTERS
═══════════════════════════════════════════════════

WRITING CSVS PROGRAMMATICALLY
  - Always use Python's csv.DictWriter — never concatenate strings manually
  - DictWriter handles quoting of commas, quotes, and newlines automatically
  - heredoc (cat << 'EOF') works fine for simple CSVs but breaks with embedded commas

PROCESSING MANY CSVS WITHOUT HITTING CONTEXT LIMITS
  - Process one CSV at a time with a subagent
  - Each subagent: read CSV → write Python script → run script → verify output
  - This avoids accumulating 15 CSVs worth of context in one conversation

WRITING GOOD D&D SENTENCES
  - Every sentence should be a plausible thing said during a D&D session
  - Use character types, monsters, spells, locations from the campaign
  - Vary sentence structures: statements, questions, commands, dialogue
  - Keep sentences short enough for a 10-year-old: 6-12 words ideal

COMMON SENTENCE PATTERNS THAT WORK WELL
  - "El [class] [action] [object]." — El guerrero protege al grupo.
  - "Tengo [number] de [stat]."     — Tengo quince de fuerza.
  - "¿Cuál es tu [noun]?"           — ¿Cuál es tu clase?
  - "El [noun] es [adjective]."     — El dragón es enorme.
  - "[Verb] un/una [noun]."         — Lanza un dado para atacar.

BACKWARD COMPATIBILITY
  - Old CSVs without cloze/french_sentence columns still load without errors
  - load_words() uses .get() with empty string defaults
  - Rows without cloze data are skipped during deck building
  - validate.py treats cloze and french_sentence as optional columns

VENV ON SYSTEMS WITH OLD PYTHON
  - If default python3 is 3.8, weasyprint and other deps won't install
  - Find a newer Python: ls /opt/python/*/bin/python3
  - Create venv manually: /opt/python/3.12.11/bin/python3 -m venv ~/.local/share/calabozos-venv
  - Upgrade pip first: venv/bin/pip install --upgrade pip

ICON HANDLING
  - Icons are SVGs from game-icons.net, cached in assets/icons/
  - fetch_icons.py converts SVG → PNG bytes for Anki embedding
  - PNGs are stored in output/icons/ (separate from audio files)
  - If icon cache is empty, cards generate without icons (graceful skip)