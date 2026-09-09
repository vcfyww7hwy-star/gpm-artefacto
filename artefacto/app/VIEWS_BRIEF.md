# Brief F4 — vistas del artefacto «Modelo FV Montecristi → GPM»

Artefacto interactivo (React 19 + TS + Tailwind con tokens CSS) que sustituye/acompaña al libro Excel
`Modelo_FV_5MWp_GPM_v3.1.xlsx` (planta FV 5 MWp Montecristi → Gran Piazza Machala; dueño SALELGI S.A.; gerencia Exergy).
Ya existen y funcionan: cascarón (TopBar, SideNav, Mandos, ⌘K), vistas **Resumen** y **Sensibilidad** (`src/views/`), motor
TS verificado (111 casos ≡ Excel), `book.json` (todos los textos del libro) y los componentes compartidos listados abajo.
Cada agente escribe 3–4 vistas nuevas en `src/views/<Nombre>.tsx` (y `src/internal/` si es interna). Idioma de la UI: **español**.

## 0. Reglas duras (no negociables)

1. **Cero contenido inventado.** Todo texto de contenido sale de `book.json` (`m.book…`) o de las etiquetas de fila de la hoja
   Excel equivalente (`m.book.sheets["07_Fiscal"].labels[fila]` o `python3 scripts/dump_sheet.py 07_Fiscal`). Los títulos de
   sección y guías cortas de UI («qué muestra esta tabla») sí puede escribirlos el agente, sobrios y en español, sin adjetivos
   de marketing. Nunca paráfrasis de textos legales/técnicos: si el libro lo dice de una forma, el artefacto lo dice igual.
2. **Toda cifra la calcula el motor** (`useModel()`), nunca literal. Si un dato sólo existe en el libro (controles, conteos),
   se toma de `m.book.frozen`/`m.book.calc_names` y se marca con `<Frozen />`.
3. **Formato es-EC** con `src/lib/format.ts` (`fmtNum`, `fmtPct`, `fmtUSD`, `fmtUSDCompact`, `fmtX`, `fmtYears`, `fmtDate`,
   `fmtMonthYear`, `fmtPP`, `fmtSigned`, `MINUS`). Nunca `toFixed`/`toLocaleString`/`Intl` para mostrar cifras.
4. **Sistema visual**: sólo clases Tailwind mapeadas a tokens (`text-ink`, `text-ink-2`, `text-ink-3`, `bg-surface`,
   `bg-surface-2`, `border-hairline`, `text-accent`, `bg-accent-soft`, `text-ok`, `text-warn-text`, `text-risk`, `text-info`,
   `rounded-1`, `shadow-1`, `font-serif`, `font-mono`) y variables CSS (`var(--accent)`, `var(--c-conservador|base|favorable)`,
   `var(--cat-1|2|3)`, `var(--ok)`, `var(--warn-fill)`, `var(--risk)`, `var(--ink-3)`, `var(--hairline)`, `var(--surface)`).
   Prohibido: colores hex literales, emojis, `rounded-lg` genérico en todo, degradados, sombras fuertes. El color **sólo donde
   hay significado**: estado (● ▲ ■ ◇), caso Custom (acento), series categóricas (≤ 3, `--cat-*` en orden fijo), casos C·B·F
   (grises ordinales + trazo `--dash-*`). Texto siempre en tinta (`ink`, `ink-2`, `ink-3`), nunca del color de la serie.
5. **Gráficos**: un solo eje y; leyenda si hay ≥ 2 series; hover con tooltip; categorías en orden fijo; nunca dual-axis;
   nunca arcoíris. Usar los componentes de `src/components/charts/` (no d3 directo, no nuevas librerías).
6. **Tema claro y oscuro** automáticos vía tokens: no escribir colores por tema. Nada de `localStorage`.
7. **Anatomía de vista** (idéntica a Resumen/Sensibilidad): `<div className="mx-auto flex max-w-[1180px] flex-col gap-8">`
   → `<ViewHeader title sheet=…>` (la intro es la celda B2 de la hoja: misma redacción que el Excel) → `<Section title guide>`…
   Tablas con `<DataTable>`; notas en `<Note>` (serif); parámetros en `<Chip>`.
