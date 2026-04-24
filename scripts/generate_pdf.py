#!/usr/bin/env python3
"""Generate El Libro del Aventurero PDF from vocabulary CSVs and grammar YAMLs."""

import base64
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
ICONS_DIR = BASE / "assets" / "icons"


def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _icon_to_data_uri(icon_ref: str) -> str | None:
    """Convert a cached SVG icon to a base64 data URI for embedding in HTML.

    icon_ref is either 'author/filename.svg' or bare 'filename'.
    """
    if not icon_ref:
        return None
    svg_path = ICONS_DIR / icon_ref
    if not svg_path.exists():
        return None
    try:
        svg_bytes = svg_path.read_bytes()
        b64 = base64.b64encode(svg_bytes).decode("ascii")
        return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        return None


def load_session_csv(path: Path) -> dict:
    """Load a theme CSV and return a session dict for the template."""
    theme_num = path.stem.split("_")[1]
    raw_title = path.stem.split("_", 2)[2] if len(path.stem.split("_")) > 2 else ""
    title = f"Tema {int(theme_num)} — {raw_title.replace('_', ' ').title()}"

    words = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            icon_ref = row.get("icon", "").strip()
            icon_uri = _icon_to_data_uri(icon_ref)
            words.append({
                "spanish": row.get("spanish", "").strip(),
                "french": row.get("french", "").strip(),
                "category": row.get("category", "").strip(),
                "icon": icon_ref,
                "icon_uri": icon_uri,
                "tags": row.get("tags", "").strip(),
                "notes": row.get("notes", "").strip(),
            })

    return {"title": title, "subtitle": "", "framing": "", "words": words}


SESSION_TITLES = {
    "01": ("Tema 1 — ¡Hola, aventurero!", "Les bases pour survivre à la table"),
    "02": ("Tema 2 — Mi Personaje", "Créer ton personnage"),
    "03": ("Tema 3 — La Tienda", "Acheter de l'équipement"),
    "04": ("Tema 4 — La Misión", "Poser des questions et accepter une quête"),
    "05": ("Tema 5 — El Camino", "Voyager, explorer et demander son chemin"),
    "06": ("Tema 6 — El Jefe", "Explorer le donjon, combattre et vaincre le boss"),
}

SESSION_FRAMINGS = {
    "01": "Avant de partir à l'aventure, apprends à dire bonjour, à te présenter et à poser des questions simples en espagnol !",
    "02": "Tu crées ton personnage. Choisis ta race et ta classe — en espagnol, bien sûr !",
    "03": "Tu arrives en ville avec de l'or mais sans équipement. Le marchand ne parle qu'espagnol — nomme ce que tu veux acheter !",
    "04": "Un vieil homme t'aborde dans la taverne. Il a besoin d'aide — pose-lui des questions pour comprendre sa mission !",
    "05": "Tu pars en voyage ! Décris ce que tu vois, demande ton chemin et explore le monde — en espagnol !",
    "06": "Tu entres dans le donjon du boss. Explore les salles, bats les monstres et affronte le boss final !",
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
    "reference_attributes": ("Los Atributos",           "Les caractéristiques de ton personnage"),
    "reference_game_words": ("Palabras del Juego",       "Le vocabulaire des mécaniques de jeu"),
    "reference_races":     ("Las Razas y las Clases",   "Todas las razas y clases jugables"),
    "reference_equipment": ("El Equipo del Aventurero", "Armas, armaduras y equipo básico"),
    "reference_spells":    ("Los Hechizos",             "Hechizos comunes y escuelas de magia"),
    "reference_enemies":   ("Los Enemigos",             "Monstruos comunes"),
    "reference_lugares":   ("Los Lugares",              "Lugares, edificios y zonas por explorar"),
    "reference_numbers":   ("Los Números",              "1 → 20, 50, 100, 1000"),
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
                    icon_ref = row.get("icon", "").strip()
                    icon_uri = _icon_to_data_uri(icon_ref)
                    words.append({
                        "spanish": row.get("spanish", "").strip(),
                        "french":  row.get("french",  "").strip(),
                        "category": row.get("category", "").strip(),
                        "icon": icon_ref,
                        "icon_uri": icon_uri,
                        "notes":   row.get("notes",   "").strip(),
                    })
        tables.append({"title": title, "subtitle": subtitle, "words": words})
    return tables


def main() -> int:
    config = load_config()
    out_dir = BASE / config["output"]["pdf_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(VOCAB_DIR.glob("theme_*.csv"))
    if not csv_files:
        print("ERROR: no theme CSV files found in vocabulary/")
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
