# NOTES_A — vistas Supuestos · Guía · Fuentes · Controles (agente A)

Archivos creados (sólo estos; ningún archivo ajeno tocado):

- `src/views/Supuestos.tsx` — `export function Supuestos({ caseId, onNavigate })` · hoja 01_Supuestos
- `src/views/Guia.tsx` — `export function Guia(...)` · hoja 00b_Guía
- `src/views/Fuentes.tsx` — `export function Fuentes(...)` · hoja 12_Fuentes
- `src/views/Controles.tsx` — `export function Controles(...)` · hoja 13_Controles

Las cuatro reciben `{ caseId: CaseId; onNavigate: (v: ViewId) => void }`. Ninguna usa `caseId` (las cuatro hojas son
transversales a los casos); se acepta en `Props` para cumplir el contrato y no se desestructura.

`npx tsc -b`: limpio (0 errores). `npx oxlint src/views`: sin avisos en los cuatro archivos (el único aviso del directorio es el
preexistente de `Sensibilidad.tsx`). Sin `console.log`, sin dependencias nuevas, sin builds ni publicaciones.

Integración pendiente (coordinador, `App.tsx`): `view === "supuestos" ? <Supuestos caseId={caseId} onNavigate={navigate} />`,
ídem `guia`, `fuentes`, `controles`.

## Verificación hecha (además de tsc)

1. Render estático en Node (`react-dom/server`) de las cuatro vistas con el `ModelProvider` real para los cuatro casos: sin
   excepciones; los textos vivos no contienen `#NAME?`, `#REF!`, `#VALUE!`, `NaN` ni `undefined`.
2. Humo funcional en Chromium headless (sin capturas) con un arnés temporal (`__smoke_a/`, ya borrado) sobre `vite dev`:
   editar Potencia_DC (selector) mueve el panel a «6.000 kWp» y aparece el chip sandbox; ↺ de fila restaura; Tasa_Descuento se
   edita en % (10 → 12) y el panel dice «12,0 %»; una entrada extra (Capacidad_Alimentador_kW) actualiza el texto vivo del panel;
   bloque B: la columna Custom del peaje pasa a 0,01 y el panel dice «peaje 1,0 ¢» con C·B·F intactas; Sí/No, selector de tres
   opciones, campo vaciable (Utilidad_Gravable_SALELGI → vacío = null), fecha, texto (Version), notas por fila y por bloque,
   «volver al libro», «editar ↓» (desplazamiento) y «Sensibilizado en» (navega a Sensibilidad) funcionan. Guía: 14 convenciones,
   7 FAQ (plegables), 38 términos, índice de 14 hojas que navega. Fuentes: 5 secciones, 21 ítems en §A, tabla §C 5 × 4, 26 fuentes
   con 11 enlaces `target=_blank rel=noreferrer`. Controles: 79 filas en 9 grupos, filtro «con aviso» deja F10, fórmula plegable,
   autocomprobación 1.776/1.776. Cero errores/avisos de consola (React incluido). Sin scroll horizontal a 640 px en claro y oscuro.

## Qué muestra cada vista

### Supuestos (01_Supuestos)

- Cabecera `ViewHeader` (intro B2 del libro) con chips: `Estado_Custom` (lo calcula el motor), `Estado_Entregado`,
  `Estado_Controles`, `Estado_Neutro` (valores del libro, con marca `Frozen`), «▲ N_Por_Confirmar supuestos por confirmar (lista
  en 12 §A)» (fila C17 de la hoja, con `Frozen`, «12 §A» navega a Fuentes) y el chip sandbox con «volver al libro» (`m.reset`) o
  «● valores del libro v3.1 (08-sep-2026)» cuando no hay cambios.
- **Panel de mandos**: las 8 tarjetas de `inputs.panel` (label · `m.live(value)` grande · `m.live(sub)` · `<Trace name>` ·
  botón «editar ↓» que desplaza a la fila del parámetro). La guía de la sección es la celda C7 de la hoja. Las dos tarjetas que en el
  libro van en ciruela (`extra` = color Custom) llevan la cifra en acento.
