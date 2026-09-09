/**
 * Modelo de navegación: grupos y vistas. El id de vista viaja en el hash de la
 * URL (`#v=<id>`, ver ./hash.ts). Los ids son estables: no renombrar.
 */
export const VIEW_IDS = [
  "resumen",
  "sensibilidad",
  "supuestos",
  "energia",
  "capex",
  "opex",
  "fiscal",
  "flujo",
  "exergy",
  "legal",
  "tramites",
  "riesgos",
  "fuentes",
  "controles",
  "guia",
] as const;

export type ViewId = (typeof VIEW_IDS)[number];

export interface ViewMeta {
  id: ViewId;
  label: string;
  /** sólo en la edición interna (se excluye físicamente de la edición externa) */
  internalOnly?: true;
}

export type NavGroupId = "decision" | "motor" | "marco" | "calidad";

export interface NavGroup {
  id: NavGroupId;
  label: string;
  views: readonly ViewMeta[];
}

const ALL_NAV_GROUPS: readonly NavGroup[] = [
  {
    id: "decision",
    label: "Decisión",
    views: [
      { id: "resumen", label: "Resumen" },
      { id: "sensibilidad", label: "Sensibilidad" },
    ],
  },
  {
    id: "motor",
    label: "Motor",
    views: [
      { id: "supuestos", label: "Supuestos" },
      { id: "energia", label: "Energía" },
      { id: "capex", label: "CAPEX" },
      { id: "opex", label: "OPEX" },
      { id: "fiscal", label: "Fiscal" },
      { id: "flujo", label: "Flujo" },
      { id: "exergy", label: "Exergy", internalOnly: true },
    ],
  },
  {
    id: "marco",
    label: "Marco",
    views: [
      { id: "legal", label: "Legal" },
      { id: "tramites", label: "Trámites" },
      { id: "riesgos", label: "Riesgos" },
    ],
  },
  {
    id: "calidad",
    label: "Calidad",
    views: [
      { id: "fuentes", label: "Fuentes" },
      { id: "controles", label: "Controles" },
      { id: "guia", label: "Guía" },
    ],
  },
];

/** Grupos de navegación de la edición compilada: la externa no lista las vistas internas (la constante se pliega en el build). */
export const NAV_GROUPS: readonly NavGroup[] = ALL_NAV_GROUPS.map((g) => ({
  ...g,
  views: g.views.filter((v) => !v.internalOnly || process.env.VITE_EDITION !== "externo"),
}));

export const VIEWS: readonly ViewMeta[] = NAV_GROUPS.flatMap((g) => g.views);

export const DEFAULT_VIEW: ViewId = "resumen";

export function isViewId(value: unknown): value is ViewId {
  return typeof value === "string" && VIEWS.some((v) => v.id === value);
}

export function viewMeta(id: ViewId): ViewMeta {
  const meta = VIEWS.find((v) => v.id === id);
  if (!meta) throw new Error(`Vista desconocida: ${id}`);
  return meta;
}

export function groupOf(id: ViewId): NavGroup {
  const group = NAV_GROUPS.find((g) => g.views.some((v) => v.id === id));
  if (!group) throw new Error(`Vista sin grupo: ${id}`);
  return group;
}

/* --------------------------------------------------------------------------
   Casos del modelo. «custom» es el caso editable (tinta/acento); los tres
   ordinales usan los grises --c-* y los patrones de trazo --dash-*.
   -------------------------------------------------------------------------- */
export const CASE_IDS = ["custom", "conservador", "base", "favorable"] as const;
export type CaseId = (typeof CASE_IDS)[number];

export interface CaseMeta {
  id: CaseId;
  label: string;
  /** Variable CSS del color del caso. */
  colorVar: string;
  /** Variable CSS del patrón de trazo (stroke-dasharray). */
  dashVar: string;
}

export const CASES: readonly CaseMeta[] = [
  { id: "custom", label: "Custom", colorVar: "--accent", dashVar: "--dash-base" },
  { id: "conservador", label: "Conservador", colorVar: "--c-conservador", dashVar: "--dash-conservador" },
  { id: "base", label: "Base", colorVar: "--c-base", dashVar: "--dash-base" },
  { id: "favorable", label: "Favorable", colorVar: "--c-favorable", dashVar: "--dash-favorable" },
];

export const DEFAULT_CASE: CaseId = "base";

export function isCaseId(value: unknown): value is CaseId {
  return typeof value === "string" && (CASE_IDS as readonly string[]).includes(value);
}
