import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";
const require = createRequire(import.meta.url);
const { chromium } = require("/home/claude/.npm-global/lib/node_modules/playwright");
const ed = process.argv[2] ?? "interno";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const errs=[]; page.on("console", m => { if (m.type()==="error") errs.push(m.text()); }); page.on("pageerror", e => errs.push(String(e)));
const url = pathToFileURL(resolve("out", ed, "bundle.html")).href;
await page.goto(`${url}#v=flujo&c=custom`); await page.waitForSelector("main h1");
console.log("h1 flujo =", JSON.stringify(await page.textContent("main h1")));
console.log("data-view / hash =", await page.evaluate(()=>[document.querySelector('[data-view]')?.getAttribute('data-view'), location.hash]));
await page.goto(`${url}#v=riesgos`); await page.waitForTimeout(300);
console.log("h1 riesgos =", JSON.stringify(await page.textContent("main h1")));
// ⌘K: primeras 6 coincidencias para "Riesgos"
await page.keyboard.press("Control+K"); await page.waitForSelector("[cmdk-root]");
await page.keyboard.type("Riesgos"); await page.waitForTimeout(200);
const items = await page.$$eval("[cmdk-item]", els => els.slice(0,6).map(e => e.textContent.trim().slice(0,70)));
console.log("⌘K 'Riesgos' →", items);
await page.keyboard.press("Escape");
// fragment-host
const host = pathToFileURL(resolve("out", ed, "shots", "fragment-host.html")).href;
const p2 = await browser.newPage({ viewport:{width:1280,height:800} });
const e2=[]; p2.on("console", m=>{ if(m.type()==="error") e2.push(m.text()); }); p2.on("pageerror", e=>e2.push(String(e)));
await p2.goto(`${host}#v=guia`); await p2.waitForTimeout(800);
console.log("host: title =", JSON.stringify(await p2.title()), "| h1 =", JSON.stringify(await p2.textContent("main h1").catch(()=>null)), "| errores:", e2);
console.log("errores consola app:", errs);
await browser.close();
