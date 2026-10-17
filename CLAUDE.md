# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repo builds a custom game definition for **Mitos y Leyendas** (MyL), a Chilean trading card game, targeting the **TCG Arena** platform. TCG Arena is a web-based simulator that loads custom games from publicly-hosted JSON files. There is no build system, no tests, and no application code — the project is pure JSON data.

## Key Files

- **`Game_Mitos_y_Leyendas.json`** — The main game definition file. Configures board layout, gameplay rules (mulligan, turns, sections), deck building formats, and points to the card list URL. Structure is documented in `GAME_JSON_DOCS.md`.
- **`myl_card_list.json`** — Aggregated card list in TCG Arena format (keyed by `{SET}-{NUM}` IDs). This is the file referenced by `cards.dataUrl` in the game JSON and consumed directly by TCG Arena. **Generated file — do NOT edit by hand.** Regenerate via `build_card_list.py`.
- **`cards_json/`** — Per-set card data scraped from `api.myl.cl`. Files are named `{code}_{slug}.json` (e.g., `125_espiritu_samurai.json`). These are the **source data** used to generate `myl_card_list.json`. Sets the API doesn't publish yet come from codicetcg and are named `CODICE{edicion}_{slug}.json` (the number is codice's edition id, not the API's).
- **`convert_codice_to_cards_json.py`** — Converts a codicetcg dump into `cards_json/`. See "Agregar una edición desde codicetcg" below.
- **`convert_raw_to_cards_json.py`** — Record of the July 2026 conversion from raw `api.myl.cl` dumps. **Do not re-run it as is**: `cards_json/` has had manual fixes since (names the API corrupted or got wrong, types, races) and it would overwrite them.
- **`vigencia_cartas.json`** — Per-name rotation overrides (Inmortal / season), plus per-ID overrides. See "Vigencia y rotación".
- **`revisar_dragones.py`** — Builds contact sheets of each card's frequency dragon from a codicetcg dump, for visual review of rotation.
- **`myl_banlist.json`** — Source of truth for format legality (banned / limited_1 / limited_2 / mercenary lists, keyed by card ID). Consumed by `build_card_list.py` to populate the `_legal` field on each card.
- **`build_card_list.py`** — Build script that transforms `cards_json/*.json` + `myl_banlist.json` into `myl_card_list.json`. Run with `--replace` to overwrite the published file in place.
- **`GAME_JSON_DOCS.md`** — Complete field-by-field documentation of the Game JSON schema, extracted from the TCG Arena Custom Game Builder UI. Enriched with fields discovered from Riftbound, Magic the Gathering, and Yu-Gi-Oh examples.

## Data Pipeline

