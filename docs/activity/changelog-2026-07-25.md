# 2026-07-25 — Rotación IMP, sets nuevos y sistema de vigencia

Detalle técnico de la jornada. Resumen en el [CHANGELOG](../../CHANGELOG.md).

## Rotación de formato IMP

- Rotan los sets **125** (Espíritu Samurái), **126** (Zodiaco) y **136** (Amenaza Kaiju).
  Copiados a `../cards_json_deprecated_2026-07-25/` y eliminados de `cards_json/`.
- Backup completo de `assets/` en `../assets_backup_2026-07-25/`.

## Sets nuevos

Convertidos desde `cards_raw/` (dumps de `api.myl.cl`) al formato de `cards_json/`:

| Archivo | Set | Cartas |
|---------|-----|--------|
| `163_toolkit_2026.json` | IMP - Toolkit 2026 | 36 |
| `165_chile_oculto.json` | IMP - Chile Oculto | 21 |
| `166_ayd_vigilantes.json` | IMP - AyD Vigilantes | 302 |
| `168_mazo_imp_dragon.json` | IMP - Mazo Dragón | 46 |
| `169_mazo_imp_eterno.json` | IMP - Mazo Eterno | 46 |
| `170_mazo_imp_guerrero.json` | IMP - Mazo Guerrero | 43 |

- La API publica el Toolkit 2026 partido en dos ediciones (163/164) con 8 cartas
  repetidas; se fusionaron en un archivo deduplicando por `edid`.
- Chile Oculto conserva los IDs antiguos (`CHILE_OSCURO_2-*`) pese a que la API los
  renumeró, para no romper los mazos guardados por los usuarios.
- Se eliminaron las imágenes placeholder de `assets/cards/` ya cubiertas por la API.
  Se conservan solo las 11 que la API no tiene (25 Aniversario y KVM JO).
- Nuevo `convert_raw_to_cards_json.py` para reproducir la conversión.

## Banlist

- Actualizada con la lista oficial de julio: 19 prohibidas, 32 limitadas a 1,
  18 limitadas a 2, 4 mercenarias.
- Los IDs se resolvieron por nombre contra el pool real: la tabla oficial cita el
  set "grande" de la temporada, que no siempre es la edición donde está la carta.
- Limpiados los IDs de sets rotados.

## Nombres de cartas

- Normalizados 71 nombres en 38 grupos: TCG Arena agrupa reimpresiones como
  "estilos" solo si el nombre coincide carácter a carácter, y variantes como
  `Fuente De La Juventud` / `Fuente de la Juventud` las separaban.
- Corregidos ~35 nombres con caracteres perdidos por la API (`Cañón Naval`,
  `Guadaña Gigante`, `Águila Negra`, `Spada da Lato`, `Deñ`, `Ángel Gabriel`…).
  Contrastados contra un dump de codicetcg, verificando caso por caso — ese dump
  tiene hasta 4 grafías del mismo nombre y no es fuente de verdad.
- `Visión Heróica` mantiene la tilde incorrecta: es errata de imprenta real.
- `El Caleuche` unificado en sus 6 impresiones, incluida la impresa sin artículo
  (necesario para la resolución de efectos por nombre).

## Razas

- Completadas 9 razas ausentes usando otra impresión de la misma carta como fuente
  (Sombrerero Loco → Faerie, Horda Tenebris → Bestia/Dragón/Sombra…), más
  Ignacio Carrera Pinto → Caballero/Héroe.
- Los 34 Aliados restantes sin raza son **Sin Raza legítimos**: los Jinetes operan
  sobre un arquetipo por nombre, y Malevolente / Cleopatra VII declaran en su texto
  "Entra en juego con una Raza a tu elección".

## Filtros: `Set`, `Edicion`, `Vigencia`

TCG Arena solo renderiza un filtro como dropdown si el campo tiene pocos valores
únicos (umbral entre 10 y 17, verificado). Con los 17 títulos de set reales el
filtro `Set` caía a campo de texto.

- **`Set`** (array) pasa a ser la **temporada**: 5 valores → dropdown.
  Mapeo en `SET_TO_SEASON` dentro de `build_card_list.py`.
- **`Edicion`** (string) conserva el título real del set → búsqueda por texto.
- **`Vigencia`** (array) indica con qué temporada rota cada carta, o `Inmortal`:
  6 valores → dropdown. Permite ver qué se va en la próxima rotación.

## Vigencia y cartas huérfanas

- Eliminadas 44 cartas que ya habían rotado pero sobrevivían por estar reimpresas
  en productos vigentes. Respaldadas en
  `../cards_json_deprecated_2026-07-25/huerfanas_2026-07-25.json`.
- Nuevo `vigencia_cartas.json`: declara por **nombre** con qué temporada rota cada
  carta; la heredan todas sus impresiones, así que una reimpresión extiende la vida
  de las copias anteriores. 245 excepciones — 109 inmortales, 110 de mazos precon
  (heredan AyD Vigilantes), 26 revisadas a mano.
- La rotación ahora se ejecuta editando `TEMPORADAS_VIGENTES` en
  `build_card_list.py`. Los archivos de `cards_json/` ya no se borran: el filtro es
  por vigencia, por lo que las huérfanas dejan de ser posibles.
- Tras una rotación quedan IDs muertos en `myl_banlist.json`. Es intencional: si la
  carta se reimprime, la restricción sigue declarada.

## Separador de multi-raza

8 cartas declaraban la raza con espacio en vez de `/`, o sin tilde:

- `160_onyria.json` (7): `Dragon Sombra`, `Bestia Faerie`, `Eterno Héroe` ×2,
  `Caballero Sacerdote`, `Faerie Sacerdote`, `Caballero Sombra`.
- `TMP1_aniversario_2025.json` (1): `Bestia/Dragon/Sombra` → `Bestia/Dragón/Sombra`.

`parse_race()` ya las absorbía por coincidencia de substring contra `KNOWN_RACES`,
así que el `race` emitido era correcto y el bug no se veía en TCG Arena. El problema
era el silencio: nada impedía que un scrape nuevo las reintrodujera. Se corrigieron
en `cards_json/`, que es el origen, y `build_card_list.py` ahora avisa de tres casos
—separador con espacio, ortografía sin tilde (derivada de `RACE_FIXES` para que no se
desincronice) y raza fuera de `KNOWN_RACES`— con dedup por raza+problema para que 80
cartas mal escritas den una línea y no 80.

El tercer caso es el que faltaba: una raza nueva o con typo raro no entra en el
fallback y se emitía tal cual al filtro, subiendo su cardinalidad sin aviso — el
mismo riesgo que ya cubría `SET_TO_SEASON` para los sets.

De paso, `CLAUDE.md` documentaba que el `type` de TCG Arena se componía como
`"{tipo} - {raza}"`. Es falso: `build_card_list.py` emite el tipo desnudo, y las
claves de `autoPlayFromHand` son `Oro`/`Aliado`/`Arma`/`Tótem`/`Talismán`. Corregido.

## Total

1927 cartas (desde 1897), 17 ediciones agrupadas en 5 temporadas.
