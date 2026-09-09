import { Download } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { outcomeText, safeName, saveText, stamp, tableToRows, toCsv } from "@/lib/export";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  label: ReactNode;
  align?: "left" | "right" | "center";
  /** ancho CSS opcional (p. ej. "28%" o "120px") */
  width?: string;
  render: (row: T, index: number) => ReactNode;
  /** celda en monoespaciada (nombres Excel, códigos) */
  mono?: boolean;
  /** celda en tinta terciaria */
  muted?: boolean;
  /** tooltip de la cabecera */
  title?: string;
  /** no envolver el texto */
  nowrap?: boolean;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  /** filas destacadas (totales): negrita y borde superior */
  emphasize?: (row: T, index: number) => boolean;
  /** filas atenuadas (memo, informativas) */
  muted?: (row: T, index: number) => boolean;
  /** clase adicional por fila */
  rowClass?: (row: T, index: number) => string | undefined;
  onRowClick?: (row: T, index: number) => void;
  selected?: (row: T, index: number) => boolean;
  /** encabezado pegajoso dentro de un contenedor con altura */
  sticky?: boolean;
  /** tamaño de letra: 12 px (defecto) u 11,5 px para tablas anchas */
  size?: "md" | "sm";
  caption?: ReactNode;
  footer?: ReactNode;
  className?: string;
  /** fila de sección (agrupador) insertada antes de la fila i */
  sectionBefore?: (row: T, index: number) => ReactNode | null;
  /** nombre base del CSV exportado (defecto: «tabla»); `false` oculta el botón de exportar */
  exportName?: string | false;
}

/**
 * Tabla densa del sistema: cabecera en versalitas terciarias, cifras tabulares alineadas a la derecha, hairlines entre filas,
 * hover sutil, contenedor con desplazamiento horizontal propio (la página nunca desplaza de lado).
 */
export function DataTable<T>({ columns, rows, rowKey, emphasize, muted, rowClass, onRowClick, selected, sticky, size = "md", caption, footer, className, sectionBefore, exportName }: Props<T>) {
  const fs = size === "sm" ? "text-[11.5px]" : "text-[12px]";
  const ref = useRef<HTMLTableElement>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const exportCsv = async () => {
    if (!ref.current) return;
    const csv = toCsv(tableToRows(ref.current));
    const o = await saveText(`${safeName(exportName || "tabla")}-${stamp()}.csv`, csv);
    setMsg(outcomeText(o, "CSV"));
    window.setTimeout(() => setMsg(null), 4000);
  };
  return (
    <div className={cn("group/table scroll-x-shadows relative w-full overflow-x-auto", className)}>
      {exportName !== false && (
        <div className="absolute right-0 top-0 z-[1] flex items-center gap-1 print:hidden">
          {msg && <span className="text-[10.5px] text-ink-3">{msg}</span>}
          <button
            type="button"
            onClick={exportCsv}
            title="Exportar esta tabla tal como se ve (CSV)"
            aria-label="Exportar tabla en CSV"
            className="inline-flex h-5 items-center gap-1 rounded-[3px] px-1 font-mono text-[10px] text-ink-3 opacity-0 transition-opacity hover:text-ink focus-visible:opacity-100 group-hover/table:opacity-100"
          >
            <Download className="size-3" aria-hidden /> CSV
          </button>
        </div>
      )}
      <table ref={ref} className={cn("w-full border-collapse", fs)} style={{ fontVariantNumeric: "tabular-nums" }}>
        {caption && <caption className="pb-2 text-left text-[12px] text-ink-3">{caption}</caption>}
        <thead className={cn(sticky && "sticky top-0 z-10 bg-surface")}>
          <tr className="border-b border-hairline">
            {columns.map((c) => (
              <th
                key={c.key}
                title={c.title}
                style={{ width: c.width }}
                className={cn(
                  "px-2 py-1.5 text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3",
                  c.align === "right" ? "text-right" : c.align === "center" ? "text-center" : "text-left",
                  c.nowrap && "whitespace-nowrap",
                )}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r, i) => {
            const emph = emphasize?.(r, i) ?? false;
            const mut = muted?.(r, i) ?? false;
            const sel = selected?.(r, i) ?? false;
            const section = sectionBefore?.(r, i);
            return (
              <FragmentRow key={rowKey(r, i)} section={section} colSpan={columns.length}>
                <tr
                  data-rowkey={rowKey(r, i)}
                  onClick={onRowClick ? () => onRowClick(r, i) : undefined}
                  className={cn(
                    onRowClick && "cursor-pointer",
                    "hover:bg-surface-hover",
                    emph && "border-t border-ink-3/40 font-semibold text-ink",
                    mut && "text-ink-3",
                    sel && "bg-accent-soft",
                    rowClass?.(r, i),
                  )}
                >
                  {columns.map((c) => (
                    <td
                      key={c.key}
                      className={cn(
                        "px-2 py-1.5 align-top",
                        c.align === "right" ? "whitespace-nowrap text-right" : c.align === "center" ? "text-center" : "text-left",
                        c.mono && "font-mono text-[11px]",
                        c.muted && !emph && "text-ink-3",
                        c.nowrap && "whitespace-nowrap",
                      )}
                    >
                      {c.render(r, i)}
                    </td>
                  ))}
                </tr>
              </FragmentRow>
            );
          })}
        </tbody>
        {footer && (
          <tfoot>
            <tr>
              <td colSpan={columns.length} className="px-2 pt-2 text-[11px] text-ink-3">{footer}</td>
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  );
}

function FragmentRow({ section, colSpan, children }: { section: ReactNode | null | undefined; colSpan: number; children: ReactNode }) {
  return (
    <>
      {section && (
        <tr className="bg-surface-2">
          <td colSpan={colSpan} className="px-2 py-1 text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">{section}</td>
        </tr>
      )}
      {children}
    </>
  );
}
