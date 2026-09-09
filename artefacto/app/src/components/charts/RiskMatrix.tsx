import { cn } from "@/lib/utils";

export interface RiskPoint {
  id: string;
  label: string;
  prob: 1 | 2 | 3;
  impacto: 1 | 2 | 3;
}

interface Props {
  points: RiskPoint[];
  /** umbrales del libro (01 §I): score ≥ alto → riesgo · ≥ medio → atención */
  umbralAlto: number;
  umbralMedio: number;
  selected?: string | null;
  onSelect?: (id: string | null) => void;
  className?: string;
}

const CELL = 92;

/**
 * Matriz probabilidad × impacto (3 × 3): el color de cada celda es el nivel (score = p × i frente a los umbrales del libro),
 * mezclado con la superficie; los riesgos se listan dentro de su celda como fichas con su número. Clic en una ficha selecciona.
 */
export function RiskMatrix({ points, umbralAlto, umbralMedio, selected, onSelect, className }: Props) {
  const level = (s: number) => (s >= umbralAlto ? "risk" : s >= umbralMedio ? "warn" : "ok");
  const fill: Record<string, string> = {
    risk: "color-mix(in oklab, var(--risk) 22%, var(--surface))",
    warn: "color-mix(in oklab, var(--warn-fill) 20%, var(--surface))",
    ok: "color-mix(in oklab, var(--ok) 12%, var(--surface))",
  };
  return (
    <div className={cn("inline-grid gap-1", className)} style={{ gridTemplateColumns: `28px repeat(3, ${CELL}px)` }}>
      {[3, 2, 1].map((p) => (
        <RowFrag key={p}>
          <div className="flex items-center justify-end pr-1 text-[10.5px] text-ink-3" title="probabilidad">{p}</div>
          {[1, 2, 3].map((im) => {
            const s = p * im;
            const lv = level(s);
            const here = points.filter((q) => q.prob === p && q.impacto === im);
            return (
              <div key={im} className="flex min-h-[64px] flex-col gap-1 rounded-1 p-1.5" style={{ background: fill[lv] }} title={`p ${p} × i ${im} = ${s}`}>
                <div className="flex items-baseline justify-between text-[10px] text-ink-3" style={{ fontVariantNumeric: "tabular-nums" }}>
                  <span>{s}</span>
                  <span>{lv === "risk" ? "■ alto" : lv === "warn" ? "▲ medio" : "● bajo"}</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {here.map((q) => (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => onSelect?.(selected === q.id ? null : q.id)}
                      title={q.label}
                      className={cn("rounded-[3px] border border-hairline bg-surface px-1.5 py-0.5 font-mono text-[10.5px] text-ink-2 hover:text-ink", selected === q.id && "border-accent text-accent")}
                    >
                      {q.id}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </RowFrag>
      ))}
      <div />
      {[1, 2, 3].map((im) => (
        <div key={im} className="pt-0.5 text-center text-[10.5px] text-ink-3" title="impacto">{im}</div>
      ))}
    </div>
  );
}

function RowFrag({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
