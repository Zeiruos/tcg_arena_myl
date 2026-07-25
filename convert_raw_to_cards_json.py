#!/usr/bin/env python3
"""
Convierte los JSON crudos de api.myl.cl (cards_raw/) al formato de cards_json/.

Formato destino:
{
  "edicion": {"codigo", "slug", "titulo", "fecha_lanzamiento"},
  "total_cartas": N,
  "cartas": [{"nombre","tipo","raza","coste","fuerza","edicion","frecuencia",
              "descripcion","habilidad","imagen_url"}]
}
"""

import json
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path

RAW_DIR = Path("/home/antonio/Documentos/proyectos_varios/tcg_arena_myl/cards_raw")
OUT_DIR = Path("/home/antonio/Documentos/proyectos_varios/tcg_arena_myl/tcg_arena_myl/cards_json")

# rarity id -> codigo corto usado en cards_json
RARITY_CODES = {
    "0": "P",    # Promocional
    "1": "L",    # Legendaria
    "2": "UR",   # Ultra Real
    "3": "MR",   # Mega Real
    "4": "R",    # Real
    "5": "C",    # Cortesano
    "6": "V",    # Vasallo
    "7": "O",    # Oro
    "8": "M",    # Milenaria
    "9": "S",    # Secreta
    "10": "F",   # Ficha
    "11": "SP",  # Set Paralelo
}

# type id -> nombre. El id "0" es dato malo de la API (una sola carta,
# "Ofrenda a los Abuelos", que por su texto y coste es un Talisman).
TYPE_NAMES = {
    "0": "Talismán",
    "1": "Aliado",
    "2": "Talismán",
    "3": "Arma",
    "4": "Tótem",
    "5": "Oro",
    "6": "Monumento",
}

# race id -> nombre, tal como los emite la propia API en su diccionario "races".
RACE_NAMES = {
    "0": None, "1": "Caballero", "2": "Bestia", "3": "Eterno", "4": "Guerrero",
    "5": "Bárbaro", "6": "Faerie", "7": "Samurái", "8": "Sombra", "9": "Ancestral",
    "10": "Sacerdote", "11": "Dragón", "12": "Héroe", "13": "Oni", "14": "Olímpico",
    "15": "Titán", "16": "Faraón", "17": "Desafiante", "18": "Defensor",
    "19": "Licántropo", "20": "Vampiro", "21": "Cazador", "22": "Chamán",
    "23": "Dios", "24": "Abominación", "25": "Kami", "26": "Xian", "27": "Criaturas",
    "28": "Campeón / Shaolín", "29": "Campeón / Ninja", "30": "Campeón / Samurái",
    "31": "Campeón", "32": "Héroe/Sacerdote", "33": "Eterno/Sombra",
    "34": "Caballero/Guerrero", "35": "Bestia/Guerrero", "36": "Caballero/Héroe",
    "37": "Dragón/Eterno", "38": "Eterno/Faerie", "39": "Paladín", "40": "Asesino",
    "41": "Tenebris", "42": "Eterno/Sacerdote", "43": "Caballero/Guerrero/Héroe",
    "44": "Bestia/Dragón/Sombra", "45": "Eterno/Faerie/Sacerdote",
    "46": "Bestia Faerie", "47": "Bestia/Sombra", "48": "Guerrero/Héroe",
    "49": "Bestia/Dragón", "50": "Guerrero/Sacerdote", "51": "Dragon Sombra",
    "52": "Eterno Héroe", "53": "Caballero Sacerdote", "54": "Faerie Sacerdote",
    "55": "Caballero Sombra",
}

# Palabras que van en minuscula dentro de un titulo (salvo la primera).
LOWER_WORDS = {
    "de", "del", "la", "las", "el", "los", "y", "a", "al", "en", "con",
    "su", "sus", "un", "una", "por", "para",
}

