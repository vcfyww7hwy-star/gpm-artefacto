/**
 * Resolutor de nombres definidos del libro → valores vivos del motor.
 *
 * Orden de resolución: entradas (01) → derivados (04/05, bloque B del Custom) → KPI por caso (X_/C_/B_/F_/P50_/P90_)
 * → alias del Custom (TIR_Proyecto, CAPEX_Total, …) → magnitudes calculadas aquí (Anio_DSCR_Min, Deuda_Max_Plazo*, TIR_Exergy,
 * Carga_Exergy, Aranceles_ISD, …) → referencias 'Motor_Sens'!Celda (columna = caso, fila = parámetro/escalar/salida/bloque)
 * → valores «congelados» del libro (controles, estados, conteos que sólo existen en Excel), marcados como tales.
 *
 * Toda resolución congelada queda registrada en `frozenUsed` para que la vista pueda señalar «valor del libro (08-sep-2026)».
 */
import {
  BLOCK_NAMES, irr, OUTPUT_LABELS, PARAM_KEYS, SCALAR_LABELS, T_AXIS,
  type ComputedCase, type Derived, type Inputs, type OutputKey, type ScalarKey,
} from "@/engine";
import { opexLines } from "@/model/opex";
import { capexTable } from "@/model/capex";
import { CASE_B, CASE_C, CASE_F, CASE_P50, CASE_P90, CASE_X, DM_START } from "@/model/cases";
import { type EvalCtx, type Locale, type Value, XlError } from "@/model/formula";

export interface ModelSnapshot {
  inputs: Inputs;
  derived: Derived;
  cases: ComputedCase[];
  /** entradas de 01_Supuestos que el Motor no usa (Capacidad_Alimentador_kW, Tasa_Desc_Alt1, umbrales, tolerancias…) */
  extras?: Record<string, Value>;
}

export interface BookFrozen {
  frozen: Record<string, Value>;
  calc_names: Record<string, Value>;
}

const CASE_PREFIX: Record<string, number> = { X: CASE_X, C: CASE_C, B: CASE_B, F: CASE_F, P50: CASE_P50, P90: CASE_P90 };
const KPI_SUFFIX: Record<string, OutputKey> = {
  TIR: "TIR", VAN: "VAN", PB: "PB", LCOE: "LCOE", TIReq: "TIR_eq", VANeq: "VAN_eq", DSCR: "DSCR_min",
  Ahorro1: "Ahorro1", Aporte: "Aporte_eq", VANX: "VAN_X", TIRG: "TIR_G", E1: "E1",
};
/** alias del Custom (hojas 04–09) → salida del Motor */
const CUSTOM_OUTPUT: Record<string, OutputKey> = {
  TIR_Proyecto: "TIR", VAN_Proyecto: "VAN", Payback_Simple: "PB", LCOE: "LCOE", TIR_Equity: "TIR_eq", VAN_Equity: "VAN_eq",
  DSCR_Min: "DSCR_min", DSCR_Prom: "DSCR_avg", Ahorro_Anio1: "Ahorro1", Aporte_Equity: "Aporte_eq", VAN_Exergy: "VAN_X",
  TIR_Grupo: "TIR_G", Nominal_Exergy: "Nominal_X", Cobertura_Anual: "Cob",
};
/** alias del Custom → escalar del Motor */
const CUSTOM_SCALAR: Record<string, ScalarKey> = {
  CAPEX_Total: "K", IVA_Total: "IVA", CAPEX_Depreciable: "Kdep", DedAd_Anual: "DedAd", OPEX_Anio1: "OPEX1", Subtotal_EPC: "Sub",
  Deuda_Monto: "D", IDC: "IDC", Deuda_Total: "Dt", Cuota: "PMT", Desmantelamiento_USD: "Decom",
};

const outVal = (c: ComputedCase, k: OutputKey): Value => {
  const v = c.result.outputs[OUTPUT_LABELS[k]];
  return typeof v === "number" ? v : v; // "n/a" / "no cruza" viajan como texto, igual que en Excel
};
const scal = (c: ComputedCase, k: ScalarKey): number => c.result.scalars[SCALAR_LABELS[k]];

