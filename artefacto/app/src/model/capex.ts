/**
 * 05_CAPEX — tabla de rubros (filas 7–24) para cualquier caso del Motor.
 * Misma aritmética que la hoja (columnas V, F, H, J, K, L, M, N, W, P, Q) con el Factor_Caso del caso
 * (= «Factor CAPEX efectivo» × «Factor de escalación» del Motor) y su parámetro de contrato de inversión.
 * Verificado contra el libro: para el Custom, N19 ≡ CAPEX_Total y P19 ≡ IVA_Total (test-live.ts).
 */
import type { CaseParams, Derived, Inputs } from "@/engine";

export interface RubroRow {
  n: number;
  nombre: string;
  /** D · costo base a 5 MWp */
  base: number;
  /** E · % compartido */
  pctComp: number;
  /** V · cargado a GPM (aux., f = 1) */
  cargado: number;
  /** F · costo del caso */
  costo: number;
  /** G · % exterior */
  pctExt: number;
  /** H · valor exterior */
  exterior: number;
  /** I · arancel % */
  arancelPct: number;
  /** J · arancel USD */
  arancel: number;
  /** K · FODINFA */
  fodinfa: number;
  /** L · ISD */
  isd: number;
  /** M · arancel + ISD aplicado (0 con contrato de inversión) */
  arancelIsd: number;
  /** N · capitalizable sin IVA */
  capitalizable: number;
  /** O · IVA % */
  ivaPct: number;
  /** P · IVA USD */
  iva: number;
  /** Q · $/Wp */
  usdWp: number;
  /** drivers */
  drvWp: number;
  drvWac: number;
  drvFijo: number;
}

export interface CapexTable {
  rubros: RubroRow[];
  /** fila 16 */
  contingencia: { capitalizable: number; iva: number; usdWp: number };
  /** fila 17 · subtotal EPC = valor del proyecto (base del fee) */
  subtotal: { capitalizable: number; iva: number; usdWp: number };
  /** fila 18 · gerencia Exergy */
  gerencia: { capitalizable: number; iva: number; usdWp: number; pct: number };
  /** fila 19 · total industrial sin IVA */
  total: { capitalizable: number; iva: number; usdWp: number };
  /** fila 20 */
  total_con_iva: number;
  /** fila 21 · terreno comprado por quien compra en el caso (0 si Exergy) */
  terreno: number;
  /** fila 22 */
  total_con_terreno: number;
  /** fila 23 · aranceles + ISD dentro del total (M) y FODINFA aparte (K) */
  aranceles_isd: number;
  fodinfa: number;
  /** fila 24 · % del CAPEX industrial en obra civil */
  pct_civil: number;
  /** factores del caso */
  factor_caso: number;
  contrato: boolean;
  potencia_dc: number;
}

/** Factor_Caso del caso: kfix > 0 → kfix × P × 1000 / bottom-up@f1, si no fK; × factor de escalación (mismo D30 de 05). */
/** Escalas del caso (01!C147/C148 con la potencia del caso): (P/Pref)^(1−ε) y (AC/ACref)^(1−ε). */
export function escalas(i: Inputs, p: CaseParams): { escWp: number; escWac: number } {
  const e = 1 - i.Exponente_Escala;
  return { escWp: Math.pow(p.P / i.Potencia_Ref, e), escWac: Math.pow((p.P / p.ratio) / (i.Potencia_Ref / i.Ratio_Ref), e) };
}

export function factorCaso(i: Inputs, d: Derived, p: CaseParams): number {
  const { escWp, escWac } = escalas(i, p);
  const cont = p.cont === 1;
  const kbase = cont
    ? escWp * d.CAPEX_CC_Wp + escWac * d.CAPEX_CC_Wac + d.CAPEX_CC_Fijo
    : escWp * d.CAPEX_SC_Wp + escWac * d.CAPEX_SC_Wac + d.CAPEX_SC_Fijo;
  const fKeff = p.kfix > 0 ? (p.kfix * p.P * 1000) / kbase : p.fK;
  const fEsc = i.Fase_m1 * Math.pow(1 + p.dK, Math.max(0, d.Anios_Precios - 1)) + (1 - i.Fase_m1) * Math.pow(1 + p.dK, Math.max(0, d.Anios_Precios));
  return fKeff * fEsc;
}

export function capexTable(i: Inputs, d: Derived, p: CaseParams): CapexTable {
  const { escWp, escWac } = escalas(i, p);
  const cont = p.cont === 1;
  const fc = factorCaso(i, d, p);
  const P1000 = p.P * 1000;
  const rows: RubroRow[] = i.rubros.map((rb, k) => {
    const V = rb.costo * (1 - rb.pctComp * (1 - i.Asignacion_Compartida));
    const F = V * fc * (rb.drvWp * escWp + rb.drvWac * escWac + rb.drvFijo);
    const H = F * rb.pctExt;
    const J = H * rb.arancel;
    const K = H * i.FODINFA_Pct;
    const L = H * i.ISD_Pct;
    const M = cont ? 0 : J + L;
    const N = F + K + M;
    const W = F + K + (cont ? 0 : J);
    const Pv = W * rb.iva;
    return {
      n: k + 1, nombre: rb.nombre, base: rb.costo, pctComp: rb.pctComp, cargado: V, costo: F, pctExt: rb.pctExt, exterior: H,
      arancelPct: rb.arancel, arancel: J, fodinfa: K, isd: L, arancelIsd: M, capitalizable: N, ivaPct: rb.iva, iva: Pv, usdWp: N / P1000,
      drvWp: rb.drvWp, drvWac: rb.drvWac, drvFijo: rb.drvFijo,
    };
  });
  const sN = rows.reduce((s, r) => s + r.capitalizable, 0);
  const sP = rows.reduce((s, r) => s + r.iva, 0);
  const N16 = i.Contingencia_Pct * sN;
  const P16 = N16 * i.Tasa_IVA * i.Contingencia_Frac_IVA;
  const N17 = sN + N16, P17 = sP + P16;
  const N18 = i.Fee_Gerencia_Pct * N17, P18 = N18 * i.iva_fee;
  const N19 = N17 + N18, P19 = P17 + P18;
  const terr = p.terr === 1 ? i.Precio_Terreno_ha * (p.P / 1000) / i.Densidad_MWp_ha * (1 + i.Costos_Transaccion_Terreno_Pct) * p.fPre : 0;
  return {
    rubros: rows,
    contingencia: { capitalizable: N16, iva: P16, usdWp: N16 / P1000 },
    subtotal: { capitalizable: N17, iva: P17, usdWp: N17 / P1000 },
    gerencia: { capitalizable: N18, iva: P18, usdWp: N18 / P1000, pct: i.Fee_Gerencia_Pct },
    total: { capitalizable: N19, iva: P19, usdWp: N19 / P1000 },
    total_con_iva: N19 + P19,
    terreno: terr,
    total_con_terreno: N19 + terr,
    aranceles_isd: rows.reduce((s, r) => s + r.arancelIsd, 0),
    fodinfa: rows.reduce((s, r) => s + r.fodinfa, 0),
    pct_civil: N19 > 0 ? rows[5].capitalizable / N19 : 0,
    factor_caso: fc,
    contrato: cont,
    potencia_dc: p.P,
  };
}