8. **Caso seleccionado**: la vista recibe `caseId` (`"custom" | "conservador" | "base" | "favorable"`); `const ci = m.idx(caseId)`;
   `const c = m.cases[ci]` → `c.params`, `c.result.scalars[SCALAR_LABELS.K]`, `c.result.outputs[OUTPUT_LABELS.TIR]`,
   `c.result.blocks.FCF_u` (27 valores, t = −1…25 = `T_AXIS`). Color/trazo del caso: `CASES.find(x => x.id === caseId)` →
   `colorVar`, `dashVar` (`import { CASES } from "@/lib/views"`). Cuando la tabla compara los cuatro casos, orden fijo
   Custom · Conservador · Base · Favorable (`CASE_X, CASE_C, CASE_B, CASE_F` de `@/model/cases`).
9. **Trazabilidad «¿de dónde sale?»**: junto a cada cifra/tabla clave, `<Trace name="TIR_Proyecto" cell="08_Flujo!D7" />`
   (nombre definido Excel y/o celda). Los nombres están en `book.calc_names` (claves) y en las fórmulas del dump.
10. **Edición externa**: la vista **Exergy** es interna. Debe vivir en `src/internal/Exergy.tsx` y sólo importarse detrás de
    `process.env.VITE_EDITION !== "externo"` (ver patrón en `src/lib/edition.ts`; la integración en App.tsx la hace el
    coordinador — el agente sólo crea el archivo y documenta en su nota). Las demás vistas no muestran fee/margen/utilidad de
    Exergy salvo lo que ya aparece en el libro como costo de SALELGI (fee de gerencia y fee O&M son costos de SALELGI: sí se ven).
11. **No tocar** archivos fuera de `src/views/<propias>.tsx`, `src/internal/<propias>.tsx`. Si un componente compartido necesita
    un cambio, describirlo en `NOTES_<agente>.md` (raíz del app) en lugar de editarlo. No ejecutar `npm run build*`, no
    publicar, no capturas. Sí ejecutar `npx tsc -b` hasta que compile sin errores.
12. **Accesibilidad y robustez**: `n/a`/`no cruza` de salidas se muestran tal cual (texto); `null` → `—`; nada debe lanzar si
    el usuario cambia entradas en Mandos (potencia 5–8 MWp, deuda 0–100 %, etc.).

## 1. API del modelo (`import { useModel, BOOK } from "@/model/store"`)

```ts
const m = useModel();
m.inputs            // Inputs (nombres Excel: Potencia_DC, Tasa_Descuento, Fee_OM_kWp, Esc_Peaje[4], rubros[9], Y_P50[30], …)
m.extras            // entradas de 01 que el Motor no usa: Capacidad_Alimentador_kW, Tasa_Desc_Alt1/2, Ha_Disponibles,
                    //   Tope_SGDA_kW, Cargo_Demanda, Cargo_Comercializacion, SAPG_mes, Meses_Recup_IVA, Umbral_Riesgo_Alto/Medio,
                    //   Tol_Costo_Tramites, Tol_Dias_COD  (m.setExtra(name, value) para editarlas)
m.derived           // Derived: Potencia_AC, Hectareas, Consumo_Anual, Consumo_Mensual[12], Tarifa_Evitable, Frac_Peaje[27],
                    //   Loss_Ref, Loss_Act, F_Recorte, CAPEX_*_f1, Factor_Caso, Reemplazo_USD, Desmantelamiento_USD, Eff_Scen…
m.cases[i]          // { name, desc, params, result: { scalars, outputs, blocks } }  · i = 0…110
m.idx(caseId)       // índice del caso seleccionado (0–3)
m.num(i, "TIR")     // salida numérica o null · claves OutputKey: TIR VAN PB LCOE TIR_eq VAN_eq DSCR_min DSCR_avg Ahorro1
                    //   Aporte_eq VAN_X TIR_G E1 NoRec Cob Nominal_X
m.out(i, "PB")      // número | "n/a" | "no cruza"
m.live(l)           // texto vivo del libro (book.json) evaluado con los valores actuales → string
m.nameValue("Deuda_Max_Plazo2")  // valor de un nombre definido del libro (o null)
m.book              // Book (ver §3) · m.book.frozen.N_Controles …
m.setInput(k, v) · m.setInputs(patch) · m.reset() · m.dirty · m.dirtyKeys · m.dirtyExtras
m.selfCheck         // { status, compared, failed, worst[] } motor ≡ oráculo (1776 salidas)
```

