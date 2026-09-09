import { useMemo, type ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { KpiTile, type StripValue } from "@/components/KpiTile";
import { Trace } from "@/components/Live";
import { Status, stripGlyph } from "@/components/Status";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { Series } from "@/components/charts/Series";
import { StackedBars } from "@/components/charts/StackedBars";
import { edate, parseISODate, SCALAR_LABELS, T_AXIS, type CaseParams, type CaseResult, type Inputs } from "@/engine";
import { fmtNum, fmtPct, fmtUSD, fmtUSDCompact } from "@/lib/format";
import { CASES, type CaseId, type ViewId } from "@/lib/views";
import { statusOf } from "@/model/book";
import { useModel } from "@/model/store";

/**
 * Fiscal (hoja 07_Fiscal): impuestos incrementales de SALELGI para el caso seleccionado. Las filas que son bloques del Motor
 * (Ahorro, OPEX, Peaje, EBITDA, Part_u, IR_u, PoolU, Int, Part_l, IR_l, PoolL) se toman tal cual; las que en la hoja son
 * combinaciones (depreciación por componente, deducción adicional del año, IVA pagado/recuperado, impuestos = participación + IR,
 * escudo de los intereses, tasa efectiva) se recomponen aquí con las mismas fórmulas de `computeCase` (verificado contra el
 * libro para el Custom, celda a celda, filas 7–16, 19, 22–38, 41–42 y 45–52).
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

/** Etiquetas de la columna B de 07_Fiscal (texto oficial del libro, verbatim). */
const L: Record<number, string> = {
  5: "Cifras fiscales clave",
  7: "CAPEX depreciable (sin IVA; + IVA si no se recupera)",
  8: "Deducción adicional anual (años 1–10, topada; 0 si Aplica_DedAd = No)",
  9: "¿El tope del 5 % de ingresos es vinculante?",
  10: "Ingreso mínimo para deducir el 100 % (tope 5 %)",
  12: "Totales del horizonte",
  13: "Impuestos incrementales sin deuda (Σ)",
  14: "Impuestos incrementales con deuda (Σ)",
  15: "Escudo de la deducción adicional (Σ, a la tasa de IR)",
  16: "IVA total pagado / recuperado",
  18: "Año (t)",
  19: "Año calendario (inicio del período)",
  21: "A · Sin deuda (proyecto puro)",
  22: "Ahorro por energía evitada (energía valorizable × tarifa)",
  23: "OPEX SALELGI (× Factor_OPEX del caso)",
  24: "Peaje SGDA: energía inyectada × $/kWh + potencia AC × $/kW-mes × 12",
  25: "Desmantelamiento en t = Horizonte (gasto deducible)",
  26: "EBITDA incremental (ahorro − OPEX − peaje − desmantelamiento)",
  27: "Depreciación equipos (10 años)",
  28: "Depreciación obra civil (20 años)",
  29: "Depreciación del reemplazo de inversores (si lo paga SALELGI; 10 años o hasta el horizonte)",
  30: "Utilidad contable incremental antes de participación",
  31: "Participación laboral 15 % (absorción limitada si hay utilidad gravable)",
  32: "Utilidad antes de IR",
  33: "Deducción adicional 100 % (art. 10.7, topada)",
  34: "Base imponible incremental",
  35: "Pool de pérdidas arrastradas (art. 11 LRTI, ≤ 25 %/año) — sólo con utilidad gravable limitada",
  36: "Impuesto a la Renta 25 % (con absorción limitada y arrastre si hay utilidad gravable)",
  37: "Impuestos incrementales (participación + IR)",
  38: "Tasa efectiva sobre EBITDA",
  40: "B · IVA del CAPEX (capital de trabajo si es recuperable)",
  41: "IVA pagado",
  42: "IVA recuperado (período siguiente)",
  44: "C · Con deuda (intereses deducibles)",
  45: "Intereses de la deuda",
  46: "Utilidad contable antes de participación (con intereses)",
  47: "Participación laboral 15 % (absorción limitada si hay utilidad gravable)",
  48: "Base imponible (con intereses)",
  49: "Pool de pérdidas arrastradas con deuda",
  50: "Impuesto a la Renta 25 % (con absorción limitada y arrastre si hay utilidad gravable)",
  51: "Impuestos incrementales con deuda",
  52: "Escudo fiscal de los intereses",
};

/** Cabecera de columna: la etiqueta oficial hasta el primer paréntesis / dos puntos / raya (el texto completo va en el tooltip). */
const short = (s: string): string => {
  const cut = s.search(/ \(|:| — /);
  return cut > 0 ? s.slice(0, cut) : s;
};
const n = (v: number | null | undefined): number => (typeof v === "number" ? v : 0);

interface FiscalRow {
  t: number;
  anio: number;
  ahorro: number; opex: number; peaje: number; desm: number; ebitda: number;
  depEq: number; depCiv: number; depRep: number; utilAP: number; part: number; utilAIR: number; dedad: number; base: number;
  pool: number; ir: number; imp: number; tasaEf: number;
  ivaPag: number; ivaRec: number;
  int: number; utilAPl: number; partL: number; baseL: number; poolL: number; irL: number; impL: number; escudo: number;
}

/** Filas 22–52 de 07_Fiscal para un caso: bloques del Motor + recomposiciones con las fórmulas de computeCase. */
function fiscalRows(i: Inputs, p: CaseParams, res: CaseResult): FiscalRow[] {
  const s = res.scalars, b = res.blocks;
  const H = i.Horizonte, VFE = i.Vida_Fiscal_Equipos, VFC = i.Vida_Fiscal_Civil, RA = i.Reemplazo_Anio, fase = i.Fase_m1;
  const IVA = s[SCALAR_LABELS.IVA], DepEq = s[SCALAR_LABELS.DepEq], DepCiv = s[SCALAR_LABELS.DepCiv], DedAd = s[SCALAR_LABELS.DedAd];
  const Krep = s[SCALAR_LABELS.Krep], Decom = s[SCALAR_LABELS.Decom];
  const cod = parseISODate(i.Fecha_COD);
  return T_AXIS.map((t, k) => {
    const ahorro = n(b.Ahorro[k]), opex = n(b.OPEX[k]), peaje = n(b.Peaje[k]), ebitda = n(b.EBITDA[k]), dep = n(b.Dep[k]);
    const part = n(b.Part_u[k]), ir = n(b.IR_u[k]), int = n(b.Int[k]), partL = n(b.Part_l[k]), irL = n(b.IR_l[k]);
    // 07!25 =IF(t=Horizonte, Desmantelamiento_USD, 0)
    const desm = t === H ? Decom : 0;
    // 07!27 =IF(AND(t>=1,t<=Vida_Fiscal_Equipos), CAPEX_Depreciable*(1-Pct_CAPEX_Civil)/Vida_Fiscal_Equipos, 0)  (= Dep. equipos/año del Motor)
    const depEq = t >= 1 && t <= VFE ? DepEq : 0;
    // 07!28 =IF(AND(t>=1,t<=Vida_Fiscal_Civil,t<=Horizonte), CAPEX_Depreciable*Pct_CAPEX_Civil/Vida_Fiscal_Civil, 0)
    const depCiv = t >= 1 && t <= VFC && t <= H ? DepCiv : 0;
    // 07!29 =IF(AND(Reemplazo_Pagador="SALELGI", Reemplazo_Anio<Horizonte, t>Reemplazo_Anio, t<=MIN(Horizonte, Reemplazo_Anio+Vida)), Reemplazo_USD/MIN(Vida, Horizonte-Reemplazo_Anio), 0)
    const depRep = p.rep === 1 && RA < H && t > RA && t <= Math.min(H, RA + VFE) ? Krep / Math.min(VFE, H - RA) : 0;
    // 07!33 =IF(AND(t>=1,t<=Vida_Fiscal_Equipos), DedAd_Anual, 0)
    const dedad = t >= 1 && t <= VFE ? DedAd : 0;
    const utilAP = ebitda - dep;                 // 07!30
    const utilAIR = utilAP - part;               // 07!32
    const base = utilAIR - dedad;                // 07!34
    const imp = part + ir;                       // 07!37
    const tasaEf = ebitda !== 0 ? imp / ebitda : 0; // 07!38
    // 07!41 =IF(t=-1, IVA_Total*Fase_m1, IF(t=0, IVA_Total*(1-Fase_m1), 0)) ; 07!42 =IF(IVA_Recuperable="Sí", IF(t=0, IVA*Fase_m1, IF(t=1, IVA*(1-Fase_m1), 0)), 0)
    const ivaPag = t === -1 ? IVA * fase : t === 0 ? IVA * (1 - fase) : 0;
    const ivaRec = p.iva === 1 ? (t === 0 ? IVA * fase : t === 1 ? IVA * (1 - fase) : 0) : 0;
    const utilAPl = ebitda - dep - int;          // 07!46
    const baseL = utilAPl - partL - dedad;       // 07!48
    const impL = partL + irL;                    // 07!51
    return {
      t, anio: edate(cod, 12 * (t - 1)).y,
      ahorro, opex, peaje, desm, ebitda, depEq, depCiv, depRep, utilAP, part, utilAIR, dedad, base,
      pool: n(b.PoolU[k]), ir, imp, tasaEf, ivaPag, ivaRec,
      int, utilAPl, partL, baseL, poolL: n(b.PoolL[k]), irL, impL, escudo: imp - impL,
    };
  });
}

const sum = (rows: FiscalRow[], f: (r: FiscalRow) => number): number => rows.reduce((a, r) => a + f(r), 0);

export function Fiscal({ caseId }: Props) {
  const m = useModel();
  const ci = m.idx(caseId);
  const c = m.cases[ci];
  const i = m.inputs, d = m.derived, p = c.params, s = c.result.scalars;
  const H = i.Horizonte, VFE = i.Vida_Fiscal_Equipos, VFC = i.Vida_Fiscal_Civil;
  const K = s[SCALAR_LABELS.K], IVA = s[SCALAR_LABELS.IVA], Kdep = s[SCALAR_LABELS.Kdep], DedAd = s[SCALAR_LABELS.DedAd];
  const rows = useMemo(() => fiscalRows(i, p, c.result), [i, p, c.result]);

  // ---- filas 7–16 ----------------------------------------------------------------------------------------------------------------------
  // 07!D9 =IF(Aplica_DedAd="No","◇ n/a — sin deducción adicional (Aplica_DedAd = No)",IF(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos>Tope_DedAd_Pct*Ingresos_SALELGI,"▲ SÍ — tope activo","● No — cabe completa"))
  const dedSinTope = Kdep * i.Pct_Elegible_DedAd / VFE;
  const topeTexto = p.dedad === 0
    ? "◇ n/a — sin deducción adicional (Aplica_DedAd = No)"
    : dedSinTope > i.Tope_DedAd_Pct * i.Ingresos_SALELGI ? "▲ SÍ — tope activo" : "● No — cabe completa";
  // 07!D10 =CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos/Tope_DedAd_Pct
  const ingresoMin = i.Tope_DedAd_Pct > 0 ? dedSinTope / i.Tope_DedAd_Pct : null;
  const sumImpU = sum(rows, (r) => r.imp), sumImpL = sum(rows, (r) => r.impL);
  const sumPartU = sum(rows, (r) => r.part), sumIrU = sum(rows, (r) => r.ir);
  const escudoDedAd = sum(rows, (r) => r.dedad) * i.Tasa_IR;      // 07!D15 =SUM(fila 33)*Tasa_IR
  const ivaPagado = sum(rows, (r) => r.ivaPag), ivaRecuperado = sum(rows, (r) => r.ivaRec);

  const others = CASES.filter((x) => x.id !== caseId);
  const strip = (f: (k: number) => number, fmt: (v: number) => string): StripValue[] => others.map((x) => ({ caseId: x.id, text: fmt(f(m.idx(x.id))) }));
  const sumCase = (k: number, key: "imp" | "impL") => sum(fiscalRows(i, m.cases[k].params, m.cases[k].result), (r) => r[key]);

  // ---- tablas ---------------------------------------------------------------------------------------------------------------------------
  const usd = (v: number): ReactNode => (Math.abs(v) < 0.5 ? <span className="text-ink-3">0</span> : fmtNum(v, 0));
  const col = (key: keyof FiscalRow, row: number, render?: (r: FiscalRow) => ReactNode): Column<FiscalRow> => ({
    key,
    label: short(L[row]),
    title: `${L[row]} · 07_Fiscal!fila ${row}`,
    align: "right",
    render: render ?? ((r) => usd(r[key] as number)),
  });
  const base: Column<FiscalRow>[] = [
    { key: "t", label: L[18], title: "07_Fiscal!fila 18", align: "right", mono: true, nowrap: true, render: (r) => (r.t === 0 ? "0 · COD" : fmtNum(r.t, 0)) },
    { key: "anio", label: "Año calendario", title: `${L[19]} · 07_Fiscal!fila 19`, align: "right", muted: true, render: (r) => String(r.anio) },
  ];
  const conPool = p.ug >= 0;
  const colsA: Column<FiscalRow>[] = [
    ...base,
    col("ahorro", 22), col("opex", 23), col("peaje", 24),
    ...(s[SCALAR_LABELS.Decom] > 0 ? [col("desm", 25)] : []),
    col("ebitda", 26, (r) => <span className="font-medium text-ink">{usd(r.ebitda)}</span>),
    col("depEq", 27), col("depCiv", 28),
    ...(p.rep === 1 ? [col("depRep", 29)] : []),
    col("utilAP", 30), col("part", 31), col("utilAIR", 32), col("dedad", 33), col("base", 34),
    ...(conPool ? [col("pool", 35)] : []),
    col("ir", 36),
    col("imp", 37, (r) => <span className="font-medium text-ink">{usd(r.imp)}</span>),
    col("tasaEf", 38, (r) => (r.ebitda === 0 ? <span className="text-ink-3">—</span> : fmtPct(r.tasaEf, 1))),
  ];
  const colsB: Column<FiscalRow>[] = [...base, col("ivaPag", 41), col("ivaRec", 42)];
  const colsC: Column<FiscalRow>[] = [
    ...base,
    col("int", 45), col("utilAPl", 46), col("partL", 47), col("baseL", 48),
    ...(conPool ? [col("poolL", 49)] : []),
    col("irL", 50),
    col("impL", 51, (r) => <span className="font-medium text-ink">{usd(r.impL)}</span>),
    col("escudo", 52),
  ];
  const rowsB = rows.filter((r) => r.t >= -1 && r.t <= 1);

  interface ClaveRow { row: number; unidad: string; valor: ReactNode; trace: string }
  const claves: ClaveRow[] = [
    { row: 7, unidad: "USD", valor: fmtUSD(Kdep), trace: "CAPEX_Depreciable · 07_Fiscal!D7" },
    { row: 8, unidad: "USD/año", valor: fmtUSD(DedAd), trace: "DedAd_Anual · 07_Fiscal!D8" },
    { row: 9, unidad: "", valor: <Status kind={statusOf(topeTexto)}>{stripGlyph(topeTexto)}</Status>, trace: "07_Fiscal!D9" },
    { row: 10, unidad: "USD/año", valor: ingresoMin === null ? "—" : fmtUSD(ingresoMin), trace: "07_Fiscal!D10" },
    { row: 13, unidad: "USD", valor: fmtUSD(sumImpU), trace: "07_Fiscal!D13 = Σ fila 37" },
    { row: 14, unidad: "USD", valor: fmtUSD(sumImpL), trace: "07_Fiscal!D14 = Σ fila 51" },
    { row: 15, unidad: "USD", valor: fmtUSD(escudoDedAd), trace: "07_Fiscal!D15 = Σ fila 33 × Tasa_IR" },
    { row: 16, unidad: "USD", valor: <>{fmtUSD(ivaPagado)} <span className="text-ink-3">/</span> {fmtUSD(ivaRecuperado)}</>, trace: "07_Fiscal!D16:E16" },
  ];
  const clavesCols: Column<ClaveRow>[] = [
    { key: "ind", label: "Indicador", render: (r) => L[r.row] },
    { key: "u", label: "Unidad", muted: true, nowrap: true, render: (r) => r.unidad },
    { key: "v", label: "Valor", align: "right", nowrap: true, render: (r) => r.valor },
    { key: "tr", label: "Celda", render: (r) => <Trace cell={r.trace} /> },
  ];

  const xTick = (t: number) => t === -1 || t % 5 === 0;

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Fiscal" sheet="07_Fiscal">
        <Chip title="Caso seleccionado (Motor)">caso {c.name}</Chip>
        <Chip title="Tasa_Participacion · Participación (1/0) del caso">Participación laboral {fmtPct(i.Tasa_Participacion, 0)}: {p.part === 1 ? "Sí" : "No"}</Chip>
        <Chip title="Tasa_IR">IR {fmtPct(i.Tasa_IR, 0)}</Chip>
        <Chip title="Tasa_Efectiva · 01_Supuestos!C142">Tasa efectiva {fmtPct(d.Tasa_Efectiva, 2)}</Chip>
        <Chip title="Escudo_Negativo">Escudo_Negativo {i.Escudo_Negativo}</Chip>
        <Chip title="Utilidad_Gravable_SALELGI (vacía = ilimitada)">Utilidad gravable: {p.ug < 0 ? "ilimitada" : fmtUSD(p.ug)}</Chip>
        <Chip title="Aplica_DedAd · Pct_Elegible_DedAd · Tope_DedAd_Pct · Ingresos_SALELGI">
          Deducción adicional: {p.dedad === 1 ? "Sí" : "No"} · {fmtPct(i.Pct_Elegible_DedAd, 0)} elegible · tope {fmtPct(i.Tope_DedAd_Pct, 0)} de {fmtUSDCompact(i.Ingresos_SALELGI, 0)}
        </Chip>
        <Chip title="Vida_Fiscal_Equipos · Vida_Fiscal_Civil">Vida fiscal {fmtNum(VFE, 0)} / {fmtNum(VFC, 0)} años</Chip>
        <Chip title="IVA recuperable (1/0) del caso">IVA recuperable: {p.iva === 1 ? "Sí" : "No"}</Chip>
      </ViewHeader>

      {/* ---- filas 7–16 ---------------------------------------------------------------------------------------------------------------- */}
      <Section title={L[5]} guide={`caso ${c.name} · cifra grande = caso seleccionado; debajo, los otros tres casos`}>
        <div className="grid grid-cols-2 gap-x-8 gap-y-5 lg:grid-cols-4">
          <KpiTile
            label={L[7]}
            excelName="CAPEX_Depreciable"
            value={fmtUSDCompact(Kdep, 2)}
            compare={<>CAPEX industrial {fmtUSD(K)} · IVA {fmtUSD(IVA)} · IVA recuperable: {p.iva === 1 ? "Sí" : "No"}</>}
            strip={strip((k) => m.cases[k].result.scalars[SCALAR_LABELS.Kdep], (v) => fmtUSDCompact(v, 2))}
          />
          <KpiTile
            label={L[8]}
            excelName="DedAd_Anual"
            value={fmtUSD(DedAd)}
            compare={<Status kind={statusOf(topeTexto)}>{stripGlyph(topeTexto)}</Status>}
            strip={strip((k) => m.cases[k].result.scalars[SCALAR_LABELS.DedAd], (v) => fmtUSD(v))}
          />
          <KpiTile
            label={L[13]}
            excelName="07_Fiscal!D13"
            value={fmtUSDCompact(sumImpU, 2)}
            compare={<>participación Σ {fmtUSD(sumPartU)} + IR Σ {fmtUSD(sumIrU)}</>}
            strip={strip((k) => sumCase(k, "imp"), (v) => fmtUSDCompact(v, 2))}
          />
          <KpiTile
            label={L[14]}
            excelName="07_Fiscal!D14"
            value={fmtUSDCompact(sumImpL, 2)}
            compare={<>{L[52]} Σ {fmtUSD(sumImpU - sumImpL)}</>}
            strip={strip((k) => sumCase(k, "impL"), (v) => fmtUSDCompact(v, 2))}
          />
        </div>
        <DataTable columns={clavesCols} rows={claves} rowKey={(r) => String(r.row)} sectionBefore={(r) => (r.row === 13 ? L[12] : null)} />
      </Section>

      {/* ---- A · sin deuda ------------------------------------------------------------------------------------------------------------- */}
      <Section
        title={L[21]}
        guide="barras = participación e IR del año sin deuda (filas 31 y 36); línea = impuestos con deuda (fila 51) · pase el cursor por un año"
        aside={<Trace name="Part_u · IR_u" cell="07_Fiscal!D31:AD31 · D36:AD36" />}
      >
        <StackedBars
          x={T_AXIS}
          xTick={xTick}
          stacks={[
            { id: "part", label: short(L[31]), values: rows.map((r) => r.part), color: "var(--cat-1)" },
            { id: "ir", label: short(L[36]), values: rows.map((r) => r.ir), color: "var(--cat-2)" },
          ]}
          line={s[SCALAR_LABELS.D] > 0 ? { label: L[51], values: rows.map((r) => r.impL), color: "var(--cat-3)" } : undefined}
          yFormat={(v) => fmtUSDCompact(v, 1)}
          height={210}
          ariaLabel="Impuestos incrementales por año: participación e IR sin deuda, e impuestos con deuda"
        />
        <DataTable
          size="sm"
          columns={colsA}
          rows={rows}
          rowKey={(r) => String(r.t)}
          muted={(r) => r.t < 1 || r.t > H}
          caption={`Filas 22–38 de la hoja para el caso ${c.name}, un año por fila (USD; la tasa efectiva en %). La cabecera abreviada lleva la etiqueta completa de la hoja en el tooltip.`}
          footer={
            <>
              {s[SCALAR_LABELS.Decom] > 0 ? null : <>La columna «{L[25]}» se omite porque Desmantelamiento_Pct = 0 en este caso. </>}
              {p.rep === 1 ? null : <>La columna «{short(L[29])}» se omite porque el reemplazo de inversores no lo paga SALELGI en este caso. </>}
              {conPool ? null : <>Las columnas del pool de pérdidas (filas 35 y 49) se omiten: ver la nota al pie de la sección C.</>}
            </>
          }
        />
      </Section>

      {/* ---- B · IVA ------------------------------------------------------------------------------------------------------------------- */}
      <Section
        title={L[40]}
        guide="sólo los años con movimiento (t = −1, 0 y 1); el resto de la fila es 0"
        aside={<Trace name="IVA_Total · Fase_m1 · IVA_Recuperable" cell="07_Fiscal!D41:F42" />}
      >
        <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(260px,2fr)]">
          <DataTable columns={colsB} rows={rowsB} rowKey={(r) => String(r.t)} />
          <Note>
            IVA del CAPEX del caso {fmtUSD(IVA)}: {fmtPct(i.Fase_m1, 0)} pagado en t = −1 y {fmtPct(1 - i.Fase_m1, 0)} en t = 0.{" "}
            {p.iva === 1
              ? `Recuperable (IVA_Recuperable = Sí): cada tramo vuelve en el período siguiente (t = 0 y t = 1); Σ recuperado ${fmtUSD(ivaRecuperado)}.`
              : "No recuperable (IVA_Recuperable = No): no vuelve y se suma al CAPEX depreciable (fila 7)."}
          </Note>
        </div>
      </Section>

      {/* ---- C · con deuda ------------------------------------------------------------------------------------------------------------- */}
      <Section
        title={L[44]}
        guide={
          s[SCALAR_LABELS.D] > 0
            ? `deuda del caso: ${fmtPct(p.lev, 0)} al ${fmtPct(p.rd, 2)} · ${fmtNum(p.plazo, 0)} años (${fmtNum(p.gr, 0)} de gracia) · barras = escudo fiscal de los intereses (fila 52), línea = intereses (fila 45)`
            : "este caso no lleva deuda"
        }
        aside={<Trace name="Int · Part_l · IR_l" cell="07_Fiscal!D45:AD52" />}
      >
        {s[SCALAR_LABELS.D] > 0 ? (
          <>
            <Series
              x={T_AXIS}
              xTick={xTick}
              series={[
                { id: "escudo", label: L[52], values: rows.map((r) => r.escudo), color: "var(--cat-1)", bars: true },
                { id: "int", label: L[45], values: rows.map((r) => (r.t >= 1 && r.t <= p.plazo ? r.int : null)), color: "var(--cat-2)" },
              ]}
              yFormat={(v) => fmtUSDCompact(v, 1)}
              height={200}
              ariaLabel="Escudo fiscal de los intereses e intereses de la deuda por año"
            />
            <DataTable
              size="sm"
              columns={colsC}
              rows={rows}
              rowKey={(r) => String(r.t)}
              muted={(r) => r.t < 1 || r.t > H}
              caption={`Filas 45–52 de la hoja para el caso ${c.name} (USD). Los intereses son los del cuadro de la deuda de 08_Flujo (fila 68).`}
            />
          </>
        ) : (
          <Note>Este caso no lleva deuda (Deuda = 0): las filas 45–52 coinciden con las de la sección A y el escudo fiscal de los intereses es 0.</Note>
        )}
        {conPool ? (
          <Note>
            Utilidad gravable de SALELGI limitada a {fmtUSD(p.ug)} por año (Utilidad_Gravable_SALELGI): las pérdidas incrementales se absorben hasta ese
            importe y el resto entra en el pool de arrastre (filas 35 y 49), que se compensa cada año hasta el 25 % de la utilidad gravable del año
            (base incremental + Utilidad_Gravable_SALELGI), art. 11 LRTI.
          </Note>
        ) : (
          <Note>
            Utilidad_Gravable_SALELGI está vacía: la utilidad gravable es ilimitada y el pool de arrastre (filas 35 y 49) no aplica.{" "}
            {i.Escudo_Negativo === "Sí"
              ? "Con Escudo_Negativo = Sí, las pérdidas incrementales se absorben sin límite: participación e IR negativos actúan como escudo en el año."
              : "Con Escudo_Negativo = No, la participación y el IR negativos se truncan a 0 (MAX(0, ·))."}
          </Note>
        )}
      </Section>
    </div>
  );
}
