import { useMemo } from "react";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { computeAll, OUTPUT_LABELS, SCALAR_LABELS, type ComputedCase, type OutputKey, type ScalarKey } from "@/engine";
import { fmtNum, fmtPct, fmtUSD, fmtX, fmtYears } from "@/lib/format";
import { CASES, type CaseId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { CASE_INDEX } from "@/model/cases";
import { applyScenario, describePatch, type Scenario } from "@/model/scenarios";
import { BASELINE_EXTRAS, BASELINE_INPUTS, useModel } from "@/model/store";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  scenarios: Scenario[];
  caseId: CaseId;
}

type Row = { label: string; excel: string; kind: "pct" | "usd" | "x" | "years" | "num0" | "num1"; out?: OutputKey; scalar?: ScalarKey };

const ROWS: Row[] = [
  { label: "TIR del proyecto (sin deuda)", excel: "TIR_Proyecto", kind: "pct", out: "TIR" },
  { label: "VAN del proyecto @ tasa exigida", excel: "VAN_Proyecto", kind: "usd", out: "VAN" },
  { label: "Payback simple (años desde COD)", excel: "Payback_Simple", kind: "years", out: "PB" },
  { label: "LCOE ($/MWh)", excel: "LCOE", kind: "num1", out: "LCOE" },
  { label: "TIR del accionista (con deuda)", excel: "TIR_Equity", kind: "pct", out: "TIR_eq" },
  { label: "VAN del accionista", excel: "VAN_Equity", kind: "usd", out: "VAN_eq" },
  { label: "DSCR mínimo", excel: "DSCR_Min", kind: "x", out: "DSCR_min" },
  { label: "Ahorro año 1", excel: "Ahorro_Anio1", kind: "usd", out: "Ahorro1" },
  { label: "Energía año 1 (MWh)", excel: "E1", kind: "num0", out: "E1" },
  { label: "CAPEX industrial sin IVA", excel: "CAPEX_Total", kind: "usd", scalar: "K" },
  { label: "OPEX año 1", excel: "OPEX_Anio1", kind: "usd", scalar: "OPEX1" },
  { label: "Deuda total en el COD", excel: "Deuda_Total", kind: "usd", scalar: "Dt" },
];

function fmt(v: unknown, kind: Row["kind"]): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return v === "n/a" || v === "no cruza" ? String(v) : "—";
  switch (kind) {
    case "pct": return fmtPct(v, 2);
    case "usd": return fmtUSD(v);
    case "x": return fmtX(v, 2);
    case "years": return fmtYears(v, 1);
    case "num0": return fmtNum(v, 0);
    case "num1": return fmtNum(v, 1);
  }
}

/**
 * Comparación lado a lado: entradas actuales (columna «Actual») frente a hasta tres escenarios, para el caso seleccionado.
 * Cada escenario se recalcula con el motor aplicando su parche sobre el libro; debajo, las entradas que lo definen.
 */
export function CompareDialog({ open, onOpenChange, scenarios, caseId }: Props) {
  const m = useModel();
  const ci = CASE_INDEX[caseId];
  const meta = CASES.find((c) => c.id === caseId)!;
  const cols = useMemo(() => {
    const out: { id: string; nombre: string; cases: ComputedCase[]; diffs: string[] }[] = [
      { id: "actual", nombre: m.scenario ? `Actual (${m.scenario.nombre})` : m.dirty ? "Actual (edición libre)" : "Actual (libro)", cases: m.cases, diffs: [] },
    ];
    for (const s of scenarios.slice(0, 3)) {
      const applied = applyScenario(BASELINE_INPUTS, BASELINE_EXTRAS, s);
      out.push({ id: s.id, nombre: s.nombre, cases: computeAll(applied.inputs).cases, diffs: describePatch(s.patch ?? {}, s.extras ?? {}) });
    }
    return out;
  }, [scenarios, m.cases, m.scenario, m.dirty]);

  const value = (cases: ComputedCase[], r: Row): unknown => (r.out ? cases[ci].result.outputs[OUTPUT_LABELS[r.out]] : r.scalar ? cases[ci].result.scalars[SCALAR_LABELS[r.scalar]] : null);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] w-[min(96vw,1040px)] max-w-none overflow-auto bg-surface text-ink">
        <DialogHeader>
          <DialogTitle className="text-[15px] font-semibold text-ink">Comparar escenarios · caso {meta.label}</DialogTitle>
          <DialogDescription className="text-[12px] text-ink-3">
            Cada escenario se recalcula con el motor aplicando sus entradas sobre el libro v{m.book.meta.version.replace(/^v/, "")}; la primera columna son las entradas actuales de la sesión. Las cifras en acento difieren de la columna «Actual».
          </DialogDescription>
        </DialogHeader>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-[12px]" style={{ fontVariantNumeric: "tabular-nums" }}>
            <thead>
              <tr className="border-b border-hairline text-left text-[10.5px] uppercase tracking-[0.06em] text-ink-3">
                <th className="px-2 py-1.5 font-medium">Indicador</th>
                {cols.map((c) => <th key={c.id} className="px-2 py-1.5 text-right font-medium normal-case tracking-normal text-ink-2">{c.nombre}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {ROWS.map((r) => {
                const base = value(cols[0].cases, r);
                return (
                  <tr key={r.excel} className="hover:bg-surface-hover">
                    <td className="px-2 py-1.5">
                      <div className="text-ink">{r.label}</div>
                      <div className="font-mono text-[10px] text-ink-3">{r.excel}</div>
                    </td>
                    {cols.map((c, k) => {
                      const v = value(c.cases, r);
                      const differs = k > 0 && JSON.stringify(v) !== JSON.stringify(base);
                      return <td key={c.id} className={cn("px-2 py-1.5 text-right", differs ? "font-medium text-accent" : "text-ink")}>{fmt(v, r.kind)}</td>;
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {cols.length > 1 && (
          <div className="grid gap-4 border-t border-hairline pt-3 md:grid-cols-3">
            {cols.slice(1).map((c) => (
              <div key={c.id} className="text-[11.5px]">
                <div className="mb-1 font-medium text-ink">{c.nombre}</div>
                {c.diffs.length === 0 ? <div className="text-ink-3">sin diferencias con el libro</div> : (
                  <ul className="flex flex-col gap-0.5 font-mono text-[10.5px] text-ink-2">
                    {c.diffs.map((d) => <li key={d}>{d}</li>)}
                  </ul>
                )}
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