/** Columna Excel («B», «DB») → índice de caso del Motor (B = 0). */
export function colToCase(col: string): number {
  let n = 0;
  for (const ch of col) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n - 2;
}

/** Fila del Motor → descriptor (parámetro / escalar / salida / bloque·t). */
export function motorRow(row: number): { kind: "param"; key: string } | { kind: "scalar"; key: ScalarKey } | { kind: "output"; key: OutputKey } | { kind: "block"; block: string; t: number } | null {
  if (row >= 5 && row <= 34) return { kind: "param", key: PARAM_KEYS[row - 5] };
  const scalarKeys = Object.keys(SCALAR_LABELS) as ScalarKey[];
  if (row >= 35 && row <= 56) return { kind: "scalar", key: scalarKeys[row - 35] };
  const outKeys = Object.keys(OUTPUT_LABELS) as OutputKey[];
  if (row >= 57 && row <= 72) return { kind: "output", key: outKeys[row - 57] };
  if (row >= 76) {
    const b = Math.floor((row - 76) / 28), off = (row - 76) % 28;
    if (off <= 26 && b < BLOCK_NAMES.length) return { kind: "block", block: BLOCK_NAMES[b], t: T_AXIS[off] };
  }
  return null;
}

export interface Resolver {
  ctx: EvalCtx;
  /** nombres que se resolvieron con el valor congelado del libro (no calculados por el motor) */
  frozenUsed: Set<string>;
}