- **Bloques A–I** (`inputs.bloques`): una `Section` por bloque (título y guía del libro) con `DataTable` size sm. Columnas:
  Parámetro (label; debajo `short` vivo o `label2` en 11 px terciario; la nota desplegada aparece bajo el label en serif) · Valor ·
  Unidad · ▲ (por confirmar, tooltip con `confirm_why`) · Sensibilizado en (`sens[0]`; si el ancla es una sección de 10 o
  «#'Hoja'!Celda», es un botón que navega a esa vista) · Nota (botón «nota ▾/▴», tooltip con el texto; «mostrar notas» en la
  cabecera del bloque las abre todas) · Nombre (`<Trace name>`).
- **Valor**: `calc` → tinta terciaria con `m.nameValue(name)` formateado según `fmt`; `info` → tinta 2, no editable;
  `yesno` → segmentado Sí/No; `selector` → segmentado (Potencia_DC muestra 5.000 · 6.000 · 7.000 · 8.000 y guarda número);
  fecha (`unit` «fecha» o `fmt` con «yyyy») → `<input type="date">` ISO; `unit` «texto» → texto; número → `<input type="number">`
  con paso según `fmt` (porcentajes se editan en % con paso 0,01 y se guardan como fracción con `roundTo(·/100, 10)`; «0.00» → 0,01;
  «0.0000» → 0,0001; enteros/USD → 1). Vaciar un campo cuyo valor del libro es vacío guarda `null` (placeholder «vacío»).
  Guardar: `name in m.inputs` → `m.setInput(name, v)`; si no → `m.setExtra(name, v)`.
- **Bloque B** (`inputs.escenarios`): columnas Custom · Conservador · Base · Favorable con la muestra de trazo del caso en la
  cabecera. Sólo Custom es editable (`m.inputs[esc_name][0]`, se guarda una copia del arreglo); C·B·F se muestran desde
  `m.inputs[esc_name][1..3]` y, si difirieran de `escenarios[].values` (definición entregada), irían en acento con tooltip «control G4».
  «Sensibilizado en» del bloque B viene de la columna H de la hoja (H38:H45), transcrita en `SENS_BLOQUE_B` porque
  `inputs.escenarios` no la trae.
- Entradas distintas del libro (`m.dirtyKeys` / `m.dirtyExtras`): label y campo en acento, debajo «libro: valor» y un ↺ por fila
  que restaura sólo esa entrada (`m.baseline` / `BASELINE_EXTRAS`).
- **Por confirmar**: `inputs.confirm_list` con ▲ (los dos últimos ítems, «Además (no contados)…» y «Pendientes legales…», con ◇
  porque el propio texto dice que no cuentan); aside con el conteo: entradas marcadas en la hoja (15 filas + 3 del bloque B = 18)
  frente a `n_por_confirmar_esperado` (18) → ● si coinciden, y `frozen.N_Por_Confirmar` (19, con `Frozen`) «con los drivers de 05».

### Guía (00b_Guía)

- Pasos (5) con `<Live>` y botón «→ vista» según la hoja del paso (00_Portada → Resumen, 04 → Energía, 01 → Supuestos, 10 →
  Sensibilidad, 13 → Controles).
- Convenciones (14): tabla «En el libro · Significado · En el artefacto». La tercera columna traduce cada color del libro a los
  tokens: tinta/terracota/arcilla/ciruela → acento; glifos → `StatusGlyph`; carbón·grafito·piedra → `text-ink`/`ink-2`/`ink-3`;
  índigo/petróleo/verde → muestras de trazo `--c-*` + `--dash-*`; ladrillo → `text-risk`; fila bruma → chip `bg-surface-2`;
  «toda cifra es fórmula» → marca `<Frozen>` para lo que sólo existe en el libro.
- FAQ (7) en `<details>` estilizados (`<Live>` en pregunta y respuesta).
- Glosario: 5 grupos × `DataTable` (Término · Qué es y dónde vive · Cómo leerlo (cifra viva)); los anclajes empiezan todos por «#»
  y se ignoran, como pide el brief.
- Índice de hojas (`guia.index`) → botón a la vista (01→supuestos … 13→controles, Motor_Sens→sensibilidad). En la edición externa
  no se enlaza «09_Exergy» (`isExterno()`), ni desde «Sensibilizado en» de Supuestos.
- Pie: la fórmula de 00b!B92 («Guía elaborada con el libro …») evaluada en vivo.

### Fuentes (12_Fuentes)

