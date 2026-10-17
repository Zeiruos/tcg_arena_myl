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
    "Onyria",
    "Libertadores",
    "Kaiju vs Mecha",
    "AyD Vigilantes",
    "Drácula",
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

# Los nombres se emiten sin tildes: el buscador de TCG Arena hace match literal
# sobre el texto, asi que "Baculo" no encuentra "Báculo de los Eternos".
# Se quita cualquier diacritico, no solo las tildes del castellano: Drácula
# trae nombres rumanos ("Vâlve Albe", "Rey de los Loçolicos") y hay cosas como
# "Martillo Mjölnir" que nadie teclea asi al buscar.
# La ñ se conserva a proposito: es una letra distinta, no un diacritico
# ("Cañón" -> "Cañon", no "Canon").
KEEP_CHARS = "ñÑ"

# La API emite muchos nombres con cada palabra en mayuscula ("Yelmo De
# Mambrino"); codicetcg, y por lo tanto las reimpresiones nuevas, los escribe
# bien ("Yelmo de Mambrino"). TCG Arena agrupa los estilos de una carta solo si
# el nombre coincide exacto, asi que los conectores se pasan a minuscula al
# emitir (salvo la primera palabra). Solo cambia mayusculas, nunca la ortografia.
LOWER_WORDS = {
    "de", "del", "la", "las", "el", "los", "y", "e", "en", "a", "al", "con",
    "por", "para", "o", "u", "un", "una", "su", "sus", "sin", "sobre",
}

GAME_FILE = "Game_Mitos_y_Leyendas.json"

# Agrupacion de sets en temporadas para el campo "Set".
#
# TCG Arena renderiza un filtro como dropdown solo si el campo tiene pocos
# valores unicos; con los 17 titulos de set reales caia a campo de texto libre.
# Agrupando en 5 temporadas el filtro vuelve a ser dropdown, igual que "race"
# (10 valores). El titulo de set real se conserva en el campo "Edicion", que
# se emite como string (no array) para que sea busqueda por texto.
#
# La temporada de un set es la de su dragon de frecuencia (el emblema junto a
# la caja de texto), no la de su fecha de salida: los mazos precon salieron con
# AyD pero llevan el dragon de KvM. Las impresiones sueltas con un dragon
# distinto al de su set se corrigen por nombre en vigencia_cartas.json.
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
    "IMP - Mazo Dragón": "Kaiju vs Mecha",
    "IMP - Mazo Eterno": "Kaiju vs Mecha",
    "IMP - Mazo Guerrero": "Kaiju vs Mecha",
    "IMP - Drácula: Rey Vampiro": "Drácula",
    "IMP - Drácula: Rey Vampiro - Inmortales": "Drácula",
    "IMP - Drácula: Cazadores Nocturnos": "Drácula",
    "IMP - Drácula: Hijos de la Noche": "Drácula",
    "IMP - Drácula: Carmilla la Condesa": "Drácula",
    "IMP - Drácula: Ruthven el Vampiro": "Drácula",
    "IMP - Promociones CasaMyL 2026": "Drácula",
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


def strip_accents(text):
    """Quita los diacriticos (tildes, dieresis, ç...), conservando la ñ. Ver KEEP_CHARS."""
    return "".join(
        ch if ch in KEEP_CHARS else "".join(
            c for c in unicodedata.normalize("NFD", ch) if unicodedata.category(c) != "Mn")
        for ch in (text or "")
    )


def lower_connectors(name):
    """Conectores en minuscula salvo al inicio: "El Rey Y El Verdugo" -> "El Rey y el Verdugo"."""
    words = (name or "").split(" ")
    for i in range(1, len(words)):
        core = words[i].strip(".,:;!?\"'()")
        if core and core.lower() in LOWER_WORDS and core != core.lower():
            words[i] = words[i].replace(core, core.lower(), 1)
    return " ".join(words)


def normalize_name(name):
    """Clave de comparacion de nombres: sin tildes, sin puntuacion, minusculas."""
    n = unicodedata.normalize("NFD", name or "")
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", n.lower())


