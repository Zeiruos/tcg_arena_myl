# Documentacion del Game JSON - TCG Arena Custom Builder

Documentacion generada a partir del HTML del Custom Game Builder de TCG Arena.
Cada campo incluye su descripcion (tooltip `class="help"`) y el mapeo al JSON.
Enriquecida con campos descubiertos de los juegos Riftbound, Magic the Gathering, Yu-Gi-Oh y Lorcana (ejemplos funcionales).

---

## Flujo de Trabajo General

Para jugar un juego custom en TCG Arena se necesitan **3 archivos** (+ 2 opcionales), todos en formato `.json` y hosteados publicamente:

1. **Card images** - Subir todas las imagenes (cartas, tokens, playmats, banner) al host de tu eleccion.
2. **Card list file** (`.json`) - Lista de cartas. Una vez entendida la estructura, se puede generar/actualizar con un script.
3. **Game file** (`.json`) - Archivo principal del juego (este documento describe su estructura).
4. **(Opcional) Starter decklists file** (`.json`) - Mazos preconstruidos. Conviene crear el juego primero y luego exportar mazos desde el deckbuilder.
5. **(Opcional) Translations file** (`.json`) - Archivo de traducciones para localizar el juego.

### Pasos para publicar:
1. Subir imagenes al host.
2. Crear y subir el card list JSON.
3. Crear y subir el game file JSON.
4. Ingresar la URL del game file en TCG Arena para generar un link compartible.
5. Compartir el link a otros jugadores.
6. Para actualizar: editar los JSON directamente o reimportarlos en el Custom Builder.

> Los archivos son legibles y faciles de modificar con un editor de texto. Tambien se pueden reimportar en el builder para hacer cambios visuales.

---

## Estructura General del Game JSON

```json
{
  "name": "...",
  "menuBackgroundImage": "...",
  "defaultRessources": { ... },
  "customHelp": "...",
  "cardRotation": 45,
  "cards": { ... },
  "translationsUrl": "...",
  "deckBuilding": { ... },
  "gameplay": { ... }
}
```

---

## Campos de Nivel Superior

### `name` (string)
- **Label UI:** Game name
- **Descripcion:** Decks saved by users will be identified by this. It needs to be unique and never change it after sharing your game.
- **Importante:** Una vez compartido el juego, NO cambiar este valor. Los mazos guardados por usuarios se identifican con este nombre.

### `menuBackgroundImage` (string, URL)
- **Label UI:** Game image URL
- **Descripcion:** The image used as a background in the menu/deckbuilder.

### `customHelp` (string)
- **Label UI:** Custom help message
- **Descripcion:** Message displayed in the help section in game.
- **Nota:** Soporta `\n` para saltos de linea.
- **Traduccion:** Puede ser una referencia a una key del archivo de traducciones usando el prefijo `translations.` (ej: `"translations.customHelp"`). El texto real se define en el translations JSON, permitiendo multi-idioma. Descubierto en Lorcana.

### `cardRotation` (number | string)
- **Label UI:** Card rotation when tapped
- **Descripcion:** By how many degrees should a card be tapped when clicking it. 45 degrees is recommended. Choosing 90 degrees is not recommended if your game uses horizontal cards.
- **Valores comunes:** `45`, `"90"`

