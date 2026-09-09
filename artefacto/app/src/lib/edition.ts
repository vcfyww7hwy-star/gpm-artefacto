import { INTERNO_MARKER_9F2A } from "@/internal/marker";

/**
 * Edición del artefacto.
 *  - «interno»: equipo GPM / analistas (todo el contenido).
 *  - «externo»: terceros (sin los módulos de `src/internal/`).
 *
 * La edición se fija en tiempo de build con la variable de entorno
 * `VITE_EDITION` (defecto: interno). Dentro del código se lee SIEMPRE como
 * `process.env.VITE_EDITION`, la constante de compilación que Vite (`define`)
 * y Parcel (inlining nativo) sustituyen por un literal y cuyas ramas muertas
 * eliminan antes de empaquetar; `import.meta.env` no existe en Parcel.
 */
export type Edition = "interno" | "externo";

export const EDITION: Edition =
  process.env.VITE_EDITION === "externo" ? "externo" : "interno";

export function isInterno(): boolean {
  return EDITION === "interno";
}

export function isExterno(): boolean {
  return EDITION === "externo";
}

/**
 * Patrón de exclusión física: el único uso del módulo interno está detrás de la
 * constante de compilación. En la edición externa la condición se pliega a
 * `false`, la rama muere, la importación queda sin uso y el empaquetador
 * elimina el módulo (Parcel: scope hoisting + minificación; Rollup: tree
 * shaking). Verificado por `npm run check:exclusion`.
 */
export const INTERNAL_MARKER: string | null =
  process.env.VITE_EDITION !== "externo" ? INTERNO_MARKER_9F2A : null;