def load_vigencia(path):
    """Carga las excepciones de vigencia: por nombre normalizado y por ID."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {path} no encontrado, todas las cartas rotan con su set.")
        return {"nombre": {}, "id": {}}
    return {
        "nombre": {normalize_name(k): v for k, v in data.get("vigencia", {}).items()},
        "id": dict(data.get("vigencia_por_id", {})),
    }


def vigencia_for(card_id, nombre, set_title, vigencias):
    """Temporada con la que rota una carta, o INMORTAL si no rota nunca.

    La vigencia se declara por NOMBRE y la heredan todas las impresiones: una
    reimpresion con un dragon de frecuencia mas nuevo extiende la vida de todas
    sus copias anteriores. Sin excepcion declarada, la carta rota con su set.
    El override por ID manda sobre el nombre: sirve para separar cartas
    distintas que comparten nombre (p. ej. Alicanto Oro vs Alicanto Aliado).
    """
    return (vigencias["id"].get(card_id)
            or vigencias["nombre"].get(normalize_name(nombre))
            or season_for(set_title))


def season_for(set_title):
    """Temporada a la que pertenece un set. Sin mapeo, usa el titulo tal cual."""
    if set_title not in SET_TO_SEASON:
        print(f"  Warning: set sin temporada asignada en SET_TO_SEASON: {set_title!r}")
        return set_title
    return SET_TO_SEASON[set_title]


def transform_card(source_card, set_title, banlist, vigencias):
    """Transform a single source card to TCG Arena format."""
    card_id = source_card["edicion"]
    # Sin tildes y con conectores en minuscula, para que el buscador de TCG
    # Arena encuentre igual y las reimpresiones se agrupen como estilos.
    # El lookup de vigencia normaliza aparte, asi que no se ve afectado.
    nombre = lower_connectors(strip_accents(source_card["nombre"]))
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
    # La legalidad ("Única") ya se calculo sobre el texto original; el campo
    # emitido es solo para buscar, asi que va sin tildes como el nombre.
    card["ability"] = strip_accents(ability)
    # "Set" agrupa por temporada: array de pocos valores -> filtro dropdown.
    # "Edicion" guarda el set real como string -> busqueda por texto.
    # "Vigencia" es la temporada con la que rota (o Inmortal) -> dropdown.
    # Una impresion de una temporada ya rotada que sigue legal (Inmortal o
    # reimpresa) queda sin Set: asi la temporada rotada desaparece del filtro.
    season = season_for(set_title)
    card["Set"] = [season] if season in TEMPORADAS_VIGENTES else []
    card["Edicion"] = strip_accents(set_title)
    card["Vigencia"] = [vigencia_for(card_id, nombre, set_title, vigencias)]

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


def warn_unknown_types(cards):
    """Avisa de tipos de carta que el game JSON no sabe jugar (autoPlayFromHand)."""
    try:
        with open(GAME_FILE, encoding="utf-8") as f:
            game = json.load(f)
        known = set(game["gameplay"]["Classic"]["sections"]["autoPlayFromHand"])
    except (FileNotFoundError, KeyError):
        print(f"  Warning: no pude leer autoPlayFromHand de {GAME_FILE}")
        return
    unknown = {}
    for c in cards.values():
        if c["type"] not in known:
            unknown.setdefault(c["type"], []).append(c["id"])
    for tipo, ids in unknown.items():
        print(f"  Warning: tipo {tipo!r} no esta en autoPlayFromHand ({len(ids)} cartas, p.ej. {ids[0]})")


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
    print(f"  {len(vigencias['nombre'])} nombres y {len(vigencias['id'])} IDs con vigencia declarada")
    print(f"  Temporadas vigentes: {', '.join(TEMPORADAS_VIGENTES)}")

    print(f"\nProcessing source files from {CARDS_JSON_DIR}/...")
    cards = build_card_list(banlist, vigencias)

    warn_unknown_types(cards)
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
    sin_set = sum(1 for v in cards.values() if not v.get("Set") and not v.get("isToken"))
    if sin_set:
        print(f"  {sin_set:5}  (sin Set: impresiones de temporadas rotadas que siguen legales)")

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