Escalares del caso (`SCALAR_LABELS`, `c.result.scalars[SCALAR_LABELS.X]`): frec (factor de recorte) · AC (Potencia AC kW) · ha ·
K (CAPEX industrial sin IVA) · IVA · Kdep (CAPEX depreciable) · DepEq · DepCiv · DedAd (deducción adicional/año) · Terr ·
Resid · OPEX1 · Sub (subtotal EPC) · D (deuda) · IDC · Dt (deuda total COD) · n (nº cuotas) · PMT (cuota) · fKeff · fEsc ·
Krep (reemplazo inversores USD) · Decom (desmantelamiento USD).

Bloques anuales (`c.result.blocks.<B>`, 27 valores t = −1…25): E (energía producida MWh) · Eval (energía valorizable) ·
Ahorro · OPEX · Peaje · EBITDA · Dep (depreciación total) · Part_u · IR_u · Terr (flujo del terreno) · FCF_u · Cum_u · Int ·
Amort · Part_l · IR_l · CFADS · EQ (flujo del accionista) · DSCR (null si no hay servicio) · DF (factor de descuento) ·
Ux (utilidad Exergy) · Ix (impuestos Exergy) · Tx (terreno Exergy) · Fx (flujo Exergy) · Gx (flujo grupo) · Krep · PoolU · PoolL.

Parámetros del caso (`c.params`, 30): fK fT scen fO pj escT part iva cont deb rd lev plazo gr P ratio terr finT fPre kfix disp dK
pkw rep ug ncon req dec deg dedad (etiquetas en `PARAM_LABELS`).

Módulos ya verificados contra el libro (usarlos, no reimplementar): `capexTable(i, d, params)` (`@/model/capex`: filas 7–24 de
05 para cualquier caso) · `opexLines(i, d, params, t)` / `opexSeries(...)` (`@/model/opex`: cinco líneas de 06) ·
`escalas(i, params)`.

## 2. Componentes disponibles

- `@/components/ViewHeader`: `ViewHeader({title, sheet, intro?, children})`, `Section({title, guide, aside, children})`, `Chip`, `Note`.
- `@/components/DataTable`: `DataTable<T>({columns, rows, rowKey, emphasize?, muted?, selected?, onRowClick?, sectionBefore?, size?, footer?})`
  con `Column<T> = {key, label, align, width, render, mono?, muted?, nowrap?, title?}`.
- `@/components/Status`: `Status({kind, children})`, `StatusGlyph`, `stripGlyph`; `@/model/book`: `statusOf(text)`.
- `@/components/Live`: `<Live text={live} />` (texto vivo con marca si usa datos congelados), `<LiveStatus text=… />`,
  `<Frozen what=… />`, `<Trace name cell />`.
