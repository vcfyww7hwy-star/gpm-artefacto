import { Monitor, Moon, Sun, type LucideIcon } from "lucide-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useTheme, type ThemePref } from "@/lib/theme";

interface Option {
  value: ThemePref;
  label: string;
  Icon: LucideIcon;
}

const OPTIONS: readonly Option[] = [
  { value: "system", label: "Tema del sistema", Icon: Monitor },
  { value: "light", label: "Tema claro", Icon: Sun },
  { value: "dark", label: "Tema oscuro", Icon: Moon },
];

/**
 * Selector de tema de tres estados (sistema / claro / oscuro).
 * Requiere un <TooltipProvider> por encima (App lo provee).
 */
export function ThemeToggle({ className }: { className?: string }) {
  const { pref, setPref } = useTheme();

  return (
    <div
      role="radiogroup"
      aria-label="Tema"
      className={cn(
        "inline-flex h-7 items-stretch rounded-1 border border-hairline bg-surface p-px",
        className,
      )}
    >
      {OPTIONS.map(({ value, label, Icon }) => {
        const active = pref === value;
        return (
          <Tooltip key={value}>
            <TooltipTrigger asChild>
              <button
                type="button"
                role="radio"
                aria-checked={active}
                aria-label={label}
                onClick={() => setPref(value)}
                className={cn(
                  "inline-flex w-7 items-center justify-center rounded-[3px] text-ink-3 transition-colors",
                  "hover:text-ink focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                  active && "bg-surface-hover text-ink",
                )}
              >
                <Icon className="size-3.5" strokeWidth={1.75} aria-hidden />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">{label}</TooltipContent>
          </Tooltip>
        );
      })}
    </div>
  );
}
