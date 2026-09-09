#!/usr/bin/env node
/**
 * bundle.html  →  dist/fragment.html
 *
 * Convierte el bundle de Parcel + html-inline en un FRAGMENTO HTML para el
 * publicador de Artifacts de claude.ai, que envuelve el contenido en su propio
 * esqueleto <!doctype html><html><head>…</head><body>…</body>. Se eliminan
 * <!DOCTYPE>, <html>, <head>, <body> y <meta>, y se conservan, en este orden:
 *   1. <title>
 *   2. el único <link> a Google Fonts (se inyecta si el bundle no lo trae)
 *   3. todos los <style>
 *   4. el <div id="root"> (y cualquier otro elemento del body, en orden)
 *   5. todos los <script> inline (los `type="module"` lo conservan)
 *
 * CSP: falla si algún src=/href= apunta a un host externo distinto de
 * fonts.googleapis.com / fonts.gstatic.com, o si queda un <script src>.
 *
 * Uso:  node scripts/to-fragment.mjs [bundle.html] [--out dist/fragment.html]
 * Env:  VITE_EDITION=interno|externo  → copia además a out/<edición>/
 *       FRAGMENT_TARGET_BYTES          → objetivo de tamaño (defecto 1.500.000)
 */
import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parse, serializeOuter } from "parse5";

import { ALLOWED_HOSTS, GOOGLE_FONTS_HREF } from "./fonts.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const outIdx = args.indexOf("--out");
const OUT = resolve(ROOT, outIdx >= 0 ? args[outIdx + 1] : "dist/fragment.html");
const INPUT = resolve(ROOT, args.find((a, i) => !a.startsWith("--") && i !== outIdx + 1) ?? "bundle.html");
const TARGET_BYTES = Number(process.env.FRAGMENT_TARGET_BYTES ?? 1_500_000);
const EDITION = process.env.VITE_EDITION === "externo" ? "externo" : "interno";

const fail = (msg) => {
  console.error(`✖ to-fragment: ${msg}`);
  process.exit(2);
};
const fmtKB = (n) => `${(n / 1024).toFixed(1)} KB`;

if (!existsSync(INPUT)) fail(`no existe ${INPUT} (ejecuta primero npm run build:bundle)`);
const source = readFileSync(INPUT, "utf8");
const doc = parse(source);

/* --- helpers sobre el árbol de parse5 -------------------------------------- */
const isElement = (n) => typeof n.tagName === "string";
const attr = (el, name) => el.attrs?.find((a) => a.name === name)?.value;
const children = (n) => n.childNodes ?? [];
const textOf = (el) => children(el).map((c) => c.value ?? "").join("");

const htmlEl = children(doc).find((n) => n.nodeName === "html");
if (!htmlEl) fail("el bundle no tiene elemento <html>");
const headEl = children(htmlEl).find((n) => n.nodeName === "head");
const bodyEl = children(htmlEl).find((n) => n.nodeName === "body");

/* --- clasificación --------------------------------------------------------- */
const titles = [];
const fontLinks = [];
const styles = [];
const bodyContent = [];
const scripts = [];
const warnings = [];
const errors = [];

