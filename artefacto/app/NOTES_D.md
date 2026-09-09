# NOTES_D — vistas Legal · Trámites · Riesgos (agente D)

Archivos creados (sólo estos; ningún archivo ajeno tocado):

- `src/views/Legal.tsx` — `export function Legal({ caseId, onNavigate })` · hoja 02_Legal
- `src/views/Tramites.tsx` — `export function Tramites({ caseId, onNavigate })` · hoja 03_Tramites
- `src/views/Riesgos.tsx` — `export function Riesgos({ caseId, onNavigate })` · hoja 11_Riesgos

Las tres reciben `{ caseId: CaseId; onNavigate: (v: ViewId) => void }`. Trámites usa `caseId` (rubro 9 del CAPEX del caso
seleccionado); Legal y Riesgos no dependen del caso (sus textos vivos usan los nombres del Custom/«caso activo» del libro, igual
que la hoja) y aceptan `caseId` por contrato sin desestructurarlo.

`npx tsc -b`: limpio (0 errores). `npx oxlint` sobre los tres archivos: sin avisos. Sin `console.log`, sin dependencias nuevas,
sin `toFixed`/`Intl`, sin colores literales ni emojis, sin builds ni publicaciones ni capturas.

Integración pendiente (coordinador, `App.tsx`): `view === "legal" ? <Legal caseId={caseId} onNavigate={navigate} />`, ídem
`tramites` y `riesgos`.

## Verificación hecha (además de tsc)

Render estático en Node (`react-dom/server` + bundle esbuild temporal en el scratchpad, ya borrado) de las tres vistas dentro del
`ModelProvider` real, para los cuatro casos: sin excepciones; el texto no contiene `NaN`, `undefined`, `null`, `Infinity`,
`#NAME?`, `#REF!`, `#VALUE!`, `#DIV/0!`. Cotejos con el libro:

- Legal: criterio del candado 4 → «Capacidad del alimentador 13,8 kV para 3.788 kWac (aprobable: 3.800 kW, por confirmar)»;
  candado 5 → «Peaje de red desde 28-feb-2029 — valor no publicado (por potencia y energía)» y su estado «▲ Sensibilizado 0–1,5
  ¢/kWh y 0,5 $/kW-mes (activo: 0,0 ¢ · 0,00 $/kW-mes)»; contrato 3 → «Contrato de arriendo / usufructo del terreno (5,0 ha)»;
  E29 vivo → «Con ingresos de 10,0 M el tope (500 k$) no muerde. Aplica_DedAd = Sí; … TIR 9,42 % frente a 10,64 %».
- Trámites: Fecha de COD implícita 01-jul-2028 = Fecha_COD → «● coherente con Fecha_COD del modelo» (0 días, tolerancia 45);
  F12 → «● ok (4 meses)»; Σ costos $ 194.500 (= Costo_Desarrollo_Cron) frente al rubro 9 del Custom $ 250.000 × 1,05 →
  «● cabe», margen $ 68.000. Rama alterna probada mutando las entradas base antes de renderizar (Meses_Construccion = 24, rubro 9
  = 150.000): «▲ revisar Fecha_COD» (92 días), aviso «Meses_Construccion = 24 ≠ mes de COD del cronograma del libro (21)», dos
  marcadores en el Gantt (COD implícito oct-2028 y Fecha_COD 01-jul-2028), «▲ excede el rubro 9 — revisar», margen −$ 29.143.
- Riesgos: con los umbrales del libro (6 / 3) → 8 altos · 6 medios · 1 bajo, fila 14 viva «DSCR mínimo 0,73x en t = 8 con 8 años
  / 100 % (objetivo 1,20x)» → score 6 → «■ ALTO»; con umbrales 9 / 4 → 2 altos · 12 medios · 1 bajo.

## Qué muestra cada vista

### Legal (02_Legal)

- `ViewHeader` (intro B2) con chips de conteo (normas, instrumentos, zonas grises y cuántas en urgencia Alta) y tres `Status` con
  cuántos candados están en ● / ▲ / ■ (evaluados en vivo).
