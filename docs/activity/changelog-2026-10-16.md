# 2026-10-16 — Drácula: Rey Vampiro y rotación de Bestiarium

Detalle técnico de la jornada. Resumen en el [CHANGELOG](../../CHANGELOG.md).

## Origen de los datos

`api.myl.cl` todavía no publica Drácula (las imágenes de los códigos 171–182 dan 404), así
que la edición se sacó de codicetcg, con dos archivos guardados a mano:

- `dump_json_codice_upto_dracula.json`: la respuesta XHR de la librería, con 1789 cartas IMP
  de todas las ediciones vigentes.
- `dump_html_codice_dracula.html`: la librería filtrada por las 7 ediciones nuevas. Es la
  fuente de verdad: se convierten las 270 cartas del JSON cuya imagen aparece en el HTML
  (coinciden exacto con las ediciones 173–178 y 903 del JSON).

Nuevo `scripts/convert_codice_to_cards_json.py` para reproducir la conversión.

| Archivo | Edición | Cartas | IDs |
|---------|---------|--------|-----|
| `CODICE178_dracula_rey_vampiro.json` | IMP - Drácula: Rey Vampiro | 155 | `DRACULA-001`…`135`, `186`…`206` |
| `CODICE174_dracula_cazadores_nocturnos.json` | IMP - Drácula: Cazadores Nocturnos | 10 | `DRACULA-136`…`145` |
| `CODICE175_dracula_hijos_de_la_noche.json` | IMP - Drácula: Hijos de la Noche | 11 | `DRACULA-146`…`155`, `193` |
| `CODICE176_dracula_carmilla_la_condesa.json` | IMP - Drácula: Carmilla la Condesa | 15 | `DRACULA-156`…`170` |
| `CODICE177_dracula_ruthven_el_vampiro.json` | IMP - Drácula: Ruthven el Vampiro | 15 | `DRACULA-171`…`185` |
| `CODICE903_dracula_rey_vampiro_inmortales.json` | IMP - Drácula: Rey Vampiro - Inmortales | 50 | `DRACULA-207`…`256` |
| `CODICE173_promos_casamyl_2026.json` | IMP - Promociones CasaMyL 2026 | 14 | `PROMOS_CASAMYL_2026-*` |

- Toda la línea Drácula comparte una numeración lineal (001–256) en codicetcg, la misma
  forma en que la API numeró AyD Vigilantes (set + kits + Inmortales en un solo correlativo).
  Por eso comparten el prefijo `DRACULA-`: si la API publica la edición, debería bastar con
  cambiar las URLs de imagen sin tocar los IDs (y sin romper mazos guardados).
- Promociones CasaMyL 2026 se asignó a la temporada Drácula.

## Errores de codicetcg corregidos

Verificados contra la imagen de cada carta. Viven en los diccionarios `*_FIXES` del
conversor, para que una reconversión no los pierda.

- **Tipo**: Libro de Enoc, Bastón de la Bestia y Muñeco Vudú son Oros (codicetcg: Talismán).
- **Coste**: Psicofonía 1, Seducción 1, Sacrificio Solar 0, Carruaje Infernal 0 (venían vacíos).
- **Raza**: Jonathan Harker de Drácula es Caballero/Héroe (venía vacía). La Catrina y Nanna
  sí son Sin Raza, igual que en sus impresiones anteriores.
- **Nombre**: "Nocturlabio de Llull" (codicetcg: "Liull"), "Vâlve Negre" ("Välve").
  "Quincery Morris", "Legua Muerta" y "Rey de los Loçolicos" vienen así impresas.
- **Habilidad**: "previen"/"Preven" → "prevén"/"Prevén", "júgalo" → "juégalo", "Tótems" →
  "Tótem" (el plural impreso es invariable), y tres typos puntuales (Romualdito, Pan de
  Muerto, Hacha de Seth).
- **Versiones alternativas**: las Legendarias 198–206 vienen en codicetcg en MAYÚSCULAS o con
  typos ("mejor" por "menor"). Mismo nombre y estadísticas = misma carta, así que toman el
  texto de su impresión base.