- Secciones A–E reconstruidas desde `fuentes.cells` agrupando por las cabeceras de `fuentes.secciones`; texto tal cual (se quita
  sólo la viñeta «• »). §A usa `inputs.confirm_list` (mismo glifo que en Supuestos) y su guía es la fórmula de C5 evaluada en vivo
  (N_Por_Confirmar con marca `Frozen`). §B y §E: viñetas en serif. §C: tabla Pieza · CAPEX · OPEX año 1 · Fiscal · Resultado
  reportado, con la fila «Este libro …» destacada y viva; la nota de la fila 48 debajo. §D: `fuentes.rows` (26) con «abrir ↗»
  (texto del libro, columna F) en acento, `target="_blank" rel="noreferrer"`, y la URL en mono 10,5 px debajo.
- Las cuatro celdas que en la hoja son fórmulas (C5, B47, C47, D47) están transcritas al AST del evaluador en `LIVE_CELLS`
  (comentadas con la fórmula original) porque `fuentes.cells[].f` trae la fórmula como texto plano y no hay parser en TS.
  Resultado comprobado: «Bottom-up 0,82 $/Wp sin IVA a 5,0 MWp …» y «107 k (fee O&M 80 k + seguros 17,5 k …)» = valores del libro
  en es-EC.
- Las columnas E («Fiscal») y F («Resultado reportado») de la tabla §C no están en `fuentes.cells` (sólo B–D): se copiaron tal
  cual de la hoja en `SECCION_C_EF` (filas 43–47). Ver «Dudas».

### Controles (13_Controles)

- Cabecera: `resumen.Estado` con `<Frozen what="Control">`, chip ■ si `N_Controles_Fail > 0`, chip «Motor ≡ Excel n/n salidas ·
  111 casos» (`m.selfCheck`) y chip sandbox.
- «Estado del libro»: las cuatro entradas de `controles.resumen` (etiquetas = claves del libro) con marca `Frozen` + nota de que
  los estados son los del libro a la fecha de corte.
- «Autocomprobación del motor» (separada): cifra `compared − failed / compared`, chip de estado, `namesOk`, lista `worst` si hay
  fallos, y nota explicando que compara con las entradas entregadas y que recalcula salidas, no controles.
- Tabla de los 79 controles con `sectionBefore` por `group`: # (mono) · Qué prueba · Estado (`Status` con `statusOf`, texto sin
  glifo; la cabecera lleva `Frozen`) · Fórmula del libro (mono truncada a 72 caracteres con tooltip completo; clic despliega).
  Filtro «Todos (79) · Con aviso (1)». Pie de tabla con versión/corte.

## Decisiones

1. **Notas plegables bajo el label** (no en tooltip solamente): la columna Nota tiene un botón; la nota abierta se muestra en la
   celda Parámetro en serif, para que el texto largo tenga ancho. «mostrar notas» por bloque abre todas.
2. **Campos numéricos con borrador**: el `<input type="number">` muestra el valor del modelo salvo mientras tiene el foco
   (borrador local), así «0,» o vacío transitorio no rompen la edición y los cambios externos (Mandos, «volver al libro») se
   reflejan al instante. Sin `useEffect`. La fecha es no controlada con `key={valor}` para no pelear con la edición por segmentos.
3. **Porcentajes en %**: se muestran como `roundTo(v·100, 6)` y se guardan como `roundTo(n/100, 10)` para evitar ruido binario.
4. **`Meses_Construccion`** está en `m.inputs` pero el libro lo marca `calc` (= Mes_COD_Cron): se muestra sólo lectura, como pide
   el brief. Si se quiere editarlo desde Supuestos basta quitar la condición `calc` para ese nombre (o hacerlo desde Trámites).
5. **Bloque B**: C·B·F se leen del modelo (`m.inputs[esc][k]`) y no de `escenarios.values` para que, si algún día se editan,
   el acento avise (control G4); hoy coinciden siempre.
6. **Conteo «por confirmar»**: `n_por_confirmar_esperado` del book.json vale 18 y `frozen.N_Por_Confirmar` 19 (la hoja suma un
   ítem por los drivers de 05: `COUNTIF(...,2)+(COUNTA(Drv_Wp)>0)`; la constante C141 del libro es 19). Para no mostrar «19 frente
   a 18» como si fuera una discrepancia, el aside compara las entradas marcadas en la hoja (18, contadas en vivo desde
   `rows[].confirm` + `escenarios[].confirm`) con las 18 esperadas, y muestra aparte el 19 del libro «con los drivers de 05».