- `@/components/KpiTile`: `KpiTile({label, value, compare, state, strip, excelName})` (tira C·B·F: `StripValue[]`).
- Gráficos (`@/components/charts/…`): `Series({x, series:[{id,label,values,color,dash?,area?,bars?}], yFormat, refLine?, height})`,
  `StackedBars({x, stacks, yFormat, line?})`, `Heatmap({rowLabels, colLabels, cells, center, halfSpan, legend})`, `Tornado`,
  `CintaAnual({t, fcf, cum, lineColor, lineDash, codYear, payback})`, `Gantt({rows, months, monthLabel, markers, window, selected, onSelect})`,
  `RiskMatrix({points, umbralAlto, umbralMedio, selected, onSelect})`; utilidades `linear`, `ticks`, `useMeasure`, `divergingFill`.
- Motor: `import { T_AXIS, SCALAR_LABELS, OUTPUT_LABELS, PARAM_LABELS, edate, parseISODate, formatISODate } from "@/engine"`.

Ejemplo mínimo de vista:
```tsx
import { T_AXIS, SCALAR_LABELS } from "@/engine";
import { Section, ViewHeader } from "@/components/ViewHeader";
import { DataTable } from "@/components/DataTable";
import { fmtUSD } from "@/lib/format";
import type { CaseId, ViewId } from "@/lib/views";
import { useModel } from "@/model/store";

export function Opex({ caseId }: { caseId: CaseId; onNavigate: (v: ViewId) => void }) {
  const m = useModel();
  const c = m.cases[m.idx(caseId)];
  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="OPEX de SALELGI" sheet="06_OPEX" />
      <Section title="Composición del año 1" guide={`caso ${c.name}`}>…</Section>
    </div>
  );
}
```

## 3. `book.json` (`m.book`) — qué hay en cada sección (tipos en `src/model/book.ts`)

- `inputs.rows[]` (97; las filas con sólo `section` son cabeceras de bloque): `name, label, value, formula (Live si es calculada),
  calc, unit, fmt, confirm (· por confirmar), note (Live), info, yesno, selector[], short (Live), label2, sens [texto, ancla],
  confirm_why`. `inputs.bloques[]` (9 bloques A–I con `title, guide, names[]`), `inputs.escenarios[]` (8 filas del bloque B con
  `values {X,C,B,F}`), `inputs.panel[]` (8 tarjetas del panel de mandos de 01: `label, value(Live), sub(Live), name`),
  `inputs.confirm_list[]` (21 textos «por confirmar»), `n_por_confirmar_esperado`.
- `capex.rubros[]` (9: `name, desc, base_5mwp, pct_comp, pct_ext, arancel, iva, source(Live), drv_*`), `capex.notas[]` (1)…(12),
  `capex.headers`, `capex.labels` (filas 16–30), `capex.reemplazo` (filas 39–41), `capex.intro`.
- `opex.lines[]` (filas 7–12 de 06 con etiquetas y nota H7), `opex.serie_labels[]`, `opex.memo_exergy[]`.
- `legal.rows[]` (25 normas: `tema, norma, texto, aplicacion, estado, confianza`; Live), `legal.candados[]` (5), `legal.contratos[]`
  (8), `legal.dudas[]` (15 zonas grises: `id, duda, impacto, accion, prioridad`), `legal.table_headers`.
- `tramites.rows[]` (17 hitos RC-xx: `id, tramite, autoridad, base_legal, inicio, dur, fin, costo, predecesor, critica (Sí/No/Parcial),
  riesgo, nota`), `tramites.mes1` («2026-10-01»), `tramites.headers[]`, `tramites.totales` (filas 25–27), `tramites.gantt_leyenda`,
  `tramites.memo[]` (memo estático de escenarios), `tramites.controles.cron`.
- `riesgos.rows[]` (15: `categoria, riesgo, prob, impacto, mitigacion, dueno, disparador`), `riesgos.umbrales {alto, medio}`, `headers`.
- `fuentes.rows[]` (26 fuentes con `texto, url`), `fuentes.secciones[]` (A–E), `fuentes.cells[]` (todas las celdas B–D de 12).
- `controles.rows[]` (79: `group, id, desc, status (texto del libro), formula, prueba`), `controles.resumen`.
- `guia.pasos[]` (5), `guia.convenciones[]` (14), `guia.grupos[]` (5 grupos de glosario con `items {term, def, live, anchor}`),
  `guia.faq[]` (7 `{q, a}` Live), `guia.index[]`.
