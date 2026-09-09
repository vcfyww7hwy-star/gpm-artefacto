# NOTES_C — vistas Fiscal · Flujo · Exergy (agente C)

Archivos creados (sólo estos; ningún archivo ajeno tocado):

- `src/views/Fiscal.tsx` — `export function Fiscal({ caseId, onNavigate })` · hoja 07_Fiscal
- `src/views/Flujo.tsx` — `export function Flujo(...)` · hoja 08_Flujo
- `src/internal/Exergy.tsx` — `export function Exergy(...)` · hoja 09_Exergy · **INTERNA** (sólo importar detrás de
  `process.env.VITE_EDITION !== "externo"`, patrón de `src/lib/edition.ts`)

Las tres reciben `{ caseId: CaseId; onNavigate: (v: ViewId) => void }`; todo se calcula para el caso seleccionado (`m.idx(caseId)`),
con la tira C·B·F en los indicadores. `onNavigate` se acepta por contrato y no se desestructura.

`npx tsc -b`: limpio (0 errores). `npx oxlint` sobre los tres archivos: sin avisos. Sin `console.log`, sin `toFixed`/`Intl`/
`toLocaleString`, sin colores literales, sin dependencias nuevas, sin builds ni publicaciones ni capturas. Scripts temporales de
comprobación (`__check_c.ts`, `__render_c.tsx`, `__text_c.tsx`) borrados.

Integración pendiente (coordinador, `App.tsx`):

```tsx
import { Fiscal } from "@/views/Fiscal";
import { Flujo } from "@/views/Flujo";
import { Exergy } from "@/internal/Exergy";          // único uso: dentro de la rama guardada por la constante de compilación
…
view === "fiscal" ? <Fiscal caseId={caseId} onNavigate={navigate} />
: view === "flujo" ? <Flujo caseId={caseId} onNavigate={navigate} />
: view === "exergy" && process.env.VITE_EDITION !== "externo" ? <Exergy caseId={caseId} onNavigate={navigate} />
: <ViewPlaceholder view={view} />
```

En la edición externa la condición se pliega a `false`, la importación queda sin uso y el empaquetador elimina el módulo (mismo
mecanismo que `INTERNAL_MARKER`; `npm run check:exclusion` debería seguir pasando: el módulo no contiene el marcador, pero conviene
añadir un `grep` de una cadena propia de la vista, p. ej. «Negocio Exergy», al script de exclusión).

## Verificación hecha (además de tsc)

1. **Reconstrucciones ≡ libro (Custom), celda a celda**, con un script temporal `npx tsx` que montó `computeAll(inputs_v31.json)` y
   comparó cada helper con `../data/sheets.json` (tolerancia 1e-6 abs / 1e-9 rel): **11.230 comprobaciones · 0 fallos**.
   - 07_Fiscal: D7, D8, D9 (texto), D10, D13, D14, D15, D16, E16; filas 19, 22–38, 41–42, 45–52 × 27 años (D:AD); Σ depreciación
     por componente (27 + 28 + 29) ≡ bloque Dep.
   - 08_Flujo: filas 44, 47–61, 66–76 × 27 años; D7, E7, D8, E8, D9, D10 (VAN a tasas alternas), D11, **E11** (payback del
     accionista), **D12** (payback descontado), D13, D14, D15, D16, D17, D19, E19, E20, E21, E22, E23, E24, F24 (texto), E25 y los
     nombres `Anio_DSCR_Min`, `Deuda_Max_Plazo1`, `Reduccion_Factura` del resolutor; Σ componentes (47–56 + desmantelamiento) ≡ FCF_u.
   - 09_Exergy: filas 36, 39–52, 69–71 × 27 años; D7, D8 (n/a, ≡ `TIR_Exergy`), D9, D10, D11, D12, D13, D14 (≡ `Carga_Exergy`), D55
     (Ann_Esc), D72, D73 (≡ `VAN_Grupo` de calc_names: 328.477,68); Σ componentes 39–46 ≡ Ux; Ux + Ix + compra + residual ≡ Fx.
   - Coherencia interna en los **111 casos** del Motor: Σ componentes del flujo ≡ FCF_u, Σ depreciaciones ≡ Dep, Σ componentes de
     Exergy ≡ Ux, y el saldo final de la deuda tras la última cuota ≈ 0 en todos los casos con deuda.
   - Textos vivos F8, F20, F22 y F24 de 08: misma redacción que el libro (el libro los renderiza en en-US «12.0%», «351,528»; la
     vista usa es-EC «12,0 %», «351.528»).
