# NOTES_B — vistas Energía · CAPEX · OPEX (agente B)

Archivos creados (sólo estos; ningún archivo ajeno tocado):

- `src/views/Energia.tsx` — `export function Energia({ caseId, onNavigate })` · hoja 04_Energia
- `src/views/Capex.tsx` — `export function Capex(...)` · hoja 05_CAPEX
- `src/views/Opex.tsx` — `export function Opex(...)` · hoja 06_OPEX

Las tres reciben `{ caseId: CaseId; onNavigate: (v: ViewId) => void }` y usan `caseId` (todo se calcula para el caso seleccionado);
`onNavigate` se acepta por contrato y no se desestructura.

`npx tsc -b`: limpio (0 errores). `npx oxlint` sobre los tres archivos: sin avisos. Sin `console.log`, sin dependencias nuevas, sin
`toFixed`/`Intl`, sin colores literales, sin builds ni publicaciones.

Integración pendiente (coordinador, `App.tsx`): `view === "energia" ? <Energia caseId={caseId} onNavigate={navigate} />`, ídem
`capex` y `opex`.

## Verificación hecha (además de tsc)

1. **Fórmulas de 04 reproducidas ≡ libro** (script temporal con `computeAll` + `data/sheets.json`, ya borrado): E33, F33, J33, J49,
   I45 (6.275.900), J61 (707.620,28), K61 (0,112752), J45 (60,25 %), K45 (0 meses), L45 (7 meses), F93 (6.275,9), F94 (5.603,69),
   E11 (8.299 kWp), G100 (−1,55 %), F101 (194,1), D78 (0), J81 (0,18 %); la energía P50/P90 por año con los parámetros del caso
   coincide con los bloques E de los casos 4–5 del Motor para el Custom y con E1 del Conservador (P90).
2. **Render estático en Node** (`react-dom/server`, bundle esbuild temporal) de las tres vistas con el `ModelProvider` real para los
   cuatro casos: sin excepciones; el texto no contiene `NaN`, `undefined`, `null`, `Infinity`, `#NAME?`, `#REF!`, `#VALUE!`,
   `#DIV/0!`; cero avisos de React (claves duplicadas, etc.). Cifras cotejadas a mano con el dump: 05!N19 4.120.481 · P19 459.043 ·
   N21 253.750 · N23 224.200 · P23 8.740 · N24 9,7 % (Custom); 06!D12 106.500 · E12 21,30 (Custom) y × 1,15 en el Conservador.

## Qué muestra cada vista

### Energía (04_Energia)

- Cabecera `ViewHeader` (intro B2) con chips: D6 de la hoja («5.000 kWp / 3.788 kWac · 1,32 · 5,0 ha», con la potencia y el ratio del
  caso), I6 («Alimentador: 3.800 kW (por confirmar) · predio 10,78 ha», con `m.extras`) y «caso X · P50/P90 · disponibilidad».
- **Resumen · año 1 del caso**: seis `KpiTile` — Producción año 1 (E1 del Motor; compara P50/P90 del año 1 y el yield específico;
  tira C·B·F), Cobertura del consumo (salida Cob; compara con el consumo anual y la «potencia máxima teórica bajo el art. 9» de E11;
  en riesgo si el art. 9 no se cumple), Tarifa evitable efectiva (Tarifa_Evitable en $/kWh y $/MWh, con el texto de E8 vivo),
  Factor de recorte vs referencia (escalar del caso; texto de E7), Potencia AC y Hectáreas (escalares). Debajo, los dos candados de
  la hoja con `Status`: D12 (art. 9) con su nota I12 y D13 (art. 27) con I13, ambos reconstruidos con las cifras del caso.
- **Balance mensual del año 1 · consumo del medidor por bloque horario** (filas 15–29): tabla 2025 A/B/C/total → proyección A/B/C/total,
  fila «Año» destacada; nota E9 viva.
