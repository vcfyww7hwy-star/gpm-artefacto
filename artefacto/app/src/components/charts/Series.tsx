import { useMemo, useState } from "react";

import { linear, ticks, useMeasure } from "@/components/charts/util";
import { cn } from "@/lib/utils";

export interface SeriesDef {
  id: string;
  label: string;
  values: readonly (number | null)[];
  /** color CSS (var(--accent), var(--c-base), var(--cat-1)…) */
  color: string;
  /** stroke-dasharray (var(--dash-base) o "6 3") */
  dash?: string;
  /** relleno de área tenue bajo la línea */
  area?: boolean;
  /** dibujar como barras finas en lugar de línea */
  bars?: boolean;
  width?: number;
}

interface Props {
  /** eje x: categorías (años t) */
  x: readonly number[];
  series: SeriesDef[];
  /** etiqueta de un valor del eje y (y del tooltip) */
  yFormat: (v: number) => string;
  /** etiqueta de un valor del eje x (defecto: t y «COD» en 0) */
  xFormat?: (x: number, i: number) => string;
  /** cada cuántas categorías se rotula el eje x (defecto: t=−1 y múltiplos de 5) */
  xTick?: (x: number, i: number) => boolean;
  /** línea de referencia horizontal (umbral) */
  refLine?: { value: number; label: string };
  /** forzar el cero en el dominio (defecto true) */
  includeZero?: boolean;
  height?: number;
  /** rótulo del eje y (unidad) */
  yLabel?: string;
  /** leyenda (defecto: si hay ≥ 2 series) */
  legend?: boolean;
  className?: string;
  ariaLabel?: string;
}

const PAD = { l: 60, r: 14, t: 14, b: 26 };

/**
 * Gráfico de series sobre el eje de años: líneas (o barras finas) con un solo eje y, rejilla recesiva, leyenda si hay ≥ 2
 * series, capa de hover con línea vertical y tooltip que lista todas las series del año. Colores fijos por serie (identidad).
 */
