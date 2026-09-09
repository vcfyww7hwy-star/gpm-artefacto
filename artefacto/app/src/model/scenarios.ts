/**
 * Escenarios: un escenario es un «parche» sobre las entradas del libro (sólo las que difieren) más las extras,
 * con una etiqueta y un resumen de KPI del Custom al guardarlo. Se guardan en la base del artefacto (`db`, sólo
 * organización) o se aplican en la sesión (presets del memo de 03). El parche siempre se aplica sobre la v3.1
 * entregada (BASELINE), de modo que un escenario sigue siendo legible aunque cambie el libro base: `base` lo registra.
 */
import { computeAll, edate, formatISODate, OUTPUT_LABELS, parseISODate, type ComputedCase, type Inputs } from "@/engine";
import type { Value } from "@/model/formula";

export interface ScenarioKpi {
  TIR: number | null;
  VAN: number | null;
  TIR_eq: number | null;
  DSCR_min: number | null;
}

export interface Scenario {
  id: string;
  nombre: string;
  nota: string;
  /** versión del libro sobre la que se definió el parche */
  base: string;
  creado: string;
  actualizado: string;
  /** G5 · borrado lógico (D-V2-5): fecha ISO en que se envió a la papelera; ausente = activo */
  eliminado?: string | null;
  /** entradas del Motor que difieren del libro */
  patch: Partial<Inputs>;
  /** entradas informativas (extras) que difieren del libro */
  extras: Record<string, Value>;
  /** KPI del Custom al guardar (para la lista; se recalculan al cargar) */
  kpi: ScenarioKpi;
  /** preset del libro (memo de 03): no se guarda en la base */
  preset?: true;
}

export const SCENARIOS_COLLECTION = "escenarios";

function sameValue(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

/** Parche = entradas distintas del libro. */
export function diffInputs(inputs: Inputs, baseline: Inputs): Partial<Inputs> {
  const out: Partial<Inputs> = {};
  for (const k of Object.keys(baseline) as (keyof Inputs)[]) {
    if (!sameValue(inputs[k], baseline[k])) (out as unknown as Record<string, unknown>)[k] = inputs[k];
  }
  return out;
}
export function diffExtras(extras: Record<string, Value>, baseline: Record<string, Value>): Record<string, Value> {
  const out: Record<string, Value> = {};
  for (const k of Object.keys(baseline)) if (!sameValue(extras[k], baseline[k])) out[k] = extras[k];
  return out;
}

export function applyScenario(baseline: Inputs, baseExtras: Record<string, Value>, s: Pick<Scenario, "patch" | "extras">): { inputs: Inputs; extras: Record<string, Value> } {
  // sólo claves conocidas del libro: un parche de otra versión no introduce entradas desconocidas
  const inputs: Inputs = { ...baseline };
  const target = inputs as unknown as Record<string, unknown>;
  for (const k of Object.keys(s.patch ?? {}) as (keyof Inputs)[]) if (k in baseline) target[k] = s.patch[k];
  const extras = { ...baseExtras };
  for (const k of Object.keys(s.extras ?? {})) if (k in baseExtras) extras[k] = s.extras[k];
  return { inputs, extras };
}

export function kpiOf(cases: ComputedCase[]): ScenarioKpi {
  const o = cases[0].result.outputs;
  const n = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);
  return { TIR: n(o[OUTPUT_LABELS.TIR]), VAN: n(o[OUTPUT_LABELS.VAN]), TIR_eq: n(o[OUTPUT_LABELS.TIR_eq]), DSCR_min: n(o[OUTPUT_LABELS.DSCR_min]) };
}

export function computeScenario(baseline: Inputs, s: Pick<Scenario, "patch" | "extras">): ComputedCase[] {
  return computeAll(applyScenario(baseline, {}, s).inputs).cases;
}

/** Etiquetas cortas de las entradas para listar las diferencias de un escenario. */
export function describePatch(patch: Partial<Inputs>, extras: Record<string, Value>): string[] {
  const out: string[] = [];
  for (const [k, v] of Object.entries(patch)) out.push(`${k} → ${fmtValue(v)}`);
  for (const [k, v] of Object.entries(extras)) out.push(`${k} → ${fmtValue(v)}`);
  return out;
}
function fmtValue(v: unknown): string {
  if (Array.isArray(v)) return `[${v.map((x) => (x === null ? "—" : String(x))).join(" · ")}]`;
  if (v === null || v === undefined) return "—";
  return String(v);
}

/** Desplaza el cronograma k meses: más meses de construcción (IDC) y COD k meses después (misma definición que el memo de 03). */
export function shiftSchedule(i: Inputs, months: number): Partial<Inputs> {
  return { Meses_Construccion: i.Meses_Construccion + months, Fecha_COD: formatISODate(edate(parseISODate(i.Fecha_COD), months)) };
}

/**
 * Presets del libro (memo estático de 03_Tramites, «sombra Python ≡ Motor, 08-sep-2026»): reproducidos por el motor
 * (verificado: +12 → TIR accionista 16,45 %, DSCR 0,701; +3 → 17,99 %, 0,723 en el Custom).
 */
export function presetScenarios(baseline: Inputs): Scenario[] {
  const now = "";
  return [
    {
      id: "preset-licencia-cod-3",
      nombre: "Caso Conservador ambiental (Licencia en vez de Registro): COD +3 meses",
      nota: "Memo de 03: RC-04′ Licencia Ambiental meses 3–11 y RC-05 participación ciudadana → COD +3 meses (24). El costo (≈ USD 70.000) no cambia el CAPEX del Motor (rubro 9 fijo).",
      base: "v3.1", creado: now, actualizado: now, patch: shiftSchedule(baseline, 3), extras: {}, kpi: { TIR: null, VAN: null, TIR_eq: null, DSCR_min: null }, preset: true,
    },
    {
      id: "preset-red-cod-12",
      nombre: "Retraso por red (refuerzos del alimentador): COD +12 meses",
      nota: "Memo de 03: 33 meses de construcción. No incluye el costo de oportunidad del ahorro no percibido durante el retraso ni el riesgo del D.E. 32.",
      base: "v3.1", creado: now, actualizado: now, patch: shiftSchedule(baseline, 12), extras: {}, kpi: { TIR: null, VAN: null, TIR_eq: null, DSCR_min: null }, preset: true,
    },
  ];
}

/** id corto y único para un escenario nuevo (fecha + aleatorio); segmentos válidos para la base (letras, dígitos, - _). */
export function newScenarioId(): string {
  const d = new Date();
  const stamp = d.toISOString().slice(0, 19).replace(/\D/g, "");   // sólo dígitos (AAAAMMDDhhmmss)
  const rnd = Math.random().toString(36).slice(2, 7);
  return `s-${stamp}-${rnd}`;
}
