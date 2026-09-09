import { useCallback, useEffect, useState } from "react";
import {
  DEFAULT_CASE,
  DEFAULT_VIEW,
  isCaseId,
  isViewId,
  type CaseId,
  type ViewId,
} from "./views";

/**
 * Estado de navegación en el hash de la URL: `#v=<vista>&c=<caso>`.
 * Funciona dentro del iframe del artefacto (navegación same-document). Si el
 * host bloquea la escritura del hash, el estado sigue viviendo en memoria.
 */
export const HASH_VIEW_KEY = "v";
export const HASH_CASE_KEY = "c";

export function readHashParams(): URLSearchParams {
  try {
    return new URLSearchParams(window.location.hash.replace(/^#/, ""));
  } catch {
    return new URLSearchParams();
  }
}

export function writeHashParams(params: URLSearchParams): boolean {
  try {
    const next = params.toString();
    if (window.location.hash.replace(/^#/, "") === next) return true;
    window.location.hash = next;
    return true;
  } catch {
    return false;
  }
}

export function viewFromHash(params: URLSearchParams = readHashParams()): ViewId {
  const raw = params.get(HASH_VIEW_KEY);
  return isViewId(raw) ? raw : DEFAULT_VIEW;
}

export function caseFromHash(params: URLSearchParams = readHashParams()): CaseId {
  const raw = params.get(HASH_CASE_KEY);
  return isCaseId(raw) ? raw : DEFAULT_CASE;
}

export function hrefForView(id: ViewId): string {
  const params = readHashParams();
  params.set(HASH_VIEW_KEY, id);
  return `#${params.toString()}`;
}

export interface HashNav {
  view: ViewId;
  caseId: CaseId;
  navigate: (view: ViewId) => void;
  setCase: (caseId: CaseId) => void;
}

export function useHashNav(): HashNav {
  const [view, setView] = useState<ViewId>(() => viewFromHash());
  const [caseId, setCaseState] = useState<CaseId>(() => caseFromHash());

  useEffect(() => {
    const onHashChange = () => {
      const params = readHashParams();
      setView(viewFromHash(params));
      setCaseState(caseFromHash(params));
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigate = useCallback((next: ViewId) => {
    setView(next);
    const params = readHashParams();
    params.set(HASH_VIEW_KEY, next);
    writeHashParams(params);
  }, []);

  const setCase = useCallback((next: CaseId) => {
    setCaseState(next);
    const params = readHashParams();
    params.set(HASH_CASE_KEY, next);
    writeHashParams(params);
  }, []);

  return { view, caseId, navigate, setCase };
}

/* --------------------------------------------------------------------------
   Foco: `#f=id:<elementId>` o `#f=row:<rowkey>` (fila de una DataTable). Lo escribe la paleta ⌘K junto con la vista;
   App lo consume (desplaza y resalta) y lo borra del hash.
   -------------------------------------------------------------------------- */
export const HASH_FOCUS_KEY = "f";

export function navigateWithFocus(view: ViewId, focus: string): void {
  const params = readHashParams();
  params.set(HASH_VIEW_KEY, view);
  params.set(HASH_FOCUS_KEY, focus);
  writeHashParams(params);
}

export function takeFocusParam(): string | null {
  const params = readHashParams();
  const f = params.get(HASH_FOCUS_KEY);
  if (f === null) return null;
  params.delete(HASH_FOCUS_KEY);
  writeHashParams(params);
  return f;
}

/** Busca el destino del foco (con reintentos mientras la vista se monta), lo desplaza al centro y lo resalta. */
export function applyFocus(token: string, attempts = 20): void {
  const find = (): HTMLElement | null => {
    if (token.startsWith("id:")) return document.getElementById(token.slice(3));
    if (token.startsWith("row:")) {
      const key = token.slice(4).replace(/"/g, '\\"');
      return document.querySelector<HTMLElement>(`[data-rowkey="${key}"]`);
    }
    return null;
  };
  const tick = (left: number) => {
    const el = find();
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("focus-flash");
      window.setTimeout(() => el.classList.remove("focus-flash"), 2600);
      return;
    }
    if (left > 0) window.setTimeout(() => tick(left - 1), 100);
  };
  tick(attempts);
}
