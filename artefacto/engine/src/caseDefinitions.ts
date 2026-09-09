/**
 * caseDefinitions.ts — the 111 columns of Motor_Sens, in order, with the parameter formulas of
 * build_content.build_cases() evaluated against the Inputs (v3.1).
 *
 *   0      Custom            (block B column «Custom» + the rest of 01)
 *   1–3    Conservador · Base · Favorable   (INDEX(Esc_*, k), k = 2, 3, 4; everything else = Custom)
 *   4–5    Custom P50 · Custom P90
 *   6–17   tornado (12 single-lever cases on the Custom)
 *   18     PISO
 *   19–43  M11…M55  CAPEX × tarifa matrix (Mat_CAPEX × Mat_Tarifa)
 *   44–58  E11…E53  tasa × plazo (Sens_Tasas × Sens_Plazos)
 *   59–62  L1…L4    apalancamiento (Sens_Lev)
 *   63     Terreno alt.
 *   64–67  P1…P4    Sweep_P
 *   68–72  R1…R5    Sweep_Ratio
 *   73–77  A1…A5    AC fija (Sweep_AC_Fija × Sweep_Ratio)
 *   78–92  DM11…DM35 deuda máxima: Sens_Plazos × Sweep_Lev
 *   93–95  TS1…TS3  SALELGI buys the land at price × (0.6, 1.0, 1.4)
 *   96–98  TX1…TX3  Exergy buys the land at price × (0.6, 1.0, 1.4)
 *   99–104 ronda 2 tornado: Disponibilidad − · Escalación CAPEX + · Peaje kW · Sin absorción fiscal · Reemplazo alt. · Sin deducción adicional
 *   105–110 bridge BR0…BR5 v2.0 → v3.0 on the Base column (D) with the «neutro» overrides
 */
import type { CaseParams, Derived, Inputs } from "./engine";

export interface CaseDef {
  name: string;
  desc: string;
  params: CaseParams;
}

/** Excel N(): numbers pass, blanks/text → 0. */
const N = (v: number | null | undefined): number => (typeof v === "number" && Number.isFinite(v) ? v : 0);

/** Motor column B — the Custom case (build_cases() ▸ base). */
export function customParams(i: Inputs, d: Derived): CaseParams {
  return {
    fK: d.Factor_CAPEX,                                                 // =Factor_CAPEX
    fT: 1,                                                              // =1
    scen: d.Eff_Scen,                                                   // =Eff_Scen  (=IF(Escenario_Energia="P50",1,2))
    fO: d.Eff_fO,                                                       // =Eff_fO    (=Factor_OPEX)
    pj: d.Eff_Peaje,                                                    // =Eff_Peaje (=Peaje_SGDA)
    escT: d.Eff_EscT,                                                   // =Eff_EscT  (=Escalacion_Tarifa)
    part: i.Incluir_Participacion === "Sí" ? 1 : 0,                     // =IF(Incluir_Participacion="Sí",1,0)
    iva: i.IVA_Recuperable === "Sí" ? 1 : 0,                            // =IF(IVA_Recuperable="Sí",1,0)
    cont: i.Contrato_Inversion === "Sí" ? 1 : 0,                        // =IF(Contrato_Inversion="Sí",1,0)
    deb: 1,                                                             // =1
    rd: i.Tasa_Deuda,                                                   // =Tasa_Deuda
    lev: i.Pct_Apalancamiento,                                          // =Pct_Apalancamiento
    plazo: i.Plazo_Deuda,                                               // =Plazo_Deuda
    gr: i.Gracia_Deuda,                                                 // =Gracia_Deuda
    P: i.Potencia_DC,                                                   // =Potencia_DC
    ratio: i.Ratio_DCAC,                                                // =Ratio_DCAC
    terr: i.Comprador_Terreno === "SALELGI" ? 1 : 0,                    // =IF(Comprador_Terreno="SALELGI",1,0)
    finT: i.Deuda_Financia_Terreno === "Sí" ? 1 : 0,                    // =IF(Deuda_Financia_Terreno="Sí",1,0)
    fPre: 1,                                                            // =1
    kfix: N(d.CAPEX_Fijo_Wp),                                           // =N(CAPEX_Fijo_Wp)
    disp: d.Disponibilidad,                                             // =Disponibilidad
    dK: d.Escalacion_CAPEX,                                             // =Escalacion_CAPEX
    pkw: i.Peaje_kW_mes,                                                // =Peaje_kW_mes
    rep: i.Reemplazo_Pagador === "SALELGI" ? 1 : i.Reemplazo_Pagador === "Exergy" ? 2 : 0,   // =IF(Reemplazo_Pagador="SALELGI",1,IF(…="Exergy",2,0))
    ug: typeof i.Utilidad_Gravable_SALELGI === "number" && Number.isFinite(i.Utilidad_Gravable_SALELGI)
      ? i.Utilidad_Gravable_SALELGI : -1,                               // =IF(ISNUMBER(Utilidad_Gravable_SALELGI),Utilidad_Gravable_SALELGI,-1)
    ncon: i.Meses_Construccion,                                         // =Meses_Construccion
    req: i.Tasa_Descuento_Equity,                                       // =Tasa_Descuento_Equity
    dec: i.Desmantelamiento_Pct,                                        // =Desmantelamiento_Pct
    deg: i.Degradacion_Adicional,                                       // =Degradacion_Adicional
    dedad: i.Aplica_DedAd === "Sí" ? 1 : 0,                             // =IF(Aplica_DedAd="Sí",1,0)
  };
}

