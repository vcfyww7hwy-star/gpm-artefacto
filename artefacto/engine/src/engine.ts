/**
 * engine.ts — Motor_Sens (Modelo_FV_5MWp_GPM v3.1) transliterated to TypeScript.
 *
 * Pure, deterministic, zero runtime dependencies. Every formula is commented with the
 * Excel cell / defined name / Motor row label it reproduces (see build_core.py ▸ build_motor
 * and the sheets 04_Energia / 05_CAPEX for the derived globals).
 *
 * Layout of the Motor (one case per column):
 *   rows  5–34  → 30 parameters   (CaseParams, PARAM_LABELS)
 *   rows 35–56  → 22 scalars      (SCALAR_LABELS)
 *   rows 57–72  → 16 outputs      (OUTPUT_LABELS)
 *   rows 75–…   → 28 blocks × 27 years (t = −1 … 25)   (BLOCK_NAMES)
 *
 * Property names of `Inputs` are the Excel defined names of 01_Supuestos (and the
 * few 04/05/10 tables the Motor depends on) so the mapping stays 1:1 with the workbook.
 */

// ---------------------------------------------------------------------------------------------
// Time axis (fixed by the Motor layout: T_MIN … T_MAX, 27 rows, independent of Horizonte)
// ---------------------------------------------------------------------------------------------
export const T_MIN = -1;
export const T_MAX = 25;
/** Years t = −1, 0, 1, …, 25 (27 values) — column A of every block. */
export const T_AXIS: readonly number[] = Array.from({ length: T_MAX - T_MIN + 1 }, (_, i) => T_MIN + i);
/** 0-based row index of year t inside a block array. */
export const tIndex = (t: number): number => t - T_MIN;

export type SiNo = "Sí" | "No";

// ---------------------------------------------------------------------------------------------
// Inputs — primitives (sheet 01_Supuestos + the tables of 04_Energia, 05_CAPEX, 10_Sensibilidad)
// ---------------------------------------------------------------------------------------------

/** One row (7–15) of the 05_CAPEX rubro table. */
export interface Rubro {
  /** C7:C15 — label (informative only). */
  nombre: string;
  /** D — "Costo base 5 MWp [USD]". */
  costo: number;
  /** E — "% comp." (share of the rubro that is shared with the site). */
  pctComp: number;
  /** G — "% ext." (imported share). */
  pctExt: number;
  /** I — "Arancel %". */
  arancel: number;
  /** O — "IVA %". */
  iva: number;
  /** Drv_Wp (05_CAPEX!D45:D53) — share of the rubro that scales with kWp. */
  drvWp: number;
  /** Drv_Wac (05_CAPEX!E45:E53) — share that scales with kWac. */
  drvWac: number;
  /** Drv_Fijo (05_CAPEX!F45:F53) — fixed share. */
  drvFijo: number;
}

export interface Inputs {
  // ---- A · Mandos y marco general (01_Supuestos rows 23–35) ------------------------------
  /** 01!C23 Potencia_DC — kWp (Custom). */
  Potencia_DC: number;
  /** 01!C24 Ratio_DCAC (Custom). */
  Ratio_DCAC: number;
  /** 01!C25 Comprador_Terreno — "SALELGI" | "Exergy". */
  Comprador_Terreno: "SALELGI" | "Exergy";
  /** 01!C26 Usar_Deuda — "Destacar el caso con deuda en la portada". NOT used by the Motor
   *  (the Custom column has Deuda(1/0) = 1 hard-wired); kept for completeness of 01. */
  Usar_Deuda: SiNo;
  /** 01!C27 Tasa_Descuento — nominal USD discount rate (VAN proyecto, VAN Exergy, DF). */
  Tasa_Descuento: number;
  /** 01!C28 Tasa_Descuento_Equity — shareholder rate (VAN equity). */
  Tasa_Descuento_Equity: number;
  /** 01!C31 Horizonte — years of operation (25). */
  Horizonte: number;
  /** 01!C32 Fecha_COD — ISO date "YYYY-MM-DD". */
  Fecha_COD: string;
  /** 01!C33 Meses_Construccion (= Mes_COD_Cron = MAX('03_Tramites'!H8:H24)); treated as a primitive here. */
  Meses_Construccion: number;

  // ---- B · Supuestos de escenario (01_Supuestos rows 38–45, columns C:F = Custom · Conservador · Base · Favorable)
  /** 01!C38:F38 Esc_Energia — "P50" | "P90" per column; [0] = Escenario_Energia (Custom). */
  Esc_Energia: string[];
  /** 01!C39:F39 Esc_Factor_CAPEX; [0] = Factor_CAPEX. */
  Esc_Factor_CAPEX: number[];
  /** 01!C40:F40 Esc_CAPEX_Fijo_Wp ($/Wp, null = blank → bottom-up × factor); [0] = CAPEX_Fijo_Wp. */
  Esc_CAPEX_Fijo_Wp: (number | null)[];
  /** 01!C41:F41 Esc_Factor_OPEX; [0] = Factor_OPEX. */
  Esc_Factor_OPEX: number[];
  /** 01!C42:F42 Esc_Peaje ($/kWh); [0] = Peaje_SGDA. */
  Esc_Peaje: number[];
  /** 01!C43:F43 Esc_EscTarifa; [0] = Escalacion_Tarifa. */
  Esc_EscTarifa: number[];
  /** 01!C44:F44 Esc_Disponibilidad; [0] = Disponibilidad. */
  Esc_Disponibilidad: number[];
  /** 01!C45:F45 Esc_Escalacion_CAPEX; [0] = Escalacion_CAPEX. */
  Esc_Escalacion_CAPEX: number[];

  // ---- C · Energía, red y tarifa (01 rows 49–68) ------------------------------------------
  /** 01!C49 Potencia_Ref (kWp of the CAPEX/yield study). */
  Potencia_Ref: number;
  /** 01!C50 Ratio_Ref. */
  Ratio_Ref: number;
  /** 01!C52 Densidad_MWp_ha. */
  Densidad_MWp_ha: number;
  /** 01!C57 Degradacion_Adicional (%/yr). */
  Degradacion_Adicional: number;
  /** 01!C58 Frac_A — share of injection in block A (08–18 h). */
  Frac_A: number;
  /** 01!C59 Frac_B. */
  Frac_B: number;
  /** 01!C60 Frac_C. */
  Frac_C: number;
  /** 01!C61 Tarifa_A ($/kWh, blocks A and B). */
  Tarifa_A: number;
  /** 01!C62 Tarifa_C ($/kWh, block C). */
  Tarifa_C: number;
  /** 01!C66 Crecimiento_Consumo (%/yr). */
  Crecimiento_Consumo: number;
  /** 01!C67 Fecha_Peaje — ISO date. */
  Fecha_Peaje: string;
  /** 01!C68 Peaje_kW_mes ($/kW-month). */
  Peaje_kW_mes: number;
  /** 04!F91:AI91 Y_P50 — canonical P50 yield kWh/kWp, years 1…30. */
  Y_P50: number[];
  /** 04!F92:AI92 Y_P90. */
  Y_P90: number[];
  /** 04!H66:H79 CR_Ratio — clipping curve abscissa (ratio DC/AC). */
  CR_Ratio: number[];
  /** 04!I66:I79 CR_Loss — clipping loss at each ratio. */
  CR_Loss: number[];
  /** 04!D33:D44 Perfil_Mensual — monthly production profile (Σ = 1). */
  Perfil_Mensual: number[];
  /** 04!D17:D28 — 2025 consumption block A [kWh], ene…dic. */
  Consumo_2025_A: number[];
  /** 04!E17:E28 — 2025 consumption block B. */
  Consumo_2025_B: number[];
  /** 04!F17:F28 — 2025 consumption block C. */
  Consumo_2025_C: number[];
  /** 04!D66:D70 — 2025 ene–may totals (denominator of Factor_Nivel_2026). */
  Consumo_2025_EneMay: number[];
  /** 04!E66:E70 — 2026 ene–may totals (numerator of Factor_Nivel_2026). */
  Consumo_2026_EneMay: number[];