- **Oro básico**: el Oro sin habilidad de la edición se llama "Drácula" en codicetcg, igual
  que el Oro UR "Drácula" de Onyria, que sigue vigente. Para que TCG Arena no los agrupe como
  estilos de una sola carta se renombró "Drácula Rey Vampiro" (mismo criterio que
  "Kaiju Vs Mecha Titanes").

## Rotación de Bestiarium

`TEMPORADAS_VIGENTES` cambia `Bestiarium` por `Drácula`. Salen 394 cartas, todas con vigencia
Bestiarium (incluidas 5 reimpresiones JO/SP en KvM y Libertadores que no extienden
legalidad). Se mantienen 98 impresiones de la temporada Bestiarium:

- 54 Inmortales. De 22 de esos nombres, la de Bestiarium es la única impresión que hay.
- 44 reimpresas en los mazos precon (vigencia AyD Vigilantes) u Onyria.

`Set` ahora solo lista temporadas vigentes: esas 98 salen con `Set: []`, de modo que
"Bestiarium" desaparece del dropdown. La edición real sigue en `Edicion`.

## Vigencia

- **Inmortales**: se acumulan y nunca rotan. El lote de Drácula comparte 25 nombres con el
  de AyD y trae 25 distintos; los 16 que no eran Inmortales entran como `Inmortal`. Faltaba
  Arturo de Bretaña, del lote de AyD. Total: 126 nombres.
- **Mismo nombre**: mismo texto, o el mismo con errata de redacción = misma carta; carta
  completamente distinta = rota con su set.

### Dragón de frecuencia

La vigencia de cada impresión la marca su dragón de frecuencia, el emblema junto a la caja
de texto. El color indica la frecuencia; lo que importa es el símbolo. Ni codicetcg ni la
API lo traen como dato:
- codicetcg solo marca `nv: true` en 21 JO/SP.
- La API trae `date_empire_valid` por edición, y para los precon dice la fecha de AyD
  aunque llevan el dragón de KvM.

Así que se revisaron a ojo los emblemas de todas las impresiones de productos mixtos
(kits, precon, toolkits, promos y secciones P/SP/JO de cada set): ~640 de las 1589 cartas
del dump, recortadas en hojas de contacto. Los sets principales se validaron con un
clasificador de forma (99.8 % de acierto). Una segunda pasada con recortes más grandes
corrigió tres JO mal leídas en la primera (Onyria sobre anillo verde se confunde con el
robot de KvM si el recorte es chico). La vigencia de cada carta es la del dragón más
reciente entre sus impresiones, ignorando los logos especiales de promos.

Hallazgos:
- **Precon (Mazo Dragón, Eterno y Guerrero)**: las 135 cartas llevan el robot de KvM.
  `SET_TO_SEASON` los pasa a KvM y 102 nombres que rotaban con AyD pasan a KvM.
- **Kits y promos de Drácula**: ninguna reimpresión trae el murciélago, así que no se
  extienden a Drácula.
  - Con el robot de KvM: Tamales, Muñeco Vudú, Psicofonía, Bayou St. John, Romualdito,
    Pan de Muerto, Acabar la Esperanza, Activar Tenshi Z, El Caleuche, Duelo Espacial,
    Diadema Celestial, Fortaleza Hoshi, La Catrina, Culto a la Muerte, Daga Ritual,
    Ofrenda a los Abuelos, Guadaña de Santa Muerte y Maldición Vudú.
  - Con el dragón de AyD: Juicio de Vigilantes, Fuego Purificador, Visión de Enoc, Espada
    del Juicio, Sacrificio Solar, El Abismo y Libro de Enoc. Libro de Revelaciones, aunque
    es una carta nueva, también trae el de AyD.
- **Promos CasaMyL 2026**: las 001–003 traen murciélago; las 025–035 ("Desafiantes",
  Pirámide de Guiza, Remate Mortal…) traen el robot y rotan con KvM.
