# Changelog

Auto-deploy a GitHub Pages: sin versionado, las entradas van por fecha.

El detalle de cada jornada de trabajo está en [`docs/activity/`](docs/activity/).

---

## 2026-10-16

- **Agrega la línea Drácula: Rey Vampiro y rota Bestiarium**
  Entran 270 cartas (set principal, 4 kits, 50 Inmortales y Promociones CasaMyL 2026) en la
  temporada nueva `Drácula`. Rota la temporada Bestiarium: salen 394 cartas; sus Inmortales y
  las reimpresas en los mazos precon se mantienen.
- **Agrega conversor desde codicetcg**
  `scripts/convert_codice_to_cards_json.py`, para ediciones que `api.myl.cl` aún no publica. Las
  imágenes de Drácula apuntan provisoriamente al CDN de codicetcg.
- **Corrige la vigencia de los Inmortales**
  Se acumulan y nunca rotan: entran los 16 nombres nuevos del lote de Drácula y Arturo de
  Bretaña, que faltaba del lote de AyD.
- **La vigencia pasa a definirse por el dragón de frecuencia**
  Revisión visual del emblema de todas las impresiones vigentes. Los mazos precon llevan el
  dragón de KvM, no el de AyD: 102 cartas pasan a rotar con KvM. Las reimpresiones de los
  kits de Drácula traen su dragón original (KvM o AyD) y no se extienden a Drácula, igual
  que las promos "Desafiantes" de CasaMyL (KvM). Salen Gog de Bestiarium (era otra carta que
  el Gog de AyD) y Lágrima de Dragón (su SP de KvM trae el dragón de Bestiarium). Nuevo
  `scripts/revisar_dragones.py` para revisar las próximas ediciones.
- **El filtro Set solo muestra temporadas vigentes**
  Las impresiones de Bestiarium que siguen legales salen sin Set; su edición real sigue en
  `Edicion`.
- **Búsqueda sin tildes y nombres con mayúsculas parejas**
  Se quitan todos los diacríticos, no solo las tildes: "Martillo Mjölnir" se encuentra como
  "Mjolnir" y "Vâlve Albe" como "Valve" (la ñ se conserva). Ahora también en los campos
  Habilidad y Edición. Los conectores de los nombres van en minúscula ("Yelmo De Mambrino" →
  "Yelmo de Mambrino"), así las reimpresiones de codicetcg se agrupan como estilos.
- **Corrige nombres y datos de cartas existentes**
  Unifica "Cienpiés-SP" (dos grafías), corrige "Martillo Mjölnir", "Trempulcahue" y las
  mayúsculas de 20 Inmortales. Repara 9 nombres a los que la API les borró la Á o la ñ
  ("Ngel Gadreel", "Caon Helios", "O Carmelito"…) y que por eso no heredaban la vigencia de
  sus reimpresiones, más "Cruz de Borgoña" y "Puertas Grandes y Pequeñas". Agrega "Ángel" a
  Castiel, Sandalfón y Abadón, como vienen impresas. La API les había puesto otro nombre a
  tres cartas: "Principe Orion" de Onyria es Ismael, "Rlyeh" es Casa de Opio y "Vuelo
  Mágico" es Polvo de Hadas. Las cartas distintas que comparten nombre llevan sufijo:
  "Alicanto (Aliado)" y "Jonathan Harker (Drácula)". Bayou St. John es Tótem, no Talismán.
- **Actualiza banlist — lista oficial de octubre**
  Kuchiku el Cazador pasa de limitada a 2 a limitada a 1. Entran limitadas a 1 Espada de
  O'Higgins, Duelo de Dragones, Escamas de Dragón, Lilith y Jinete de la Peste. Se limpian 12
  IDs rotados con Bestiarium. Shakar Raj se mantiene limitada a 1 aunque no aparece en la
  tabla. "Metatron" pasa a llamarse "Ángel Metatrón", como en la lista y en la carta.

- **Versiona `CLAUDE.md`, `GAME_JSON_DOCS.md` y las listas de restricciones**
  La documentación del proyecto vivía solo en disco por el `*.md` del `.gitignore`.

→ [Detalle completo](docs/activity/changelog-2026-10-16.md)

---

## 2026-08-09

- **Actualiza banlist — última actualización oficial 08/07/26**
  Entran prohibidas Ereshkigal (subía de limitada a 2) y Resistencia de Acero (subía de
  limitada a 1); Sherlock Holmes baja a limitada a 2; entran limitadas Mariano Osorio (2),
  Voragh el Devorador (1) y Ángel Metatrón (1). Se liberan Los Umbras y Alicia en Wonderland.
  Salen Niten Ichi-Ryu y Anillo de Vacío por estar fuera de rotación. Shakar Raj se mantiene
  limitada a 1 pese a no aparecer en la tabla publicada (omisión del publisher).
  IDs resueltos por nombre contra el pool real, incluidas todas las reimpresiones.
- **Quita las tildes de los nombres de las cartas**
  El buscador de TCG Arena hace match literal, así que "Baculo" no encontraba "Báculo de los
  Eternos". `strip_accents()` lo aplica en el build; la ñ se conserva y `cards_json/` mantiene
  sus tildes para que un re-scrape no haya que parcharlo.

---

## 2026-07-25