2. **Render estático en Node** (`react-dom/server`) de las tres vistas con el `ModelProvider` real: cuatro casos × cuatro juegos de
   entradas (libro; A: sin deuda + IVA no recuperable + utilidad gravable 100.000 + reemplazo Exergy + desmantelamiento 5 % + terreno
   Exergy; B: deuda 100 % a 25 años con 25 de gracia (bullet) + Escudo_Negativo No + Aplica_DedAd No + reemplazo No; C: 8 MWp con
   tarifa 0 → TIR n/a) = 48 renders sin excepciones y sin `NaN`, `undefined`, `Infinity`, `null`, `#NAME?`, `#REF!`, `#VALUE!`,
   `#DIV/0!` en el texto visible. Cifras cotejadas a ojo con el dump para el Custom (07!F22 707.620 · F31 31.361 · F36 −22.530 ·
   F37 8.831 · F38 1,5 % · 08!E20 0,73x · E22 4.472.009 · E24 6.245.618 · 09!D7 113.787 · D10 178.490 · D55 10,6072).

## Qué muestra cada vista

### Fiscal (07_Fiscal)

- Cabecera `ViewHeader` (intro B2) con chips del régimen del caso: participación (tasa y si aplica en el caso), IR, tasa efectiva
  (01!C142), Escudo_Negativo, utilidad gravable (ilimitada o importe), deducción adicional (aplica · % elegible · tope), vidas
  fiscales, IVA recuperable.
- **Cifras fiscales clave** (título = B5): cuatro `KpiTile` con las etiquetas B7, B8, B13 y B14 (CAPEX depreciable con la tira C·B·F;
  deducción adicional anual con el estado de D9 como `Status`; Σ impuestos sin deuda con su descomposición participación + IR; Σ con
  deuda con el escudo fiscal de los intereses Σ) y una `DataTable` que reproduce las filas 7–16 (Indicador · Unidad · Valor · Celda)
  con la cabecera de grupo «Totales del horizonte» (B12). D9 se reconstruye con la regla y redacción exacta de la fórmula
  («◇ n/a — sin deducción adicional (Aplica_DedAd = No)» / «▲ SÍ — tope activo» / «● No — cabe completa»).
- **A · Sin deuda (proyecto puro)** (B21): `StackedBars` de participación (fila 31, `--cat-1`) e IR (fila 36, `--cat-2`) por año, con
  la línea de impuestos con deuda (fila 51, `--cat-3`; sólo si el caso lleva deuda), y `DataTable` size sm con **t en filas** y las
  filas 22–38 como columnas (cabecera abreviada + etiqueta completa en tooltip; EBITDA e impuestos en negrita; años de construcción y
  posteriores al horizonte atenuados). Las columnas que son 0 en todos los años por definición del caso se omiten y el pie lo dice
  (desmantelamiento si Desmantelamiento_Pct = 0; depreciación del reemplazo si no lo paga SALELGI; pool si la utilidad gravable es
  ilimitada).
- **B · IVA del CAPEX** (B40): tabla de t = −1, 0, 1 con IVA pagado / recuperado (41–42) y nota con la mecánica (fase, período
  siguiente, Σ recuperado o «se suma al CAPEX depreciable»).
- **C · Con deuda** (B44): `Series` con barras del escudo fiscal de los intereses (fila 52) y línea de intereses (fila 45) y
  `DataTable` con las filas 45–52. Si el caso no lleva deuda, nota en su lugar. Nota del pool de pérdidas: con `ug ≥ 0` explica la
  absorción limitada y el arrastre (≤ 25 %/año, art. 11 LRTI); con `ug < 0` (celda vacía) dice que la utilidad gravable es
  ilimitada, que el pool no aplica y cómo actúa Escudo_Negativo (Sí: escudo en el año; No: MAX(0, ·)).

