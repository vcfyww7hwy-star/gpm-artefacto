/// <reference types="vite/client" />

/**
 * `process.env.VITE_EDITION` es una CONSTANTE DE COMPILACIÓN, no un objeto en
 * tiempo de ejecución: Vite la sustituye vía `define` (vite.config.ts) y Parcel
 * la inserta nativamente al construir el artefacto. Sólo se declara aquí para
 * TypeScript. No añadir otras claves sin darlas de alta en vite.config.ts.
 */
declare const process: {
  readonly env: {
    readonly VITE_EDITION?: string;
  };
};
