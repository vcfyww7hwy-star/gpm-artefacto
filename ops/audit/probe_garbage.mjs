import { createRequire } from "node:module"; import { resolve } from "node:path"; import { pathToFileURL } from "node:url";
const require = createRequire(import.meta.url); const { chromium } = require("/home/claude/.npm-global/lib/node_modules/playwright");
const [,, bundlePath, label] = process.argv;
const bundle = pathToFileURL(resolve(bundlePath)).href;
const VIEWS = ["resumen","sensibilidad","supuestos","energia","capex","opex","fiscal","flujo","exergy","legal","tramites","riesgos","fuentes","controles","guia"];
const browser = await chromium.launch(); const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const pat = /fbin&|callTEXT|&TEXT\(|\bstr[#"]|\bname[A-Z][A-Za-z_]+str|\[object Object\]|undefined|NaN/g;
for (const v of VIEWS) {
  await page.goto(`${bundle}#v=${v}&c=custom`); await page.waitForSelector("main h1").catch(()=>{}); await page.waitForTimeout(250);
  const hits = await page.evaluate((src) => { const re = new RegExp(src, "g"); const t = document.querySelector("main")?.innerText ?? ""; const m = [...t.matchAll(re)]; const ctx = m.slice(0, 3).map(x => t.slice(Math.max(0, x.index - 40), x.index + 60).replace(/\s+/g, " ")); return { n: m.length, ctx }; }, pat.source);
  if (hits.n) console.log(`${label} ${v}: ${hits.n} coincidencias ·`, hits.ctx);
}
await browser.close(); console.log(`${label}: fin`);
