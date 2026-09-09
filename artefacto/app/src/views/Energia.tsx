import type { ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { KpiTile, type StripValue } from "@/components/KpiTile";
import { Frozen, Trace } from "@/components/Live";
import { Status } from "@/components/Status";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { Series, type SeriesDef } from "@/components/charts/Series";
import { edate, lossAt, parseISODate, SCALAR_LABELS, T_AXIS, type CaseParams, type Derived, type Inputs } from "@/engine";
import { fmtDate, fmtNum, fmtPct, fmtUSD, MONTHS_ES_ABBR } from "@/lib/format";
import { CASES, type CaseId, type ViewId } from "@/lib/views";
import { statusOf } from "@/model/book";
import type { Value } from "@/model/formula";
import { useModel } from "@/model/store";

/**
 * Energía (hoja 04_Energia): balance energético de GPM para el caso seleccionado. Las cifras salen del motor (bloques E, Eval
 * y salidas E1 · Cob del caso; `derived` de 04) y de las fórmulas de la hoja reproducidas aquí con los parámetros del caso
 * (balance mensual del año 1, valor evitado por bloque, curva de recorte, factura de referencia). La hoja es «del caso Custom»;
 * la vista generaliza sus filas al caso elegido con la misma aritmética (fT = 1 y misma potencia en los cuatro casos).
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

const n0 = (v: number | null | undefined): number => (typeof v === "number" && Number.isFinite(v) ? v : 0);
const numOf = (v: Value): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
/** Cabecera de columna de la hoja con salto de línea («Proyección · A\n[kWh]»). */
const hdr = (s: string): ReactNode => s.split("\n").map((l, k) => (k === 0 ? l : <span key={k}><br />{l}</span>));
/** Eje x de meses/ratios: `Series` añade « · t = n» al título del tooltip cuando x > 0; con x negativo lo omite (el rótulo lo da xFormat). */
const MES_X: readonly number[] = MONTHS_ES_ABBR.map((_, k) => -(12 - k));
/** Rótulo del eje de años con el menos tipográfico (t = −1). */
const xAnio = (t: number) => (t === 0 ? "COD" : fmtNum(t, 0));

// ------------------------------------------------------------------------------------------------ fórmulas de 04 reproducidas
/** 04!F93 / F94 con los parámetros del caso: Potencia/1000 × F_Recorte × yield(t) × Disponibilidad × (1 − Degradación_Adicional)^MAX(0, t−1). */
function energiaAnual(p: CaseParams, frec: number, Y: readonly number[], t: number): number {
  const y = Y[Math.max(1, t) - 1];
  if (y === undefined) return 0;
  return (p.P / 1000) * frec * y * p.disp * Math.pow(1 - p.deg, Math.max(0, t - 1));
}

interface MesRow {
  k: number;
  mes: string;
  /** D33 · perfil mensual */
  perfil: number;
  /** E33 · producción [MWh] = E1 × perfil */
  prod: number;
  /** F33 · G33 · H33 · I33 [kWh] */
  inyA: number;
  inyB: number;
  inyC: number;
  iny: number;
  /** K17 · consumo proyectado total [kWh] · H17 · bloque A proyectado */
  consumo: number;
  consumoA: number;
  /** J33 · cobertura = I33/K17 */
  cob: number;
  /** K33 · ¿excedente mensual? (I33 > K17) */
  excedente: boolean;
  /** L33 · bloque A neteo: F33 > H17 → «energía equiv.», si no «directo» */
  neteoA: string;
  /** J49 · valor evitado [USD] = F·Tarifa_A + G·Tarifa_A + H·Tarifa_C · K49 = J49/I33 */
  valor: number;
  tarifaEf: number;
}

/** Filas 33–44 (balance) y 49–60 (valor evitado) de 04 con la energía del año 1 del caso (E1 = Σ E33:E44 porque Σ Perfil = 1). */
function balanceMensual(i: Inputs, d: Derived, e1: number): MesRow[] {
  return MONTHS_ES_ABBR.map((mes, k) => {
    const prod = e1 * (i.Perfil_Mensual[k] ?? 0);                              // E33 =Potencia_DC/1000*Yield_Ref*F_Recorte*Disponibilidad*D33
    const inyA = prod * 1000 * i.Frac_A;                                         // F33 =E33*1000*Frac_A
    const inyB = prod * 1000 * i.Frac_B;                                         // G33
    const inyC = prod * 1000 * i.Frac_C;                                         // H33
    const iny = inyA + inyB + inyC;                                              // I33
    const consumo = d.Consumo_Mensual[k] ?? 0;                                   // K17 =H17+I17+J17
    const consumoA = (i.Consumo_2025_A[k] ?? 0) * d.Factor_Nivel_2026;          // H17 =D17*Factor_Nivel_2026
    const valor = inyA * i.Tarifa_A + inyB * i.Tarifa_A + inyC * i.Tarifa_C;     // J49 =F33*Tarifa_A+G33*Tarifa_A+H33*Tarifa_C
    return {
      k, mes, perfil: i.Perfil_Mensual[k] ?? 0, prod, inyA, inyB, inyC, iny, consumo, consumoA,
      cob: consumo > 0 ? iny / consumo : 0,                                      // J33 =I33/K17
      excedente: iny > consumo,                                                  // K33 =IF(I33>K17,"SÍ","no")
      neteoA: inyA > consumoA ? "energía equiv." : "directo",                    // L33 =IF(F33>H17,"energía equiv.","directo")
      valor,
      tarifaEf: iny > 0 ? valor / iny : 0,                                       // K49 =J49/I33
    };
  });
}

interface AnualRow {
  t: number;
  anio: number;
  yP50: number;
  yP90: number;
  eP50: number;
  eP90: number;
  e: number;
  eval: number;
  noRec: number;
  yieldEsp: number;
  fracPeaje: number;
  degrad: number;
  noProd: number;
}

export function Energia({ caseId }: Props) {
  const m = useModel();
  const ci = m.idx(caseId);
  const c = m.cases[ci];
  const meta = CASES.find((x) => x.id === caseId)!;
  const i = m.inputs, d = m.derived, p = c.params;
  const blocks = c.result.blocks;
  const frec = c.result.scalars[SCALAR_LABELS.frec];
  const AC = c.result.scalars[SCALAR_LABELS.AC];
  const ha = c.result.scalars[SCALAR_LABELS.ha];
  const e1 = m.num(ci, "E1") ?? 0;
  const cob = m.num(ci, "Cob");
  const noRecTotal = m.num(ci, "NoRec");
  const H = Math.min(i.Horizonte, T_AXIS[T_AXIS.length - 1]);
  const Y = p.scen === 1 ? i.Y_P50 : i.Y_P90;
  const escenario = p.scen === 1 ? "P50" : "P90";
  const eP50_1 = energiaAnual(p, frec, i.Y_P50, 1);                              // 04!F93
  const eP90_1 = energiaAnual(p, frec, i.Y_P90, 1);                              // 04!F94
  const lossCaso = lossAt(i.CR_Ratio, i.CR_Loss, p.ratio);                       // 04!J81 (Loss_Act con el ratio del caso)
  const others = CASES.filter((x) => x.id !== caseId);
  const strip = (key: "E1" | "Cob", fmt: (v: number | null) => string): StripValue[] =>
    others.map((x) => ({ caseId: x.id, text: fmt(m.num(m.idx(x.id), key)) }));

  // ---- balance mensual del año 1 (filas 33–45 · 49–61) ---------------------------------------------------------------
  const meses = balanceMensual(i, d, e1);
  const tot = (() => {
    const s = (f: (r: MesRow) => number) => meses.reduce((a, r) => a + f(r), 0);
    const iny = s((r) => r.iny), valor = s((r) => r.valor);
    return {
      perfil: s((r) => r.perfil), prod: s((r) => r.prod), inyA: s((r) => r.inyA), inyB: s((r) => r.inyB), inyC: s((r) => r.inyC), iny,
      cob: d.Consumo_Anual > 0 ? iny / d.Consumo_Anual : 0,                       // J45 =I45/K29
      nExced: meses.filter((r) => r.excedente).length,                            // K45 =COUNTIF(K33:K44,"SÍ")
      nEquiv: meses.filter((r) => r.neteoA === "energía equiv.").length,          // L45
      valor,                                                                       // J61 =SUM(J49:J60)
      tarifa: iny > 0 ? valor / iny : 0,                                           // K61 =J61/I45 (= Tarifa_Evitable)
    };
  })();

  // ---- textos de estado de la hoja (D12 · D13 · I13), reproducidos con las cifras del caso ------------------------------
  const demandaMWh = d.Consumo_Anual / 1000;
  const art9 = eP50_1 <= demandaMWh
    ? `● cumple (${fmtPct(demandaMWh > 0 ? eP50_1 / demandaMWh : 0, 0)} de la demanda)`
    : `■ NO cumple: ${fmtNum(n0(blocks.E[2]) - n0(blocks.Eval[2]), 0)} MWh no reconocidos en el año 1`;
  const art27 = tot.nExced === 0
    ? "● ninguno: toda la energía se netea el mismo mes; la bolsa de 24 meses no se usa"
    : `▲ ${tot.nExced} meses con excedente → crédito kWh (caduca a 24 meses)`;
  const neteoTxt = `${tot.nEquiv} meses con inyección A > consumo A: se netea como energía equivalente (art. 27.3) sin perder valor en USD`;
  const potMaxArt9 = eP50_1 > 0 ? (p.P * d.Consumo_Anual) / 1000 / eP50_1 : 0;   // E11: Potencia_DC*K29/1000/F93

  // ---- serie anual (filas 89–101) con el eje del Motor (t = −1…25) -------------------------------------------------------
  const cod = parseISODate(i.Fecha_COD);
  const anual: AnualRow[] = T_AXIS.filter((t) => t >= 1 && t <= H).map((t) => {
    const k = t - T_AXIS[0];
    const e = n0(blocks.E[k]), ev = n0(blocks.Eval[k]);
    const eP50 = energiaAnual(p, frec, i.Y_P50, t), eP90 = energiaAnual(p, frec, i.Y_P90, t);
    return {
      t,
      anio: edate(cod, 12 * (t - 1)).y,                                            // fila 90 =YEAR(EDATE(Fecha_COD,12*(t-1)))
      yP50: i.Y_P50[t - 1] ?? 0, yP90: i.Y_P90[t - 1] ?? 0,                        // filas 91–92
      eP50, eP90,                                                                  // filas 93–94
      e, eval: ev, noRec: e - ev,                                                  // filas 95–97
      yieldEsp: e > 0 ? (e * 1000) / p.P : 0,                                      // fila 98
      fracPeaje: d.Frac_Peaje[k] ?? 0,                                             // fila 99
      degrad: eP50_1 > 0 ? eP50 / eP50_1 - 1 : 0,                                  // fila 100 (P50, incl. adicional)
      noProd: (p.P / 1000) * frec * (Y[t - 1] ?? 0) - e,                           // fila 101 (informativa)
    };
  });
  const demandaAnual = T_AXIS.map((t) => (t < 1 || t > H ? null : (d.Consumo_Anual * Math.pow(1 + i.Crecimiento_Consumo, t - 1)) / 1000)); // tope del art. 9 (fila 96)
  const serieAnual: SeriesDef[] = [
    { id: "p50", label: "Energía anual P50", values: T_AXIS.map((t) => (t < 1 || t > H ? null : energiaAnual(p, frec, i.Y_P50, t))), color: "var(--ink-3)", width: 1.5 },
    { id: "p90", label: "Energía anual P90", values: T_AXIS.map((t) => (t < 1 || t > H ? null : energiaAnual(p, frec, i.Y_P90, t))), color: "var(--ink-3)", dash: "4 3", width: 1.5 },
    { id: "e", label: `Energía producida del caso (${escenario})`, values: blocks.E.map((v, k) => (T_AXIS[k] < 1 || T_AXIS[k] > H ? null : n0(v))), color: "var(--cat-1)", area: true },
    { id: "dem", label: "Demanda anual (tope del art. 9)", values: demandaAnual, color: "var(--cat-2)" },
  ];

  // ---- curva de recorte (H65:J79 · J80–J82) --------------------------------------------------------------------------------
  const cr = i.CR_Ratio.map((r, k) => ({ ratio: r, loss: i.CR_Loss[k] ?? 0, rel: (1 - (i.CR_Loss[k] ?? 0)) / (1 - d.Loss_Ref) - 1 })); // J66 =(1-I66)/(1-Loss_Ref)-1
  const crSel = cr.reduce((best, r, k) => (Math.abs(r.ratio - p.ratio) < Math.abs(cr[best].ratio - p.ratio) ? k : best), 0);

  // ---- factura de referencia (filas 74–78): D74 y D75 son constantes de la hoja que no viajan en book.json → valor del libro
  const facturaRef = numOf(m.nameValue("Factura_Referencia"));                   // 04!D76
  const reduccion = numOf(m.nameValue("Reduccion_Factura"));                     // 04!D77 =J61/D76
  const peajeEq = AC > 0 ? (p.pj * eP50_1 * 1000) / AC / 12 : 0;                  // 04!D78 =IF(Potencia_AC>0,Eff_Peaje*$F$93*1000/Potencia_AC/12,0)
  const notaFGD = m.book.inputs.confirm_list.find((t) => t.includes("FGD"));
  const cap = numOf(m.extras.Capacidad_Alimentador_kW), haDisp = numOf(m.extras.Ha_Disponibles);
  const rowLabel = (name: string) => m.book.inputs.rows.find((r) => r.name === name)?.label2 ?? m.book.inputs.rows.find((r) => r.name === name)?.label ?? name;

  // ---- columnas -----------------------------------------------------------------------------------------------------------------
  const consumoCols: Column<{ k: number; mes: string }>[] = [
    { key: "mes", label: "Mes", render: (r) => r.mes },
    { key: "a", label: hdr("2025 · A\n08–18 h"), align: "right", render: (r) => fmtNum(r.k < 0 ? sum(i.Consumo_2025_A) : i.Consumo_2025_A[r.k], 0) },
    { key: "b", label: hdr("2025 · B\n18–22 h"), align: "right", render: (r) => fmtNum(r.k < 0 ? sum(i.Consumo_2025_B) : i.Consumo_2025_B[r.k], 0) },
    { key: "c", label: hdr("2025 · C\n22–08 h"), align: "right", render: (r) => fmtNum(r.k < 0 ? sum(i.Consumo_2025_C) : i.Consumo_2025_C[r.k], 0) },
    { key: "tot", label: hdr("2025\ntotal"), align: "right", render: (r) => fmtNum(r.k < 0 ? sum(i.Consumo_2025_A) + sum(i.Consumo_2025_B) + sum(i.Consumo_2025_C) : i.Consumo_2025_A[r.k] + i.Consumo_2025_B[r.k] + i.Consumo_2025_C[r.k], 0) },
    { key: "pa", label: hdr("Proyección · A\n[kWh]"), align: "right", render: (r) => fmtNum((r.k < 0 ? sum(i.Consumo_2025_A) : i.Consumo_2025_A[r.k]) * d.Factor_Nivel_2026, 0) },
    { key: "pb", label: hdr("Proyección · B\n[kWh]"), align: "right", render: (r) => fmtNum((r.k < 0 ? sum(i.Consumo_2025_B) : i.Consumo_2025_B[r.k]) * d.Factor_Nivel_2026, 0) },
    { key: "pc", label: hdr("Proyección · C\n[kWh]"), align: "right", render: (r) => fmtNum((r.k < 0 ? sum(i.Consumo_2025_C) : i.Consumo_2025_C[r.k]) * d.Factor_Nivel_2026, 0) },
    { key: "pt", label: hdr("Proyección\ntotal [kWh]"), align: "right", render: (r) => fmtNum(r.k < 0 ? d.Consumo_Anual : d.Consumo_Mensual[r.k], 0) },
  ];
  const consumoRows = [...MONTHS_ES_ABBR.map((mes, k) => ({ k, mes })), { k: -1, mes: "Año" }];

  interface EneMayRow { mes: string; a: number; b: number }
  const eneMayCols: Column<EneMayRow>[] = [
    { key: "mes", label: "Mes", render: (r) => r.mes },
    { key: "a", label: "kWh 2025", align: "right", render: (r) => fmtNum(r.a, 0) },
    { key: "b", label: "kWh 2026", align: "right", render: (r) => fmtNum(r.b, 0) },
  ];
  const eneMayRows: EneMayRow[] = [
    ...i.Consumo_2025_EneMay.map((a, k) => ({ mes: MONTHS_ES_ABBR[k] ?? String(k + 1), a, b: i.Consumo_2026_EneMay[k] ?? 0 })),
    { mes: "Σ ene–may", a: sum(i.Consumo_2025_EneMay), b: sum(i.Consumo_2026_EneMay) },
  ];

  type BalRow = MesRow | { k: -1 };
  const isTot = (r: BalRow): r is { k: -1 } => r.k < 0;
  const balanceCols: Column<BalRow>[] = [
    { key: "mes", label: "Mes", render: (r) => (isTot(r) ? "Año" : r.mes) },
    { key: "perfil", label: hdr("Perfil\nmensual"), align: "right", muted: true, render: (r) => fmtPct(isTot(r) ? tot.perfil : r.perfil, 2) },
    { key: "prod", label: hdr(`Producción\n${escenario} [MWh]`), align: "right", render: (r) => fmtNum(isTot(r) ? tot.prod : r.prod, 0) },
    { key: "inyA", label: hdr("Inyección · A\n[kWh]"), align: "right", render: (r) => fmtNum(isTot(r) ? tot.inyA : r.inyA, 0) },
    { key: "inyB", label: hdr("Inyección · B\n[kWh]"), align: "right", render: (r) => fmtNum(isTot(r) ? tot.inyB : r.inyB, 0) },
    { key: "inyC", label: hdr("Inyección · C\n[kWh]"), align: "right", render: (r) => fmtNum(isTot(r) ? tot.inyC : r.inyC, 0) },
    { key: "iny", label: hdr("Inyección\ntotal [kWh]"), align: "right", render: (r) => fmtNum(isTot(r) ? tot.iny : r.iny, 0) },
    { key: "cons", label: hdr("Consumo\nproyectado [kWh]"), align: "right", render: (r) => fmtNum(isTot(r) ? d.Consumo_Anual : r.consumo, 0) },
    { key: "cob", label: "Cobertura", align: "right", render: (r) => fmtPct(isTot(r) ? tot.cob : r.cob, 1) },
    { key: "exc", label: hdr("¿Excedente\nmensual?"), align: "center", render: (r) => (isTot(r) ? `${tot.nExced} meses` : r.excedente ? <span className="text-warn-text">SÍ</span> : <span className="text-ink-3">no</span>) },
    { key: "neteo", label: hdr("Bloque A\nneteo"), align: "center", render: (r) => (isTot(r) ? `${tot.nEquiv} meses` : <span className={r.neteoA === "directo" ? "text-ink-3" : "text-ink-2"}>{r.neteoA}</span>) },
    { key: "valor", label: hdr("Valor evitado\n[USD]"), align: "right", render: (r) => fmtUSD(isTot(r) ? tot.valor : r.valor) },
    { key: "tar", label: hdr("Tarifa efect.\n[$/kWh]"), align: "right", render: (r) => fmtNum(isTot(r) ? tot.tarifa : r.tarifaEf, 4) },
  ];
  const balanceRows: BalRow[] = [...meses, { k: -1 }];

  const anualCols: Column<AnualRow>[] = [
    { key: "t", label: "Año (t)", align: "right", mono: true, render: (r) => String(r.t) },
    { key: "anio", label: hdr("Año\ncalendario"), align: "right", muted: true, render: (r) => String(r.anio) },
    { key: "yP50", label: hdr("Yield P50\n[kWh/kWp]"), align: "right", muted: true, render: (r) => fmtNum(r.yP50, 1) },
    { key: "yP90", label: hdr("Yield P90\n[kWh/kWp]"), align: "right", muted: true, render: (r) => fmtNum(r.yP90, 1) },
    { key: "eP50", label: hdr("Energía anual\nP50 [MWh]"), align: "right", render: (r) => fmtNum(r.eP50, 0) },
    { key: "eP90", label: hdr("Energía anual\nP90 [MWh]"), align: "right", render: (r) => fmtNum(r.eP90, 0) },
    { key: "e", label: hdr(`Producida del caso\n(${escenario}) [MWh]`), align: "right", render: (r) => fmtNum(r.e, 0) },
    { key: "eval", label: hdr("Valorizable\n(art. 9) [MWh]"), align: "right", render: (r) => fmtNum(r.eval, 0) },
    { key: "noRec", label: hdr("No reconocida\n[MWh]"), align: "right", render: (r) => (r.noRec > 0.5 ? <span className="text-warn-text">{fmtNum(r.noRec, 0)}</span> : <span className="text-ink-3">{fmtNum(r.noRec, 0)}</span>) },
    { key: "ye", label: hdr("Yield específico\n[kWh/kWp]"), align: "right", render: (r) => fmtNum(r.yieldEsp, 0) },
    { key: "fp", label: hdr("Fracción del año\ncon peaje"), align: "right", render: (r) => fmtPct(r.fracPeaje, 0) },
    { key: "deg", label: hdr("Degradación acum.\nvs año 1 (P50)"), align: "right", render: (r) => fmtPct(r.degrad, 1) },
    { key: "np", label: hdr("No producida (indisp.\n+ deg. adicional) [MWh]"), align: "right", muted: true, render: (r) => fmtNum(r.noProd, 0) },
  ];

  const crCols: Column<{ ratio: number; loss: number; rel: number }>[] = [
    { key: "r", label: "Ratio DC/AC", align: "right", render: (r) => fmtNum(r.ratio, 2) },
    { key: "l", label: hdr("Pérdida por\nrecorte"), align: "right", render: (r) => fmtPct(r.loss, 2) },
    { key: "y", label: hdr(`Yield rel.\nvs ${fmtNum(i.Ratio_Ref, 2)}`), align: "right", render: (r) => fmtPct(r.rel, 2, "always") },
  ];

  const bloques = [
    { id: "A", nombre: "Bloque A · 08–18 h", frac: i.Frac_A, tarifa: i.Tarifa_A, iny: tot.inyA, valor: tot.inyA * i.Tarifa_A, tarifaName: "Tarifa_A" },
    { id: "B", nombre: "Bloque B · 18–22 h (se valora a la tarifa A)", frac: i.Frac_B, tarifa: i.Tarifa_A, iny: tot.inyB, valor: tot.inyB * i.Tarifa_A, tarifaName: "Tarifa_A" },
    { id: "C", nombre: "Bloque C · 22–08 h", frac: i.Frac_C, tarifa: i.Tarifa_C, iny: tot.inyC, valor: tot.inyC * i.Tarifa_C, tarifaName: "Tarifa_C" },
    { id: "T", nombre: "Inyección total · tarifa evitable ponderada", frac: i.Frac_A + i.Frac_B + i.Frac_C, tarifa: tot.tarifa, iny: tot.iny, valor: tot.valor, tarifaName: "Tarifa_Evitable" },
  ];
  const bloqueCols: Column<(typeof bloques)[number]>[] = [
    { key: "n", label: "Bloque horario", render: (r) => r.nombre },
    { key: "f", label: hdr("Fracción de\nla inyección"), align: "right", render: (r) => fmtPct(r.frac, 1) },
    { key: "t", label: hdr("Tarifa\n[$/kWh]"), align: "right", render: (r) => <>{fmtNum(r.tarifa, 4)} <Trace name={r.tarifaName} /></> },
    { key: "i", label: hdr("Inyección\naño 1 [kWh]"), align: "right", render: (r) => fmtNum(r.iny, 0) },
    { key: "v", label: hdr("Valor evitado\naño 1 [USD]"), align: "right", render: (r) => fmtUSD(r.valor) },
  ];

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Energía" sheet="04_Energia">
        {/* D6 y I6 de la hoja con las cifras del caso */}
        <Chip title="04_Energia!D6">{fmtNum(p.P, 0)} kWp / {fmtNum(AC, 0)} kWac · {fmtNum(p.ratio, 2)} · {fmtNum(ha, 1)} ha</Chip>
        <Chip title="04_Energia!I6">Alimentador: {fmtNum(cap, 0)} kW (por confirmar) · predio {fmtNum(haDisp, 2)} ha</Chip>
        <Chip>caso {meta.label} · {escenario} · disponibilidad {fmtPct(p.disp, 1)}</Chip>
      </ViewHeader>

      {/* ---------------------------------------------------------------- resumen (filas 5–13) */}
      <Section title={`Resumen · año 1 del caso ${meta.label}`} guide="cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo · la serie anual está más abajo">
        <div className="grid grid-cols-2 gap-x-6 gap-y-5 md:grid-cols-3 lg:grid-cols-6">
          <KpiTile
            label="Producción año 1"
            excelName="Energía año 1 (MWh) · 04!E45"
            value={`${fmtNum(e1, 0)} MWh`}
            compare={<>P50 {fmtNum(eP50_1, 0)} · P90 {fmtNum(eP90_1, 0)} MWh · yield {fmtNum(p.P > 0 ? (e1 * 1000) / p.P : 0, 0)} kWh/kWp</>}
            strip={strip("E1", (v) => (v === null ? "—" : fmtNum(v, 0)))}
          />
          <KpiTile
            label="Cobertura del consumo (año 1)"
            excelName="Cobertura_Anual"
            value={cob === null ? "—" : fmtPct(cob, 1)}
            state={eP50_1 <= demandaMWh ? "ok" : "risk"}
            compare={<>consumo anual {fmtNum(d.Consumo_Anual, 0)} kWh · potencia máxima teórica bajo el art. 9 con este consumo: {fmtNum(potMaxArt9, 0)} kWp</>}
            strip={strip("Cob", (v) => (v === null ? "—" : fmtPct(v, 1)))}
          />
          <KpiTile
            label="Tarifa evitable efectiva"
            excelName="Tarifa_Evitable"
            value={`${fmtNum(d.Tarifa_Evitable, 4)} $/kWh`}
            compare={<>{fmtNum(d.Tarifa_Evitable * 1000, 1)} $/MWh · ponderada por bloques: {fmtPct(i.Frac_A, 1)} de la inyección cae en el bloque A ({fmtNum(i.Tarifa_A, 3)}) y {fmtPct(i.Frac_C, 1)} en el C ({fmtNum(i.Tarifa_C, 3)})</>}
          />
          <KpiTile
            label={`Factor de recorte vs referencia (ratio ${fmtNum(i.Ratio_Ref, 2)})`}
            excelName="F_Recorte"
            value={`${fmtNum(frec, 3)} ×`}
            compare={<>pérdida por recorte {fmtPct(lossCaso, 2)} (ref. {fmtPct(d.Loss_Ref, 2)}); curva pvlib más abajo</>}
          />
          <KpiTile label="Potencia AC" excelName="Potencia_AC" value={`${fmtNum(AC, 0)} kW`} compare={<>{fmtNum(p.P, 0)} kWp · ratio DC/AC {fmtNum(p.ratio, 2)}</>} />
          <KpiTile label="Hectáreas" excelName="Hectareas" value={`${fmtNum(ha, 1)} ha`} compare={<>densidad {fmtNum(i.Densidad_MWp_ha, 2)} MWp/ha · predio {fmtNum(haDisp, 2)} ha</>} />
        </div>
        <ul className="flex flex-col gap-1.5 text-[12.5px]">
          <li className="grid grid-cols-[minmax(0,260px)_minmax(0,1fr)] items-start gap-x-3">
            <span className="text-ink-2">{m.book.sheets["04_Energia"]?.labels["12"]}</span>
            <span className="flex flex-col gap-0.5">
              <Status kind={statusOf(art9)}>{art9.replace(/^[●▲■◇]\s*/, "")} <Trace cell="04_Energia!D12" /></Status>
              <span className="text-[12px] text-ink-3">Candado de energía del régimen SGDA. La energía por encima de la demanda anual no se valora (E_Val).</span>
            </span>
          </li>
          <li className="grid grid-cols-[minmax(0,260px)_minmax(0,1fr)] items-start gap-x-3">
            <span className="text-ink-2">{m.book.sheets["04_Energia"]?.labels["13"]}</span>
            <span className="flex flex-col gap-0.5">
              <Status kind={statusOf(art27)}>{art27.replace(/^[●▲■◇]\s*/, "")} <Trace cell="04_Energia!D13" /></Status>
              <span className="text-[12px] text-ink-3">{neteoTxt}</span>
            </span>
          </li>
        </ul>
      </Section>

      {/* ---------------------------------------------------------------- consumo (filas 15–29 · 64–80) */}
      <div className="grid gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(300px,2fr)]">
        <Section title={m.book.sheets["04_Energia"]?.labels["15"] ?? "Balance mensual del año 1 · consumo del medidor por bloque horario"} guide="planillas 2025 y proyección al nivel 2026 (kWh)" aside={<Trace name="Consumo_Anual" cell="04_Energia!K17:K29" />}>
          <DataTable columns={consumoCols} rows={consumoRows} rowKey={(r) => r.mes} size="sm" emphasize={(r) => r.k < 0} />
          <Note>Estacionalidad 2025 × nivel 2026; crecimiento {fmtPct(i.Crecimiento_Consumo, 1)}/año en el horizonte.</Note>
        </Section>

        <Section title={m.book.sheets["04_Energia"]?.labels["64"] ?? "Proyección del consumo y factura de referencia"} guide="Σ ene–may 2026 ÷ Σ ene–may 2025">
          <DataTable columns={eneMayCols} rows={eneMayRows} rowKey={(r) => r.mes} size="sm" emphasize={(r) => r.mes.startsWith("Σ")} />
          <dl className="flex flex-col divide-y divide-hairline text-[12.5px]">
            <Fila label="Factor de nivel 2026 (Σ 2026 / Σ 2025)" value={`${fmtNum(d.Factor_Nivel_2026, 4)} ×`} trace={<Trace name="Factor_Nivel_2026" cell="04_Energia!D72" />} />
            <Fila
              label="Factura de referencia anual sin SGDA (tarifa 2026)"
              value={<>{fmtUSD(facturaRef)}<Frozen what="Factura de referencia" /></>}
              trace={<Trace name="Factura_Referencia" cell="04_Energia!D76" />}
            />
            <Fila
              label="Reducción de la factura en el año 1"
              value={<>{reduccion === null ? "—" : fmtPct(reduccion, 1)}<Frozen what="Reducción de la factura" /></>}
              trace={<Trace name="Reduccion_Factura" cell="04_Energia!D77" />}
            />
            <Fila label="Valor evitado en el año 1 (Σ mensual)" value={fmtUSD(tot.valor)} trace={<Trace name="Ahorro_Mensual_Anio1" cell="04_Energia!J61" />} />
            <Fila label="Peaje equivalente por potencia (informativo)" value={`${fmtNum(peajeEq, 2)} $/kW-mes`} trace={<Trace cell="04_Energia!D78" />} />
          </dl>
          <Note>{m.book.sheets["04_Energia"]?.labels["80"]}</Note>
          {notaFGD && <Note className="text-ink-3">{notaFGD}</Note>}
          <p className="text-[11.5px] text-ink-3">
            La factura de referencia y la reducción son valores del libro (marca ·): la demanda facturable promedio y el FGD de la hoja no son entradas del modelo, así que el motor no las recalcula. El valor evitado sí es vivo.
          </p>
        </Section>
      </div>

      {/* ---------------------------------------------------------------- balance mensual (filas 31–61) */}
      <Section
        title={`Balance mensual del año 1 · producción ${escenario} e inyección por bloque`}
        guide="inyección = producción × fracción horaria del TMY; cobertura = inyección ÷ consumo proyectado · pase el cursor por un mes"
        aside={<Trace name="Perfil_Mensual" cell="04_Energia!D33:K45 · J49:K61" />}
      >
        <Series
          x={MES_X}
          xTick={() => true}
          xFormat={(_, k) => MONTHS_ES_ABBR[k]}
          series={[
            { id: "prod", label: `Producción ${escenario} [MWh]`, values: meses.map((r) => r.prod), color: "var(--cat-1)", bars: true },
            { id: "cons", label: "Consumo proyectado [MWh]", values: meses.map((r) => r.consumo / 1000), color: "var(--cat-2)", bars: true },
          ]}
          yFormat={(v) => fmtNum(v, 0)}
          yLabel="MWh"
          height={220}
          ariaLabel="Producción mensual frente a consumo mensual del año 1"
        />
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <Status kind={statusOf(art27)}>{art27.replace(/^[●▲■◇]\s*/, "")}</Status>
          <span className="text-[12px] text-ink-3">{neteoTxt}</span>
        </div>
        <DataTable columns={balanceCols} rows={balanceRows} rowKey={(r) => (isTot(r) ? "año" : r.mes)} size="sm" emphasize={(r) => isTot(r)} />
        <Note>el valor evitado usa la tarifa del bloque donde se inyecta (B se valora a la tarifa A)</Note>
      </Section>

      {/* ---------------------------------------------------------------- serie anual (filas 88–101) */}
      <Section
        title="Serie anual — yield canónico × potencia × recorte"
        guide={`t = 1…${H} del Motor (años 26–30 de la hoja quedan fuera del horizonte); demanda anual = Consumo_Anual × (1 + crecimiento)^(t−1)`}
        aside={<Trace name="E_Activa · E_Val" cell="04_Energia!D89:AD101" />}
      >
        <Series x={T_AXIS} xFormat={xAnio} series={serieAnual} yFormat={(v) => fmtNum(v, 0)} yLabel="MWh" height={230} ariaLabel="Serie anual de energía producida, valorizable y demanda" />
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-ink-2">
          <span>Energía no reconocida Σ (producción − demanda): <span className="text-ink">{fmtNum(noRecTotal, 0)} MWh</span> <Trace name="Energía no reconocida Σ (MWh)" /></span>
          <span>Degradación adicional {fmtPct(p.deg, 2)}/año sobre el yield canónico · disponibilidad {fmtPct(p.disp, 1)}</span>
          <span>Peaje SGDA desde {fmtDate(i.Fecha_Peaje)} (COD {fmtDate(i.Fecha_COD)}) <Trace name="Frac_Peaje" cell="04_Energia!D99:AD99" /></span>
        </div>
        <DataTable columns={anualCols} rows={anual} rowKey={(r) => String(r.t)} size="sm" />
      </Section>

      {/* ---------------------------------------------------------------- técnicos (filas 47–61 · 64–83 · 99) */}
      <div className="grid gap-8 lg:grid-cols-2">
        <Section title="Curva de recorte por ratio DC/AC (pvlib)" guide="pérdida por recorte según el ratio; la fila destacada es el ratio del caso" aside={<Trace name="CR_Ratio · CR_Loss" cell="04_Energia!H66:J79" />}>
          <Series
            x={cr.map((r) => -r.ratio)}
            xTick={(_, k) => k % 2 === 0}
            xFormat={(t) => fmtNum(-t, 2)}
            series={[{ id: "loss", label: "Pérdida por recorte", values: cr.map((r) => r.loss), color: "var(--ink-2)", area: true }]}
            yFormat={(v) => fmtPct(v, 1)}
            refLine={{ value: lossCaso, label: `ratio ${fmtNum(p.ratio, 2)} · pérdida ${fmtPct(lossCaso, 2)}` }}
            height={190}
            ariaLabel="Curva de pérdida por recorte según el ratio DC/AC"
          />
          <dl className="flex flex-col divide-y divide-hairline text-[12.5px]">
            <Fila label={`Pérdida a Ratio_Ref (${fmtNum(i.Ratio_Ref, 2)})`} value={fmtPct(d.Loss_Ref, 2)} trace={<Trace name="Loss_Ref" cell="04_Energia!J80" />} />
            <Fila label={`Pérdida al ratio del caso (${fmtNum(p.ratio, 2)})`} value={fmtPct(lossCaso, 2)} trace={<Trace name="Loss_Act" cell="04_Energia!J81" />} />
            <Fila label="Factor de recorte F" value={`${fmtNum(frec, 4)} ×`} trace={<Trace name="F_Recorte" cell="04_Energia!J82" />} />
          </dl>
          <DataTable columns={crCols} rows={cr} rowKey={(r) => String(r.ratio)} size="sm" selected={(_, k) => k === crSel} />
          <Note>Curva pvlib (TMY P50 Montecristi, 10° N, PVWatts; 12 §D): interpolación lineal, fuera de 1,00–1,60 se toma el extremo; ±0,3 pp.</Note>
        </Section>

        <Section title="Tarifa evitable por bloques horarios y cargos" guide="año 1 del caso; los cargos fijos no son evitables con un SGDA remoto" aside={<Trace name="Tarifa_Evitable" cell="04_Energia!K61" />}>
          <DataTable columns={bloqueCols} rows={bloques} rowKey={(r) => r.id} size="sm" emphasize={(r) => r.id === "T"} />
          <dl className="flex flex-col divide-y divide-hairline text-[12.5px]">
            <Fila label={rowLabel("Cargo_Demanda")} value={`${fmtNum(numOf(m.extras.Cargo_Demanda), 2)} $/kW-mes`} trace={<Trace name="Cargo_Demanda" />} />
            <Fila label={rowLabel("Cargo_Comercializacion")} value={`${fmtNum(numOf(m.extras.Cargo_Comercializacion), 2)} $/mes`} trace={<Trace name="Cargo_Comercializacion" />} />
            <Fila label={rowLabel("SAPG_mes")} value={`${fmtNum(numOf(m.extras.SAPG_mes), 0)} $/mes`} trace={<Trace name="SAPG_mes" />} />
            <Fila label={`Peaje SGDA del caso (desde ${fmtDate(i.Fecha_Peaje)})`} value={`${fmtNum(p.pj * 100, 2)} ¢/kWh · ${fmtNum(p.pkw, 2)} $/kW-mes`} trace={<Trace name="Peaje_SGDA · Peaje_kW_mes" />} />
          </dl>
          <h3 className="mt-1 text-[12px] font-medium text-ink-2">Fracción del año con peaje SGDA vigente</h3>
          <Series
            x={T_AXIS}
            xFormat={xAnio}
            series={[{ id: "fp", label: "Fracción del año con peaje SGDA vigente", values: d.Frac_Peaje.map((v, k) => (T_AXIS[k] > H ? null : v)), color: "var(--ink-2)", bars: true }]}
            yFormat={(v) => fmtPct(v, 0)}
            height={130}
            legend={false}
            ariaLabel="Fracción de cada año con el peaje SGDA vigente"
          />
        </Section>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------------ piezas locales
function sum(a: readonly number[]): number {
  let s = 0;
  for (const v of a) s += v;
  return s;
}

/** Fila etiqueta · valor · rastro para listas de definición compactas. */
function Fila({ label, value, trace }: { label: ReactNode; value: ReactNode; trace?: ReactNode }) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-3 py-1.5">
      <dt className="text-ink-2">{label}</dt>
      <dd className="flex flex-col items-end text-right text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
        <span>{value}</span>
        {trace}
      </dd>
    </div>
  );
}
