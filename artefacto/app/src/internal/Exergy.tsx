import { useMemo, type ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { KpiTile, type StripValue } from "@/components/KpiTile";
import { Trace } from "@/components/Live";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { Series } from "@/components/charts/Series";
import { StackedBars, type StackDef } from "@/components/charts/StackedBars";
import { edate, irr, parseISODate, SCALAR_LABELS, T_AXIS, vanMotor, type CaseParams, type CaseResult, type Derived, type Inputs } from "@/engine";
import { fmtNum, fmtPct, fmtUSD, fmtUSDCompact } from "@/lib/format";
import { CASES, type CaseId, type ViewId } from "@/lib/views";
import { opexLines } from "@/model/opex";
import { useModel } from "@/model/store";

/**
 * Negocio Exergy (hoja 09_Exergy) — vista INTERNA (src/internal/, sólo detrás de `process.env.VITE_EDITION !== "externo"`).
 * Bloques del Motor tal cual: Ux (utilidad operativa), Ix (impuestos), Tx (terreno: compra en t = −1, residual en t = H), Fx, Gx.
 * Filas recompuestas con las fórmulas de la hoja/computeCase: fee y costo interno de gerencia por fase, arriendo, predial, fee y
 * costo propio de O&M (opexLines sin el factor OPEX del caso, como el bloque Ux), reemplazo a cargo de Exergy, acumulado, factor
 * de descuento (todos los t), VAN por línea (SUMPRODUCT con el factor de descuento), rendimiento del arriendo, carga para SALELGI,
 * factor de anualidad escalado (Ann_Esc) y VAN del grupo (misma convención que el Motor). Verificado celda a celda para el Custom.
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

/** Marcador de exclusión física: check-exclusion.mjs exige que esta cadena NO exista en el bundle externo. */
export const EXERGY_VIEW_MARKER = "EXERGY_VIEW_MARKER_7C1D";

/** Etiquetas de la columna B de 09_Exergy (texto oficial del libro, verbatim). */
const L: Record<number, string> = {
  5: "Indicadores del negocio Exergy",
  7: "VAN del negocio Exergy @ tasa de descuento",
  8: "TIR del negocio Exergy",
  9: "Ingreso neto nominal acumulado (Σ FCF)",
  10: "VAN línea gerencia (antes de impuestos)",
  11: "VAN línea terreno (antes de impuestos)",
  12: "VAN línea O&M (antes de impuestos)",
  13: "Rendimiento bruto del arriendo sobre el precio del terreno",
  14: "Costo anual de Exergy para SALELGI (fee O&M + arriendo) / ahorro año 1",
  15: "VAN Exergy y TIR del grupo en los cuatro casos → 10 §A",
  35: "Año (t)",
  36: "Año calendario (inicio del período)",
  38: "Flujo de caja de Exergy",
  39: "Fee de gerencia del proyecto (+)",
  40: "Costo interno de gerencia (−)",
  41: "Compra del terreno incl. costos de transacción (−) — si Exergy es la compradora",
  42: "Arriendo del terreno cobrado a SALELGI (+)",
  43: "Predial y gastos del terreno (−)",
  44: "Fee de O&M cobrado a SALELGI (+)",
  45: "Costo propio de O&M (−)",
  46: "Reemplazo de inversores a cargo de Exergy (−), con la reserva del fee de O&M",
  47: "Utilidad operativa antes de impuestos (sin compra/venta de terreno)",
  48: "Impuestos Exergy (participación + IR sobre utilidad positiva)",
  49: "Valor residual del terreno, neto de impuesto sobre la ganancia (+)",
  50: "Flujo de caja de Exergy",
  51: "Acumulado",
  52: "Factor de descuento",
  54: "Sensibilidad del negocio Exergy (ΔVAN lineal, neto de impuestos) y carga para SALELGI",
  55: "Factor de anualidad escalado Σ (1+esc)^(t−1)/(1+r)^t, t = 1…horizonte",
  68: "Memo — vista consolidada del grupo (SALELGI sin deuda + Exergy): los pagos entre partes relacionadas se netean",
  69: "FCF SALELGI sin deuda",
  70: "FCF Exergy",
  71: "FCF grupo",
  72: "TIR del grupo",
  73: "VAN del grupo @ tasa de descuento",
  74: "Lectura: si el grupo consolida, el fee, el arriendo y el margen de O&M son transferencias internas; lo que queda es el ahorro de energía menos el costo real (CAPEX + costo propio de O&M + terreno) y los impuestos de cada entidad. El comparativo «quién compra el terreno» está en 10 §G (calculado en Motor_Sens para ambas alternativas).",
};
/** Columna E («Definición») de 09_Exergy, verbatim. */
const DEF: Record<number, string> = {
  7: "Neto de impuestos; incluye compra y residual del terreno si Exergy es la propietaria.",
  8: "Alta por el fee inicial; el VAN es la métrica relevante.",
  10: "Fee − costo interno.",
  11: "Compra + arriendo − predial + residual (0 si compra SALELGI).",
  12: "Fee − costo propio.",
  14: "Cuánto del ahorro del cliente se queda en servicios Exergy.",
};

const short = (s: string): string => {
  const cut = s.search(/ \(|:| — /);
  return cut > 0 ? s.slice(0, cut) : s;
};
const n = (v: number | null | undefined): number => (typeof v === "number" ? v : 0);

interface XRow {
  t: number; anio: number;
  feeG: number; costoG: number; compra: number; arriendo: number; predial: number; feeOM: number; costoOM: number; rep: number;
  ux: number; ix: number; resid: number; fx: number; cum: number; df: number;
  fcfU: number; gx: number;
}

/** Filas 39–52 y 69–71 de 09_Exergy para un caso. */
function exergyRows(i: Inputs, d: Derived, p: CaseParams, res: CaseResult): XRow[] {
  const s = res.scalars, b = res.blocks;
  const H = i.Horizonte, r = i.Tasa_Descuento, fase = i.Fase_m1, RA = i.Reemplazo_Anio;
  const Sub = s[SCALAR_LABELS.Sub], Krep = s[SCALAR_LABELS.Krep];
  const cod = parseISODate(i.Fecha_COD);
  const out: XRow[] = [];
  T_AXIS.forEach((t, k) => {
    const prev = out[k - 1];
    // 09!39 =IF(t=-1, Fee_Gerencia_USD*Fase_m1, IF(t=0, Fee_Gerencia_USD*(1-Fase_m1), 0)) · Fee_Gerencia_USD = Fee_Gerencia_Pct × Subtotal_EPC
    const fG = t === -1 ? fase : t === 0 ? 1 - fase : 0;
    const ol = opexLines(i, d, p, t, false);   // líneas de 06 sin el factor OPEX del caso (como el bloque Ux)
    const fx = n(b.Fx[k]);
    out.push({
      t, anio: edate(cod, 12 * (t - 1)).y,
      feeG: i.Fee_Gerencia_Pct * Sub * fG,
      costoG: -i.Costo_Gerencia_Pct * Sub * fG,                       // 09!40
      compra: t === -1 ? n(b.Tx[k]) : 0,                              // 09!41 (= bloque Tx en t = −1: −Terreno si Exergy compra)
      arriendo: ol.arriendo,                                           // 09!42 = '06_OPEX'!20
      predial: -ol.predial_exergy,                                     // 09!43 = −'06_OPEX'!28
      feeOM: ol.fee,                                                   // 09!44 = '06_OPEX'!18
      costoOM: -ol.om_exergy,                                          // 09!45 = −'06_OPEX'!27
      rep: p.rep === 2 && t === RA ? -Krep : 0,                        // 09!46
      ux: n(b.Ux[k]), ix: n(b.Ix[k]),                                  // 09!47 · 09!48
      resid: t === H ? n(b.Tx[k]) : 0,                                 // 09!49 (= bloque Tx en t = Horizonte)
      fx, cum: (prev ? prev.cum : 0) + fx,                             // 09!50 · 09!51
      df: 1 / Math.pow(1 + r, t),                                      // 09!52 =1/(1+Tasa_Descuento)^t (también t = −1 y 0)
      fcfU: n(b.FCF_u[k]), gx: n(b.Gx[k]),                             // 09!69 · 09!71
    });
  });
  return out;
}

export function Exergy({ caseId }: Props) {
  const m = useModel();
  const ci = m.idx(caseId);
  const c = m.cases[ci];
  const i = m.inputs, d = m.derived, p = c.params, b = c.result.blocks;
  const H = i.Horizonte, r = i.Tasa_Descuento;
  const rows = useMemo(() => exergyRows(i, d, p, c.result), [i, d, p, c.result]);
  const exergyCompra = p.terr === 0, exergyRep = p.rep === 2;

  // ---- indicadores (filas 7–14, 72–73) ---------------------------------------------------------------------------------------------------
  const vanX = m.num(ci, "VAN_X"), nominalX = m.num(ci, "Nominal_X"), tirG = m.out(ci, "TIR_G"), a1 = m.num(ci, "Ahorro1");
  const tirX = useMemo(() => irr(b.Fx.map(n)), [b.Fx]);                                          // 09!D8 =IFERROR(IRR(fila 50),"n/a") (= TIR_Exergy)
  const sp = (f: (x: XRow) => number) => rows.reduce((a, x) => a + f(x) * x.df, 0);           // SUMPRODUCT(·, fila 52)
  const vanGerencia = sp((x) => x.feeG + x.costoG);                                              // 09!D10
  const vanTerreno = sp((x) => x.compra + x.arriendo + x.predial + x.resid);                     // 09!D11
  const vanOM = sp((x) => x.feeOM + x.costoOM);                                                  // 09!D12
  const rendArriendo = i.Precio_Terreno_ha > 0 ? i.Renta_Terreno_ha / i.Precio_Terreno_ha : null; // 09!D13
  const cargaOf = (k: number): number => {                                                       // 09!D14 =IF(Ahorro_Anio1>0, ('06_OPEX'!F18+'06_OPEX'!F20)/Ahorro_Anio1, 0) (= Carga_Exergy)
    const ah = m.num(k, "Ahorro1");
    if (ah === null || ah <= 0) return 0;
    const l = opexLines(i, d, m.cases[k].params, 1);
    return (l.fee + l.arriendo) / ah;
  };
  const carga = cargaOf(ci);
  const vanGrupoOf = (k: number) => vanMotor(r, m.cases[k].result.blocks.Gx.map(n));            // 09!D73 = Gx₋₁(1+r) + Gx₀ + NPV(r, Gx₁…₂₅)
  const vanGrupo = vanGrupoOf(ci);
  const annEsc = rows.reduce((a, x) => a + (x.t >= 1 && x.t <= H ? Math.pow(1 + i.Escalacion_OPEX, x.t - 1) * x.df : 0), 0);   // 09!D55 (Ann_Esc)

  const others = CASES.filter((x) => x.id !== caseId);
  const strip = (f: (k: number) => string): StripValue[] => others.map((x) => ({ caseId: x.id, text: f(m.idx(x.id)) }));
  const tirText = (v: number | null | "n/a" | "no cruza") => (typeof v === "number" ? fmtPct(v, 2) : v === null ? "n/a" : v);

  interface IndRow { row: number; unidad: string; valor: ReactNode; def: ReactNode; trace: string }
  const dash = <span className="text-ink-3">—</span>;
  const ind: IndRow[] = [
    { row: 10, unidad: "USD", valor: fmtUSD(vanGerencia), def: DEF[10], trace: "09_Exergy!D10 = Σ (filas 39 + 40) × fila 52" },
    { row: 11, unidad: "USD", valor: fmtUSD(vanTerreno), def: DEF[11], trace: "09_Exergy!D11 = Σ (filas 41 + 42 + 43 + 49) × fila 52" },
    { row: 12, unidad: "USD", valor: fmtUSD(vanOM), def: DEF[12], trace: "09_Exergy!D12 = Σ (filas 44 + 45) × fila 52" },
    { row: 13, unidad: "%", valor: rendArriendo === null ? "n/a" : fmtPct(rendArriendo, 1), def: dash, trace: "09_Exergy!D13 = Renta_Terreno_ha / Precio_Terreno_ha" },
    { row: 55, unidad: "", valor: fmtNum(annEsc, 4), def: dash, trace: "Ann_Esc · 09_Exergy!D55" },
  ];
  const indCols: Column<IndRow>[] = [
    { key: "ind", label: "Indicador", render: (x) => L[x.row] },
    { key: "u", label: "Unidad", muted: true, nowrap: true, render: (x) => x.unidad },
    { key: "v", label: "Valor", align: "right", nowrap: true, render: (x) => x.valor },
    { key: "d", label: "Definición", render: (x) => <span className="text-ink-2">{x.def}</span> },
    { key: "tr", label: "Celda", render: (x) => <Trace cell={x.trace} /> },
  ];

  // ---- serie anual ----------------------------------------------------------------------------------------------------------------------
  const usd = (v: number): ReactNode => (Math.abs(v) < 0.5 ? <span className="text-ink-3">0</span> : fmtNum(v, 0));
  const strong = (v: number) => <span className="font-medium text-ink">{usd(v)}</span>;
  const col = (key: keyof XRow, row: number, render?: (x: XRow) => ReactNode): Column<XRow> => ({
    key, label: short(L[row]), title: `${L[row]} · 09_Exergy!fila ${row}`, align: "right", render: render ?? ((x) => usd(x[key] as number)),
  });
  const cols: Column<XRow>[] = [
    { key: "t", label: L[35], title: "09_Exergy!fila 35", align: "right", mono: true, nowrap: true, render: (x) => (x.t === 0 ? "0 · COD" : fmtNum(x.t, 0)) },
    { key: "anio", label: "Año calendario", title: `${L[36]} · 09_Exergy!fila 36`, align: "right", muted: true, render: (x) => String(x.anio) },
    col("feeG", 39), col("costoG", 40),
    ...(exergyCompra ? [col("compra", 41), col("arriendo", 42), col("predial", 43)] : []),
    col("feeOM", 44), col("costoOM", 45),
    ...(exergyRep ? [col("rep", 46)] : []),
    col("ux", 47, (x) => strong(x.ux)), col("ix", 48),
    ...(exergyCompra ? [col("resid", 49)] : []),
    col("fx", 50, (x) => strong(x.fx)), col("cum", 51),
    col("df", 52, (x) => <span className="text-ink-3">{fmtNum(x.df, 4)}</span>),
  ];
  const stacks: StackDef[] = [
    { id: "ger", label: `Gerencia: ${DEF[10].replace(/\.$/, "").toLowerCase()}`, values: rows.map((x) => x.feeG + x.costoG), color: "var(--cat-1)" },
    { id: "om", label: `O&M: ${DEF[12].replace(/\.$/, "").toLowerCase()}`, values: rows.map((x) => x.feeOM + x.costoOM), color: "var(--cat-2)" },
    ...(exergyCompra ? [{ id: "terr", label: `Terreno: ${short(DEF[11]).toLowerCase()}`, values: rows.map((x) => x.compra + x.arriendo + x.predial + x.resid), color: "var(--cat-3)" }] : []),
    { id: "ix", label: short(L[48]), values: rows.map((x) => x.ix), color: "var(--c-conservador)" },
    ...(exergyRep ? [{ id: "rep", label: short(L[46]), values: rows.map((x) => x.rep), color: "var(--c-favorable)" }] : []),
  ];
  const xTick = (t: number) => t === -1 || t % 5 === 0;

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8" data-internal-view={EXERGY_VIEW_MARKER}>
      <ViewHeader title="Negocio Exergy" sheet="09_Exergy">
        <Chip title="Vista de la edición interna (src/internal)">edición interna</Chip>
        <Chip title="Caso seleccionado (Motor)">caso {c.name}</Chip>
        <Chip title="Fee_Gerencia_Pct · Costo_Gerencia_Pct (sobre Subtotal_EPC)">gerencia: fee {fmtPct(i.Fee_Gerencia_Pct, 1)} · costo interno {fmtPct(i.Costo_Gerencia_Pct, 1)}</Chip>
        <Chip title="Fee_OM_kWp · Costo_OM_Exergy_kWp">O&M: fee {fmtNum(i.Fee_OM_kWp, 2)} · costo propio {fmtNum(i.Costo_OM_Exergy_kWp, 2)} $/kWp-año</Chip>
        <Chip title="Terreno lo compra SALELGI (1/0) del caso · Renta_Terreno_ha · Predial_Terreno">
          terreno: {exergyCompra ? <>Exergy compra · arriendo {fmtUSD(i.Renta_Terreno_ha)}/ha-año · predial {fmtUSD(i.Predial_Terreno)}/año</> : "SALELGI compra (sin línea terreno)"}
        </Chip>
        <Chip title="Reemplazo inversores (0 No · 1 SALELGI · 2 Exergy) del caso">reemplazo de inversores: {p.rep === 2 ? "Exergy" : p.rep === 1 ? "SALELGI" : "No"}</Chip>
        <Chip title="Tasa_Efectiva_Exergy">Tasa_Efectiva_Exergy {fmtPct(i.Tasa_Efectiva_Exergy, 2)}</Chip>
      </ViewHeader>

      {/* ---- indicadores ------------------------------------------------------------------------------------------------------------- */}
      <Section title={L[5]} guide={`caso ${c.name} · cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo`}>
        <div className="grid grid-cols-2 gap-x-8 gap-y-5 lg:grid-cols-4">
          <KpiTile label={L[7]} excelName="VAN_Exergy" value={fmtUSDCompact(vanX, 2)} state={vanX === null ? "neutral" : vanX >= 0 ? "ok" : "risk"} compare={DEF[7]} strip={strip((k) => fmtUSDCompact(m.num(k, "VAN_X"), 2))} />
          <KpiTile label={L[8]} excelName="TIR_Exergy" value={tirText(tirX)} compare={DEF[8]} strip={strip((k) => tirText(irr(m.cases[k].result.blocks.Fx.map(n))))} />
          <KpiTile label={L[9]} excelName="Nominal_Exergy" value={fmtUSDCompact(nominalX, 2)} compare={<>Σ de la fila 50, t = −1…{fmtNum(T_AXIS[T_AXIS.length - 1], 0)}, sin descontar</>} strip={strip((k) => fmtUSDCompact(m.num(k, "Nominal_X"), 2))} />
          <KpiTile label={L[14]} excelName="Carga_Exergy" value={fmtPct(carga, 1)} compare={<>{DEF[14]} Ahorro año 1 {fmtUSD(a1)}.</>} strip={strip((k) => fmtPct(cargaOf(k), 1))} />
        </div>
        <DataTable columns={indCols} rows={ind} rowKey={(x) => String(x.row)} sectionBefore={(x) => (x.row === 55 ? L[54] : null)} />
        <Note>{L[15]}</Note>
      </Section>

      {/* ---- flujo de caja de Exergy --------------------------------------------------------------------------------------------------- */}
      <Section
        title={L[38]}
        guide="barras = componentes del flujo por línea de negocio (filas 39–49 agrupadas como en las definiciones de la hoja); línea = flujo de caja de Exergy (fila 50) · pase el cursor por un año"
        aside={<Trace name="Ux · Ix · Tx · Fx" cell="09_Exergy!D39:AD52" />}
      >
        <StackedBars
          x={T_AXIS}
          xTick={xTick}
          stacks={stacks}
          line={{ label: L[50], values: rows.map((x) => x.fx), color: "var(--ink-2)" }}
          yFormat={(v) => fmtUSDCompact(v, 1)}
          height={220}
          ariaLabel="Flujo de caja de Exergy por año y por línea de negocio"
        />
        <DataTable
          size="sm"
          columns={cols}
          rows={rows}
          rowKey={(x) => String(x.t)}
          muted={(x) => x.t > H}
          caption={`Filas 39–52 de la hoja para el caso ${c.name}, un año por fila (USD). La cabecera abreviada lleva la etiqueta completa en el tooltip; la utilidad operativa y el flujo son los bloques Ux y Fx del Motor y la suma de las columnas coincide con ellos en todos los años.`}
          footer={
            <>
              {exergyCompra ? null : <>Las líneas del terreno (filas 41, 42, 43 y 49) se omiten: en este caso el terreno lo compra SALELGI y son 0. </>}
              {exergyRep ? null : <>«{short(L[46])}» se omite: en este caso el reemplazo no lo paga Exergy. </>}
              El fee de O&M y el arriendo se toman sin el factor OPEX del caso, como en el bloque Ux del Motor (filas 18 y 20 de 06_OPEX).
            </>
          }
        />
      </Section>

      {/* ---- grupo ---------------------------------------------------------------------------------------------------------------------- */}
      <Section title={L[68].split(": ")[0]} guide={L[68].split(": ").slice(1).join(": ")} aside={<Trace name="TIR_Grupo · Gx" cell="09_Exergy!D69:AD73" />}>
        <div className="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="grid grid-cols-2 gap-x-8 gap-y-5">
            <KpiTile label={L[72]} excelName="TIR_Grupo" value={tirText(tirG)} compare={<>TIR del proyecto sin deuda (TIR_Proyecto): {tirText(m.out(ci, "TIR"))}</>} strip={strip((k) => tirText(m.out(k, "TIR_G")))} />
            <KpiTile label={L[73]} excelName="09_Exergy!D73" value={fmtUSDCompact(vanGrupo, 2)} state={vanGrupo >= 0 ? "ok" : "risk"} compare={<>VAN proyecto {fmtUSDCompact(m.num(ci, "VAN"), 2)} + VAN Exergy {fmtUSDCompact(vanX, 2)}</>} strip={strip((k) => fmtUSDCompact(vanGrupoOf(k), 2))} />
          </div>
          <Series
            x={T_AXIS}
            xTick={xTick}
            series={[
              { id: "fx", label: L[70], values: rows.map((x) => x.fx), color: "var(--cat-2)", bars: true },
              { id: "fcf", label: L[69], values: rows.map((x) => x.fcfU), color: "var(--cat-1)" },
              { id: "gx", label: L[71], values: rows.map((x) => x.gx), color: "var(--cat-3)" },
            ]}
            yFormat={(v) => fmtUSDCompact(v, 1)}
            height={220}
            ariaLabel="Flujo del grupo frente al flujo de SALELGI sin deuda y al de Exergy"
          />
        </div>
        <Note>{L[74]}</Note>
      </Section>
    </div>
  );
}
