import { Component, type ErrorInfo, type ReactNode } from "react";
import { EDITION_DATA, book, oracle } from "@/model/edition-data";
import { useModel } from "@/model/store";

/**
 * A7 (doc 25 · F1-08): límite de error POR VISTA. Un fallo de render en una vista deja el resto de la aplicación operativa
 * (barra, navegación, mandos) y ofrece un diagnóstico copiable para enviarlo. Textos de interfaz (no son contenido del libro).
 */
interface Props { view: string; caseId: string; inputsJson: () => string; children: ReactNode }
interface State { error: Error | null; info: string; copied: boolean }

export class ViewErrorBoundary extends Component<Props, State> {
  state: State = { error: null, info: "", copied: false };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    this.setState({ info: info.componentStack ?? "" });
    console.error(`[artefacto] error en la vista «${this.props.view}»`, error, info.componentStack);
  }

  componentDidUpdate(prev: Props): void {
    // al cambiar de vista o de caso se reintenta el render
    if ((prev.view !== this.props.view || prev.caseId !== this.props.caseId) && this.state.error) this.setState({ error: null, info: "", copied: false });
  }

  diagnostic(): string {
    const e = this.state.error;
    const meta = (book as { meta?: Record<string, string> }).meta ?? {};
    return [
      `Artefacto Modelo FV Montecristi → GPM · edición ${EDITION_DATA}`,
      `libro ${meta.version ?? "?"} · fecha de análisis ${meta.fecha_analisis ?? "?"} · calc SHA ${(meta.calc_sha256 ?? "").slice(0, 8)} · extraído ${meta.extracted ?? "?"}`,
      `oráculo ${(oracle as { version?: string }).version ?? "?"} · vista «${this.props.view}» · caso «${this.props.caseId}»`,
      `navegador ${typeof navigator !== "undefined" ? navigator.userAgent : "?"} · ${new Date().toISOString()}`,
      `error: ${e?.name ?? "Error"}: ${e?.message ?? ""}`,
      e?.stack ? `pila:\n${e.stack}` : "",
      this.state.info ? `componentes:${this.state.info}` : "",
      `entradas (JSON):\n${this.props.inputsJson()}`,
    ].filter(Boolean).join("\n");
  }

  copy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(this.diagnostic());
      this.setState({ copied: true });
      window.setTimeout(() => this.setState({ copied: false }), 3000);
    } catch {
      // sin portapapeles: el texto queda visible en el <details>
    }
  };

  render(): ReactNode {
    if (!this.state.error) return this.props.children;
    return (
      <section role="alert" className="mx-auto flex max-w-[72ch] flex-col gap-3 rounded-2 border border-risk/40 bg-surface p-5 text-[13px] text-ink">
        <h1 className="text-[16px] font-semibold">Esta vista no se pudo mostrar</h1>
        <p className="text-ink-2">
          Ocurrió un error al dibujar la vista «{this.props.view}». El resto del artefacto sigue funcionando: puede cambiar de vista o de caso.
          Si el problema persiste, copie el diagnóstico y envíelo con una nota de lo que estaba haciendo.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={this.copy} className="inline-flex h-8 items-center rounded-1 border border-hairline bg-surface-2 px-3 text-[12.5px] font-medium hover:bg-surface-hover">
            {this.state.copied ? "Diagnóstico copiado" : "Copiar diagnóstico"}
          </button>
          <button type="button" onClick={() => this.setState({ error: null, info: "" })} className="inline-flex h-8 items-center rounded-1 border border-hairline px-3 text-[12.5px] hover:bg-surface-hover">
            Reintentar
          </button>
        </div>
        <details className="text-[11.5px] text-ink-2">
          <summary className="cursor-pointer">Detalle técnico</summary>
          <pre className="mt-2 max-h-[40vh] overflow-auto whitespace-pre-wrap break-all rounded-1 bg-surface-2 p-2 font-mono text-[10.5px]">{this.diagnostic()}</pre>
        </details>
      </section>
    );
  }
}

/** Envoltorio funcional: toma las entradas vivas del modelo para el diagnóstico (debe estar dentro de ModelProvider). */
export function ViewBoundary({ view, caseId, children }: { view: string; caseId: string; children: ReactNode }) {
  const m = useModel();
  return (
    <ViewErrorBoundary view={view} caseId={caseId} inputsJson={() => JSON.stringify({ inputs: m.inputs, extras: m.extras })}>
      {children}
    </ViewErrorBoundary>
  );
}
