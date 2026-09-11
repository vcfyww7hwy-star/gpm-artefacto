import { EDITION } from "@/lib/edition";

/**
 * A1 (11-sep-2026, prueba en el visor real de claude.ai): el visor carga el artefacto en un <iframe> de otro origen
 * (`*.frame.claudeusercontent.com`) y NO le reenvía el fragmento `#…` de la URL pública, por lo que:
 *   - los enlaces profundos `#v= #c= #s= #f=` sólo funcionan DENTRO del artefacto (navegación interna), no desde la URL pública;
 *   - `window.location.href` dentro del marco es una URL tokenizada del marco, inútil para compartir.
 * Por eso «Copiar enlace» usa la URL pública conocida de la edición (constante de compilación) y describe el estado en texto,
 * y la última vista/caso se recuerda en localStorage para reabrir donde se dejó.
 */
export const ARTIFACT_URL: Record<"interno" | "externo", string> = {
  interno: "https://claude.ai/code/artifact/6fb96cf4-613a-4649-ad0c-96704dc4d271",
  externo: "https://claude.ai/code/artifact/dd6ec83a-940b-4a4c-ac9b-5f9e2bd2cda7",
};

/** true cuando la página corre embebida (visor de claude.ai u otro host), false al abrir el bundle directamente. */
export function inEmbeddedViewer(): boolean {
  try { return window.top !== window.self; } catch { return true; }
}

export function publicArtifactUrl(): string {
  return ARTIFACT_URL[EDITION];
}

const LAST_KEY = "fv-montecristi.last";
export function rememberLast(view: string, caseId: string): void {
  try { localStorage.setItem(LAST_KEY, JSON.stringify({ view, caseId })); } catch { /* sin almacenamiento */ }
}
export function readLast(): { view: string; caseId: string } | null {
  try { const raw = localStorage.getItem(LAST_KEY); return raw ? (JSON.parse(raw) as { view: string; caseId: string }) : null; } catch { return null; }
}
