#!/usr/bin/env node
/**
 * Verifica la exclusión FÍSICA de la edición interna:
 *   - out/interno/{bundle,fragment}.html  DEBEN contener INTERNO_MARKER_9F2A
 *   - out/externo/{bundle,fragment}.html  NO deben contenerlo
 * También comprueba que cada bundle declara su edición (data-edition).
 * Requiere haber ejecutado `npm run build:interno` y `npm run build:externo`.
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MARKER = "INTERNO_MARKER_9F2A";
/**
 * Contenido que NO puede existir en la edición externa: la vista interna (marcador), los textos internos del libro (hoja 09,
 * bloque H de 01, glosario, memo de 06) y los VALORES de las tres entradas internas de Exergy (sus claves siguen existiendo en
 * el motor con valor 0: son estructura, no datos). Cadenas literales o expresiones regulares.
 */
const FORBIDDEN_EXTERNO = [
  MARKER,
  "EXERGY_VIEW_MARKER_7C1D",
  "Negocio Exergy",
  "Negocio de Exergy",
  "costo interno de Exergy",
  "Costo propio de Exergy",
  "margen de Exergy",
  "Fee de gerencia − costo, margen O&M",
  /Costo_OM_Exergy_kWp"?\s*:\s*(?!0[,}\s])[0-9.]+/,      // valor interno (16) — sólo se admite 0
  /Costo_Gerencia_Pct"?\s*:\s*(?!0[,}\s])[0-9.]+/,        // valor interno (0,025) — sólo se admite 0
  /Tasa_Efectiva_Exergy"?\s*:\s*(?!0[,}\s])[0-9.]+/,      // valor interno (0,3625) — sólo se admite 0
];
const hit = (html, s) => (typeof s === "string" ? html.includes(s) : s.test(html));
const label = (s) => (typeof s === "string" ? s : s.source.slice(0, 32));

let failed = false;
const results = [];

for (const edition of ["interno", "externo"]) {
  for (const file of ["bundle.html", "fragment.html"]) {
    const p = resolve(ROOT, "out", edition, file);
    if (!existsSync(p)) {
      results.push({ edition, file, ok: false, detail: `falta ${p} (ejecuta npm run build:${edition})` });
      failed = true;
      continue;
    }
    const html = readFileSync(p, "utf8");
    const count = html.split(MARKER).length - 1;
    const expectMarker = edition === "interno";
    const okMarker = expectMarker ? count > 0 : count === 0;
    const declares = html.includes(`"${edition}"`) || html.includes(`data-edition="${edition}"`);
    const leaks = edition === "externo" ? FORBIDDEN_EXTERNO.filter((s) => hit(html, s)).map(label) : [];
    const ok = okMarker && declares && leaks.length === 0;
    if (!ok) failed = true;
    results.push({
      edition,
      file,
      ok,
      detail: `${MARKER} ×${count} (${expectMarker ? "debe aparecer" : "no debe aparecer"}) · edición declarada: ${declares ? "sí" : "no"}${edition === "externo" ? ` · cadenas internas: ${leaks.length === 0 ? "ninguna" : leaks.join(", ")}` : ""} · ${(html.length / 1024).toFixed(1)} KB`,
    });
  }
}

for (const r of results) console.log(`${r.ok ? "  ✔" : "  ✖"} ${r.edition.padEnd(7)} ${r.file.padEnd(13)} ${r.detail}`);
if (failed) {
  console.error("\n✖ check:exclusion FALLÓ");
  process.exit(1);
}
console.log("\n✔ check:exclusion OK — el marcador interno sólo existe en la edición interna");
