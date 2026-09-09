/**
 * Estado del modelo: entradas (01_Supuestos) → motor TS (111 casos) → vistas.
 *  - `inputs` arranca con los valores entregados de la v3.1 (inputs_v31.json = libro raíz recalculado).
 *  - Cada cambio en Mandos/Supuestos recalcula los 111 casos (≈ 30 ms); las vistas leen `computed`.
 *  - `extras`: entradas de 01 que el Motor no usa (capacidad del alimentador, tasas alternas, umbrales, tolerancias);
 *    alimentan textos, candados y controles.
 *  - Autocomprobación: al cargar, el motor se compara con el oráculo (salidas de los 111 casos del Excel/LibreOffice);
 *    el chip «● Motor ≡ Excel n/n» muestra el resultado. Si el usuario cambia entradas, el chip pasa a «◇ sandbox».
 *  - `live(texto)`: evalúa los textos vivos del libro (book.json) con los valores actuales — el artefacto dice lo que dice
 *    el Excel, con las cifras del momento. `frozenUsed` lista los nombres que sólo existen en el libro (controles, estados).
 */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { computeAll, OUTPUT_LABELS, type ComputedCase, type Derived, type Inputs, type OutputKey, type OutputValue } from "@/engine";
import type { CaseId } from "@/lib/views";
import { BOOK, type Book } from "@/model/book";
import { CASE_INDEX, EXPECTED_NAMES, N_CASES } from "@/model/cases";
import { renderLive, type Live, type Value, XlError } from "@/model/formula";
import { createResolver, type Resolver } from "@/model/names";
import { applyScenario, type Scenario } from "@/model/scenarios";
import { inputs as inputsJson, oracle as oracleJson } from "@/model/edition-data";

/** Entradas y oráculo de la edición compilada (src/model/edition-data.ts, generado antes del bundle). */
export const BASELINE_INPUTS = inputsJson as unknown as Inputs;
export { BOOK };

/** Entradas de 01 que el Motor no usa: valor entregado del libro (editables en Supuestos). */
export const BASELINE_EXTRAS: Record<string, Value> = Object.fromEntries(
  BOOK.inputs.rows
    .filter((r) => r.name && !r.calc && !(r.name in BASELINE_INPUTS))
    .map((r) => [r.name as string, (r.value as Value) ?? (BOOK.calc_names[r.name as string] as Value) ?? null]),
);

export interface Oracle {
  version: string;
  fecha_analisis: string;
  calc_sha256: string;
  raw_sha256: string;
  outputLabels: string[];
  cases: { name: string; outputs: (number | string | null)[] }[];
}
export const ORACLE = oracleJson as unknown as Oracle;

export interface SelfCheck {
  status: "ok" | "warn" | "risk";
  compared: number;
  failed: number;
  maxRel: number;
  namesOk: boolean;
  worst: string[];
}

export function runSelfCheck(cases: ComputedCase[]): SelfCheck {
  let compared = 0, failed = 0, maxRel = 0;
  const worst: string[] = [];
  const labels = ORACLE.outputLabels;
  for (let c = 0; c < Math.min(cases.length, ORACLE.cases.length); c++) {
    const o = ORACLE.cases[c];
    const r = cases[c].result.outputs as Record<string, OutputValue>;
    for (let k = 0; k < labels.length; k++) {
      const exp = o.outputs[k];
      const got = r[labels[k]];
      compared++;
      if (typeof exp === "number") {
        if (typeof got !== "number") { failed++; worst.push(`${o.name} · ${labels[k]}: ${exp} → ${String(got)}`); continue; }
        const d = Math.abs(got - exp);
        const rel = d / Math.max(1e-9, Math.abs(exp));
        if (d > 1e-6 && rel > 1e-9) { failed++; if (worst.length < 8) worst.push(`${o.name} · ${labels[k]}: ${exp} → ${got}`); }
        if (Number.isFinite(rel)) maxRel = Math.max(maxRel, Math.min(rel, d));
      } else if (typeof got === "number") {
        failed++; if (worst.length < 8) worst.push(`${o.name} · ${labels[k]}: ${String(exp)} → ${got}`);
      }
    }
  }
  const namesOk = cases.length === N_CASES && Object.entries(EXPECTED_NAMES).every(([i, n]) => cases[Number(i)]?.name === n);
  const status: SelfCheck["status"] = failed === 0 && namesOk ? "ok" : failed <= 3 ? "warn" : "risk";
  return { status, compared, failed, maxRel, namesOk, worst };
}