const hostOf = (url) => {
  if (!url) return null;
  const m = /^(?:https?:)?\/\/([^/?#]+)/i.exec(url.trim());
  return m ? m[1].toLowerCase() : null;
};
const checkExternal = (where, url) => {
  const host = hostOf(url);
  if (host && !ALLOWED_HOSTS.includes(host)) errors.push(`${where}: host externo no permitido «${host}» (${url.slice(0, 80)})`);
  return host;
};
const URL_ATTRS = ["src", "href", "xlink:href", "poster", "data", "srcset", "action", "formaction"];
const walkAttrs = (el, where) => {
  for (const a of el.attrs ?? []) {
    if (URL_ATTRS.includes(a.name)) checkExternal(`${where} <${el.tagName} ${a.name}>`, a.value);
  }
  for (const c of children(el)) if (isElement(c)) walkAttrs(c, where);
};

const classify = (node, where) => {
  if (!isElement(node)) {
    if (node.nodeName === "#text" && node.value.trim()) warnings.push(`${where}: texto suelto descartado: ${JSON.stringify(node.value.trim().slice(0, 40))}`);
    return; // comentarios y espacios se descartan
  }
  switch (node.tagName) {
    case "meta":
      return; // el host aporta charset/viewport
    case "title":
      titles.push(node);
      return;
    case "link": {
      const host = checkExternal(`${where} <link>`, attr(node, "href"));
      if (host && ALLOWED_HOSTS.includes(host)) fontLinks.push(node);
      else warnings.push(`${where}: <link rel="${attr(node, "rel")}"> no externo descartado (${attr(node, "href")})`);
      return;
    }
    case "style": {
      const css = textOf(node);
      for (const m of css.matchAll(/url\(\s*['"]?([^'")\s]+)/g)) checkExternal(`${where} <style> url()`, m[1]);
      for (const m of css.matchAll(/@import\s+(?:url\()?\s*['"]?([^'")\s;]+)/g)) checkExternal(`${where} <style> @import`, m[1]);
      styles.push(node);
      return;
    }
    case "script": {
      if (attr(node, "src") !== undefined) errors.push(`${where}: <script src="${attr(node, "src")}"> no inlinado`);
      scripts.push(node);
      return;
    }
    default:
      if (where === "head") {
        warnings.push(`head: <${node.tagName}> inesperado descartado`);
        return;
      }
      walkAttrs(node, "body");
      bodyContent.push(node);
  }
};

for (const n of children(headEl ?? { childNodes: [] })) classify(n, "head");
for (const n of children(bodyEl ?? { childNodes: [] })) classify(n, "body");

/* --- validaciones estructurales -------------------------------------------- */
if (titles.length !== 1) errors.push(`se esperaba exactamente 1 <title>, hay ${titles.length}`);
if (!bodyContent.some((el) => el.tagName === "div" && attr(el, "id") === "root")) errors.push('falta <div id="root">');
if (scripts.length === 0) errors.push("no hay <script> inline");
if (styles.length === 0) warnings.push("no hay <style> (¿CSS no inlinado?)");
if (fontLinks.length > 1) warnings.push(`hay ${fontLinks.length} <link> a Google Fonts; se conservan todos`);

// URLs externas citadas dentro del JS (sólo informativo: no son cargas de recursos).
const jsHosts = new Set();
for (const s of scripts) for (const m of textOf(s).matchAll(/https?:\/\/([a-z0-9.-]+\.[a-z]{2,})/gi)) jsHosts.add(m[1].toLowerCase());

if (errors.length) {
  for (const e of errors) console.error(`  ✖ ${e}`);
  fail("comprobación CSP/estructura fallida");
}

/* --- ensamblado ------------------------------------------------------------- */
const fontLinkHtml = fontLinks.length
  ? fontLinks.map((n) => serializeOuter(n)).join("\n")
  : `<link rel="stylesheet" href="${GOOGLE_FONTS_HREF.replace(/&/g, "&amp;")}">`;
if (!fontLinks.length) warnings.push("el bundle no traía <link> a Google Fonts: inyectado desde scripts/fonts.mjs");

// título por edición (doc 17: «Modelo FV Montecristi → GPM» interno · «Proyecto FV Montecristi → GPM» externo)
const TITLE = EDITION === "externo" ? "Proyecto FV Montecristi → GPM" : "Modelo FV Montecristi → GPM";
const parts = [
  `<title>${TITLE}</title>`,
  fontLinkHtml,
  ...styles.map((n) => serializeOuter(n)),
  ...bodyContent.map((n) => serializeOuter(n)),
  ...scripts.map((n) => serializeOuter(n)),
];
const fragment = `${parts.join("\n")}\n`;

// Debe empezar por <title> (el publicador sólo busca el título en los primeros 8 KB).
if (!/^<title>/.test(fragment)) fail("el fragmento no empieza por <title>");
if (/<!doctype|<html[\s>]|<head[\s>]|<body[\s>]|<\/html>|<\/head>|<\/body>/i.test(fragment.replace(/<script[\s\S]*?<\/script>/gi, "").replace(/<style[\s\S]*?<\/style>/gi, "")))
  fail("quedan etiquetas de esqueleto (doctype/html/head/body) fuera de script/style");

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, fragment, "utf8");

/* --- informe ---------------------------------------------------------------- */
const bundleBytes = statSync(INPUT).size;
const fragmentBytes = Buffer.byteLength(fragment, "utf8");
const moduleScripts = scripts.filter((s) => attr(s, "type") === "module").length;
const report = {
  edition: EDITION,
  input: INPUT,
  output: OUT,
  bundleBytes,
  fragmentBytes,
  targetBytes: TARGET_BYTES,
  withinTarget: fragmentBytes < TARGET_BYTES,
  title: TITLE,
  counts: { styles: styles.length, scripts: scripts.length, moduleScripts, fontLinks: fontLinks.length || 1, bodyElements: bodyContent.length },
  allowedHosts: ALLOWED_HOSTS,
  cspCheck: "ok",
  jsMentionedHosts: [...jsHosts].sort(),
  warnings,
};
writeFileSync(resolve(dirname(OUT), "fragment.report.json"), JSON.stringify(report, null, 2));

// Copia por edición para conservar ambos bundles a la vez (check:exclusion).
const outDir = resolve(ROOT, "out", EDITION);
mkdirSync(outDir, { recursive: true });
copyFileSync(INPUT, resolve(outDir, "bundle.html"));
copyFileSync(OUT, resolve(outDir, "fragment.html"));
copyFileSync(resolve(dirname(OUT), "fragment.report.json"), resolve(outDir, "fragment.report.json"));

console.log(`✔ fragmento [${EDITION}] → ${OUT}`);
console.log(`  bundle.html   ${fmtKB(bundleBytes)} (${bundleBytes.toLocaleString("en-US")} bytes)`);
console.log(`  fragment.html ${fmtKB(fragmentBytes)} (${fragmentBytes.toLocaleString("en-US")} bytes) · objetivo < ${fmtKB(TARGET_BYTES)} → ${report.withinTarget ? "OK" : "EXCEDIDO"}`);
console.log(`  <title> «${report.title}» · ${styles.length} <style> · ${scripts.length} <script> (${moduleScripts} type=module) · ${report.counts.fontLinks} <link> fonts · ${bodyContent.length} elementos body`);
console.log(`  CSP: OK (hosts externos permitidos: ${ALLOWED_HOSTS.join(", ")})`);
if (jsHosts.size) console.log(`  info: hosts citados dentro del JS (cadenas, no cargas): ${[...jsHosts].sort().join(", ")}`);
for (const w of warnings) console.log(`  ⚠ ${w}`);
console.log(`  copia → out/${EDITION}/{bundle,fragment}.html`);
if (!report.withinTarget) console.log("  ⚠ el fragmento supera el objetivo de tamaño");