export function Series({ x, series, yFormat, xFormat, xTick, refLine, includeZero = true, height = 200, yLabel, legend, className, ariaLabel }: Props) {
  const [box, width] = useMeasure<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const w = Math.max(360, width);
  const H = height;
  const n = x.length;
  const vals = useMemo(() => {
    const out: number[] = [];
    for (const s of series) for (const v of s.values) if (typeof v === "number" && Number.isFinite(v)) out.push(v);
    if (refLine) out.push(refLine.value);
    return out;
  }, [series, refLine]);
  let vmin = Math.min(...vals), vmax = Math.max(...vals);
  if (includeZero) { vmin = Math.min(0, vmin); vmax = Math.max(0, vmax); }
  if (vmin === vmax) { vmin -= 1; vmax += 1; }
  const pad = (vmax - vmin) * 0.04;
  const y = linear([vmin - (includeZero && vmin === 0 ? 0 : pad), vmax + pad], [H - PAD.b, PAD.t]);
  const xs = linear([-0.5, n - 0.5], [PAD.l, w - PAD.r]);
  const step = xs(1) - xs(0);
  const yt = ticks(vmin, vmax, 4);
  const showX = xTick ?? ((t: number) => t === x[0] || t % 5 === 0);
  const fmtX = xFormat ?? ((t: number) => (t === 0 ? "COD" : String(t)));
  const showLegend = legend ?? series.length >= 2;
  const nBars = series.filter((s) => s.bars).length;

  return (
    <div ref={box} className={cn("relative w-full", className)} onMouseLeave={() => setHover(null)}>
      {showLegend && (
        <ul className="mb-1 flex flex-wrap gap-x-4 gap-y-1 text-[11.5px] text-ink-2">
          {series.map((s) => (
            <li key={s.id} className="inline-flex items-center gap-1.5">
              <svg width="16" height="8" aria-hidden>
                {s.bars ? <rect x="2" y="1" width="12" height="6" fill={s.color} opacity="0.7" /> : <line x1="0" y1="4" x2="16" y2="4" stroke={s.color} strokeWidth="2" strokeDasharray={s.dash ?? "0"} />}
              </svg>
              {s.label}
            </li>
          ))}
        </ul>
      )}
      <svg width={w} height={H} role="img" aria-label={ariaLabel ?? "Serie anual"}>
        {yt.map((v) => (
          <g key={v}>
            <line x1={PAD.l} x2={w - PAD.r} y1={y(v)} y2={y(v)} stroke={v === 0 ? "var(--ink-3)" : "var(--hairline)"} strokeWidth={1} />
            <text x={PAD.l - 6} y={y(v) + 3.5} textAnchor="end" fontSize={10.5} fill="var(--ink-3)" fontFamily="var(--font-sans)" style={{ fontVariantNumeric: "tabular-nums" }}>
              {yFormat(v)}
            </text>
          </g>
        ))}
        {yLabel && (
          <text x={PAD.l - 6} y={PAD.t - 4} textAnchor="end" fontSize={10} fill="var(--ink-3)" fontFamily="var(--font-sans)">{yLabel}</text>
        )}
        {refLine && (
          <g>
            <line x1={PAD.l} x2={w - PAD.r} y1={y(refLine.value)} y2={y(refLine.value)} stroke="var(--ink-2)" strokeWidth={1} strokeDasharray="4 3" />
            <text x={w - PAD.r} y={y(refLine.value) - 4} textAnchor="end" fontSize={10.5} fill="var(--ink-2)" fontFamily="var(--font-sans)">{refLine.label}</text>
          </g>
        )}
        {/* barras (si las hay), agrupadas por categoría */}
        {series.filter((s) => s.bars).map((s, bi) => {
          const bw = Math.max(2, (step * 0.7) / Math.max(1, nBars));
          return s.values.map((v, i) => {
            if (typeof v !== "number" || !Number.isFinite(v)) return null;
            const top = y(Math.max(0, v)), bot = y(Math.min(0, v));
            return <rect key={`${s.id}-${i}`} x={xs(i) - (step * 0.7) / 2 + bi * bw} y={top} width={bw - 1} height={Math.max(1, bot - top)} rx={1.5} fill={s.color} opacity={hover === null || hover === i ? 0.7 : 0.35} />;
          });
        })}
        {/* áreas y líneas */}
        {series.filter((s) => !s.bars).map((s) => {
          const pts: string[] = [];
          s.values.forEach((v, i) => { if (typeof v === "number" && Number.isFinite(v)) pts.push(`${xs(i).toFixed(1)},${y(v).toFixed(1)}`); });
          const first = s.values.findIndex((v) => typeof v === "number" && Number.isFinite(v));
          let last = -1; s.values.forEach((v, i) => { if (typeof v === "number" && Number.isFinite(v)) last = i; });
          return (
            <g key={s.id}>
              {s.area && first >= 0 && (
                <polygon points={`${xs(first).toFixed(1)},${y(0).toFixed(1)} ${pts.join(" ")} ${xs(last).toFixed(1)},${y(0).toFixed(1)}`} fill={s.color} opacity={0.08} />
              )}
              <polyline points={pts.join(" ")} fill="none" stroke={s.color} strokeWidth={s.width ?? 2} strokeDasharray={s.dash ?? "0"} strokeLinejoin="round" strokeLinecap="round" />
              {hover !== null && typeof s.values[hover] === "number" && (
                <circle cx={xs(hover)} cy={y(s.values[hover] as number)} r={3.5} fill={s.color} stroke="var(--surface)" strokeWidth={2} />
              )}
            </g>
          );
        })}
        {/* eje x */}
        {x.map((t, i) => showX(t, i) && (
          <text key={t} x={xs(i)} y={H - 8} textAnchor="middle" fontSize={10.5} fill="var(--ink-3)" fontFamily="var(--font-sans)">{fmtX(t, i)}</text>
        ))}
        {/* capa de hover */}
        {x.map((_, i) => (
          <rect key={`h${i}`} x={xs(i) - step / 2} y={PAD.t} width={step} height={H - PAD.t - PAD.b} fill="transparent" onMouseEnter={() => setHover(i)} />
        ))}
        {hover !== null && <line x1={xs(hover)} x2={xs(hover)} y1={PAD.t} y2={H - PAD.b} stroke="var(--ink-2)" strokeWidth={1} strokeDasharray="3 3" pointerEvents="none" />}
      </svg>
      {hover !== null && (
        <div className="pointer-events-none absolute top-1 rounded-1 border border-hairline bg-surface px-2 py-1 text-[11.5px] shadow-1" style={{ left: Math.min(w - 210, Math.max(0, xs(hover) + 8)) }}>
          <div className="font-medium text-ink">{fmtX(x[hover], hover)}{x[hover] === 0 ? "" : x[hover] > 0 ? ` · t = ${x[hover]}` : ""}</div>
          {series.map((s) => (
            <div key={s.id} className="flex items-center justify-between gap-3 text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}>
              <span className="inline-flex items-center gap-1.5"><span className="inline-block h-2 w-2 rounded-[2px]" style={{ background: s.color }} />{s.label}</span>
              <span className="text-ink">{typeof s.values[hover] === "number" ? yFormat(s.values[hover] as number) : "—"}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
