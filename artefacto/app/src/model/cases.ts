/**
 * Índice de casos del Motor (mismo orden que build_content.build_cases() y que Motor_Sens):
 * 0–3 Custom · Conservador · Base · Favorable · 4–5 P50/P90 · 6–17 tornado v2.0 · 18 PISO · 19–43 matriz CAPEX × tarifa ·
 * 44–58 tasa × plazo · 59–62 apalancamiento · 63 terreno alt. · 64–67 potencia · 68–72 ratio · 73–77 AC fija · 78–92 deuda máxima ·
 * 93–98 precio del terreno · 99–104 tornado ronda 2 (+ «Sin deducción adicional» v3.1) · 105–110 puente BR0–BR5.
 */
import type { CaseId } from "@/lib/views";

export const CASE_X = 0, CASE_C = 1, CASE_B = 2, CASE_F = 3;
export const CASE_P50 = 4, CASE_P90 = 5;
export const T_CAPEX_DN = 6, T_CAPEX_UP = 7, T_TAR_DN = 8, T_TAR_UP = 9, T_ENERGIA = 10, T_OPEX_UP = 11, T_OPEX_DN = 12,
  T_PEAJE = 13, T_ESC = 14, T_PART = 15, T_IVA = 16, T_CONTRATO = 17;
export const CASE_PISO = 18;
export const MAT_START = 19;      // 5 × 5: fila i (CAPEX) × columna j (tarifa) → MAT_START + i*5 + j
export const EQ_START = 44;       // 5 tasas × 3 plazos → EQ_START + i*3 + j
export const LEV_START = 59;      // 4
export const CASE_TERR_ALT = 63;
export const SWEEP_P_START = 64, SWEEP_R_START = 68, SWEEP_A_START = 73, DM_START = 78, TS_START = 93, TX_START = 96;
export const T_DISP = 99, T_ESCK = 100, T_PKW = 101, T_UG = 102, T_REP = 103, T_DEDAD = 104;
export const BR0 = 105, BR5 = 110;
export const N_CASES = 111;

export const CASE_INDEX: Record<CaseId, number> = { custom: CASE_X, conservador: CASE_C, base: CASE_B, favorable: CASE_F };

/** Nombres esperados en posiciones clave (comprobación en tiempo de carga: si el motor cambia el orden, el chip de autocomprobación lo avisa). */
export const EXPECTED_NAMES: Record<number, string> = {
  [CASE_X]: "Custom",
  [CASE_C]: "Conservador",
  [CASE_B]: "Base",
  [CASE_F]: "Favorable",
  [CASE_PISO]: "PISO",
  [CASE_TERR_ALT]: "Terreno alt.",
  [T_DEDAD]: "Sin deducción adicional",
  [BR0]: "BR0 v2.0",
  [BR5]: "BR5 ≡ Base",
};

export interface TornadoDef {
  /** identificador estable (selección en la vista) */
  id: string;
  /** índice de la barra en 10 §B = book.sens.tornado[k] (etiqueta larga, corta y nota (k+1) son textos vivos del libro) */
  k: number;
  /** caso «bajo» (lado izquierdo) */
  lo: number;
  /** caso «alto» (lado derecho); null = barra de un solo lado */
  hi: number | null;
}

/**
 * Las 15 barras del tornado en el orden de la tabla de 10 §B (el gráfico las ordena por amplitud). Los casos lo/hi son los
 * de book.sens.tornado (misma fuente que el Excel); los textos se toman del libro en vivo: `m.live(BOOK.sens.tornado_short[k])`.
 */
export const TORNADO_IDS = ["tarifa", "capex", "esc", "peaje", "energia", "opex", "iva", "part", "contrato", "disp", "esck", "pkw", "ug", "rep", "dedad"] as const;
export function tornadoDefs(book: { sens: { tornado: { lo: number; hi: number | null }[] } }): TornadoDef[] {
  return book.sens.tornado.map((t, k) => ({ id: TORNADO_IDS[k] ?? `barra${k + 1}`, k, lo: t.lo, hi: t.hi }));
}