### Flujo (08_Flujo)

- Cabecera (intro B2) con chips: caso, fases del CAPEX (Fase_m1) y meses de construcción, tasas de descuento (proyecto / accionista),
  deuda del caso (o «sin deuda»), horizonte y año del COD.
- **Indicadores** (título = B5 con el nombre del caso en lugar de «Custom»): cuatro `KpiTile` no redundantes con Resumen — payback
  simple (con el descontado y el del accionista), LCOE frente a la tarifa evitable y ahorro por kWh, ahorro año 1 (con Σ nominal y
  reducción de la factura, marcada `<Frozen>` porque el denominador es la factura de referencia del libro), aporte de capital (con y
  sin deuda) — y la `DataTable` que **reproduce las filas 7–25** con las cabeceras oficiales de la fila 6 (Indicador · Unidad · Sin
  deuda · Con deuda · Lectura) más «Nombre / celda». La columna Lectura lleva los textos F verbatim; F8, F20 (con `Status`), F22 y
  F24 se recomponen con la misma redacción de la fórmula. Debajo, la nota B26.
- **Cinta anual**: `CintaAnual` del caso (FCF_u, Cum_u, payback, año calendario).
- **A · Proyecto sin deuda** (B46): `DataTable` size sm con t en filas y las filas 47–61 como columnas (CAPEX por fase, terreno, IVA
  pagado/recuperado, ahorro, OPEX, peaje, impuestos, reemplazo, residual, FCF, acumulado, factor de descuento, FCF descontado,
  acumulado descontado). Columnas 0 por definición del caso omitidas con aviso en el pie.
- **B · Con deuda** (B63): cuatro cifras (deuda desembolsada B64, IDC F64, deuda total al COD B65, cuota F65) y `DataTable` con las
  filas 66–76 (desembolso, saldo inicial, intereses, amortización, servicio, saldo final, IDC memo, CFADS, DSCR coloreado bajo 1,00x y
  bajo el objetivo, flujo del accionista, acumulado equity). Dos `Series`: DSCR en barras con `refLine` = DSCR_Objetivo (B78) y el
  texto F20; flujo del accionista en barras + acumulado equity en línea con el color/trazo del caso. Sin deuda → nota.
- **Deuda máxima por plazo (10 §H)**: mini-tabla Sens_Plazos × `Deuda_Max_Plazo1..3` (`m.nameValue`, calculados por el resolutor a
  partir de los casos 78–92 del Motor, que parten del Custom) con la deuda en USD sobre la base del Custom; fila del plazo actual
  resaltada cuando el caso es el Custom; nota con la deuda del caso y remisión a Sensibilidad §D y §H.

### Exergy (09_Exergy) — interna

- Cabecera (intro B2) con chips: «edición interna», caso, fee y costo interno de gerencia, fee y costo propio de O&M, terreno (Exergy
  compra con arriendo y predial / SALELGI compra), pagador del reemplazo, Tasa_Efectiva_Exergy.
- **Indicadores del negocio Exergy** (B5): cuatro `KpiTile` (VAN Exergy, TIR Exergy —«n/a» como texto—, ingreso neto nominal Σ,
  carga para SALELGI) con las definiciones de la columna E como texto de comparación y tira C·B·F; `DataTable` con las filas 10–13
  (VAN por línea gerencia / terreno / O&M, rendimiento bruto del arriendo) y, bajo la cabecera de grupo B54, el factor de anualidad
  escalado Ann_Esc (fila 55). Debajo, la nota B15.
- **Flujo de caja de Exergy** (B38): `StackedBars` con las líneas de negocio agrupadas como en las definiciones de la hoja (gerencia:
  fee − costo interno `--cat-1`; O&M: fee − costo propio `--cat-2`; terreno: compra + arriendo − predial + residual `--cat-3`, sólo si
  Exergy compra; impuestos y reemplazo en grises ordinales) y la línea del flujo (fila 50); `DataTable` con las filas 39–52.
