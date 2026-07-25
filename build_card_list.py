#!/usr/bin/env python3
"""
Build script: transforms source card data (cards_json/) into TCG Arena format (myl_card_list.json).

Usage:
    python build_card_list.py                  # outputs to myl_card_list_build.json
    python build_card_list.py --output FILE    # outputs to custom file
    python build_card_list.py --replace        # overwrites myl_card_list.json directly

Inputs:
    - cards_json/*.json     : per-set card data scraped from api.myl.cl
    - myl_banlist.json      : legality overrides (banned, limited, mercenary)

Output:
    - myl_card_list_build.json (or custom path): aggregated card list in TCG Arena format
"""

import json
import glob
import argparse
import re
import sys
import unicodedata
from collections import OrderedDict

# --- Constants ---

CARDS_JSON_DIR = "cards_json"
BANLIST_FILE = "myl_banlist.json"
VIGENCIA_FILE = "vigencia_cartas.json"
DEFAULT_OUTPUT = "myl_card_list_build.json"
REPLACE_OUTPUT = "myl_card_list.json"

# Temporadas legales actualmente. Para ejecutar una rotacion basta con sacar la
# temporada de esta lista y regenerar: las cartas cuya vigencia sea esa temporada
# desaparecen del card list, y las marcadas "inmortal" sobreviven siempre.
# Los archivos de cards_json/ NO se borran: quedan como historico.
TEMPORADAS_VIGENTES = [
    "Bestiarium",
    "Onyria",
    "Libertadores",
    "Kaiju vs Mecha",
    "AyD Vigilantes",
]

INMORTAL = "Inmortal"

# Known races for splitting compound race strings
KNOWN_RACES = [
    "Bestia", "Caballero", "Dragón", "Dragon", "Eterno",
    "Faerie", "Guerrero", "Héroe", "Heroe", "Sacerdote", "Sombra",
]

# Fix known typos in source data: source_value -> corrected_value
RACE_FIXES = {
    "Dragon": "Dragón",
    "Heroe": "Héroe",
}

# Fix known typos in card types
TYPE_FIXES = {
    "Talisman": "Talismán",
    "Totem": "Tótem",
}

# Agrupacion de sets en temporadas para el campo "Set".
#
# TCG Arena renderiza un filtro como dropdown solo si el campo tiene pocos
# valores unicos; con los 17 titulos de set reales caia a campo de texto libre.
# Agrupando en 5 temporadas el filtro vuelve a ser dropdown, igual que "race"
# (10 valores). El titulo de set real se conserva en el campo "Edicion", que
# se emite como string (no array) para que sea busqueda por texto.
SET_TO_SEASON = {
    "IMP - Bestiarium": "Bestiarium",
    "IMP - Secretos Arcanos": "Bestiarium",
    "IMP - Lootbox Imperio 2024": "Bestiarium",
    "IMP - Hielo Inmortal": "Bestiarium",
    "IMP - Cenizas de Fuego": "Bestiarium",
    "IMP - Onyria": "Onyria",
    "IMP - Libertadores": "Libertadores",
    "IMP - Kaiju vs Mecha - Titanes": "Kaiju vs Mecha",
    "IMP - Toolkit 2026": "Kaiju vs Mecha",
    "IMP - Chile Oculto": "Kaiju vs Mecha",
    "IMP - Escuadrón Mecha": "Kaiju vs Mecha",
    "25 Aniversario": "Kaiju vs Mecha",
    "KVM JO": "Kaiju vs Mecha",
    "IMP - AyD Vigilantes": "AyD Vigilantes",
    "IMP - Mazo Dragón": "AyD Vigilantes",
    "IMP - Mazo Eterno": "AyD Vigilantes",
    "IMP - Mazo Guerrero": "AyD Vigilantes",
}

# Gold generation patterns in ability text (no spaces, as stored)
GOLD_GEN_1 = ["generaunoro"]
GOLD_GEN_2 = ["generadosoros"]

# Token card definition
ORO_VIRTUAL_ID = "ORO_VIRTUAL"
ORO_VIRTUAL_CARD = {
    "id": ORO_VIRTUAL_ID,
    "isToken": True,
    "face": {
        "front": {
            "name": "Oro Virtual",
            "type": "Oro",
            "cost": 0,
            "image": "https://api.myl.cl/static/cards/125/337.png",
            "isHorizontal": False
        }
    },
    "name": "Oro Virtual",
    "type": "Oro",
    "cost": 0,
    "Vigencia": ["Inmortal"]
}