- **Proyección del consumo y factura de referencia** (filas 64–80, aside): tabla ene–may 2025/2026 con Σ, lista Factor de nivel 2026
  (D72), Factura de referencia anual sin SGDA (D76, **valor del libro con `<Frozen>`**), Reducción de la factura en el año 1 (D77,
  **`<Frozen>`**), Valor evitado en el año 1 (J61, vivo), Peaje equivalente por potencia (D78, vivo); nota B80 y el ítem de la lista
  «por confirmar» que declara la demanda 2.200 kW y el FGD 0,956.
- **Balance mensual del año 1 · producción P50/P90 e inyección por bloque** (filas 31–61): `Series` de barras agrupadas producción
  (`--cat-1`) frente a consumo proyectado (`--cat-2`) por mes, estado del art. 27 + texto I13, tabla con las 13 columnas de la hoja
  (perfil, producción, inyección A/B/C/total, consumo, cobertura, ¿excedente?, bloque A neteo, valor evitado, tarifa efectiva) y
  fila «Año»; nota F47.
- **Serie anual** (filas 88–101): `Series` con energía anual P50 y P90 (grises, trazo continuo/discontinuo), energía producida del
  caso (`--cat-1`, con área) y demanda anual (tope del art. 9, `--cat-2`); resumen de energía no reconocida Σ (salida NoRec),
  degradación adicional, disponibilidad y fecha del peaje; tabla t = 1…H con las filas 89–101 de la hoja como columnas.
- **Técnicos**: curva de recorte (`Series` sobre CR_Ratio con `refLine` en la pérdida del ratio del caso; lista J80–J82; tabla H65:J79
  con la fila del ratio del caso seleccionada; nota H83), tarifa evitable por bloques (fracción, tarifa, inyección y valor evitado por
  bloque A/B/C y total), cargos no evitables (Cargo_Demanda, Cargo_Comercializacion, SAPG_mes de `m.extras`), peaje del caso y
  gráfico de barras de Frac_Peaje (fila 99).

### CAPEX (05_CAPEX)

- Cabecera con chips: definición del CAPEX del caso (D27: «fijo X $/Wp» o «bottom-up × f» + «· precios +x %/año»), Factor del caso
  (D30), Contrato de Inversión, IVA recuperable, Escala_Wp/Escala_Wac del caso, potencia.
- **CAPEX del caso**: seis `KpiTile` — Total CAPEX industrial (K, con $/Wp, subtotal EPC y fee; tira C·B·F), IVA del CAPEX (con total
  con IVA; tira), Terreno comprado por SALELGI (N21, con total con terreno), Aranceles + ISD dentro del total (N23, FODINFA aparte),
  % del CAPEX industrial en obra civil (N24), Bottom-up a factor 1 (D28) con la descomposición del factor del caso.
- **Rubros del CAPEX**: `DataTable` con las 17 columnas de la hoja (cabeceras de `capex.headers`) y las filas 7–24 de `capexTable`:
  9 rubros, contingencia, subtotal EPC, gerencia (C18 vivo), TOTAL industrial, total con IVA, terreno (C21 vivo), TOTAL con
  terreno, aranceles + ISD / FODINFA, % obra civil; `emphasize` en los tres totales, filas informativas atenuadas; la columna «nota»
  muestra «(n)» con la nota completa en tooltip. Nota B87 debajo.
- **Composición del CAPEX industrial por rubro**: lista con barras (11 filas: rubros + contingencia + gerencia) — las tres partidas
  mayores del Custom en `--cat-1..3` (Módulos, Estructura, BOS; orden fijo de la hoja), el resto en `--c-base`; USD, % del total y
  $/Wp; fila total.
- **Factores del caso** (filas 27–30): definición, bottom-up a factor 1, escalación (fEsc), factor CAPEX efectivo (fKeff), factor del
  caso; texto E29 vivo y nota B88.
- **Comparativo de los cuatro casos** (filas 26–36): Custom · Conservador · Base · Favorable con muestra de trazo, total sin IVA, $/Wp,
  IVA, total con IVA, fKeff, fEsc y la «Definición del CAPEX en el caso» (I33:I36 reconstruidas, incluida la comparación Favorable
  vs Base en «+0%;-0%»); fila del caso seleccionado resaltada; nota B86.