- **Memo — vista consolidada del grupo** (B68): TIR del grupo (B72) y VAN del grupo (B73, = VAN proyecto + VAN Exergy) con tira
  C·B·F, `Series` con FCF Exergy (barras) frente a FCF SALELGI sin deuda y FCF grupo (líneas), y la lectura B74 verbatim.

## Filas reconstruidas (helpers locales) y su celda

Todas en el propio archivo de la vista, con la fórmula del libro anotada en el código y la celda en `<Trace>` / tooltip de cabecera:

| Vista | Fila / celda | Reconstrucción |
|---|---|---|
| Fiscal | 07!D9 | regla y textos exactos de la fórmula (`p.dedad`, `Kdep·Pct_Elegible/Vida > Tope·Ingresos`) |
| Fiscal | 07!D10 | `Kdep·Pct_Elegible/Vida/Tope` («—» si Tope = 0) |
| Fiscal | 07!D13 · D14 · D15 · D16:E16 | Σ (Part_u + IR_u) · Σ (Part_l + IR_l) · Σ fila 33 × Tasa_IR · Σ IVA pagado / recuperado |
| Fiscal | 07!25 | `t = H ? Decom : 0` |
| Fiscal | 07!27 · 28 · 29 | DepEq en 1…VFE · DepCiv en 1…min(VFC, H) · Krep/min(VFE, H−RA) en RA+1…min(H, RA+VFE) si rep = 1 (≡ bloque Dep) |
| Fiscal | 07!30 · 32 · 33 · 34 · 37 · 38 | EBITDA − Dep · − Part_u · DedAd en 1…VFE · − DedAd · Part_u + IR_u · impuestos/EBITDA |
| Fiscal | 07!41 · 42 | IVA·Fase_m1 (t = −1), IVA·(1−Fase_m1) (t = 0) · recuperado en t = 0 / 1 si `iva = 1` |
| Fiscal | 07!46 · 48 · 51 · 52 | EBITDA − Dep − Int · − Part_l − DedAd · Part_l + IR_l · (37) − (51) |
| Flujo | 08!47 · 48 · 49 · 50 · 52 · 53 · 54 · 55 · 56 | −K por fase · Terr[t=−1] · −IVA pagado · IVA recuperado · −OPEX · −Peaje · −(Part_u + IR_u) · bloque Krep · Terr[t=H] |
| Flujo | 07!25 en 08 | columna «Desmantelamiento…» (negativa) sólo si Decom > 0, para que Σ columnas ≡ FCF_u (ver duda 1) |
| Flujo | 08!59 · 60 · 61 · D12 | `1/(1+r)^t` para todo t · FCF×DF · acumulado · `paybackLastCrossing` sobre 61/60 |
| Flujo | 08!D9 · D10 | `vanMotor(Tasa_Desc_Alt1/2, FCF_u)` con `m.extras` |
| Flujo | 08!D14 · D15 · D17 · D18 · D19 | Tarifa_Evitable×1000 · 1 − LCOE/tarifa · Σ Ahorro · Ahorro1 / Factura_Referencia (frozen) · −(FCF₋₁ + FCF₀) |
| Flujo | 08!66 · 67 · 70 · 71 · 72 · 76 · E11 · E24 · F24 · E25 | D por fase · saldo final anterior · Int + Amort · saldo + desembolso + IDC(t=0) − Amort · IDC(t=0) · Σ EQ · `paybackLastCrossing(ΣEQ, EQ)` · Σ servicio · Σ Int · t del DSCR mínimo (t ≥ 1) |
| Flujo | 08!F8 · F20 · F22 · F24 | textos vivos recompuestos con la redacción de la fórmula (formato es-EC) |
| Exergy | 09!39 · 40 · 41 · 42 · 43 · 44 · 45 · 46 · 49 · 51 · 52 | Fee_Gerencia_Pct·Sub por fase · −Costo_Gerencia_Pct·Sub por fase · Tx[t=−1] · `opexLines(…, withFactor=false)`: arriendo, −predial_exergy, fee, −om_exergy · −Krep en RA si rep = 2 · Tx[t=H] · Σ Fx · `1/(1+r)^t` |
| Exergy | 09!D8 · D10 · D11 · D12 · D13 · D14 · D55 · D73 | `irr(Fx)` · SUMPRODUCT por línea con la fila 52 · Renta/Precio · (fee + arriendo)/Ahorro1 · Σ (1+esc)^(t−1)·DF · `vanMotor(r, Gx)` |