7. **Fórmulas de 12_Fuentes** transcritas al AST (ver arriba) en lugar de mostrar el valor cacheado del libro (que además venía en
   formato en-US: «0.82», «5.0», «17.5»).
8. **Colores**: acento sólo en editable/distinto del libro/Custom/enlaces; glifos de estado con `Status`/`StatusGlyph`; nada de
   hex. Grises ordinales sólo como muestra de trazo en cabeceras y en la Guía.
9. **Edición externa**: enlaces a la vista Exergy (índice de la Guía, paso de la Guía si lo hubiera, anclas «#'09_Exergy'!…» de
   «Sensibilizado en») se omiten cuando `isExterno()`.

## Textos de UI escritos por el agente (para revisión)

Supuestos:
- Título «Supuestos».
- Párrafo bajo la cabecera: «Acento = editable y distinto del libro (aparece «libro: …» y ↺ para volver); tinta terciaria =
  calculado por el motor; ▲ = por confirmar (sin fuente firme). Cada cambio recalcula los {n} casos; los valores viven en esta
  sesión y no se guardan.»
- Chips: «{n} supuestos por confirmar (lista en 12 §A)» (adaptado de C17), «sandbox: {n} entrada(s) distinta(s) del libro ·
  volver al libro» (igual que Resumen), «valores del libro {versión} ({fecha})».
- Sección «Panel de mandos» (guía = C7 del libro). Botón «editar ↓» (texto del libro).
- Cabeceras de tabla: «Parámetro», «Valor», «Unidad», «▲» (tooltip «Por confirmar (sin fuente firme)»), «Sensibilizado en»,
  «Nota», «Nombre». Botones «nota ▾ / nota ▴», «mostrar notas / ocultar notas». «libro: …» y «↺» (tooltip «Volver al valor del
  libro para {nombre}»). Tooltips «Calculado por el motor (no editable)», «Informativo: no alimenta cálculos», «Por confirmar:
  {confirm_why}», «Sólo lectura: definición entregada del caso», «Definición entregada: … (control G4)», «Abrir la vista …».
  Placeholder «vacío» y texto «vacío» para celdas en blanco.
- Sección «Por confirmar», guía «Marcados aquí + los drivers de escala de 05 (un ítem); lista en 12 §A» (texto I140 del libro);
  aside «{n} marcadas en esta hoja frente a {m} esperadas al entregar · {k} en el libro (con los drivers de 05)»; nota «Las entradas
  marcadas ▲ no tienen fuente firme; la lista completa, con las simplificaciones declaradas y las fuentes, está en Fuentes.»

Guía:
- Título «Guía de lectura» (B1 del libro). Guías de sección tomadas de la hoja (D5, D12) o escritas: «{n} preguntas · cada
  respuesta señala la hoja donde se ve el dato · las cifras son las del momento», «{n} términos en {g} grupos · la cifra viva
  cambia con Supuestos y Mandos». Sección «Índice de hojas», guía «cada hoja del libro y la vista del artefacto que la sustituye».
- Cabeceras «En el libro», «Significado», «En el artefacto», «Término» (las otras dos son del libro). Columna «En el artefacto»
  (muestras + textos): «texto en acento», «acento: entradas editables (Supuestos y Mandos)», «los mismos glifos; el color va sólo
  en el glifo, el texto en tinta», «tinta · tinta 2 · tinta 3», «tres tintas: texto y cifras · etiquetas y notas · pistas, ejes y
  valores calculados», «▲ en la columna «por confirmar» de Supuestos, con el motivo al pasar el cursor», «el dato que decide»,
  «acento: enlaces y el dato que decide», «≠ libro», «acento en Supuestos: entrada distinta del libro (aparece «libro: …» y ↺)»,
  «acento, trazo continuo», «Sección», «fila de sección en las tablas y cabecera de sección con su guía», «gris oscuro, trazo
  discontinuo», «sin agrupación: las series anuales se muestran completas», «gris medio, trazo continuo», «cifra bajo el umbral»,
  «rojo (riesgo) sólo en la cifra que queda bajo el umbral», «gris claro, trazo punteado», «valor del libro», «el motor recalcula
  todo con cada cambio; lo que sólo existe en el libro (controles, conteos) lleva esta marca».
