/**
 * «Libro» estático del modelo (book.json, generado por build30/extract_book.py desde las constantes del generador y el
 * libro _calc): textos de 01–13, definiciones (rubros, trámites, riesgos, fuentes, controles, guía) y valores congelados.
 * Los campos de tipo `Live` son fórmulas/plantillas del Excel que se evalúan con `useModel().live(...)`.
 */
import type { Live, Value } from "@/model/formula";
import { book as bookJson } from "@/model/edition-data";

export interface InputRow {
  section?: string;
  name?: string;
  label?: string;
  value?: Value;
  formula?: Live;
  calc?: boolean;
  unit?: string | null;
  fmt?: string | null;
  confirm?: boolean;
  note?: Live;
  info?: boolean;
  yesno?: boolean;
  selector?: string[] | null;
  short?: Live;
  label2?: string | null;
  sens?: [string, string] | null;
  confirm_why?: string | null;
}

export interface Escenario {
  name: string;
  esc_name: string;
  label: string;
  unit: string | null;
  fmt: string | null;
  values: Record<"X" | "C" | "B" | "F", Value>;
  confirm: boolean;
  note: Live;
  sens?: [string, string] | null;
  short?: Live;
  label2?: string | null;
  confirm_why?: string | null;
}

export interface CellRow { row: number; v: Record<string, Value>; f: Record<string, string>; live?: Record<string, Live> }

export interface Book {
  meta: { version: string; fecha_analisis: string; calc_sha256: string; extracted: string; generator: string };
  inputs: {
    rows: InputRow[];
    bloques: { title: string; guide: string; names: string[] }[];
    escenarios: Escenario[];
    n_por_confirmar_marcadas?: number;
    panel: { label: string; value: Live; sub: Live; name: string; extra: Live }[];
    case_keys: string[];
    confirm_list: string[];
    n_por_confirmar_esperado: number;
  };
  capex: {
    rubros: { n: number; name: string; desc: string; base_5mwp: number; pct_comp: number; pct_ext: number; arancel: number; iva: number; source: Live; drv_wp: number; drv_wac: number; drv_fijo: number }[];
    notas: string[];
    intro: string;
    headers: Record<string, string>;
    labels: Record<string, string>;
    reemplazo: CellRow[];
  };
  opex: { intro: string; lines: CellRow[]; serie_labels: string[]; memo_exergy: string[] };
  legal: {
    intro: string;
    rows: { tema: Live; norma: Live; texto: Live; aplicacion: Live; estado: Live; confianza: Live }[];
    candados: { label: Live; criterio: Live; estado: Live; kind: string }[];
    contratos: { contrato: Live; partes: Live; alcance: Live; nota: Live }[];
    dudas: { id: Live; duda: Live; impacto: Live; accion: Live; prioridad: Live }[];
    table_headers: Record<string, (string | null)[] | null>;
  };
  tramites: {
    intro: string;
    mes1: string;
    headers: string[];
    rows: { id: string; tramite: Live; autoridad: Live; base_legal: Live; inicio: number; dur: number; fin: number; costo: number; predecesor: string; critica: string; riesgo: string; nota: Live }[];
    totales: Record<string, { label: string; formula: string; value: Value }>;
    gantt_leyenda: string[];
    memo: string[];
    controles: { cron: { formula: string; value: Value } };
  };
  riesgos: {
    intro: string;
    rows: { categoria: Live; riesgo: Live; prob: number; impacto: number; mitigacion: Live; dueno: Live; disparador: Live }[];
    headers: string[] | null;
    umbrales: { alto: number; medio: number };
  };
  fuentes: { intro: string; rows: { texto: string; url: string | null }[]; secciones: string[]; cells: CellRow[] };
  controles: { intro: string; rows: { group: string; id: string; desc: string; status: string; formula: string; prueba: string | null }[]; resumen: Record<string, Value> };
  guia: {
    intro: string;
    pasos: { title: string; text: Live; sheet: string }[];
    convenciones: { a: string; b: string; color: string; bold: boolean }[];
    grupos: { title: string; items: { term: string; def: Live; live: Live; anchor: string | null }[] }[];
    faq: { q: Live; a: Live }[];
    index: { sheet: string; title: string }[];
  };
  sens: { tornado: { label: Live; lo: number; hi: number | null; note: Live }[]; tornado_short: Live[]; precio_steps: number[]; intro: string };
  sheets: Record<string, { intro: string | null; title: string | null; labels: Record<string, string>; labels_b?: Record<string, string>; labels_c?: Record<string, string>; labels_f?: Record<string, string> }>;
  energia?: { intro: string; demanda_facturable_kW: { label: string; value: Value; formula: string | null }; fgd: { label: string; value: Value; formula: string | null }; factura_referencia: { label: string; formula: string | null; value: Value } };
  exergy?: { intro: string; palancas: CellRow[] };
  frozen: Record<string, Value>;
  frozen_formulas: Record<string, string>;
  calc_names: Record<string, Value>;
  live_names: string[];
}

/** Libro de la edición compilada (src/model/edition-data.ts lo selecciona antes del bundle; check:exclusion lo verifica). */
export const BOOK = bookJson as unknown as Book;

/** Estado (● ▲ ■ ◇) a partir del primer carácter de un texto de estado del libro. */
export function statusOf(text: string): "ok" | "warn" | "risk" | "info" {
  const g = text.trim().charAt(0);
  return g === "●" ? "ok" : g === "▲" ? "warn" : g === "■" ? "risk" : "info";
}