## Decisiones

1. **Etiquetas oficiales transcritas.** `book.sheets[hoja].labels[fila]` guarda la última celda de texto de la fila (la unidad de la
   columna C cuando existe), así que las etiquetas de la columna B de 07/08/09 se transcribieron verbatim del dump a un mapa `L`
   en cada vista (y los textos de las columnas E/F de 08/09 a `LECTURA` / `DEF`). Sugerencia para el extractor: conservar también la
   columna B (`labels_b`) para que las vistas la lean de `book.json`.
2. **Tablas anuales con t en filas** (27 filas) y las filas de la hoja como columnas, `DataTable size="sm"` con desplazamiento
   horizontal propio. La cabecera usa la etiqueta oficial **abreviada hasta el primer paréntesis / dos puntos / raya** (p. ej.
   «Peaje SGDA», «Participación laboral 15 %»); la etiqueta completa y la celda van en el tooltip de la cabecera (`title`). Es un
   recorte, no una paráfrasis; si el revisor prefiere la etiqueta completa, basta quitar `short()` en las tres vistas.
3. **Columnas nulas por definición del caso se omiten** (desmantelamiento con Desmantelamiento_Pct = 0, reemplazo según el pagador,
   terreno según el comprador, pool con utilidad gravable ilimitada) y el pie de la tabla lo declara. Así la tabla no cambia de
   ancho sin motivo y Σ columnas ≡ bloque del Motor sigue siendo cierto en todos los casos.
4. **Desmantelamiento en Flujo.** 08_Flujo no tiene fila de desmantelamiento (el Motor lo resta dentro del EBITDA, como 07!26); con
   Desmantelamiento_Pct = 0 (libro) no se nota, pero si el usuario lo cambia en Mandos la suma de las filas 47–56 dejaría de cuadrar
   con FCF_u. Se añade la columna «Desmantelamiento en t = Horizonte (gasto deducible)» (07!25, en negativo) sólo cuando Decom > 0,
   con rastro a 07_Fiscal.
5. **Indicadores de Flujo**: además de cuatro tiles no redundantes con Resumen, la tabla reproduce las filas 7–25 completas con sus
   cabeceras de la fila 6 y la columna Lectura; el título B5 sustituye «Custom» por el nombre del caso seleccionado.
6. **VAN del grupo** (09!D73) no es salida del Motor: se calcula `vanMotor(Tasa_Descuento, Gx)` (coincide con `VAN_Grupo` de
   calc_names, 328.477,68). **TIR Exergy** se calcula con `irr(Fx)` del motor para todos los casos (igual que `TIR_Exergy` del
   resolutor; en el libro es «n/a» porque Fx no cambia de signo) y se muestra «n/a» como texto.
7. **Carga para SALELGI** (09!D14) para casos ≠ Custom: (fee O&M + arriendo del caso, con el factor OPEX del caso, como costo de
   SALELGI) / Ahorro año 1 del caso — misma convención que `Carga_Exergy` en `names.ts`; para el Custom coincide con la celda.
   En cambio, las filas 42/44 del flujo de Exergy se toman **sin** el factor OPEX (como el bloque Ux del Motor).
8. **Reducción de la factura** (08!D18): Ahorro año 1 del caso / Factura_Referencia (valor del libro: depende de la demanda facturable
   y el FGD, que no están en el Motor) → marcada con `<Frozen what="Factura de referencia (denominador)">`; para el Custom es
   exactamente `Reduccion_Factura`.
9. **Gráficos con un solo eje**: la tasa efectiva (%) queda sólo en la tabla; el gráfico A de Fiscal superpone «impuestos con deuda»
   (USD) a las barras de participación + IR; el DSCR (x) y el flujo del accionista (USD) van en dos gráficos separados.
