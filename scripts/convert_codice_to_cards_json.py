#!/usr/bin/env python3
"""
Convierte un dump de codicetcg al formato de cards_json/.

Se usa para las ediciones que api.myl.cl todavia no publica. Necesita dos
archivos guardados a mano desde la libreria de codicetcg (formato Imperio):

    --json  la respuesta XHR con todas las cartas ({"cards", "dictionaries"}).
            Trae mas cartas de las que interesan.
    --html  la pagina de la libreria con el filtro de Edicion aplicado a las
            ediciones nuevas. Es la fuente de verdad de QUE cartas entran: se
            convierten solo las del JSON cuya imagen aparece en el HTML.

Usage:
    python scripts/convert_codice_to_cards_json.py
    python scripts/convert_codice_to_cards_json.py --json DUMP.json --html DUMP.html

Al final imprime un reporte de nombres que ya existen en cards_json/. Una
reimpresion (mismo texto, o el mismo con errata de redaccion) es la misma
carta; si extiende o no la vigencia lo decide su dragon de frecuencia, que hay
que revisar a ojo con revisar_dragones.py. Una carta distinta con el mismo
nombre rota con su propio set.
"""

import argparse
import difflib
import glob
import html
import json
import re
import sys
import unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # raiz del repo (el script vive en scripts/)
OUT_DIR = ROOT / "cards_json"
DEFAULT_JSON = ROOT.parent / "dump_json_codice_upto_dracula.json"
DEFAULT_HTML = ROOT.parent / "dump_html_codice_dracula.html"

# Edicion de codice -> (prefijo de ID, slug del archivo, titulo).
# Toda la linea Drácula comparte una sola numeracion (001-256) entre el set
# principal, los kits y los Inmortales, asi que comparten prefijo de ID. Es la
# misma numeracion lineal que api.myl.cl uso para AyD Vigilantes: si la API
# publica Drácula, deberia bastar con cambiar las URLs de imagen.
# Una edicion nueva hay que agregarla aqui; el script se niega a adivinarla.
EDITIONS = {
    173: ("PROMOS_CASAMYL_2026", "promos_casamyl_2026", "IMP - Promociones CasaMyL 2026"),
    174: ("DRACULA", "dracula_cazadores_nocturnos", "IMP - Drácula: Cazadores Nocturnos"),
    175: ("DRACULA", "dracula_hijos_de_la_noche", "IMP - Drácula: Hijos de la Noche"),
    176: ("DRACULA", "dracula_carmilla_la_condesa", "IMP - Drácula: Carmilla la Condesa"),
    177: ("DRACULA", "dracula_ruthven_el_vampiro", "IMP - Drácula: Ruthven el Vampiro"),
    178: ("DRACULA", "dracula_rey_vampiro", "IMP - Drácula: Rey Vampiro"),
    903: ("DRACULA", "dracula_rey_vampiro_inmortales", "IMP - Drácula: Rey Vampiro - Inmortales"),
}

# Las ediciones >= 900 son el lote de Inmortales de cada temporada. Vienen sin
# rareza (la carta impresa dice "INMDRAC-021", sin letra).
INMORTALES_MIN_EDITION = 900
RAREZA_INMORTAL = "IM"

# Errores de codice verificados contra la imagen de la carta, por id "u".
NAME_FIXES = {
    "178_039": "Vâlve Negre",           # codice: "Välve"
    "178_109": "Nocturlabio de Llull",  # codice: "Liull"
    # Oro sin habilidad de la edicion. Codice lo llama "Drácula", igual que el
    # Oro UR de Onyria que sigue vigente: con el mismo nombre TCG Arena los
    # agruparia como estilos de una sola carta. Mismo criterio que
    # "Kaiju Vs Mecha Titanes": nombre completo de la edicion.
    "178_135": "Drácula Rey Vampiro",
    # Otra carta que el Jonathan Harker de Onyria, que sigue vigente.
    "178_126": "Jonathan Harker (Drácula)",
}
TYPE_FIXES = {
    # Codice los tiene como Talismán sin coste; impresos son Oros.
    "176_170": "Oro",   # Libro de Enoc
    "177_178": "Oro",   # Bastón de la Bestia
    "177_184": "Oro",   # Muñeco Vudú
}
COST_FIXES = {
    "174_143": 1,   # Psicofonía
    "176_160": 1,   # Seducción
    "176_166": 0,   # Sacrificio Solar
    "178_128": 0,   # Carruaje Infernal
}
RACE_FIXES = {
    "178_126": "Caballero/Héroe",   # Jonathan Harker: codice no trae la raza
}
RARITY_FIXES = {
    "178_135": "P",   # impresa "DRAC 001 P"; codice dice "O"
}
# Typos de codice en las habilidades, verificados contra la carta impresa.
# Globales (se repiten en varias cartas) y por carta.
TEXT_FIXES = [
    (r"\bprevien\b", "prevén"),
    (r"\bPreven\b", "Prevén"),
    (r"\bjúgalo\b", "juégalo"),
    (r"\bTótems\b", "Tótem"),   # el plural impreso es invariable
]
ABILITY_FIXES = {
    "174_144": [("tope de tu Castillo", "tope de un Castillo")],   # Romualdito
    "176_169": [("coste en tu Oro", "coste en un Oro")],           # Pan de Muerto
    "178_253": [("en el mano", "en la mano")],                     # Hacha de Seth
}
# Aliados sin raza verificados como Sin Raza real (igual que sus impresiones
# anteriores en api.myl.cl), para que no salten en el warning.
SIN_RAZA_OK = {
    "175_155",   # La Catrina
    "178_250",   # Nanna
}