  // ---- D · CAPEX y terreno (01 rows 71–91, 05_CAPEX table) --------------------------------
  /** 01!C71 Fase_m1 — CAPEX fraction disbursed in t = −1. */
  Fase_m1: number;
  /** 01!C72 Fecha_Precios — ISO date of the CAPEX price basis. */
  Fecha_Precios: string;
  /** 01!C73 Contingencia_Pct. */
  Contingencia_Pct: number;
  /** 01!C74 Contingencia_Frac_IVA. */
  Contingencia_Frac_IVA: number;
  /** 01!C75 Fee_Gerencia_Pct. */
  Fee_Gerencia_Pct: number;
  /** 01!C76 Asignacion_Compartida. */
  Asignacion_Compartida: number;
  /** 01!C77 Exponente_Escala (ε). */
  Exponente_Escala: number;
  /** 01!C78 Contrato_Inversion. */
  Contrato_Inversion: SiNo;
  /** 01!C79 IVA_Recuperable. */
  IVA_Recuperable: SiNo;
  /** 01!C80 Tasa_IVA. */
  Tasa_IVA: number;
  /** 01!C81 FODINFA_Pct. */
  FODINFA_Pct: number;
  /** 01!C82 ISD_Pct. */
  ISD_Pct: number;
  /** 01!C83 Reemplazo_Anio (t of the inverter replacement). */
  Reemplazo_Anio: number;
  /** 01!C84 Reemplazo_USD_Wac ($/Wac). */
  Reemplazo_USD_Wac: number;
  /** 01!C85 Reemplazo_Pagador — "SALELGI" | "Exergy" | "No". */
  Reemplazo_Pagador: "SALELGI" | "Exergy" | "No";
  /** 01!C86 Desmantelamiento_Pct (% of CAPEX at t = H). */
  Desmantelamiento_Pct: number;
  /** 01!C87 Precio_Terreno_ha. */
  Precio_Terreno_ha: number;
  /** 01!C88 Costos_Transaccion_Terreno_Pct. */
  Costos_Transaccion_Terreno_Pct: number;
  /** 01!C89 Predial_Terreno ($/yr). */
  Predial_Terreno: number;
  /** 01!C90 Residual_Terreno_Pct. */
  Residual_Terreno_Pct: number;
  /** 01!C91 Apreciacion_Terreno (%/yr). */
  Apreciacion_Terreno: number;
  /** 05_CAPEX rows 7–15 (9 rubros). */
  rubros: Rubro[];
  /** 05_CAPEX!O18 — IVA % of the management fee row. */
  iva_fee: number;

  // ---- E · OPEX de SALELGI (01 rows 94–98) ------------------------------------------------
  Fee_OM_kWp: number;
  Seguro_kWp: number;
  Renta_Terreno_ha: number;
  Tributos_Locales: number;
  Escalacion_OPEX: number;

  // ---- F · Deuda (01 rows 101–107) ----------------------------------------------------------
  Pct_Apalancamiento: number;
  Tasa_Deuda: number;
  Plazo_Deuda: number;
  Gracia_Deuda: number;
  IDC_Frac_Tramo0: number;
  /** 01!C106 DSCR_Objetivo — used by 10_Sensibilidad (Deuda_Max), not by the Motor. */
  DSCR_Objetivo: number;
  Deuda_Financia_Terreno: SiNo;

  // ---- G · Fiscal (01 rows 110–121) ---------------------------------------------------------
  Tasa_IR: number;
  Tasa_Participacion: number;
  Incluir_Participacion: SiNo;
  Escudo_Negativo: SiNo;
  /** 01!C114 Utilidad_Gravable_SALELGI — null (blank) = unlimited absorption. */
  Utilidad_Gravable_SALELGI: number | null;
  Vida_Fiscal_Equipos: number;
  Vida_Fiscal_Civil: number;
  Aplica_DedAd: SiNo;
  Pct_Elegible_DedAd: number;
  Ingresos_SALELGI: number;
  Tope_DedAd_Pct: number;

  // ---- H · Negocio Exergy (01 rows 124–126) -------------------------------------------------
  Costo_Gerencia_Pct: number;
  Costo_OM_Exergy_kWp: number;
  Tasa_Efectiva_Exergy: number;

  // ---- 10_Sensibilidad — sensitivity knobs used by caseDefinitions.ts -----------------------
  Sens_CAPEX: number;
  Sens_Tarifa: number;
  Sens_OPEX_Up: number;
  Sens_OPEX_Dn: number;
  Sens_Peaje: number;
  Sens_EscTarifa: number;
  Sens_Disponibilidad: number;
  Sens_EscCAPEX: number;
  Sens_Peaje_kW: number;
  Sweep_AC_Fija: number;
  /** 10!C11:G11 (5). */
  Mat_CAPEX: number[];
  /** 10!C12:G12 (5). */
  Mat_Tarifa: number[];
  /** 10!C13:G13 (5). */
  Sens_Tasas: number[];
  /** 10!C14:E14 (3). */
  Sens_Plazos: number[];
  /** 10!C15:F15 (4). */
  Sens_Lev: number[];
  /** 10!C16:F16 (4). */
  Sweep_P: number[];
  /** 10!C17:G17 (5). */
  Sweep_Ratio: number[];
  /** 10!C18:G18 (5). */
  Sweep_Lev: number[];
}

// ---------------------------------------------------------------------------------------------
// Derived globals (defined names computed in 04_Energia / 05_CAPEX / 01_Supuestos §J)
// ---------------------------------------------------------------------------------------------
export interface Derived {
  // 01 §B Custom scalars (first column of the block-B ranges)
  Escenario_Energia: string;
  Factor_CAPEX: number;
  CAPEX_Fijo_Wp: number | null;
  Factor_OPEX: number;
  Peaje_SGDA: number;
  Escalacion_Tarifa: number;
  Disponibilidad: number;
  Escalacion_CAPEX: number;
  // 01 §C/§J
  Potencia_AC: number;
  Hectareas: number;
  Yield_Ref: number;
  Tasa_Efectiva: number;
  Eff_Scen: number;
  Eff_fO: number;
  Eff_Peaje: number;
  Eff_EscT: number;
  Escala_Wp: number;
  Escala_Wac: number;
  Anios_Precios: number;
  // 04_Energia
  Factor_Nivel_2026: number;
  /** 04!K17:K28 — projected monthly consumption [kWh]. */
  Consumo_Mensual: number[];
  Consumo_Anual: number;
  Loss_Ref: number;
  Loss_Act: number;
  F_Recorte: number;
  /** 04!J61 — avoided value of year 1 at the Custom (informative). */
  Ahorro_Mensual_Anio1: number;
  Tarifa_Evitable: number;
  /** 04!D99:AD99 — fraction of year t with the SGDA toll in force, t = −1…25 (27). */
  Frac_Peaje: number[];
  // 05_CAPEX (all at factor 1, Potencia_Ref/Ratio_Ref reference)
  CAPEX_SC_Wp: number; CAPEX_SC_Wac: number; CAPEX_SC_Fijo: number;
  CAPEX_CC_Wp: number; CAPEX_CC_Wac: number; CAPEX_CC_Fijo: number;
  IVA_SC_Wp: number; IVA_SC_Wac: number; IVA_SC_Fijo: number;
  IVA_CC_Wp: number; IVA_CC_Wac: number; IVA_CC_Fijo: number;
  CAPEX_SC_f1: number; CAPEX_CC_f1: number; IVA_SC_f1: number; IVA_CC_f1: number;
  /** 05!D28 — bottom-up at factor 1 for the Custom power/ratio/contract. */
  CAPEX_Base_f1: number;
  /** 05!D29 — price escalation factor of the Custom. */
  Factor_Escalacion: number;
  /** 05!D30 — factor applied to every rubro in the Custom sheet (incl. escalation). */
  Factor_Caso: number;
  /** 05!N24 = N12/N19 — share of the industrial CAPEX that is civil works (Custom). */
  Pct_CAPEX_Civil: number;
  /** 05!H40 Reemplazo_USD (Custom, informative). */
  Reemplazo_USD: number;
  /** 05!H41 Desmantelamiento_USD (Custom, informative). */
  Desmantelamiento_USD: number;
}

// ---------------------------------------------------------------------------------------------
// Case parameters (Motor rows 5–34)
// ---------------------------------------------------------------------------------------------
export interface CaseParams {
  fK: number; fT: number; scen: number; fO: number; pj: number; escT: number; part: number; iva: number;
  cont: number; deb: number; rd: number; lev: number; plazo: number; gr: number; P: number; ratio: number;
  terr: number; finT: number; fPre: number; kfix: number; disp: number; dK: number; pkw: number; rep: number;
  ug: number; ncon: number; req: number; dec: number; deg: number; dedad: number;
}
export type ParamKey = keyof CaseParams;

/** Short key → Motor row label (column A), in Motor row order (rows 5…34). */
export const PARAM_LABELS: Readonly<Record<ParamKey, string>> = {
  fK: "Factor CAPEX (× bottom-up)",
  fT: "Factor tarifa",
  scen: "Escenario energía (1=P50, 2=P90)",
  fO: "Factor OPEX",
  pj: "Peaje $/kWh",
  escT: "Escalación tarifa",
  part: "Participación (1/0)",
  iva: "IVA recuperable (1/0)",
  cont: "Contrato inversión (1/0)",
  deb: "Deuda (1/0)",
  rd: "Tasa deuda",
  lev: "Apalancamiento",
  plazo: "Plazo",
  gr: "Gracia",
  P: "Potencia DC (kWp)",
  ratio: "Ratio DC/AC",
  terr: "Terreno lo compra SALELGI (1/0)",
  finT: "Banco financia terreno (1/0)",
  fPre: "Factor precio terreno",
  kfix: "CAPEX fijo $/Wp (0 = bottom-up × factor)",
  disp: "Disponibilidad",
  dK: "Escalación CAPEX (%/año hasta la compra)",
  pkw: "Peaje por potencia $/kW-mes",
  rep: "Reemplazo inversores (0 No · 1 SALELGI · 2 Exergy)",
  ug: "Utilidad gravable SALELGI (−1 = ilimitada)",
  ncon: "Meses de construcción",
  req: "Tasa descuento accionista",
  dec: "Desmantelamiento (% CAPEX en t=H)",
  deg: "Degradación adicional (%/año)",
  dedad: "Deducción adicional aplicable (1/0)",
};
export const PARAM_KEYS = Object.keys(PARAM_LABELS) as ParamKey[];

