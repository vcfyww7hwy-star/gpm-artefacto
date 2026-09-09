import { useMemo, useState, type ReactNode } from "react";

import { Heatmap, type HeatCell } from "@/components/charts/Heatmap";
import { Tornado, type TornadoRow } from "@/components/charts/Tornado";
import { fmtNum, fmtPct, fmtUSD, fmtUSDCompact, fmtX } from "@/lib/format";
import type { CaseId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { CASE_X, EQ_START, MAT_START, tornadoDefs } from "@/model/cases";
import { useModel } from "@/model/store";

interface Props {
  caseId: CaseId;
}

function Section({ id, title, guide, children }: { id: string; title: string; guide?: string; children: ReactNode }) {
  return (
    <section id={id} className="flex flex-col gap-3">
      <header className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
        <h2 className="text-[13.5px] font-semibold text-ink">{title}</h2>
        {guide && <p className="text-[12px] text-ink-3">{guide}</p>}
      </header>
      {children}
    </section>
  );
}

function Chip({ children }: { children: ReactNode }) {
  return <span className="inline-flex items-center rounded-1 border border-hairline bg-surface px-1.5 py-0.5 font-mono text-[11px] text-ink-2">{children}</span>;
}

const signPct = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${fmtPct(Math.abs(v), Math.abs(v * 100) % 1 ? 1 : 0)}`;

export function Sensibilidad(_: Props) {
  const m = useModel();
  const i = m.inputs;
  const tasa = i.Tasa_Descuento;
  const tirX = m.num(CASE_X, "TIR") ?? 0;
  const [sel, setSel] = useState<string | null>("dedad");

  const TORNADO = useMemo(() => tornadoDefs(m.book), [m.book]);
  const rows: TornadoRow[] = useMemo(
    () => TORNADO.map((t) => ({ id: t.id, label: m.live(m.book.sens.tornado_short[t.k]), lo: m.num(t.lo, "TIR"), hi: t.hi === null ? null : m.num(t.hi, "TIR"), note: m.live(m.book.sens.tornado[t.k].note), loName: m.cases[t.lo].name, hiName: t.hi === null ? null : m.cases[t.hi].name })),
    [m, TORNADO],
  );
  const selDef = TORNADO.find((t) => t.id === sel) ?? null;
  const selRow = rows.find((r) => r.id === sel) ?? null;
  const detailCases = selDef ? [CASE_X, selDef.lo, ...(selDef.hi === null ? [] : [selDef.hi])] : [];

  // §C matrices CAPEX (filas) × tarifa (columnas)
  const matLabelsR = i.Mat_CAPEX.map(signPct), matLabelsC = i.Mat_Tarifa.map(signPct);
  const tirCells: HeatCell[][] = i.Mat_CAPEX.map((_, r) =>
    i.Mat_Tarifa.map((__, c) => {
      const idx = MAT_START + r * 5 + c;
      const v = m.num(idx, "TIR");
      return { value: v, text: v === null ? "n/a" : fmtPct(v, 2), active: i.Mat_CAPEX[r] === 0 && i.Mat_Tarifa[c] === 0, title: `${m.cases[idx].name}: TIR ${v === null ? "n/a" : fmtPct(v, 2)} · VAN ${fmtUSD(m.num(idx, "VAN"))}` };
    }),
  );
  const vanCells: HeatCell[][] = i.Mat_CAPEX.map((_, r) =>
    i.Mat_Tarifa.map((__, c) => {
      const idx = MAT_START + r * 5 + c;
      const v = m.num(idx, "VAN");
      return { value: v, text: fmtUSDCompact(v, 1), active: i.Mat_CAPEX[r] === 0 && i.Mat_Tarifa[c] === 0, title: `${m.cases[idx].name}: VAN ${fmtUSD(v)}` };
    }),
  );
  const vanSpan = Math.max(1, ...vanCells.flat().map((c) => Math.abs(c.value ?? 0)));
  // §D deuda: tasas (filas) × plazos (columnas)
  const tasasL = i.Sens_Tasas.map((t) => fmtPct(t, 2)), plazosL = i.Sens_Plazos.map((p) => `${p} años`);
  const eqCells: HeatCell[][] = i.Sens_Tasas.map((_, r) =>
    i.Sens_Plazos.map((__, c) => {
      const idx = EQ_START + r * 3 + c;
      const v = m.num(idx, "TIR_eq");
      return { value: v, text: v === null ? "n/a" : fmtPct(v, 1), active: i.Sens_Tasas[r] === i.Tasa_Deuda && i.Sens_Plazos[c] === i.Plazo_Deuda, title: `${m.cases[idx].name}: TIR accionista ${v === null ? "n/a" : fmtPct(v, 2)} · DSCR mín ${fmtX(m.num(idx, "DSCR_min"), 2)}` };
    }),
  );
  const dscrCells: HeatCell[][] = i.Sens_Tasas.map((_, r) =>
    i.Sens_Plazos.map((__, c) => {
      const idx = EQ_START + r * 3 + c;
      const v = m.num(idx, "DSCR_min");
      return { value: v, text: v === null ? "n/a" : fmtX(v, 2), active: i.Sens_Tasas[r] === i.Tasa_Deuda && i.Sens_Plazos[c] === i.Plazo_Deuda, title: `${m.cases[idx].name}: DSCR mín ${fmtX(v, 2)}` };
    }),
  );

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-[20px] font-semibold tracking-[-0.01em] text-ink">Sensibilidad</h1>
        <p className="text-[12.5px] text-ink-2">
          Qué mueve el resultado, en vivo desde el motor ({m.cases.length} casos). Todas las palancas parten del Custom; los pasos se editan en Mandos.
        </p>
        <div className="mt-1 flex flex-wrap gap-1.5">
          <Chip>Sens_CAPEX ±{fmtPct(i.Sens_CAPEX, 0)}</Chip>
          <Chip>Sens_Tarifa ±{fmtPct(i.Sens_Tarifa, 0)}</Chip>
          <Chip>Sens_Peaje {fmtNum(i.Sens_Peaje * 100, 1)} ¢/kWh</Chip>
          <Chip>Sens_OPEX +{fmtPct(i.Sens_OPEX_Up, 0)} / −{fmtPct(i.Sens_OPEX_Dn, 0)}</Chip>
          <Chip>Sens_Disponibilidad −{fmtNum(i.Sens_Disponibilidad * 100, 0)} pp</Chip>
          <Chip>Sens_EscCAPEX +{fmtNum(i.Sens_EscCAPEX * 100, 0)} pp</Chip>
          <Chip>Sens_Peaje_kW {fmtNum(i.Sens_Peaje_kW, 1)} $/kW-mes</Chip>
        </div>
      </header>

      <Section id="B" title="B · Tornado — TIR del proyecto sin deuda" guide="una palanca a la vez sobre el Custom; ordenado por amplitud · clic en una barra para ver los casos y la nota">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(280px,2fr)]">
          <Tornado rows={rows} ref={tirX} selected={sel} onSelect={setSel} />
          <aside className="flex flex-col gap-3 border-l border-hairline pl-5 text-[12.5px]">
            {selDef ? (
              <>
                <div>
                  <div className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">Palanca</div>
                  <div className="text-[14px] font-semibold text-ink">{m.live(m.book.sens.tornado[selDef.k].label)}</div>
                </div>
                <table className="w-full text-[12px]" style={{ fontVariantNumeric: "tabular-nums" }}>
                  <thead>
                    <tr className="text-left text-[10.5px] uppercase tracking-wide text-ink-3">
                      <th className="pb-1 font-medium">Caso</th>
                      <th className="pb-1 text-right font-medium">TIR</th>
                      <th className="pb-1 text-right font-medium">VAN</th>
                      <th className="pb-1 text-right font-medium">Accionista</th>
                      <th className="pb-1 text-right font-medium">DSCR</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hairline">
                    {detailCases.map((idx) => {
                      const tir = m.num(idx, "TIR");
                      return (
                        <tr key={idx} className={cn(idx === CASE_X && "text-accent")}>
                          <td className="py-1 pr-2">{m.cases[idx].name}</td>
                          <td className={cn("py-1 text-right", tir !== null && tir < tasa && idx !== CASE_X && "text-risk")}>{tir === null ? "n/a" : fmtPct(tir, 2)}</td>
                          <td className="py-1 text-right">{fmtUSDCompact(m.num(idx, "VAN"), 1)}</td>
                          <td className="py-1 text-right">{m.num(idx, "TIR_eq") === null ? "n/a" : fmtPct(m.num(idx, "TIR_eq"), 1)}</td>
                          <td className="py-1 text-right">{fmtX(m.num(idx, "DSCR_min"), 2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <p className="font-serif text-[13px] leading-[1.45] text-ink-2">{selRow?.note}</p>
                <p className="text-[11px] text-ink-3">Casos del Motor: {detailCases.map((k) => m.cases[k].name).join(" · ")}</p>
              </>
            ) : (
              <p className="text-ink-3">Seleccione una barra para ver sus casos y la nota.</p>
            )}
          </aside>
        </div>
      </Section>

      <Section id="C" title="C · Frontera CAPEX × tarifa" guide="TIR y VAN del proyecto sin deuda; el color se centra en el umbral que decide (tasa exigida · VAN 0); la celda con borde es el Custom">
        <div className="grid gap-8 lg:grid-cols-2">
          <div>
            <h3 className="mb-2 text-[12px] font-medium text-ink-2">TIR del proyecto</h3>
            <Heatmap rowLabels={matLabelsR} colLabels={matLabelsC} rowTitle="Δ CAPEX" colTitle="Δ tarifa" cells={tirCells} center={tasa} halfSpan={0.04} legend={{ low: "bajo la tasa exigida", mid: fmtPct(tasa, 0), high: "sobre la tasa exigida" }} />
          </div>
          <div>
            <h3 className="mb-2 text-[12px] font-medium text-ink-2">VAN @ {fmtPct(tasa, 0)}</h3>
            <Heatmap rowLabels={matLabelsR} colLabels={matLabelsC} rowTitle="Δ CAPEX" colTitle="Δ tarifa" cells={vanCells} center={0} halfSpan={vanSpan} legend={{ low: "VAN negativo", mid: "0", high: "VAN positivo" }} />
          </div>
        </div>
      </Section>

      <Section id="D" title="D · Deuda — tasa × plazo" guide={`TIR del accionista y DSCR mínimo con ${fmtPct(i.Pct_Apalancamiento, 0)} de deuda; el color del DSCR se centra en el objetivo ${fmtX(i.DSCR_Objetivo, 2)}`}>
        <div className="grid gap-8 lg:grid-cols-2">
          <div>
            <h3 className="mb-2 text-[12px] font-medium text-ink-2">TIR del accionista</h3>
            <Heatmap rowLabels={tasasL} colLabels={plazosL} rowTitle="tasa" colTitle="plazo" cells={eqCells} center={tasa} halfSpan={0.08} legend={{ low: "bajo la tasa exigida", mid: fmtPct(tasa, 0), high: "sobre la tasa exigida" }} />
          </div>
          <div>
            <h3 className="mb-2 text-[12px] font-medium text-ink-2">DSCR mínimo</h3>
            <Heatmap rowLabels={tasasL} colLabels={plazosL} rowTitle="tasa" colTitle="plazo" cells={dscrCells} center={i.DSCR_Objetivo} halfSpan={0.5} legend={{ low: "bajo el objetivo", mid: fmtX(i.DSCR_Objetivo, 2), high: "sobre el objetivo" }} />
          </div>
        </div>
      </Section>
    </div>
  );
}