# Ids de raza de codice que no son razas: 0 "Sin raza", 100 "No aplica".
NO_RACE_IDS = {0, 100}


def load_html_images(path):
    """URLs de imagen (sin query string) de las cartas que muestra el HTML."""
    text = Path(path).read_text(encoding="utf-8")
    urls = re.findall(r'<img[^>]*?src="(https://codicetcg\.b-cdn\.net/[^"?]+)', text)
    return {html.unescape(u) for u in urls}


def clean_text(v):
    """Normaliza texto libre: quita espacios sobrantes al final de linea."""
    if v is None:
        return None
    v = v.replace("\r\n", "\n").replace("\r", "\n")
    v = "\n".join(line.rstrip() for line in v.split("\n")).strip()
    return v or None


def fix_ability(u, text):
    if text is None:
        return None
    for pattern, repl in TEXT_FIXES:
        text = re.sub(pattern, repl, text)
    for old, new in ABILITY_FIXES.get(u, []):
        if old not in text:
            # Si codice corrige el typo, el fix sobra: mejor enterarse.
            print(f"  Warning: {u}: ABILITY_FIXES no encontro {old!r}")
        text = text.replace(old, new)
    return text


def convert_card(card, dicts):
    u = card["u"]
    edition = card["e"]
    prefix = EDITIONS[edition][0]

    tipo = TYPE_FIXES.get(u) or dicts["t"][str(card["t"])]
    raza = None
    if tipo == "Aliado":
        races = [dicts["r"][str(r)] for r in card.get("r") or [] if r not in NO_RACE_IDS]
        raza = RACE_FIXES.get(u) or "/".join(races) or None

    coste = COST_FIXES.get(u, card["c"])
    rareza = RARITY_FIXES.get(u) or card["f"]
    if rareza is None and edition >= INMORTALES_MIN_EDITION:
        rareza = RAREZA_INMORTAL

    out = OrderedDict()
    out["nombre"] = NAME_FIXES.get(u, card["n"])
    out["tipo"] = tipo
    out["raza"] = raza
    out["coste"] = coste
    out["fuerza"] = card["z"]
    out["edicion"] = f"{prefix}-{card['d']:03d}"
    out["frecuencia"] = rareza
    out["descripcion"] = None
    out["habilidad"] = fix_ability(u, clean_text(card["h"]))
    # Provisorio: CDN de codice (archivo original, sin parametros de resize
    # para no gatillar transformaciones en su optimizador).
    out["imagen_url"] = card["i"]
    return out


def warn_suspicious(card, out):
    """Avisa de los patrones que en Drácula resultaron ser errores de codice."""
    u = card["u"]
    if out["tipo"] == "Aliado" and not out["raza"] and u not in SIN_RAZA_OK:
        print(f"  Warning: {u} {out['nombre']!r}: Aliado sin raza (verificar si es Sin Raza real)")
    if out["tipo"] != "Oro" and out["coste"] is None:
        print(f"  Warning: {u} {out['nombre']!r}: {out['tipo']} sin coste (en Drácula eran Oros mal tipados o costes perdidos)")


def unify_alt_prints(cartas):
    """Las versiones alternativas repiten el texto de su impresion base.

    Codice transcribe las Legendarias/Secretas alternativas en MAYUSCULAS o
    con typos ("mejor" por "menor", "Roba" por "Bota"). Mismo nombre y mismas
    estadisticas dentro del lote = misma carta, asi que todas toman el texto
    de la impresion de menor numero.
    """
    base = {}
    unified = 0
    for c in sorted(cartas, key=lambda c: c["edicion"]):
        key = (c["nombre"], c["tipo"], c["coste"], c["fuerza"], c["raza"])
        if key not in base:
            base[key] = c
        elif c["habilidad"] != base[key]["habilidad"]:
            c["habilidad"] = base[key]["habilidad"]
            unified += 1
    if unified:
        print(f"  {unified} versiones alternativas toman el texto de su impresion base")


