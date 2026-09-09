import { useMemo, useState } from "react";

import { fmtUSD, fmtUSDCompact } from "@/lib/format";
import { cn } from "@/lib/utils";
import { linear, ticks, useMeasure } from "@/components/charts/util";

interface Props {
  /** años t = −1…25 */
  t: readonly number[];
  /** flujo del año (barras) */
  fcf: readonly (number | null)[];
  /** acumulado (línea) */
  cum: readonly (number | null)[];
  /** color CSS de la línea del caso (var(--accent) para el Custom) */
  lineColor: string;
  lineDash?: string;
  /** año calendario del t = 0 (COD) para el eje secundario de etiquetas */
  codYear?: number;
  /** payback (años desde COD) para el marcador */
  payback?: number | null;
  className?: string;
}

const H = 190;
const PAD = { l: 56, r: 12, t: 14, b: 26 };

/**
 * Cinta anual: 27 años en una tira — barras = flujo libre del año (negativo en la construcción), línea = acumulado,
 * punto = cruce del acumulado por cero (payback). Un solo eje (USD). Hover por año con tooltip.
 */
export function CintaAnual({ t, fcf, cum, lineColor, lineDash = "0", codYear, payback, className }: Props) {
  const [box, width] = useMeasure<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const w = Math.max(360, width);
  const n = t.length;
  const vals = useMemo(() => [...fcf, ...cum].filter((v): v is number => typeof v === "number" && Number.isFinite(v)), [fcf, cum]);
  const vmin = Math.min(0, ...vals), vmax = Math.max(0, ...vals);
  const y = linear([vmin, vmax], [H - PAD.b, PAD.t]);
  const x = linear([-0.5, n - 0.5], [PAD.l, w - PAD.r]);
  const bw = Math.max(3, (x(1) - x(0)) * 0.62);
  const yt = ticks(vmin, vmax, 4);
  const line = useMemo(() => {
    const pts: string[] = [];
    cum.forEach((v, i) => { if (typeof v === "number" && Number.isFinite(v)) pts.push(`${x(i).toFixed(1)},${y(v).toFixed(1)}`); });
    return pts.join(" ");
  }, [cum, w, vmin, vmax]); // eslint-disable-line react-hooks/exhaustive-deps
  // cruce por cero del acumulado (para el marcador de payback): interpolación en el último cruce
  const pbX = useMemo(() => {
    if (payback === null || payback === undefined || !Number.isFinite(payback)) return null;
    // payback = años desde el COD (t = 0 es el índice 1 del eje)
    const idx = payback + 1;
    return x(idx);
  }, [payback, w]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div ref={box} className={cn("relative w-full", className)} onMouseLeave={() => setHover(null)}>
      <svg width={w} height={H} role="img" aria-label="Cinta anual: flujo libre del año y acumulado">
        {yt.map((v) => (
          <g key={v}>
            <line x1={PAD.l} x2={w - PAD.r} y1={y(v)} y2={y(v)} stroke={v === 0 ? "var(--ink-2)" : "var(--hairline)"} strokeWidth={1} />
            <text x={PAD.l - 6} y={y(v) + 3.5} textAnchor="end" fontSize={10.5} fill="var(--ink-3)" fontFamily="var(--font-sans)" style={{ fontVariantNumeric: "tabular-nums" }}>
              {fmtUSDCompact(v, 1)}
            </text>
          </g>
        ))}
        {fcf.map((v, i) => {
          if (typeof v !== "number" || !Number.isFinite(v)) return null;
          const top = y(Math.max(0, v)), bot = y(Math.min(0, v));
          const isH = hover === i;
          return (
            <rect
              key={i}
              x={x(i) - bw / 2}
              y={top}
              width={bw}
              height={Math.max(1, bot - top)}
              rx={1.5}
              fill={v < 0 ? "var(--ink-3)" : "var(--c-base)"}
              opacity={hover === null || isH ? (v < 0 ? 0.75 : 0.6) : 0.3}
            />
          );
        })}
        <polyline points={line} fill="none" stroke={lineColor} strokeWidth={2} strokeDasharray={lineDash} strokeLinejoin="round" />
        {pbX !== null && (
          <g>
            <line x1={pbX} x2={pbX} y1={PAD.t} y2={H - PAD.b} stroke={lineColor} strokeWidth={1} strokeDasharray="2 3" />
            <circle cx={pbX} cy={y(0)} r={4} fill={lineColor} stroke="var(--surface)" strokeWidth={2} />
            <text x={pbX + 6} y={PAD.t + 9} fontSize={10.5} fill="var(--ink-2)" fontFamily="var(--font-sans)">
              payback {payback!.toFixed(1).replace(".", ",")} a
            </text>
          </g>
        )}
        {/* eje x: t y año calendario */}
        {t.map((tt, i) => (
          (tt === -1 || tt % 5 === 0) && (
            <text key={tt} x={x(i)} y={H - 8} textAnchor="middle" fontSize={10.5} fill="var(--ink-3)" fontFamily="var(--font-sans)">
              {tt === 0 ? "COD" : tt}{codYear && tt > 0 && tt % 5 === 0 ? ` · ${codYear + tt}` : ""}
            </text>
          )
        ))}
        {/* capa de hover: una franja por año */}
        {t.map((_, i) => (
          <rect key={`h${i}`} x={x(i) - (x(1) - x(0)) / 2} y={PAD.t} width={x(1) - x(0)} height={H - PAD.t - PAD.b} fill="transparent" onMouseEnter={() => setHover(i)} />
        ))}
        {hover !== null && (
          <line x1={x(hover)} x2={x(hover)} y1={PAD.t} y2={H - PAD.b} stroke="var(--ink-2)" strokeWidth={1} strokeDasharray="3 3" pointerEvents="none" />
        )}
      </svg>
      {hover !== null && (
        <div
          className="pointer-events-none absolute top-1 rounded-1 border border-hairline bg-surface px-2 py-1 text-[11.5px] shadow-1"
          style={{ left: Math.min(w - 190, Math.max(0, x(hover) + 8)) }}
        >
          <div className="font-medium text-ink">t = {t[hover]}{codYear ? ` · ${codYear + t[hover]}` : ""}</div>
          <div className="text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}>flujo {fmtUSD(fcf[hover] ?? 0)}</div>
          <div className="text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}>acumulado {fmtUSD(cum[hover] ?? 0)}</div>
        </div>
      )}
    </div>
  );
}
