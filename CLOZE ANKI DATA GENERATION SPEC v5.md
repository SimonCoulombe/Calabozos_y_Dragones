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