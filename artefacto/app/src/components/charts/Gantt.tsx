import { useState } from "react";

import { useMeasure } from "@/components/charts/util";
import { cn } from "@/lib/utils";

export interface GanttRow {
  id: string;
  label: string;
  /** mes de inicio (1 = primer mes del cronograma) */
  start: number;
  /** mes de fin (inclusive) */
  end: number;
  critical: boolean;
  /** texto secundario del tooltip */
  detail?: string;
}

export interface GanttMarker {
  /** posición en meses (frontera: 0 = inicio del mes 1; k = fin del mes k) */
  month: number;
  label: string;
  kind?: "cod" | "info" | "warn";
}

interface Props {
  rows: GanttRow[];
  /** número de meses del eje */
  months: number;
  /** etiqueta de cada mes (1-based), p. ej. «oct-26» */
  monthLabel: (m: number) => string;
  markers?: GanttMarker[];
  selected?: string | null;
  onSelect?: (id: string | null) => void;
  /** ventana resaltada (p. ej. vigencia de la factibilidad): meses [a, b] */
  window?: { from: number; to: number; label: string };
  className?: string;
}

const ROW_H = 24, LABEL_W = 232, HEAD_H = 22;

/**
 * Gantt de trámites: una fila por hito, barras en acento (ruta crítica) o gris (no crítica), rejilla mensual recesiva,
 * marcadores verticales (COD implícito) y ventana resaltada; hover con el detalle. Clic para seleccionar.
 */
export function Gantt({ rows, months, monthLabel, markers = [], selected, onSelect, window: win, className }: Props) {
  const [box, width] = useMeasure<HTMLDivElement>();
  const [hover, setHover] = useState<string | null>(null);
  const w = Math.max(560, width);
  const plotW = w - LABEL_W - 12;
  const mw = plotW / months;
  const x = (m: number) => LABEL_W + m * mw; // frontera de mes: m = 0…months
  const H = HEAD_H + rows.length * ROW_H + 8;
  const every = mw < 26 ? 3 : mw < 40 ? 2 : 1;

  return (
    <div ref={box} className={cn("relative w-full", className)} onMouseLeave={() => setHover(null)}>
      <svg width={w} height={H} role="img" aria-label="Cronograma de trámites">
        {/* ventana resaltada */}
        {win && (
          <g>
            <rect x={x(win.from - 1)} y={HEAD_H} width={x(win.to) - x(win.from - 1)} height={rows.length * ROW_H} fill="var(--warn-fill)" opacity={0.08} />
            <text x={x(win.from - 1) + 4} y={HEAD_H - 8} fontSize={10} fill="var(--warn-text)" fontFamily="var(--font-sans)">{win.label}</text>
          </g>
        )}
        {/* rejilla mensual y cabecera */}
        {Array.from({ length: months }, (_, k) => (
          <g key={k}>
            <line x1={x(k)} x2={x(k)} y1={HEAD_H} y2={H - 8} stroke="var(--hairline)" strokeWidth={1} />
            {k % every === 0 && (
              <text x={x(k) + mw / 2} y={HEAD_H - 8} textAnchor="middle" fontSize={10} fill="var(--ink-3)" fontFamily="var(--font-sans)">{monthLabel(k + 1)}</text>
            )}
          </g>
        ))}
        <line x1={x(months)} x2={x(months)} y1={HEAD_H} y2={H - 8} stroke="var(--hairline)" strokeWidth={1} />
        {/* filas */}
        {rows.map((r, i) => {
          const y0 = HEAD_H + i * ROW_H;
          const active = hover === r.id || selected === r.id;
          const dim = (hover !== null || (selected !== null && selected !== undefined)) && !active;
          return (
            <g key={r.id} onMouseEnter={() => setHover(r.id)} onClick={() => onSelect?.(selected === r.id ? null : r.id)} className={onSelect ? "cursor-pointer" : undefined}>
              <rect x={0} y={y0} width={w} height={ROW_H} fill={active ? "var(--surface-hover)" : "transparent"} />
              <text x={8} y={y0 + ROW_H / 2 + 3.5} fontSize={11.5} fill={active ? "var(--ink)" : "var(--ink-2)"} fontFamily="var(--font-sans)" fontWeight={r.critical ? 500 : 400}>
                <tspan fill="var(--ink-3)" fontFamily="var(--font-mono)" fontSize={10.5}>{r.id}</tspan>
                <tspan dx={8}>{r.label.length > 34 ? `${r.label.slice(0, 33)}…` : r.label}</tspan>
              </text>
              <rect
                x={x(r.start - 1) + 1}
                y={y0 + 6}
                width={Math.max(2, x(r.end) - x(r.start - 1) - 2)}
                height={ROW_H - 12}
                rx={2}
                fill={r.critical ? "var(--accent)" : "var(--ink-3)"}
                opacity={dim ? 0.3 : r.critical ? 0.9 : 0.55}
              />
            </g>
          );
        })}
        {/* marcadores */}
        {markers.map((mk) => {
          const nearRight = x(mk.month) > w - 90;   // etiqueta hacia la izquierda si el marcador cae junto al borde derecho
          return (
            <g key={mk.label}>
              <line x1={x(mk.month)} x2={x(mk.month)} y1={HEAD_H - 2} y2={H - 8} stroke={mk.kind === "warn" ? "var(--warn-fill)" : "var(--ink)"} strokeWidth={1} strokeDasharray="3 3" />
              <text x={x(mk.month) + (nearRight ? -4 : 4)} y={H - 2} textAnchor={nearRight ? "end" : "start"} fontSize={10} fill={mk.kind === "warn" ? "var(--warn-text)" : "var(--ink-2)"} fontFamily="var(--font-sans)">{mk.label}</text>
            </g>
          );
        })}
      </svg>
      {hover !== null && (() => {
        const r = rows.find((q) => q.id === hover)!;
        const i = rows.indexOf(r);
        return (
          <div className="pointer-events-none absolute rounded-1 border border-hairline bg-surface px-2 py-1 text-[11.5px] shadow-1" style={{ left: Math.min(w - 300, x(r.start - 1) + 8), top: HEAD_H + i * ROW_H - 4, maxWidth: 290 }}>
            <div className="font-medium text-ink"><span className="font-mono text-[10.5px] text-ink-3">{r.id}</span> {r.label}</div>
            <div className="text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}>meses {r.start}–{r.end} ({r.end - r.start + 1} m) · {monthLabel(r.start)} → {monthLabel(r.end)}{r.critical ? " · ruta crítica" : ""}</div>
            {r.detail && <div className="text-ink-3">{r.detail}</div>}
          </div>
        );
      })()}
    </div>
  );
}