export function createResolver(m: ModelSnapshot, book: BookFrozen, locale: Locale = "es-EC"): Resolver {
  const frozenUsed = new Set<string>();
  const i = m.inputs, d = m.derived, cases = m.cases;
  const X = cases[CASE_X];
  const cache = new Map<string, Value>();

  const computed: Record<string, () => Value> = {
    Tarifa_MWh: () => d.Tarifa_Evitable * 1000,
    Ahorro_kWh: () => {
      const lcoe = outVal(X, "LCOE");
      const t = d.Tarifa_Evitable * 1000;
      return t > 0 && typeof lcoe === "number" ? 1 - lcoe / t : "n/a";
    },
    Anio_DSCR_Min: () => {
      if (scal(X, "D") <= 0) return "—";
      const dscr = X.result.blocks.DSCR;
      let best: number | null = null, bt: number | string = "—";
      dscr.forEach((v, k) => { if (typeof v === "number" && T_AXIS[k] >= 1 && (best === null || v < best)) { best = v; bt = T_AXIS[k]; } });
      return bt;
    },
    Terreno_SALELGI: () => (i.Comprador_Terreno === "SALELGI" ? scal(X, "Terr") : 0),
    Fee_Gerencia_USD: () => i.Fee_Gerencia_Pct * scal(X, "Sub"),
    Factor_Caso: () => scal(X, "fKeff") * scal(X, "fEsc"),
    Factor_Escalacion: () => scal(X, "fEsc"),
    Reemplazo_USD: () => d.Reemplazo_USD,
    TIR_Exergy: () => {
      const fx = X.result.blocks.Fx.map((v) => (typeof v === "number" ? v : 0));
      const r = irr(fx);
      return r === null ? "n/a" : r;
    },
    Carga_Exergy: () => {
      const a1 = outVal(X, "Ahorro1");
      if (typeof a1 !== "number" || a1 <= 0) return 0;
      const l = opexLines(i, d, X.params, 1);
      return (l.fee + l.arriendo) / a1;
    },
    Aranceles_ISD: () => capexTable(i, d, X.params).aranceles_isd,
    Mes_COD_Cron: () => i.Meses_Construccion,
    N_Custom_vs_Base: () => {
      // bloque B: Custom (col. 0) frente a la definición Base (col. 2) — misma lectura que 01!C136 para las 8 filas del bloque
      const keys = ["Esc_Energia", "Esc_Factor_CAPEX", "Esc_CAPEX_Fijo_Wp", "Esc_Factor_OPEX", "Esc_Peaje", "Esc_EscTarifa", "Esc_Disponibilidad", "Esc_Escalacion_CAPEX"] as const;
      let n = 0;
      for (const k of keys) { const arr = i[k] as unknown[]; if (String(arr[0] ?? "") !== String(arr[2] ?? "")) n++; }
      return n;
    },
    Estado_Custom: () => {
      const n = computed.N_Custom_vs_Base() as number;
      return n === 0 ? "● Custom = Base" : `▲ Custom ≠ Base en ${n} entrada(s)`;
    },
  };
  // Deuda_Max_Plazo{1,2,3}: 10 §H (fila por plazo, columnas = Sweep_Lev): apalancamiento máximo con DSCR mín ≥ objetivo,
  // interpolado linealmente entre el último punto que cumple y el siguiente (misma fórmula que H288:H290 del libro)
  for (let j = 0; j < 3; j++) {
    computed[`Deuda_Max_Plazo${j + 1}`] = () => {
      const lev = i.Sweep_Lev, obj = i.DSCR_Objetivo;
      const dscr = lev.map((_, k) => { const c = cases[DM_START + j * lev.length + k]; const v = c ? outVal(c, "DSCR_min") : null; return typeof v === "number" ? v : NaN; });
      const count = dscr.filter((v) => v >= obj).length;
      if (count === 0) return 0;
      if (count >= lev.length) return lev[lev.length - 1];
      const a = dscr[count - 1], b = dscr[count];
      return lev[count - 1] + (lev[count] - lev[count - 1]) * (a - obj) / (a - b);
    };
  }

  const resolve = (n: string): Value => {
    if (n in i) return (i as unknown as Record<string, Value>)[n];
    if (n in d) return (d as unknown as Record<string, Value>)[n];
    if (m.extras && n in m.extras) return m.extras[n];
    const m1 = /^(X|C|B|F|P50|P90)_([A-Za-z0-9]+)$/.exec(n);
    if (m1 && m1[2] in KPI_SUFFIX) return outVal(cases[CASE_PREFIX[m1[1]]], KPI_SUFFIX[m1[2]]);
    if (n in CUSTOM_OUTPUT) return outVal(X, CUSTOM_OUTPUT[n]);
    if (n in CUSTOM_SCALAR) return scal(X, CUSTOM_SCALAR[n]);
    if (n in computed) return computed[n]();
    if (n in book.frozen) { frozenUsed.add(n); return book.frozen[n]; }
    if (n in book.calc_names) { frozenUsed.add(n); return book.calc_names[n]; }
    throw new XlError("#NAME?", n);
  };

  const ctx: EvalCtx = {
    locale,
    name(n) {
      if (cache.has(n)) return cache.get(n)!;
      const v = resolve(n);
      cache.set(n, v);
      return v;
    },
    ref(sheet, cell) {
      const mm = /^([A-Z]+)(\d+)$/.exec(cell);
      if (!mm) throw new XlError("#REF!", `${sheet}!${cell}`);
      if (sheet === "Motor_Sens") {
        const c = cases[colToCase(mm[1])];
        const r = motorRow(Number(mm[2]));
        if (!c || !r) throw new XlError("#REF!", `${sheet}!${cell}`);
        if (r.kind === "output") return outVal(c, r.key);
        if (r.kind === "scalar") return scal(c, r.key);
        if (r.kind === "param") return (c.params as unknown as Record<string, number>)[r.key];
        const v = c.result.blocks[r.block as keyof typeof c.result.blocks][r.t - T_AXIS[0]];
        return v === null ? "" : v;
      }
      if (sheet === "04_Energia" && cell === "F93") return outVal(X, "E1");
      if (sheet === "04_Energia" && cell === "F97") return outVal(X, "NoRec");
      throw new XlError("#REF!", `${sheet}!${cell}`);
    },
  };
  return { ctx, frozenUsed };
}