# El campo "name" de la API viene con los caracteres no-ASCII borrados
# ("ngel gabriel"), pero el slug conserva la letra base ("angel_gabriel").
# Reconstruimos desde el slug y luego devolvemos las tildes con este mapa.
ACCENT_FIXES = {
    # ñ perdida
    "guadana": "Guadaña", "muneco": "Muñeco", "bretana": "Bretaña",
    "senalados": "Señalados", "canon": "Cañón", "tamano": "Tamaño",
    "cienpies-sp": "Ciempiés-SP",
    # nombres propios y sustantivos con tilde
    "angel": "Ángel", "angeles": "Ángeles", "angelus": "Angelus",
    "satanas": "Satanás", "belcebu": "Belcebú", "cain": "Caín",
    "noe": "Noé", "adan": "Adán", "sem": "Sem", "cam": "Cam",
    "matusalen": "Matusalén", "lamec": "Lamec", "abadon": "Abadón",
    "dracula": "Drácula", "apofis": "Apofis", "behemot": "Behemot",
    "azi": "Azi", "raoioita": "Raoioita", "aaru": "Aaru",
    "o'higgins": "O'Higgins", "ohiggins": "O'Higgins",
    "maipu": "Maipú", "quicavi": "Quicaví", "paris": "París",
    "germain": "Germain", "john": "John",
    "huitzilin": "Huitzilín", "tempilcahue": "Tempilcahue",
    "jepresh": "Jepresh", "grisgris": "Grisgrís",
    # sustantivos comunes con tilde
    "dragon": "Dragón", "dragones": "Dragones", "leon": "León",
    "dia": "Día", "da": "Día", "azucar": "Azúcar", "corazon": "Corazón",
    "vision": "Visión", "invocacion": "Invocación", "cancion": "Canción",
    "espiritu": "Espíritu", "heroe": "Héroe", "magico": "Mágico",
    "magica": "Mágica", "ejercito": "Ejército", "tunel": "Túnel",
    "tuneles": "Túneles", "aparicion": "Aparición", "abduccion": "Abducción",
    "psicofonia": "Psicofonía", "sesion": "Sesión", "marin": "Marín",
    "jose": "José", "cesar": "César", "cesares": "Césares", "atun": "Atún",
    "rio": "Río", "arbol": "Árbol", "vudu": "Vudú", "maldicion": "Maldición",
    "escuadron": "Escuadrón", "caida": "Caída", "caido": "Caído",
    "martires": "Mártires", "ultima": "Última", "septimo": "Séptimo",
    "titan": "Titán", "titanes": "Titanes", "titanico": "Titánico",
    "paladin": "Paladín", "baculo": "Báculo", "armeria": "Armería",
    "caballeria": "Caballería", "destruccion": "Destrucción",
    "energia": "Energía", "estacion": "Estación", "fision": "Fisión",
    "guardian": "Guardián", "intervencion": "Intervención",
    "legion": "Legión", "motin": "Motín", "serafin": "Serafín",
    "serafico": "Seráfico", "supremacia": "Supremacía", "travesia": "Travesía",
    "biblioteca": "Biblioteca", "demoniaca": "Demoníaca",
    "demoniaco": "Demoníaco", "inmortal": "Inmortal", "juventud": "Juventud",
    "zombi": "Zombi", "colmillo": "Colmillo", "compendium": "Compendium",
}

# Sufijos que la API cuelga del slug para marcar variantes de impresion.
SLUG_SUFFIXES = ("_secreta_enoc", "_secreta", "_leg", "_promo", "_alt")

# Chile Oculto (165) reimprime las 21 cartas que ya existian como TMP2 con
# numeracion propia (038-058). Se conservan los IDs antiguos para no romper
# los mazos ya guardados por los usuarios, mapeando edid real -> ID antiguo.
CHILE_OCULTO_LEGACY_IDS = {
    f"{38 + i:03d}": f"CHILE_OSCURO_2-{i + 1:03d}" for i in range(21)
}

# La API no trae la raza de estos Aliados; se recupera de los datos previos o
# de otra impresion de la misma carta. Ojo: hay Aliados que son legitimamente
# Sin Raza (los Jinetes, Malevolente, Cleopatra VII...), y esos no van aqui.
RACE_OVERRIDES = {
    "CHILE_OSCURO_2-001": "Eterno/Faerie",
    "CHILE_OSCURO_2-002": "Caballero/Sombra",
    "CHILE_OSCURO_2-003": "Bestia/Guerrero",
    "CHILE_OSCURO_2-004": "Sombra",
}


def slug_to_words(slug):
    """Convierte un slug de la API en la lista de palabras del nombre."""
    s = slug.strip()
    for suf in SLUG_SUFFIXES:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    s = s.rstrip("_")
    # El slug usa "_" como separador y a veces conserva la puntuacion original.
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def titlecase(text):
    """Title Case respetando preposiciones y articulos, y aplicando tildes."""
    words = text.split(" ")
    out = []
    for i, w in enumerate(words):
        # Separa la puntuacion final para no romper el matching del acento.
        core = w.strip(".,")
        trail = w[len(core):]
        key = strip_accents(core).lower()
        fixed = ACCENT_FIXES.get(key)
        if fixed is not None:
            word = fixed
            if i > 0 and key in LOWER_WORDS:
                word = word.lower()
        elif i > 0 and core.lower() in LOWER_WORDS:
            word = core.lower()
        else:
            word = core[:1].upper() + core[1:].lower() if core else core
        out.append(word + trail)
    return " ".join(out)


def strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def build_name(card):
    """Nombre final de la carta, reconstruido desde el slug."""
    return titlecase(slug_to_words(card["slug"]))


def to_int(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def clean_text(v):
    """Normaliza texto libre: quita espacios sobrantes al final de linea."""
    if v is None:
        return None
    v = v.replace("\r\n", "\n").replace("\r", "\n")
    v = "\n".join(line.rstrip() for line in v.split("\n")).strip()
    return v or None


def convert_card(card, set_slug_upper, image_set_id, legacy_ids=None):
    """Convierte una carta cruda al formato de cards_json."""
    tipo = TYPE_NAMES[card["type"]]
    raza = RACE_NAMES.get(card["race"]) if card["race"] is not None else None
    # Solo los Aliados llevan raza en el formato destino.
    if tipo != "Aliado":
        raza = None

    edid = card["edid"]
    # El ID de carta puede diferir del numero de imagen cuando se conserva
    # la numeracion antigua de una reimpresion.
    card_id = (legacy_ids or {}).get(edid) or f"{set_slug_upper}-{edid}"
    if tipo == "Aliado" and not raza:
        raza = RACE_OVERRIDES.get(card_id)

    out = OrderedDict()
    out["nombre"] = build_name(card)
    out["tipo"] = tipo
    out["raza"] = raza
    out["coste"] = to_int(card["cost"])
    out["fuerza"] = to_int(card["damage"])
    out["edicion"] = card_id
    out["frecuencia"] = RARITY_CODES[card["rarity"]]
    out["descripcion"] = clean_text(card.get("flavour"))
    out["habilidad"] = clean_text(card.get("ability"))
    out["imagen_url"] = f"https://api.myl.cl/static/cards/{image_set_id}/{edid}.png"
    return out


def write_set(path, codigo, slug, titulo, fecha, cartas):
    data = OrderedDict()
    data["edicion"] = OrderedDict([
        ("codigo", codigo),
        ("slug", slug),
        ("titulo", titulo),
        ("fecha_lanzamiento", fecha),
    ])
    data["total_cartas"] = len(cartas)
    data["cartas"] = cartas
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  {path.name}: {len(cartas)} cartas")


def load_raw(name):
    with open(RAW_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def main():
    print("Convirtiendo sets simples...")
    # (archivo raw, id de set, slug destino, nombre de archivo)
    simple = [
        ("chile_oculto_raw.json", "165", "CHILE_OCULTO", "165_chile_oculto.json",
         CHILE_OCULTO_LEGACY_IDS),
        ("ayd_vigilantes_raw.json", "166", "AYD_VIGILANTES", "166_ayd_vigilantes.json", None),
        ("mazo_imp_dragon_raw.json", "168", "MAZO_IMP_DRAGON", "168_mazo_imp_dragon.json", None),
        ("mazo_imp_eterno_raw.json", "169", "MAZO_IMP_ETERNO", "169_mazo_imp_eterno.json", None),
        ("mazo_guerrero_raw.json", "170", "MAZO_IMP_GUERRERO", "170_mazo_imp_guerrero.json", None),
    ]
    for raw_name, set_id, slug_upper, out_name, legacy in simple:
        raw = load_raw(raw_name)
        ed = raw["edition"]
        cartas = [convert_card(c, slug_upper, set_id, legacy) for c in raw["cards"]]
        cartas.sort(key=lambda c: c["edicion"])
        write_set(OUT_DIR / out_name, set_id, ed["slug"], ed["title"],
                  ed["date_release"], cartas)

    # Los sets 163 y 164 son un unico toolkit numerado 001-036 que la API
    # publica partido en dos ediciones con cartas repetidas. Se fusionan
    # deduplicando por edid, conservando el set de origen de cada imagen.
    print("Fusionando toolkit 2026 (163 + 164)...")
    merged = {}
    for raw_name, set_id in [("dia_de_muertos_raw.json", "163"),
                             ("ritual_vudu_raw.json", "164")]:
        raw = load_raw(raw_name)
        for c in raw["cards"]:
            if c["edid"] not in merged:
                merged[c["edid"]] = convert_card(c, "TOOLKIT_26_IMPERIO", set_id)
    cartas = sorted(merged.values(), key=lambda c: c["edicion"])
    write_set(OUT_DIR / "163_toolkit_2026.json", "163", "toolkit_2026",
              "IMP - Toolkit 2026", "2026-04-28", cartas)


if __name__ == "__main__":
    main()
