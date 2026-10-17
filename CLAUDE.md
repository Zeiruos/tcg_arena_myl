# CLAUDE.md

Este archivo orienta a Claude Code (claude.ai/code) al trabajar en este repositorio.

## El proyecto

Este repo arma la definición de juego de **Mitos y Leyendas** (MyL), el TCG chileno,
para la plataforma **TCG Arena**: un simulador web que carga juegos custom desde
archivos JSON publicados. No hay sistema de build, tests ni aplicación: el proyecto
son datos JSON más unos scripts en Python que los generan.

## Archivos clave

- **`Game_Mitos_y_Leyendas.json`** — Definición del juego: layout del tablero, reglas
  (mulligan, turnos, secciones), formatos de mazo y la URL de la lista de cartas. Su
  estructura está documentada en `GAME_JSON_DOCS.md`.
- **`myl_card_list.json`** — Lista de cartas en formato TCG Arena, indexada por ID. Es
  el archivo al que apunta `cards.dataUrl` en el game JSON. **Es generado: no se edita
  a mano**, se regenera con `build_card_list.py`.
- **`cards_json/`** — Datos fuente por set. Los que vienen de `api.myl.cl` se llaman
  `{codigo}_{slug}.json` (p. ej. `166_ayd_vigilantes.json`); los que la API todavía no
  publica vienen de codicetcg y se llaman `CODICE{edicion}_{slug}.json` (el número es
  el id de edición de codicetcg, no el de la API).
- **`build_card_list.py`** — Transforma `cards_json/` + `myl_banlist.json` +
  `vigencia_cartas.json` en `myl_card_list.json`. Con `--replace` sobrescribe el
  archivo publicado; sin él escribe `myl_card_list_build.json` para probar. Se corre
  desde la raíz del repo.
- **`myl_banlist.json`** — Fuente de verdad de la legalidad del formato (prohibidas,
  limitadas a 1 y a 2, mercenarias), por ID de carta.
- **`vigencia_cartas.json`** — Con qué temporada rota cada carta, por nombre (más
  overrides por ID). Ver "Vigencia y rotación".
- **`lista_restricciones_*.json`** — Transcripción de las listas oficiales de
  restricciones, de donde sale `myl_banlist.json`.
- **`scripts/convert_codice_to_cards_json.py`** — Convierte un dump de codicetcg a
  `cards_json/`. Ver "Agregar una edición desde codicetcg".
- **`scripts/revisar_dragones.py`** — Arma hojas con el dragón de frecuencia de cada
  carta de un dump de codicetcg, para revisar la vigencia a ojo.
- **`scripts/convert_raw_to_cards_json.py`** — Registro de la conversión de julio 2026
  desde los dumps crudos de `api.myl.cl`. **No volver a correrlo tal cual**: desde
  entonces `cards_json/` recibió correcciones a mano (nombres que la API corrompió o
  puso mal, tipos, razas) y las pisaría.
- **`GAME_JSON_DOCS.md`** — Documentación campo por campo del game JSON, sacada del
  Custom Game Builder de TCG Arena y de los juegos de ejemplo (Riftbound, Magic,
  Yu-Gi-Oh, Lorcana).

Fuera del repo, en la carpeta padre, viven los insumos que no se publican: los dumps de
codicetcg (`dump_json_codice_*.json`, `dump_html_codice_*.html`), los dumps crudos de la
API (`cards_raw/`), la caché de imágenes de `revisar_dragones.py`
(`cache_imagenes_codice/`) y los PDF/MD de reglas, FAQ y fe de erratas.

## Flujo de datos

1. Cada set queda en `cards_json/` con los campos `nombre`, `tipo`, `raza`, `coste`,
   `fuerza`, `edicion` (el ID de la carta), `frecuencia`, `descripcion`, `habilidad` e
   `imagen_url`.
2. `build_card_list.py` emite por carta: `id`, `isToken`,
   `face.front.{name,type,cost,image,isHorizontal}`, `name`, `type`, `cost`, `_legal`,
   `race`, `rarity`, `strength`, `ability`, `Set`, `Edicion`, `Vigencia` y, si genera
   Oros, `tokens`.
3. `type` es el tipo de carta a secas (`Aliado`, `Arma`, `Oro`, `Talismán`, `Tótem`),
   sin la raza. Tiene que coincidir con las claves de `autoPlayFromHand` del game
   JSON; el build avisa si aparece un tipo que no está ahí (la API ya conoce
   "Monumento").
