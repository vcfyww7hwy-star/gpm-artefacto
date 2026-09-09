/**
 * Única fuente de verdad de la tipografía web y de la lista CSP de hosts.
 *
 * El <link> de Google Fonts NO vive en index.html: html-inline (el inliner del
 * skill web-artifacts-builder) intenta leer TODO `link[href]` como archivo local
 * y aborta con una URL externa. Por eso se inyecta en dos puntos:
 *   - vite.config.ts  → transformIndexHtml (dev y `vite build`)
 *   - scripts/to-fragment.mjs → dist/fragment.html (artefacto publicado)
 */
export const GOOGLE_FONTS_HREF =
  "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@400;500&family=IBM+Plex+Mono:wght@400;500&display=swap";

/** Hosts externos permitidos por la CSP del publicador de Artifacts (estilos/fuentes). */
export const ALLOWED_HOSTS = ["fonts.googleapis.com", "fonts.gstatic.com"];