- **Reemplazo de inversores y desmantelamiento** (filas 38–41): partida, año, base (E40/E41 vivos), USD (escalares Krep/Decom del caso),
  pagador y nota (J40 con sus tres variantes, J41).
- **Drivers de escala** (filas 43–54): tabla % Wp / % Wac / % fijo / Σ / control por rubro, control D54 con `Status`, texto F54 vivo,
  nota B85.
- **Notas — alcance y fuente de cada rubro**: las 12 notas numeradas en `<details>` (resumen = «(n) Rubro»).

### OPEX (06_OPEX)

- Cabecera con chips: factor OPEX del caso, escalación, comprador del terreno → arriendo/predial, horizonte.
- **OPEX del año 1**: cuatro `KpiTile` — Total OPEX año 1 (con $/kWp y la base sin factor × fO; tira C·B·F), OPEX unitario (con el valor
  en t = H; tira), Fee O&M todo incluido → Exergy (% del total y su fórmula), y la línea del terreno que aplica (predial si SALELGI
  compra, arriendo si Exergy).
- **Composición del año 1** (filas 5–12): tabla Línea · USD/año · $/kWp · % del total con la muestra de color de cada línea y la fila
  total destacada; nota H7 de la hoja.
- **Serie anual** (filas 14–24): `StackedBars` de las cinco líneas (tres mayores en `--cat-1..3`, el resto en `--c-base`/`--c-favorable`,
  orden fijo de la hoja), `Series` del OPEX unitario ($/kWp) y tabla t = 1…H con las siete filas de la hoja.
- **Memo · costos propios de Exergy (→ 09)**: sólo las dos etiquetas de la hoja y una nota de que las cifras no se muestran.

## Decisiones

1. **La hoja es «del caso Custom»; la vista generaliza al caso seleccionado.** Las filas 33–61 de 04 (balance mensual y valor
   evitado) se recalculan con E1 del caso (E1 × Perfil_Mensual ≡ E33:E44 porque Σ Perfil = 1); las filas 93–94 (energía P50/P90) con
   la fórmula de la hoja y los parámetros del caso (potencia, ratio, disponibilidad, degradación) — para el Custom coincide
   exactamente con los casos 4–5 del Motor (comprobado). fT = 1 y la potencia es la misma en los cuatro casos, así que el valor
   evitado mensual con Tarifa_A/Tarifa_C es consistente con el Ahorro del Motor.
2. **Art. 9 con P50, como la hoja.** D12 y E11 comparan la energía P50 del año 1 (F93) con la demanda, no la energía del escenario
   del caso; la cobertura del KPI es la salida Cob del Motor (E1 del caso). Se documenta en el código.
3. **Factura de referencia y reducción = valor del libro (`<Frozen>`).** D74 (demanda facturable 2.200 kW) y D75 (FGD 0,956) son
   constantes de la hoja que no viajan en `book.json` ni son entradas del modelo; se muestran `calc_names.Factura_Referencia` y
   `calc_names.Reduccion_Factura` vía `m.nameValue` con la marca y un aviso. El numerador (J61) sí es vivo y se muestra aparte.
4. **Textos con cifras de las hojas, vivos.** Las celdas-fórmula de texto que `book.json` no trae como `Live` (04: D6, I6, E7, E8,
   E9, E11, D12, D13, I13; 05: C18, C21, D27, E29, I33:I36, E40, J40, E41, D54, F54) se reprodujeron en TS con la misma redacción y
   `fmt*` (es-EC ≡ `xlText`). Dos ajustes de redacción no técnicos: E7 «curva pvlib en la página 3» → «curva pvlib más abajo»; el
   título de la fila 31 dice «producción P50» → «producción P50/P90» según el escenario del caso.
