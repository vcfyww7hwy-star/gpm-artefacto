import type { ReactNode } from "react";

import { CASES, type CaseId } from "@/lib/views";
import { cn } from "@/lib/utils";

export interface StripValue {
  caseId: CaseId;
  text: string;
  /** true si el valor está bajo el umbral (se pinta en riesgo) */
  below?: boolean;
}

interface Props {
  label: string;
  /** cifra grande del caso seleccionado */
  value: string;
  /** comparación con el umbral («frente al 10 % exigido») */
  compare?: ReactNode;
  /** estado frente al umbral: ok / risk / neutral */
  state?: "ok" | "risk" | "neutral";
  /** tira C · B · F (y Custom si no es el seleccionado) */
  strip?: StripValue[];
  /** nombre Excel del indicador (mono) para «¿de dónde sale?» */
  excelName?: string;
  className?: string;
}

/**
 * Tarjeta de indicador: etiqueta · cifra grande (tabular) · comparación con el umbral · tira de los otros casos.
 * El color sólo aparece donde hay significado: la cifra en riesgo si está bajo el umbral; la tira en los grises ordinales.
 */
export function KpiTile({ label, value, compare, state = "neutral", strip, excelName, className }: Props) {
  return (
    <div className={cn("flex min-w-0 flex-col gap-1 border-t border-hairline pt-2", className)}>
      <span className="text-[10.5px] font-medium uppercase leading-tight tracking-[0.06em] text-ink-3" title={excelName}>{label}</span>
      <div
        className={cn("whitespace-nowrap font-semibold leading-none tracking-[-0.01em]", state === "risk" ? "text-risk" : "text-ink")}
        style={{ fontVariantNumeric: "tabular-nums", fontSize: "clamp(19px, 1.65vw, 28px)" }}
      >
        {value}
      </div>
      {compare && <div className="text-[12px] text-ink-2">{compare}</div>}
      {strip && strip.length > 0 && (
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
          {strip.map((s) => {
            const meta = CASES.find((c) => c.id === s.caseId)!;
            return (
              <span key={s.caseId} className="inline-flex items-center gap-1.5 text-[11.5px]" style={{ fontVariantNumeric: "tabular-nums" }} title={meta.label}>
                <svg width="14" height="6" viewBox="0 0 14 6" aria-hidden>
                  <line x1="0" y1="3" x2="14" y2="3" strokeWidth="2" style={{ stroke: `var(${meta.colorVar})`, strokeDasharray: `var(${meta.dashVar})` }} />
                </svg>
                <span className="text-ink-3">{meta.label.slice(0, 1)}</span>
                <span className={cn(s.below ? "text-risk" : "text-ink-2")}>{s.text}</span>
              </span>
            );
          })}
        </div>
      )}
      {excelName && <div className="mt-0.5 font-mono text-[10px] text-ink-3">{excelName}</div>}
    </div>
  );
}
