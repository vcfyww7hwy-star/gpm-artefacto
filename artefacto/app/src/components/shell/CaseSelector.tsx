import { CASES, type CaseId } from "@/lib/views";
import { cn } from "@/lib/utils";

interface Props {
  value: CaseId;
  onChange: (next: CaseId) => void;
  className?: string;
}

/**
 * Selector segmentado de caso (placeholder: aún no conectado al motor).
 * Custom se pinta con el acento «tinta»; los ordinales con los grises --c-* y
 * su patrón de trazo --dash-*, la misma codificación que usarán las gráficas.
 */
export function CaseSelector({ value, onChange, className }: Props) {
  return (
    <div
      role="radiogroup"
      aria-label="Caso"
      className={cn(
        "inline-flex h-7 items-stretch rounded-1 border border-hairline bg-surface p-px",
        className,
      )}
    >
      {CASES.map((c) => {
        const active = c.id === value;
        const isCustom = c.id === "custom";
        return (
          <button
            key={c.id}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(c.id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-[3px] px-2.5 text-[12.5px] text-ink-2 transition-colors",
              "hover:text-ink focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
              active && !isCustom && "bg-surface-hover font-medium text-ink",
              active && isCustom && "bg-accent-soft font-medium text-accent",
            )}
          >
            <svg width="14" height="6" viewBox="0 0 14 6" aria-hidden className="shrink-0">
              <line
                x1="0"
                y1="3"
                x2="14"
                y2="3"
                strokeWidth="2"
                style={{ stroke: `var(${c.colorVar})`, strokeDasharray: `var(${c.dashVar})` }}
              />
            </svg>
            {c.label}
          </button>
        );
      })}
    </div>
  );
}