- **Kits de AyD**: varias cartas traen dragones viejos. Alicia en Wonderland y Dulce
  Canasta traen el de Onyria, Miguel Grau el de Libertadores, y Mano de Destrucción,
  Lanza Argenta y las reimpresiones promo de AyD el robot de KvM.
- **Secciones SP/JO de KvM y Libertadores**: muchas traen el dragón de Onyria o de
  Bestiarium. Eso confirma, por ejemplo, que Behemot o Rey de Amarillo rotaron con
  Bestiarium.
  - Las JO de KvM de Conde Drácula, Sombrerero Loco y Cuervo Nocturno traen el dragón de
    Onyria, así que las dos primeras siguen rotando con Onyria.
  - Monumento Inmortal (solo existe como JO de KvM, con dragón de Onyria) pasa a Onyria.
  - Lágrima de Dragón (solo existe como SP de KvM, con dragón de Bestiarium) ya rotó y sale
    del pool.
- **Logos especiales**, que se ignoran: fénix JO (Onyria), estrella SP y serie Rapa
  Nui/kiwi (Libertadores), escudo chileno (JO de KvM), "25 Años", Pecados Capitales,
  dragón asiático y la serie Wonderland/Quijote.

### Cartas distintas con el mismo nombre

La revisión también destapó colisiones que ya existían: Moloch y Gog (Bestiarium vs AyD),
Príncipe Orión (Onyria vs precon) y Alicanto (Oro de los precon vs Aliado de Libertadores).
Gog de Bestiarium sobrevivía gracias a una entrada pensada para el de AyD, y sale del pool.
Para Alicanto se agregó `vigencia_por_id` al build: un override por ID que manda sobre el
nombre.

En cambio, Cuervo Nocturno, Trentren Vilu, Antonio Pincheira, Escarapela Nacional, Terminal
P-12 y Guerrillero Rodríguez son erratas de la misma carta.

## Nombres y datos existentes

- `strip_accents()` quita cualquier diacrítico vía NFD, no solo las tildes del castellano
  (había que cubrir los nombres rumanos de Drácula). La ñ se conserva.
- "Cienpiés-SP" tenía dos grafías ("Cienpies-Sp" en 3 sets, "Ciempiés-SP" en los precon) y
  TCG Arena las mostraba como cartas distintas. Unificada como viene impresa, también en
  `convert_raw_to_cards_json.py`.
- "Martillo Mjlnir" → "Martillo Mjölnir" (la API perdió la ö). "Trempulcahue Bestiarium" →
  "Trempulcahue".
- Mayúsculas de 20 Inmortales alineadas con codicetcg ("Batalla De Azincourt" →
  "Batalla de Azincourt", "Cleopatra Vii" → "Cleopatra VII"…): se reimprimen en cada
  temporada, y "Caminar El Tablon" ya se separaba de su reimpresión de Drácula.
- 9 nombres a los que la API les borró la Á o la ñ, corregidos con la grafía de codicetcg:
  Ángel Vengador, Ángel Gadreel, Ángel Eistibus, En las Montañas de la Locura, Ángel del
  Desierto, Ño Carmelito, Cañón Helios, Escuadrón Ángel y Cambiar de Tamaño. Varios tienen
  reimpresiones con el nombre bien escrito, y la vigencia (que se hereda por nombre) no les
  llegaba: Ángel Gadreel y Ángel Vengador de Onyria pasan a rotar con KvM.
- Castiel, Sandalfón y Abadón (AyD) son "Ángel Castiel", "Ángel Sandalfón" y "Ángel Abadón",
  igual que Ángel Metatrón (verificado en la carta).
- "Cruz De Borgoa" y "Puertas Grandes Y Pequeas" también habían perdido la ñ.
- Cruzando por texto contra codicetcg dentro de cada edición aparecieron cartas a las que la
  API les puso otro nombre: "Principe Orion" de Onyria (ONYRIA-136/235) es **Ismael**,
  "Rlyeh" (ONYRIA-117/216) es **Casa de Opio** y "Vuelo Mágico" (MAZO_IMP_ETERNO-004) es
  **Polvo de Hadas**. Todas verificadas en la carta. Al revés, codicetcg se equivoca con
  "Hijos del Fuego Blanco": la carta es Paladín del Fuego Blanco, como la teníamos. Los
  pares "Alicia en el País…" / "Las Aventuras de Alicia…", "Frankenstein o el nuevo/Moderno
  Prometeo", "Viaje…" / "Un Viaje al Centro…" y "El Gran Descenso" / "Santo, Santo, Santo"
  tienen el mismo texto con nombres distintos en las dos fuentes, así que se dejaron.