- **Los 5 candados del régimen elegido (estado en vivo)** (título = B5): cabecera con las tres cabeceras de la hoja
  (`legal.table_headers.candados`: Candado · Qué exige · Estado); por candado: etiqueta, `<Trace cell="02_Legal!D7…D11">`,
  criterio (`<Live>`; los criterios 4 y 5 llegan como fórmula, ver decisiones) y `<LiveStatus text={estado}>`.
- **Matriz normativa verificada** (título = B13): `DataTable` size sm con las seis cabeceras de la hoja
  (`legal.table_headers.marco`): Tema · Norma / artículo · Qué dice (verificado) · Implicación para GPM / Exergy · Estado ·
  verificación · Confianza. Todas las celdas de texto son `<Live>` (el punto gris aparece si dependen de un valor congelado).
  «Qué dice» se pliega a dos líneas (`line-clamp-2`) cuando el texto evaluado pasa de 150 caracteres, con «ver más / ver menos»
  por fila. Filtro segmentado por confianza con los niveles presentes en la columna (Alta · Media · Baja · ❓, con conteos) y
  búsqueda (`input type=search`) sin acentos ni mayúsculas sobre los textos ya evaluados (tema, norma, qué dice, implicación,
  estado, confianza). Guía con «n de 25 normas»; mensaje de vacío si nada coincide.
- **Arquitectura contractual (SALELGI dueña · Exergy gerencia, arrienda y opera)** (título = B41): tabla de 8 instrumentos:
  Instrumento (`<Live>`, el título del arriendo lleva las hectáreas vivas) · Partes · Contenido esencial (`<Live>`) · Nota (`<Live>`).
