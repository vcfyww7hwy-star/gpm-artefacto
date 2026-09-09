import { Printer, Search, SlidersHorizontal } from "lucide-react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CaseSelector } from "@/components/shell/CaseSelector";
import { SelfCheckChip } from "@/components/shell/SelfCheckChip";
import { EDITION } from "@/lib/edition";
import type { CaseId } from "@/lib/views";
import { cn } from "@/lib/utils";

/** Atajo mostrado: ⌘ en Apple, Ctrl en el resto (sólo etiqueta; el listener acepta ambos). */
function isMacLike(): boolean {
  try {
    return /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent);
  } catch {
    return false;
  }
}

interface Props {
  caseId: CaseId;
  onCaseChange: (next: CaseId) => void;
  onOpenCommand: () => void;
  mandosOpen: boolean;
  onToggleMandos: () => void;
  className?: string;
}

export function TopBar({
  caseId,
  onCaseChange,
  onOpenCommand,
  mandosOpen,
  onToggleMandos,
  className,
}: Props) {
  return (
    <header
      className={cn(
        "flex h-11 items-center gap-3 border-b border-hairline bg-surface px-3",
        className,
      )}
    >
      <div className="flex min-w-0 items-center gap-2">
        <p className="truncate text-[13px] font-medium text-ink">{EDITION === "externo" ? "Proyecto FV Montecristi → GPM" : "Modelo FV Montecristi → GPM"}</p>
        <Badge
          variant="outline"
          className="h-5 rounded-1 px-1.5 font-mono text-[10.5px] font-medium uppercase tracking-wide text-ink-3"
          title={`Edición ${EDITION}`}
        >
          {EDITION}
        </Badge>
      </div>

      <CaseSelector value={caseId} onChange={onCaseChange} className="ml-2 max-lg:hidden" />

      <div className="ml-auto flex items-center gap-2">
        <Button
          variant="outline"
          size="xs"
          onClick={onOpenCommand}
          className="text-ink-2"
          aria-label="Abrir paleta de comandos"
        >
          <Search aria-hidden />
          <span className="max-md:hidden">Buscar</span>
          <kbd className="ml-1 rounded-[3px] border border-hairline bg-surface-2 px-1 font-mono text-[10.5px] text-ink-3">
            {isMacLike() ? "⌘K" : "Ctrl K"}
          </kbd>
        </Button>

        <SelfCheckChip className="max-md:hidden" />

        <Button variant="outline" size="icon-xs" onClick={() => window.print()} title="Imprimir la vista actual (sólo el contenido)" aria-label="Imprimir la vista actual" className="text-ink-2 max-md:hidden">
          <Printer aria-hidden />
        </Button>

        <Button
          variant={mandosOpen ? "secondary" : "outline"}
          size="xs"
          onClick={onToggleMandos}
          aria-expanded={mandosOpen}
          aria-controls="mandos"
          className={cn(mandosOpen && "border border-hairline text-ink")}
        >
          <SlidersHorizontal aria-hidden />
          Mandos
        </Button>

        <ThemeToggle />
      </div>
    </header>
  );
}