4. La raza va aparte, en el array `race`, armado por `parse_race()`: las multirraza se
   separan por `/` (`"Bestia/Dragón"` → `["Bestia", "Dragón"]`). En `cards_json/` el
   separador siempre es `/` y la ortografía la de `KNOWN_RACES`, con tilde (`Dragón`,
   `Héroe`). Las variantes con espacio (`"Bestia Faerie"`) igual se parsean, pero son
   un bug del dato fuente: se corrigen en `cards_json/` y el build avisa.
5. Los nombres se emiten **sin diacríticos** (`name` y `face.front.name`): el buscador
   de TCG Arena compara literal, y "Baculo" no encontraba "Báculo". `strip_accents()`
   quita cualquier diacrítico, no solo las tildes del castellano ("Martillo Mjölnir" →
   "Martillo Mjolnir", "Rey de los Loçolicos" → "Rey de los Locolicos"), y conserva la
   ñ ("Cañón" → "Cañon", ver `KEEP_CHARS`). `cards_json/` guarda el nombre tal como
   viene impreso, así un re-scrape no hay que parcharlo. Los campos de búsqueda
   `ability` y `Edicion` van igual sin tildes; la detección de "Única" para la
   legalidad corre antes, sobre el texto original.
6. Los conectores del nombre van en minúscula salvo al inicio (`lower_connectors()`,
   `LOWER_WORDS`): la API escribe "Yelmo De Mambrino" y codicetcg —y por lo tanto las
   reimpresiones nuevas— "Yelmo de Mambrino", y TCG Arena solo agrupa las impresiones
   como estilos de una misma carta si el nombre coincide exacto. Solo cambian
   mayúsculas, nunca la ortografía.

## Actualizar el banlist

Se edita `myl_banlist.json` (nunca el campo `_legal` de `myl_card_list.json`) y se
regenera:

```
python build_card_list.py --replace
```

Cada categoría se traduce a un valor de `_legal`. Prioridad: `banned` > `limited_1` >
`limited_2` > `mercenary` > "Única" en la habilidad > `true` por defecto.

| Categoría   | `_legal` | Significado            |
|-------------|----------|------------------------|
| `banned`    | `false`  | Prohibida              |
| `limited_1` | `1`      | Única (1 copia)        |
| `limited_2` | `2`      | Restringida a 2 copias |
| `mercenary` | `50`     | Mercenaria (ilimitada) |

Un ID va en una sola categoría: al mover una carta, se saca de la lista anterior. Las
listas oficiales nombran una carta, pero el banlist es por ID: hay que agregar todas
sus impresiones (las reimpresiones de la misma carta, no las cartas distintas que
comparten nombre). La edición que cita la tabla oficial no siempre es la correcta.

## Set y Edicion: agrupación por temporada

TCG Arena solo muestra un filtro como **dropdown** si el campo tiene pocos valores
distintos; pasado cierto umbral (entre 10 y 17, verificado en julio 2026) cae a campo
de texto libre aunque el valor siga siendo un array. Con los títulos de set reales,
el filtro no salía como dropdown. Por eso el build emite dos campos:

| Campo     | Tipo   | Contenido                         | Filtro   |
|-----------|--------|-----------------------------------|----------|
| `Set`     | array  | Temporada vigente (5 valores)     | dropdown |
| `Edicion` | string | Título real del set (24 valores)  | texto    |

El mapeo set → temporada vive en `SET_TO_SEASON` dentro de `build_card_list.py`. **Al
agregar un set hay que sumarlo ahí**; si no, el build avisa y usa el título tal cual,
lo que sube la cantidad de valores y puede romper el dropdown. Conviene mantener pocas
temporadas: idealmente 10 o menos, como `race`.

`Set` solo lista temporadas de `TEMPORADAS_VIGENTES`. Una impresión de una temporada
ya rotada que sigue legal (Inmortal o reimpresa en algo vigente) sale con `Set: []`:
así la temporada rotada desaparece del dropdown y el set real sigue en `Edicion`. Esas
cartas se encuentran por `Vigencia` o sin filtro de Set.

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

**La vigencia de una carta es la del dragón más reciente entre todas sus
impresiones**, y la heredan todas sus copias. Una reimpresión solo extiende la vida de
las anteriores si trae un dragón más nuevo. Por ejemplo:
- Signo Amarillo es de Bestiarium, pero rota con KvM por su impresión en los precon.
- Tamales y Visión de Enoc se reimprimieron en Drácula con su dragón original (KvM y
  AyD), así que no se extienden.