def write_set(path, codigo, slug, titulo, cartas):
    data = OrderedDict()
    data["edicion"] = OrderedDict([
        ("codigo", codigo),
        ("slug", slug),
        ("titulo", titulo),
        ("fecha_lanzamiento", None),
    ])
    data["total_cartas"] = len(cartas)
    data["cartas"] = cartas
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  {path.name}: {len(cartas)} cartas")


def text_key(text):
    """Clave para comparar habilidades: sin tildes, puntuacion ni espacios."""
    n = unicodedata.normalize("NFD", text or "")
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", n.lower())


def card_key(c):
    return (c["tipo"], c["coste"] or 0, c["fuerza"] or 0, text_key(c["habilidad"]))


def report_same_names(new_cards, new_files):
    """Compara contra las cartas existentes con el mismo nombre."""
    existing = defaultdict(list)
    for f in sorted(glob.glob(str(OUT_DIR / "*.json"))):
        if Path(f).name in new_files:
            continue
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        for c in data["cartas"]:
            existing[text_key(c["nombre"])].append(c)

    same, different = [], []
    seen = set()
    for c in new_cards:
        k = text_key(c["nombre"])
        if k not in existing or k in seen:
            continue
        seen.add(k)
        olds = existing[k]
        if any(card_key(o) == card_key(c) for o in olds):
            same.append(c["nombre"])
        else:
            best = max(olds, key=lambda o: difflib.SequenceMatcher(
                None, text_key(o["habilidad"]), text_key(c["habilidad"])).ratio())
            ratio = difflib.SequenceMatcher(
                None, text_key(best["habilidad"]), text_key(c["habilidad"])).ratio()
            different.append((c["nombre"], best["edicion"], ratio))

    print(f"\nNombres que ya existian en cards_json/: {len(same) + len(different)}")
    print(f"  Reimpresiones identicas ({len(same)}) — revisar su dragon: {', '.join(sorted(same))}")
    # En Drácula las erratas dieron similitud 0.82-0.97 y las cartas distintas
    # 0.02-0.35. Es solo una pista: decidir mirando el texto.
    print(f"  Mismo nombre, otro texto ({len(different)}) — errata = misma carta; si no, rota por separado:")
    for nombre, old_id, ratio in sorted(different, key=lambda x: -x[2]):
        hint = "probable errata" if ratio > 0.6 else "probable carta distinta"
        print(f"    {nombre} (vs {old_id}, similitud {ratio:.2f})  <- {hint}")


def main():
    parser = argparse.ArgumentParser(description="Convierte un dump de codicetcg a cards_json/")
    parser.add_argument("--json", default=DEFAULT_JSON, help="respuesta XHR de codicetcg")
    parser.add_argument("--html", default=DEFAULT_HTML, help="pagina de la libreria con el filtro aplicado")
    args = parser.parse_args()

    with open(args.json, encoding="utf-8") as f:
        dump = json.load(f)
    dicts = dump["dictionaries"]
    wanted = load_html_images(args.html)

    selected = [c for c in dump["cards"] if c["i"] in wanted]
    missing = wanted - {c["i"] for c in selected}
    print(f"HTML: {len(wanted)} cartas, encontradas en el JSON: {len(selected)}")
    if missing:
        print(f"Error: {len(missing)} imagenes del HTML no estan en el JSON, p.ej. {sorted(missing)[:3]}")
        sys.exit(1)
    unknown = sorted({c["e"] for c in selected if c["e"] not in EDITIONS})
    if unknown:
        names = [dicts["e"].get(str(e), "?") for e in unknown]
        print(f"Error: ediciones sin entrada en EDITIONS: {list(zip(unknown, names))}")
        sys.exit(1)

    by_edition = defaultdict(list)
    converted = []
    for card in selected:
        out = convert_card(card, dicts)
        warn_suspicious(card, out)
        by_edition[card["e"]].append(out)
        converted.append(out)
    unify_alt_prints(converted)

    print("\nEscribiendo cards_json/...")
    new_files, new_cards = set(), []
    for edition, cartas in sorted(by_edition.items()):
        _, slug, titulo = EDITIONS[edition]
        cartas.sort(key=lambda c: c["edicion"])
        codigo = f"CODICE{edition}"
        name = f"{codigo}_{slug}.json"
        write_set(OUT_DIR / name, codigo, slug, titulo, cartas)
        new_files.add(name)
        new_cards.extend(cartas)

    ids = [c["edicion"] for c in new_cards]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if dups:
        print(f"Error: IDs repetidos: {dups}")
        sys.exit(1)

    report_same_names(new_cards, new_files)


if __name__ == "__main__":
    main()
