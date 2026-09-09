import type { ReactNode } from "react";

import { Status, stripGlyph } from "@/components/Status";
import { statusOf } from "@/model/book";
import { namesIn, type Live as LiveText } from "@/model/formula";
import { useModel } from "@/model/store";

/**
 * Texto vivo del libro: evalúa una fórmula/plantilla con los valores actuales. Si depende de un valor «congelado» (que sólo
 * existe en el Excel: controles, conteos), lo señala con un punto y el tooltip «valor del libro (fecha de corte)».
 */
export function Live({ text, className, frozenHint = true }: { text: LiveText | undefined; className?: string; frozenHint?: boolean }) {
  const m = useModel();
  const s = m.live(text);
  const usesFrozen = frozenHint && [...namesIn(text)].some((n) => m.resolver.frozenUsed.has(n));
  return (
    <span className={className}>
      {s}
      {usesFrozen && <Frozen />}
    </span>
  );
}

/** Marca de «valor del libro»: el dato no lo calcula el motor; es el del Excel a la fecha de corte. */
export function Frozen({ what }: { what?: string }) {
  const m = useModel();
  return (
    <span
      className="ml-1 inline-block -translate-y-px rounded-[3px] border border-hairline px-1 align-middle font-mono text-[8.5px] uppercase leading-[13px] tracking-[0.06em] text-ink-3"
      title={`${what ?? "Dato"} del libro v${m.book.meta.version.replace(/^v/, "")} (corte ${m.book.meta.fecha_analisis}); el motor no lo recalcula.`}
      aria-label="valor del libro"
    >
      libro
    </span>
  );
}

/** Estado vivo del libro («● ok (…)»): glifo coloreado + texto sin glifo. */
export function LiveStatus({ text, className, children }: { text: LiveText | undefined; className?: string; children?: ReactNode }) {
  const m = useModel();
  const s = m.live(text);
  return (
    <Status kind={statusOf(s)} className={className}>
      {stripGlyph(s)}
      {children}
    </Status>
  );
}

/** Rastro «¿de dónde sale?»: nombre Excel (mono) y, opcionalmente, la celda de la hoja. */
export function Trace({ name, cell, className }: { name?: string; cell?: string; className?: string }) {
  if (!name && !cell) return null;
  return (
    <span className={`inline-flex items-center gap-1 font-mono text-[10px] text-ink-3 ${className ?? ""}`} title="Nombre definido / celda del libro Excel">
      {name}
      {cell && <span className="text-ink-3/80">· {cell}</span>}
    </span>
  );
}
