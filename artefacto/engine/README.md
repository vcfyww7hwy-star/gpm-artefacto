# Motor_Sens engine (TypeScript) — Modelo FV 5 MWp GPM v3.1

Pure, deterministic TypeScript transliteration of the `Motor_Sens` sheet of
`Modelo_FV_5MWp_GPM_v3.1.xlsx` (5 MWp solar plant, Ecuador: SALELGI owner / Exergy operator).
Zero runtime dependencies. Reproduces the LibreOffice-recalculated workbook to floating-point noise:
**91 546 cells compared, 0 outside tolerance** (max rel Δ 2.8e-12, see *Verification*).

```
src/engine.ts           Inputs · Derived · CaseParams · computeDerived() · computeCase() · finance helpers
src/caseDefinitions.ts  buildCases(): the 111 Motor columns (names, order and parameter formulas of build_content.build_cases)
src/inputs.ts           inputsFromWorkbookJson(names, sheets): Inputs from ../data/names.json + ../data/sheets.json
src/index.ts            re-exports + computeAll(inputs) → { derived, cases[111] }
data/inputs_v31.json    the v3.1 defaults (written by test/verify.ts)
test/verify.ts          oracle verification against ../data/motor.json (writes verify_report.json)
test/crosscheck_shadow.py + test/crosscheck.ts   randomized cross-check against shadow30.run_case (Python)
```

## Run

```bash
npm install                 # dev deps only: typescript, tsx, @types/node
npm run typecheck           # tsc --strict, noEmit
npm run verify              # npx tsx test/verify.ts  → summary + verify_report.json (exit 0 = PASS)
npm run crosscheck          # 400 random parameter sets vs shadow30.run_case (needs python3 + numpy)
```

Programmatic use:

```ts
import { computeAll, inputsFromWorkbookJson } from "./src";
const inputs = JSON.parse(fs.readFileSync("data/inputs_v31.json", "utf8"));   // or inputsFromWorkbookJson(names, sheets)
const { derived, cases } = computeAll(inputs);        // 111 cases, ≈ 30 ms total
cases[1].result.outputs["TIR equity"];                // Conservador → 0.010754…
cases[0].result.blocks.FCF_u;                         // 27 values, t = −1 … 25
```