- Botones «→ {vista} {hoja}» y «{vista} →».

Fuentes:
- Título «Fuentes y calidad» (B1). Guía de §D cuando la hoja no trae texto en C: «{n} fuentes · {m} con enlace». Nota de §A: «Los
  valores marcados se editan en Supuestos; el control I2 de Controles vigila que la lista esté al día.» Enlace «abrir ↗» (libro).

Controles:
- Título «Controles». Chips «{n} control(es) en ■», «Motor ≡ Excel {ok}/{n} salidas · {casos} casos» (igual que Resumen).
- Sección «Estado del libro», guía «resumen de la hoja a la fecha de corte ({versión}, {fecha})»; nota «Los estados de los {n}
  controles ({k} en ●) son los del libro {versión} a la fecha de corte ({fecha}); el artefacto no los recalcula. Si cambia entradas
  en Supuestos o Mandos, los controles siguen reflejando el libro entregado.»
- Sección «Autocomprobación del motor», guía «en vivo: motor TypeScript frente al oráculo (salidas de los casos del libro)»; chip
  «Motor ≡ Excel · {casos} casos · orden de casos verificado / orden de casos distinto del esperado»; nota «El motor recalcula los
  {n} casos con las entradas entregadas ({versión}, {fecha}) y compara cada salida con la del libro; la comprobación no depende de
  los cambios hechos en la sesión. Recalcula salidas, no controles: la tabla de abajo es la del libro.»
- Sección «Los controles del libro», guía «identidades, candados y rangos agrupados como en la hoja · clic en una fórmula larga
  para desplegarla»; filtro «Todos ({n})» / «Con aviso ({n})»; cabeceras «#», «Qué prueba» (libro), «Estado» (libro), «Fórmula del
  libro»; pie «Estados del libro {versión} ({fecha}); fórmulas tal cual en la hoja 13_Controles, columna D.»; «Ningún control con
  aviso: todos en ●.» (estado vacío del filtro).

## Dudas y sugerencias (no se tocó nada ajeno)

1. **Extractor / book.json**: (a) `fuentes.cells` sólo trae B–D; la tabla §C de 12 tiene E «Fiscal» y F «Resultado reportado»
   (filas 43–47) que copié como constante `SECCION_C_EF`. Mejor que el extractor incluya E–F (o `fuentes.conciliacion` como tabla).
   (b) Las fórmulas de `fuentes.cells[].f` llegan como texto; si el extractor las emitiera como `Live` (AST), sobraría `LIVE_CELLS`.
   (c) `inputs.escenarios` no trae la columna H («Sensibilizado en») ni `confirm_why`; transcribí H38:H45 en `SENS_BLOQUE_B`.
   (d) `inputs.n_por_confirmar_esperado` = 18 mientras el libro (C141 y `frozen.N_Por_Confirmar_Esperado`) dice 19: parece contar
   sólo las entradas marcadas en 01, sin el ítem de los drivers. Lo resolví como se explica en Decisiones 6; convendría unificar.
2. **Textos del libro con cifras desactualizadas** (no se corrigieron, van tal cual): la intro de 00b dice «seis preguntas frecuentes
   y un glosario de treinta términos» (hay 7 y 38); `sheets["00b_Guía"].labels["6"]` dice «110 casos» mientras `guia.pasos[0]`
   dice 111 (usé `guia.pasos`).
3. **Componentes compartidos**: `Status`/`LiveStatus` no muestran la marca `Frozen`; en los chips de estado congelado añadí
   `<Frozen>` como hijo de `Status` (funciona, pero un prop `frozen` en `LiveStatus` sería más limpio). `DataTable` no admite `id`
   por fila: puse el `id` de desplazamiento en el `<span>` del label. `Trace` sólo recibe `name` (no tengo la celda de 01 por fila en
   book.json).
4. **Meses_Construccion** (ver Decisión 4): ¿debe poder editarse desde Supuestos? Hoy es sólo lectura como `calc`; Trámites no
   es editable en el artefacto, así que nadie puede moverlo. Cambio trivial si se desea.
5. Los enlaces a «exergy» se ocultan en la edición externa; si la navegación externa hace algo distinto con esa vista, avisar.