- **Agrega rotación de formato IMP, nuevo set AyD, precon, Chile Oscuro y Toolkit 2026**
  Rotan los sets 125, 126 y 136. Entran 6 sets nuevos convertidos desde los dumps de la API.
- **Actualiza banlist**
  Lista oficial de julio, con los IDs resueltos por nombre contra el pool real.
- **Corrige tildes y ortografía de los nombres de las cartas**
  TCG Arena agrupa reimpresiones como "estilos" solo si el nombre coincide exactamente.
- **Agrupa por set global**
  `Set` pasa a ser la temporada (5 valores) para que el filtro salga como dropdown; el
  título real del set queda en `Edicion`.
- **Elimina cartas huérfanas que ya rotaron pero se encuentran reimpresas en productos vigentes**
  44 cartas que sobrevivían por compartir producto con sets vigentes.
- **Agrega campo de vigencia en las cartas**
  Declara por nombre con qué temporada rota cada carta, o si es inmortal.
- **Corrige nombres corruptos**
  Caracteres perdidos por la API, contrastados contra un dump externo.
- **Corrige el separador de los Aliados de múltiples razas**
  8 cartas traían la raza con espacio en vez de `/` o sin tilde (`Dragon Sombra`,
  `Bestia Faerie`…). Corregidas en `cards_json/`, que es el origen.
- **Agrega un warning para capturar separadores distintos al esperado**
  `build_card_list.py` ahora avisa de razas malformadas en vez de absorberlas en
  silencio, para que un scrape nuevo no las reintroduzca sin que nadie lo note.

→ [Detalle completo](docs/activity/changelog-2026-07-25.md)

## 2026-05-09

- **Agrega nuevas cartas e importa las habilidades para su búsqueda**

## 2026-04-30

- **Actualiza banlist 24-04-2026**
- **Modifica configuración de juego para incluir nuevo mulligan**
- **Elimina sección de selection count**
- **Actualiza configuración selection count min: 0**
- **Modifica configuración para probar mulligan sin seleccionar**
- **Modifica configuración para asimilar a config de MTG sobre selection count**
- **Ajusta pasos de mulligan para robar 1 menos cada mulligan**
- **Modifica traducciones para que español sea el lenguaje por defecto**

## 2026-04-19

- **Agrega cartas nuevas vudú**
- **Agrega cartas nuevas sueltas del toolkit**
- **Agrega carta nueva**
- **Corrige formato de imagen png → jpeg**

## 2026-04-14

- **Agrega nueva carta**
- **Corrige filtro por coste modificando el coste de los oros null → 0**

## 2026-04-12

- **Agrega script para generar cartas y banlist para aplicar la legalidad correspondiente**
  `build_card_list.py`: transforma `cards_json/` + `myl_banlist.json` en el card list publicado.
- **Agrega cartas nuevas**
- **Corrige tildes en raw data para tipos y raza**
- **Agrega fixes para cuando el raw data venga sin tildes definidos**

## 2026-04-06

- **Actualiza banlist 06-04-2026**

## 2026-04-04

- **Agrega token oro virtual para cartas que generan oro**
- **Agrega deck temporal para usarlo de transición y separación de descarte y/o búsqueda**
  Renombrado a "zona temporal" en el mismo día.
- **Agrega tokens genéricos** (estilo MTG en TCG Arena)
- **Agrega acciones rápidas a cartas** (oros y cartas en línea de ataque/defensa)
- **Agrega botón flecha hacia abajo para botones de agrupación**

## 2026-04-02

- **Agrega en filtros de carta aliados sin raza**
- **Agrega traducciones**
- **Agrega zona opcional para efectos activos y/o recordatorios**
- **Modifica cost de las cartas Oro null → 0**
- **Modifica campo ability: cadena de texto sin espacios ni saltos de línea**
  Necesario para que la búsqueda por habilidad funcione.
- **Modifica campo `set` a `Set` en las cartas y en el game json**

## 2026-04-01

- **Restaura acción de cartas por defecto y cambia alignment de Destierro a discard** (test)
- **Elimina Destierro para usar Exile built-in**
- **Mapea oro inicial a oro reserva en el deckbuilder**
- **Agrega AutoPlayFromStack para distintos tipos de carta**
- **Modifica flex para las secciones de oro**
- **Agrega opción para ignorar costo de oro en el deckbuilder**
- **Ajusta layout en los anchos de las secciones oro y oro pagado**
- **Reorganiza layout para mantener fidelidad**
- **Invierte secciones oro pagado y oro reserva**
- **Agrega assets iniciales**
- **Agrega checks de legalidad por carta** para cartas únicas, mercenarias y banlist
- **Modifica host para archivos de logo y carta boca abajo**
- **Agrega habilidades a todas las cartas y organiza Sets y Razas por arrays**
- **Reorganiza filtros y añade Habilidades**

## 2026-03-31

- **Inicio de proyecto**
- **Agrega url de lista de cartas en el archivo de juego**
- **Agrega url para obtener las cartas**
- **Modifica tamaño de las secciones**
- **Agrega mejoras respecto a las secciones de construcción de mazo, filtros y estados de juego**
  Todo pasa por la pila antes de ser jugado.
- **Modifica alignment de las cartas en destierro, línea de defensa y ataque**
- **Agrega simetría en filas internas**
- **Actualiza README**
