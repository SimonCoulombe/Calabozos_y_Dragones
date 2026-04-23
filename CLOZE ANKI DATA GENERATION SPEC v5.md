CLOZE ANKI DATA GENERATION SPEC v5

GOAL
Transform a Spanish → French D&D vocabulary CSV into Anki-ready cloze deletion cards.

Each card must:

test Spanish recall (production)
include a visible French meaning cue
use exactly one canonical sentence per concept
support multi-word expressions safely
avoid ambiguity and guessing between similar words

INPUT CSV FORMAT

spanish,french,category,icon,tags,notes,hint_sentence

FIELD DEFINITIONS

spanish

target concept
may be single word or multi-word expression
may include gender pairs separated by slash:
example: el mago / la maga
example: el humano / la humana
example: la clase de armadura

french

direct translation of spanish
may also include gender variants

category

grouping label

icon

UI only

tags

filtering / metadata

notes

MUST contain a full natural D&D-style sentence
this is the canonical sentence used for:
PDF output
audio generation
base sentence for cloze generation
MUST NOT contain cloze markup
MUST be grammatically complete

hint_sentence

identical to notes
BUT with French translation of the target word appended in parentheses at the end
used as the FRONT display sentence in Anki

Example:
La maga elfa lanza un hechizo en la mazmorra (magicienne)

GENDER HANDLING RULES

If spanish contains a gender pair (X / Y):

treat as a single concept
split internally into variants:
masculine form and feminine form
BUT CSV remains ONE row

Example:
el mago / la maga

Internal representation:

M: el mago → le magicien
F: la maga → la magicienne

Only ONE sentence is stored in notes per row.
Do not duplicate sentence columns.

Sentence should usually use ONE grammatical form consistently (typically feminine or masculine based on dataset consistency rules).

Adjectives must agree with sentence subject gender.

Example:
peligroso / peligrosa

El monstruo es peligroso
La misión es peligrosa

ANKI OUTPUT STRUCTURE

From each CSV row generate:

CLOZE FIELD (Text)
Derived from hint_sentence by replacing ONLY the target expression from spanish with:
{{c1::TARGET}}
FRONT DISPLAY
Show cloze sentence with French hint already present in parentheses.
BACK
Must include:
Spanish answer (exact matched span from spanish field)
full sentence from notes
audio indicator (sentence-level audio)

CLOZE GENERATION RULES

Use deterministic span matching only.
Do NOT use fuzzy matching.

MULTI-WORD TARGET HANDLING (CRITICAL)

Spanish may contain multi-word expressions:
example:
la clase de armadura
los puntos de golpe

RULE 1: Exact phrase match only

must match full sequence of words exactly as written in spanish field
no partial matching allowed

RULE 2: Token sequence match

split sentence and target into tokens
find exact contiguous sequence match

RULE 3: Article inclusion
If article is part of expression (el/la/los/las):

it MUST be included in cloze span

Correct:
{{c1::la clase de armadura}}

Incorrect:
{{c1::clase de armadura}}

RULE 4: Longest match priority
If multiple overlapping matches exist:

choose longest valid match

RULE 5: No substring matching
Do not match inside other words or partial overlaps.

RULE 6: Failure rule
If exact match does not exist in sentence:

reject row (do not guess or modify sentence)

CLOZE EXAMPLE OUTPUTS

Single word:
El guerrero saca su {{c1::espada}} del cinturón (épée)