5. **`capexTable`/`opexLines` sin reimplementar.** La tabla de rubros, los agregados 16–24, los factores y las líneas del OPEX salen de
   los módulos verificados; K, IVA, fKeff, fEsc, Krep y Decom de los escalares del Motor. El «bottom-up a factor 1» (D28) del caso
   se obtiene como K ÷ (fKeff × fEsc). En OPEX el KPI y la tira usan `opexLines(...).total` (≡ bloque OPEX del Motor) para que la cifra
   y el $/kWp coincidan al céntimo con la tabla de composición.
6. **Colores.** Producción `--cat-1`, consumo/demanda `--cat-2`; P50/P90 de referencia en `--ink-3` (continuo/discontinuo); series únicas
   (curva de recorte, Frac_Peaje, OPEX unitario) en `--ink-2`; composición CAPEX: tres mayores del Custom en `--cat-1..3`, resto
   `--c-base`; OPEX: tres líneas mayores del año 1 del caso en `--cat-1..3`, resto `--c-base`/`--c-favorable`; casos con
   `--c-*`/`--dash-*` y Custom en acento (muestras de trazo). Texto siempre en tinta; ▲ sólo en «SÍ» de excedente y en energía no
   reconocida > 0.
7. **Meses en `Series`.** El componente añade « · t = n» al título del tooltip cuando x > 0; para los ejes de meses y de ratio DC/AC se
   pasan abscisas negativas (−12…−1 y −ratio) con `xFormat` propio, así el tooltip muestra sólo «ene» o «1,32». Ver sugerencias.
8. **Serie anual acotada al Motor.** Se muestran t = 1…min(Horizonte, 25); los años 26–30 de la hoja quedan fuera del horizonte y no
   existen en el Motor (se avisa en la guía de la sección).
9. **Memo Exergy en OPEX sólo como texto** (regla 10): ni Costo_OM_Exergy ni el predial de Exergy se muestran; la nota remite a la hoja 09.
10. **Sin `useMemo` salvo `capexTable`** (cálculos de 12–27 filas; el linter de React Compiler avisaba de una memoización no preservable).

## Fórmulas de 04 reproducidas en TS (celda → código)

- E33:E44 `=Potencia_DC/1000*Yield_Ref*F_Recorte*Disponibilidad*D33` → `prod = e1 × Perfil_Mensual[k]` (E1 del caso; ≡ para el Custom).
- F33/G33/H33 `=E33*1000*Frac_A|B|C`; I33 `=F+G+H`; J33 `=I33/K17`; K33 `=IF(I33>K17,"SÍ","no")`; L33 `=IF(F33>H17,"energía equiv.","directo")`
  con H17 `=D17*Factor_Nivel_2026` → `balanceMensual()`.
- J49:J60 `=F33*Tarifa_A+G33*Tarifa_A+H33*Tarifa_C`; K49 `=J49/I33`; J61 `=SUM`; K61 `=J61/I45`; J45 `=I45/K29`; K45/L45 `COUNTIF(...)&" meses"`.
- D12 `=IF($F$93<=$K$29/1000,"● cumple ("&TEXT(F93/(K29/1000),"0%")&" de la demanda)","■ NO cumple: "&TEXT(F97,"#,##0")&" MWh no reconocidos en el año 1")`.
- D13 `=IF(COUNTIF(K33:K44,"SÍ")=0,"● ninguno: …","▲ "&n&" meses con excedente → crédito kWh (caduca a 24 meses)")`; I13 `=COUNTIF(L33:L44,"energía equiv.")&" meses con inyección A > consumo A: …"`.
- E11 `Potencia_DC*$K$29/1000/$F$93` (potencia máxima teórica bajo el art. 9).
- F93/F94 y filas 93–94 `=Potencia_DC/1000*F_Recorte*yield*Disponibilidad*(1-Degradacion_Adicional)^MAX(0,t-1)` → `energiaAnual(p, frec, Y, t)`.
- Fila 90 `=YEAR(EDATE(Fecha_COD,12*(t-1)))` → `edate(cod, 12*(t−1)).y`; fila 96 (tope) `Consumo_Anual*(1+Crecimiento_Consumo)^(t-1)/1000`;
  fila 97 `E95−E96`; fila 98 `E95*1000/Potencia_DC`; fila 100 `E93/$F$93−1`; fila 101 `Potencia_DC/1000*F_Recorte*yield−E95`.
