import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export type StatusKind = "ok" | "warn" | "risk" | "info";

/** Glifos de estado del libro (13_Controles, candados): ● ok · ▲ atención · ■ riesgo · ◇ informativo. */
export const GLYPH: Record<StatusKind, { g: string; cls: string }> = {
  ok: { g: "●", cls: "text-ok" },
  warn: { g: "▲", cls: "text-warn-text" },
  risk: { g: "■", cls: "text-risk" },
  info: { g: "◇", cls: "text-info" },
};

export function StatusGlyph({ kind, className }: { kind: StatusKind; className?: string }) {
  return <span aria-hidden className={cn("text-[9px] leading-none", GLYPH[kind].cls, className)}>{GLYPH[kind].g}</span>;
}

/** Chip de estado: glifo + texto (el texto va en tinta secundaria; el color sólo en el glifo). */
export function Status({ kind, children, mono, className }: { kind: StatusKind; children: ReactNode; mono?: boolean; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[12px] text-ink-2", mono && "font-mono", className)}>
      <StatusGlyph kind={kind} />
      {children}
    </span>
  );
}

/** Quita el glifo inicial de un texto de estado del libro («● ok (…)» → «ok (…)»). */
export function stripGlyph(text: string): string {
  return text.replace(/^[●▲■◇]\s*/, "");
}
