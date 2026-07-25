# Changelog

Auto-deploy a GitHub Pages: sin versionado, las entradas van por fecha.

El detalle de cada jornada de trabajo está en [`docs/activity/`](docs/activity/).

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
