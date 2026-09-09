import { useMemo, type ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { KpiTile, type StripValue } from "@/components/KpiTile";
import { Trace } from "@/components/Live";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { Series } from "@/components/charts/Series";
import { StackedBars, type StackDef } from "@/components/charts/StackedBars";
import { edate, parseISODate, SCALAR_LABELS, T_AXIS, tIndex } from "@/engine";
import { fmtNum, fmtPct, fmtUSD, fmtUSDCompact } from "@/lib/format";
import { CASES, type CaseId, type ViewId } from "@/lib/views";
import { opexLines, opexSeries, type OpexLines } from "@/model/opex";
import { useModel } from "@/model/store";

/**
 * OPEX de SALELGI (hoja 06_OPEX): las cinco líneas del costo anual del dueño del SGDA para el caso seleccionado, con
 * `opexLines`/`opexSeries` (Σ líneas ≡ bloque OPEX del Motor, verificado). El factor OPEX del caso (fO) multiplica las líneas
 * como en el Motor; el comprador del terreno decide arriendo o predial. El memo de costos propios de Exergy (filas 26–28)
 * se muestra sólo como texto: sus cifras pertenecen al flujo de Exergy (hoja 09).
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

type LineKey = "fee" | "seguros" | "arriendo" | "predial" | "tributos";
/** Orden fijo de la hoja (filas 7–11 · 18–22). */
const ORDER: readonly LineKey[] = ["fee", "seguros", "arriendo", "predial", "tributos"];
const hdr = (s: string): ReactNode => s.split("\n").map((l, k) => (k === 0 ? l : <span key={k}><br />{l}</span>));

export function Opex({ caseId }: Props) {
  const m = useModel();
  const ci = m.idx(caseId);
  const c = m.cases[ci];
  const meta = CASES.find((x) => x.id === caseId)!;
  const i = m.inputs, d = m.derived, p = c.params;
  const H = Math.min(i.Horizonte, T_AXIS[T_AXIS.length - 1]);
  const serie = useMemo(() => opexSeries(i, d, p), [i, d, p]);
  const y1 = serie[tIndex(1)] ?? opexLines(i, d, p, 1);
  const opex1Base = c.result.scalars[SCALAR_LABELS.OPEX1];                        // «OPEX año 1 SALELGI» sin el factor del caso
  const ultimo = serie[tIndex(H)] ?? y1;
  const cod = parseISODate(i.Fecha_COD);
  const book = m.book.opex;
  const L: Record<string, string> = m.book.sheets["06_OPEX"]?.labels ?? {};
  /** Etiquetas de la hoja: filas 7–11 (composición) y 18–22 (serie), en el orden fijo. */
  const labelComp = (k: LineKey) => String(book.lines[ORDER.indexOf(k)]?.v.B ?? k);
  const labelSerie = (k: LineKey) => book.serie_labels[ORDER.indexOf(k)] ?? labelComp(k);
  const notaH7 = book.lines[0]?.v.H;
  const others = CASES.filter((x) => x.id !== caseId);
  const strip = (f: (k: number) => number, fmt: (v: number) => string): StripValue[] => others.map((x) => ({ caseId: x.id, text: fmt(f(m.idx(x.id))) }));
  /** Total del año 1 de otro caso con la misma aritmética de la hoja (≡ bloque OPEX[t = 1] del Motor). */
  const total1Of = (k: number) => opexLines(i, d, m.cases[k].params, 1).total;
  const xAnio = (t: number) => (t === 0 ? "COD" : fmtNum(t, 0));

  // ---- colores: las tres líneas mayores del año 1 en --cat-1..3 (orden fijo de la hoja), el resto en grises ---------------------------
  const ranked = useMemo(() => [...ORDER].sort((a, b) => y1[b] - y1[a]), [y1]);
  const colorOf = (k: LineKey): string => {
    const r = ranked.indexOf(k);
    if (r < 3) return `var(--cat-${r + 1})`;
    return r === 3 ? "var(--c-base)" : "var(--c-favorable)";
  };

  // ---- composición del año 1 (filas 7–12) ----------------------------------------------------------------------------------------------
  interface CompRow { key: LineKey | "total"; label: string; usd: number; kwp: number; pct: number; trace: string }
  const compRows: CompRow[] = [
    ...ORDER.map((k, n) => ({ key: k, label: labelComp(k), usd: y1[k], kwp: p.P > 0 ? y1[k] / p.P : 0, pct: y1.total > 0 ? y1[k] / y1.total : 0, trace: `06!D${7 + n}` })),
    { key: "total", label: String(book.lines[5]?.v.B ?? "Total OPEX año 1"), usd: y1.total, kwp: p.P > 0 ? y1.total / p.P : 0, pct: y1.total > 0 ? 1 : 0, trace: "OPEX_Anio1 · 06!D12" },
  ];
  const compCols: Column<CompRow>[] = [
    {
      key: "linea", label: L["6"] ?? "Línea",
      render: (r) => (
        <span className="inline-flex items-center gap-2">
          {r.key !== "total" && <span className="inline-block h-2.5 w-2.5 shrink-0 rounded-[2px]" style={{ background: colorOf(r.key) }} aria-hidden />}
          <span>{r.label}</span>
        </span>
      ),
    },
    { key: "usd", label: "USD/año", align: "right", render: (r) => fmtUSD(r.usd) },
    { key: "kwp", label: "$/kWp", align: "right", render: (r) => fmtNum(r.kwp, 2) },
    { key: "pct", label: "% del total", align: "right", render: (r) => fmtPct(r.pct, 1) },
    { key: "trace", label: "", align: "right", render: (r) => <Trace cell={r.trace} /> },
  ];

  // ---- serie anual (filas 15–24) -----------------------------------------------------------------------------------------------------------
  const stacks: StackDef[] = ORDER.map((k) => ({ id: k, label: labelSerie(k), values: serie.map((r) => (r.t < 1 || r.t > H ? null : r[k])), color: colorOf(k) }));
  const unitario = serie.map((r) => (r.t < 1 || r.t > H ? null : r.total > 0 && p.P > 0 ? r.total / p.P : 0));   // fila 24 =IF(total>0, total/Potencia_DC, 0)
  const anualRows = serie.filter((r) => r.t >= 1 && r.t <= H);
  const anualCols: Column<OpexLines>[] = [
    { key: "t", label: L["15"] ?? "Año (t)", align: "right", mono: true, render: (r) => String(r.t) },
    { key: "anio", label: hdr("Año\ncalendario"), align: "right", muted: true, render: (r) => String(edate(cod, 12 * (r.t - 1)).y) },
    ...ORDER.map((k): Column<OpexLines> => ({ key: k, label: hdr(labelSerie(k).replace(" → ", "\n→ ").replace(" (", "\n(")), align: "right", render: (r) => fmtNum(r[k], 0) })),
    { key: "total", label: hdr((book.serie_labels[5] ?? "Total OPEX SALELGI").replace(" SALELGI", "\nSALELGI")), align: "right", render: (r) => <span className="font-semibold text-ink">{fmtNum(r.total, 0)}</span> },
    { key: "unit", label: hdr(`${book.serie_labels[6] ?? "OPEX unitario"}\n[$/kWp]`), align: "right", muted: true, render: (r) => fmtNum(r.total > 0 && p.P > 0 ? r.total / p.P : 0, 2) },
  ];

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="OPEX de SALELGI" sheet="06_OPEX">
        <Chip>caso {meta.label} · factor OPEX × {fmtNum(p.fO, 2)}</Chip>
        <Chip title="Escalacion_OPEX">escalación {fmtPct(i.Escalacion_OPEX, 1)}/año</Chip>
        <Chip title="Comprador_Terreno">terreno: {i.Comprador_Terreno} → {p.terr === 1 ? "predial" : "arriendo"}</Chip>
        <Chip title="Horizonte">horizonte {i.Horizonte} años</Chip>
      </ViewHeader>

      {/* ---------------------------------------------------------------- cifras clave */}
      <Section title={`OPEX del año 1 · caso ${meta.label}`} guide="cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo · USD nominales del año 1 de operación">
        <div className="grid grid-cols-2 gap-x-6 gap-y-5 lg:grid-cols-4">
          <KpiTile
            label={String(book.lines[5]?.v.B ?? "Total OPEX año 1")}
            excelName="OPEX_Anio1 · 06!D12 · Motor OPEX[t=1]"
            value={fmtUSD(y1.total)}
            compare={<>{fmtNum(p.P > 0 ? y1.total / p.P : 0, 2)} $/kWp · base sin factor {fmtUSD(opex1Base)} × {fmtNum(p.fO, 2)}</>}
            strip={strip(total1Of, (v) => fmtUSD(v))}
          />
          <KpiTile
            label={`${book.serie_labels[6] ?? "OPEX unitario"} (año 1)`}
            excelName="06!E12"
            value={`${fmtNum(p.P > 0 ? y1.total / p.P : 0, 2)} $/kWp`}
            compare={<>{fmtNum(p.P, 0)} kWp · en t = {H}: {fmtNum(p.P > 0 ? ultimo.total / p.P : 0, 2)} $/kWp</>}
            strip={strip((k) => (m.cases[k].params.P > 0 ? total1Of(k) / m.cases[k].params.P : 0), (v) => `${fmtNum(v, 2)} $/kWp`)}
          />
          <KpiTile
            label={labelComp("fee")}
            excelName="Fee_OM_kWp · 06!D7"
            value={fmtUSD(y1.fee)}
            compare={<>{fmtPct(y1.total > 0 ? y1.fee / y1.total : 0, 1)} del total · {fmtNum(i.Fee_OM_kWp, 1)} $/kWp-año × {fmtNum(p.P, 0)} kWp × {fmtNum(p.fO, 2)}</>}
          />
          <KpiTile
            label={p.terr === 1 ? labelComp("predial") : labelComp("arriendo")}
            excelName={p.terr === 1 ? "Predial_Terreno · 06!D10" : "Renta_Terreno_ha · 06!D9"}
            value={fmtUSD(p.terr === 1 ? y1.predial : y1.arriendo)}
            compare={p.terr === 1 ? <>SALELGI es dueña del terreno: paga predial y gastos; el arriendo es 0</> : <>Exergy es dueña del terreno: SALELGI paga arriendo {fmtNum(i.Renta_Terreno_ha, 0)} $/ha-año × {fmtNum(c.result.scalars[SCALAR_LABELS.ha], 1)} ha</>}
          />
        </div>
      </Section>

      {/* ---------------------------------------------------------------- composición (5–12) */}
      <Section title={L["5"] ?? "Composición del año 1"} guide={`año 1 del caso ${meta.label}; el detalle anual está debajo`} aside={<Trace name="OPEX_Anio1" cell="06_OPEX!D7:F12" />}>
        <DataTable columns={compCols} rows={compRows} rowKey={(r) => r.key} emphasize={(r) => r.key === "total"} />
        {typeof notaH7 === "string" && <Note>{notaH7}</Note>}
      </Section>

      {/* ---------------------------------------------------------------- serie anual (14–24) */}
      <Section
        title={L["14"] ?? "Serie anual"}
        guide={`t = 1…${H}; cada línea escala ${fmtPct(i.Escalacion_OPEX, 1)}/año desde el año 1 · pase el cursor por un año`}
        aside={<Trace name="Motor bloque OPEX" cell="06_OPEX!D18:AD24" />}
      >
        <StackedBars x={T_AXIS} stacks={stacks} xFormat={xAnio} yFormat={(v) => fmtUSDCompact(v)} height={230} ariaLabel="OPEX anual de SALELGI por línea" />
        <h3 className="text-[12px] font-medium text-ink-2">{book.serie_labels[6] ?? "OPEX unitario"} · $/kWp</h3>
        <Series
          x={T_AXIS}
          xFormat={xAnio}
          series={[{ id: "unit", label: `${book.serie_labels[6] ?? "OPEX unitario"} [$/kWp]`, values: unitario, color: "var(--ink-2)" }]}
          yFormat={(v) => fmtNum(v, 1)}
          yLabel="$/kWp"
          height={140}
          legend={false}
          ariaLabel="OPEX unitario por año"
        />
        <DataTable columns={anualCols} rows={anualRows} rowKey={(r) => String(r.t)} size="sm" />
      </Section>

      {/* ---------------------------------------------------------------- memo Exergy (26–28), sólo texto */}
      <Section title={book.memo_exergy[0] ?? "Memo · costos propios de Exergy (→ 09)"} guide="filas 27–28 de la hoja; sólo las etiquetas">
        <ul className="flex flex-col gap-1 text-[12.5px] text-ink-2">
          {book.memo_exergy.slice(1).map((t) => (
            <li key={t} className="flex items-baseline gap-2"><span aria-hidden className="text-ink-3">·</span>{t}</li>
          ))}
        </ul>
        <Note className="text-ink-3">Las cifras del memo no se muestran en esta vista: no forman parte del OPEX de SALELGI y pertenecen al flujo de Exergy (hoja 09).</Note>
      </Section>
    </div>
  );
}