- J66:J79 `=(1-I66)/(1-Loss_Ref)-1`; J81 (Loss_Act) con `lossAt(CR_Ratio, CR_Loss, ratio del caso)`; J82 = escalar «Factor de recorte».
- D78 `=IF(Potencia_AC>0,Eff_Peaje*$F$93*1000/Potencia_AC/12,0)` → `p.pj × eP50_1 × 1000 / AC / 12`.
- D76/D77 NO reproducidas (faltan D74, D75): valores de `calc_names` con `<Frozen>`.

05_CAPEX: C18, C21, D27/I33:I36 (`IF(N(kfix)>0,"Fijo "&TEXT(kfix,"0.000")&" $/Wp","Bottom-up × "&TEXT(fK,"0.00"))&IF(dK>0," · precios +"&TEXT(dK,"0.0%")&"/año","")&sufijo`;
el sufijo del Favorable incluye `TEXT(D36/D35-1,"+0%;-0%")`), E29, E40, J40 (tres ramas), E41, D54 (`ABS(Σ drivers − 1) ≤ 0,0005`), F54;
D28 como K ÷ (fKeff × fEsc). 06_OPEX: fila 24 `=IF(total>0,total/Potencia_DC,0)`; fila 16 `=YEAR(EDATE(Fecha_COD,12*(t-1)))`.

## Textos de UI escritos por el agente (para revisión)

Energía:
- Título «Energía». Chip «caso {X} · {P50|P90} · disponibilidad {x}».
- Sección «Resumen · año 1 del caso {X}», guía «cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo · la serie
  anual está más abajo». Etiquetas de KPI: «Producción año 1», «Cobertura del consumo (año 1)», «Tarifa evitable efectiva», «Factor de
  recorte vs referencia (ratio {r})», «Potencia AC», «Hectáreas». Comparaciones: «P50 … · P90 … MWh · yield … kWh/kWp»; «consumo anual
  … kWh · potencia máxima teórica bajo el art. 9 con este consumo: … kWp»; «… $/MWh · ponderada por bloques: {E8 vivo}»; «pérdida por
  recorte … (ref. …); curva pvlib más abajo»; «… kWp · ratio DC/AC …»; «densidad … MWp/ha · predio … ha».
- Sección (título de la hoja, fila 15), guía «planillas 2025 y proyección al nivel 2026 (kWh)» (F15 de la hoja). Cabecera «Mes».
- Sección (título de la hoja, fila 64), guía «Σ ene–may 2026 ÷ Σ ene–may 2025». Filas «Factor de nivel 2026 (Σ 2026 / Σ 2025)» (B72),
  «Valor evitado en el año 1 (Σ mensual)», cabeceras «kWh 2025», «kWh 2026». Aviso: «La factura de referencia y la reducción son valores
  del libro (marca ·): la demanda facturable promedio y el FGD de la hoja no son entradas del modelo, así que el motor no las recalcula.
  El valor evitado sí es vivo.»
- Sección «Balance mensual del año 1 · producción {P50|P90} e inyección por bloque», guía «inyección = producción × fracción horaria del
  TMY; cobertura = inyección ÷ consumo proyectado · pase el cursor por un mes» (F31 + añadido). Series «Producción {esc} [MWh]»,
  «Consumo proyectado [MWh]». Cabeceras «Consumo proyectado [kWh]» (las demás son de la hoja).