- **Zonas grises vivas … Atlas Regulatorio v2.0** (título = B52): tabla de 15 dudas con las cabeceras de la hoja
  (`legal.table_headers.dudas`: # · Duda · Por qué importa · Resolver con · Urgencia); Duda/Por qué importa/Resolver con en
  `<Live>`; Urgencia como `Status` ▲ si «Alta», ◇ en otro caso; filtro «Todas / Urgencia Alta».
- `Note` final con enlaces a Riesgos, Trámites, Fuentes y Controles (`onNavigate`).

### Trámites (03_Tramites)

- `ViewHeader` (intro B2) con chips: «Mes 1 del cronograma · oct-2026» (etiqueta = labels["5"]), «Mes de COD (fin de RC-13) · 21»
  (= max(fin) de las filas, etiqueta de E5), «Fecha de COD implícita · 01-jul-2028» (= EDATE(Mes1, Meses_Construccion), etiqueta
  de I5; en acento si Meses_Construccion difiere del libro), «Fecha_COD · 01-jul-2028» (en acento si difiere del libro), el control
  M5 como `Status` con la regla y los textos exactos de la hoja (`ABS(EDATE(Mes1,Mes_COD)−Fecha_COD) ≤ Tol_Dias_COD` → «● coherente
  con Fecha_COD del modelo» / «▲ revisar Fecha_COD») y `<Trace name="Check_Cron" cell="03_Tramites!M5">`; si Meses_Construccion ≠
  max(fin), un `Status` ▲ lo avisa (ver decisiones).
- **Cronograma a COD**: `Gantt` con las 17 filas (`start = inicio`, `end = fin`, `critical = critica === "Sí"`, detalle = autoridad ·
  costo · riesgo, y «ruta crítica parcial (dibujada como no crítica)» cuando aplica), `months = max(max(fin)+1, COD implícito+1,
  Fecha_COD+1)`, `monthLabel(k) = fmtMonthYear(EDATE(mes1, k−1))`, marcadores (COD implícito en la frontera Meses_Construccion; si
  coincide con Fecha_COD se dibuja uno solo «COD · jul-2028 = Fecha_COD», si no dos: «COD implícito · mmm-aaaa» y «Fecha_COD ·
  dd-mmm-aaaa», este último ▲ si el control M5 no es ●), ventana de vigencia de la Factibilidad (meses fin(RC-09)+1 … fin(RC-09)+6).
  Selección sincronizada con la tabla (clic en fila del Gantt o de la tabla). Debajo: leyenda propia (ver textos), el control F12
  con la regla y los textos exactos de 13_Controles (`Fin_RC10 − Fin_RC09 ≤ 6` → «● ok (4 meses)» / «■ n meses > 6: la
  factibilidad vence antes de la habilitación — reordenar 03»; tooltip = descripción del control en el libro; `<Frozen>` porque el
  cronograma no se edita en el artefacto), chip Tol_Dias_COD, la diferencia en días COD implícito frente a Fecha_COD, y la nota D29
  de la hoja (`gantt_leyenda[1]`) tal cual.
- **Hitos**: `DataTable` size sm con las 12 columnas de la hoja (`tramites.headers`, saltos de línea → espacio): ID · Trámite ·
  Autoridad · Base legal · Inicio (mes) · Dur. (m) · Fin (mes) · Costo [USD] · Predecesor · Ruta crítica · Riesgo · Nota (`<Live>`).
  Inicio/Fin llevan el mes calendario en el tooltip; Ruta crítica «Sí» en acento (mismo color que la barra), «Parcial» en tinta
  secundaria con tooltip, «No» en terciaria; Riesgo con glifo (Alto ■ · Medio-Alto y Medio ▲ · Bajo ● · otro ◇).
- **Costos de desarrollo frente al rubro 9 del CAPEX** (filas 25–27, etiquetas de `tramites.totales`): Σ costos del cronograma
  (`<Frozen what="Cronograma valorado">`, `<Trace name="Costo_Desarrollo_Cron" cell="03_Tramites!I25">`), rubro 9 del caso
  seleccionado (`capexTable(m.inputs, m.derived, c.params).rubros[8].costo`, `<Trace cell="05_CAPEX!F15">`, con el tope
  × (1 + Tol_Costo_Tramites)), y el control I27 con la regla y los textos exactos («● cabe» / «▲ excede el rubro 9 — revisar»),
  el margen (tope − Σ) y la tolerancia. Nota con enlace a CAPEX.
- **Escenarios de cronograma — memo estático (…)** (título = `tramites.memo[0]` = B32): los cuatro párrafos del memo tal cual
  (`Note` serif) y, como `aside`, un `Status` ◇ con el aviso de que es un memo estático del libro a la fecha de corte
  (`<Frozen what="Memo">`).

### Riesgos (11_Riesgos)

- `ViewHeader` (intro B2) con chips `Umbral_Riesgo_Alto · score ≥ 6` y `Umbral_Riesgo_Medio · score ≥ 3` (de `m.extras`, respaldo
  `riesgos.umbrales`; en acento si difieren del libro) y tres `Status` con cuántos riesgos son altos / medios / bajos.
- **Probabilidad × impacto**: `RiskMatrix` con los 15 puntos (`id` = número de fila 1…15, `prob`/`impacto` acotados a 1–3) y los
  umbrales vivos; a la derecha, el detalle del riesgo seleccionado: #, categoría, nivel (`Status` con el texto de la hoja «ALTO /
  MEDIO / BAJO» y «p × i = score»), riesgo (`<Live>`), mitigación (`<Live>`, serif), dueño, alerta temprana y
  `<Trace cell="11_Riesgos!C6…C20">`. Texto de ayuda cuando no hay selección.
- **Los 15 riesgos ordenados por score**: `DataTable` size sm ordenada por score descendente (a igual score, el orden de la hoja):
  # · Categoría · Riesgo (`<Live>`) · Prob. (1-3) · Impacto (1-3) · Score · Nivel (`Status` con la regla y los textos exactos de
  11!G: `≥ Umbral_Riesgo_Alto → ■ ALTO`, `≥ Umbral_Riesgo_Medio → ▲ MEDIO`, si no `● BAJO`) · Mitigación (`<Live>`) · Dueño ·
  Alerta temprana. Selección sincronizada con la matriz.
- `Note` final con enlaces a Supuestos (donde se editan los umbrales, 01 §I), Sensibilidad y Legal.

## Decisiones

