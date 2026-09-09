import { useMemo, type ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { KpiTile, type StripValue } from "@/components/KpiTile";
import { Frozen, Trace } from "@/components/Live";
import { Status, stripGlyph } from "@/components/Status";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { CintaAnual } from "@/components/charts/CintaAnual";
import { Series } from "@/components/charts/Series";
import { edate, parseISODate, paybackLastCrossing, SCALAR_LABELS, T_AXIS, vanMotor, type CaseParams, type CaseResult, type Inputs } from "@/engine";
import { fmtNum, fmtPct, fmtUSD, fmtUSDCompact, fmtX, fmtYears } from "@/lib/format";
import { CASES, type CaseId, type ViewId } from "@/lib/views";
import { BOOK, statusOf } from "@/model/book";
import { useModel } from "@/model/store";

/**
 * Flujo de caja de SALELGI (hoja 08_Flujo) para el caso seleccionado: indicadores sin y con deuda (filas 7–25), cinta anual,
 * cuadro anual sin deuda (47–61) y con deuda (63–76), DSCR frente al objetivo y deuda máxima por plazo (10 §H).
 * Bloques del Motor tal cual: Ahorro, OPEX, Peaje, Part_u+IR_u, Krep, Terr, FCF_u, Cum_u, Int, Amort, CFADS, DSCR, EQ. Recompuestos
 * aquí con las fórmulas de la hoja/computeCase: CAPEX por fase, IVA pagado/recuperado, factor de descuento (t = 0 base), FCF
 * descontado y su acumulado, payback descontado y del accionista, VAN a tasas alternas, desembolso/saldo/servicio de la deuda,
 * acumulado del accionista, año del DSCR mínimo y los textos vivos F8, F20, F22 y F24 (verificado celda a celda para el Custom).
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

/** Etiquetas de las columnas B y F de 08_Flujo (texto oficial del libro, verbatim). */
const L: Record<number, string> = {
  5: "Indicadores del caso Custom — sin deuda vs con deuda",
  7: "TIR",
  8: "VAN en el COD (t = 0): proyecto @ tasa de descuento · accionista @ tasa del accionista",
  9: "VAN @ tasa alterna 1",
  10: "VAN @ tasa alterna 2",
  11: "Payback simple (años desde COD)",
  12: "Payback descontado (años desde COD)",
  13: "LCOE (sin impuestos)",
  14: "Tarifa evitable de la red",
  15: "Ahorro por kWh vs LCOE",
  16: "Ahorro año 1",
  17: "Ahorro acumulado (nominal)",
  18: "Reducción de la factura (año 1)",
  19: "Aporte de capital (años −1 y 0)",
  20: "DSCR mínimo (años con servicio)",
  21: "DSCR promedio",
  22: "Deuda total al COD (incl. IDC)",
  23: "Cuota anual (francesa, post-gracia)",
  24: "Servicio de la deuda (Σ)",
  25: "Año del DSCR mínimo (t)",
  26: "Los cuatro casos (Custom · Conservador · Base · Favorable) con estos indicadores → 10 §A",
  43: "Año (t)",
  44: "Año calendario (inicio del período)",
  46: "A · Proyecto sin deuda",
  47: "CAPEX industrial (sin IVA)",
  48: "Terreno SALELGI (−), con costos de transacción",
  49: "IVA pagado",
  50: "IVA recuperado",
  51: "Ahorro por energía evitada",
  52: "OPEX SALELGI",
  53: "Peaje SGDA",
  54: "Impuestos incrementales (participación + IR)",
  55: "Reemplazo de inversores (−), si lo paga SALELGI",
  56: "Residual del terreno SALELGI, neto de impuesto (+)",
  57: "Flujo de caja libre del proyecto",
  58: "Acumulado",
  59: "Factor de descuento (t=0 base)",
  60: "FCF descontado",
  61: "Acumulado descontado",
  63: "B · Con deuda (SALELGI deudor)",
  64: "Deuda desembolsada (% × CAPEX, + terreno si se financia)",
  65: "Deuda total al COD",
  66: "Desembolso de deuda (+)",
  67: "Saldo inicial",
  68: "Intereses",
  69: "Amortización (bullet si plazo ≤ gracia)",
  70: "Servicio de la deuda",
  71: "Saldo final",
  72: "IDC capitalizados (memo)",
  73: "CFADS (EBITDA − impuestos + IVA rec. + residual − reemplazo)",
  74: "DSCR",
  75: "Flujo de caja del accionista (equity)",
  76: "Acumulado equity",
  78: "DSCR objetivo (referencia del gráfico)",
};
/** Columna F («Lectura») de 08_Flujo: textos estáticos del libro (book.sheets["08_Flujo"].labels_f, extraídos verbatim de las
 *  celdas F sin fórmula); los vivos (F8, F20, F22, F24) se recomponen en la vista. */
const LECTURA: Record<number, string> = Object.fromEntries(
  Object.entries(BOOK.sheets["08_Flujo"]?.labels_f ?? {}).map(([row, text]) => [Number(row), text]),
);
/** Etiquetas de 08!F64 y 08!F65 (rótulos de los memos J64 = IDC y J65 = Cuota). */
const L_IDC = LECTURA[64] ?? "";
const L_CUOTA = LECTURA[65] ?? "";
/** Fila 25 de 07_Fiscal (el desmantelamiento resta en el EBITDA del Motor; 08 no lo desglosa en una fila propia). */
const L_DESM = "Desmantelamiento en t = Horizonte (gasto deducible)";

const short = (s: string): string => {
  const cut = s.search(/ \(|:| — /);
  return cut > 0 ? s.slice(0, cut) : s;
};
const n = (v: number | null | undefined): number => (typeof v === "number" ? v : 0);
const numOf = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

interface FlowRow {
  t: number; anio: number;
  capex: number; terreno: number; ivaPag: number; ivaRec: number; ahorro: number; opex: number; peaje: number; desm: number; imp: number; rep: number; resid: number;
  fcf: number; cum: number; df: number; fcfDesc: number; cumDesc: number;
  desemb: number; saldoIni: number; int: number; amort: number; servicio: number; saldoFin: number; idc: number; cfads: number; dscr: number | null; eq: number; cumEq: number;
}

/** Filas 47–76 de 08_Flujo para un caso (bloques del Motor + recomposiciones con las fórmulas de la hoja). */
function flowRows(i: Inputs, p: CaseParams, res: CaseResult): FlowRow[] {
  const s = res.scalars, b = res.blocks;
  const H = i.Horizonte, r = i.Tasa_Descuento, fase = i.Fase_m1;
  const K = s[SCALAR_LABELS.K], IVA = s[SCALAR_LABELS.IVA], D = s[SCALAR_LABELS.D], IDC = s[SCALAR_LABELS.IDC], Decom = s[SCALAR_LABELS.Decom];
  const cod = parseISODate(i.Fecha_COD);
  const out: FlowRow[] = [];
  T_AXIS.forEach((t, k) => {
    const prev = out[k - 1];
    const fcf = n(b.FCF_u[k]), df = 1 / Math.pow(1 + r, t);   // 08!59 =1/(1+Tasa_Descuento)^t (también en t = −1 y 0)
    const fcfDesc = fcf * df;                                  // 08!60
    const int = n(b.Int[k]), amort = n(b.Amort[k]), eq = n(b.EQ[k]);
    // 08!66 =IF(t=-1, Deuda_Monto*Fase_m1, IF(t=0, Deuda_Monto*(1-Fase_m1), 0))
    const desemb = t === -1 ? D * fase : t === 0 ? D * (1 - fase) : 0;
    const saldoIni = prev ? prev.saldoFin : 0;                 // 08!67 (D67 = 0; E67 = D66; F67 = E71 …)
    const idc = t === 0 ? IDC : 0;                             // 08!72
    const saldoFin = saldoIni + desemb + idc - amort;          // 08!71
    out.push({
      t, anio: edate(cod, 12 * (t - 1)).y,
      // 08!47 =IF(t=-1, -CAPEX_Total*Fase_m1, IF(t=0, -CAPEX_Total*(1-Fase_m1), 0))
      capex: t === -1 ? -K * fase : t === 0 ? -K * (1 - fase) : 0,
      // 08!48 =IF(t=-1, -Terreno_SALELGI, 0)  (= bloque Terr en t = −1) · 08!56 residual neto (= bloque Terr en t = Horizonte)
      terreno: t === -1 ? n(b.Terr[k]) : 0,
      // 08!49 = −'07_Fiscal'!41 · 08!50 = '07_Fiscal'!42
      ivaPag: t === -1 ? -IVA * fase : t === 0 ? -IVA * (1 - fase) : 0,
      ivaRec: p.iva === 1 ? (t === 0 ? IVA * fase : t === 1 ? IVA * (1 - fase) : 0) : 0,
      ahorro: n(b.Ahorro[k]), opex: -n(b.OPEX[k]), peaje: -n(b.Peaje[k]),
      desm: t === H ? -Decom : 0,                              // 07_Fiscal!25 (dentro del EBITDA del Motor)
      imp: -(n(b.Part_u[k]) + n(b.IR_u[k])),                   // 08!54 = −'07_Fiscal'!37
      rep: n(b.Krep[k]),                                       // 08!55 (bloque Krep: −Krep en t = Reemplazo_Anio si lo paga SALELGI)
      resid: t === H ? n(b.Terr[k]) : 0,
      fcf, cum: n(b.Cum_u[k]), df, fcfDesc, cumDesc: (prev ? prev.cumDesc : 0) + fcfDesc,
      desemb, saldoIni, int, amort, servicio: int + amort, saldoFin, idc,
      cfads: n(b.CFADS[k]), dscr: b.DSCR[k], eq, cumEq: (prev ? prev.cumEq : 0) + eq,
    });
  });
  return out;
}

/** 08!E25 / Anio_DSCR_Min: t (≥ 1) del DSCR mínimo; null sin servicio de deuda. */
function anioDscrMin(dscr: readonly (number | null)[]): number | null {
  let best: number | null = null, bt: number | null = null;
  dscr.forEach((v, k) => { if (typeof v === "number" && T_AXIS[k] >= 1 && (best === null || v < best)) { best = v; bt = T_AXIS[k]; } });
  return bt;
}

export function Flujo({ caseId }: Props) {
  const m = useModel();
  const ci = m.idx(caseId);
  const c = m.cases[ci];
  const meta = CASES.find((x) => x.id === caseId)!;
  const i = m.inputs, d = m.derived, p = c.params, s = c.result.scalars, b = c.result.blocks;
  const H = i.Horizonte, tasa = i.Tasa_Descuento, req = p.req;
  const K = s[SCALAR_LABELS.K], D = s[SCALAR_LABELS.D], IDC = s[SCALAR_LABELS.IDC], Dt = s[SCALAR_LABELS.Dt], PMT = s[SCALAR_LABELS.PMT], Terr = s[SCALAR_LABELS.Terr];
  const rows = useMemo(() => flowRows(i, p, c.result), [i, p, c.result]);
  const conDeuda = D > 0;

  // ---- indicadores (filas 7–25) ---------------------------------------------------------------------------------------------------------
  const tir = m.num(ci, "TIR"), van = m.num(ci, "VAN"), pb = m.out(ci, "PB"), lcoe = m.num(ci, "LCOE");
  const tirEq = m.out(ci, "TIR_eq"), vanEq = m.num(ci, "VAN_eq"), dscrMin = m.out(ci, "DSCR_min"), dscrAvg = m.out(ci, "DSCR_avg");
  const a1 = m.num(ci, "Ahorro1"), aporteEq = m.num(ci, "Aporte_eq");
  const fcfNum = b.FCF_u.map(n);
  const alt1 = numOf(m.extras.Tasa_Desc_Alt1), alt2 = numOf(m.extras.Tasa_Desc_Alt2);
  const vanAlt1 = alt1 === null ? null : vanMotor(alt1, fcfNum);          // 08!D9 = FCF₋₁(1+r) + FCF₀ + NPV(r, FCF₁…₂₅)
  const vanAlt2 = alt2 === null ? null : vanMotor(alt2, fcfNum);          // 08!D10
  const pbDesc = paybackLastCrossing(rows.map((r) => r.cumDesc), rows.map((r) => r.fcfDesc));   // 08!D12 (misma fórmula que D11 sobre las filas 60–61)
  const pbEq = paybackLastCrossing(rows.map((r) => r.cumEq), rows.map((r) => r.eq));            // 08!E11 (filas 75–76)
  const tarifaMWh = d.Tarifa_Evitable * 1000;                                                    // 08!D14
  const ahorroKwh = tarifaMWh > 0 && lcoe !== null ? 1 - lcoe / tarifaMWh : null;                // 08!D15
  const sumAhorro = rows.reduce((a, r) => a + r.ahorro, 0);                                      // 08!D17
  const facturaRef = numOf(m.nameValue("Factura_Referencia"));                                   // 04!D76 (valor del libro)
  const reduccion = facturaRef !== null && facturaRef > 0 && a1 !== null ? a1 / facturaRef : null; // 08!D18 =Reduccion_Factura (04!D77 = J61/D76)
  const aporteU = -(n(b.FCF_u[0]) + n(b.FCF_u[1]));                                              // 08!D19 =-SUM(D47:E50)
  const sumServicio = rows.reduce((a, r) => a + r.servicio, 0), sumInt = rows.reduce((a, r) => a + r.int, 0);   // 08!E24 · F24
  const anioMin = conDeuda ? anioDscrMin(b.DSCR) : null;                                          // 08!E25
  // 08!F20 =IF(Deuda_Monto=0,"—",IF(DSCR_Min<1,"■ DSCR < 1,00x: el flujo no cubre la cuota en t = "&Anio_DSCR_Min&" — ver 10 §D y §H",
  //            IF(DSCR_Min<DSCR_Objetivo,"▲ DSCR < "&TEXT(DSCR_Objetivo,"0.00")&"x: bajo el umbral bancario","● DSCR ≥ "&TEXT(DSCR_Objetivo,"0.00")&"x")))
  const f20 = !conDeuda || typeof dscrMin !== "number"
    ? "—"
    : dscrMin < 1
      ? `■ DSCR < 1,00x: el flujo no cubre la cuota en t = ${anioMin ?? "—"} — ver 10 §D y §H`
      : dscrMin < i.DSCR_Objetivo
        ? `▲ DSCR < ${fmtNum(i.DSCR_Objetivo, 2)}x: bajo el umbral bancario`
        : `● DSCR ≥ ${fmtNum(i.DSCR_Objetivo, 2)}x`;
  // 08!F22 ="IDC "&TEXT(IDC,"#,##0")&": (tramo −1 un año + tramo 0 × "&TEXT(IDC_Frac_Tramo0,"0.00")&" años) × "&Meses_Construccion&" meses de construcción / 12 (03)"
  const f22 = `IDC ${fmtNum(IDC, 0)}: (tramo −1 un año + tramo 0 × ${fmtNum(i.IDC_Frac_Tramo0, 2)} años) × ${fmtNum(p.ncon, 0)} meses de construcción / 12 (03)`;
  // 08!F8 ="El VAN del accionista se descuenta al "&TEXT(Tasa_Descuento_Equity,"0.0%")&" (Tasa_Descuento_Equity; proyecto al "&TEXT(Tasa_Descuento,"0.0%")&") e incluye el escudo fiscal de los intereses."
  const f8 = `El VAN del accionista se descuenta al ${fmtPct(req, 1)} (Tasa_Descuento_Equity; proyecto al ${fmtPct(tasa, 1)}) e incluye el escudo fiscal de los intereses.`;
  const f24 = `intereses Σ ${fmtNum(sumInt, 0)}`;                                                // 08!F24

  const others = CASES.filter((x) => x.id !== caseId);
  const strip = (f: (k: number) => string, below?: (k: number) => boolean): StripValue[] => others.map((x) => { const k = m.idx(x.id); return { caseId: x.id, text: f(k), below: below ? below(k) : false }; });
  const pbText = (v: number | "n/a" | "no cruza" | null): string => (typeof v === "number" ? fmtYears(v, 1) : v === null ? "—" : v);
  const aporteUOf = (k: number) => { const f = m.cases[k].result.blocks.FCF_u; return -(n(f[0]) + n(f[1])); };

  interface IndRow { row: number; unidad: string; sin: ReactNode; con: ReactNode; lectura: ReactNode; trace?: string }
  const dash = <span className="text-ink-3">—</span>;
  const pct = (v: number | null | "n/a" | "no cruza") => (typeof v === "number" ? fmtPct(v, 2) : v === null ? dash : v);
  const ind: IndRow[] = [
    { row: 7, unidad: "%", sin: pct(tir), con: pct(tirEq), lectura: LECTURA[7], trace: "TIR_Proyecto · TIR_Equity" },
    { row: 8, unidad: "USD", sin: fmtUSD(van), con: fmtUSD(vanEq), lectura: f8, trace: "VAN_Proyecto · VAN_Equity" },
    { row: 9, unidad: "USD", sin: vanAlt1 === null ? dash : fmtUSD(vanAlt1), con: dash, lectura: alt1 === null ? dash : <>@ {fmtPct(alt1, 1)} (Tasa_Desc_Alt1)</>, trace: "08_Flujo!D9" },
    { row: 10, unidad: "USD", sin: vanAlt2 === null ? dash : fmtUSD(vanAlt2), con: dash, lectura: alt2 === null ? dash : <>@ {fmtPct(alt2, 1)} (Tasa_Desc_Alt2)</>, trace: "08_Flujo!D10" },
    { row: 11, unidad: "años", sin: pbText(pb), con: pbText(conDeuda ? pbEq : null), lectura: LECTURA[11], trace: "Payback_Simple · 08_Flujo!E11" },
    { row: 12, unidad: "años", sin: pbText(pbDesc), con: dash, lectura: <>@ {fmtPct(tasa, 1)} (Tasa_Descuento), sobre las filas 60–61</>, trace: "08_Flujo!D12" },
    { row: 13, unidad: "$/MWh", sin: lcoe === null ? dash : fmtNum(lcoe, 1), con: dash, lectura: LECTURA[13], trace: "LCOE" },
    { row: 14, unidad: "$/MWh", sin: fmtNum(tarifaMWh, 1), con: dash, lectura: LECTURA[14], trace: "Tarifa_MWh · 08_Flujo!D14" },
    { row: 15, unidad: "%", sin: ahorroKwh === null ? "n/a" : fmtPct(ahorroKwh, 1), con: dash, lectura: LECTURA[15], trace: "Ahorro_kWh · 08_Flujo!D15" },
    { row: 16, unidad: "USD", sin: fmtUSD(a1), con: dash, lectura: dash, trace: "Ahorro_Anio1" },
    { row: 17, unidad: "USD", sin: fmtUSD(sumAhorro), con: dash, lectura: dash, trace: "08_Flujo!D17 = Σ fila 51" },
    { row: 18, unidad: "%", sin: <>{reduccion === null ? dash : fmtPct(reduccion, 1)}<Frozen what="Factura de referencia (denominador)" /></>, con: dash, lectura: LECTURA[18], trace: "Reduccion_Factura · 04_Energia!D77" },
    { row: 19, unidad: "USD", sin: fmtUSD(aporteU), con: conDeuda ? fmtUSD(aporteEq) : dash, lectura: LECTURA[19], trace: "08_Flujo!D19 · Aporte_Equity" },
    { row: 20, unidad: "x", sin: dash, con: conDeuda ? (typeof dscrMin === "number" ? fmtX(dscrMin, 2) : String(dscrMin)) : dash, lectura: f20 === "—" ? dash : <Status kind={statusOf(f20)}>{stripGlyph(f20)}</Status>, trace: "DSCR_Min" },
    { row: 21, unidad: "x", sin: dash, con: conDeuda ? (typeof dscrAvg === "number" ? fmtX(dscrAvg, 2) : String(dscrAvg)) : dash, lectura: dash, trace: "DSCR_Prom" },
    { row: 22, unidad: "USD", sin: dash, con: conDeuda ? fmtUSD(Dt) : dash, lectura: conDeuda ? f22 : dash, trace: "Deuda_Total" },
    { row: 23, unidad: "USD", sin: dash, con: conDeuda ? fmtUSD(PMT) : dash, lectura: dash, trace: "Cuota" },
    { row: 24, unidad: "USD", sin: dash, con: conDeuda ? fmtUSD(sumServicio) : dash, lectura: conDeuda ? f24 : dash, trace: "08_Flujo!E24 = Σ fila 70" },
    { row: 25, unidad: "t", sin: dash, con: conDeuda && anioMin !== null ? String(anioMin) : dash, lectura: LECTURA[25], trace: "Anio_DSCR_Min" },
  ];
  const indCols: Column<IndRow>[] = [
    { key: "ind", label: "Indicador", render: (r) => L[r.row] },
    { key: "u", label: "Unidad", muted: true, nowrap: true, render: (r) => r.unidad },
    { key: "sin", label: "Sin deuda", align: "right", nowrap: true, render: (r) => r.sin },
    { key: "con", label: "Con deuda", align: "right", nowrap: true, render: (r) => r.con },
    { key: "lec", label: "Lectura", render: (r) => <span className="text-ink-2">{r.lectura}</span> },
    { key: "tr", label: "Nombre / celda", render: (r) => <Trace cell={r.trace} /> },
  ];

  // ---- tablas anuales ------------------------------------------------------------------------------------------------------------------
  const usd = (v: number): ReactNode => (Math.abs(v) < 0.5 ? <span className="text-ink-3">0</span> : fmtNum(v, 0));
  const col = (key: keyof FlowRow, label: string, cell: string, render?: (r: FlowRow) => ReactNode): Column<FlowRow> => ({
    key,
    label: short(label),
    title: `${label} · ${cell}`,
    align: "right",
    render: render ?? ((r) => usd(r[key] as number)),
  });
  const base: Column<FlowRow>[] = [
    { key: "t", label: L[43], title: "08_Flujo!fila 43", align: "right", mono: true, nowrap: true, render: (r) => (r.t === 0 ? "0 · COD" : fmtNum(r.t, 0)) },
    { key: "anio", label: "Año calendario", title: `${L[44]} · 08_Flujo!fila 44`, align: "right", muted: true, render: (r) => String(r.anio) },
  ];
  const strong = (v: number) => <span className="font-medium text-ink">{usd(v)}</span>;
  const colsA: Column<FlowRow>[] = [
    ...base,
    col("capex", L[47], "08_Flujo!fila 47"),
    ...(p.terr === 1 ? [col("terreno", L[48], "08_Flujo!fila 48")] : []),
    col("ivaPag", L[49], "08_Flujo!fila 49 = −07_Fiscal!41"), col("ivaRec", L[50], "08_Flujo!fila 50 = 07_Fiscal!42"),
    col("ahorro", L[51], "08_Flujo!fila 51"), col("opex", L[52], "08_Flujo!fila 52"), col("peaje", L[53], "08_Flujo!fila 53"),
    ...(s[SCALAR_LABELS.Decom] > 0 ? [col("desm", L_DESM, "07_Fiscal!fila 25")] : []),
    col("imp", L[54], "08_Flujo!fila 54 = −07_Fiscal!37"),
    ...(p.rep === 1 ? [col("rep", L[55], "08_Flujo!fila 55")] : []),
    ...(p.terr === 1 ? [col("resid", L[56], "08_Flujo!fila 56")] : []),
    col("fcf", L[57], "FCF_u · 08_Flujo!fila 57", (r) => strong(r.fcf)),
    col("cum", L[58], "Cum_u · 08_Flujo!fila 58"),
    col("df", L[59], "08_Flujo!fila 59", (r) => <span className="text-ink-3">{fmtNum(r.df, 4)}</span>),
    col("fcfDesc", L[60], "08_Flujo!fila 60"),
    col("cumDesc", L[61], "08_Flujo!fila 61"),
  ];
  const colsB: Column<FlowRow>[] = [
    ...base,
    col("desemb", L[66], "08_Flujo!fila 66"), col("saldoIni", L[67], "08_Flujo!fila 67"),
    col("int", L[68], "Int · 08_Flujo!fila 68"), col("amort", L[69], "Amort · 08_Flujo!fila 69"),
    col("servicio", L[70], "08_Flujo!fila 70", (r) => strong(r.servicio)),
    col("saldoFin", L[71], "08_Flujo!fila 71"), col("idc", L[72], "08_Flujo!fila 72"),
    col("cfads", L[73], "CFADS · 08_Flujo!fila 73", (r) => strong(r.cfads)),
    col("dscr", L[74], "DSCR · 08_Flujo!fila 74", (r) => (r.dscr === null ? <span className="text-ink-3">—</span> : <span className={r.dscr < 1 ? "text-risk" : r.dscr < i.DSCR_Objetivo ? "text-warn-text" : "text-ink"}>{fmtX(r.dscr, 2)}</span>)),
    col("eq", L[75], "EQ · 08_Flujo!fila 75", (r) => strong(r.eq)),
    col("cumEq", L[76], "08_Flujo!fila 76"),
  ];

  // ---- deuda máxima por plazo (10 §H, casos Custom del Motor) ------------------------------------------------------------------------------
  const cx = m.cases[m.idx("custom")];
  const baseDeudaX = cx.result.scalars[SCALAR_LABELS.K] + cx.params.finT * cx.params.terr * cx.result.scalars[SCALAR_LABELS.Terr];
  const deudaMax = i.Sens_Plazos.map((plazo, j) => ({ plazo, lev: numOf(m.nameValue(`Deuda_Max_Plazo${j + 1}`)), name: `Deuda_Max_Plazo${j + 1}` }));
  const dmCols: Column<(typeof deudaMax)[number]>[] = [
    { key: "plazo", label: "Plazo", render: (r) => `${fmtNum(r.plazo, 0)} años` },
    { key: "lev", label: `Apalancamiento máximo (DSCR mín ≥ ${fmtX(i.DSCR_Objetivo, 2)})`, align: "right", render: (r) => (r.lev === null ? "—" : fmtPct(r.lev, 1)) },
    { key: "usd", label: "Deuda (USD, Custom)", align: "right", render: (r) => (r.lev === null ? "—" : fmtUSD(r.lev * baseDeudaX)) },
    { key: "n", label: "Nombre", render: (r) => <Trace name={r.name} cell="10_Sensibilidad §H" /> },
  ];

  const codYear = Number(i.Fecha_COD.slice(0, 4));
  const xTick = (t: number) => t === -1 || t % 5 === 0;
  const dscrSerie = rows.map((r) => (r.t >= 1 && r.t <= p.plazo ? r.dscr : null));

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Flujo de caja de SALELGI" sheet="08_Flujo">
        <Chip title="Caso seleccionado (Motor)">caso {c.name}</Chip>
        <Chip title="Fase_m1 · Meses_Construccion">t = −1: {fmtPct(i.Fase_m1, 0)} del CAPEX · t = 0: {fmtPct(1 - i.Fase_m1, 0)} · {fmtNum(p.ncon, 0)} meses de construcción</Chip>
        <Chip title="Tasa_Descuento · Tasa_Descuento_Equity">descuento {fmtPct(tasa, 1)} · accionista {fmtPct(req, 1)}</Chip>
        <Chip title="Apalancamiento · Tasa deuda · Plazo · Gracia del caso">
          {conDeuda ? <>deuda {fmtPct(p.lev, 0)} al {fmtPct(p.rd, 2)} · {fmtNum(p.plazo, 0)} años · {fmtNum(p.gr, 0)} de gracia</> : "sin deuda"}
        </Chip>
        <Chip title="Horizonte · Fecha_COD">horizonte {fmtNum(H, 0)} años · COD {codYear}</Chip>
      </ViewHeader>

      {/* ---- indicadores ------------------------------------------------------------------------------------------------------------- */}
      <Section title={L[5].replace("Custom", c.name)} guide="cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo · la tabla reproduce las filas 7–25 de la hoja">
        <div className="grid grid-cols-2 gap-x-8 gap-y-5 lg:grid-cols-4">
          <KpiTile
            label={L[11]}
            excelName="Payback_Simple"
            value={pbText(pb)}
            compare={<>{short(L[12])} @ {fmtPct(tasa, 0)}: {pbText(pbDesc)}{conDeuda && <> · del accionista: {pbText(pbEq)}</>}</>}
            strip={strip((k) => pbText(m.out(k, "PB")))}
          />
          <KpiTile
            label={L[13]}
            excelName="LCOE"
            value={lcoe === null ? "n/a" : `${fmtNum(lcoe, 1)} $/MWh`}
            state={lcoe === null ? "neutral" : lcoe <= tarifaMWh ? "ok" : "risk"}
            compare={<>{L[14]} {fmtNum(tarifaMWh, 1)} $/MWh · {L[15]} {ahorroKwh === null ? "n/a" : fmtPct(ahorroKwh, 1)}</>}
            strip={strip((k) => { const v = m.num(k, "LCOE"); return v === null ? "n/a" : fmtNum(v, 1); }, (k) => { const v = m.num(k, "LCOE"); return v !== null && v > tarifaMWh; })}
          />
          <KpiTile
            label={L[16]}
            excelName="Ahorro_Anio1"
            value={fmtUSD(a1)}
            compare={<>{L[17]} {fmtUSDCompact(sumAhorro, 2)} · {L[18]} {reduccion === null ? "—" : fmtPct(reduccion, 1)}<Frozen what="Factura de referencia (denominador)" /></>}
            strip={strip((k) => fmtUSD(m.num(k, "Ahorro1")))}
          />
          <KpiTile
            label={L[19]}
            excelName={conDeuda ? "Aporte_Equity" : "08_Flujo!D19"}
            value={fmtUSDCompact(conDeuda ? aporteEq : aporteU, 2)}
            compare={conDeuda ? <>sin deuda {fmtUSDCompact(aporteU, 2)} · {LECTURA[19]}</> : <>{LECTURA[19]}</>}
            strip={strip((k) => fmtUSDCompact(m.cases[k].result.scalars[SCALAR_LABELS.D] > 0 ? m.num(k, "Aporte_eq") : aporteUOf(k), 2))}
          />
        </div>
        <DataTable columns={indCols} rows={ind} rowKey={(r) => String(r.row)} sectionBefore={(r) => (r.row === 7 ? "Sin deuda vs con deuda" : r.row === 20 ? "Deuda" : null)} />
        <Note>{L[26]}</Note>
      </Section>

      {/* ---- cinta anual ------------------------------------------------------------------------------------------------------------- */}
      <Section title="Cinta anual · flujo libre sin deuda y acumulado" guide="barras = flujo del año (construcción en gris oscuro), línea = acumulado, punto = payback · pase el cursor por un año" aside={<Trace name="FCF_u · Cum_u" cell="08_Flujo!D57:AD58" />}>
        <CintaAnual t={T_AXIS} fcf={b.FCF_u} cum={b.Cum_u} lineColor={`var(${meta.colorVar})`} lineDash={`var(${meta.dashVar})`} codYear={codYear} payback={typeof pb === "number" ? pb : null} />
      </Section>

      {/* ---- A · sin deuda ----------------------------------------------------------------------------------------------------------- */}
      <Section title={L[46]} guide="filas 47–61 de la hoja, un año por fila (USD); las columnas que en este caso son 0 en todos los años se omiten" aside={<Trace name="FCF_u" cell="08_Flujo!D47:AD61" />}>
        <DataTable
          size="sm"
          columns={colsA}
          rows={rows}
          rowKey={(r) => String(r.t)}
          muted={(r) => r.t > H}
          caption="La cabecera abreviada lleva la etiqueta completa de la hoja en el tooltip. El flujo de caja libre es el bloque FCF_u del Motor; la suma de las columnas anteriores coincide con él en todos los años."
          footer={
            <>
              {p.terr === 1 ? null : <>«{L[48]}» y «{L[56]}» se omiten: en este caso el terreno no lo compra SALELGI. </>}
              {p.rep === 1 ? null : <>«{L[55]}» se omite: el reemplazo de inversores no lo paga SALELGI en este caso. </>}
              {s[SCALAR_LABELS.Decom] > 0 ? <>La columna «{L_DESM}» viene de 07_Fiscal (fila 25): el Motor la resta dentro del EBITDA y 08_Flujo no la desglosa. </> : null}
            </>
          }
        />
      </Section>

      {/* ---- B · con deuda ----------------------------------------------------------------------------------------------------------- */}
      <Section title={L[63]} guide={conDeuda ? "filas 64–76 de la hoja, un año por fila (USD; DSCR en x)" : undefined} aside={<Trace name="Deuda_Monto · Deuda_Total · IDC · Cuota" cell="08_Flujo!D64:J65" />}>
        {conDeuda ? (
          <>
            <dl className="grid gap-x-8 gap-y-1 text-[12.5px] sm:grid-cols-2 lg:grid-cols-4">
              <Fila label={L[64]} value={fmtUSD(D)} trace={<Trace name="Deuda_Monto" cell="08_Flujo!D64" />} />
              <Fila label={L_IDC} value={fmtUSD(IDC)} trace={<Trace name="IDC" cell="08_Flujo!J64" />} />
              <Fila label={L[65]} value={fmtUSD(Dt)} trace={<Trace name="Deuda_Total" cell="08_Flujo!D65" />} />
              <Fila label={L_CUOTA} value={fmtUSD(PMT)} trace={<Trace name="Cuota" cell="08_Flujo!J65" />} />
            </dl>
            <DataTable
              size="sm"
              columns={colsB}
              rows={rows}
              rowKey={(r) => String(r.t)}
              muted={(r) => r.t > Math.max(H, p.plazo)}
              caption={`Deuda del caso: ${fmtPct(p.lev, 0)} de ${fmtUSD(K + p.finT * p.terr * Terr)} (${p.finT === 1 && p.terr === 1 ? "CAPEX + terreno" : "CAPEX industrial"}) al ${fmtPct(p.rd, 2)}, ${fmtNum(p.plazo, 0)} años con ${fmtNum(p.gr, 0)} de gracia; ${fmtNum(s[SCALAR_LABELS.n], 0)} cuotas.`}
            />
            <div className="grid gap-8 lg:grid-cols-2">
              <div className="flex flex-col gap-2">
                <h3 className="text-[12px] font-medium text-ink-2">{L[74]} frente al objetivo · {L[78]}</h3>
                <Series
                  x={T_AXIS}
                  xTick={xTick}
                  series={[{ id: "dscr", label: L[74], values: dscrSerie, color: "var(--cat-1)", bars: true }]}
                  refLine={{ value: i.DSCR_Objetivo, label: `DSCR objetivo ${fmtX(i.DSCR_Objetivo, 2)}` }}
                  yFormat={(v) => fmtX(v, 2)}
                  height={200}
                  ariaLabel="DSCR por año frente al DSCR objetivo"
                />
                <p className="text-[11.5px] text-ink-3">{f20 === "—" ? "—" : <Status kind={statusOf(f20)}>{stripGlyph(f20)}</Status>}</p>
              </div>
              <div className="flex flex-col gap-2">
                <h3 className="text-[12px] font-medium text-ink-2">{L[75]} y {L[76].toLowerCase()}</h3>
                <Series
                  x={T_AXIS}
                  xTick={xTick}
                  series={[
                    { id: "eq", label: L[75], values: rows.map((r) => r.eq), color: "var(--cat-2)", bars: true },
                    { id: "cum", label: L[76], values: rows.map((r) => r.cumEq), color: `var(${meta.colorVar})`, dash: `var(${meta.dashVar})` },
                  ]}
                  yFormat={(v) => fmtUSDCompact(v, 1)}
                  height={200}
                  ariaLabel="Flujo del accionista por año y acumulado"
                />
                <p className="text-[11.5px] text-ink-3">payback del accionista: {pbText(pbEq)} · {L[19]}: {fmtUSD(aporteEq)}</p>
              </div>
            </div>
          </>
        ) : (
          <Note>Este caso no lleva deuda (Deuda = 0): las filas 64–76 son 0, el flujo del accionista coincide con el flujo libre del proyecto y no hay DSCR.</Note>
        )}
      </Section>

      {/* ---- deuda máxima por plazo ------------------------------------------------------------------------------------------------ */}
      <Section title="Deuda máxima por plazo (10 §H)" guide={`apalancamiento con DSCR mínimo ≥ ${fmtX(i.DSCR_Objetivo, 2)} para cada plazo de Sens_Plazos, interpolado entre los puntos de Sweep_Lev; los casos del Motor parten del Custom`}>
        <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(260px,2fr)]">
          <DataTable columns={dmCols} rows={deudaMax} rowKey={(r) => String(r.plazo)} selected={(r) => conDeuda && r.plazo === p.plazo && caseId === "custom"} />
          <Note>
            {conDeuda
              ? `El caso ${c.name} lleva ${fmtPct(p.lev, 0)} a ${fmtNum(p.plazo, 0)} años` + (typeof dscrMin === "number" ? ` con DSCR mínimo ${fmtX(dscrMin, 2)}${anioMin !== null ? ` en t = ${anioMin}` : ""}` : "") + "."
              : `El caso ${c.name} no lleva deuda.`}{" "}
            La matriz tasa × plazo y el detalle del barrido de apalancamiento están en Sensibilidad §D y §H.
          </Note>
        </div>
      </Section>
    </div>
  );
}

/** Fila etiqueta · valor · rastro para listas de definición compactas. */
function Fila({ label, value, trace }: { label: ReactNode; value: ReactNode; trace?: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-t border-hairline pt-2">
      <dt className="text-[10.5px] font-medium uppercase leading-tight tracking-[0.06em] text-ink-3">{label}</dt>
      <dd className="text-[16px] font-semibold text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>{value}</dd>
      {trace}
    </div>
  );
}