// ---------------------------------------------------------------------------------------------
// Scalars (Motor rows 35–56), outputs (57–72) and blocks (75…)
// ---------------------------------------------------------------------------------------------
export const SCALAR_LABELS = {
  frec: "Factor de recorte",
  AC: "Potencia AC (kW)",
  ha: "Hectáreas",
  K: "CAPEX industrial sin IVA",
  IVA: "IVA CAPEX",
  Kdep: "CAPEX depreciable",
  DepEq: "Dep. equipos/año",
  DepCiv: "Dep. civil/año",
  DedAd: "Deducción adicional/año",
  Terr: "Terreno (costo total quien compra)",
  Resid: "Residual terreno neto (t=H)",
  OPEX1: "OPEX año 1 SALELGI",
  Sub: "Subtotal EPC (base fee)",
  D: "Deuda",
  IDC: "IDC",
  Dt: "Deuda total COD",
  n: "Nº cuotas",
  PMT: "Cuota",
  fKeff: "Factor CAPEX efectivo",
  fEsc: "Factor de escalación del CAPEX",
  Krep: "Reemplazo de inversores (USD)",
  Decom: "Desmantelamiento (USD)",
} as const;
export type ScalarKey = keyof typeof SCALAR_LABELS;
export type ScalarLabel = (typeof SCALAR_LABELS)[ScalarKey];

export const OUTPUT_LABELS = {
  TIR: "TIR proyecto",
  VAN: "VAN proyecto",
  PB: "Payback simple",
  LCOE: "LCOE $/MWh",
  TIR_eq: "TIR equity",
  VAN_eq: "VAN equity",
  DSCR_min: "DSCR mín",
  DSCR_avg: "DSCR prom",
  Ahorro1: "Ahorro año 1",
  Aporte_eq: "Aporte equity",
  VAN_X: "VAN Exergy",
  TIR_G: "TIR grupo",
  E1: "Energía año 1 (MWh)",
  NoRec: "Energía no reconocida Σ (MWh)",
  Cob: "Cobertura año 1",
  Nominal_X: "Nominal Exergy Σ",
} as const;
export type OutputKey = keyof typeof OUTPUT_LABELS;
export type OutputLabel = (typeof OUTPUT_LABELS)[OutputKey];

export const BLOCK_NAMES = [
  "E", "Eval", "Ahorro", "OPEX", "Peaje", "EBITDA", "Dep", "Part_u", "IR_u", "Terr", "FCF_u", "Cum_u",
  "Int", "Amort", "Part_l", "IR_l", "CFADS", "EQ", "DSCR", "DF", "Ux", "Ix", "Tx", "Fx", "Gx", "Krep", "PoolU", "PoolL",
] as const;
export type BlockName = (typeof BLOCK_NAMES)[number];

/** Motor outputs: numeric, "n/a" (IFERROR / no debt) or "no cruza" (payback never turns positive). */
export type OutputValue = number | "n/a" | "no cruza";

export interface CaseResult {
  scalars: Record<ScalarLabel, number>;
  outputs: Record<OutputLabel, OutputValue>;
  /** 27 values per block (t = −1…25). Only DSCR contains nulls (Excel "" when no debt service). */
  blocks: Record<BlockName, (number | null)[]>;
}

// ---------------------------------------------------------------------------------------------
// Dates — Excel serial arithmetic and EDATE (end-of-month clamping)
// ---------------------------------------------------------------------------------------------
export interface YMD { y: number; m: number; d: number }

export function parseISODate(s: string): YMD {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s.trim());
  if (!m) throw new Error(`Fecha no ISO (YYYY-MM-DD): ${s}`);
  return { y: +m[1], m: +m[2], d: +m[3] };
}

/** Days since 1970-01-01 (UTC); differences reproduce Excel serial-date differences. */
export function dayNumber(d: YMD): number {
  return Math.round(Date.UTC(d.y, d.m - 1, d.d) / 86400000);
}

export function daysInMonth(y: number, m: number): number {
  return new Date(Date.UTC(y, m, 0)).getUTCDate(); // day 0 of next month
}

/** Excel EDATE: same day `months` later, clamped to the last day of the target month. */
export function edate(d: YMD, months: number): YMD {
  const idx = d.m - 1 + months;
  const y = d.y + Math.floor(idx / 12);
  const m = ((idx % 12) + 12) % 12 + 1;
  return { y, m, d: Math.min(d.d, daysInMonth(y, m)) };
}

export function formatISODate(d: YMD): string {
  const p = (n: number, w: number) => String(n).padStart(w, "0");
  return `${p(d.y, 4)}-${p(d.m, 2)}-${p(d.d, 2)}`;
}

// ---------------------------------------------------------------------------------------------
// Finance helpers (Excel semantics)
// ---------------------------------------------------------------------------------------------

/** Excel NPV(rate, v1..vn) = Σ v_i / (1+rate)^i, i = 1…n. */
export function npv(rate: number, values: readonly number[]): number {
  let s = 0;
  for (let i = 0; i < values.length; i++) s += values[i] / Math.pow(1 + rate, i + 1);
  return s;
}

/** Motor "VAN …": v[t=−1]·(1+r) + v[t=0] + NPV(r, v[t=1…25]). */
export function vanMotor(rate: number, v: readonly number[]): number {
  return v[0] * (1 + rate) + v[1] + npv(rate, v.slice(2));
}

/** f(r) = Σ cf_i/(1+r)^i (i = 0…n−1) and its derivative. */
function irrF(cfs: readonly number[], r: number): number {
  let s = 0;
  for (let i = 0; i < cfs.length; i++) s += cfs[i] / Math.pow(1 + r, i);
  return s;
}
function irrDF(cfs: readonly number[], r: number): number {
  let s = 0;
  for (let i = 1; i < cfs.length; i++) s -= (i * cfs[i]) / Math.pow(1 + r, i + 1);
  return s;
}

/** Relative residual of the NPV at rate r: |Σ cf_i/(1+r)^i| / Σ |cf_i|/(1+r)^i (scale-free, valid for r < 0 too). */
function irrRelResidual(cfs: readonly number[], r: number): number {
  let s = 0, a = 0;
  for (let i = 0; i < cfs.length; i++) { const v = cfs[i] / Math.pow(1 + r, i); s += v; a += Math.abs(v); }
  return a > 0 ? Math.abs(s) / a : 0;
}

/** Fallback bracket window (absolute rates) for `irr` when Newton from the seed does not converge. */
export const IRR_FALLBACK_WINDOW: readonly [number, number] = [-0.5, 1.0];
/** true = comportamiento estricto de Excel (sin convergencia → «n/a»); false = raíz más cercana a la semilla dentro de la ventana. */
export const IRR_STRICT_EXCEL = true;

/** Excel/LibreOffice IRR iteration budget and step tolerance (LibreOffice ScIrr: 20 iterations, ε = 1e-7). */
export const IRR_EXCEL_MAX_ITER = 20;
export const IRR_EXCEL_EPS = 1e-7;
/**
 * Guardia R3-5 (propuesta 08-sep-2026, cruce aleatorio s19): una TIR ≤ −100 % es una raíz espuria del dominio 1+r < 0 —
 * Newton la alcanza cuando el equity cubre el servicio de deuda con flujos negativos casi todo el horizonte (100 % de deuda
 * bajo estrés) y la raíz real (≈ −5 % en s19) queda fuera de su trayectoria. LibreOffice devuelve esa raíz tal cual (−303 %
 * en s19); el Motor r3 la mostrará como «n/a» con IF(IRR(…)<=-1,"n/a",IRR(…)) y el motor JS hace lo mismo. Con `false` el
 * motor devuelve la raíz exactamente como LibreOffice (paridad con el libro r2 sin la guardia).
 */
export const IRR_GUARD_BELOW_MINUS1 = true;

/**
 * Excel/LibreOffice IRR semantics.
 *  Phase 1 — Newton–Raphson from `guess` (Excel default 0.1; the Motor uses 0.02 for the equity IRR) exactly as
 *            LibreOffice ScIrr: x ← x − f(x)/f'(x), converged when a step is < 1e-7 within 20 iterations, WITHOUT a
 *            domain cut (1+x may turn negative; the powers are integer so f stays real — a root reached there is
 *            spurious and IRR_GUARD_BELOW_MINUS1 decides whether it is shown). The converged root is then polished
 *            to |Δr| ≤ 1e-14·max(1,|r|) (same root, more digits). Newton lands on the root its own path reaches —
 *            this is what reproduces the 1.0754 % equity IRR of the Conservador case (a multi-root flow) from the
 *            seed 0.02, and Excel's +103 % rather than −14 % on some pathological equity flows.
 *  Phase 2 — only if Newton did not converge in 20 iterations (Excel → #NUM! → "n/a"): a sign-change search
 *            expands outwards from the seed inside IRR_FALLBACK_WINDOW = [−50 %, +100 %] (nearest bracket
 *            first) and bisection finishes, i.e. the engine returns the root nearest the seed where Excel shows
 *            "n/a". Roots outside that window are NOT returned (Excel: "n/a"; engine: null → "n/a").
 *  Returns null when no root is found (→ "n/a" in the Motor).
 */