### `translationsUrl` (string, URL)
- **Descripcion:** URL to a JSON file containing translations for the game UI. Allows localizing section names, card types, filter labels, card attributes, and other UI text.
- **Ejemplo:** `"https://example.com/MyGame-Translations.json"`
- **Estructura del archivo de traducciones:** Ver seccion [Archivo de Traducciones](#archivo-de-traducciones).

---

## `defaultRessources` (object)

```json
"defaultRessources": {
  "backgrounds": [],
  "decksUrl": ""
}
```

### `defaultRessources.backgrounds` (array of strings)
- **Label UI:** Playmats images
- **Descripcion:** Playmats available to players in the preferences. Try to have at least one.
- **Formato:** Array de URLs a imagenes de playmat.

### `defaultRessources.decksUrl` (string, URL)
- **Label UI:** Preconstructed decks file URL
- **Descripcion:** The URL to a JSON file containing an array of decks. Preconstructed decks in this file will be available to all players in game when choosing a deck. The file should look like this `[DECK1, DECK2, ...]` with the deck data in the TCG Arena starter deck format (you'll find it in the export menu in the deckbuilder).

---

## `cards` (object)

```json
"cards": {
  "dataUrl": "...",
  "cardBack": "...",
  "cardBackColor": "#03354a",
  "extraCardBacks": {
    "CategoryName": "https://..."
  }
}
```

### `cards.dataUrl` (string, URL)
- **Label UI:** Card list .json URL
- **Descripcion:** URL to the card list file you created earlier.
- **Nota:** Debe apuntar a un JSON publico con la lista de cartas.

### `cards.cardBack` (string, URL)
- **Label UI:** Card back image
- **Descripcion:** URL de la imagen del reverso de las cartas.

### `cards.cardBackColor` (string, color hex)
- **Descripcion:** Background color shown behind/around the card back image. Useful when the card back image has transparency or doesn't fill the entire card area.
- **Ejemplo:** `"#03354a"`

### `cards.version` (number)
- **Descripcion:** Version number for the card data. Can be used to force TCG Arena to refresh cached card data when the card list is updated.
- **Ejemplo:** `10`

### `cards.extraCardBacks` (object)
- **Descripcion:** Per-category custom card back images. Keys are deck category names (must match categories in `deckBuilding`), values are image URLs. Cards in these categories will show their specific card back instead of the default.
- **Ejemplo:**
```json
"extraCardBacks": {
  "Runes": "https://example.com/cardBack-white.png",
  "Battlefields": "https://example.com/cardBack-black.png"
}
```

---

## `deckBuilding` (object)

```json
"deckBuilding": {
  "mainFilters": ["type", "cost", "name"],
  "formats": [ ... ],
  "deckRulesets": { ... }
}
```

### `deckBuilding.costCurveIgnoredTypes` (array of strings)
- **Descripcion:** Card types that should be excluded from the mana/cost curve chart in the deck builder. Useful for resource cards that have cost 0 or no meaningful cost (e.g., Lands in MTG, Oros in MyL).
- **Ejemplo:** `["Land"]`, `["Oro"]`

### `deckBuilding.mainFilters` (array of strings)
- **Label UI:** Main filters
- **Descripcion:** Filters displayed below the search bar in the deckbuilder. Each filter name must match a key in the card list. The `name` field has su propio buscador dedicado en la UI (campo "Card Name" arriba), por lo que no es necesario incluirlo aqui. Default keys: `type`, `cost`, `name`. Also supports custom keys defined in the card list.
- **Comportamiento segun tipo de dato en la carta:**
  - **string** → Filtro de texto libre (ej: `name`, `Habilidad`).
  - **array** → Filtro **dropdown/select** con opciones autogeneradas desde los valores unicos (ej: `Raza: ["Bestia", "Dragón"]`, `Set: ["01 - Origins"]`, `Colors: ["G"]`), **siempre que haya pocos valores unicos** (ver abajo).
  - **number** → Filtro numerico (ej: `cost`).
- **Umbral de cardinalidad (verificado en MyL, 2026-07):** un campo array solo se
  renderiza como dropdown si tiene **pocos valores unicos**; por encima del umbral
  degrada a campo de texto libre aunque siga siendo array. Comprobado en este proyecto:
  con 17 titulos de set el filtro `Set` salia como texto, y al agrupar los sets en
  5 temporadas paso a dropdown sin ningun otro cambio. El umbral exacto no esta
  documentado por la plataforma; los datos conocidos lo acotan **entre 10 y 17**:

  | Juego | Campo | Tipo | Valores unicos | Widget |
  |-------|-------|------|----------------|--------|
  | MTG | `Colors` | array | 5 | dropdown |
  | Shadowverse Evolve | `Set` | array | 8 | dropdown |
  | MyL | `race` | array | 10 | dropdown |
  | MyL | `Set` (agrupado) | array | 5 | dropdown |
  | MyL | `Set` (sin agrupar) | array | 17 | texto |
  | MTG | `set` | string | 465 | (no esta en mainFilters) |

  Patron recomendado cuando hay muchos sets: agrupar en pocas categorias para el
  campo del dropdown y conservar el valor real en otro campo string. Shadowverse
  Evolve hace lo mismo agrupando en rangos (`BP01-03`, `BP04-06`). En MyL:
  `Set` = temporada (array, dropdown) y `Edicion` = titulo real del set (string, texto).
- **Label visible:** El label que muestra el filtro es la key misma (ej: key `"type"` muestra "type", key `"Raza"` muestra "Raza"). Los campos obligatorios de TCG Arena (`type`, `cost`, `name`) no se pueden renombrar.
- **Ejemplos por juego:**
  - MTG: `["type", "Colors", "cost"]` — Colors es array → dropdown.
  - Yu-Gi-Oh: `["type", "archetype", "level"]` — archetype es string → texto.
  - Riftbound: `["type", "cost", "name", "Domain", "Set"]` — Domain y Set son arrays → dropdowns.
  - MYL: `["type", "cost", "name", "Raza", "Set", "Habilidad"]` — Raza y Set son arrays → dropdowns, Habilidad es string → texto.

### `deckBuilding.formats` (array of objects)
- **Label UI:** Game formats
- Cada formato tiene:

#### `formats[].title` (string)
- **Label UI:** Format title
- **Descripcion:** Nombre visible del formato de juego.

#### `formats[].gameplay` (string)
- **Label UI:** Gameplay identifier
- **Descripcion:** The title of the gameplay used for this format. Define them below in the Gameplay Data section.
- **Importante:** Debe coincidir exactamente con una key dentro de `gameplay`.

#### `formats[].customCategories` (array of strings)
- **Descripcion:** Additional deck categories specific to this format. These are sections where the player must place specific cards during deck building (e.g., a champion pick, a leader card). The category name must match a section in `customSections`.
- **Ejemplo:** `["Chosen_Champion"]`

#### `formats[].deckRuleset` (string)
- **Descripcion:** References a ruleset defined in `deckBuilding.deckRulesets`. Defines deck size limits, per-card limits, and category constraints for this format.
- **Ejemplo:** `"Standard"`

#### `formats[].legalityCode` (string)
- **Descripcion:** Code used to filter which cards are legal in this format. Each card in the card list must have a `_legal` field with a key matching this code. The value determines legality and can also override `maxPerCard` per card (see seccion [Card List: Campo `_legal`](#card-list-campo-_legal)).
- **Ejemplo:** `"S02"`, `"EDH"`, `"IR"`

---

### `deckBuilding.deckRulesets` (object)

Defines reusable deck validation rulesets referenced by `formats[].deckRuleset`.

```json
"deckRulesets": {
  "Standard": {
    "reversedLegality": true,
    "general": {
      "min": 56,
      "max": 56,
      "maxPerCard": 3
    },
    "categories": [
      {
        "category": "Legend",
        "min": 1,
        "max": 1,
        "maxPerCard": 1
      }
    ]
  }
}
```

#### `deckRulesets.{name}.checkCardLegality` (boolean)
- **Descripcion:** If `true`, enforces legality checking for cards in this ruleset. Each card must have a `_legal` field in the card list with a key matching the format's `legalityCode`. The value of that key controls both legalidad and `maxPerCard` override per carta (ver seccion [Card List: Campo `_legal`](#card-list-campo-_legal)).
- **Importante:** Sin este campo en `true`, el campo `_legal` de las cartas es ignorado.

#### `deckRulesets.{name}.reversedLegality` (boolean)
- **Descripcion:** If `true`, the legality check is reversed: cards that match the `legalityCode` are **banned** instead of legal. Useful for ban lists instead of allow lists.
- **Nota:** Solo invierte el chequeo boolean (`true`/`false`). No afecta los overrides numericos de `_legal`.

#### `deckRulesets.{name}.general` (object)
- **Descripcion:** Global deck constraints.
  - `min` (number) - Minimum total cards in deck.
  - `max` (number) - Maximum total cards in deck.
  - `maxPerCard` (number) - Maximum copies of any single card.

#### `deckRulesets.{name}.categories` (array of objects)
- **Descripcion:** Per-category constraints. Each entry:
  - `category` (string) - Must match a deck category / section name.
  - `min` (number) - Minimum cards in this category.
  - `max` (number) - Maximum cards in this category.
  - `maxPerCard` (number, optional) - Max copies per card within this category.
  - `ignoreTotalCount` (boolean, optional) - If `true`, cards in this category do not count toward the `general.min`/`general.max` total. Useful for side decks or extra categories.

---

## `gameplay` (object)

Contiene las configuraciones de gameplay. Cada key es un identificador referenciado desde `deckBuilding.formats[].gameplay`. Se pueden definir multiples modos de juego con configuraciones independientes (ej: `"Classic"`, `"Multiplayer"`, `"Commander"`). Cada modo puede tener su propio mulligan, layout de tablero, tokens y reglas de turno.

```json
"gameplay": {
  "Classic": {
    "mulligan": { ... },
    "newTurn": { ... },
    "defaultNotes": "...",
    "tokens": [ ... ],
    "countersStartingValues": [ ... ],
    "hideFacedDownCards": false,
    "draggableTokens": [ ... ],
    "beforeGameStart": { ... },
    "sections": { ... }
  },
  "Multiplayer": {
    // Configuracion independiente para multijugador
    // Puede tener layout, tokens y reglas completamente distintas
  }
}
```

> **Nota:** Cada modo de gameplay es completamente independiente. Riftbound, por ejemplo, define un modo `"Classic"` y un `"Multiplayer"` con layouts, draggableTokens y secciones distintas. Yu-Gi-Oh solo define `"Classic"`. Para vincular un formato con un modo, usar `formats[].gameplay`.

---

### `gameplay.{id}.mulligan` (object)

TCG Arena reemplazó el sistema antiguo de flags booleanos (`drawNewHand`, `putSelectionAtBottom`, `drawNewSelectedCards`) por un sistema basado en **ciclos** con `steps` declarativos. Todos los campos son opcionales.

```json
"mulligan": {
  "triggeredByButton": true,
  "startingHandSize": 8,
  "mulliganCount": { "min": 0, "max": 4 },
  "mulliganCycle": {
    "info": "translations.mulliganInfo",
    "steps": ["toBottom", "shuffle", "applyPenalty", "draw"],
    "selectionRange": { "min": 1, "max": 99 },
    "keepCardsOrder": false
  },
  "postMulligan": {
    "minMulligansToTrigger": 1,
    "info": "...",
    "steps": ["toBottom", "shuffle", "draw"],
    "selectionRange": { "min": 1, "max": 99 },
    "keepCardsOrder": false
  }
}
```

#### `mulligan.triggeredByButton` (boolean)
- **Descripcion:** Si `true`, el panel de mulligan no aparece automaticamente al inicio — el jugador lo abre manualmente con un boton. Util cuando el mulligan es opcional. Si `false`, el panel aparece automaticamente.

#### `mulligan.startingHandSize` (number)
- **Descripcion:** Cantidad de cartas de la mano inicial.

#### `mulligan.mulliganCount` (object)
- **Descripcion:** Cuantas veces se puede ejecutar el ciclo.
- **`min`** (number): minimo de mulligans (normalmente `0`).
- **`max`** (number): maximo de mulligans permitidos. Si `0`, la mano se reparte sin mostrar el panel.

#### `mulligan.mulliganCycle` (object)
Define lo que ocurre **cada vez** que el jugador ejecuta un mulligan.

- **`info`** (string): texto mostrado arriba del panel. Acepta `translations.<key>`.
- **`steps`** (array): secuencia de acciones en orden. Solo incluir las que se necesiten:
  - `"toBottom"` — pone las cartas seleccionadas al fondo del mazo.
  - `"toTop"` — pone las cartas seleccionadas arriba del mazo.
  - `"draw"` — roba hasta el max-hand-size actual.
  - `"shuffle"` — baraja el mazo.
  - `"applyPenalty"` — reduce el max-hand-size en 1 (ciclo escalonado: 8→7→6...).
- **`selectionRange`** (object): cuantas cartas debe seleccionar el jugador.
  - `min`, `max` (number). Si `max` ≥ tamaño de la mano, el ciclo aplica a la mano completa sin requerir seleccion individual.
- **`keepCardsOrder`** (boolean): si `true`, las cartas se devuelven al mazo en el orden en que el jugador las clickeo.

#### `mulligan.postMulligan` (object, opcional)
Acción adicional disponible **después** del ciclo principal. Misma estructura que `mulliganCycle` mas:

- **`minMulligansToTrigger`** (number): cuantos mulligans del ciclo principal deben haberse ejecutado para habilitar este paso. `0` = siempre disponible.

Util para "comodines" o efectos finales que no deben repetir el ciclo escalonado.

#### Campos legacy (sistema antiguo)
Los siguientes campos pertenecen al schema viejo y no se mezclan con `mulliganCycle`:
- `mulligan.drawNewHand` (boolean)
- `mulligan.putSelectionAtBottom` (boolean)
- `mulligan.drawNewSelectedCards` (boolean)
- `mulligan._NO_SHUFFLE` (boolean) — desactiva el shuffle post-mulligan.

Si migras al sistema nuevo, eliminalos.

---

### `gameplay.{id}.newTurn` (object)

```json
"newTurn": {
  "drawOnStart": false,
  "sharedTurn": true,
  "firstPlayerTokenName": "",
  "drawPerTurn": 0
}
```

#### `newTurn.drawOnStart` (boolean)
- **Label UI:** First player draw at game start
- **Descripcion:** Si el primer jugador roba carta al inicio del juego.

#### `newTurn.sharedTurn` (boolean)
- **Label UI:** Shared turn
- **Descripcion:** Si los turnos son compartidos (ambos jugadores actuan al mismo tiempo) o alternados.

#### `newTurn.firstPlayerTokenName` (string)
- **Label UI:** First player token name
- **Descripcion:** Token to represent the first player. Use the name of the token defined in the Tokens section below.
- **Nota:** Dejar vacio si no se usa token de primer jugador.

#### `newTurn.drawPerTurn` (number | string)
- **Label UI:** Cards draw per turn
- **Descripcion:** Cartas robadas automaticamente al inicio de cada turno. Si es `0`, el robo es manual.
- **Nota:** Acepta tanto number como string (ej: `0`, `"1"`).

---

### `gameplay.{id}.defaultNotes` (string)
- **Label UI:** Default notes
- **Descripcion:** Default player notes. Will be applied to all players when each game starts.

---

### `gameplay.{id}.tokens` (array of objects)

```json
"tokens": [
  {
    "name": "Oro_Virtual",
    "image": "https://..."
  }
]
```

- **Descripcion:** Tokens disponibles en el juego. Cada token tiene:
  - `name` (string) - Identificador del token.
  - `image` (string, URL) - Imagen del token.
  - `isUnique` (boolean, optional) - If `true`, only one instance of this token can exist at a time. When played, it is transferred rather than duplicated (e.g., Monarch in MTG).
  - `leavesAtEndOfTurn` (boolean, optional) - If `true`, the token is automatically removed at the end of each turn.

---

### `gameplay.{id}.draggableTokens` (array of objects)

```json
"draggableTokens": [
  {
    "id": "stun-token",
    "name": "Stun",
    "image": "https://..."
  }
]
```

- **Descripcion:** Tokens that can be dragged and placed on top of cards on the board. Unlike regular `tokens`, these are visual markers/status indicators (e.g., stun, buff, temporary). Each has:
  - `id` (string) - Unique identifier.
  - `name` (string) - Display name.
  - `image` (string, URL) - Token image, typically a small overlay icon.

---

### `gameplay.{id}.countersStartingValues` (array of numbers | strings)
- **Label UI:** Player counters starting value
- **Descripcion:** ALWAYS HAVE AT LEAST 1 AND NEVER MORE THAN 2.
- **Nota:** Son los contadores de vida/puntos. Min 1, max 2 valores. Acepta tanto numbers como strings.
- **Ejemplos:**
  - MTG Commander: `[40, 0]` (vida + veneno)
  - Yu-Gi-Oh: `["8000"]` (life points como string)
  - Riftbound: `[0]` (un solo contador)

---

### `gameplay.{id}.hideFacedDownCards` (boolean)
- **Label UI:** Prevent seeing your own faced down card
- **Descripcion:** If set to yes, the player won't be able to see its faced down cards at all time without flipping them.

---

### `gameplay.{id}.beforeGameStart` (object)

Permite configurar acciones que ocurren antes de que comience la partida.

#### `beforeGameStart.decksToPick` (number)
- **Descripcion:** Number of decks the player must pick before the game starts. Used for formats like Jumpstart where players combine multiple mini-decks.
- **Ejemplo:** `2`

#### `beforeGameStart.initialBoardSetup` (array)
- **Descripcion:** Array of actions to set up the board automatically before the game starts. Each action can create cards or draw from a deck.

**Crear una carta por ID:**
```json
{
  "createCardId": "cardId",
  "count": 1,
  "destination": "sectionId"
}
```

**Robar cartas del tope del mazo:**
```json
{
  "drawFromTop": "Deck",
  "count": 3,
  "destination": "sectionId"
}
```
- **Nota:** `drawFromTop` actualmente solo soporta `"Deck"` como origen.

---

## `gameplay.{id}.sections` (object)

Configura el tablero de juego: zonas, layout visual y comportamiento.

```json
"sections": {
  "customSections": ["Oro", "Oro_Pagado", "Destierro", "Ataque", "Defensa", "Apoyo"],
  "layout": { ... },
  "categoriesAlreadyOnBoard": [],
  "autoPlayFromHand": { ... },
  "autoPlayFromStack": { ... },
  "sectionsDict": { ... }
}
```

---

### `sections.customSections` (array of strings)
- **Label UI:** Custom sections name list
- **Descripcion:** All board sections in which the players will be able to drop cards (except hand, deck, discard, pile and removed). List their name here. Make sure to use the exact same name in the Layout and the Sections Data below.
- **Nombres prohibidos:** `Hand`, `Deck`, `Stack`, `Discard`, `Exile` (ya existen por defecto).
- **Importante:** No usar espacios en los nombres, usar `_` en su lugar.

---

### `sections.layout` (object)

Define el layout visual del tablero usando un sistema de filas/columnas con flex.

```json
"layout": {
  "direction": "column",
  "isSymetricalForOpponents": true,
  "content": [ ... ]
}
```

#### `layout.direction` (string)
- **Valores:** `"column"` | `"row"`
- **Descripcion:** Direccion del layout principal.

#### `layout.isSymetricalForOpponents` (boolean)
- **Label UI:** Is symetrical for opponents
- **Descripcion:** Should the group be reversed for opponents to appear symmetrical to the player board. Only reverse the direct children of the group. If the whole board should be symmetrical, set this to true to all groups.

#### `layout.content` (array)
Array de grupos (rows/columns) o secciones individuales.

**Grupo (row/column):**
```json
{
  "direction": "row",
  "style": false,
  "content": [ ... ],
  "isSymetricalForOpponents": false,
  "optional": { "key": "Feature Name" }
}
```

**Seccion individual dentro de un grupo:**
```json
{
  "section": "NombreSeccion",
  "style": { "flex": 4 }
}
```

#### `style` (object | false)
- **Label UI:** Style
- **Descripcion:** CSS style object applied to the area (optional).
- **Ejemplo:** `{ "flex": 1 }`, `{ "width": "12vh" }`, `{ "height": "24.25vh" }`
- **Nota:** Usar `false` si no se necesita estilo.
- **Propiedades CSS observadas en ejemplos:**
  - `flex` - Proporcion del espacio disponible.
  - `width`, `height` - Dimensiones en vh.
  - `marginRight`, `marginLeft`, `marginTop` - Margenes (ej: `"4vh"`, `"auto"`).
  - `justifyContent` - Alineacion del contenido dentro del grupo (ej: `"start"`). Usado en Yu-Gi-Oh para alinear columnas laterales al inicio.
  - `position`, `top`, `left`, `translate`, `scale` - Posicionamiento absoluto.
  - `background` - Fondos con gradientes.
  - `borderRadius` - Bordes redondeados.
- **Avanzado:** Soporta CSS completo incluyendo posicionamiento absoluto. Esto permite superponer secciones:
```json
{
  "section": "Battlefields",
  "style": {
    "width": "30vh",
    "height": "12vh",
    "scale": "0.68",
    "position": "absolute",
    "top": "0",
    "left": "50%",
    "translate": "-50% -3.25vh"
  }
}
```
- Tambien se pueden usar gradientes para fondos de secciones:
```json
"style": {
  "background": "linear-gradient(0deg, rgba(170, 85, 85, 0) 0%, rgba(170, 85, 85, 0.6) 90%)",
  "borderRadius": "1vh",
  "marginTop": "auto"
}
```

#### `section` (string)
- **Label UI:** Section title
- **Descripcion:** Make sure the title here matches the title used in 'Sections Data' below.

#### `optional` (object)
- **Descripcion:** Makes a layout group optional. The group will only appear if enabled by the game mode or configuration. Contains a `key` field with the feature name.
- **Ejemplo:** `{ "key": "Baron Pit" }` - This layout group only appears when "Baron Pit" is active.

---

### `sections.categoriesAlreadyOnBoard` (array of strings)
- **Label UI:** Deck categories that start the game on board
- **Descripcion:** The deck category should match the section in which they are placed. Cards in these categories are placed directly on the board at game start instead of going into the deck.
- **Ejemplo:** `["Runes", "Battlefields", "Legend", "Chosen_Champion"]`
- **Sintaxis especial `->` :** Si la categoria tiene un nombre distinto a la seccion destino, se usa la sintaxis `"Categoria->Seccion"`. Esto permite que una categoria del deck builder se coloque en una seccion con nombre diferente.
- **Ejemplos:**
  - `"Artifact - Attraction->ExtraDeck"` — cartas de categoria "Artifact - Attraction" se colocan en la seccion "ExtraDeck" (MTG).
  - `"Extra deck->Extra_Deck"` — la categoria del deckbuilder "Extra deck" va a la seccion "Extra_Deck" (Yu-Gi-Oh). Notar que el nombre de categoria puede tener espacios, pero la seccion destino debe usar `_`.

---

### `sections.autoPlayFromHand` (object)
- **Label UI:** Play cards from Hand
- **Descripcion:** Where should a clicked card from hand go by default. The first value is the card type (should match the value used in your card file). The second value is the game section (should match the name used in this file).
- **Formato:** `{ "TipoCarta": "SeccionDestino" }`

```json
"autoPlayFromHand": {
  "Oro": "Oro",
  "Aliado - Bestia": "Defensa",
  "Arma": "Defensa",
  "Totem": "Apoyo"
}
```

---

### `sections.autoPlayFromStack` (object)
- **Label UI:** Play cards from Pile
- **Descripcion:** Where should the top card of the Pile go when a player press the Play button. Same model as play cards from Hand.
- **Formato:** Mismo formato que `autoPlayFromHand`.
- **Valor especial:** `"GROUP"` - En vez de mover la carta a una seccion, la agrupa con la carta objetivo (e.g., Auras en MTG se agrupan con la criatura que encantan).
- **Valor especial:** `"Discard"` - Envia la carta directamente al descarte/cementerio (e.g., Traps y Spells en Yu-Gi-Oh se resuelven y van al cementerio).
```json
"autoPlayFromStack": {
  "Enchantment - Aura": "GROUP",
  "Trap": "Discard",
  "Spell": "Discard"
}
```

---

### `sections.sectionsDict` (object)

Define el comportamiento de cada zona del tablero. Cada key debe coincidir con un nombre en `customSections`.

```json
"sectionsDict": {
  "NombreSeccion": {
    "title": "NombreSeccion",
    "isHidden": "no",
    "height": "BIG",
    "alignment": "CENTER",
    "opponentAlignment": false,
    "noAutoPayTo": false,
    "isHorizontalAllowed": false,
    "displayedTitle": "Titulo Visible",
    "noQuickActions": false,
    "enterTapped": false,
    "enterSpun": false,
    "isGroupForbidden": false,
    "keepTappedNewTurn": false,
    "showHiddenCardInHistory": false,
    "isDefaultSection": false,
    "drawPerTurn": 0,
    "cardBackColor": "#e0e0e0",
    "cardStyle": { ... },
    "reverseZOrder": false,
    "cardActionShortcut": { ... }
  }
}
```

#### `title` (string)
- **Label UI:** Title
- **Descripcion:** This is the identifier. It must match the value above. This is the area name you should use everywhere else on this file. Make sure there is no space (' ') in it, use '_' instead. If your game uses a resource mechanic like MTG or Lorcana, call the section 'Mana' for cards to be tapped automatically when paying cost.

#### `isHidden` (string)
- **Label UI:** Are cards hidden
- **Descripcion:** Who can see the card when it's played in this area? Ignored for cards that are already hidden to everyone.
- **Valores:**
  - `"no"` - Face up to everyone
  - `"opponent-only"` - Face down to your opponents only
  - `"yes"` - Face down to everyone

#### `height` (string)
- **Label UI:** Height
- **Descripcion:** Size of the cards played in this section.
- **Valores predefinidos:** `"SMALL"` | `"MEDIUM"` | `"BIG"` | `"HUGE"`
- **Valores numericos:** Tambien acepta valores numericos como string para alturas custom en vh (ej: `"12"`, `"16"`, `"12.5"`). Util para ajuste fino del layout cuando los predefinidos no calzan.
- **Ejemplo en Riftbound:** Battlefields usa `"12"`, secciones de campo usan `"16"`, variante multiplayer usa `"12.5"`.

#### `alignment` (string)
- **Descripcion:** Alineacion de las cartas en la seccion.
- **Valores:** `"START"` | `"CENTER"` | `"END"` | `"DECK"` | `"NONE"`
- `"DECK"` - Cards stack like a deck (pile). Useful for secondary decks/draw piles.
- `"NONE"` - No alignment, cards are freely positioned. Used for pile/stack zones.

#### `opponentAlignment` (string | false)
- **Label UI:** Different alignment for opponents
- **Descripcion:** For visual purpose, you might want the opponents card alignments in this section to be different from the main player's.
- **Valores:** `"START"` | `"CENTER"` | `"END"` | `false` (same as player)

#### `noAutoPayTo` (boolean | string)
- **Label UI:** No autopay to place cards in this section
- **Descripcion:** Cards played here are always played for free.
- **Nota:** `true` = no se cobra costo al jugar cartas aqui. Acepta tanto boolean como string (ej: `true`, `"true"`).

#### `isHorizontalAllowed` (boolean)
- **Label UI:** Are horizontal cards allowed
- **Descripcion:** Should horizontal cards be shown horizontally when played here? Or Vertically like normal cards? (like the hand for example).

#### `displayedTitle` (string)
- **Label UI:** Custom displayed title
- **Descripcion:** By default the area will have its title displayed. You can define a different name here. Keep empty to ignore it and use the default title.

#### `noQuickActions` (boolean)
- **Label UI:** No quick actions
- **Descripcion:** Hide the quick action buttons that affect all cards in the area.

#### `enterTapped` (boolean)
- **Label UI:** Cards enter tapped
- **Descripcion:** Should cards played here be tapped automatically.

#### `enterSpun` (boolean)
- **Label UI:** Cards enter rotated by 180 degrees
- **Descripcion:** Should cards played here be rotated by 180 degrees automatically.

#### `isGroupForbidden` (boolean)
- **Label UI:** Are grouped cards forbidden
- **Descripcion:** If set to yes, a grouped card moved here will be ungrouped.

#### `keepTappedNewTurn` (boolean)
- **Label UI:** Keep tapped on new turn
- **Descripcion:** All cards are untapped when the new turn starts. Set this to yes if you want cards in this area to only be untapped manually by the player.

#### `showHiddenCardInHistory` (boolean)
- **Label UI:** Hidden cards appear in history
- **Descripcion:** If set to yes, a faced down card played here will have its name appear in the history. Use this if the card is played faced down but needs to be revealed to other players.

#### `logWhenPlayed` (boolean)
- **Descripcion:** If `true`, when a card is played in this section it appears in the game history/log. Useful for sections con `isHidden: "yes"` donde se quiere que el oponente sepa que se jugo una carta sin revelar cual es. Descubierto en Lorcana (seccion Inkwell/Mana).
- **Ejemplo:** En Lorcana, la seccion Mana tiene `"isHidden": "yes"` y `"logWhenPlayed": true` — las cartas entran boca abajo pero el oponente ve en el historial que se jugo una carta ahi.

#### `autoPayFrom` (boolean)
- **Descripcion:** If `true`, cards in this section can be tapped to pay mana costs, similar to the `Mana` section. Useful for sections that contain mana-producing cards but are not the main mana section (e.g., Commander zone in MTG).

#### `isDefaultSection` (boolean)
- **Descripcion:** Marks this section as the default play area. When a card type is not mapped in `autoPlayFromHand`, it goes here. Typically used for a general "pile" or "stack" section.
- **Ejemplo:** The `Stack` section in Riftbound uses `"isDefaultSection": true`.

#### `drawPerTurn` (number)
- **Descripcion:** Number of cards automatically drawn from this section at the start of each turn. Independent from the global `newTurn.drawPerTurn` (which draws from the main Deck). Useful for secondary decks that have their own draw rate.
- **Ejemplo:** `2` - Draw 2 cards from this section each turn.

#### `cardBackColor` (string, color hex)
- **Descripcion:** Custom background color for card backs in this specific section. Overrides the global `cards.cardBackColor`.
- **Ejemplo:** `"#e0e0e0"`

#### `cardStyle` (object)
- **Descripcion:** CSS style object applied to individual cards within this section. Useful for visual adjustments like overlapping cards.
- **Ejemplo:** `{ "marginTop": "-2vh" }` makes cards overlap vertically.

#### `reverseZOrder` (boolean)
- **Descripcion:** If `true`, reverses the z-order (stacking order) of cards in this section. Later cards appear behind earlier ones instead of on top. Useful for sections where you want the first card to always be visible.

#### `cardActionShortcut` (object)
- **Descripcion:** Adds a shortcut button on each card in this section that triggers an action when clicked. Avoids needing to drag cards manually for common operations.

```json
"cardActionShortcut": {
  "action": "MOVE",
  "actionData": {
    "destination": "Runes",
    "position": "BOTTOM"
  },
  "image": "https://example.com/recycleButton.png"
}
```

- `action` (string) - The action type. Known value: `"MOVE"`.
- `actionData` (object) - Action parameters:
  - `destination` (string) - Target section name (including built-ins like `"ExileHidden"`).
  - `position` (string, optional) - Where in the destination: `"BOTTOM"`, `"TOP"`.
- `image` (string, URL) - Button icon image. Optional — si se omite, se muestra un boton por defecto.

---

## Card List: Tokens creables por carta

En el archivo de card list, las cartas pueden definir un campo `tokens` que permite al jugador crear tokens/cartas con click derecho sobre la carta fuente. Los tokens creados deben existir como entradas en el mismo card list.

```json
"mi-carta-001": {
  "id": "mi-carta-001",
  "name": "Carta Creadora",
  "type": "Aliado",
  ...
  "tokens": ["token-001", "token-002"]
}
```

- `tokens` (array of strings) - Array de IDs de cartas del card list que esta carta puede crear. La carta creada se considera un token en juego.
- Las cartas referenciadas no necesitan tener `"isToken": true`, pero el resultado creado se tratara como token.

---

## Card List: Campo `_legal`

El campo `_legal` en cada carta del card list controla la **legalidad por formato** y permite **overrides de `maxPerCard` por carta individual**. Funciona en conjunto con `checkCardLegality` en el deckRuleset y `legalityCode` en el formato.

### Requisitos

1. El formato debe tener un `legalityCode` (ej: `"IR"`, `"EDH"`).
2. El deckRuleset debe tener `"checkCardLegality": true`.
3. Cada carta debe tener un campo `_legal` con una key que coincida con el `legalityCode`.

### Valores posibles

| Valor | Tipo | Efecto |
|---|---|---|
| `true` | boolean | Carta legal. Usa el `maxPerCard` global del formato. |
| `false` | boolean | Carta **baneada**. No aparece en el deckbuilder para ese formato. |
| `1` | number | Legal, maximo **1 copia** (override de maxPerCard). |
| `7` | number | Legal, maximo **7 copias**. |
| `50`, `99`, `200` | number | Legal, practicamente **ilimitada**. |

> **Regla general:** Cuando el valor es un numero, ese numero se convierte en el `maxPerCard` para esa carta especifica en ese formato, ignorando el limite global.

### Ejemplo en el card list

```json
{
  "carta-normal-001": {
    "id": "carta-normal-001",
    "name": "Aliado Comun",
    "type": "Aliado",
    "_legal": { "IR": true }
  },
  "carta-unica-001": {
    "id": "carta-unica-001",
    "name": "Dragon Dorado",
    "type": "Talismán",
    "_legal": { "IR": 1 }
  },
  "carta-ilimitada-001": {
    "id": "carta-ilimitada-001",
    "name": "Hitodama",
    "type": "Talismán",
    "_legal": { "IR": 50 }
  },
  "carta-baneada-001": {
    "id": "carta-baneada-001",
    "name": "Carta Prohibida",
    "type": "Aliado",
    "_legal": { "IR": false }
  }
}
```

### Ejemplo del game JSON correspondiente

```json
"formats": [{
  "title": "Imperio Racial",
  "gameplay": "Classic",
  "deckRuleset": "Imperio_Racial",
  "legalityCode": "IR"
}],
"deckRulesets": {
  "Imperio_Racial": {
    "checkCardLegality": true,
    "general": {
      "min": 50,
      "max": 50,
      "maxPerCard": 3
    }
  }
}
```

Con esta configuracion:
- Cartas con `"IR": true` → max 3 copias (regla global).
- Cartas con `"IR": 1` → max 1 copia (cartas Unicas).
- Cartas con `"IR": 50` → hasta 50 copias (cartas mercenarias / copias ilimitadas).
- Cartas con `"IR": false` → no aparecen en el deckbuilder.

### Multiples formatos

Una carta puede tener legalidad distinta en cada formato:

```json
"_legal": {
  "IR": 1,       // Unica en Imperio Racial
  "CL": true,    // Normal en Clasico (3 copias)
  "UN": false    // Baneada en Unificado
}
```

### Valores numericos observados en MTG

| Valor | Uso en MTG | Cartas ejemplo |
|---|---|---|
| `1` | Cartas unicas (EDH singleton) | Todas las cartas en Commander |
| `7` | Limite especial de 7 | Seven Dwarves |
| `9` | Limite especial de 9 | Nazgul |
| `99` | Tierras basicas (ilimitado) | Swamp, Forest, Island, etc. |
| `200` | Copias ilimitadas | Relentless Rats, Shadowborn Apostle, Persistent Petitioners |

> **Descubierto por ingenieria inversa** del card list de MTG en TCG Arena (`valcur/TCG-Arena-MTG`). No hay documentacion oficial de este campo.

---

## Secciones por defecto (no necesitan declararse)

Las siguientes secciones existen automaticamente y NO deben incluirse en `customSections`:

| Seccion       | Descripcion                                      |
|---------------|--------------------------------------------------|
| `Hand`        | Mano del jugador                                 |
| `Deck`        | Mazo principal                                   |
| `Stack`       | Pila (pile) - zona temporal                      |
| `Discard`     | Cementerio / descarte                            |
| `Exile`       | Zona de exilio / removida del juego              |
| `ExileHidden` | Zona de exilio oculta (no visible para nadie)    |

> **Nota:** `Stack` puede ser redefinido en `sectionsDict` para personalizar su comportamiento (height, alignment, etc.) y marcarse como `isDefaultSection`. Esto es util cuando se quiere que cartas sin mapeo en `autoPlayFromHand` vayan a la pila en vez de no tener destino.
>
> **Nota:** Las secciones built-in (`Discard`, `Exile`, `ExileHidden`) pueden usarse como destino en `autoPlayFromStack`, `cardActionShortcut`, y `categoriesAlreadyOnBoard` sin necesidad de declararlas en `customSections`.

---

## Archivo de Traducciones

El archivo referenciado por `translationsUrl` permite traducir labels de la UI sin modificar el game JSON ni el card list. Descubierto en Lorcana (`Valcur/TCG-Arena-Lorcana`).

### Estructura

```json
{
  "additionalLanguages": ["es"],
  "en": {
    "Gameplay": {
      "Classic": "Classic"
    },
    "Big stuffs": {
      "translations.customHelp": "Help text in English...",
      "translations.mulliganInfo": "Mulligan rules in English..."
    }
  },
  "es": {
    "Deck - Card types": {
      "Ally": "Aliado",
      "Weapon": "Arma",
      "Totem": "Tótem",
      "Talisman": "Talismán",
      "Gold": "Oro"
    },
    "Deck - Filters": {
      "type": "Tipo",
      "cost": "Coste",
      "race": "Raza",
      "set": "Set",
      "ability": "Habilidad"
    },
    "Gameplay": {
      "Classic": "Clásico"
    },
    "Sections": {
      "Gold_Reserve": "Reserva de Oro",
      "Gold_Paid": "Oro Pagado",
      "Attack": "Ataque",
      "Defense": "Defensa",
      "Support": "Apoyo"
    },
    "Big stuffs": {
      "translations.customHelp": "Texto de ayuda en español...",
      "translations.mulliganInfo": "Reglas de mulligan en español..."
    }
  }
}
```

### Categorias traducibles

| Categoria | Que traduce | Ejemplo |
|---|---|---|
| `Deck - Card types` | Valores del campo `type` en las cartas | `"Character" → "Personage"` |
| `Deck - Card color` / filtros | Nombres de filtros y sus valores | `"color" → "Couleur"`, `"Amber" → "Ambre"` |
| `Deck - Others` | Atributos de carta (keys custom) | `"cost" → "coût"`, `"strength" → "force"` |
| `Gameplay` | Nombres de modos de juego | `"Classic" → "Classique"` |
| `Sections` | Nombres de secciones del tablero (`displayedTitle`) | `"Main" → "Principale"` |
| `Big stuffs` | Textos largos referenciados con prefijo `translations.` | `customHelp`, `mulligan.info` |

### Patron `translations.` prefix

Si un campo del game JSON (como `customHelp` o `mulligan.info`) tiene un valor que comienza con `translations.`, TCG Arena lo reemplaza con el texto correspondiente del archivo de traducciones. Esto permite manejar textos largos multi-idioma fuera del game JSON.

```json
// En el game JSON:
"customHelp": "translations.customHelp"

// En el translations JSON:
"en": { "Big stuffs": { "translations.customHelp": "English help..." } },
"es": { "Big stuffs": { "translations.customHelp": "Ayuda en español..." } }
```

### Notas

- `additionalLanguages` define los idiomas extra ademas de ingles.
- El idioma `"en"` es el base/default.
- Los nombres de las categorias (ej: `"Deck - Card types"`, `"Big stuffs"`) son organizacionales — lo que importa son las keys dentro de cada categoria.
- No todos los campos son traducibles. Solo se ha confirmado: `customHelp`, `mulligan.info`, labels de filtros, valores de tipo, nombres de secciones, y nombres de gameplay.
- Descubierto por ingenieria inversa del proyecto Lorcana. No hay documentacion oficial.

---

## Notas sobre Tipos de Datos

TCG Arena es flexible con los tipos en varios campos. Los siguientes campos aceptan indistintamente `number` o `string`:

| Campo | Ejemplo number | Ejemplo string |
|-------|---------------|----------------|
| `cardRotation` | `45` | `"90"` |
| `mulligan.startingHandSize` | `7` | `"5"` |
| `newTurn.drawPerTurn` | `0` | `"1"` |
| `countersStartingValues[]` | `[40, 0]` | `["8000"]` |
| `sectionsDict.height` | — | `"12"`, `"SMALL"` |
| `noAutoPayTo` | `false` | `"true"` |

> **Recomendacion:** Aunque TCG Arena acepta ambos tipos, conviene ser consistente dentro del mismo archivo. Los ejemplos oficiales mezclan tipos libremente.

---

## Referencia Rapida por Juego

Patrones comunes observados en los juegos de ejemplo:

| Caracteristica | Yu-Gi-Oh | Magic the Gathering | Riftbound | Lorcana |
|---|---|---|---|---|
| Turnos | Alternados | Alternados | Alternados | Alternados |
| Robo por turno | 1 automatico | 1 automatico | 0 (manual) | 0 (no definido) |
| Mulligan | Sin mulligan | Mano nueva + devolver | Boton manual, sin barajar | Devolver y robar igual cantidad |
| Tokens | Ninguno | 2 unicos (Monarch, Initiative) | Ninguno | Ninguno |
| Draggable tokens | Ninguno | 4 (colores) | 6 (stun, buff, etc.) | Ninguno |
| Secciones custom | 14 | 6-9 (segun formato) | 7-10 (segun modo) | 4 (Main, Mana, Items, Test) |
| Modos de juego | 1 (Classic) | 3 (Classic, Commander, Oathbreaker) | 2 (Classic, Multiplayer) | 1 (Classic) |
| categoriesAlreadyOnBoard | Extra deck | Runes, Battlefields, etc. | Legend, Chosen_Champion, etc. | Ninguno |
| autoPlayFromStack | Trap/Spell → Discard | Auras → GROUP | Varies | Action → Discard |
| Layout principal | row | column | column | column |
| Contadores | 1 (8000 LP) | 1-2 (vida + veneno) | 1 (0) | 1 (0) |
| Traducciones | No | No | Minima (gameplay) | Completa (multi-idioma) |
| hideFacedDownCards | false | false | false | true |
| logWhenPlayed | No | No | No | Si (Mana/Inkwell) |

---

## Ejemplo Minimo Completo

```json
{
  "name": "Mi_Juego",
  "menuBackgroundImage": "https://ejemplo.com/fondo.png",
  "defaultRessources": {
    "backgrounds": ["https://ejemplo.com/playmat.png"],
    "decksUrl": ""
  },
  "customHelp": "Reglas del juego aqui",
  "cardRotation": 45,
  "cards": {
    "dataUrl": "https://ejemplo.com/cards.json",
    "cardBack": "https://ejemplo.com/cardback.png"
  },
  "deckBuilding": {
    "mainFilters": ["type", "cost", "name"],
    "formats": [
      {
        "title": "Standard",
        "gameplay": "Classic"
      }
    ]
  },
  "gameplay": {
    "Classic": {
      "mulligan": {
        "info": "Draw 7 cards",
        "startingHandSize": 7,
        "drawNewHand": true,
        "putSelectionAtBottom": false,
        "drawNewSelectedCards": false
      },
      "newTurn": {
        "drawOnStart": true,
        "sharedTurn": false,
        "firstPlayerTokenName": "",
        "drawPerTurn": 1
      },
      "defaultNotes": "",
      "tokens": [],
      "countersStartingValues": [20],
      "hideFacedDownCards": false,
      "sections": {
        "customSections": ["Battlefield"],
        "layout": {
          "direction": "column",
          "isSymetricalForOpponents": true,
          "content": [
            {
              "direction": "row",
              "style": false,
              "content": [
                {
                  "section": "Battlefield",
                  "style": { "flex": 1 }
                }
              ],
              "isSymetricalForOpponents": false
            }
          ]
        },
        "categoriesAlreadyOnBoard": [],
        "autoPlayFromHand": {},
        "autoPlayFromStack": {},
        "sectionsDict": {
          "Battlefield": {
            "title": "Battlefield",
            "isHidden": "no",
            "height": "BIG",
            "alignment": "CENTER",
            "opponentAlignment": false,
            "noAutoPayTo": false,
            "isHorizontalAllowed": false,
            "displayedTitle": "",
            "noQuickActions": false,
            "enterTapped": false,
            "enterSpun": false,
            "isGroupForbidden": false,
            "keepTappedNewTurn": false,
            "showHiddenCardInHistory": false
          }
        }
      }
    }
  }
}
```