def load_banlist(path):
    """Load banlist file. Returns dict with sets of card IDs per category."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {path} not found, all cards will be legal.")
        return {"legalityCode": "IR", "banned": set(), "limited_1": set(),
                "limited_2": set(), "mercenary": set()}

    return {
        "legalityCode": data.get("legalityCode", "IR"),
        "banned": set(data.get("banned", [])),
        "limited_1": set(data.get("limited_1", [])),
        "limited_2": set(data.get("limited_2", [])),
        "mercenary": set(data.get("mercenary", [])),
    }


_RACE_WARNINGS = set()


def warn_race(card_id, raza, problema):
    """Avisa una vez por combinacion de raza malformada + problema."""
    if (raza, problema) in _RACE_WARNINGS:
        return
    _RACE_WARNINGS.add((raza, problema))
    donde = f" ({card_id})" if card_id else ""
    print(f"  Warning: raza {raza!r}{donde}: {problema}")


def parse_race(raza, tipo, card_id=None):
    """Convert source raza to TCG Arena race array.

    Avisa de razas malformadas en cards_json/: el separador canonico es "/" y
    la ortografia debe ser la de RACE_FIXES (con tilde). El parser las absorbe
    igual, pero hay que corregirlas en el origen — si no, un scrape nuevo las
    vuelve a introducir en silencio.
    """
    if raza is None or raza == "":
        if tipo == "Aliado":
            return ["Sin Raza"]
        return []

    # Split by "/" first (e.g. "Caballero/Guerrero/Héroe")
    if "/" in raza:
        races = [r.strip() for r in raza.split("/")]
    else:
        # Some source data uses spaces instead of "/" (e.g. "Dragon Sombra")
        # Match known races within the string
        races = [r for r in KNOWN_RACES if r in raza]
        if len(races) > 1:
            warn_race(card_id, raza, "separador de multi-raza debe ser '/'")
        if not races:
            warn_race(card_id, raza, "raza desconocida (no esta en KNOWN_RACES)")
            races = [raza]

    # Apply typo fixes
    for r in races:
        if r in RACE_FIXES:
            warn_race(card_id, raza, f"{r!r} deberia escribirse {RACE_FIXES[r]!r}")
    races = [RACE_FIXES.get(r, r) for r in races]
    return races


def transform_ability(habilidad):
    """Remove spaces and newlines from ability text for search compatibility."""
    if not habilidad:
        return ""
    return habilidad.replace(" ", "").replace("\n", "").replace("\r", "")


def detect_gold_generation(ability_no_spaces):
    """Detect how many virtual gold tokens a card generates."""
    ab = ability_no_spaces.lower()
    for pattern in GOLD_GEN_2:
        if pattern in ab:
            return 2
    for pattern in GOLD_GEN_1:
        if pattern in ab:
            return 1
    return 0


def compute_legality(card_id, ability_no_spaces, banlist):
    """Compute _legal field for a card."""
    code = banlist["legalityCode"]

    # Priority: banned > limited_1 > limited_2 > mercenary > única > default
    if card_id in banlist["banned"]:
        return {code: False}
    if card_id in banlist["limited_1"]:
        return {code: 1}
    if card_id in banlist["limited_2"]:
        return {code: 2}
    if card_id in banlist["mercenary"]:
        return {code: 50}

    # Auto-detect Única keyword
    ab = ability_no_spaces
    if "Única" in ab or "única" in ab:
        return {code: 1}

    return {code: True}


def normalize_name(name):
    """Clave de comparacion de nombres: sin tildes, sin puntuacion, minusculas."""
    n = unicodedata.normalize("NFD", name or "")
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", n.lower())


def load_vigencia(path):
    """Carga las excepciones de vigencia, indexadas por nombre normalizado."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {path} no encontrado, todas las cartas rotan con su set.")
        return {}
    return {normalize_name(k): v for k, v in data.get("vigencia", {}).items()}


def vigencia_for(nombre, set_title, vigencias):
    """Temporada con la que rota una carta, o INMORTAL si no rota nunca.

    La vigencia se declara por NOMBRE y la heredan todas las impresiones: una
    reimpresion en un set nuevo puede extender la vida de todas sus copias
    anteriores. Sin excepcion declarada, la carta rota con su propio set.
    """
    return vigencias.get(normalize_name(nombre)) or season_for(set_title)


def season_for(set_title):
    """Temporada a la que pertenece un set. Sin mapeo, usa el titulo tal cual."""
    if set_title not in SET_TO_SEASON:
        print(f"  Warning: set sin temporada asignada en SET_TO_SEASON: {set_title!r}")
        return set_title
    return SET_TO_SEASON[set_title]


