#!/usr/bin/env python3
"""Generate El Libro del Aventurero PDF from vocabulary CSVs and grammar YAMLs."""

import csv
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

BASE = Path(__file__).parent.parent
VOCAB_DIR = BASE / "vocabulary"
TEMPLATE_DIR = BASE / "templates"
CONFIG_FILE = BASE / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_session_csv(path: Path) -> dict:
    """Load a session CSV and return a session dict for the template."""
    session_num = path.stem.split("_")[1]
    raw_title = path.stem.split("_", 2)[2] if len(path.stem.split("_")) > 2 else ""
    title = f"Séance {int(session_num)} — {raw_title.replace('_', ' ').title()}"

    words = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            words.append({
                "spanish": row.get("spanish", "").strip(),
                "french": row.get("french", "").strip(),
                "category": row.get("category", "").strip(),
                "icon": row.get("icon", "").strip(),
                "tags": row.get("tags", "").strip(),
                "notes": row.get("notes", "").strip(),
            })

    return {"title": title, "subtitle": "", "framing": "", "words": words}


SESSION_TITLES = {
    "00": ("Séance 0 — ¿Quién eres tú ?", "Créer ton personnage"),
    "01": ("Séance 1 — La Tienda", "Acheter de l'équipement"),
    "02": ("Séance 2 — El Camino", "Voyager et se battre"),
    "03": ("Séance 3 — La Misión", "Recevoir une quête"),
    "04": ("Séance 4 — La Mazmorra", "Explorer le donjon"),
    "05": ("Séance 5 — El Jefe", "Affronter le boss"),
}

SESSION_FRAMINGS = {
    "00": "Avant de partir à l'aventure, tu dois créer ton personnage. Réponds aux questions du Maître de Donjon en espagnol !",
    "01": "Tu arrives en ville avec de l'or mais sans équipement. Le marchand ne parle qu'espagnol — nomme ce que tu veux acheter !",
    "02": "Sur la route, tu dois décrire ce que tu vois, entends et fais. En espagnol, bien sûr !",
    "03": "Un vieil homme t'aborde dans la taverne. Il a besoin d'aide. Comprends sa mission et pose tes questions.",
    "04": "L'obscurité t'entoure. Tu dois explorer, trouver des trésors et éviter les pièges — en décrivant tout en espagnol.",
    "05": "Le boss final attend. Tout ce que tu as appris va servir dans ce combat épique !",
}


def load_grammar() -> dict:
    grammar_dir = VOCAB_DIR / "grammar"
    grammar = {}

    for name, key in [
        ("regular_verbs.yaml", "regular_verbs"),        
        ("dnd_verbs.yaml", "dnd_verbs"),        
        ("ser_estar.yaml", "ser_estar"),
        ("hacer_tener.yaml", "hacer_tener"),        
        ("ir_poder_hay.yaml", "ir_poder_hay"),        
        ("colors.yaml", "colors")
    ]:
        p = grammar_dir / name
        if p.exists():
            with open(p, encoding="utf-8") as f:
                grammar[key] = yaml.safe_load(f)

    return grammar


REFERENCE_TITLES = {
    "reference_races":     ("Las Razas y las Clases",   "Todas las razas y clases jugables"),
    "reference_equipment": ("El Equipo del Aventurero", "Armas, armaduras y equipo básico"),
    "reference_spells":    ("Los Hechizos",             "Hechizos comunes y escuelas de magia"),
    "reference_enemies":   ("Los Enemigos",             "Monstruos comunes"),
    "reference_lugares":   ("Los Lugares",              "Lugares, edificios y zonas por explorar"),
    "reference_numbers":   ("Los Números",              "1 → 20 — ¡para tirar los dados!"),
    "reference_colors":   ("Los Colores",             "¡Describe tu equipo!"),
    "reference_adjectives": ("Otros Adjetivos",         "Adjetivos útiles para describir el mundo"),
    "reference_mis_palabras":   ("Mis Palabras",              "Mis nuevas palabras"),    
}


def load_reference_tables() -> list[dict]:
    tables = []
    for stem, (title, subtitle) in REFERENCE_TITLES.items():
        p = VOCAB_DIR / f"{stem}.csv"
        if not p.exists():
            continue
        words = []
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("spanish", "").strip():
                    words.append({
                        "spanish": row.get("spanish", "").strip(),
                        "french":  row.get("french",  "").strip(),
                        "category": row.get("category", "").strip(),
                        "notes":   row.get("notes",   "").strip(),
                    })
        tables.append({"title": title, "subtitle": subtitle, "words": words})
    return tables


def main() -> int:
    config = load_config()
    out_dir = BASE / config["output"]["pdf_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(VOCAB_DIR.glob("session_*.csv"))
    if not csv_files:
        print("ERROR: no session CSV files found in vocabulary/")
        return 1

    sessions = []
    for p in csv_files:
        s = load_session_csv(p)
        num = p.stem.split("_")[1]
        if num in SESSION_TITLES:
            s["title"], s["subtitle"] = SESSION_TITLES[num]
            s["framing"] = SESSION_FRAMINGS.get(num, "")
        sessions.append(s)

    grammar = load_grammar()
    reference_tables = load_reference_tables()

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    env.filters["chunks"] = lambda lst, n: [lst[i:i + n] for i in range(0, len(lst), n)]
    template = env.get_template("livre_aventurier.html")

    html_content = template.render(
        campaign=config["campaign"],
        sessions=sessions,
        grammar=grammar,
        reference_tables=reference_tables,
    )

    out_path = out_dir / "livre_aventurier.pdf"
    HTML(string=html_content, base_url=str(BASE)).write_pdf(
        str(out_path), finisher=_pdf_finisher
    )
    print(f"  PDF  →  {out_path}")
    return 0


def _pdf_finisher(document, pdf) -> None:
    """Inject viewer preferences directly into the pydyf PDF catalog."""
    pdf.catalog["PageLayout"] = "/OneColumn"
    pdf.catalog["PageMode"] = "/UseNone"


if __name__ == "__main__":
    sys.exit(main())