export function irr(cfs: readonly number[], guess = 0.1): number | null {
  const n = cfs.length;
  if (n < 2) return null;
  let hasPos = false, hasNeg = false;
  for (const v of cfs) { if (v > 0) hasPos = true; if (v < 0) hasNeg = true; }
  if (!hasPos || !hasNeg) return null;
  const tolStep = 1e-14;
  const okRoot = (r: number) => Number.isFinite(r) && r !== -1 && irrRelResidual(cfs, r) <= 1e-9;

  // --- Phase 1: Newton from the seed with Excel's budget (20 iterations, step < 1e-7), then polish
  let x = guess;
  let converged = false;
  for (let it = 0; it < IRR_EXCEL_MAX_ITER; it++) {
    const fv = irrF(cfs, x);
    const d = irrDF(cfs, x);
    if (!Number.isFinite(fv) || !Number.isFinite(d) || d === 0) break;   // 1+x = 0 or f' = 0 → LibreOffice: NaN → NoConvergence
    const nx = x - fv / d;
    if (!Number.isFinite(nx)) break;
    const step = Math.abs(nx - x);
    x = nx;
    if (step < IRR_EXCEL_EPS) { converged = true; break; }
  }
  if (converged) {
    for (let it = 0; it < 20; it++) {                          // polish: same root, full double precision
      const fv = irrF(cfs, x);
      const d = irrDF(cfs, x);
      if (!Number.isFinite(fv) || !Number.isFinite(d) || d === 0) break;
      const nx = x - fv / d;
      if (!Number.isFinite(nx) || (nx <= -1) !== (x <= -1)) break;   // never cross 1+r = 0 while polishing
      const step = Math.abs(nx - x);
      x = nx;
      if (step <= tolStep * Math.max(1, Math.abs(x))) break;
    }
    if (!okRoot(x)) return null;
    if (x <= -1 && IRR_GUARD_BELOW_MINUS1) return null;         // R3-5: raíz espuria (TIR ≤ −100 %) → «n/a»
    return x;
  }

  // --- Strict Excel semantics (decisión F2, 08-sep-2026): si Newton no converge en 20 iteraciones Excel devuelve #NUM! → «n/a».
  //     El motor reproduce ESE comportamiento («Motor ≡ Excel» también en los casos patológicos). La fase 2 (raíz más cercana a la
  //     semilla dentro de IRR_FALLBACK_WINDOW) queda disponible sólo con IRR_STRICT_EXCEL = false.
  if (IRR_STRICT_EXCEL) return null;

  // --- Phase 2: nearest sign change to the seed inside the fallback window, then bisection
  const [lo0, hi0] = IRR_FALLBACK_WINDOW;
  const fAt = (r: number) => irrF(cfs, r);
  const bisect = (a: number, b: number): number | null => {
    let fa = fAt(a), fb = fAt(b);
    if (!Number.isFinite(fa) || !Number.isFinite(fb)) return null;
    if (fa === 0) return a;
    if (fb === 0) return b;
    if ((fa > 0) === (fb > 0)) return null;
    for (let it = 0; it < 400; it++) {
      const m = 0.5 * (a + b);
      const fm = fAt(m);
      if (fm === 0 || Math.abs(b - a) <= tolStep * Math.max(1, Math.abs(m))) return okRoot(m) ? m : null;
      if ((fm > 0) === (fa > 0)) { a = m; fa = fm; } else { b = m; fb = fm; }
    }
    const r = 0.5 * (a + b);
    return okRoot(r) ? r : null;
  };
  const g = Math.min(Math.max(guess, lo0), hi0);
  const step = 0.0025;
  let aL = g, aR = g;
  let fL = fAt(g), fR = fL;
  while (aL > lo0 || aR < hi0) {
    if (aR < hi0) {                                              // right side
      const nr = Math.min(hi0, aR + step);
      const fn = fAt(nr);
      if (Number.isFinite(fn) && Number.isFinite(fR) && (fn > 0) !== (fR > 0)) { const r = bisect(aR, nr); if (r !== null) return r; }
      aR = nr; fR = fn;
    }
    if (aL > lo0) {                                              // left side
      const nl = Math.max(lo0, aL - step);
      const fn = fAt(nl);
      if (Number.isFinite(fn) && Number.isFinite(fL) && (fn > 0) !== (fL > 0)) { const r = bisect(nl, aL); if (r !== null) return r; }
      aL = nl; fL = fn;
    }
  }
  return null;
}

/**
 * Motor "Payback simple" (robust: last crossing, interpolated).
 *   IF(last(cum) < 0, "no cruza", IF(iLast = 0, -1, (iLast − 2) + (−cum[iLast]) / fcf[iLast + 1]))
 * where iLast is the 1-based index of the last negative cumulative (rows t = −1…25 → 1…27).
 */
export function paybackLastCrossing(cum: readonly number[], fcf: readonly number[]): number | "no cruza" {
  const n = cum.length;
  if (cum[n - 1] < 0) return "no cruza";
  let iLast = 0; // 1-based
  for (let i = 0; i < n; i++) if (cum[i] < 0) iLast = i + 1;
  if (iLast === 0) return -1;
  return (iLast - 2) + (-cum[iLast - 1]) / fcf[iLast]; // fcf[iLast] is element iLast+1 (1-based)
}

// ---------------------------------------------------------------------------------------------
// 04_Energia helpers
// ---------------------------------------------------------------------------------------------

/**
 * Clipping loss at a DC/AC ratio (04!J80 Loss_Ref, 04!J81 Loss_Act, Motor "Factor de recorte"):
 *   x = MIN(MAX(r, CR_Ratio[1]), CR_Ratio[n]); k = MIN(MATCH(x, CR_Ratio, 1), n − 1)
 *   loss = CR_Loss[k] + (x − CR_Ratio[k]) · (CR_Loss[k+1] − CR_Loss[k]) / (CR_Ratio[k+1] − CR_Ratio[k])
 */
export function lossAt(CR_Ratio: readonly number[], CR_Loss: readonly number[], ratio: number): number {
  const n = CR_Ratio.length;
  const x = Math.min(Math.max(ratio, CR_Ratio[0]), CR_Ratio[n - 1]);
  let k = 0; // MATCH(x, CR_Ratio, 1) → largest value ≤ x (0-based here)
  for (let i = 0; i < n; i++) if (CR_Ratio[i] <= x) k = i;
  k = Math.min(k, n - 2);
  return CR_Loss[k] + (x - CR_Ratio[k]) * (CR_Loss[k + 1] - CR_Loss[k]) / (CR_Ratio[k + 1] - CR_Ratio[k]);
}

/**
 * 04!D99:AD99 Frac_Peaje(t) = IF(t<1, 0, MAX(0, MIN(1, (EDATE(COD,12t) − MAX(Fecha_Peaje, EDATE(COD,12(t−1))))
 *                                                   / (EDATE(COD,12t) − EDATE(COD,12(t−1))))))
 */
export function fracPeaje(Fecha_COD: YMD, Fecha_Peaje: YMD, t: number): number {
  if (t < 1) return 0;
  const a = dayNumber(edate(Fecha_COD, 12 * (t - 1)));
  const b = dayNumber(edate(Fecha_COD, 12 * t));
  const p = dayNumber(Fecha_Peaje);
  return Math.max(0, Math.min(1, (b - Math.max(p, a)) / (b - a)));
}