- Cartas distintas con el mismo nombre que siguen vigentes, con sufijo para que TCG Arena no
  las agrupe: "Alicanto (Aliado)" (Libertadores, vs el Oro de los precon) y "Jonathan Harker
  (Drácula)" (vs el de Onyria). Con el sufijo, el override por ID de Alicanto ya no hace
  falta. Libro de Revelaciones tiene dos versiones con texto distinto (AyD y kit de
  Drácula), pero las dos traen el dragón de AyD, así que rotan juntas.
- Bayou St. John (Toolkit 2026) es Tótem, no Talismán.

## Búsqueda y nombres en el build

- `ability` y `Edicion` se emiten sin tildes, como el nombre. La detección de "Única" corre
  antes, sobre el texto original, así que la legalidad no cambia.
- `lower_connectors()`: los conectores del nombre (de, del, la, y, en…) van en minúscula
  salvo al inicio. Afecta 145 nombres que la API escribía con cada palabra en mayúscula;
  así calzan con las reimpresiones que vienen de codicetcg. Solo cambia mayúsculas.
- El build avisa si aparece un tipo de carta que no está en `autoPlayFromHand` del game
  JSON (la API ya conoce el tipo "Monumento").
- Los scripts de conversión y `revisar_dragones.py` pasan a `scripts/`. `convert_raw_to_cards_json.py` usa rutas relativas al repo y advierte que no debe volver
  a correrse tal cual: pisaría las correcciones hechas a mano en `cards_json/`.

## Repositorio

- `.gitignore` deja de excluir `CLAUDE.md` y `GAME_JSON_DOCS.md`, y se versionan las listas
  de restricciones de agosto-septiembre y octubre.

## Banlist

Se limpian 12 IDs rotados. Ninguna carta restringida se reimprime en Drácula, así que no hay
restricciones nuevas que propagar.

Después entra la lista oficial de octubre, transcrita en `lista_restricciones_octubre.json`.
Los IDs se resolvieron por nombre contra el pool, con todas las reimpresiones (incluidas las
con errata menor, como León Indiferente, Tesoro de los Césares y Shiji):

- Kuchiku el Cazador: de limitada a 2 a limitada a 1 (3 IDs).
- Nuevas limitadas a 1:
  - Espada de O'Higgins (4 IDs: Libertadores ×2, Toolkit 2026 y Mazo Guerrero).
  - Duelo de Dragones y Escamas de Dragón (Mazo Dragón; la tabla les pone "Kaiju vs Mecha"
    por error).
  - Lilith y Jinete de la Peste (AyD).
- "Metatron" (AYD_VIGILANTES-076) se renombra "Ángel Metatrón": así la llaman la lista y
  codicetcg, y el texto coincide.
- La tabla trae la fila de Sheut con la edición repetida en la columna Estatus. Como no marca
  cambio, se mantiene limitada a 2.
- Shakar Raj no aparece en la tabla pero sigue vigente por el Mazo Guerrero. Se mantiene
  limitada a 1, igual que en julio, hasta confirmarlo.
- La tabla no trae mercenarias: Siete Enanos, Escudo Nacional y Leyaden siguen como estaban.
- Las demás bajas respecto de agosto-septiembre (Ereshkigal, Paladín, Rey de Amarillo,
  Ryugu-Jo, El Mago y Perseguir el Sol) ya no tienen impresiones vigentes.

Resultado: 15 prohibidas, 39 IDs limitados a 1, 12 limitados a 2 y 4 mercenarios.

## Total

1801 cartas (antes 1927), 24 ediciones en 5 temporadas.
