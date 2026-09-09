/**
 * 06_OPEX — las cinco líneas del costo anual de SALELGI (filas 18–22) y el memo de costos propios de Exergy (27–28),
 * para cualquier caso del Motor: el factor OPEX del caso (fO) multiplica las líneas de SALELGI como en el bloque OPEX
 * del Motor; el comprador del terreno del caso (terr) decide arriendo o predial; el horizonte y la escalación son los del libro.
 * Verificado: Σ líneas ≡ bloque OPEX del Motor para los 111 casos (test-live.ts).
 */
import { T_AXIS, type CaseParams, type Derived, type Inputs } from "@/engine";

export interface OpexLines {
  t: number;
  fee: number;
  seguros: number;
  arriendo: number;
  predial: number;
  tributos: number;
  total: number;
  /** memo Exergy (no forma parte del OPEX de SALELGI) */
  om_exergy: number;
  predial_exergy: number;
}

export const OPEX_LINE_LABELS = {
  fee: "Fee O&M todo incluido → Exergy",
  seguros: "Seguros all-risk + RC (SALELGI dueño)",
  arriendo: "Arriendo del terreno → Exergy (0 si SALELGI compra)",
  predial: "Predial y gastos del terreno (SALELGI dueña)",
  tributos: "Tributos locales y administración",
} as const;

/** Líneas del año t (t = 1…Horizonte; fuera del rango todo es 0), sin el factor del caso salvo que se pida. */
export function opexLines(i: Inputs, d: Derived, p: CaseParams, t: number, withFactor = true): OpexLines {
  const H = i.Horizonte;
  const on = t >= 1 && t <= H;
  const g = on ? Math.pow(1 + i.Escalacion_OPEX, t - 1) : 0;
  const f = withFactor ? p.fO : 1;
  const ha = p.P / 1000 / i.Densidad_MWp_ha;
  const salelgi = p.terr === 1;
  const fee = on ? i.Fee_OM_kWp * p.P * g * f : 0;
  const seguros = on ? i.Seguro_kWp * p.P * g * f : 0;
  const arriendo = on && !salelgi ? i.Renta_Terreno_ha * ha * g * f : 0;
  const predial = on && salelgi ? i.Predial_Terreno * g * f : 0;
  const tributos = on ? i.Tributos_Locales * g * f : 0;
  void d;
  return {
    t, fee, seguros, arriendo, predial, tributos,
    total: fee + seguros + arriendo + predial + tributos,
    om_exergy: on ? i.Costo_OM_Exergy_kWp * p.P * g : 0,
    predial_exergy: on && !salelgi ? i.Predial_Terreno * g : 0,
  };
}

/** Serie completa t = −1…25. */
export function opexSeries(i: Inputs, d: Derived, p: CaseParams): OpexLines[] {
  return T_AXIS.map((t) => opexLines(i, d, p, t));
}
