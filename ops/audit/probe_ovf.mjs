import { createRequire } from "node:module"; import { resolve } from "node:path"; import { pathToFileURL } from "node:url";
const require = createRequire(import.meta.url); const { chromium } = require("/home/claude/.npm-global/lib/node_modules/playwright");
const APP = process.env.APP_DIR; const bundle = pathToFileURL(resolve(APP, "out/interno/bundle.html")).href;
const browser = await chromium.launch(); const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto(`${bundle}#v=resumen&c=custom`); await page.waitForSelector("main h1"); await page.waitForTimeout(300);
const r = await page.evaluate(() => {
  const main = document.querySelector("main"); const mr = main.getBoundingClientRect();
  // buscar el descendiente con scrollWidth máximo respecto a su clientWidth y overflow visible
  const cands = [...main.querySelectorAll("*")].map(el => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect(); return { el, cs, r, over: el.scrollWidth - el.clientWidth }; })
    .filter(x => x.over > 20 && x.cs.overflowX === "visible").sort((a, b) => b.over - a.over).slice(0, 8)
    .map(x => ({ tag: x.el.tagName.toLowerCase(), cls: (x.el.className || "").toString().slice(0, 90), over: x.over, w: Math.round(x.r.width), left: Math.round(x.r.left - mr.left), text: x.el.textContent.trim().slice(0, 30) }));
  // ¿qué hay más a la derecha? desplazar y listar
  main.scrollLeft = 10000; const sl = main.scrollLeft;
  const far = [...main.querySelectorAll("*")].filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.right > mr.right - 2 && r.left > mr.left + mr.width * 0.5; }).slice(0, 8)
    .map(el => ({ tag: el.tagName.toLowerCase(), cls: (el.className || "").toString().slice(0, 90), w: Math.round(el.getBoundingClientRect().width), text: el.textContent.trim().slice(0, 30) }));
  return { scrolledTo: sl, cands, far };
});
console.log(JSON.stringify(r, null, 1));
await page.screenshot({ path: "out2_interno/resumen-scrolled-right.png" });
await browser.close();