// ---------------------------------------------------------------------------------------------
// computeDerived — the defined names of 04/05/01§J that the Motor references
// ---------------------------------------------------------------------------------------------
export function computeDerived(i: Inputs): Derived {
  const H = i.Horizonte;
  // ---- 01 §B Custom column = element [0] of every Esc_* range
  const Escenario_Energia = i.Esc_Energia[0];
  const Factor_CAPEX = i.Esc_Factor_CAPEX[0];
  const CAPEX_Fijo_Wp = i.Esc_CAPEX_Fijo_Wp[0] ?? null;
  const Factor_OPEX = i.Esc_Factor_OPEX[0];
  const Peaje_SGDA = i.Esc_Peaje[0];
  const Escalacion_Tarifa = i.Esc_EscTarifa[0];
  const Disponibilidad = i.Esc_Disponibilidad[0];
  const Escalacion_CAPEX = i.Esc_Escalacion_CAPEX[0];

  // ---- 01 §C / §J
  const Potencia_AC = i.Potencia_DC / i.Ratio_DCAC;                       // 01!C48 =Potencia_DC/Ratio_DCAC
  const Hectareas = i.Potencia_DC / 1000 / i.Densidad_MWp_ha;             // 01!C53
  const Yield_Ref = i.Y_P50[0];                                            // 01!C51 =INDEX(Y_P50,1,1)
  const partOn = i.Incluir_Participacion === "Sí" ? i.Tasa_Participacion : 0;
  const Tasa_Efectiva = partOn + i.Tasa_IR * (1 - partOn);                // 01!C142
  const Eff_Scen = Escenario_Energia === "P50" ? 1 : 2;                    // 01!C143
  const Eff_fO = Factor_OPEX;                                              // 01!C144
  const Eff_Peaje = Peaje_SGDA;                                            // 01!C145
  const Eff_EscT = Escalacion_Tarifa;                                      // 01!C146
  const Escala_Wp = Math.pow(i.Potencia_DC / i.Potencia_Ref, 1 - i.Exponente_Escala);                 // 01!C147
  const Escala_Wac = Math.pow(Potencia_AC / (i.Potencia_Ref / i.Ratio_Ref), 1 - i.Exponente_Escala);  // 01!C148
  const cod = parseISODate(i.Fecha_COD);
  const fpe = parseISODate(i.Fecha_Peaje);
  const fpr = parseISODate(i.Fecha_Precios);
  const Anios_Precios = (dayNumber(cod) - dayNumber(fpr)) / 365.25;       // 01!C150 =(Fecha_COD-Fecha_Precios)/365.25

  // ---- 04_Energia: consumption projection (rows 17–29, 66–72)
  let s25 = 0, s26 = 0;
  for (let k = 0; k < 5; k++) { s25 += i.Consumo_2025_EneMay[k]; s26 += i.Consumo_2026_EneMay[k]; }
  const Factor_Nivel_2026 = s26 / s25;                                     // 04!D72 =E71/D71
  const Consumo_Mensual: number[] = [];
  let Consumo_Anual = 0;
  for (let m = 0; m < 12; m++) {
    // 04!H = D·Factor, I = E·Factor, J = F·Factor ; K = H+I+J
    const K = i.Consumo_2025_A[m] * Factor_Nivel_2026 + i.Consumo_2025_B[m] * Factor_Nivel_2026 + i.Consumo_2025_C[m] * Factor_Nivel_2026;
    Consumo_Mensual.push(K);
    Consumo_Anual += K;                                                    // 04!K29 =SUM(K17:K28)
  }

  // ---- 04_Energia: clipping curve and Custom recorte factor
  const Loss_Ref = lossAt(i.CR_Ratio, i.CR_Loss, i.Ratio_Ref);            // 04!J80
  const Loss_Act = lossAt(i.CR_Ratio, i.CR_Loss, i.Ratio_DCAC);           // 04!J81
  const F_Recorte = (1 - Loss_Act) / (1 - Loss_Ref);                       // 04!J82

  // ---- 04_Energia: monthly balance of year 1 (rows 33–45) → Tarifa_Evitable = J61/I45
  let J61 = 0, I45 = 0;
  for (let m = 0; m < 12; m++) {
    const E = i.Potencia_DC / 1000 * Yield_Ref * F_Recorte * Disponibilidad * i.Perfil_Mensual[m]; // 04!E33
    const F = E * 1000 * i.Frac_A;                                         // 04!F33 inyección A
    const G = E * 1000 * i.Frac_B;                                         // 04!G33 inyección B
    const Hc = E * 1000 * i.Frac_C;                                        // 04!H33 inyección C
    I45 += F + G + Hc;                                                     // 04!I33 → I45 =SUM
    J61 += F * i.Tarifa_A + G * i.Tarifa_A + Hc * i.Tarifa_C;              // 04!J49 → J61 =SUM
  }
  const Ahorro_Mensual_Anio1 = J61;
  const Tarifa_Evitable = J61 / I45;                                       // 04!K61 =J61/I45

  // ---- 04_Energia row 99: Frac_Peaje for t = −1…25
  const Frac_Peaje = T_AXIS.map((t) => fracPeaje(cod, fpe, t));

  // ---- 05_CAPEX: decomposition at factor 1 (columns V…AM, rows 7–19)
  const nR = i.rubros.length;
  const X: number[] = [], Y: number[] = [], Z: number[] = [], AA: number[] = [];
  for (const rb of i.rubros) {
    const V = rb.costo * (1 - rb.pctComp * (1 - i.Asignacion_Compartida));                     // V7 =D7*(1-E7*(1-Asignacion_Compartida))
    X.push(V + V * rb.pctExt * i.FODINFA_Pct + V * rb.pctExt * (rb.arancel + i.ISD_Pct));      // X7  cap. sin contrato @f1
    Y.push(V + V * rb.pctExt * i.FODINFA_Pct);                                                   // Y7  cap. con contrato @f1
    Z.push((V + V * rb.pctExt * i.FODINFA_Pct + V * rb.pctExt * rb.arancel) * rb.iva);          // Z7  IVA sin contrato @f1
    AA.push((V + V * rb.pctExt * i.FODINFA_Pct) * rb.iva);                                       // AA7 IVA con contrato @f1
  }
  const drv = (rb: Rubro, j: number) => (j === 0 ? rb.drvWp : j === 1 ? rb.drvWac : rb.drvFijo);
  /** rows 7–19 of a (base, ivaBase) pair split by driver → [cap[3], iva[3]] */
  const split = (base: number[], ivab: number[]): { cap: number[]; iva: number[] } => {
    const cap: number[] = [], iva: number[] = [];
    for (let j = 0; j < 3; j++) {
      let s7_15 = 0, i7_15 = 0;
      for (let r = 0; r < nR; r++) { s7_15 += base[r] * drv(i.rubros[r], j); i7_15 += ivab[r] * drv(i.rubros[r], j); }   // AB7..AB15 =X7*INDEX(Drv,·)
      const r16 = i.Contingencia_Pct * s7_15;                              // AB16 =Contingencia_Pct*SUM(AB7:AB15)
      const i16 = r16 * i.Tasa_IVA * i.Contingencia_Frac_IVA;              // AH16 =AB16*Tasa_IVA*Contingencia_Frac_IVA
      const r17 = s7_15 + r16;                                             // AB17 =SUM(AB7:AB16)
      const i17 = i7_15 + i16;                                             // AH17 =SUM(AH7:AH16)
      const r18 = i.Fee_Gerencia_Pct * r17;                                // AB18 =Fee_Gerencia_Pct*AB17
      const i18 = r18 * i.iva_fee;                                         // AH18 =AB18*$O$18
      cap.push(r17 + r18);                                                 // AB19 =AB17+AB18
      iva.push(i17 + i18);                                                 // AH19 =AH17+AH18
    }
    return { cap, iva };
  };
  const SC = split(X, Z), CC = split(Y, AA);
  /** total columns X/Y/Z/AA rows 16–19 (CAPEX_SC_f1 …) */
  const total = (col: number[], isIva: boolean, ivaOf?: number[]): number => {
    let s = 0; for (const v of col) s += v;
    if (!isIva) {
      const r16 = i.Contingencia_Pct * s; const r17 = s + r16; const r18 = i.Fee_Gerencia_Pct * r17; return r17 + r18;   // X16..X19
    }
    let sb = 0; for (const v of ivaOf!) sb += v;
    const b16 = i.Contingencia_Pct * sb; const b17 = sb + b16; const b18 = i.Fee_Gerencia_Pct * b17;
    const i16 = b16 * i.Tasa_IVA * i.Contingencia_Frac_IVA; const i17 = s + i16; const i18 = b18 * i.iva_fee;              // Z16..Z19
    return i17 + i18;
  };
  const CAPEX_SC_f1 = total(X, false), CAPEX_CC_f1 = total(Y, false);
  const IVA_SC_f1 = total(Z, true, X), IVA_CC_f1 = total(AA, true, Y);

  // ---- 05!D28:D30 (Custom) and 05!N column → Pct_CAPEX_Civil = N12/N19
  const cont = i.Contrato_Inversion === "Sí";
  const CAPEX_Base_f1 = cont
    ? Escala_Wp * CC.cap[0] + Escala_Wac * CC.cap[1] + CC.cap[2]
    : Escala_Wp * SC.cap[0] + Escala_Wac * SC.cap[1] + SC.cap[2];                                  // 05!D28
  const Factor_Escalacion = i.Fase_m1 * Math.pow(1 + Escalacion_CAPEX, Math.max(0, Anios_Precios - 1))
    + (1 - i.Fase_m1) * Math.pow(1 + Escalacion_CAPEX, Math.max(0, Anios_Precios));                 // 05!D29
  const kfixN = typeof CAPEX_Fijo_Wp === "number" ? CAPEX_Fijo_Wp : 0;                               // N(CAPEX_Fijo_Wp)
  const Factor_Caso = (kfixN > 0 ? kfixN * i.Potencia_DC * 1000 / CAPEX_Base_f1 : Factor_CAPEX) * Factor_Escalacion;   // 05!D30
  const N: number[] = [];
  for (const rb of i.rubros) {
    const V = rb.costo * (1 - rb.pctComp * (1 - i.Asignacion_Compartida));                              // V
    const F = V * Factor_Caso * (rb.drvWp * Escala_Wp + rb.drvWac * Escala_Wac + rb.drvFijo);         // F7 =V7*Factor_Caso*(…)
    const Hh = F * rb.pctExt;                                                                           // H7 =F7*G7
    const J = Hh * rb.arancel;                                                                          // J7 =H7*I7
    const Kf = Hh * i.FODINFA_Pct;                                                                      // K7 =H7*FODINFA_Pct
    const L = Hh * i.ISD_Pct;                                                                           // L7 =H7*ISD_Pct
    const M = cont ? 0 : J + L;                                                                         // M7 =IF(Contrato="Sí",0,J7+L7)
    N.push(F + Kf + M);                                                                                 // N7 =F7+K7+M7
  }
  let sN = 0; for (const v of N) sN += v;
  const N16 = i.Contingencia_Pct * sN;                                                                  // N16
  const N17 = sN + N16;                                                                                 // N17 =SUM(N7:N16)
  const N18 = i.Fee_Gerencia_Pct * N17;                                                                 // N18
  const N19 = N17 + N18;                                                                                // N19 CAPEX_Total
  const Pct_CAPEX_Civil = N[5] / N19;                                                                   // N24 =N12/N19 (rubro 6 = obra civil)

  const Reemplazo_USD = i.Reemplazo_Pagador === "No" ? 0 : i.Reemplazo_USD_Wac * Potencia_AC * 1000;   // 05!H40
  const Desmantelamiento_USD = i.Desmantelamiento_Pct * N19;                                            // 05!H41 (=Desmantelamiento_Pct*CAPEX_Total)
  void H;

  return {
    Escenario_Energia, Factor_CAPEX, CAPEX_Fijo_Wp, Factor_OPEX, Peaje_SGDA, Escalacion_Tarifa, Disponibilidad, Escalacion_CAPEX,
    Potencia_AC, Hectareas, Yield_Ref, Tasa_Efectiva, Eff_Scen, Eff_fO, Eff_Peaje, Eff_EscT, Escala_Wp, Escala_Wac, Anios_Precios,
    Factor_Nivel_2026, Consumo_Mensual, Consumo_Anual, Loss_Ref, Loss_Act, F_Recorte, Ahorro_Mensual_Anio1, Tarifa_Evitable, Frac_Peaje,
    CAPEX_SC_Wp: SC.cap[0], CAPEX_SC_Wac: SC.cap[1], CAPEX_SC_Fijo: SC.cap[2],
    CAPEX_CC_Wp: CC.cap[0], CAPEX_CC_Wac: CC.cap[1], CAPEX_CC_Fijo: CC.cap[2],
    IVA_SC_Wp: SC.iva[0], IVA_SC_Wac: SC.iva[1], IVA_SC_Fijo: SC.iva[2],
    IVA_CC_Wp: CC.iva[0], IVA_CC_Wac: CC.iva[1], IVA_CC_Fijo: CC.iva[2],
    CAPEX_SC_f1, CAPEX_CC_f1, IVA_SC_f1, IVA_CC_f1,
    CAPEX_Base_f1, Factor_Escalacion, Factor_Caso, Pct_CAPEX_Civil, Reemplazo_USD, Desmantelamiento_USD,
  };
}

