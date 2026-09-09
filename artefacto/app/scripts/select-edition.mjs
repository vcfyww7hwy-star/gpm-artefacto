#!/usr/bin/env node
/**
 * Escribe src/model/edition-data.ts con las importaciones de datos de la edición a compilar (VITE_EDITION=interno|externo).
 * Los JSON no se eliminan por tree-shaking con seguridad, así que la selección se hace ANTES del bundle: el bundle sólo
 * contiene los datos de su edición (check-exclusion.mjs lo verifica con cadenas prohibidas).
 */
import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const EDITION = process.env.VITE_EDITION === "externo" ? "externo" : "interno";
const suffix = EDITION === "externo" ? ".externo" : "";
const src = `// GENERADO por scripts/select-edition.mjs — edición «${EDITION}». No editar: se reescribe en cada build.
// Datos del libro de esta edición (book.json, entradas v3.1 y oráculo). La externa excluye físicamente los internos de Exergy.
import book from "@/model/book_v31${suffix}.json";
import inputs from "@/model/inputs_v31${suffix}.json";
import oracle from "@/model/oracle_v31${suffix}.json";

export const EDITION_DATA = "${EDITION}" as const;
export { book, inputs, oracle };
`;
writeFileSync(resolve(ROOT, "src/model/edition-data.ts"), src);
console.log(`✔ edition-data.ts → ${EDITION}`);