const ESC_NAMES: Record<number, string> = { 2: "Conservador", 3: "Base", 4: "Favorable" };

export function buildCases(i: Inputs, d: Derived): CaseDef[] {
  const B = customParams(i, d);
  const cases: CaseDef[] = [];
  const kase = (name: string, desc: string, over: Partial<CaseParams> = {}): CaseDef => ({ name, desc, params: { ...B, ...over } });

  // 0 · Custom
  cases.push({ name: "Custom", desc: "Caso de trabajo: bloque B (columna Custom) + resto de entradas de 01", params: { ...B } });

  // 1–3 · Conservador · Base · Favorable — INDEX(Esc_*, k) with k = 2, 3, 4 (1-based over C:F)
  for (const k of [2, 3, 4]) {
    const j = k - 1;
    cases.push(kase(ESC_NAMES[k], `Escenario fijo ${ESC_NAMES[k]}: bloque B de 01 (columna ${k}); diseño compartido con el Custom`, {
      scen: i.Esc_Energia[j] === "P50" ? 1 : 2,            // =IF(INDEX(Esc_Energia,k)="P50",1,2)
      fK: i.Esc_Factor_CAPEX[j],                           // =INDEX(Esc_Factor_CAPEX,k)
      kfix: N(i.Esc_CAPEX_Fijo_Wp[j]),                     // =N(INDEX(Esc_CAPEX_Fijo_Wp,k))
      fO: i.Esc_Factor_OPEX[j],                            // =INDEX(Esc_Factor_OPEX,k)
      pj: i.Esc_Peaje[j],                                  // =INDEX(Esc_Peaje,k)
      escT: i.Esc_EscTarifa[j],                            // =INDEX(Esc_EscTarifa,k)
      disp: i.Esc_Disponibilidad[j],                       // =INDEX(Esc_Disponibilidad,k)
      dK: i.Esc_Escalacion_CAPEX[j],                       // =INDEX(Esc_Escalacion_CAPEX,k)
    }));
  }

  // 4–5 · energía forzada
  cases.push(kase("Custom P50", "Custom con energía P50", { scen: 1 }));
  cases.push(kase("Custom P90", "Custom con energía P90", { scen: 2 }));

  // 6–17 · tornado (single levers on the Custom)
  cases.push(kase("CAPEX −", "CAPEX del Custom × (1−Sens_CAPEX)", { fK: B.fK * (1 - i.Sens_CAPEX), kfix: B.kfix * (1 - i.Sens_CAPEX) }));
  cases.push(kase("CAPEX +", "CAPEX del Custom × (1+Sens_CAPEX)", { fK: B.fK * (1 + i.Sens_CAPEX), kfix: B.kfix * (1 + i.Sens_CAPEX) }));
  cases.push(kase("Tarifa −", "Factor tarifa 1−Sens_Tarifa", { fT: 1 - i.Sens_Tarifa }));
  cases.push(kase("Tarifa +", "Factor tarifa 1+Sens_Tarifa", { fT: 1 + i.Sens_Tarifa }));
  cases.push(kase("Energía alt.", "P90 si el Custom usa P50 (y viceversa)", { scen: B.scen === 1 ? 2 : 1 }));
  cases.push(kase("OPEX +", "Factor OPEX del Custom × (1+Sens_OPEX_Up)", { fO: B.fO * (1 + i.Sens_OPEX_Up) }));
  cases.push(kase("OPEX −", "Factor OPEX del Custom × (1−Sens_OPEX_Dn)", { fO: B.fO * (1 - i.Sens_OPEX_Dn) }));
  cases.push(kase("Peaje", "Peaje SGDA = Sens_Peaje", { pj: i.Sens_Peaje }));
  cases.push(kase("Esc. tarifa", "Escalación = Sens_EscTarifa", { escT: i.Sens_EscTarifa }));
  cases.push(kase("Participación alt.", "Participación alterna", { part: 1 - B.part }));
  cases.push(kase("IVA alt.", "IVA recuperable alterno", { iva: 1 - B.iva }));
  cases.push(kase("Contrato alt.", "Contrato de Inversión alterno", { cont: 1 - B.cont }));

  // 18 · PISO
  cases.push(kase("PISO", "P90 + CAPEX+ + OPEX+ + peaje + IVA no recuperable", {
    scen: 2, fK: B.fK * (1 + i.Sens_CAPEX), kfix: B.kfix * (1 + i.Sens_CAPEX), fO: B.fO * (1 + i.Sens_OPEX_Up), pj: i.Sens_Peaje, iva: 0,
  }));

  // 19–43 · matrix CAPEX × tarifa
  for (let a = 0; a < 5; a++) {
    for (let b = 0; b < 5; b++) {
      cases.push(kase(`M${a + 1}${b + 1}`, `CAPEX paso ${a + 1} × tarifa paso ${b + 1}`, {
        fK: B.fK * (1 + i.Mat_CAPEX[a]),                   // =$B$5*(1+INDEX(Mat_CAPEX,a))
        kfix: B.kfix * (1 + i.Mat_CAPEX[a]),               // =$B$24*(1+INDEX(Mat_CAPEX,a))
        fT: 1 + i.Mat_Tarifa[b],                           // =1+INDEX(Mat_Tarifa,b)
      }));
    }
  }
  // 44–58 · tasa × plazo
  for (let a = 0; a < 5; a++) {
    for (let b = 0; b < 3; b++) {
      cases.push(kase(`E${a + 1}${b + 1}`, `Tasa paso ${a + 1} × plazo paso ${b + 1}`, { rd: i.Sens_Tasas[a], plazo: i.Sens_Plazos[b] }));
    }
  }
  // 59–62 · apalancamiento
  for (let a = 0; a < 4; a++) cases.push(kase(`L${a + 1}`, `Apalancamiento paso ${a + 1}`, { lev: i.Sens_Lev[a] }));

  // 63 · terreno alterno
  cases.push(kase("Terreno alt.", "Comprador del terreno alterno (Exergy ↔ SALELGI)", { terr: 1 - B.terr }));

  // 64–67 · sweep potencia (ratio del Custom)
  for (let a = 0; a < 4; a++) cases.push(kase(`P${a + 1}`, `Potencia paso ${a + 1} (ratio del Custom)`, { P: i.Sweep_P[a] }));
  // 68–72 · sweep ratio (potencia del Custom)
  for (let a = 0; a < 5; a++) cases.push(kase(`R${a + 1}`, `Ratio DC/AC paso ${a + 1} (potencia del Custom)`, { ratio: i.Sweep_Ratio[a] }));
  // 73–77 · AC fija: P = Sweep_AC_Fija × ratio
  for (let a = 0; a < 5; a++) {
    cases.push(kase(`A${a + 1}`, `AC fija: DC = AC_fija × ratio paso ${a + 1}`, { ratio: i.Sweep_Ratio[a], P: i.Sweep_AC_Fija * i.Sweep_Ratio[a] }));
  }
  // 78–92 · deuda máxima: plazo × apalancamiento
  for (let j = 0; j < 3; j++) {
    for (let a = 0; a < 5; a++) {
      cases.push(kase(`DM${j + 1}${a + 1}`, `Deuda máxima: plazo paso ${j + 1} × apalancamiento paso ${a + 1}`, { plazo: i.Sens_Plazos[j], lev: i.Sweep_Lev[a] }));
    }
  }
  // 93–98 · precio del terreno (SALELGI / Exergy compra)
  const PRECIO_STEPS = [0.6, 1.0, 1.4];
  PRECIO_STEPS.forEach((fp, a) => cases.push(kase(`TS${a + 1}`, `SALELGI compra a precio × ${fp}`, { terr: 1, fPre: fp })));
  PRECIO_STEPS.forEach((fp, a) => cases.push(kase(`TX${a + 1}`, `Exergy compra a precio × ${fp}`, { terr: 0, fPre: fp })));

  // 99–104 · ronda 2 tornado (+ v3.1 deducción adicional)
  cases.push(kase("Disponibilidad −", "Disponibilidad del Custom − Sens_Disponibilidad", { disp: Math.max(0, B.disp - i.Sens_Disponibilidad) }));
  cases.push(kase("Escalación CAPEX +", "Escalación del CAPEX del Custom + Sens_EscCAPEX", { dK: B.dK + i.Sens_EscCAPEX }));
  cases.push(kase("Peaje kW", "Peaje por potencia = Sens_Peaje_kW", { pkw: i.Sens_Peaje_kW }));
  cases.push(kase("Sin absorción fiscal", "Utilidad gravable disponible 0 (pérdidas sólo por arrastre)", { ug: 0 }));
  cases.push(kase("Reemplazo alt.", "Reemplazo pagado por el otro (SALELGI ↔ Exergy; si No → SALELGI)", { rep: B.rep === 1 ? 2 : 1 }));
  cases.push(kase("Sin deducción adicional", "Deducción adicional alterna al Custom (Sí ↔ No): sin la certificación ambiental previa del RLRTI 28.6.g", { dedad: 1 - B.dedad }));

  // 105–110 · bridge v2.0 → v3.0 on the Base column (D) with the neutral overrides
  const Dp = cases[2].params; // Base
  const neutro: Partial<CaseParams> = { disp: 1, dK: 0, rep: 0, ncon: 12, req: i.Tasa_Descuento, dec: 0, deg: 0, pkw: 0, ug: -1 };
  const bridge = (name: string, desc: string, on: Partial<CaseParams>): CaseDef => ({ name, desc, params: { ...Dp, ...neutro, ...on } });
  cases.push(bridge("BR0 v2.0", "Base con los parámetros de la ronda 2 en neutro (≡ definición v2.0)", {}));
  cases.push(bridge("BR1 + escalación", "+ escalación del CAPEX del Base", { dK: Dp.dK }));
  cases.push(bridge("BR2 + disponibilidad", "+ disponibilidad del Base", { dK: Dp.dK, disp: Dp.disp }));
  cases.push(bridge("BR3 + reemplazo", "+ reemplazo de inversores (pagador de 01)", { dK: Dp.dK, disp: Dp.disp, rep: Dp.rep }));
  cases.push(bridge("BR4 + construcción", "+ meses de construcción (03)", { dK: Dp.dK, disp: Dp.disp, rep: Dp.rep, ncon: Dp.ncon }));
  cases.push(bridge("BR5 ≡ Base", "+ tasa del accionista y demás parámetros de diseño (peaje kW, desmantelamiento, degradación, utilidad gravable) ≡ Base",
    { dK: Dp.dK, disp: Dp.disp, rep: Dp.rep, ncon: Dp.ncon, req: Dp.req, dec: Dp.dec, deg: Dp.deg, pkw: Dp.pkw, ug: Dp.ug }));

  if (cases.length !== 111) throw new Error(`buildCases: ${cases.length} casos (esperados 111)`);
  return cases;
}