Las promos y artes alternativos a veces traen **logos especiales** (fénix JO, "25
Años", estrella SP, Rapa Nui, dragón asiático…). Se ignoran y se usa el dragón de las
otras impresiones de la misma carta; si no hay otras, rota con su set.

Ningún dato textual lo dice: codicetcg no lo trae (salvo `nv: true` en algunas JO/SP)
y las fechas `date_empire_valid` de la API son por edición y no siempre calzan (los
precon figuran con la fecha de AyD). Se revisa a ojo con `scripts/revisar_dragones.py`.
Con recortes chicos el dragón de Onyria sobre anillo verde se confunde con el robot de
KvM: ante la duda, mirar la carta en grande o preguntar.

`vigencia_cartas.json` declara la vigencia **por nombre de carta**:

| Valor | Significado |
|-------|-------------|
| `Inmortal` | No rota nunca |
| nombre de temporada | Rota cuando esa temporada rote |
| (ausente del archivo) | Rota con la temporada de su propio set (`SET_TO_SEASON`) |

Solo hace falta una entrada cuando alguna impresión no rotaría, por defecto, con el
dragón más reciente de la carta. `vigencia_por_id` manda sobre el nombre y sirve para
separar cartas distintas que comparten nombre (hoy está vacío).

Cada carta emite `Vigencia` (array), que va en `mainFilters` como dropdown: permite ver
de un vistazo qué cartas se van en la próxima rotación.

### Mismo nombre: ¿reimpresión o carta distinta?

Pueden existir cartas distintas con el mismo nombre. Se decide caso por caso:

- **Mismo texto**, o el mismo con **errata** de redacción (Tamales, Fuego Purificador,
  Visión de Enoc…) → es la misma carta, y el diseño anterior sigue siendo válido. Su
  vigencia se calcula con todas sus impresiones.
- **Carta completamente distinta** (Zmeoaica de Bestiarium y la de Drácula, Moloch y
  Gog de Bestiarium y AyD…) → cada una rota con su propio set y **no** se declara su
  nombre. Si las dos siguen vigentes, TCG Arena las mostraría como estilos de una sola
  carta, así que la que menos se usa lleva sufijo: "Alicanto (Aliado)" (vs el Oro de
  los precon) y "Jonathan Harker (Drácula)" (vs el de Onyria). Se acuerda con el
  usuario.
- Antes de concluir que son distintas, revisar el nombre impreso: la API les puso otro
  nombre a cartas enteras ("Principe Orion" de Onyria era Ismael, "Rlyeh" era Casa de
  Opio, "Vuelo Mágico" era Polvo de Hadas). Cruzar por texto contra codicetcg dentro
  de la misma edición destapa esos casos.

`scripts/convert_codice_to_cards_json.py` imprime esta clasificación al final.

### Inmortales

Cada temporada trae un lote de ~50 Inmortales (en codicetcg, las ediciones 900+:
"Bestiarium - Inmortales", "Drácula: Rey Vampiro - Inmortales"…). El lote cambia de una
temporada a otra, pero **los Inmortales se acumulan y nunca rotan**: si un nombre
estuvo en algún lote, es `Inmortal` para siempre, aunque el lote siguiente no lo
incluya. Al agregar una temporada, los nombres nuevos de su lote se suman como
`Inmortal`. Sus impresiones vienen sin rareza (la carta dice "INMDRAC-021"): en
`cards_json/` llevan `frecuencia: "IM"`.

### Ejecutar una rotación

Se saca la temporada de `TEMPORADAS_VIGENTES` en `build_card_list.py` y se regenera.
**Los archivos de `cards_json/` no se borran**: el filtro es por vigencia, así que las
Inmortales y las reimpresas sobreviven solas y no quedan cartas huérfanas. Después hay
que limpiar de `myl_banlist.json` los IDs que ya no existen (el build no falla, pero
quedan entradas muertas).

Las 6 entradas `Bestiarium` (Behemot, Ereshkigal, Rey de Amarillo, Lágrima de Dragón…)
no sobran aunque Bestiarium ya rotó: esas cartas tienen reimpresiones JO/SP en sets
vigentes con el dragón de Bestiarium, y sin la entrada esas copias sobrevivirían con la
temporada de su set.

De dónde sale `vigencia_cartas.json`: las 126 Inmortales son la unión de los lotes de
Bestiarium, Onyria, AyD Vigilantes y Drácula; el resto, de la revisión visual de los
dragones de todas las impresiones de codicetcg (octubre 2026).

## Agregar una edición desde codicetcg

Cuando `api.myl.cl` todavía no publica una edición (así entró Drácula, octubre 2026):

1. En la librería de codicetcg (formato Imperio), filtrar por las ediciones nuevas y
   guardar la página (HTML) y la respuesta XHR con las cartas (JSON). El JSON trae más
   cartas de las que interesan; **el HTML filtrado es la fuente de verdad** de cuáles
   entran.
2. Agregar las ediciones nuevas a `EDITIONS` en `scripts/convert_codice_to_cards_json.py`
   (prefijo de ID, slug y título) y correr
   `python scripts/convert_codice_to_cards_json.py --json DUMP.json --html DUMP.html`.
3. Revisar contra la imagen de la carta los avisos (Aliado sin raza, no-Oro sin coste)
   y el reporte de nombres repetidos. Los datos de codicetcg traen errores: en Drácula
   hubo Oros tipados como Talismán, costes perdidos, una raza faltante y typos en
   nombres ("Liull" por "Llull") y habilidades. Se corrigen en los diccionarios
   `*_FIXES` del script, no a mano en `cards_json/`, para que una reconversión no los
   pierda.
4. Revisar el dragón de cada carta nueva con `python scripts/revisar_dragones.py <ediciones>`,
   sobre todo reimpresiones, kits y promos. Cada impresión tiene que terminar rotando
   con su dragón:
   - nombres nuevos del lote de Inmortales → `Inmortal`;
   - reimpresión con el dragón nuevo → la temporada nueva para ese nombre;
   - reimpresión con un dragón viejo → la temporada vieja para ese nombre (sin
     entrada, la copia nueva rotaría con el set nuevo);
   - carta nueva con el dragón de otra temporada → esa temporada.
5. En `build_card_list.py`, sumar los títulos nuevos a `SET_TO_SEASON` y la temporada a
   `TEMPORADAS_VIGENTES` (y sacar la que rote).
6. Regenerar, limpiar del banlist los IDs muertos y revisar que las reimpresiones de
   cartas restringidas compartan la restricción.

Las imágenes quedan apuntando al CDN de codicetcg (`codicetcg.b-cdn.net`, webp de
~150 KB). Es provisorio: codicetcg se financia con donaciones, y cuando la API oficial
publique la edición conviene pasar a sus URLs. Los IDs siguen la numeración lineal de
codicetcg (la misma que usó la API para AyD Vigilantes), así que en principio basta con
cambiar `imagen_url`.

## Convenciones

- Los nombres de sección del game JSON usan `_` en vez de espacios (`Oro_Pagado`).
- El campo `name` de `Game_Mitos_y_Leyendas.json` no se cambia nunca una vez
  compartido: los mazos guardados por los usuarios dependen de él.
- Los IDs de carta son `{SLUG_DEL_SET}-{número de 3 dígitos}` (`AYD_VIGILANTES-001`,
  `DRACULA-126`) y tampoco se cambian: los mazos guardan IDs. Hay excepciones
  heredadas (`CHILE_OSCURO_2-*`, `25-ANIVERSARIO_*`) que se mantienen por eso mismo.
- El juego usa robo manual a propósito: no se roba al empezar el turno
  (`drawOnStart: false`, `drawPerTurn: 0`), porque en MyL se roba en la Fase Final.
- Las imágenes están en `api.myl.cl/static/cards/{codigo}/{num}.png`, salvo la línea
  Drácula (`DRACULA-*`, `PROMOS_CASAMYL_2026-*`), que por ahora usa el CDN de
  codicetcg, y unas pocas cartas propias en `assets/cards/`.
- GitHub Pages sirve el repo tal cual desde `main`: **cada push publica**. Pages corre
  Jekyll, que convierte cada `.md` en una página; los documentos internos
  (`CLAUDE.md`, `GAME_JSON_DOCS.md`) se versionan pero van en el `exclude` de
  `_config.yml` para no publicarse. Cualquier documento interno nuevo va ahí. Igual se
  ven en el repo público de GitHub.
- Los commits se escriben en español, solo con título.
