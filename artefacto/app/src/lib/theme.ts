import { useCallback, useEffect, useState } from "react";

/**
 * Tema de la interfaz: tres estados.
 *  - "system": sin atributo → decide `prefers-color-scheme` (capa (b) de tokens.css)
 *  - "light" / "dark": `data-theme` en <html> (capa (c) gana en ambas direcciones)
 * La preferencia se persiste en localStorage; todo acceso al almacenamiento va
 * envuelto en try/catch (el host puede bloquearlo: vista previa, ventana privada…).
 */
export type ThemePref = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

export const THEME_PREFS: readonly ThemePref[] = ["system", "light", "dark"];
const STORAGE_KEY = "fv-montecristi.theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

export function isThemePref(value: unknown): value is ThemePref {
  return typeof value === "string" && (THEME_PREFS as readonly string[]).includes(value);
}

export function readStoredTheme(): ThemePref {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return isThemePref(raw) ? raw : "system";
  } catch {
    return "system";
  }
}

export function storeTheme(pref: ThemePref): void {
  try {
    if (pref === "system") window.localStorage.removeItem(STORAGE_KEY);
    else window.localStorage.setItem(STORAGE_KEY, pref);
  } catch {
    /* almacenamiento no disponible: la preferencia vive sólo en memoria */
  }
}

export function applyTheme(pref: ThemePref): void {
  const root = document.documentElement;
  if (pref === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", pref);
}

export function systemPrefersDark(): boolean {
  try {
    return typeof window.matchMedia === "function" && window.matchMedia(DARK_QUERY).matches;
  } catch {
    return false;
  }
}

export function resolveTheme(pref: ThemePref): ResolvedTheme {
  if (pref === "system") return systemPrefersDark() ? "dark" : "light";
  return pref;
}

/** Aplica la preferencia guardada antes del primer render (evita el destello). */
export function initTheme(): ThemePref {
  const pref = readStoredTheme();
  applyTheme(pref);
  return pref;
}

export interface ThemeState {
  pref: ThemePref;
  resolved: ResolvedTheme;
  setPref: (pref: ThemePref) => void;
}

export function useTheme(): ThemeState {
  const [pref, setPrefState] = useState<ThemePref>(() => readStoredTheme());
  const [systemDark, setSystemDark] = useState<boolean>(() => systemPrefersDark());

  // Sincroniza el DOM y el almacenamiento (sistemas externos) con la preferencia.
  useEffect(() => {
    applyTheme(pref);
    storeTheme(pref);
  }, [pref]);

  // Sigue los cambios del sistema (evento externo → estado).
  useEffect(() => {
    let media: MediaQueryList | undefined;
    try {
      media = window.matchMedia(DARK_QUERY);
    } catch {
      return;
    }
    const onChange = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    media.addEventListener("change", onChange);
    return () => media?.removeEventListener("change", onChange);
  }, []);

  const setPref = useCallback((next: ThemePref) => setPrefState(next), []);
  const resolved: ResolvedTheme = pref === "system" ? (systemDark ? "dark" : "light") : pref;

  return { pref, resolved, setPref };
}