`computeCase(inputs, derived, params)` returns `{ scalars, outputs, blocks }` keyed by the **exact Motor
row labels** (`SCALAR_LABELS`, `OUTPUT_LABELS`, `BLOCK_NAMES`). Outputs are `number | "n/a" | "no cruza"`;
blocks are 27-element arrays (only `DSCR` contains `null`, Excel's `""` when there is no debt service).

## Inputs — mapping Excel defined name → `Inputs` field

Field names **are** the Excel defined names (01_Supuestos unless noted). Dates are ISO strings.

| Section | Excel name(s) | `Inputs` field | Notes |
|---|---|---|---|
| A | Potencia_DC, Ratio_DCAC, Comprador_Terreno, Usar_Deuda, Tasa_Descuento, Tasa_Descuento_Equity, Horizonte, Fecha_COD | same | `Usar_Deuda` is **not** used by the Motor (portada only; Custom has Deuda(1/0) = 1 hard-wired) |
| A | Meses_Construccion (= Mes_COD_Cron = MAX('03_Tramites'!H8:H24)) | `Meses_Construccion` | taken as a primitive (21); the 03 schedule is not modelled |
| B | Esc_Energia, Esc_Factor_CAPEX, Esc_CAPEX_Fijo_Wp, Esc_Factor_OPEX, Esc_Peaje, Esc_EscTarifa, Esc_Disponibilidad, Esc_Escalacion_CAPEX (01!C:F rows 38–45) | same, arrays of 4 = Custom · Conservador · Base · Favorable | the Custom scalars Escenario_Energia, Factor_CAPEX, CAPEX_Fijo_Wp (null = blank), Factor_OPEX, Peaje_SGDA, Escalacion_Tarifa, Disponibilidad, Escalacion_CAPEX are element `[0]` (exposed in `Derived`) |
| C | Potencia_Ref, Ratio_Ref, Densidad_MWp_ha, Degradacion_Adicional, Frac_A/B/C, Tarifa_A, Tarifa_C, Crecimiento_Consumo, Fecha_Peaje, Peaje_kW_mes | same | |
| C (04) | Y_P50, Y_P90 (04!F91:AI91/92, 30 yrs), CR_Ratio, CR_Loss (04!H66:I79), Perfil_Mensual (04!D33:D44) | same | constants in the sheet |
| C (04) | 04!D17:F28 (2025 consumption A/B/C), 04!D66:D70, 04!E66:E70 | `Consumo_2025_A/B/C`, `Consumo_2025_EneMay`, `Consumo_2026_EneMay` | feed Factor_Nivel_2026 and Consumo_Anual |
| D | Fase_m1, Fecha_Precios, Contingencia_Pct, Contingencia_Frac_IVA, Fee_Gerencia_Pct, Asignacion_Compartida, Exponente_Escala, Contrato_Inversion, IVA_Recuperable, Tasa_IVA, FODINFA_Pct, ISD_Pct, Reemplazo_Anio, Reemplazo_USD_Wac, Reemplazo_Pagador, Desmantelamiento_Pct, Precio_Terreno_ha, Costos_Transaccion_Terreno_Pct, Predial_Terreno, Residual_Terreno_Pct, Apreciacion_Terreno | same | |
| D (05) | 05_CAPEX rows 7–15: C nombre, D costo, E %comp, G %ext, I arancel, O IVA + Drv_Wp/Drv_Wac/Drv_Fijo | `rubros[9]` (`Rubro`) | |
| D (05) | 05_CAPEX!O18 (IVA % of the fee row) | `iva_fee` | |
| E | Fee_OM_kWp, Seguro_kWp, Renta_Terreno_ha, Tributos_Locales, Escalacion_OPEX | same | |
| F | Pct_Apalancamiento, Tasa_Deuda, Plazo_Deuda, Gracia_Deuda, IDC_Frac_Tramo0, DSCR_Objetivo, Deuda_Financia_Terreno | same | DSCR_Objetivo only for 10_Sensibilidad (Deuda_Max), not the Motor |
| G | Tasa_IR, Tasa_Participacion, Incluir_Participacion, Escudo_Negativo, Utilidad_Gravable_SALELGI (number \| null), Vida_Fiscal_Equipos, Vida_Fiscal_Civil, Aplica_DedAd, Pct_Elegible_DedAd, Ingresos_SALELGI, Tope_DedAd_Pct | same | |
| H | Costo_Gerencia_Pct, Costo_OM_Exergy_kWp, Tasa_Efectiva_Exergy | same | |
| 10 | Sens_CAPEX, Sens_Tarifa, Sens_OPEX_Up, Sens_OPEX_Dn, Sens_Peaje, Sens_EscTarifa, Sens_Disponibilidad, Sens_EscCAPEX, Sens_Peaje_kW, Sweep_AC_Fija, Mat_CAPEX[5], Mat_Tarifa[5], Sens_Tasas[5], Sens_Plazos[3], Sens_Lev[4], Sweep_P[4], Sweep_Ratio[5], Sweep_Lev[5] | same | only used by `buildCases` |

Sí/No toggles are the literal strings `"Sí"` / `"No"`; `Comprador_Terreno` ∈ {SALELGI, Exergy}; `Reemplazo_Pagador` ∈ {SALELGI, Exergy, No}.

### `computeDerived(inputs)` — the defined names the Motor references

Consumo_Anual (04!K29 with Factor_Nivel_2026 = Σ2026 ene–may / Σ2025 ene–may), Tarifa_Evitable (04!K61 = J61/I45 from the
monthly balance of year 1), Loss_Ref / Loss_Act / F_Recorte (clipping curve, INDEX/MATCH linear interpolation with clamping),
Anios_Precios = (Fecha_COD − Fecha_Precios)/365.25, Frac_Peaje[27] (04!D99:AD99), Tasa_Efectiva, Escala_Wp/Wac, Potencia_AC,
Hectareas, Yield_Ref, Eff_Scen/Eff_fO/Eff_Peaje/Eff_EscT, the 05_CAPEX split at factor 1 (CAPEX_SC/CC_Wp/Wac/Fijo, IVA_SC/CC_*,
CAPEX_SC_f1 …), CAPEX_Base_f1 (05!D28), Factor_Escalacion (05!D29), Factor_Caso (05!D30), Pct_CAPEX_Civil (05!N24 = N12/N19,
computed with the Custom's Factor_Caso and scale, as the sheet does), Reemplazo_USD, Desmantelamiento_USD.
All are verified against `names.json` (section (a) of `verify.ts`).

## Motor labels

**Parameters (rows 5–34, `PARAM_LABELS`, short key → label):** fK "Factor CAPEX (× bottom-up)" · fT "Factor tarifa" · scen
"Escenario energía (1=P50, 2=P90)" · fO "Factor OPEX" · pj "Peaje $/kWh" · escT "Escalación tarifa" · part "Participación (1/0)" ·
iva "IVA recuperable (1/0)" · cont "Contrato inversión (1/0)" · deb "Deuda (1/0)" · rd "Tasa deuda" · lev "Apalancamiento" · plazo
"Plazo" · gr "Gracia" · P "Potencia DC (kWp)" · ratio "Ratio DC/AC" · terr "Terreno lo compra SALELGI (1/0)" · finT "Banco financia
terreno (1/0)" · fPre "Factor precio terreno" · kfix "CAPEX fijo $/Wp (0 = bottom-up × factor)" · disp "Disponibilidad" · dK
"Escalación CAPEX (%/año hasta la compra)" · pkw "Peaje por potencia $/kW-mes" · rep "Reemplazo inversores (0 No · 1 SALELGI · 2
Exergy)" · ug "Utilidad gravable SALELGI (−1 = ilimitada)" · ncon "Meses de construcción" · req "Tasa descuento accionista" · dec
"Desmantelamiento (% CAPEX en t=H)" · deg "Degradación adicional (%/año)" · dedad "Deducción adicional aplicable (1/0)".

**Scalars (rows 35–56):** Factor de recorte · Potencia AC (kW) · Hectáreas · CAPEX industrial sin IVA · IVA CAPEX · CAPEX
depreciable · Dep. equipos/año · Dep. civil/año · Deducción adicional/año · Terreno (costo total quien compra) · Residual terreno
neto (t=H) · OPEX año 1 SALELGI · Subtotal EPC (base fee) · Deuda · IDC · Deuda total COD · Nº cuotas · Cuota · Factor CAPEX
efectivo · Factor de escalación del CAPEX · Reemplazo de inversores (USD) · Desmantelamiento (USD).

**Outputs (rows 57–72):** TIR proyecto · VAN proyecto · Payback simple · LCOE $/MWh · TIR equity · VAN equity · DSCR mín · DSCR
prom · Ahorro año 1 · Aporte equity · VAN Exergy · TIR grupo · Energía año 1 (MWh) · Energía no reconocida Σ (MWh) · Cobertura
año 1 · Nominal Exergy Σ.

**Blocks (28 × 27 years, t = −1 … 25):** E, Eval, Ahorro, OPEX, Peaje, EBITDA, Dep, Part_u, IR_u, Terr, FCF_u, Cum_u, Int, Amort,
Part_l, IR_l, CFADS, EQ, DSCR, DF, Ux, Ix, Tx, Fx, Gx, Krep, PoolU, PoolL.

**Cases (111, `buildCases`):** Custom · Conservador · Base · Favorable · Custom P50 · Custom P90 · CAPEX − · CAPEX + · Tarifa − ·
Tarifa + · Energía alt. · OPEX + · OPEX − · Peaje · Esc. tarifa · Participación alt. · IVA alt. · Contrato alt. · PISO · M11…M55 ·
E11…E53 · L1…L4 · Terreno alt. · P1…P4 · R1…R5 · A1…A5 · DM11…DM35 · TS1…TS3 · TX1…TX3 · Disponibilidad − · Escalación CAPEX + ·
Peaje kW · Sin absorción fiscal · Reemplazo alt. · Sin deducción adicional · BR0 v2.0 · BR1 + escalación · BR2 + disponibilidad ·
BR3 + reemplazo · BR4 + construcción · BR5 ≡ Base.

## Semantics worth knowing

* **Time axis.** The Motor has 27 fixed rows (t = −1 … 25) regardless of `Horizonte`; sums/NPVs run over t = 1 … 25. `Horizonte`
  only gates the per-year formulas (E, OPEX, Dep civil, Decom, Resid…), exactly as in the sheet. `Horizonte` > yield length (30)
  throws (Excel: #REF!).
* **EDATE** (`edate`): same day n months later, clamped to the last day of the target month (Excel behaviour). Day arithmetic uses
  UTC day numbers, so `Fecha_COD − Fecha_Precios` reproduces Excel serial differences. `Frac_Peaje(t)` = fraction of operating
  year t (from EDATE(COD,12(t−1)) to EDATE(COD,12t)) after `Fecha_Peaje`, clamped to [0, 1]; 0 for t < 1.
* **IRR** (`irr(cfs, guess)`): Newton from the seed with Excel/LibreOffice's budget (20 iterations, converged when a step < 1e-7),
  then polished to 1e-14. Seeds: project/group IRR 0.1 (Excel default), **equity IRR 0.02** (Motor v3.1 — with 100 % debt the
  equity flow has several roots; Newton from 0.02 lands on 1.0754 % for the Conservador case, as Excel does). If Newton does not
  converge (Excel → #NUM! → "n/a") the engine looks for the sign change nearest the seed inside `IRR_FALLBACK_WINDOW` = [−50 %,
  +100 %] and bisects; roots only outside that window (e.g. −91 % equity IRR after 20 years of losses) → "n/a" like Excel. So the
  engine equals Excel whenever Excel's Newton converges, and may show a nearby root where Excel shows "n/a".
* **Payback simple** (robust, v3.0): last year with negative cumulative FCF_u, interpolated: `(iLast − 2) + (−Cum[iLast]) /
  FCF[iLast+1]` (1-based over the 27 rows); `"no cruza"` if the final cumulative is negative; `−1` if it is never negative.
* **DSCR.** Per-year DSCR is `null` (Excel "") when Int + Amort = 0. `DSCR mín/prom` = "n/a" when Deuda = 0. Degenerate case
  Deuda > 0 with no debt service in t = 1 … 25 (only reachable with Plazo = 0): min → 0 (Excel MIN of blanks), prom → "n/a"
  (Excel shows #DIV/0!).
* **Fiscal — unlimited absorption (ug < 0, i.e. Utilidad_Gravable_SALELGI blank):** negative bases generate a negative tax
  (shield) only if `Escudo_Negativo = "Sí"`, otherwise taxes are floored at 0. Participación laboral (15 %) is computed before IR
  and only if `Incluir_Participacion = "Sí"`.
* **Fiscal — limited absorption + loss pool (ug ≥ 0, art. 11 LRTI):** in each year the negative base is absorbed up to `ug`
  (SALELGI's other taxable profit, 0 for t < 1); the excess joins a loss pool without expiry (`PoolU`/`PoolL`). Positive bases
  amortise the pool up to **25 % of (base + ug)**. Participación uses the same absorption on its own base. Unlevered (`_u`) and
  levered (`_l`) pools are independent.
* **Deducción adicional (Aplica_DedAd, v3.1):** `DedAd = dedad × MIN(Kdep × Pct_Elegible_DedAd / Vida_Fiscal_Equipos,
  Tope_DedAd_Pct × Ingresos_SALELGI)`, deducted from the IR base in t = 1 … Vida_Fiscal_Equipos; `dedad` = 1 iff
  `Aplica_DedAd = "Sí"` (environmental certification, RLRTI 28.6.g). The case «Sin deducción adicional» flips the Custom value.
* **CAPEX.** `K = fKeff × fEsc × kbase`, where kbase scales the 05 decomposition by (P/Potencia_Ref)^(1−ε) and
  (AC/(Potencia_Ref/Ratio_Ref))^(1−ε) with/without Contrato de Inversión, `fKeff = kfix × P × 1000 / kbase` when a fixed $/Wp is
  given (else fK), and `fEsc = Fase_m1 (1+dK)^max(0, Anios_Precios−1) + (1−Fase_m1)(1+dK)^max(0, Anios_Precios)`.
* **Debt.** IDC = D × rd × (Fase_m1 + (1−Fase_m1) × IDC_Frac_Tramo0) × ncon/12; interest by the closed-form outstanding balance
  (`rd·Dt·(1 − ((1+rd)^(t−gr−1) − 1)/((1+rd)^n − 1))`), balloon at t = plazo when plazo ≤ gracia.
* **Replacement of inverters** (t = Reemplazo_Anio): paid by SALELGI (rep = 1: −Krep in FCF, depreciated over min(VFE, H−RA))
  or by Exergy (rep = 2: expense in Ux); rep = 0 none.
* **Energy.** `E_t = P/1000 × frec × Y[t] × disp × (1−deg)^(t−1)` (1-based INDEX into Y_P50/Y_P90); `Eval` capped by the annual
  consumption (art. 9); `Ahorro = Eval × Tarifa_Evitable × fT × (1+escT)^(t−1)`.

## Verification (npm run verify) — v3.1 oracle, LibreOffice recalculation

| Section | cells | failed | max abs Δ | max rel Δ |
|---|---:|---:|---:|---:|
| (a) derived globals vs names.json (incl. Frac_Peaje[27], Consumo_Mensual[12], EDATE) | 82 | 0 | 2.05e-8 | 1.97e-15 |
| (b) case parameters vs motor.json (111 × 30; 1e-12 / exact ints) | 3 330 | 0 | 0 | 0 |
| (c) scalars (22 × 111) | 2 442 | 0 | 5.59e-9 | 4.51e-15 |
| (d) outputs (16 × 111) | 1 776 | 0 | 6.05e-9 | 1.37e-12 |
| (e) blocks (28 × 27 × 111) | 83 916 | 0 | 5.03e-8 | 2.84e-12 |
| **total** | **91 546** | **0** | | |

Acceptance: |Δ| ≤ 1e-6 or rel ≤ 1e-9 per cell; "n/a" ⇄ non-numeric. Worst outputs: VAN proyecto rel 1.4e-12 (values near zero),
TIR/TIR equity/TIR grupo abs ≤ 6.5e-14. Full detail in `verify_report.json`.

Cross-check vs `shadow30.run_case` (Python, 5 seeds × 400 random parameter sets = 1.59 M cells): 0 differences beyond 1e-9
(relative to max(1,|x|)) once the documented semantic differences are excluded (shadow30 returns `None` for payback where the
Motor says "no cruza"/−1, and uses plain bisection on [−0.99, 1] for IRR, which can pick a different root of a multi-root flow or
find none).

## Doubts recorded (not guessed silently)

1. **IRR fallback window.** Where Excel's Newton diverges the sheet shows "n/a"; the engine returns the root nearest the seed if
   one exists in [−50 %, +100 %] (robustness request of the spec) and "n/a" otherwise. The window is a judgement call; narrow
   or remove the fallback (constant `IRR_FALLBACK_WINDOW` / phase 2 of `irr` in `engine.ts`) if strict Excel behaviour is preferred.
   None of the 111 oracle cases is affected (all converge in Newton's first phase).
2. **`Meses_Construccion`** is `=Mes_COD_Cron` (03_Tramites schedule) in the workbook; treated here as a primitive input (21).
3. **`Usar_Deuda`** is carried in `Inputs` but has no effect on the Motor (the Custom column hard-codes Deuda(1/0) = 1).
4. **AVERAGE over blanks** (Deuda > 0 but no debt service in t = 1 … 25) is #DIV/0! in Excel; rendered as "n/a".
5. **Summation order.** LibreOffice's SUM uses compensated summation; the engine sums sequentially. Differences are ≤ 1e-15
   relative (see section (a)/(e) maxima) — irrelevant at the 1e-9 tolerance but the reason the match is "to noise", not bit-exact.
