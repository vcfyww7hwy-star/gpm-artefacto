import { useMemo, useState } from "react";

import { linear, ticks, useMeasure } from "@/components/charts/util";
import { cn } from "@/lib/utils";

export interface StackDef {
  id: string;
  label: string;
  values: readonly (number | null)[];
  /** color CSS; para ≤ 3 series usar var(--cat-1..3); para más, grises ordinales */
  color: string;
  /** trama para el caso sin color (impresión / daltonismo) */
  pattern?: boolean;
}

interface Props {
  x: readonly number[];
  stacks: StackDef[];
  yFormat: (v: number) => string;
  xFormat?: (x: number, i: number) => string;
  xTick?: (x: number, i: number) => boolean;
  /** línea superpuesta (p. ej. total o referencia) */
  line?: { label: string; values: readonly (number | null)[]; color: string; dash?: string };
  height?: number;
  className?: string;
  ariaLabel?: string;
}

const PAD = { l: 60, r: 14, t: 14, b: 26 };

/**
 * Barras apiladas por año (composición): segmentos con separador de 2 px del color de la superficie, leyenda siempre
 * (≥ 2 series), hover por año con el detalle de cada componente y el total. Un solo eje y.
 */
export function StackedBars({ x, stacks, yFormat, xFormat, xTick, line, height = 200, className, ariaLabel }: Props) {
  const [box, width] = useMeasure<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const w = Math.max(360, width);
  const H = height;
  const n = x.length;
  const totals = useMemo(() => x.map((_, i) => { let pos = 0, neg = 0; for (const s of stacks) { const v = s.values[i]; if (typeof v === "number") { if (v >= 0) pos += v; else neg += v; } } return { pos, neg }; }), [x, stacks]);
  const lineVals = (line?.values ?? []).filter((v): v is number => typeof v === "number");
  const vmax = Math.max(0, ...totals.map((t) => t.pos), ...lineVals);
  const vmin = Math.min(0, ...totals.map((t) => t.neg), ...lineVals);
  const y = linear([vmin, vmax === vmin ? vmin + 1 : vmax * 1.04], [H - PAD.b, PAD.t]);
  const xs = linear([-0.5, n - 0.5], [PAD.l, w - PAD.r]);
  const step = xs(1) - xs(0);
  const bw = Math.max(3, step * 0.66);
  const yt = ticks(vmin, vmax, 4);
  const showX = xTick ?? ((t: number) => t === x[0] || t % 5 === 0);
  const fmtX = xFormat ?? ((t: number) => (t === 0 ? "COD" : String(t)));

  return (
    <div ref={box} className={cn("relative w-full", className)} onMouseLeave={() => setHover(null)}>
      <ul className="mb-1 flex flex-wrap gap-x-4 gap-y-1 text-[11.5px] text-ink-2">
        {stacks.map((s) => (
          <li key={s.id} className="inline-flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 rounded-[2px]" style={{ background: s.color }} />{s.label}</li>
        ))}
        {line && <li className="inline-flex items-center gap-1.5"><svg width="16" height="8" aria-hidden><line x1="0" y1="4" x2="16" y2="4" stroke={line.color} strokeWidth="2" strokeDasharray={line.dash ?? "0"} /></svg>{line.label}</li>}
      </ul>
      <svg width={w} height={H} role="img" aria-label={ariaLabel ?? "Composición anual"}>
        {yt.map((v) => (
          <g key={v}>
            <line x1={PAD.l} x2={w - PAD.r} y1={y(v)} y2={y(v)} stroke={v === 0 ? "var(--ink-3)" : "var(--hairline)"} strokeWidth={1} />
            <text x={PAD.l - 6} y={y(v) + 3.5} textAnchor="end" fontSize={10.5} fill="var(--ink-3)" fontFamily="var(--font-sans)" style={{ fontVariantNumeric: "tabular-nums" }}>{yFormat(v)}</text>
          </g>
        ))}
        {x.map((_, i) => {
          let accPos = 0, accNeg = 0;
          return stacks.map((s) => {
            const v = s.values[i];
            if (typeof v !== "number" || v === 0) return null;
            let y0: number, y1: number;
            if (v > 0) { y0 = y(accPos + v); y1 = y(accPos); accPos += v; } else { y0 = y(accNeg); y1 = y(accNeg + v); accNeg += v; }
            return <rect key={`${s.id}-${i}`} x={xs(i) - bw / 2} y={Math.min(y0, y1)} width={bw} height={Math.max(1, Math.abs(y1 - y0))} fill={s.color} stroke="var(--surface)" strokeWidth={1} opacity={hover === null || hover === i ? 0.85 : 0.4} />;
          });
        })}
        {line && (
          <polyline points={line.values.map((v, i) => (typeof v === "number" ? `${xs(i).toFixed(1)},${y(v).toFixed(1)}` : null)).filter(Boolean).join(" ")} fill="none" stroke={line.color} strokeWidth={2} strokeDasharray={line.dash ?? "0"} strokeLinejoin="round" />
        )}
        {x.map((t, i) => showX(t, i) && <text key={t} x={xs(i)} y={H - 8} textAnchor="middle" fontSize={10.5} fill="var(--ink-3)" fontFamily="var(--font-sans)">{fmtX(t, i)}</text>)}
        {x.map((_, i) => <rect key={`h${i}`} x={xs(i) - step / 2} y={PAD.t} width={step} height={H - PAD.t - PAD.b} fill="transparent" onMouseEnter={() => setHover(i)} />)}
      </svg>
      {hover !== null && (
        <div className="pointer-events-none absolute top-1 rounded-1 border border-hairline bg-surface px-2 py-1 text-[11.5px] shadow-1" style={{ left: Math.min(w - 230, Math.max(0, xs(hover) + 8)) }}>
          <div className="font-medium text-ink">{fmtX(x[hover], hover)}{x[hover] > 0 ? ` · t = ${x[hover]}` : ""}</div>
          {stacks.map((s) => (
            <div key={s.id} className="flex items-center justify-between gap-3 text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}>
              <span className="inline-flex items-center gap-1.5"><span className="inline-block h-2 w-2 rounded-[2px]" style={{ background: s.color }} />{s.label}</span>
              <span className="text-ink">{typeof s.values[hover] === "number" ? yFormat(s.values[hover] as number) : "—"}</span>
            </div>
          ))}
          <div className="mt-0.5 flex items-center justify-between gap-3 border-t border-hairline pt-0.5 font-medium text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
            <span>total</span><span>{yFormat(totals[hover].pos + totals[hover].neg)}</span>
          </div>
          {line && <div className="flex items-center justify-between gap-3 text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}><span>{line.label}</span><span className="text-ink">{typeof line.values[hover] === "number" ? yFormat(line.values[hover] as number) : "—"}</span></div>}
        </div>
      )}
    </div>
  );
}
