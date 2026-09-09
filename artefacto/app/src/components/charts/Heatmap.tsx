import { useState } from "react";

import { cn } from "@/lib/utils";
import { divergingFill } from "@/components/charts/util";

export interface HeatCell {
  value: number | null;
  /** texto de la celda (ya formateado) */
  text: string;
  /** tooltip */
  title?: string;
  /** celda del Custom (borde) */
  active?: boolean;
}

interface Props {
  rowLabels: string[];
  colLabels: string[];
  rowTitle: string;
  colTitle: string;
  cells: HeatCell[][];
  /** umbral central de la escala divergente (p. ej. tasa exigida o 0) */
  center: number;
  /** semiamplitud de la escala (distancia al umbral que satura el color) */
  halfSpan: number;
  /** polo bajo/alto: por defecto --cat-2 (cálido = peor) / --cat-1 (frío = mejor) */
  poleLow?: string;
  poleHigh?: string;
  legend?: { low: string; mid: string; high: string };
  className?: string;
}

/**
 * Mapa de calor 5 × 5 (o n × m) con escala divergente centrada en el umbral que decide (tasa exigida, VAN 0, DSCR objetivo).
 * El color se mezcla con la superficie del tema (color-mix) → funciona en claro y oscuro; el texto siempre en tinta.
 */
export function Heatmap({ rowLabels, colLabels, rowTitle, colTitle, cells, center, halfSpan, poleLow = "var(--cat-2)", poleHigh = "var(--cat-1)", legend, className }: Props) {
  const [hover, setHover] = useState<[number, number] | null>(null);
  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      <table className="w-full border-separate text-[12.5px]" style={{ borderSpacing: 2 }}>
        <thead>
          <tr>
            <th className="pb-1 pr-2 text-left align-bottom text-[10.5px] font-medium uppercase tracking-wide text-ink-3">
              {rowTitle} ↓ · {colTitle} →
            </th>
            {colLabels.map((c) => (
              <th key={c} className="pb-1 text-center text-[11px] font-medium text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cells.map((row, i) => (
            <tr key={i}>
              <th className="pr-2 text-right text-[11px] font-medium text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}>
                {rowLabels[i]}
              </th>
              {row.map((cell, j) => {
                const isHover = hover?.[0] === i && hover?.[1] === j;
                const rowCol = hover !== null && (hover[0] === i || hover[1] === j);
                return (
                  <td
                    key={j}
                    title={cell.title}
                    onMouseEnter={() => setHover([i, j])}
                    onMouseLeave={() => setHover(null)}
                    className={cn(
                      "h-9 min-w-[64px] rounded-[3px] text-center text-ink transition-[outline-color]",
                      cell.active && "outline outline-2 -outline-offset-1 outline-accent",
                      isHover && !cell.active && "outline outline-1 -outline-offset-1 outline-ink-2",
                    )}
                    style={{
                      background: cell.value === null ? "var(--surface-2)" : divergingFill(cell.value, center, halfSpan, poleLow, poleHigh),
                      fontVariantNumeric: "tabular-nums",
                      fontWeight: cell.active || isHover ? 600 : 400,
                      opacity: hover !== null && !rowCol ? 0.72 : 1,
                    }}
                  >
                    {cell.text}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {legend && (
        <div className="mt-1.5 flex items-center gap-2 text-[11px] text-ink-2">
          <span>{legend.low}</span>
          <span
            aria-hidden
            className="inline-block h-2 w-28 rounded-[2px]"
            style={{ background: `linear-gradient(90deg, color-mix(in oklab, ${poleLow} 72%, var(--surface)), var(--surface) 50%, color-mix(in oklab, ${poleHigh} 72%, var(--surface)))` }}
          />
          <span>{legend.high}</span>
          <span className="text-ink-3">· centro: {legend.mid} · borde tinta = Custom</span>
        </div>
      )}
    </div>
  );
}