export interface ModelState {
  inputs: Inputs;
  baseline: Inputs;
  extras: Record<string, Value>;
  derived: Derived;
  cases: ComputedCase[];
  book: Book;
  /** número de entradas que difieren de la v3.1 entregada (Motor + extras) */
  dirty: number;
  dirtyKeys: (keyof Inputs)[];
  dirtyExtras: string[];
  selfCheck: SelfCheck;
  setInput: <K extends keyof Inputs>(key: K, value: Inputs[K]) => void;
  setInputs: (patch: Partial<Inputs>) => void;
  setExtra: (name: string, value: Value) => void;
  reset: () => void;
  /** escenario cargado (guardado o preset); null = libro o edición libre */
  scenario: { id: string; nombre: string } | null;
  /** aplica un escenario (parche sobre el libro) y lo marca como activo */
  loadScenario: (s: Scenario) => void;
  /** marca (o desmarca) el escenario activo sin tocar las entradas (tras guardar/actualizar) */
  markScenario: (s: { id: string; nombre: string } | null) => void;
  /** índice del caso en el Motor para un CaseId */
  idx: (c: CaseId) => number;
  out: (caseIdx: number, key: OutputKey) => OutputValue;
  num: (caseIdx: number, key: OutputKey) => number | null;
  /** texto vivo del libro evaluado con los valores actuales (nunca lanza: un error de Excel sale como su código) */
  live: (l: Live | undefined) => string;
  /** valor de un nombre definido del libro (null si no existe) */
  nameValue: (name: string) => Value;
  resolver: Resolver;
}

const Ctx = createContext<ModelState | null>(null);

function sameValue(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function ModelProvider({ children }: { children: ReactNode }) {
  const [inputs, setInputsState] = useState<Inputs>(BASELINE_INPUTS);
  const [extras, setExtras] = useState<Record<string, Value>>(BASELINE_EXTRAS);
  const [scenario, setScenario] = useState<{ id: string; nombre: string } | null>(null);
  const computed = useMemo(() => computeAll(inputs), [inputs]);
  // la autocomprobación se hace una vez sobre las entradas entregadas (el oráculo es el libro): no depende de los mandos
  const selfCheck = useMemo(() => runSelfCheck(computeAll(BASELINE_INPUTS).cases), []);
  const dirtyKeys = useMemo(
    () => (Object.keys(BASELINE_INPUTS) as (keyof Inputs)[]).filter((k) => !sameValue(inputs[k], BASELINE_INPUTS[k])),
    [inputs],
  );
  const dirtyExtras = useMemo(() => Object.keys(BASELINE_EXTRAS).filter((k) => !sameValue(extras[k], BASELINE_EXTRAS[k])), [extras]);
  const resolver = useMemo(() => createResolver({ inputs, derived: computed.derived, cases: computed.cases, extras }, BOOK, "es-EC"), [inputs, computed, extras]);

  const setInput = useCallback(<K extends keyof Inputs>(key: K, value: Inputs[K]) => {
    setInputsState((prev) => ({ ...prev, [key]: value }));
  }, []);
  const setInputs = useCallback((patch: Partial<Inputs>) => setInputsState((prev) => ({ ...prev, ...patch })), []);
  const setExtra = useCallback((name: string, value: Value) => setExtras((prev) => ({ ...prev, [name]: value })), []);
  const reset = useCallback(() => { setInputsState(BASELINE_INPUTS); setExtras(BASELINE_EXTRAS); setScenario(null); writeScenarioHash(null); }, []);
  const writeScenarioHash = (id: string | null) => {
    try {
      const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
      if (id && !id.startsWith("preset-")) params.set("s", id); else params.delete("s");
      window.location.hash = params.toString();
    } catch { /* host sin hash: el estado vive en memoria */ }
  };
  const loadScenario = useCallback((sc: Scenario) => {
    const applied = applyScenario(BASELINE_INPUTS, BASELINE_EXTRAS, sc);
    setInputsState(applied.inputs);
    setExtras(applied.extras);
    setScenario({ id: sc.id, nombre: sc.nombre });
    writeScenarioHash(sc.id);
  }, []);
  const markScenario = useCallback((sc: { id: string; nombre: string } | null) => { setScenario(sc); writeScenarioHash(sc?.id ?? null); }, []);

  const value = useMemo<ModelState>(() => {
    const out = (caseIdx: number, key: OutputKey): OutputValue => computed.cases[caseIdx].result.outputs[OUTPUT_LABELS[key]];
    const num = (caseIdx: number, key: OutputKey): number | null => {
      const v = out(caseIdx, key);
      return typeof v === "number" && Number.isFinite(v) ? v : null;
    };
    const live = (l: Live | undefined) => renderLive(l, resolver.ctx);
    const nameValue = (name: string): Value => {
      try { return resolver.ctx.name(name); } catch (e) { if (e instanceof XlError) return null; throw e; }
    };
    return {
      inputs,
      baseline: BASELINE_INPUTS,
      extras,
      derived: computed.derived,
      cases: computed.cases,
      book: BOOK,
      dirty: dirtyKeys.length + dirtyExtras.length,
      dirtyKeys,
      dirtyExtras,
      selfCheck,
      setInput,
      setInputs,
      setExtra,
      reset,
      scenario,
      loadScenario,
      markScenario,
      idx: (c) => CASE_INDEX[c],
      out,
      num,
      live,
      nameValue,
      resolver,
    };
  }, [inputs, extras, computed, dirtyKeys, dirtyExtras, selfCheck, setInput, setInputs, setExtra, reset, scenario, loadScenario, markScenario, resolver]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useModel(): ModelState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useModel fuera de ModelProvider");
  return v;
}
