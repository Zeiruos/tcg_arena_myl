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
import sys
from collections import OrderedDict

# --- Constants ---

CARDS_JSON_DIR = "cards_json"
BANLIST_FILE = "myl_banlist.json"
DEFAULT_OUTPUT = "myl_card_list_build.json"
REPLACE_OUTPUT = "myl_card_list.json"

# Known races for splitting compound race strings
KNOWN_RACES = [
    "Bestia", "Caballero", "Dragón", "Dragon", "Eterno",
    "Faerie", "Guerrero", "Héroe", "Sacerdote", "Sombra",
]

# Fix known typos in source data: source_value -> corrected_value
RACE_FIXES = {
    "Dragon": "Dragón",
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
    "cost": 0
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


def parse_race(raza, tipo):
    """Convert source raza to TCG Arena race array."""
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
        if not races:
            races = [raza]

    # Apply typo fixes
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


def transform_card(source_card, set_title, banlist):
    """Transform a single source card to TCG Arena format."""
    card_id = source_card["edicion"]
    nombre = source_card["nombre"]
    tipo = source_card["tipo"]
    raza = source_card.get("raza")
    coste = source_card.get("coste")
    fuerza = source_card.get("fuerza")
    frecuencia = source_card.get("frecuencia")
    habilidad = source_card.get("habilidad")
    imagen_url = source_card.get("imagen_url")

    # Transform fields
    face_cost = 0 if coste is None else coste
    ability = transform_ability(habilidad)
    race = parse_race(raza, tipo)
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
    card["cost"] = coste
    card["_legal"] = compute_legality(card_id, ability, banlist)
    card["race"] = race
    card["rarity"] = frecuencia
    card["strength"] = strength
    card["ability"] = ability
    card["Set"] = [set_title]

    # Gold token generation
    gold_count = detect_gold_generation(ability)
    if gold_count > 0:
        card["tokens"] = [ORO_VIRTUAL_ID] * gold_count

    return card_id, card


def build_card_list(banlist):
    """Build the complete card list from source files."""
    cards = OrderedDict()

    source_files = sorted(glob.glob(f"{CARDS_JSON_DIR}/*.json"))
    if not source_files:
        print(f"Error: no source files found in {CARDS_JSON_DIR}/")
        sys.exit(1)

    for filepath in source_files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        set_title = data["edicion"]["titulo"]
        total = data["total_cartas"]

        for source_card in data["cartas"]:
            card_id, card = transform_card(source_card, set_title, banlist)
            cards[card_id] = card

        print(f"  {set_title}: {total} cards")

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

    print(f"Processing source files from {CARDS_JSON_DIR}/...")
    cards = build_card_list(banlist)

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

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to: {output_path}")


if __name__ == "__main__":
    main()
