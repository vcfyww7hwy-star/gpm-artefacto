import { createRequire } from "node:module"; import { resolve } from "node:path"; import { pathToFileURL } from "node:url";
const require = createRequire(import.meta.url); const { chromium } = require("/home/claude/.npm-global/lib/node_modules/playwright");
const OUT = "out_r4";
const browser = await chromium.launch();
for (const ed of ["interno", "externo"]) {
  const bundle = pathToFileURL(resolve(process.env.APP_DIR, `out/${ed}/bundle.html`)).href;
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = []; page.on("pageerror", e => errs.push(String(e)));
  // 1) Sensibilidad: tornado con la barra «Escalación tarifa +1 pp/año»
  await page.goto(`${bundle}#v=sensibilidad&c=custom`); await page.waitForSelector("main h1"); await page.waitForTimeout(400);
  const txt = await page.locator("main").innerText();
  const m = txt.match(/Escalación tarifa[^\n]*/g); console.log(ed, "tornado etiquetas:", m);
  const nota = txt.match(/\(3\)[^\n]*/g); console.log(ed, "nota (3):", nota && nota[0]);
  const sec = page.locator("section", { hasText: "Escalación tarifa" }).first(); await sec.scrollIntoViewIfNeeded(); await page.waitForTimeout(200);
  await sec.screenshot({ path: `${OUT}/r4-${ed}-tornado.png` });
  // 2) Resumen (portada): top 9 del tornado
  await page.goto(`${bundle}#v=resumen&c=custom`); await page.waitForSelector("main h1"); await page.waitForTimeout(400);
  const t2 = await page.locator("main").innerText(); console.log(ed, "portada incluye Escalación tarifa:", /Escalación tarifa \+1 pp/.test(t2), "· Contrato:", /Contrato de Inversión/.test(t2));
  await page.screenshot({ path: `${OUT}/r4-${ed}-resumen.png`, fullPage: true });
  // 3) Acerca de
  await page.click("button:has-text('Motor ≡ Excel')"); await page.waitForSelector("[role=dialog]"); await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/r4-${ed}-acerca-de.png` });
  console.log(ed, "acerca de:", (await page.locator("[role=dialog]").innerText()).slice(0, 700).replace(/\n+/g, " | "));
  await page.keyboard.press("Escape");
  // 4) Guía 00b: frase D-V2-9
  await page.goto(`${bundle}#v=guia&c=custom`); await page.waitForSelector("main h1"); await page.waitForTimeout(300);
  const g = await page.locator("main").innerText(); console.log(ed, "00b D-V2-9:", /TIR real del accionista/.test(g));
  console.log(ed, "errores de página:", errs);
  await page.close();
}
await browser.close();