- `sens.tornado[]`, `sens.tornado_short[]`, `sens.intro`.
- `sheets[hoja]` → `{intro (B2), title (B1), labels {fila: texto}}` para las 15 hojas.
- `frozen` (N_Controles 79, N_Controles_OK 78, N_Por_Confirmar 19, Estado_*, Deuda_Max_Plazo*, Mes_COD_Cron, Costo_Desarrollo_Cron,
  Fin_RC09/10, Check_*), `calc_names` (valor de los 317 nombres), `meta {version, fecha_analisis}`.

Para ver la estructura exacta de una hoja: `python3 scripts/dump_sheet.py 08_Flujo 40 80 --cols B,C,D,E --maxlen 120`.
Referencias de fila útiles (mapas del generador): 07_Fiscal filas 22–38 (sin deuda), 41–42 (IVA), 45–52 (con deuda);
08_Flujo KPI 7–25, serie 43–61 (sin deuda), 63–76 (deuda, CFADS, DSCR); 09_Exergy KPI 5–14, serie 35–52, grupo 71;
04_Energia 15–29 (consumo mensual), 31–45 (balance mensual año 1), 47–61 (valor evitado), 64–86 (técnicos: recorte, tarifa),
88–99 (serie anual: yields, E_P50/E_P90, E_Activa, E_Val, no reconocida, Frac_Peaje).

## 4. Especificación por vista (secciones mínimas; el agente puede añadir lo que la hoja tenga y quepa con sobriedad)

