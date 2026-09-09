import { useState } from "react";
import { cn } from "@/lib/utils";
import { ORACLE, useModel } from "@/model/store";
import { AboutPanel } from "@/components/shell/AboutPanel";

export type SelfCheckStatus = "pending" | "ok" | "warn" | "risk";

interface Props {
  /** Estado de la autocomprobación motor TS ≡ Excel. Sin datos: "pending". */
  status?: SelfCheckStatus;
  /** Controles superados / totales. Sin datos se muestra «—/—». */
  passed?: number;
  total?: number;
  className?: string;
}

const DOT: Record<SelfCheckStatus, string> = {
  pending: "text-ink-3",
  ok: "text-ok",
  warn: "text-warn-fill",
  risk: "text-risk",
};

/** Chip vivo «● Motor ≡ Excel n/m» (placeholder hasta que el motor reporte). */
export function SelfCheckChip({ status: statusProp, passed: passedProp, total: totalProp, className }: Props) {
  const m = useModel();
  const status: SelfCheckStatus = statusProp ?? (m.dirty > 0 ? "pending" : m.selfCheck.status);
  const passed = passedProp ?? (m.selfCheck.compared - m.selfCheck.failed);
  const total = totalProp ?? m.selfCheck.compared;
  const ratio = m.dirty > 0 ? `sandbox · ${m.dirty}` : `${passed}/${total}`;
  const title = m.dirty > 0
    ? `${m.dirty} entrada(s) distinta(s) del libro: el motor calcula en vivo; la comparación con el Excel sólo aplica a los valores del libro`
    : `${passed} de ${total} salidas de los ${ORACLE.cases.length} casos del Motor coinciden con el Excel/LibreOffice (tolerancia 1e-9); libro ${ORACLE.version} · calc SHA ${ORACLE.calc_sha256.slice(0, 8)}`;
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title={title + " · clic: acerca de esta versión"}
        aria-haspopup="dialog"
        className={cn(
          "inline-flex h-7 items-center gap-1.5 whitespace-nowrap rounded-1 border border-hairline bg-surface px-2 font-mono text-[12px] text-ink-2 hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
          className,
        )}
      >
        <span role="status" aria-live="polite" className="contents">
          <span aria-hidden className={cn("text-[10px] leading-none", DOT[status])}>
            ●
          </span>
          <span>{m.dirty > 0 ? "Motor vivo" : "Motor ≡ Excel"}</span>
          <span className="text-ink">{ratio}</span>
        </span>
      </button>
      <AboutPanel open={open} onOpenChange={setOpen} />
    </>
  );
}
