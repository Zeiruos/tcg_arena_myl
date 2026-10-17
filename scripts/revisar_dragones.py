#!/usr/bin/env python3
"""
Arma hojas de contacto con el dragon de frecuencia de cada carta de codicetcg.

La vigencia de una impresion la define su dragon de frecuencia (el emblema
junto a la caja de texto), no el producto en que salio: una reimpresion puede
traer el dragon de su edicion original. Ningun dato textual lo dice (ni
codicetcg ni api.myl.cl), asi que se revisa a ojo. El color del anillo indica
la frecuencia; lo que importa es el simbolo:

    Bestiarium      dragon alado en S, moneda lisa
    Onyria          busto de dragon con melena, anillo dorado con flores de lis
    Libertadores    dragon dentro de una corona de laureles
    Kaiju vs Mecha  cabeza de robot (tambien los mazos precon)
    AyD Vigilantes  cabeza de dragon blanca, angulosa
    Drácula         murcielago

Las promos y artes alternativos a veces traen logos especiales (fenix JO,
"25 Años", estrella SP, Rapa Nui...): esos se ignoran y se usa el dragon de las
otras impresiones de la misma carta.

Usage:
    python scripts/revisar_dragones.py 174 175 176 177          # ediciones de codicetcg
    python scripts/revisar_dragones.py 178 --desde 135 --hasta 197
    python scripts/revisar_dragones.py 173 --json DUMP.json --out hojas/

Las imagenes se bajan una vez (variante de 300 px que su sitio ya sirve, para
no gatillar transformaciones nuevas en su CDN) y quedan en cache.
"""

import argparse
import json
import subprocess
import urllib.parse
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent   # raiz del repo (el script vive en scripts/)
DEFAULT_JSON = ROOT.parent / "dump_json_codice_upto_dracula.json"
CACHE = ROOT.parent / "cache_imagenes_codice"
QUERY = "?width=300&height=422&format=webp&quality=85&fit=cover"

COLS, CELL_W, CELL_H, CROP = 10, 124, 150, (120, 124)
PER_SHEET = 60


def fetch(card):
    path = CACHE / f"{card['u']}.webp"
    if not path.exists() or path.stat().st_size < 2000:
        url = urllib.parse.quote(card["i"], safe=":/'")   # hay URLs con espacios
        subprocess.run(["curl", "-s", "-m", "40", "-o", str(path), url + QUERY], check=True)
    return Image.open(path).convert("RGB")


def emblem(img):
    """Recorte del rincon del emblema. Cubre los distintos marcos (kits, precon,
    promos), pero lo bastante ajustado para que el simbolo se lea: con recortes
    mas chicos un dragon de Onyria sobre anillo verde se confunde con el robot."""
    w, h = img.size
    return img.crop((int(.72 * w), int(.70 * h), int(.995 * w), int(.96 * h))).resize(CROP)


def write_sheet(cards, out):
    rows = (len(cards) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * CELL_W, rows * CELL_H), "white")
    draw = ImageDraw.Draw(sheet)
    for n, card in enumerate(cards):
        x, y = (n % COLS) * CELL_W, (n // COLS) * CELL_H
        sheet.paste(emblem(fetch(card)), (x + 2, y + 2))
        draw.text((x + 2, y + 127), f"{card['u']} {card['f'] or ''}", fill="black")
        draw.text((x + 2, y + 138), card["n"][:18], fill="black")
    sheet.save(out)
    print(f"  {out}: {len(cards)} cartas")


def main():
    parser = argparse.ArgumentParser(description="Hojas de dragones de frecuencia para revision visual")
    parser.add_argument("ediciones", nargs="+", type=int, help="ids de edicion de codicetcg")
    parser.add_argument("--json", default=DEFAULT_JSON, help="respuesta XHR de codicetcg")
    parser.add_argument("--desde", type=int, default=0, help="numero de carta minimo")
    parser.add_argument("--hasta", type=int, default=10**6, help="numero de carta maximo")
    parser.add_argument("--out", default=".", help="carpeta de salida")
    args = parser.parse_args()

    with open(args.json, encoding="utf-8") as f:
        cards = json.load(f)["cards"]
    sel = [c for c in cards if c["e"] in args.ediciones and args.desde <= c["d"] <= args.hasta]
    sel.sort(key=lambda c: (c["e"], c["d"]))
    CACHE.mkdir(exist_ok=True)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"{len(sel)} cartas")
    for i in range(0, len(sel), PER_SHEET):
        write_sheet(sel[i:i + PER_SHEET], out / f"dragones_{i // PER_SHEET:02d}.png")


if __name__ == "__main__":
    main()