10. **Sensibilidad de Exergy (09 filas 58–66) no reproducida**: los pasos de las palancas (5/7/9 %, 3.000/5.000/7.000 $/ha, 18/20/24
    $/kWp) son constantes de la hoja que no existen en `Inputs` ni en `book.json`; reproducirlas exigiría literales. Sí se muestra
    Ann_Esc (fila 55). Si se quiere, añadir `book.exergy.palancas` (C58:C66 + etiquetas) y la vista puede calcular D58:F66 con las
    fórmulas del dump (ya anotadas en el análisis).

## Textos de UI escritos por el agente (para revisión)

Todo lo demás (títulos de sección A/B/C, etiquetas de fila, Lectura, Definición, nota B26, B15, B74, intro) es texto del libro.

**Fiscal**
- Título de la vista: «Fiscal».
- Chips: «caso {nombre}» · «Participación laboral {x %}: Sí/No» · «IR {x %}» · «Tasa efectiva {x %}» · «Escudo_Negativo {Sí/No}» ·
  «Utilidad gravable: ilimitada / {$}» · «Deducción adicional: Sí/No · {x %} elegible · tope {x %} de {$}» · «Vida fiscal 10 / 20
  años» · «IVA recuperable: Sí/No».
- Guías: «caso {nombre} · cifra grande = caso seleccionado; debajo, los otros tres casos» · «barras = participación e IR del año sin
  deuda (filas 31 y 36); línea = impuestos con deuda (fila 51) · pase el cursor por un año» · «sólo los años con movimiento (t = −1,
  0 y 1); el resto de la fila es 0» · «deuda del caso: {lev} al {rd} · {plazo} años ({gracia} de gracia) · barras = escudo fiscal de
  los intereses (fila 52), línea = intereses (fila 45)» / «este caso no lleva deuda».
- Cabeceras de tabla: «Indicador», «Unidad», «Valor», «Celda», «Año calendario».
- Comparaciones de los tiles: «CAPEX industrial {$} · IVA {$} · IVA recuperable: Sí/No» · «participación Σ {$} + IR Σ {$}» ·
  «Escudo fiscal de los intereses Σ {$}».
- Caption A: «Filas 22–38 de la hoja para el caso {nombre}, un año por fila (USD; la tasa efectiva en %). La cabecera abreviada lleva
  la etiqueta completa de la hoja en el tooltip.» · Caption C: «Filas 45–52 de la hoja para el caso {nombre} (USD). Los intereses son
  los del cuadro de la deuda de 08_Flujo (fila 68).»
- Pies: «La columna «…» se omite porque Desmantelamiento_Pct = 0 en este caso.» · «La columna «…» se omite porque el reemplazo de
  inversores no lo paga SALELGI en este caso.» · «Las columnas del pool de pérdidas (filas 35 y 49) se omiten: ver la nota al pie de
  la sección C.»
- Nota IVA: «IVA del CAPEX del caso {$}: {30 %} pagado en t = −1 y {70 %} en t = 0. Recuperable (IVA_Recuperable = Sí): cada tramo
  vuelve en el período siguiente (t = 0 y t = 1); Σ recuperado {$}.» / «No recuperable (IVA_Recuperable = No): no vuelve y se suma al
  CAPEX depreciable (fila 7).»
- Nota sin deuda: «Este caso no lleva deuda (Deuda = 0): las filas 45–52 coinciden con las de la sección A y el escudo fiscal de los
  intereses es 0.»
- Notas del pool: «Utilidad gravable de SALELGI limitada a {$} por año (Utilidad_Gravable_SALELGI): las pérdidas incrementales se
  absorben hasta ese importe y el resto entra en el pool de arrastre (filas 35 y 49), que se compensa cada año hasta el 25 % de la
  utilidad gravable del año (base incremental + Utilidad_Gravable_SALELGI), art. 11 LRTI.» / «Utilidad_Gravable_SALELGI está vacía:
  la utilidad gravable es ilimitada y el pool de arrastre (filas 35 y 49) no aplica. Con Escudo_Negativo = Sí, las pérdidas
  incrementales se absorben sin límite: participación e IR negativos actúan como escudo en el año.» / «Con Escudo_Negativo = No, la
  participación y el IR negativos se truncan a 0 (MAX(0, ·)).»