1. **Fórmulas de texto que book.json entrega como cadena.** `legal.candados[3].criterio`, `legal.candados[4].criterio` y
   `legal.contratos[2].contrato` no son `Live` sino la fórmula Excel literal (`="Capacidad del alimentador 13,8 kV para
   "&TEXT(Potencia_AC,"#,##0")&…`). Para no mostrar la fórmula ni parafrasearla, `Legal.tsx` incluye `concatFormula()`, un
   transcriptor mínimo al AST del evaluador (literales, nombres y `TEXT(expr,"fmt")`); si la cadena no encaja en ese patrón se
   muestra tal cual. Así los tres textos dicen exactamente lo que dice el Excel con las cifras del momento y pasan por `<Live>`
   (marca de congelado incluida). **Aviso para el coordinador:** `Resumen.tsx` muestra `c.criterio` en crudo, así que en los
   candados 4 y 5 del Resumen se ve la fórmula; lo ideal es que el extractor (`build30/extract_book.py`) entregue `criterio` y
   `contrato` como `Live`, cambiar sus tipos en `book.ts` a `Live` y pasar los campos directamente a `<Live>` (el helper
   `concatFormula` de Legal.tsx se elimina entonces).
2. **Filtro por confianza sobre celdas compuestas.** La columna G trae valores como «Alta / Media (red)», «Alta (norma) / ❓
   (predio)». Los niveles del filtro se derivan de lo presente (Alta · Media · Baja · ❓) y una fila cuenta en cada nivel que su
   celda mencione; la guía de la sección lo explica. No se inventa un nivel «principal».
3. **COD implícito = `m.inputs.Meses_Construccion`.** En el libro `Meses_Construccion` es fórmula (= `Mes_COD_Cron` = MAX(fin));
   en el artefacto es una entrada. El marcador del Gantt y la «Fecha de COD implícita» siguen a la entrada (regla M5 con
   `Tol_Dias_COD`), mientras las barras son las del libro; si la entrada difiere de max(fin) del cronograma se muestra un `Status`
   ▲ «Meses_Construccion = n ≠ mes de COD del cronograma del libro (21)». Cuando el COD implícito y la Fecha_COD caen en el mismo
   mes se dibuja un solo marcador para que las etiquetas no se pisen.
4. **Cronograma = dato del libro.** Inicio, duración, costo y las magnitudes derivadas (Σ costos, Fin_RC09/Fin_RC10, max(fin)) se
   calculan desde `tramites.rows` (coinciden con `frozen.Costo_Desarrollo_Cron`, `Fin_RC09`, `Fin_RC10`, `Mes_COD_Cron`) y se
   marcan con `<Frozen>` donde se comparan con cifras vivas (Σ costos frente al rubro 9; F12). El rubro 9 sí es vivo y del caso
   seleccionado (`capexTable`), no del «caso activo» del libro (Custom): la guía de la sección lo dice.
5. **Ventana de la Factibilidad sin etiqueta dentro del SVG.** `Gantt` dibuja la etiqueta de `window` en la misma fila que los
   rótulos de mes (y = HEAD_H − 8), así que con 22 meses taparía tres o cuatro rótulos. Paso `label: ""` y explico el sombreado en
   la leyenda (con los meses y las fechas de la ventana). La vigencia (6 meses) es la constante del control F12 y de 005/24 art. 13;
   no existe como nombre definido, va como `VIGENCIA_FACTIBILIDAD` con comentario.
6. **Leyenda propia del Gantt** en lugar de `gantt_leyenda[0]` (habla de terracota/piedra del Excel); `gantt_leyenda[1]` (hitos
   binarios) se muestra tal cual como `Note`. «Parcial» (RC-07) se dibuja como no crítica y se declara en la leyenda, en el tooltip
   de la barra y en la tabla.
7. **Nivel de riesgo con los textos de la hoja** («■ ALTO», «▲ MEDIO», «● BAJO») y la misma regla; el color sólo en el glifo. Los
   umbrales se toman de `m.extras` (respaldo `riesgos.umbrales`), así la matriz y la tabla reaccionan a Supuestos §I.
8. **«Alerta temprana»** es la cabecera J5 de la hoja para la columna `disparador`; `riesgos.headers` sólo trae B5:I5, por eso el
   literal. El «#» de la tabla de riesgos es el número de fila (1 = fila 6) que la matriz usa como ficha.
9. **Cabeceras de la tabla de contratos**: `legal.table_headers.contratos` es `null`; se usan las de la fila 42 de la hoja
   (Instrumento · Partes · Contenido esencial · Nota) como respaldo literal (si el extractor las rellena, se usan las suyas).