- Sección «Serie anual — yield canónico × potencia × recorte», guía «t = 1…H del Motor (años 26–30 de la hoja quedan fuera del
  horizonte); demanda anual = Consumo_Anual × (1 + crecimiento)^(t−1)». Series «Energía anual P50», «Energía anual P90», «Energía
  producida del caso ({esc})», «Demanda anual (tope del art. 9)». Línea «Energía no reconocida Σ (producción − demanda): … MWh»,
  «Degradación adicional …/año sobre el yield canónico · disponibilidad …», «Peaje SGDA desde … (COD …)». Cabeceras abreviadas de la
  tabla anual («Producida del caso», «Valorizable (art. 9)», «No reconocida», «Fracción del año con peaje», «Degradación acum. vs año 1
  (P50)», «No producida (indisp. + deg. adicional)»).
- Sección «Curva de recorte por ratio DC/AC (pvlib)» (H64), guía «pérdida por recorte según el ratio; la fila destacada es el ratio del
  caso». refLine «ratio … · pérdida …». Filas «Pérdida a Ratio_Ref (…)» (H80), «Pérdida al ratio del caso (…)» (H81 adaptada),
  «Factor de recorte F» (H82).
- Sección «Tarifa evitable por bloques horarios y cargos», guía «año 1 del caso; los cargos fijos no son evitables con un SGDA remoto».
  Cabeceras «Bloque horario», «Fracción de la inyección», «Tarifa [$/kWh]», «Inyección año 1 [kWh]», «Valor evitado año 1 [USD]»; filas
  «Bloque A · 08–18 h», «Bloque B · 18–22 h (se valora a la tarifa A)», «Bloque C · 22–08 h», «Inyección total · tarifa evitable
  ponderada»; fila «Peaje SGDA del caso (desde …)»; subtítulo «Fracción del año con peaje SGDA vigente» (B99).

CAPEX:
- Título «CAPEX». Chips «Factor del caso × …», «Contrato de Inversión: Sí/No», «IVA recuperable: Sí/No», «Escala_Wp … · Escala_Wac …».
- Sección «CAPEX del caso {X}», guía «cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo · USD nominales sin IVA
  salvo indicación». KPI: «Total CAPEX industrial SALELGI (sin IVA, sin terreno)», «IVA del CAPEX», «Terreno comprado por SALELGI»,
  «Aranceles + ISD dentro del total», «Bottom-up a factor 1 (potencia y contrato de 01)» (C28); comparaciones «… $/Wp · subtotal EPC …
  + gerencia …», «total industrial con IVA … · recuperable (capital de trabajo) | no recuperable: se capitaliza», «comprador: … ·
  total con terreno …», «FODINFA aparte … · con Contrato de Inversión los aranceles e ISD son 0», «obra civil …», «× factor CAPEX
  efectivo … × escalación … = factor del caso …».
- Sección «Rubros del CAPEX», guía «columnas de la hoja; costo del caso = costo base × factor del caso × (drivers × escalas); «(n)» abre
  la nota del rubro al pasar el cursor».
- Sección «Composición del CAPEX industrial por rubro», guía «capitalizable sin IVA del caso; en color las tres partidas mayores, el
  resto en gris».
- Sección «Factores del caso {X}», guía «filas 27–30 de la hoja con los parámetros del caso»; filas «Definición del CAPEX {X}»,
  «Escalación de precios hasta la compra», «Factor CAPEX efectivo» (etiqueta del Motor), «Factor del caso (× cada rubro), incl.
  escalación» (C30).
- Sección (B26 de la hoja), guía «orden fijo Custom · Conservador · Base · Favorable; la fila resaltada es el caso seleccionado»;
  cabeceras «Factor CAPEX efectivo», «Factor de escalación» (las demás son de la hoja).
- Sección (B38), guía = D38 de la hoja. Sección (B43), guía = E43 de la hoja. Control «ok» / «≠ 100 %» (H45).
- Sección (B72), guía «{n} notas del libro · clic para desplegar».

OPEX:
- Título «OPEX de SALELGI» (B1). Chips «caso {X} · factor OPEX × …», «escalación …/año», «terreno: {comprador} → predial|arriendo»,
  «horizonte … años».
