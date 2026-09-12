import { useMemo, useState } from "react";

import { fmtPct, fmtPP } from "@/lib/format";
import { cn } from "@/lib/utils";
import { linear, ticks, useMeasure } from "@/components/charts/util";

export interface TornadoRow {
  id: string;
  label: string;
  /** TIR del caso bajo y alto (null = «n/a») */
  lo: number | null;
  hi: number | null;
  note: string;
  /** nombre del caso bajo/alto en el Motor */
  loName: string;
  hiName: string | null;
}

interface Props {
  rows: TornadoRow[];
  /** TIR de referencia (Custom) */
  ref: number;
  selected?: string | null;
  onSelect?: (id: string | null) => void;
  className?: string;
}

const ROW_H = 26;
const LABEL_W_MIN = 176;
/** r4 (F1-13): la columna de rótulos crece con el rótulo más largo (medido con canvas) en vez de recortarlo por la izquierda. */
function measureLabels(labels: string[], font: string): number {
  if (typeof document === "undefined") return LABEL_W_MIN;
  const ctx = document.createElement("canvas").getContext("2d");
  if (!ctx) return LABEL_W_MIN;
  ctx.font = font;
  return Math.max(0, ...labels.map((l) => ctx.measureText(l).width));
}
const PAD_R = 44;

/**
 * Tornado: Δ TIR (pp) de cada palanca frente al Custom, barras ordenadas por amplitud.
 * Polaridad: caso bajo (TIR menor) en el polo cálido (--cat-2), caso alto en el polo frío (--cat-1); el eje 0 es el Custom.
 * Interactivo: hover → tooltip con ambos casos; clic → selecciona la barra (la vista muestra los casos y la nota).
 */
export function Tornado({ rows, ref, selected, onSelect, className }: Props) {
  const [box, width] = useMeasure<HTMLDivElement>();
  const [hover, setHover] = useState<string | null>(null);
  const data = useMemo(() => {
    const d = rows.map((r) => {
      const dlo = r.lo === null ? 0 : (r.lo - ref) * 100;
      const dhi = r.hi === null ? 0 : (r.hi - ref) * 100;
      const left = Math.min(dlo, dhi, 0);
      const right = Math.max(dlo, dhi, 0);
      return { ...r, dlo, dhi, left, right, amp: right - left };
    });
    return d.sort((a, b) => b.amp - a.amp);
  }, [rows, ref]);
  const ext = Math.max(0.5, ...data.map((d) => Math.max(-d.left, d.right)));
  const w = Math.max(320, width);
  const LABEL_W = useMemo(() => {
    const family = typeof document !== "undefined" ? getComputedStyle(document.body).fontFamily || "sans-serif" : "sans-serif";
    const widest = measureLabels(data.map((d) => d.label), `12px ${family}`);
    // 10 px de holgura a la derecha del rótulo; nunca más del 45 % del ancho para que las barras conserven sitio
    return Math.min(Math.max(LABEL_W_MIN, Math.ceil(widest) + 14), Math.floor(w * 0.45));
  }, [data, w]);
  const plotW = w - LABEL_W - PAD_R;
  const x = linear([-ext, ext], [LABEL_W, LABEL_W + plotW]);
  const h = data.length * ROW_H + 28;
  // nº de ticks según el ancho del área de barras (≈ 70 px por rótulo) para que no se solapen con el cajón abierto
  const tks = ticks(-ext, ext, Math.max(2, Math.min(6, Math.floor(plotW / 70))));
  const active = hover ?? selected ?? null;

  return (
    <div ref={box} className={cn("relative w-full", className)}>
      <svg width={w} height={h} role="img" aria-label="Tornado: variación de la TIR del proyecto por palanca">
        {/* rejilla */}
        {tks.map((t) => (
          <g key={t}>
            <line x1={x(t)} x2={x(t)} y1={18} y2={h - 10} stroke={t === 0 ? "var(--ink-2)" : "var(--hairline)"} strokeWidth={t === 0 ? 1 : 1} />
            <text x={x(t)} y={12} textAnchor="middle" fontSize={10.5} fill="var(--ink-3)" fontFamily="var(--font-sans)">
              {t === 0 ? "Custom" : fmtPP(t, Math.abs(t) < 1 ? 1 : 0)}
            </text>
          </g>
        ))}
        {data.map((d, i) => {
          const y = 22 + i * ROW_H;
          const isActive = active === d.id;
          const dim = active !== null && !isActive;
          const barY = y + 6;
          const barH = ROW_H - 12;
          const seg = (from: number, to: number, pole: "lo" | "hi", name: string, val: number | null) => {
            const a = x(Math.min(from, to)), b = x(Math.max(from, to));
            if (b - a < 0.5) return null;
            return (
              <rect
                key={pole}
                x={a}
                y={barY}
                width={Math.max(2, b - a)}
                height={barH}
                rx={2}
                fill={pole === "lo" ? "var(--cat-2)" : "var(--cat-1)"}
                opacity={dim ? 0.35 : 0.92}
              >
                <title>{`${name}: TIR ${val === null ? "n/a" : fmtPct(val, 2)} (${fmtPP(to)})`}</title>
              </rect>
            );
          };
          return (
            <g
              key={d.id}
              onMouseEnter={() => setHover(d.id)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onSelect?.(selected === d.id ? null : d.id)}
              style={{ cursor: onSelect ? "pointer" : "default" }}
            >
              <rect x={0} y={y} width={w} height={ROW_H} fill={isActive ? "var(--surface-hover)" : "transparent"} />
              <text x={LABEL_W - 10} y={y + ROW_H / 2 + 4} textAnchor="end" fontSize={12} fill={dim ? "var(--ink-3)" : "var(--ink)"} fontFamily="var(--font-sans)">
                {d.label}
              </text>
              {/* lado bajo: el caso con menor TIR; lado alto: el mayor. Si una barra es de un solo lado, se pinta por su signo */}
              {d.dlo <= 0 ? seg(d.dlo, 0, "lo", d.loName, d.lo) : seg(0, d.dlo, "hi", d.loName, d.lo)}
              {d.hi !== null && (d.dhi >= 0 ? seg(0, d.dhi, "hi", d.hiName ?? "", d.hi) : seg(d.dhi, 0, "lo", d.hiName ?? "", d.hi))}
              {/* amplitud a la derecha */}
              <text x={w - 4} y={y + ROW_H / 2 + 4} textAnchor="end" fontSize={11} fill="var(--ink-2)" fontFamily="var(--font-sans)" style={{ fontVariantNumeric: "tabular-nums" }}>
                {d.amp.toFixed(2).replace(".", ",")}
              </text>
            </g>
          );
        })}
        <text x={w - 4} y={h - 2} textAnchor="end" fontSize={10} fill="var(--ink-3)" fontFamily="var(--font-sans)">
          amplitud (pp)
        </text>
      </svg>
      {/* leyenda de polaridad */}
      <div className="mt-1 flex items-center gap-4 pl-1 text-[11px] text-ink-2">
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-[2px] bg-cat-2" /> caso que baja la TIR</span>
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-[2px] bg-cat-1" /> caso que la sube</span>
        <span className="text-ink-3">eje 0 = TIR del Custom {fmtPct(ref, 2)}</span>
      </div>
    </div>
  );
}