10. **Textos de estado calculados en la vista** (M5, F12, I27, nivel de riesgo) reproducen letra por letra las cadenas de las
    fórmulas del libro y se pasan por `statusOf`/`stripGlyph`, igual que un texto vivo.

## Textos de UI escritos por el agente (para revisión)

Títulos de vista: «Marco legal y regulatorio» · «Trámites» · «Matriz de riesgos».

Legal:
- Chips: «{n} normas» · «{n} instrumentos» · «{n} zonas grises · {n} en urgencia Alta»; Status: «{n} candado(s) en ●», «{n} en ▲», «{n} en ■».
- Guía candados: «el estado se evalúa con los valores actuales del motor; el criterio es el de la hoja».
- Guía matriz: «{n} de {N} normas · el filtro toma cualquier mención de la celda de confianza («Alta / Media (red)» cuenta en Alta y en Media)».
- Filtro: «Todas ({N})», «{nivel} ({n})»; buscador: placeholder «Buscar en la matriz…», aria-label «Buscar en la matriz normativa»;
  botones «ver más» / «ver menos»; vacío: «Ninguna norma coincide con el filtro y la búsqueda.».
- Pie matriz: «Hoja 02_Legal, filas 15–39, columnas B–G; textos tal cual, evaluados con los valores actuales. El punto gris marca un
  texto que depende de un valor que sólo existe en el libro.».
- Guía contratos: «alcance y nota de cada instrumento con las cifras del momento (fee, $/kWp, renta, hectáreas)»; pie «Hoja 02_Legal,
  filas 43–50, columnas B–E.»; cabeceras de respaldo «Instrumento · Partes · Contenido esencial · Nota».
- Guía zonas grises: «▲ = urgencia Alta; el resto en ◇»; filtro «Todas ({N})» / «Urgencia Alta ({n})»; pie «Hoja 02_Legal, filas 54–68,
  columnas B–F.».
- Nota final: «Vistas relacionadas: Riesgos → · Trámites → · Fuentes → · Controles →».

Trámites:
- Chips: «Mes 1 del cronograma · {mmm-aaaa}» (etiqueta de la hoja), «Mes de COD (fin de RC-13) · {n}» (etiqueta E5), «Fecha de COD
  implícita · {dd-mmm-aaaa}» (etiqueta I5), «Fecha_COD · {dd-mmm-aaaa}», «Tol_Dias_COD · {n} días»; tooltips con la celda/nombre.
- Status propio: «Meses_Construccion = {n} ≠ mes de COD del cronograma del libro ({n})».
- Sección «Cronograma a COD», guía «un cuadro = un mes desde {mmm-aaaa} · clic en una fila para verla en la tabla»; aside «{n} hitos en
  ruta crítica · {n} parcial · {n} no críticos».
- Leyenda: «Leyenda: barra en acento = ruta crítica · gris = no crítica («Parcial» se dibuja como no crítica y se indica en la tabla) ·
  sombreado = vigencia de la Factibilidad de Conexión (6 meses desde el fin de RC-09: meses 9–14, jun-2027 → nov-2027) · línea
  discontinua = COD».
- Marcadores: «COD · {mmm-aaaa} = Fecha_COD» / «COD implícito · {mmm-aaaa}» / «Fecha_COD · {dd-mmm-aaaa}»; tooltip de barra: «{autoridad}
  · {costo} · riesgo {riesgo}[ · ruta crítica parcial (dibujada como no crítica)]».
- Línea de control: «Control F12 · {texto del libro}» (tooltip = descripción del control), «COD implícito frente a Fecha_COD: {n} días».
- Sección «Hitos», guía «{n} filas RC-xx con las columnas de la hoja · clic en una fila para resaltarla en el Gantt»; tooltip «En el Gantt
  se dibuja como no crítica»; pie «Hoja 03_Tramites, filas 8–24, columnas B–M; inicio, duración y costo son los del libro {v} ({corte}).
  Meses contados desde {mmm-aaaa}.».