1. Card data is scraped per-set into `cards_json/{code}_{slug}.json` (source format with fields: nombre, tipo, raza, coste, fuerza, frecuencia, habilidad, imagen_url).
2. `build_card_list.py` reads `cards_json/` + `myl_banlist.json` and emits `myl_card_list.json` (target format with fields: id, isToken, face.front.{name,type,cost,image,isHorizontal}, name, type, cost, _legal, race, rarity, strength, ability, Set, Edicion, Vigencia).
3. `type` in TCG Arena format is the bare card type (`Aliado`, `Arma`, `Oro`, `Talismán`, `Tótem`) — the race is **not** part of it. These values must match the keys of `autoPlayFromHand` in the game JSON.
4. The race travels in a separate `race` array, built by `parse_race()`: multi-race strings are split on `/` (e.g. `"Bestia/Dragón"` → `["Bestia", "Dragón"]`). In `cards_json/` the separator must always be `/` and the spelling must match `KNOWN_RACES` (with tildes: `Dragón`, `Héroe`, `Talismán`). Variants written with a space (`"Bestia Faerie"`) still parse via substring matching against `KNOWN_RACES`, but they are a bug in the source data — fix them in `cards_json/` rather than relying on the fallback.
5. Card names are emitted **without accents** (`name` and `face.front.name`): the TCG Arena search box matches literally, so `Báculo` was unfindable typing `Baculo`. `strip_accents()` handles it at build time — the source data in `cards_json/` keeps the name as printed, so a re-scrape never has to be patched. Every diacritic is dropped (NFD), not just Spanish tildes: `"Martillo Mjölnir"` → `"Martillo Mjolnir"`, `"Rey de los Loçolicos"` → `"Rey de los Locolicos"`. Only `ñ` is preserved (`"Cañón"` → `"Cañon"`, see `KEEP_CHARS`). The searchable `ability` and `Edicion` fields are stripped the same way (legality's "Única" check runs on the original text first).
6. Names also get their connectors lowercased (`lower_connectors()`, `LOWER_WORDS`): the API writes "Yelmo De Mambrino" while codicetcg — and therefore new reprints — write "Yelmo de Mambrino", and TCG Arena only groups prints as styles when the name matches exactly. Only casing changes, never spelling.

## Updating the banlist

Edit `myl_banlist.json` (never edit `_legal` fields directly in `myl_card_list.json`) and then regenerate:

```
python build_card_list.py --replace
```

Categories in `myl_banlist.json` map to `_legal` values as follows (priority: `banned` > `limited_1` > `limited_2` > `mercenary` > auto-detect "Única" in ability text > default `true`):

| Category    | `_legal` value | Meaning                |
|-------------|----------------|------------------------|
| `banned`    | `false`        | Prohibida              |
| `limited_1` | `1`            | Única (1 copia)        |
| `limited_2` | `2`            | Restringida a 2 copias |
| `mercenary` | `50`           | Mercenaria (ilimitada) |

When moving a card between categories, remove it from the previous list — a card ID should only appear in one category. Reprints (same name, different set codes) must each be added individually if they share a restriction.

## Set / Edicion: agrupacion por temporada

TCG Arena solo renderiza un filtro como **dropdown** si el campo tiene pocos valores
unicos; pasado cierto umbral (entre 10 y 17, verificado en julio 2026) degrada a campo
de texto libre aunque el valor siga siendo un array. Con los 17 titulos de set reales,
el filtro `Set` no era dropdown.

Por eso `build_card_list.py` emite dos campos distintos:

| Campo     | Tipo   | Contenido                          | Filtro     |
|-----------|--------|------------------------------------|------------|
| `Set`     | array  | Temporada vigente (5 valores)      | dropdown   |
| `Edicion` | string | Titulo real del set (24 valores)   | texto      |

El mapeo set → temporada vive en `SET_TO_SEASON` dentro de `build_card_list.py`.
**Al agregar un set nuevo hay que anadirlo ahi**, o el build avisa con un warning y
usa el titulo tal cual (lo que sube la cardinalidad y puede romper el dropdown).
Mantener el numero de temporadas bajo — idealmente <= 10, como `race`.

`Set` solo lista temporadas de `TEMPORADAS_VIGENTES`. Una impresión de una temporada
ya rotada que sigue legal (Inmortal o reimpresa en algo vigente) sale con `Set: []`:
así la temporada rotada desaparece del dropdown, y el set real sigue en `Edicion`.
Las mantenidas no se pierden: se encuentran por `Vigencia` o sin filtro de Set.

## Vigencia y rotación

Cada carta impresa lleva un **dragón de frecuencia**: el emblema redondo junto a la
caja de texto. El símbolo dice con qué temporada rota esa impresión; el color del
anillo solo indica la frecuencia (rareza). Manda el dragón, no la fecha ni el
producto: los mazos precon salieron con AyD pero llevan el dragón de KvM, y muchas
reimpresiones en productos nuevos traen el dragón de su edición original.

| Símbolo | Temporada |
|---------|-----------|
| Dragón alado en S, moneda lisa | Bestiarium |
| Busto de dragón con melena, anillo dorado con flores de lis | Onyria |
| Dragón en corona de laureles | Libertadores |
| Cabeza de robot | Kaiju vs Mecha (incluye Escuadrón Mecha, Toolkit 2026, Chile Oculto y los precon) |
| Cabeza de dragón blanca y angulosa | AyD Vigilantes |
| Murciélago | Drácula |

**La vigencia de una carta es la del dragón más reciente entre todas sus impresiones**,
y la heredan todas sus copias. Una reimpresión solo extiende la vida de las anteriores
si trae un dragón más nuevo. Ejemplos:
- Signo Amarillo es de Bestiarium, pero rota con KvM por su impresión en los precon.
- Tamales o Visión de Enoc se reimprimieron en Drácula con su dragón original
  (KvM y AyD), así que no se extienden.

Las promos y artes alternativos a veces traen **logos especiales** (fénix JO,
"25 Años", estrella SP, Rapa Nui, escudo chileno, dragón asiático…). Se ignoran y
se usa el dragón de las otras impresiones de la misma carta; si no hay otras, rota
con su set.

Ningún dato textual lo dice: codicetcg no lo trae (salvo `nv: true` en algunas JO/SP)
y las fechas `date_empire_valid` de la API son por edición y no siempre calzan (los
precon figuran con la fecha de AyD). Se revisa a ojo con `revisar_dragones.py`.

`vigencia_cartas.json` declara la vigencia **por nombre de carta**:

| Valor | Significado |
|-------|-------------|
| `Inmortal` | No rota nunca |
| nombre de temporada | Rota cuando esa temporada rote |
| (ausente del archivo) | Rota con la temporada de su propio set (`SET_TO_SEASON`) |

Solo hace falta una entrada cuando alguna impresión no rotaría con el dragón más
reciente de la carta. `vigencia_por_id` manda sobre el nombre; sirve para separar
cartas distintas que comparten nombre.

Cada carta emite `Vigencia` (array) en el card list, que va en `mainFilters` como
dropdown — permite ver de un vistazo qué cartas se van en la próxima rotación.

### Mismo nombre: ¿reimpresión o carta distinta?

Pueden existir cartas distintas con el mismo nombre. Regla:

- **Mismo texto**, o el mismo con **errata** de redacción (Tamales, Fuego
  Purificador, Visión de Enoc…) → es la misma carta, y el diseño anterior sigue
  siendo válido. Su vigencia se calcula con todas sus impresiones.
- **Carta completamente distinta** (Zmeoaica de Bestiarium y la de Drácula, Moloch y
  Gog de Bestiarium y AyD…) → cada una rota con su propio set y **no** se declara su
  nombre. Si las dos siguen vigentes, TCG Arena las mostraría como estilos de una
  sola carta, así que se le pone un sufijo a la que menos se usa: "Alicanto (Aliado)"
  (vs el Oro de los precon) y "Jonathan Harker (Drácula)" (vs el de Onyria). Se
  decide caso por caso con el usuario. `vigencia_por_id` queda disponible si alguna
  vez hace falta separarlas sin renombrar.
- Antes de concluir que son cartas distintas, revisar el nombre impreso: la API
  puso nombres equivocados a cartas enteras. "Principe Orion" de Onyria era Ismael,
  "Rlyeh" era Casa de Opio y "Vuelo Mágico" era Polvo de Hadas. Cruzar por texto
  contra codicetcg dentro de la misma edición destapa esos casos.

`convert_codice_to_cards_json.py` imprime esta clasificación al final.

### Inmortales

Cada temporada trae un lote de ~50 Inmortales (en codicetcg, las ediciones 900+:
"Bestiarium - Inmortales", "Drácula: Rey Vampiro - Inmortales"…). El lote cambia de
una temporada a otra, pero **los Inmortales se acumulan y nunca rotan**: si un nombre
estuvo en algún lote, es `Inmortal` para siempre, aunque el lote siguiente no lo
incluya. Al agregar una temporada, los nombres nuevos de su lote se suman como
`Inmortal`. Sus impresiones vienen sin rareza (la carta dice "INMDRAC-021"): en
`cards_json/` llevan `frecuencia: "IM"`.

### Ejecutar una rotación

Editar `TEMPORADAS_VIGENTES` en `build_card_list.py`, quitar la temporada que rota
y regenerar. **Los archivos de `cards_json/` no se borran** — el filtro es por
vigencia, así que las inmortales y las reimpresas sobreviven automáticamente y no
quedan cartas huérfanas. Después de rotar hay que limpiar de `myl_banlist.json`
los IDs que ya no existen (el build no falla, pero quedan entradas muertas).

Ojo con las 5 entradas `Bestiarium` (Behemot, Ereshkigal, Rey de Amarillo…): no
sobran aunque Bestiarium ya rotó. Esas cartas tienen reimpresiones JO/SP en sets
vigentes que traen el dragón de Bestiarium; sin la entrada, esas copias
sobrevivirían con la temporada de su set.

Fuentes del dato en `vigencia_cartas.json`: las 126 inmortales son la unión de los
lotes de Inmortales de Bestiarium, Onyria, AyD Vigilantes y Drácula; el resto sale de
la revisión visual de los dragones de todas las impresiones de codicetcg (octubre 2026).

## Agregar una edición desde codicetcg

Cuando `api.myl.cl` todavía no publica una edición (así entró Drácula, octubre 2026):

1. En la librería de codicetcg (formato Imperio), filtrar por las ediciones nuevas y
   guardar la página (HTML) y la respuesta XHR con las cartas (JSON). El JSON trae más
   cartas de las que interesan; **el HTML filtrado es la fuente de verdad** de qué
   cartas entran.
2. Agregar las ediciones nuevas a `EDITIONS` en `convert_codice_to_cards_json.py`
   (prefijo de ID, slug, título) y correr
   `python convert_codice_to_cards_json.py --json DUMP.json --html DUMP.html`.
3. Revisar los warnings (Aliado sin raza, no-Oro sin coste) y el reporte de nombres
   repetidos contra la imagen de la carta. Los datos de codicetcg traen errores: en
   Drácula hubo Oros tipados como Talismán, costes perdidos, una raza faltante, typos
   en nombres ("Liull" por "Llull") y en habilidades. Se corrigen en los diccionarios
   `*_FIXES` del script, no a mano en `cards_json/`, para que una reconversión no los
   pierda.
4. Revisar el dragón de cada carta nueva con `python revisar_dragones.py <ediciones>`
   (arma hojas con los emblemas; las imágenes quedan en caché en
   `../cache_imagenes_codice`). Mirar sobre todo las reimpresiones, los kits y las
   promos. Actualizar `vigencia_cartas.json`: los nombres nuevos del lote de
   Inmortales → `Inmortal`; una reimpresión con el dragón nuevo → la temporada nueva;
   con un dragón viejo → nada, o su temporada si la impresión nueva quedaría
   rotando con el set nuevo; una carta nueva con dragón de otra temporada → esa
   temporada.
5. En `build_card_list.py`: los títulos nuevos en `SET_TO_SEASON` y la temporada en
   `TEMPORADAS_VIGENTES` (más la rotación que toque).
6. Regenerar, limpiar del banlist los IDs muertos y revisar que las reimpresiones de
   cartas restringidas compartan la restricción.

Las imágenes quedan apuntando al CDN de codicetcg (`codicetcg.b-cdn.net`, webp de
~150 KB). Es provisorio: codicetcg se financia con donaciones, y si la API oficial
publica la edición conviene cambiar a sus URLs. Los IDs siguen la numeración
lineal de codicetcg (la misma que usó la API para AyD Vigilantes), así que en
principio basta con cambiar `imagen_url`.

## Important Conventions

- Section names in the game JSON use `_` instead of spaces (e.g., `Oro_Pagado`).
- The `name` field in `Game_Mitos_y_Leyendas.json` must never change once shared — user-saved decks are keyed by it.
- Card IDs follow the pattern `{SET_SLUG}-{3-digit number}` (e.g., `ESPIRITU_SAMURAI-001`).
- The repo is served as-is by GitHub Pages, which runs Jekyll and turns every `.md` into a page. Internal docs (`CLAUDE.md`, `GAME_JSON_DOCS.md`) are versioned but listed in `exclude` in `_config.yml` so they are not published; add any new internal doc there. They are still visible in the public GitHub repo.
- Card images are hosted at `api.myl.cl/static/cards/{code}/{num}.png`, except the Drácula line (`DRACULA-*`, `PROMOS_CASAMYL_2026-*`), which temporarily hotlinks `codicetcg.b-cdn.net`, and a few custom cards in `assets/cards/`.
- The game uses manual draw (drawPerTurn=0) and shared turns — these are intentional MyL rules, not oversights.
