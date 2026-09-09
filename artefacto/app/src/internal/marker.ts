/**
 * Módulo SÓLO de la edición interna.
 *
 * Todo lo que viva en `src/internal/` debe importarse únicamente desde una
 * expresión guardada por la constante de compilación
 * `process.env.VITE_EDITION !== "externo"` (ver src/lib/edition.ts). Así el
 * bundle «externo» no contiene físicamente este código: `npm run check:exclusion`
 * verifica que la cadena de abajo aparece en el bundle interno y NO en el externo.
 */
export const INTERNO_MARKER_9F2A = "INTERNO_MARKER_9F2A";