- Sección «Costos de desarrollo frente al rubro 9 del CAPEX», guía «el rubro 9 es el del caso seleccionado ({caso}); la tolerancia es
  Tol_Costo_Tramites de 01 §I»; subtexto «caso {caso} · ×(1 + {tol}) = {USD}»; «margen {USD} · Tol_Costo_Tramites {tol}»; nota «Los
  costos del cronograma son los del libro (el artefacto no edita los hitos); el rubro 9 cambia con el caso y con los Mandos, igual que
  en CAPEX.».
- Aviso del memo: «memo estático del libro {v} ({corte}): sus cifras no se recalculan con los Mandos».
- `Frozen what`: «Cronograma (fin de RC-09 y RC-10)», «Cronograma valorado», «Memo».

Riesgos:
- Chips: «Umbral_Riesgo_Alto · score ≥ {n}», «Umbral_Riesgo_Medio · score ≥ {n}»; Status «{n} alto(s)», «{n} medio(s)», «{n} bajo(s)».
- Sección «Probabilidad × impacto», guía «fila = probabilidad, columna = impacto; el color de la celda es el nivel de su score frente a
  los umbrales · clic en un número para ver el riesgo»; detalle: «{nivel} · p {p} × i {i} = {score}»; cabecera «Alerta temprana»;
  vacío: «Seleccione un riesgo en la matriz o en la tabla para ver su mitigación, dueño y alerta temprana.».
- Sección «Los {n} riesgos ordenados por score», guía «score = probabilidad × impacto; a igual score, el orden de la hoja · clic en una
  fila para verla en la matriz»; cabecera «#»; pie «Hoja 11_Riesgos, filas 6–20, columnas B–J; el número # es la fila de la hoja (1 =
  fila 6). Textos tal cual, evaluados con los valores actuales.».
- Nota final: «Los umbrales Umbral_Riesgo_Alto y Umbral_Riesgo_Medio se editan en Supuestos (01 §I). Los riesgos de mercado, fiscal y
  financiero se cuantifican en Sensibilidad; el marco que los sustenta está en Legal.».

## Dudas y sugerencias sobre archivos compartidos (no tocados)

1. `book.ts` / extractor: `legal.candados[].criterio` y `legal.contratos[].contrato` deberían ser `Live` (hoy `string` con la fórmula
   cruda en tres casos). Afecta a `Resumen.tsx` (muestra la fórmula en los candados 4 y 5). Mientras tanto Legal usa `concatFormula`.
2. `charts/Gantt.tsx`: (a) la etiqueta de `window` se dibuja sobre la fila de rótulos de mes; convendría dibujarla dentro del área de
   barras (p. ej. al pie, junto a los marcadores) o bajo el eje; (b) dos marcadores a menos de ~3 meses superponen sus etiquetas
   (se dibujan a la misma altura); alternar la altura o alinear a la izquierda/derecha del trazo lo resolvería. (c) `markers` usa
   `label` como `key`: dos marcadores con el mismo texto colisionarían (en Trámites las etiquetas son distintas).
3. `charts/RiskMatrix.tsx`: los rótulos de celda dicen «■ alto / ▲ medio / ● bajo» en minúsculas y la hoja «■ ALTO / ▲ MEDIO /
   ● BAJO»; es cosmético, pero si se quiere literalidad podría recibir los textos por prop.
4. `book.json`: `riesgos.headers` no incluye la cabecera J5 «Alerta temprana» (columna `disparador`); `legal.table_headers.contratos`
   es `null` aunque la hoja tiene cabeceras en la fila 42.
5. `tramites.memo[3]` dice «En el artefacto interactivo este escenario es un preset vivo» (retraso por red, COD +12 meses). Es texto
   del libro y se muestra tal cual; conviene confirmar que Mandos/Supuestos ofrezcan ese preset (o que el coordinador decida cómo
   señalarlo si no existe).
6. Semántica de `Meses_Construccion` en el artefacto (entrada) frente al libro (fórmula = Mes_COD_Cron): si en Mandos/Supuestos se
   edita, el Gantt lo refleja sólo como marcador de COD (las barras son las del libro). Si el coordinador prefiere que la vista use
   `frozen.Mes_COD_Cron` para el marcador y deje `Meses_Construccion` sólo al control M5, es un cambio de una línea (`mesCOD`).
7. La constante de vigencia de la Factibilidad (6 meses) no existe como nombre definido; va como constante comentada en la vista.