- aria-label de gráficos: «Impuestos incrementales por año: participación e IR sin deuda, e impuestos con deuda» · «Escudo fiscal de
  los intereses e intereses de la deuda por año».

**Flujo**
- Título de la vista: «Flujo de caja de SALELGI» (B1 sin el prefijo «8 · »).
- Chips: «caso {nombre}» · «t = −1: {30 %} del CAPEX · t = 0: {70 %} · {n} meses de construcción» · «descuento {x %} · accionista
  {x %}» · «deuda {lev} al {rd} · {plazo} años · {gracia} de gracia» / «sin deuda» · «horizonte {H} años · COD {año}».
- Título de sección: B5 con el nombre del caso; «Cinta anual · flujo libre sin deuda y acumulado» (igual que en Resumen); «Deuda
  máxima por plazo (10 §H)».
- Guías: «cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo · la tabla reproduce las filas 7–25 de la hoja»
  · «barras = flujo del año (construcción en gris oscuro), línea = acumulado, punto = payback · pase el cursor por un año» · «filas
  47–61 de la hoja, un año por fila (USD); las columnas que en este caso son 0 en todos los años se omiten» · «filas 64–76 de la hoja,
  un año por fila (USD; DSCR en x)» · «apalancamiento con DSCR mínimo ≥ {obj} para cada plazo de Sens_Plazos, interpolado entre los
  puntos de Sweep_Lev; los casos del Motor parten del Custom».
- Cabeceras de tabla añadidas: «Nombre / celda», «Año calendario», «Plazo», «Apalancamiento máximo (DSCR mín ≥ {obj})», «Deuda (USD,
  Custom)», «Nombre»; grupos «Sin deuda vs con deuda», «Deuda».
- Lectura escrita por el agente (filas sin texto F en el libro): «@ {8,0 %} (Tasa_Desc_Alt1)» · «@ {12,0 %} (Tasa_Desc_Alt2)» ·
  «@ {10,0 %} (Tasa_Descuento), sobre las filas 60–61».
- Comparaciones de tiles: «Payback descontado @ {10 %}: {x} · del accionista: {x}» · «{B14} {x} $/MWh · {B15} {x %}» · «{B17} {$} ·
  {B18} {x %}» · «sin deuda {$} · {F19}».
- Caption A: «La cabecera abreviada lleva la etiqueta completa de la hoja en el tooltip. El flujo de caja libre es el bloque FCF_u del
  Motor; la suma de las columnas anteriores coincide con él en todos los años.» · Pies A: «“{B48}” y “{B56}” se omiten: en este caso
  el terreno no lo compra SALELGI.» · «“{B55}” se omite: el reemplazo de inversores no lo paga SALELGI en este caso.» · «La columna
  “Desmantelamiento…” viene de 07_Fiscal (fila 25): el Motor la resta dentro del EBITDA y 08_Flujo no la desglosa.»
- Caption B: «Deuda del caso: {lev} de {$} (CAPEX industrial / CAPEX + terreno) al {rd}, {plazo} años con {gracia} de gracia; {n}
  cuotas.» · Títulos de gráfico: «{B74} frente al objetivo · {B78}» · «{B75} y acumulado equity» · pie: «payback del accionista: {x}
  · {B19}: {$}» · refLine: «DSCR objetivo {x}».
- Nota sin deuda: «Este caso no lleva deuda (Deuda = 0): las filas 64–76 son 0, el flujo del accionista coincide con el flujo libre
  del proyecto y no hay DSCR.» · Nota deuda máxima: «El caso {nombre} lleva {lev} a {plazo} años con DSCR mínimo {x} en t = {t}. /
  El caso {nombre} no lleva deuda. La matriz tasa × plazo y el detalle del barrido de apalancamiento están en Sensibilidad §D y §H.»
- aria-label: «DSCR por año frente al DSCR objetivo» · «Flujo del accionista por año y acumulado».

