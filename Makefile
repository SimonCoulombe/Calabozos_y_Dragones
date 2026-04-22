# The venv lives outside the exFAT drive (no symlinks on exFAT).
# Default: ~/.local/share/calabozos-venv  — override with: make pdf VENV=~/my-venv
VENV     ?= $(HOME)/.local/share/calabozos-venv
PYTHON    = $(VENV)/bin/python
SCRIPTS   = scripts

.PHONY: all pdf anki audio icons validate setup clean help

all: validate pdf anki

setup:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q -r requirements.txt
	@echo "Setup complete. Venv at: $(VENV)"

pdf:
	PYTHONPATH=$(SCRIPTS) $(PYTHON) $(SCRIPTS)/generate_pdf.py

anki:
	PYTHONPATH=$(SCRIPTS) $(PYTHON) $(SCRIPTS)/generate_anki.py $(ANKI_FLAGS)

audio:
	PYTHONPATH=$(SCRIPTS) $(PYTHON) $(SCRIPTS)/generate_audio.py

icons:
	PYTHONPATH=$(SCRIPTS) $(PYTHON) $(SCRIPTS)/fetch_icons.py

validate:
	PYTHONPATH=$(SCRIPTS) $(PYTHON) $(SCRIPTS)/validate.py

clean:
	rm -f output/pdfs/*.pdf
	rm -f output/anki/*.apkg
	rm -f output/audio/*.wav
	rm -f output/audio/*.mp3

help:
	@echo "First time setup:  make setup"
	@echo ""
	@echo "make pdf       - Generate El Libro del Aventurero PDF"
	@echo "make anki      - Generate Anki decks for both children"
	@echo "make audio     - Pre-generate all TTS audio files"
	@echo "make icons     - Pre-cache all game-icons.net SVGs"
	@echo "make validate  - Validate all CSV and YAML files"
	@echo "make all       - validate + pdf + anki"
	@echo "make clean     - Remove all generated output files"
	@echo ""
	@echo "Override venv:  make pdf VENV=~/my-other-venv"