- Sección «OPEX del año 1 · caso {X}», guía «cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo · USD nominales
  del año 1 de operación». KPI «{OPEX unitario} (año 1)»; comparaciones «… $/kWp · base sin factor … × …», «… kWp · en t = H: … $/kWp»,
  «… del total · … $/kWp-año × … kWp × …», «SALELGI es dueña del terreno: paga predial y gastos; el arriendo es 0», «Exergy es dueña
  del terreno: SALELGI paga arriendo … $/ha-año × … ha».
- Sección «Composición del año 1» (B5), guía «año 1 del caso {X}; el detalle anual está debajo» (H5 adaptada). Cabeceras «USD/año»,
  «$/kWp», «% del total» (D6:F6 de la hoja).
- Sección «Serie anual» (B14), guía «t = 1…H; cada línea escala …/año desde el año 1 · pase el cursor por un año»; subtítulo «OPEX
  unitario · $/kWp»; cabecera «Año calendario».
- Sección (memo B26), guía «filas 27–28 de la hoja; sólo las etiquetas»; nota «Las cifras del memo no se muestran en esta vista: no
  forman parte del OPEX de SALELGI y pertenecen al flujo de Exergy (hoja 09).»

Tooltips de `Frozen`: «Factura de referencia», «Reducción de la factura». Rastros (`Trace`): nombres y celdas listados en el código.

## Dudas y sugerencias (nada ajeno se tocó)

1. **`Series`/`StackedBars`**: (a) el título del tooltip añade « · t = n» para x > 0 — conviene un prop `tooltipTitle`/`xSuffix` o que
   el sufijo dependa de `xFormat`; hoy uso abscisas negativas para meses y ratios (funciona, pero es un rodeo). (b) El rótulo por
   defecto del eje x usa `String(t)` → «-1» con guion ASCII; en mis gráficos paso `xFormat` con `fmtNum` («−1»); el defecto podría
   hacerlo. (c) `Series` no admite un marcador puntual (el «punto del ratio actual» de la curva de recorte se resolvió con `refLine` +
   fila seleccionada en la tabla).
2. **`KpiTile`**: la tira abrevia el caso con la primera letra → Custom y Conservador comparten «C» cuando el seleccionado es Base o
   Favorable (la muestra de trazo los distingue). Sugerencia: «X» para Custom o dos letras.
3. **book.json / extractor**: (a) `sheets[hoja].labels` toma la columna C (unidad) cuando existe, así que en 04 las filas 7–11, 74, 76 y
   78 tienen etiqueta «×», «$/kWh», «kW», «USD»… y no el texto de B; usé el dump para esos títulos. (b) 04!D74 (demanda facturable
   2.200 kW) y D75 (FGD 0,956) no viajan como datos: si se añaden como entradas (`Demanda_Facturable_kW`, `FGD_Promedio`) la factura
   de referencia y la reducción podrían ser vivas (fórmula D76 lista en el código). (c) Las fórmulas de texto de 04 (D6, I6, E7, E9,
   E10, E11, D12, D13, I13) y 05 (C18, C21, D27, E29, I33:I36, J40, E40, E41, D54, F54) no están como `Live`; las reproduje en TS. Si
   el extractor las emitiera como AST (con soporte de COUNTIF en el evaluador), sobrarían. (d) `capex.notas` trae 16 textos (las 12
   notas + las filas 85–88); filtro por «(n)». (e) `opex.lines` no trae la fila 6 de cabeceras (D6:F6) ni el H5; los transcribí.
4. **Art. 9 en casos P90**: la hoja compara P50 (F93) con la demanda; mantuve ese criterio también para el Conservador (cuya energía
   del caso es P90). Si se prefiere comparar la energía del caso, es un cambio de una línea (`art9` en Energia.tsx).
5. **Horizonte > 25**: el Motor sólo tiene t ≤ 25; las tablas anuales se cortan en min(Horizonte, 25) sin avisar más que en la guía.
6. **`Trace` en cabeceras**: `DataTable` no tiene sitio natural para un rastro por columna; lo puse en el `aside` de cada `Section`.