// ---------------------------------------------------------------------------------------------
// computeCase — one Motor column
// ---------------------------------------------------------------------------------------------
export function computeCase(i: Inputs, d: Derived, p: CaseParams): CaseResult {
  const H = i.Horizonte;
  const r = i.Tasa_Descuento;
  const fase = i.Fase_m1;
  const VFE = i.Vida_Fiscal_Equipos, VFC = i.Vida_Fiscal_Civil;
  const RA = i.Reemplazo_Anio;
  const Tp = i.Tasa_Participacion, Tir = i.Tasa_IR;
  const escudo = i.Escudo_Negativo === "Sí";
  const Y = p.scen === 1 ? i.Y_P50 : i.Y_P90;

  // ---- Scalars (Motor rows 35–56) --------------------------------------------------------------
  // "Factor de recorte" =(1-loss(ratio))/(1-Loss_Ref)
  const frec = (1 - lossAt(i.CR_Ratio, i.CR_Loss, p.ratio)) / (1 - d.Loss_Ref);
  // "Potencia AC (kW)" =P/ratio
  const AC = p.P / p.ratio;
  // "Hectáreas" =P/1000/Densidad_MWp_ha
  const ha = p.P / 1000 / i.Densidad_MWp_ha;
  // a = (P/Potencia_Ref)^(1-ε) ; b = (AC/(Potencia_Ref/Ratio_Ref))^(1-ε)
  const a = Math.pow(p.P / i.Potencia_Ref, 1 - i.Exponente_Escala);
  const b = Math.pow(AC / (i.Potencia_Ref / i.Ratio_Ref), 1 - i.Exponente_Escala);
  // kbase = IF(cont=1, a*CAPEX_CC_Wp+b*CAPEX_CC_Wac+CAPEX_CC_Fijo, a*CAPEX_SC_Wp+b*CAPEX_SC_Wac+CAPEX_SC_Fijo)
  const kbase = p.cont === 1
    ? a * d.CAPEX_CC_Wp + b * d.CAPEX_CC_Wac + d.CAPEX_CC_Fijo
    : a * d.CAPEX_SC_Wp + b * d.CAPEX_SC_Wac + d.CAPEX_SC_Fijo;
  const ivabase = p.cont === 1
    ? a * d.IVA_CC_Wp + b * d.IVA_CC_Wac + d.IVA_CC_Fijo
    : a * d.IVA_SC_Wp + b * d.IVA_SC_Wac + d.IVA_SC_Fijo;
  // "Factor CAPEX efectivo" =IF(kfix>0, kfix*P*1000/kbase, fK)
  const fKeff = p.kfix > 0 ? p.kfix * p.P * 1000 / kbase : p.fK;
  // "Factor de escalación del CAPEX" =Fase_m1*(1+dK)^MAX(0,Anios_Precios-1)+(1-Fase_m1)*(1+dK)^MAX(0,Anios_Precios)
  const fEsc = fase * Math.pow(1 + p.dK, Math.max(0, d.Anios_Precios - 1)) + (1 - fase) * Math.pow(1 + p.dK, Math.max(0, d.Anios_Precios));
  // "CAPEX industrial sin IVA" =fKeff*fEsc*kbase
  const K = fKeff * fEsc * kbase;
  // "IVA CAPEX" =fKeff*fEsc*ivabase
  const IVA = fKeff * fEsc * ivabase;
  // "CAPEX depreciable" =K+(1-iva)*IVA
  const Kdep = K + (1 - p.iva) * IVA;
  // "Dep. equipos/año" =Kdep*(1-Pct_CAPEX_Civil)/Vida_Fiscal_Equipos
  const DepEq = Kdep * (1 - d.Pct_CAPEX_Civil) / VFE;
  // "Dep. civil/año" =Kdep*Pct_CAPEX_Civil/Vida_Fiscal_Civil
  const DepCiv = Kdep * d.Pct_CAPEX_Civil / VFC;
  // "Deducción adicional/año" =dedad*MIN(Kdep*Pct_Elegible_DedAd/Vida_Fiscal_Equipos, Tope_DedAd_Pct*Ingresos_SALELGI)
  const DedAd = p.dedad * Math.min(Kdep * i.Pct_Elegible_DedAd / VFE, i.Tope_DedAd_Pct * i.Ingresos_SALELGI);
  // "Terreno (costo total quien compra)" =Precio_Terreno_ha*fPre*ha*(1+Costos_Transaccion_Terreno_Pct)
  const Terr = i.Precio_Terreno_ha * p.fPre * ha * (1 + i.Costos_Transaccion_Terreno_Pct);
  // "Residual terreno neto (t=H)" = residG − MAX(0, residG − Terr)·IF(terr=1, Tasa_Efectiva, Tasa_Efectiva_Exergy)
  const residG = i.Precio_Terreno_ha * p.fPre * ha * i.Residual_Terreno_Pct * Math.pow(1 + i.Apreciacion_Terreno, H + 1);
  const Resid = residG - Math.max(0, residG - Terr) * (p.terr === 1 ? d.Tasa_Efectiva : i.Tasa_Efectiva_Exergy);
  // "OPEX año 1 SALELGI" =(Fee_OM_kWp+Seguro_kWp)*P+IF(terr=1,Predial_Terreno,Renta_Terreno_ha*ha)+Tributos_Locales
  const OPEX1 = (i.Fee_OM_kWp + i.Seguro_kWp) * p.P + (p.terr === 1 ? i.Predial_Terreno : i.Renta_Terreno_ha * ha) + i.Tributos_Locales;
  // "Subtotal EPC (base fee)" =K/(1+Fee_Gerencia_Pct)
  const Sub = K / (1 + i.Fee_Gerencia_Pct);
  // "Deuda" =deb*lev*(K+finT*terr*Terr)
  const D = p.deb * p.lev * (K + p.finT * p.terr * Terr);
  // "IDC" =D*rd*(Fase_m1+(1-Fase_m1)*IDC_Frac_Tramo0)*ncon/12
  const IDC = D * p.rd * (fase + (1 - fase) * i.IDC_Frac_Tramo0) * p.ncon / 12;
  // "Deuda total COD" =D+IDC
  const Dt = D + IDC;
  // "Nº cuotas" =MAX(1,plazo-gr)
  const n = Math.max(1, p.plazo - p.gr);
  // "Cuota" =IF(Dt>0, IF(rd=0, Dt/n, Dt*rd/(1-(1+rd)^(-n))), 0)
  const PMT = Dt > 0 ? (p.rd === 0 ? Dt / n : Dt * p.rd / (1 - Math.pow(1 + p.rd, -n))) : 0;
  // "Reemplazo de inversores (USD)" =IF(rep>0, Reemplazo_USD_Wac*AC*1000, 0)
  const Krep = p.rep > 0 ? i.Reemplazo_USD_Wac * AC * 1000 : 0;
  // "Desmantelamiento (USD)" =dec*K
  const Decom = p.dec * K;

  // ---- Blocks (27 rows each) -----------------------------------------------------------------------
  const nT = T_AXIS.length;
  const mk = () => new Array<number>(nT).fill(0);
  const E = mk(), Eval = mk(), Ahorro = mk(), OPEX = mk(), Peaje = mk(), EBITDA = mk(), Dep = mk();
  const Part_u = mk(), IR_u = mk(), TerrB = mk(), FCF_u = mk(), Cum_u = mk(), Int = mk(), Amort = mk();
  const Part_l = mk(), IR_l = mk(), CFADS = mk(), EQ = mk(), DF = mk(), Ux = mk(), Ix = mk(), Tx = mk(), Fx = mk(), Gx = mk();
  const KrepB = mk(), PoolU = mk(), PoolL = mk();
  const DSCR: (number | null)[] = new Array(nT).fill(null);

  // Ut = IF(t>=1, ug, 0) — taxable profit available for absorption in year t
  const Ut = (t: number) => (t >= 1 ? p.ug : 0);
  // dedad_t = IF(AND(t>=1, t<=Vida_Fiscal_Equipos), DedAd, 0)
  const dedadT = (t: number) => (t >= 1 && t <= VFE ? DedAd : 0);

  /** Bloque Part_u / Part_l:
   *  IF(part=1, IF(ug>=0, IF(base>=0, Tp*base, -Tp*MIN(-base, Ut)), IF(Escudo="Sí", Tp*base, MAX(0, Tp*base))), 0) */
  const partOf = (base: number, t: number): number => {
    if (p.part !== 1) return 0;
    if (p.ug >= 0) return base >= 0 ? Tp * base : -Tp * Math.min(-base, Ut(t));
    return escudo ? Tp * base : Math.max(0, Tp * base);
  };
  /** Bloque IR_u / IR_l with the loss pool (art. 11 LRTI, ≤ 25 % of the year's base):
   *  IF(ug>=0, IF(base>=0, Tir*(base-MIN(pool_prev, 0.25*(base+Ut))), -Tir*MIN(-base, Ut)), IF(Escudo="Sí", Tir*base, MAX(0, Tir*base)))
   *  Pool: IF(ug>=0, pool_prev + IF(base<0, -base-MIN(-base,Ut), -MIN(pool_prev, 0.25*(base+Ut))), 0) */
  const irOf = (base: number, t: number, poolPrev: number): { ir: number; pool: number } => {
    if (p.ug >= 0) {
      const U = Ut(t);
      const ir = base >= 0 ? Tir * (base - Math.min(poolPrev, 0.25 * (base + U))) : -Tir * Math.min(-base, U);
      const pool = poolPrev + (base < 0 ? -base - Math.min(-base, U) : -Math.min(poolPrev, 0.25 * (base + U)));
      return { ir, pool };
    }
    return { ir: escudo ? Tir * base : Math.max(0, Tir * base), pool: 0 };
  };

  for (let k = 0; k < nT; k++) {
    const t = T_AXIS[k];
    // Bloque E: =IF(OR(t<1,t>Horizonte),0, P/1000*frec*IF(scen=1,INDEX(Y_P50,1,MAX(1,t)),INDEX(Y_P90,1,MAX(1,t)))*disp*(1-deg)^(t-1))
    if (t < 1 || t > H) E[k] = 0;
    else {
      const yi = Math.max(1, t) - 1;
      if (yi >= Y.length) throw new Error(`Horizonte ${H} excede la serie de yield (${Y.length} años)`);
      E[k] = p.P / 1000 * frec * Y[yi] * p.disp * Math.pow(1 - p.deg, t - 1);
    }
    // Bloque Eval: =MIN(E, IF(t<1,0, Consumo_Anual*(1+Crecimiento_Consumo)^(t-1)/1000))
    Eval[k] = Math.min(E[k], t < 1 ? 0 : d.Consumo_Anual * Math.pow(1 + i.Crecimiento_Consumo, t - 1) / 1000);
    // Bloque Ahorro: =Eval*1000*Tarifa_Evitable*fT*(1+escT)^MAX(0,t-1)
    Ahorro[k] = Eval[k] * 1000 * d.Tarifa_Evitable * p.fT * Math.pow(1 + p.escT, Math.max(0, t - 1));
    // Bloque OPEX: =IF(OR(t<1,t>Horizonte),0, OPEX1*fO*(1+Escalacion_OPEX)^(t-1))
    OPEX[k] = t < 1 || t > H ? 0 : OPEX1 * p.fO * Math.pow(1 + i.Escalacion_OPEX, t - 1);
    // Bloque Peaje: =E*1000*pj*INDEX(Frac_Peaje,1,t+2)+IF(AND(t>=1,t<=Horizonte), AC*pkw*12*INDEX(Frac_Peaje,1,t+2), 0)
    const fp = d.Frac_Peaje[k];
    Peaje[k] = E[k] * 1000 * p.pj * fp + (t >= 1 && t <= H ? AC * p.pkw * 12 * fp : 0);
    // Bloque EBITDA: =Ahorro-OPEX-Peaje-IF(t=Horizonte, Decom, 0)
    EBITDA[k] = Ahorro[k] - OPEX[k] - Peaje[k] - (t === H ? Decom : 0);
    // Bloque Dep: =IF(AND(t>=1,t<=VFE),DepEq,0)+IF(AND(t>=1,t<=VFC,t<=H),DepCiv,0)
    //             +IF(AND(rep=1,RA<H,t>RA,t<=MIN(H,RA+VFE)), Krep/MIN(VFE,H-RA), 0)
    Dep[k] = (t >= 1 && t <= VFE ? DepEq : 0)
      + (t >= 1 && t <= VFC && t <= H ? DepCiv : 0)
      + (p.rep === 1 && RA < H && t > RA && t <= Math.min(H, RA + VFE) ? Krep / Math.min(VFE, H - RA) : 0);
    // Bloque Krep: =IF(AND(rep=1, t=Reemplazo_Anio), -Krep, 0)
    KrepB[k] = p.rep === 1 && t === RA ? -Krep : 0;
    // Bloque Terr: =IF(terr=1, IF(t=-1, -Terr, IF(t=Horizonte, Resid, 0)), 0)
    TerrB[k] = p.terr === 1 ? (t === -1 ? -Terr : t === H ? Resid : 0) : 0;

    // ---- unlevered tax (Part_u, IR_u, PoolU)
    Part_u[k] = partOf(EBITDA[k] - Dep[k], t);
    const baseU = EBITDA[k] - Dep[k] - Part_u[k] - dedadT(t);
    const ru = irOf(baseU, t, k === 0 ? 0 : PoolU[k - 1]);
    IR_u[k] = ru.ir; PoolU[k] = ru.pool;
    // Bloque FCF_u: =IF(t=-1, -(K+IVA)*Fase_m1, IF(t=0, -(K+IVA)*(1-Fase_m1)+iva*IVA*Fase_m1,
    //                  EBITDA-Part_u-IR_u+IF(t=1, iva*IVA*(1-Fase_m1), 0)+Krep)) + Terr
    FCF_u[k] = (t === -1
      ? -(K + IVA) * fase
      : t === 0
        ? -(K + IVA) * (1 - fase) + p.iva * IVA * fase
        : EBITDA[k] - Part_u[k] - IR_u[k] + (t === 1 ? p.iva * IVA * (1 - fase) : 0) + KrepB[k]) + TerrB[k];
    // Bloque Cum_u: running sum
    Cum_u[k] = k === 0 ? FCF_u[k] : Cum_u[k - 1] + FCF_u[k];

    // ---- debt service
    // Bloque Int: =IF(OR(D=0,t<1,t>plazo),0, IF(t<=gr, Dt*rd, IF(rd=0,0, rd*Dt*(1-((1+rd)^(t-gr-1)-1)/((1+rd)^n-1)))))
    if (D === 0 || t < 1 || t > p.plazo) Int[k] = 0;
    else if (t <= p.gr) Int[k] = Dt * p.rd;
    else Int[k] = p.rd === 0 ? 0 : p.rd * Dt * (1 - (Math.pow(1 + p.rd, t - p.gr - 1) - 1) / (Math.pow(1 + p.rd, n) - 1));
    // Bloque Amort: =IF(D=0,0, IF(plazo<=gr, IF(t=plazo, Dt, 0), IF(AND(t>gr,t<=plazo), PMT-Int, 0)))
    if (D === 0) Amort[k] = 0;
    else if (p.plazo <= p.gr) Amort[k] = t === p.plazo ? Dt : 0;
    else Amort[k] = t > p.gr && t <= p.plazo ? PMT - Int[k] : 0;

    // ---- levered tax (Part_l, IR_l, PoolL)
    Part_l[k] = partOf(EBITDA[k] - Dep[k] - Int[k], t);
    const baseL = EBITDA[k] - Dep[k] - Int[k] - Part_l[k] - dedadT(t);
    const rl = irOf(baseL, t, k === 0 ? 0 : PoolL[k - 1]);
    IR_l[k] = rl.ir; PoolL[k] = rl.pool;
    // Bloque CFADS: =IF(t<1,0, EBITDA-Part_l-IR_l+IF(t=1, iva*IVA*(1-Fase_m1),0)+IF(t>=1,Terr,0)+Krep)
    CFADS[k] = t < 1 ? 0 : EBITDA[k] - Part_l[k] - IR_l[k] + (t === 1 ? p.iva * IVA * (1 - fase) : 0) + (t >= 1 ? TerrB[k] : 0) + KrepB[k];
    // Bloque EQ: =IF(t=-1, FCF_u+D*Fase_m1, IF(t=0, FCF_u+D*(1-Fase_m1), CFADS-Int-Amort))
    EQ[k] = t === -1 ? FCF_u[k] + D * fase : t === 0 ? FCF_u[k] + D * (1 - fase) : CFADS[k] - Int[k] - Amort[k];
    // Bloque DSCR: =IF(Int+Amort>0, CFADS/(Int+Amort), "")
    DSCR[k] = Int[k] + Amort[k] > 0 ? CFADS[k] / (Int[k] + Amort[k]) : null;
    // Bloque DF: =IF(t<1, 0, 1/(1+Tasa_Descuento)^t)
    DF[k] = t < 1 ? 0 : 1 / Math.pow(1 + r, t);

    // ---- Exergy
    // Bloque Ux: =IF(t=-1, Fee*Sub*Fase_m1-CostoG*Sub*Fase_m1, IF(t=0, Fee*Sub*(1-Fase_m1)-CostoG*Sub*(1-Fase_m1), 0))
    //            +IF(AND(t>=1,t<=H), (1-terr)*(Renta_Terreno_ha*ha-Predial_Terreno)*g+(Fee_OM_kWp-Costo_OM_Exergy_kWp)*P*g, 0)
    //            -IF(AND(rep=2, t=Reemplazo_Anio), Krep, 0)      with g = (1+Escalacion_OPEX)^(t-1)
    const g = Math.pow(1 + i.Escalacion_OPEX, t - 1);
    let ux = t === -1
      ? i.Fee_Gerencia_Pct * Sub * fase - i.Costo_Gerencia_Pct * Sub * fase
      : t === 0
        ? i.Fee_Gerencia_Pct * Sub * (1 - fase) - i.Costo_Gerencia_Pct * Sub * (1 - fase)
        : 0;
    ux += t >= 1 && t <= H ? (1 - p.terr) * (i.Renta_Terreno_ha * ha - i.Predial_Terreno) * g + (i.Fee_OM_kWp - i.Costo_OM_Exergy_kWp) * p.P * g : 0;
    ux -= p.rep === 2 && t === RA ? Krep : 0;
    Ux[k] = ux;
    // Bloque Ix: =-MAX(0,Ux)*Tasa_Efectiva_Exergy
    Ix[k] = -Math.max(0, Ux[k]) * i.Tasa_Efectiva_Exergy;
    // Bloque Tx: =IF(terr=1, 0, IF(t=-1, -Terr, IF(t=Horizonte, Resid, 0)))
    Tx[k] = p.terr === 1 ? 0 : t === -1 ? -Terr : t === H ? Resid : 0;
    // Bloque Fx: =Ux+Ix+Tx ; Bloque Gx: =FCF_u+Fx
    Fx[k] = Ux[k] + Ix[k] + Tx[k];
    Gx[k] = FCF_u[k] + Fx[k];
  }

  // ---- Outputs (Motor rows 57–72) -------------------------------------------------------------------
  const i1 = tIndex(1), i25 = tIndex(T_MAX) + 1; // slice [t=1 … t=25]
  const naIf = (v: number | null): OutputValue => (v === null ? "n/a" : v);
  // "TIR proyecto" =IFERROR(IRR(FCF_u), "n/a")
  const TIR = naIf(irr(FCF_u));
  // "VAN proyecto" =FCF_u[-1]*(1+Tasa_Descuento)+FCF_u[0]+NPV(Tasa_Descuento, FCF_u[1..25])
  const VAN = vanMotor(r, FCF_u);
  // "Payback simple" (robust, last crossing)
  const PB = paybackLastCrossing(Cum_u, FCF_u);
  // "LCOE $/MWh" =(K+SUMPRODUCT(OPEX[1..25]+Peaje[1..25], DF[1..25]))/SUMPRODUCT(E[1..25], DF[1..25])
  let num = 0, den = 0;
  for (let k = i1; k < i25; k++) { num += (OPEX[k] + Peaje[k]) * DF[k]; den += E[k] * DF[k]; }
  const LCOE = (K + num) / den;
  // "TIR equity" =IF(D>0, IFERROR(IRR(EQ, 0.02), "n/a"), "n/a")
  const TIR_eq: OutputValue = D > 0 ? naIf(irr(EQ, 0.02)) : "n/a";
  // "VAN equity" =EQ[-1]*(1+req)+EQ[0]+NPV(req, EQ[1..25])
  const VAN_eq = vanMotor(p.req, EQ);
  // "DSCR mín" =IF(D>0, MIN(DSCR[1..25]), "n/a") ; "DSCR prom" =IF(D>0, AVERAGE(DSCR[1..25]), "n/a")
  let DSCR_min: OutputValue = "n/a", DSCR_avg: OutputValue = "n/a";
  if (D > 0) {
    const vals: number[] = [];
    for (let k = i1; k < i25; k++) { const v = DSCR[k]; if (v !== null) vals.push(v); }
    if (vals.length > 0) {
      let mn = Infinity, s = 0;
      for (const v of vals) { if (v < mn) mn = v; s += v; }
      DSCR_min = mn; DSCR_avg = s / vals.length;
    } else {
      DSCR_min = 0;        // Excel MIN over a range of "" → 0
      DSCR_avg = "n/a";    // Excel AVERAGE over "" → #DIV/0! (rendered here as "n/a")
    }
  }
  // "Ahorro año 1" =Ahorro[1]
  const Ahorro1 = Ahorro[i1];
  // "Aporte equity" =-(EQ[-1]+EQ[0])
  const Aporte_eq = -(EQ[0] + EQ[1]);
  // "VAN Exergy" =Fx[-1]*(1+Tasa_Descuento)+Fx[0]+NPV(Tasa_Descuento, Fx[1..25])
  const VAN_X = vanMotor(r, Fx);
  // "TIR grupo" =IFERROR(IRR(Gx), "n/a")
  const TIR_G = naIf(irr(Gx));
  // "Energía año 1 (MWh)" =E[1]
  const E1 = E[i1];
  // "Energía no reconocida Σ (MWh)" =SUM(E[1..25])-SUM(Eval[1..25])
  let sE = 0, sEv = 0;
  for (let k = i1; k < i25; k++) { sE += E[k]; sEv += Eval[k]; }
  const NoRec = sE - sEv;
  // "Cobertura año 1" =IF(Consumo_Anual>0, E[1]*1000/Consumo_Anual, 0)
  const Cob = d.Consumo_Anual > 0 ? E[i1] * 1000 / d.Consumo_Anual : 0;
  // "Nominal Exergy Σ" =SUM(Fx)
  let Nominal_X = 0;
  for (const v of Fx) Nominal_X += v;

  const scalars = {
    [SCALAR_LABELS.frec]: frec, [SCALAR_LABELS.AC]: AC, [SCALAR_LABELS.ha]: ha, [SCALAR_LABELS.K]: K, [SCALAR_LABELS.IVA]: IVA,
    [SCALAR_LABELS.Kdep]: Kdep, [SCALAR_LABELS.DepEq]: DepEq, [SCALAR_LABELS.DepCiv]: DepCiv, [SCALAR_LABELS.DedAd]: DedAd,
    [SCALAR_LABELS.Terr]: Terr, [SCALAR_LABELS.Resid]: Resid, [SCALAR_LABELS.OPEX1]: OPEX1, [SCALAR_LABELS.Sub]: Sub,
    [SCALAR_LABELS.D]: D, [SCALAR_LABELS.IDC]: IDC, [SCALAR_LABELS.Dt]: Dt, [SCALAR_LABELS.n]: n, [SCALAR_LABELS.PMT]: PMT,
    [SCALAR_LABELS.fKeff]: fKeff, [SCALAR_LABELS.fEsc]: fEsc, [SCALAR_LABELS.Krep]: Krep, [SCALAR_LABELS.Decom]: Decom,
  } as Record<ScalarLabel, number>;

  const outputs = {
    [OUTPUT_LABELS.TIR]: TIR, [OUTPUT_LABELS.VAN]: VAN, [OUTPUT_LABELS.PB]: PB, [OUTPUT_LABELS.LCOE]: LCOE,
    [OUTPUT_LABELS.TIR_eq]: TIR_eq, [OUTPUT_LABELS.VAN_eq]: VAN_eq, [OUTPUT_LABELS.DSCR_min]: DSCR_min, [OUTPUT_LABELS.DSCR_avg]: DSCR_avg,
    [OUTPUT_LABELS.Ahorro1]: Ahorro1, [OUTPUT_LABELS.Aporte_eq]: Aporte_eq, [OUTPUT_LABELS.VAN_X]: VAN_X, [OUTPUT_LABELS.TIR_G]: TIR_G,
    [OUTPUT_LABELS.E1]: E1, [OUTPUT_LABELS.NoRec]: NoRec, [OUTPUT_LABELS.Cob]: Cob, [OUTPUT_LABELS.Nominal_X]: Nominal_X,
  } as Record<OutputLabel, OutputValue>;

  const blocks: Record<BlockName, (number | null)[]> = {
    E, Eval, Ahorro, OPEX, Peaje, EBITDA, Dep, Part_u, IR_u, Terr: TerrB, FCF_u, Cum_u, Int, Amort, Part_l, IR_l, CFADS, EQ, DSCR, DF,
    Ux, Ix, Tx, Fx, Gx, Krep: KrepB, PoolU, PoolL,
  };
  return { scalars, outputs, blocks };
}
