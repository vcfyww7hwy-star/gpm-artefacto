#!/usr/bin/env node
/** audit2.mjs <edición> <outDir> — sondas F1: (1) culpable del overflow en Resumen; (2) Mandos: controles sin nombre, E1 latencia mando→KPI;
 *  (3) ⌘K; (4) capturas altas (viewport = alto real de main) de cada vista en Custom claro/oscuro. */
import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
const require = createRequire(import.meta.url);
const { chromium } = require("/home/claude/.npm-global/lib/node_modules/playwright");
const [,, edition = "interno", outDir = "audit2_out"] = process.argv;
const APP = resolve(process.env.APP_DIR ?? "../artefacto/app");
const bundle = pathToFileURL(resolve(APP, "out", edition, "bundle.html")).href;
mkdirSync(outDir, { recursive: true });
const VIEWS = ["resumen","sensibilidad","supuestos","energia","capex","opex","fiscal","flujo", ...(edition === "interno" ? ["exergy"] : []), "legal","tramites","riesgos","fuentes","controles","guia"];
const browser = await chromium.launch();
const out = { edition, overflowCulprits: null, mandos: null, perf: null, cmdk: null, shots: [] };

// (1) overflow en Resumen
{
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto(`${bundle}#v=resumen&c=custom`); await page.waitForSelector("main h1"); await page.waitForTimeout(300);
  out.overflowCulprits = await page.evaluate(() => {
    const main = document.querySelector("main"); const mr = main.getBoundingClientRect();
    const bad = [...main.querySelectorAll("*")].filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.right > mr.right + 1; })
      .map(el => ({ tag: el.tagName.toLowerCase(), cls: (el.className || "").toString().slice(0, 80), right: Math.round(el.getBoundingClientRect().right - mr.right), w: Math.round(el.getBoundingClientRect().width), text: el.textContent.trim().slice(0, 40) }));
    // el más externo (menor profundidad) de los que desbordan
    return { mainW: Math.round(mr.width), scrollW: main.scrollWidth, sample: bad.slice(0, 6), n: bad.length };
  });
  await page.close();
}

// (2)+(3) Mandos + E1 + ⌘K
{
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = []; page.on("pageerror", e => errors.push(String(e)));
  await page.goto(`${bundle}#v=resumen&c=custom`); await page.waitForSelector("main h1");
  await page.click("button[aria-controls=mandos]"); await page.waitForSelector("aside#mandos"); await page.waitForTimeout(300);
  out.mandos = await page.evaluate(() => {
    const aside = document.querySelector("aside#mandos");
    const ctrls = [...aside.querySelectorAll("input, button, [role=radio], [role=slider], select")];
    const unnamed = ctrls.filter(el => { const n = el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || el.getAttribute("title") || (el.labels && el.labels.length ? "x" : "") || (el.tagName === "BUTTON" || el.getAttribute("role") === "radio" ? el.textContent.trim() : ""); return !n; });
    const ranges = aside.querySelectorAll("input[type=range]").length;
    const rangesUnnamed = [...aside.querySelectorAll("input[type=range]")].filter(el => !el.getAttribute("aria-label") && !(el.labels && el.labels.length)).length;
    const mainW = document.querySelector("main").getBoundingClientRect().width;
    return { controls: ctrls.length, unnamed: unnamed.length, unnamedSample: [...new Set(unnamed.map(e => e.tagName.toLowerCase() + "[" + (e.type || e.getAttribute("role") || "") + "]"))], ranges, rangesUnnamed, asideW: Math.round(aside.getBoundingClientRect().width), mainWWithMandos: Math.round(mainW), mainScrollW: document.querySelector("main").scrollWidth };
  });
  // E1: latencia mando → KPI. Mueve el 1er range (Ratio_DCAC) con teclado y mide hasta que cambie el texto de los KPI.
  const kpiSel = "main h1"; // ancla para saber que existe
  await page.waitForSelector(kpiSel);
  out.perf = await page.evaluate(async () => {
    const range = document.querySelector("aside#mandos input[type=range]");
    const main = document.querySelector("main");
    const snapshot = () => main.innerText;
    const samples = [];
    const setVal = (v) => { const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set; setter.call(range, String(v)); range.dispatchEvent(new Event("input", { bubbles: true })); range.dispatchEvent(new Event("change", { bubbles: true })); };
    const min = parseFloat(range.min), max = parseFloat(range.max), step = parseFloat(range.step);
    let v = parseFloat(range.value);
    for (let i = 0; i < 10; i++) {
      v = v + step > max ? min + step : v + step;
      const before = snapshot(); const t0 = performance.now();
      setVal(v);
      // espera al siguiente frame en que el texto de main haya cambiado (máx 2 s)
      const changed = await new Promise(res => { const start = performance.now(); const tick = () => { if (snapshot() !== before) return res(performance.now() - t0); if (performance.now() - start > 2000) return res(null); requestAnimationFrame(tick); }; requestAnimationFrame(tick); });
      samples.push(changed);
    }
    const mem = performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : null;
    return { input: "Ratio_DCAC", samples: samples.map(s => s === null ? null : Math.round(s)), heapMB: mem };
  });
  // ⌘K: tiempo de apertura y nº de ítems
  await page.keyboard.press("Control+K");
  const tk = Date.now(); await page.waitForSelector("[cmdk-root]"); const openMs = Date.now() - tk;
  await page.waitForTimeout(200);
  const items = await page.$$eval("[cmdk-item]", els => els.length);
  const groups = await page.$$eval("[cmdk-group-heading]", els => els.map(e => e.textContent.trim()));
  out.cmdk = { openMs, itemsVisible: items, groups };
  await page.keyboard.press("Escape");
  out.mandos.pageErrors = errors;
  await page.close();
}

// (4) capturas altas: Custom claro y oscuro, viewport alto = scrollHeight de main (tope 5000)
for (const theme of ["light", "dark"]) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, colorScheme: theme });
  await ctx.addInitScript((t) => { try { localStorage.setItem("fv-montecristi.theme", t); } catch {} }, theme);
  const page = await ctx.newPage();
  for (const view of VIEWS) {
    await page.goto(`${bundle}#v=${view}&c=custom`); await page.waitForSelector("main h1"); await page.waitForTimeout(250);
    const h = await page.evaluate(() => Math.min(5000, Math.max(800, document.querySelector("main").scrollHeight + 60)));
    await page.setViewportSize({ width: 1280, height: h }); await page.waitForTimeout(250);
    const f = `${view}-custom-${theme}.png`;
    await page.screenshot({ path: resolve(outDir, f), fullPage: false });
    out.shots.push({ view, theme, height: h, file: f });
    process.stdout.write(`${theme} ${view}: alto ${h}\n`);
  }
  await ctx.close();
}
await browser.close();
writeFileSync(resolve(outDir, "audit2.json"), JSON.stringify(out, null, 1));
console.log(JSON.stringify({ overflow: out.overflowCulprits, mandos: out.mandos, perf: out.perf, cmdk: out.cmdk }, null, 1));
