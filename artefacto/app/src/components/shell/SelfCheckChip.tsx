import { cn } from "@/lib/utils";
import { ORACLE, useModel } from "@/model/store";

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
  return (
    <span
      role="status"
      aria-live="polite"
      title={title}
      className={cn(
        "inline-flex h-7 items-center gap-1.5 whitespace-nowrap rounded-1 border border-hairline bg-surface px-2 font-mono text-[12px] text-ink-2",
        className,
      )}
    >
      <span aria-hidden className={cn("text-[9px] leading-none", DOT[status])}>
        ●
      </span>
      <span>{m.dirty > 0 ? "Motor vivo" : "Motor ≡ Excel"}</span>
      <span className="text-ink">{ratio}</span>
    </span>
  );
}