### Supuestos (`Supuestos.tsx`, hoja 01_Supuestos) — la única vista editable además de Mandos
- Cabecera + panel de 8 tarjetas de `inputs.panel` (label, `m.live(value)`, `m.live(sub)`).
- Bloques A–I (`inputs.bloques`): tabla por bloque con columnas: nombre (label + `label2`/`short` como subtexto), valor
  (editable si no `calc`/`info`: número → `<input type=number>` con paso razonable; `yesno`/`selector` → segmentado; fecha → input date;
  el bloque B se edita por columna Custom (las columnas C·B·F se muestran sólo lectura desde `inputs.escenarios`), unidad,
  «· por confirmar» (▲ + tooltip `confirm_why`), sensibilizado en (`sens[0]`, texto), nota (Live, plegable o en tooltip),
  `<Trace name=…>`. Valores calculados (`calc`) en tinta terciaria con la cifra viva (usar `m.nameValue(name)` y el `fmt`).
  Editar = `m.setInput(name, v)` si `name in m.inputs`, si no `m.setExtra(name, v)`. Marcar en acento las entradas ≠ libro
  (`m.dirtyKeys`/`m.dirtyExtras`) y ofrecer «volver al libro» (`m.reset`).
- Sección «Por confirmar» con `inputs.confirm_list` y el conteo frente a `n_por_confirmar_esperado`.
- Formatos: `fmt` del libro → usar fmtPct para «%», fmtUSD para USD, fmtNum con decimales según `fmt` ("0.00" → 2).

### Energía (`Energia.tsx`, 04_Energia)
- KPI: energía año 1 (E1) frente a consumo anual (Cob %), tarifa evitable ($/MWh), factor de recorte, potencia AC, hectáreas.
- Consumo mensual 2025 → nivel 2026 (`m.inputs.Consumo_2025_*`, `m.derived.Consumo_Mensual`, `Factor_Nivel_2026`): tabla o barras.
- Balance mensual del año 1: producción mensual (E1 × `Perfil_Mensual`) frente a consumo mensual → `StackedBars`/`Series`
  con las dos series (`--cat-1` producción, `--cat-2` consumo) y aviso de excedentes (art. 27) si producción > consumo.
- Serie anual: E (producida) y Eval (valorizable) del caso + P50/P90 (casos 4–5) → `Series` con leyenda; degradación.
- Técnicos: curva de recorte (`CR_Ratio`/`CR_Loss` → `Series` con el punto del ratio actual), tarifa evitable por bloques
  (Frac_A/B/C, Tarifa_A/C, cargos) y Frac_Peaje.
### CAPEX (`Capex.tsx`, 05_CAPEX)
- Tabla de rubros de `capexTable` (columnas de la hoja: #, rubro, costo base 5 MWp, % ext., arancel %, arancel+ISD, FODINFA,
  capitalizable sin IVA, IVA %, IVA, $/Wp; filas de contingencia, subtotal EPC, gerencia, total industrial, con IVA, terreno,
  total con terreno) con `emphasize` en totales; notas (1)…(12) de `capex.notas` plegables o en tooltip por fila.
- Barras apiladas (o barras horizontales) de la composición por rubro del caso; comparativo de los cuatro casos
  (K, $/Wp, IVA, definición del CAPEX del caso: `m.live` de la definición si existe, o `params.kfix > 0 ? "fijo …" : "bottom-up × …"`).
- Drivers Wp/Wac/fijo por rubro (tabla de 05 filas 45–53) y factor del caso (fKeff, fEsc, Factor_Caso), reemplazo/desmantelamiento
  (`capex.reemplazo`, scalars Krep/Decom).
### OPEX (`Opex.tsx`, 06_OPEX)
- Composición del año 1 (`opexLines(...,1)`: USD/año, $/kWp, % del total) con la nota H7 de la hoja; serie anual apilada
  (`StackedBars` de las 5 líneas, `--cat-*` para las 3 mayores y grises para el resto, o 5 grises ordinales) y OPEX unitario;
  memo de costos propios de Exergy sólo como texto de la hoja (no cifras de margen).
### Fiscal (`Fiscal.tsx`, 07_Fiscal)
- Cifras clave (filas 7–16: CAPEX depreciable, deducción adicional anual, tope vinculante (Live D9 si está en labels/calc_names →
  reconstruir la regla con los valores: comparar `Kdep·Pct_Elegible/Vida` con `Tope_DedAd_Pct·Ingresos_SALELGI`), ingreso mínimo,
  totales del horizonte Σ impuestos sin/con deuda, escudo de la deducción, IVA).
- Serie anual A (sin deuda): Ahorro, OPEX, Peaje, EBITDA, Dep, Part_u, IR_u, impuestos = Part_u+IR_u, tasa efectiva → tabla
  compacta por año (usar `DataTable` size sm con años en columnas o filas) + `StackedBars` de participación + IR.
- B: IVA pagado/recuperado (IVA scalar, Fase_m1, params.iva). C: con deuda (Int, Part_l, IR_l, escudo = (Part_u+IR_u)−(Part_l+IR_l)).
  Pool de pérdidas (PoolU/PoolL) si params.ug ≥ 0.
### Flujo (`Flujo.tsx`, 08_Flujo)
- KPI del caso (filas 7–25 de 08): TIR, VAN, payback, LCOE, ahorro año 1, Σ ahorro, reducción de factura…, deuda: TIR accionista,
  VAN accionista, DSCR mín/prom (año), aporte, cuota, deuda total, servicio total.
- Tabla anual completa sin deuda (componentes → FCF_u → acumulado → descontado) y con deuda (desembolso, saldo, intereses,
  amortización, CFADS, servicio, DSCR, EQ) — `DataTable` size sm con t en filas y componentes en columnas; `CintaAnual` del caso;
  `Series` DSCR frente al objetivo (`refLine` = DSCR_Objetivo) y EQ.
### Exergy (`src/internal/Exergy.tsx`, 09_Exergy) — INTERNA
- KPI: VAN Exergy, TIR Exergy (`m.nameValue("TIR_Exergy")`), nominal Σ, VAN gerencia/O&M/terreno si reconstruibles, carga sobre
  el ahorro de GPM (`Carga_Exergy`), TIR/VAN del grupo (TIR_G, VAN_Grupo = suma de VAN_X y VAN? → usar salidas: VAN_X y TIR_G).
- Serie anual Ux, Ix, Tx, Fx (StackedBars) y Gx (grupo) frente a FCF_u; texto de la hoja (intro y etiquetas de fila).
### Legal (`Legal.tsx`, 02_Legal)
- Candados (5) con `LiveStatus`; tabla de 25 normas (tema, norma, qué dice, implicación, estado·verificación, confianza) con filtro
  por confianza y búsqueda; contratos (8); zonas grises/dudas (15) con prioridad (▲ alta en color de estado). Todo `<Live>`.
### Trámites (`Tramites.tsx`, 03_Tramites)
- `Gantt` de las 17 filas (start=inicio, end=fin, critical = critica === "Sí"), meses = max(fin)+1, `monthLabel` =
  `fmtMonthYear(edate(parseISODate(mes1), k-1))`, marcador COD implícito (`Mes_COD_Cron` = `m.inputs.Meses_Construccion`) y ventana
  de vigencia de la factibilidad (RC-09 fin → +6 meses; control F12: RC-10 debe caer dentro). Tabla de hitos (todas las columnas de
  la hoja, con nota Live), totales (Σ costos frente al rubro 9 del CAPEX del caso: `capexTable(...).rubros[8].costo`, tolerancia
  `m.extras.Tol_Costo_Tramites`), memo de escenarios (`tramites.memo`, texto estático del libro con su aviso «memo estático
  (sombra Python ≡ Motor, 08-sep-2026)»).
### Riesgos (`Riesgos.tsx`, 11_Riesgos)
- `RiskMatrix` (15 puntos; id = número de fila 1…15) + tabla (categoría, riesgo (Live), p, i, score = p×i, nivel según umbrales
  `m.extras.Umbral_Riesgo_*` con Status, mitigación (Live), dueño, disparador); orden por score desc; selección sincronizada.
### Fuentes (`Fuentes.tsx`, 12_Fuentes)
- Secciones A–E de la hoja a partir de `fuentes.cells` (texto tal cual, agrupado por las cabeceras de `fuentes.secciones`);
  la lista D con enlaces (`<a href target=_blank rel=noreferrer>` en acento, URL visible en mono pequeño); §A = `inputs.confirm_list`.
### Controles (`Controles.tsx`, 13_Controles)
- Estado global (`controles.resumen`, `frozen.N_Controles*`) + autocomprobación del motor (`m.selfCheck`); tabla de 79 controles
  por grupo (`sectionBefore`) con `Status` derivado del texto (`statusOf`), descripción, fórmula en mono plegable/tooltip.
  Aviso claro: los estados son los del libro a la fecha de corte (`<Frozen what="Control">`); el motor sólo recalcula las salidas.
### Guía (`Guia.tsx`, 00b_Guía)
- Pasos (5, Live), convenciones (14; el color del libro se traduce a los tokens: tinta = editable, glifos = estado…),
  glosario por grupos (Live), FAQ (Live, plegable), índice de hojas ↔ vistas (`guia.index` → botón `onNavigate(viewId)`;
  correspondencia: 01→supuestos, 02→legal, 03→tramites, 04→energia, 05→capex, 06→opex, 07→fiscal, 08→flujo, 09→exergy,
  10→sensibilidad, 11→riesgos, 12→fuentes, 13→controles, Motor_Sens→sensibilidad).

## 5. Entrega de cada agente
- Archivos `src/views/<Nombre>.tsx` (export nombrado `<Nombre>`), props `{ caseId: CaseId; onNavigate: (v: ViewId) => void }`.
- `npx tsc -b` limpio. Sin `console.log`. Sin dependencias nuevas.
- `NOTES_<agente>.md` con: qué muestra cada vista, decisiones, textos de UI escritos por el agente (para revisión), dudas.
