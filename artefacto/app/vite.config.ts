import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

import { GOOGLE_FONTS_HREF } from "./scripts/fonts.mjs";

/**
 * Edición del build: VITE_EDITION=interno (defecto) | externo.
 * Se expone al código como la constante de compilación `process.env.VITE_EDITION`
 * porque es la única forma que Vite (vía `define`) y Parcel (inlining nativo de
 * process.env en el bundle del artefacto) sustituyen ambos estáticamente y cuyas
 * ramas muertas eliminan. Ver src/lib/edition.ts y NOTES.md.
 */
const edition = process.env.VITE_EDITION === "externo" ? "externo" : "interno";

/**
 * Inyecta el único <link> de Google Fonts en dev y en `vite build`. En el
 * artefacto lo inyecta scripts/to-fragment.mjs (ver scripts/fonts.mjs).
 */
function googleFonts(): Plugin {
  return {
    name: "artefacto:google-fonts",
    transformIndexHtml() {
      return [
        {
          tag: "link",
          attrs: { rel: "stylesheet", href: GOOGLE_FONTS_HREF },
          injectTo: "head",
        },
      ];
    },
  };
}

export default defineConfig({
  plugins: [react(), googleFonts()],
  define: {
    "process.env.VITE_EDITION": JSON.stringify(edition),
  },
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  build: {
    // `dist/` lo usan Parcel (build:bundle) y el fragmento (build:fragment).
    outDir: "dist-vite",
    emptyOutDir: true,
  },
});