Multi-word:
El guerrero tiene {{c1::la clase de armadura}} alta (classe d'armure)

Gender pair:
La {{c1::maga}} elfa lanza un hechizo en la mazmorra (magicienne)

AUDIO RULE

audio MUST be generated from notes only
no cloze text
no blanks
full natural sentence only

DO NOT DO

do not store cloze markup in CSV
do not create multiple sentence columns
do not split CSV rows for gender variants
do not guess missing words
do not use partial matching for multi-word expressions
do not remove French hint from front sentence

DESIGN INTENT

This system enforces:

controlled Spanish recall via cloze deletion
always-visible French meaning disambiguation
stable multi-word expression handling
deterministic matching (no NLP guessing)
D&D immersive contextual sentences
consistent learning signal across entire deck

---

IMPLEMENTATION NOTES (v5.1 — lessons learned)

ACTUAL CSV FORMAT IMPLEMENTED

spanish,french,category,icon,tags,notes,cloze,french_sentence

Key change from original spec: cloze markup IS stored directly in CSV in a `cloze` column.
The original spec said "do not store cloze markup in CSV" but this was impractical —
storing it directly is easier to author, debug, and process.

The `hint_sentence` column was renamed to `cloze` to reflect that it contains {{c1::}} markup.
A new `french_sentence` column was added for the French translation of the full sentence.

CLOZE COLUMN FORMAT

French hint goes FIRST, then the cloze sentence:
  (magicienne) La {{c1::maga}} elfa lanza un hechizo.

NOT at the end. This way the learner sees the hint immediately when the card appears.

ANKI CARD LAYOUT

FRONT:
  (épée) El guerrero saca su _____ del cinturón.

BACK:
  espada                              ← Spanish answer (bold, large)
  El guerrero saca su espada del cinturón.   ← full Spanish sentence
  Le guerrier sort son épée de la ceinture.  ← full French sentence
  🔊 audio of full Spanish sentence (when .wav available)

ANKI MODEL

Uses genanki.Model.CLOZE with model_type parameter.
Model name: "Calabozos Cloze v2"
Model ID: stable_id("model-calabozos-cloze-v2")

Fields: Text, Spanish, FullSentence, FrenchSentence, Audio, Icon, Category, Session
- Text = cloze column from CSV (contains {{c1::}} markup + french hint)
- Spanish = spanish column
- FullSentence = notes column
- FrenchSentence = french_sentence column

GENDER PAIR RULES (CLARIFIED)

When spanish contains "el X / la Y":
- Merge into ONE CSV row
- Pick ONE gender for the example sentence (randomly or consistently)
- In the cloze, wrap ONLY the noun (not the article): El {{c1::guerrero}} humano...
- The `spanish` field keeps both forms: el guerrero / la guerrera

When spanish is a single-gender noun with article (el personaje, la fuerza):
- Cloze may or may not include the article depending on sentence structure
- For "Tengo trece de fuerza" → wrap just "fuerza" (article not in sentence)
- For "Voy a comprar el equipo" → wrap "el equipo" (article is part of expression)

SCRIPT USAGE

  # Generate only theme_01 cards (for testing):
  PYTHONPATH=scripts python scripts/generate_anki.py --no-tts --only theme_01

  # Generate all cards:
  PYTHONPATH=scripts python scripts/generate_anki.py --no-tts

  # With TTS (when server is available):
  PYTHONPATH=scripts python scripts/generate_anki.py

FILE ORGANIZATION

- Audio files: output/audio/*.wav
- Icon PNGs: output/icons/icon_*.png (NOT in audio dir)
- Anki decks: output/anki/calabozos_child_*.apkg

BACKWARD COMPATIBILITY

Old CSVs without `cloze` and `french_sentence` columns still load without errors.
When using --only filter, rows without cloze data are skipped.
validate.py treats cloze and french_sentence as optional columns.

COMMON PITFALLS

1. Sentences must contain the EXACT target word from the spanish field.
   "mi personaje" does NOT match "el personaje" — rewrite the sentence.
2. Plural forms don't match singular: "jugadores" ≠ "el jugador" — rewrite.
3. For phrases like "la clase de armadura (CA)" — drop the parenthetical from spanish field.
4. DictWriter quoting: use csv module to write, not manual string concatenation.
5. When processing CSVs with heredoc (cat << EOF), commas inside fields are fine
   because CSV fields with special chars get auto-quoted by csv.DictWriter.