def transform_card(source_card, set_title, banlist, vigencias):
    """Transform a single source card to TCG Arena format."""
    card_id = source_card["edicion"]
    nombre = source_card["nombre"]
    tipo = TYPE_FIXES.get(source_card["tipo"], source_card["tipo"])
    raza = source_card.get("raza")
    coste = source_card.get("coste")
    fuerza = source_card.get("fuerza")
    frecuencia = source_card.get("frecuencia")
    habilidad = source_card.get("habilidad")
    imagen_url = source_card.get("imagen_url")

    # Transform fields
    face_cost = 0 if coste is None else coste
    ability = transform_ability(habilidad)
    race = parse_race(raza, tipo, card_id)
    strength = 0 if fuerza is None else fuerza

    # Build card
    card = OrderedDict()
    card["id"] = card_id
    card["isToken"] = False
    card["face"] = {
        "front": {
            "name": nombre,
            "type": tipo,
            "cost": face_cost,
            "image": imagen_url,
            "isHorizontal": False
        }
    }
    card["name"] = nombre
    card["type"] = tipo
    card["cost"] = face_cost
    card["_legal"] = compute_legality(card_id, ability, banlist)
    card["race"] = race
    card["rarity"] = frecuencia
    card["strength"] = strength
    card["ability"] = ability
    # "Set" agrupa por temporada: array de pocos valores -> filtro dropdown.
    # "Edicion" guarda el set real como string -> busqueda por texto.
    # "Vigencia" es la temporada con la que rota (o Inmortal) -> dropdown.
    card["Set"] = [season_for(set_title)]
    card["Edicion"] = set_title
    card["Vigencia"] = [vigencia_for(nombre, set_title, vigencias)]

    # Gold token generation
    gold_count = detect_gold_generation(ability)
    if gold_count > 0:
        card["tokens"] = [ORO_VIRTUAL_ID] * gold_count

    return card_id, card


def build_card_list(banlist, vigencias):
    """Build the complete card list from source files."""
    cards = OrderedDict()
    rotadas = 0

    source_files = sorted(glob.glob(f"{CARDS_JSON_DIR}/*.json"))
    if not source_files:
        print(f"Error: no source files found in {CARDS_JSON_DIR}/")
        sys.exit(1)

    for filepath in source_files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        set_title = data["edicion"]["titulo"]

        incluidas = 0
        for source_card in data["cartas"]:
            card_id, card = transform_card(source_card, set_title, banlist, vigencias)
            # Una carta sale del pool cuando su temporada de vigencia ya roto.
            if card["Vigencia"][0] not in TEMPORADAS_VIGENTES + [INMORTAL]:
                rotadas += 1
                continue
            cards[card_id] = card
            incluidas += 1

        total = data["total_cartas"]
        extra = "" if incluidas == total else f"  ({total - incluidas} rotadas)"
        print(f"  {set_title}: {incluidas} cards{extra}")

    if rotadas:
        print(f"\n{rotadas} cartas excluidas por rotacion de temporada")

    # Add ORO_VIRTUAL token
    cards[ORO_VIRTUAL_ID] = ORO_VIRTUAL_CARD

    return cards


def main():
    parser = argparse.ArgumentParser(description="Build TCG Arena card list from source data")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help=f"Output file (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--replace", "-r", action="store_true", help=f"Overwrite {REPLACE_OUTPUT} directly")
    args = parser.parse_args()

    output_path = REPLACE_OUTPUT if args.replace else args.output

    print(f"Loading banlist from {BANLIST_FILE}...")
    banlist = load_banlist(BANLIST_FILE)

    print(f"Loading vigencia from {VIGENCIA_FILE}...")
    vigencias = load_vigencia(VIGENCIA_FILE)
    print(f"  {len(vigencias)} nombres con vigencia declarada")
    print(f"  Temporadas vigentes: {', '.join(TEMPORADAS_VIGENTES)}")

    print(f"\nProcessing source files from {CARDS_JSON_DIR}/...")
    cards = build_card_list(banlist, vigencias)

    print(f"\nTotal cards: {len(cards)} (including {ORO_VIRTUAL_ID} token)")

    # Stats
    legal_stats = {"true": 0, "false": 0, "1": 0, "2": 0, "50": 0}
    code = banlist["legalityCode"]
    for v in cards.values():
        ir = v.get("_legal", {}).get(code)
        if ir is True:
            legal_stats["true"] += 1
        elif ir is False:
            legal_stats["false"] += 1
        elif ir == 1:
            legal_stats["1"] += 1
        elif ir == 2:
            legal_stats["2"] += 1
        elif ir == 50:
            legal_stats["50"] += 1

    print(f"Legality: legal={legal_stats['true']}, banned={legal_stats['false']}, "
          f"limited_1={legal_stats['1']}, limited_2={legal_stats['2']}, "
          f"mercenary={legal_stats['50']}")

    # Gold token stats
    gold_cards = sum(1 for v in cards.values() if "tokens" in v)
    print(f"Gold generators: {gold_cards} cards with token creation")

    # Temporadas (campo "Set"): pocas para que el filtro salga como dropdown
    seasons = {}
    for v in cards.values():
        for s in v.get("Set", []):
            seasons[s] = seasons.get(s, 0) + 1
    print(f"\nTemporadas ({len(seasons)} valores en el filtro Set):")
    for name, n in sorted(seasons.items(), key=lambda x: -x[1]):
        print(f"  {n:5}  {name}")

    # Vigencia: con que temporada rota cada carta (Inmortal = no rota nunca)
    vig = {}
    for v in cards.values():
        for s in v.get("Vigencia", []):
            vig[s] = vig.get(s, 0) + 1
    print(f"\nVigencia ({len(vig)} valores en el filtro):")
    for name, n in sorted(vig.items(), key=lambda x: -x[1]):
        print(f"  {n:5}  {name}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to: {output_path}")


if __name__ == "__main__":
    main()
