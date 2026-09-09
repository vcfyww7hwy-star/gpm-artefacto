#!/usr/bin/env node
/**
 * audit.mjs — F1 · auditoría con evidencia del artefacto (contenedor, Playwright).
 * Uso: node audit.mjs <edición> <outDir> [--shots=all|custom|none]
 * Para cada vista × caso × tema: carga out/<ed>/bundle.html#v=&c=, fija el tema por localStorage,
 * y mide: errores de consola/página, overflow horizontal, textos recortados, fuentes < 10 px,
 * contraste (WCAG) de textos visibles, controles sin nombre accesible, SVG sin viewBox, tiempo de render.
 * Escribe <outDir>/audit.json y capturas full-page según --shots.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
const require = createRequire(import.meta.url);
const { chromium } = require("/home/claude/.npm-global/lib/node_modules/playwright");

const [,, edition = "interno", outDir = "audit_out", ...flags] = process.argv;
const shotsMode = (flags.find(f => f.startsWith("--shots=")) ?? "--shots=custom").split("=")[1];
const APP = resolve(process.env.APP_DIR ?? "../artefacto/app");
const bundle = pathToFileURL(resolve(APP, "out", edition, "bundle.html")).href;
mkdirSync(outDir, { recursive: true });

const VIEWS = ["resumen","sensibilidad","supuestos","energia","capex","opex","fiscal","flujo", ...(edition === "interno" ? ["exergy"] : []), "legal","tramites","riesgos","fuentes","controles","guia"];
const CASES = ["custom","conservador","base","favorable"];
const THEMES = ["light","dark"];

const browser = await chromium.launch();
const results = [];
const t0 = Date.now();

const METRICS = `(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none"; };
  const parseRGB = (s) => { const m = s.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(",").map(x => parseFloat(x)); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const blend = (fg, bg) => ({ r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 });
  const bgOf = (el) => { let e = el; let acc = null; while (e && e !== document.documentElement) { const c = parseRGB(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { acc = acc ? blend(acc, c) : c; if (c.a >= 1) return acc; } e = e.parentElement; } const root = parseRGB(getComputedStyle(document.body).backgroundColor) || { r: 255, g: 255, b: 255, a: 1 }; return acc ? blend(acc, root) : root; };
  const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
  const textEls = [...document.querySelectorAll("main *, header *, nav *, aside *")].filter(el => vis(el) && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 0));
  let small = 0, lowContrast = [], clipped = [];
  for (const el of textEls) {
    const cs = getComputedStyle(el); const fs = parseFloat(cs.fontSize);
    if (fs < 10) small++;
    const fg0 = parseRGB(cs.color); if (fg0) { const bg = bgOf(el); const fg = fg0.a < 1 ? blend(fg0, bg) : fg0; const r = ratio(fg, bg); const large = fs >= 18.66 || (fs >= 14 && parseInt(cs.fontWeight) >= 700); const need = large ? 3 : 4.5; if (r < need && lowContrast.length < 40) lowContrast.push({ text: el.textContent.trim().slice(0, 40), fg: cs.color, bg: "rgb(" + Math.round(bg.r) + "," + Math.round(bg.g) + "," + Math.round(bg.b) + ")", ratio: Math.round(r * 100) / 100, fs, cls: (el.className || "").toString().slice(0, 60) }); }
    if ((cs.overflow === "hidden" || cs.textOverflow === "ellipsis") && el.scrollWidth > el.clientWidth + 1 && clipped.length < 30) clipped.push({ text: el.textContent.trim().slice(0, 50), cls: (el.className || "").toString().slice(0, 60) });
  }
  const unnamed = [...document.querySelectorAll("button, input, [role=slider], [role=button], a[href]")].filter(el => vis(el)).filter(el => { const name = el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || el.getAttribute("title") || (el.tagName === "INPUT" ? (el.labels && el.labels.length ? "x" : "") : el.textContent.trim()); return !name; }).map(el => el.tagName.toLowerCase() + (el.type ? "[" + el.type + "]" : "") + "." + (el.className || "").toString().split(" ")[0]);
  const svgs = [...document.querySelectorAll("main svg")].filter(vis);
  const svgNoVB = svgs.filter(s => !s.getAttribute("viewBox")).length;
  const svgFixed = svgs.filter(s => s.getAttribute("width") && !/%/.test(s.getAttribute("width")) && parseFloat(s.getAttribute("width")) > 200).length;
  const svgNoRole = svgs.filter(s => !s.getAttribute("role") && !s.getAttribute("aria-label") && s.getBoundingClientRect().width > 120).length;
  const main = document.querySelector("main");
  return {
    h1: (document.querySelector("main h1") || {}).textContent || null,
    hOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    mainOverflowX: main ? main.scrollWidth - main.clientWidth : null,
    textEls: textEls.length, small, lowContrast, clipped,
    unnamedControls: unnamed.length, unnamedSample: [...new Set(unnamed)].slice(0, 8),
    svgs: svgs.length, svgNoVB, svgFixed, svgNoRole,
    tables: document.querySelectorAll("main table").length,
    wideTables: [...document.querySelectorAll("main table")].filter(t => t.scrollWidth > t.parentElement.clientWidth + 1).length,
    pageHeight: document.documentElement.scrollHeight,
    ariaLabels: document.querySelectorAll("[aria-label]").length,
  };
})()`;

for (const theme of THEMES) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, colorScheme: theme });
  await ctx.addInitScript((t) => { try { localStorage.setItem("fv-montecristi.theme", t); } catch {} }, theme);
  const page = await ctx.newPage();
  const errors = [];
  page.on("console", m => { if (m.type() === "error" && !/fonts\.g(oogleapis|static)|ERR_TUNNEL/.test(m.text())) errors.push(m.text()); });
  page.on("pageerror", e => errors.push("pageerror: " + String(e)));
  for (const view of VIEWS) {
    for (const c of CASES) {
      const before = errors.length;
      const tStart = Date.now();
      await page.goto(`${bundle}#v=${view}&c=${c}`, { waitUntil: "load" });
      await page.waitForSelector("main h1", { timeout: 15000 });
      await page.waitForTimeout(250);
      const loadMs = Date.now() - tStart;
      const m = await page.evaluate(METRICS);
      const rec = { edition, view, case: c, theme, loadMs, errors: errors.slice(before), ...m };
      results.push(rec);
      const want = shotsMode === "all" || (shotsMode === "custom" && c === "custom") || (shotsMode === "custom" && view === "resumen");
      if (want) {
        const f = `${view}-${c}-${theme}.png`;
        await page.screenshot({ path: resolve(outDir, f), fullPage: true });
        rec.shot = f;
      }
      process.stdout.write(`${edition} ${theme} ${view}/${c}: ${loadMs} ms · err ${rec.errors.length} · ovf ${m.hOverflow} · clip ${m.clipped.length} · lc ${m.lowContrast.length} · unnamed ${m.unnamedControls}\n`);
    }
  }
  await ctx.close();
}
await browser.close();
writeFileSync(resolve(outDir, "audit.json"), JSON.stringify({ edition, generated: new Date().toISOString(), elapsed_s: Math.round((Date.now() - t0) / 1000), results }, null, 1));
console.log(`\n${results.length} combinaciones · ${Math.round((Date.now() - t0) / 1000)} s → ${outDir}/audit.json`);