**Exergy**
- Título de la vista: «Negocio Exergy» (B1 sin «9 · »).
- Chips: «edición interna» · «caso {nombre}» · «gerencia: fee {x %} · costo interno {x %}» · «O&M: fee {x} · costo propio {x}
  $/kWp-año» · «terreno: Exergy compra · arriendo {$}/ha-año · predial {$}/año» / «terreno: SALELGI compra (sin línea terreno)» ·
  «reemplazo de inversores: Exergy / SALELGI / No» · «Tasa_Efectiva_Exergy {x %}».
- Guías: «caso {nombre} · cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo» · «barras = componentes del
  flujo por línea de negocio (filas 39–49 agrupadas como en las definiciones de la hoja); línea = flujo de caja de Exergy (fila 50) ·
  pase el cursor por un año»; el título del memo es B68 hasta los dos puntos y la guía, el resto de B68.
- Cabeceras añadidas: «Celda», «Año calendario». Leyendas del apilado: «Gerencia: fee − costo interno» · «O&M: fee − costo propio» ·
  «Terreno: compra + arriendo − predial + residual» (a partir de las definiciones E10–E12).
- Comparaciones de tiles: «Σ de la fila 50, t = −1…25, sin descontar» · «{E14} Ahorro año 1 {$}.» · «TIR del proyecto sin deuda
  (TIR_Proyecto): {x}» · «VAN proyecto {$} + VAN Exergy {$}».
- Caption: «Filas 39–52 de la hoja para el caso {nombre}, un año por fila (USD). La cabecera abreviada lleva la etiqueta completa en
  el tooltip; la utilidad operativa y el flujo son los bloques Ux y Fx del Motor y la suma de las columnas coincide con ellos en todos
  los años.» · Pies: «Las líneas del terreno (filas 41, 42, 43 y 49) se omiten: en este caso el terreno lo compra SALELGI y son 0.» ·
  «“{B46 abreviada}” se omite: en este caso el reemplazo no lo paga Exergy.» · «El fee de O&M y el arriendo se toman sin el factor OPEX
  del caso, como en el bloque Ux del Motor (filas 18 y 20 de 06_OPEX).»
- aria-label: «Flujo de caja de Exergy por año y por línea de negocio» · «Flujo del grupo frente al flujo de SALELGI sin deuda y al de
  Exergy».

## Dudas / para el coordinador

1. ¿Está bien añadir en Flujo la columna de desmantelamiento tomada de 07!25 cuando Decom > 0 (decisión 4), o se prefiere ocultarla
   siempre y aceptar que Σ columnas ≠ FCF_u en ese caso?
2. ¿Aceptable el recorte de cabeceras (`short()`, decisión 2)? Alternativa: etiquetas completas en la cabecera (se vuelven altas) o
   transponer (filas de la hoja × 27 años), que requeriría una primera columna pegajosa en `DataTable`.
3. `KpiTile`: las etiquetas oficiales largas (p. ej. B8 de 07, 70 caracteres) ocupan dos o tres líneas en versalitas. Si molesta, la
   alternativa es una etiqueta corta con la oficial en el `title` (el componente ya usa `title={excelName}`).
4. La etiqueta B8 de 07 dice «años 1–10» y B27/B28 «10 años» / «20 años» en el texto: si se cambian las vidas fiscales en Supuestos,
   la etiqueta oficial no cambia (igual que en el libro).
5. Cambios sugeridos en componentes compartidos (no hechos): (a) `DataTable`: opción `stickyFirst` (primera columna pegajosa) para
   tablas anuales anchas; (b) extractor de `book.json`: conservar la columna B de cada fila en `sheets[hoja].labels_b` y añadir las
   palancas de 09 (C58:C66) para poder reproducir la sensibilidad del negocio Exergy sin literales.
6. `check-exclusion.mjs` comprueba sólo `INTERNO_MARKER_9F2A`; conviene añadir una cadena propia de `Exergy.tsx` (p. ej. «Negocio
   Exergy» o «edición interna») para verificar que la vista no llega al bundle externo.
