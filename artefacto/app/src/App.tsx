import { useCallback, useEffect, useState } from "react";

import { CommandMenu } from "@/components/shell/CommandMenu";
import { CompareDialog } from "@/components/shell/CompareDialog";
import { ScenarioDeepLink } from "@/components/shell/ScenarioDeepLink";
import type { Scenario } from "@/model/scenarios";
import { MandosPanel } from "@/components/shell/MandosPanel";
import { CaseSelector } from "@/components/shell/CaseSelector";
import { NavStrip, SideNav } from "@/components/shell/SideNav";
import { TopBar } from "@/components/shell/TopBar";
import { ViewPlaceholder } from "@/components/shell/ViewPlaceholder";
import { ModelProvider } from "@/model/store";
import { Resumen } from "@/views/Resumen";
import { Sensibilidad } from "@/views/Sensibilidad";
import { Supuestos } from "@/views/Supuestos";
import { Energia } from "@/views/Energia";
import { Capex } from "@/views/Capex";
import { Opex } from "@/views/Opex";
import { Fiscal } from "@/views/Fiscal";
import { Flujo } from "@/views/Flujo";
import { Legal } from "@/views/Legal";
import { Tramites } from "@/views/Tramites";
import { Riesgos } from "@/views/Riesgos";
import { Fuentes } from "@/views/Fuentes";
import { Controles } from "@/views/Controles";
import { Guia } from "@/views/Guia";
import { Exergy } from "@/internal/Exergy";

/**
 * Vista interna «Exergy»: la constante de compilación pliega la condición en la edición externa, la importación queda sin uso
 * y el empaquetador elimina el módulo (mismo patrón que INTERNAL_MARKER en lib/edition.ts; verificado por check:exclusion).
 */
const ExergyView = process.env.VITE_EDITION !== "externo" ? Exergy : null;
import { TooltipProvider } from "@/components/ui/tooltip";
import { EDITION, INTERNAL_MARKER } from "@/lib/edition";
import { applyFocus, takeFocusParam, useHashNav } from "@/lib/hash";
import { cn } from "@/lib/utils";

/**
 * Cascarón de la aplicación (F3). Retícula CSS:
 *   fila 1: barra superior (ancho completo)
 *   fila 2: nav izquierda · área principal · [cajón «Mandos»]
 * En anchos < md la nav pasa a una tira horizontal bajo la barra.
 */
export default function App() {
  const { view, caseId, navigate, setCase } = useHashNav();
  const [commandOpen, setCommandOpen] = useState(false);
  const [mandosOpen, setMandosOpen] = useState(false);
  const [compare, setCompare] = useState<Scenario[] | null>(null);

  const toggleMandos = useCallback(() => setMandosOpen((v) => !v), []);
  const openCompare = useCallback((scenarios: Scenario[]) => setCompare(scenarios), []);
  useEffect(() => {
    // #s=<id> abre el cajón de escenarios para que el visitante vea qué se cargó
    if (new URLSearchParams(window.location.hash.replace(/^#/, "")).get("s")) setMandosOpen(true);
  }, []);
  useEffect(() => {
    // #f=… (paleta ⌘K): desplazar y resaltar el destino una vez montada la vista
    const consume = () => { const f = takeFocusParam(); if (f) applyFocus(f); };
    consume();
    window.addEventListener("hashchange", consume);
    return () => window.removeEventListener("hashchange", consume);
  }, [view]);

  return (
    <ModelProvider>
    <TooltipProvider delayDuration={300}>
      <div
        data-edition={EDITION}
        data-internal-marker={INTERNAL_MARKER ?? undefined}
        className={cn(
          "grid h-dvh min-w-0 grid-rows-[auto_minmax(0,1fr)] bg-bg text-ink",
          "md:grid-cols-[224px_minmax(0,1fr)]",
          mandosOpen && "md:grid-cols-[224px_minmax(0,1fr)_320px]",
          "max-md:grid-cols-[minmax(0,1fr)]",
        )}
      >
        <TopBar
          className="col-span-full"
          caseId={caseId}
          onCaseChange={setCase}
          onOpenCommand={() => setCommandOpen(true)}
          mandosOpen={mandosOpen}
          onToggleMandos={toggleMandos}
        />

        {/* Nav vertical (≥ md) */}
        <SideNav
          view={view}
          onNavigate={navigate}
          className="min-h-0 overflow-y-auto border-r border-hairline bg-surface max-md:hidden"
        />

        <div className="flex min-h-0 min-w-0 flex-col">
          {/* Nav horizontal + selector de caso (< md / < lg) */}
          <div className="border-b border-hairline bg-surface md:hidden">
            <NavStrip view={view} onNavigate={navigate} />
          </div>
          <div className="border-b border-hairline bg-surface px-3 py-1.5 lg:hidden">
            <CaseSelector value={caseId} onChange={setCase} />
          </div>

          <main className="min-h-0 min-w-0 flex-1 overflow-auto px-6 py-5">
            {view === "resumen" ? (
              <Resumen caseId={caseId} onNavigate={navigate} />
            ) : view === "sensibilidad" ? (
              <Sensibilidad caseId={caseId} />
            ) : view === "supuestos" ? (
              <Supuestos caseId={caseId} onNavigate={navigate} />
            ) : view === "energia" ? (
              <Energia caseId={caseId} onNavigate={navigate} />
            ) : view === "capex" ? (
              <Capex caseId={caseId} onNavigate={navigate} />
            ) : view === "opex" ? (
              <Opex caseId={caseId} onNavigate={navigate} />
            ) : view === "fiscal" ? (
              <Fiscal caseId={caseId} onNavigate={navigate} />
            ) : view === "flujo" ? (
              <Flujo caseId={caseId} onNavigate={navigate} />
            ) : view === "exergy" && ExergyView ? (
              <ExergyView caseId={caseId} onNavigate={navigate} />
            ) : view === "legal" ? (
              <Legal caseId={caseId} onNavigate={navigate} />
            ) : view === "tramites" ? (
              <Tramites caseId={caseId} onNavigate={navigate} />
            ) : view === "riesgos" ? (
              <Riesgos caseId={caseId} onNavigate={navigate} />
            ) : view === "fuentes" ? (
              <Fuentes caseId={caseId} onNavigate={navigate} />
            ) : view === "controles" ? (
              <Controles caseId={caseId} onNavigate={navigate} />
            ) : view === "guia" ? (
              <Guia caseId={caseId} onNavigate={navigate} />
            ) : (
              <ViewPlaceholder view={view} />
            )}
          </main>
        </div>

        {/* ≥ md: tercera columna de la retícula · < md: panel superpuesto a la derecha */}
        {mandosOpen && (
          <MandosPanel
            onClose={toggleMandos}
            onCompare={openCompare}
            className="max-md:fixed max-md:inset-y-0 max-md:right-0 max-md:z-40 max-md:w-[min(320px,90vw)] max-md:shadow-1"
          />
        )}

        <CommandMenu open={commandOpen} onOpenChange={setCommandOpen} onNavigate={navigate} />
        <CompareDialog open={compare !== null} onOpenChange={(o) => { if (!o) setCompare(null); }} scenarios={compare ?? []} caseId={caseId} />
        <ScenarioDeepLink />
      </div>
    </TooltipProvider>
    </ModelProvider>
  );
}
