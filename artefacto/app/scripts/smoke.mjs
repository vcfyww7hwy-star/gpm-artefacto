#!/usr/bin/env node
/**
 * Humo visual/funcional del bundle con Playwright (opcional; requiere el
 * paquete global `playwright` y navegadores en PLAYWRIGHT_BROWSERS_PATH).
 * Abre out/<edición>/bundle.html por file://, toma capturas en claro/oscuro,
 * con «Mandos» abierto y en ancho estrecho, y comprueba navegación por hash,
 * el selector de tema y que no haya errores de consola.
 *
 * Uso: node scripts/smoke.mjs [interno|externo]   → out/<edición>/shots/*.png
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const edition = process.argv[2] === "externo" ? "externo" : "interno";
const bundle = resolve(ROOT, "out", edition, "bundle.html");
const shots = resolve(ROOT, "out", edition, "shots");
mkdirSync(shots, { recursive: true });

let chromium;
try {
  ({ chromium } = require(process.env.PLAYWRIGHT_MODULE ?? "/home/claude/.npm-global/lib/node_modules/playwright"));
} catch {
  console.error("playwright no disponible; omitiendo humo visual");
  process.exit(0);
}

const browser = await chromium.launch();
const errors = [];
const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, colorScheme: "light" });
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
page.on("pageerror", (e) => errors.push(String(e)));

const url = pathToFileURL(bundle).href;
await page.goto(`${url}#v=flujo&c=custom`);
await page.waitForSelector("main h1");

const check = async (name, fn) => {
  const ok = await fn();
  console.log(`${ok ? "  ✔" : "  ✖"} ${name}`);
  if (!ok) process.exitCode = 1;
};

await check("vista inicial desde hash (#v=flujo) — h1 = título de la hoja del libro", async () => /^Flujo/.test(await page.textContent("main h1")));
await check("caso desde hash (c=custom)", async () => (await page.getAttribute('[role=radiogroup][aria-label=Caso] [aria-checked=true]', "aria-checked")) === "true" && (await page.textContent('[role=radiogroup][aria-label=Caso] [aria-checked=true]')) === "Custom");
await check("edición declarada en DOM", async () => (await page.getAttribute("[data-edition]", "data-edition")) === edition);
await check("body pinta var(--bg)", async () => (await page.evaluate(() => getComputedStyle(document.body).backgroundColor)) === "rgb(244, 245, 247)");
await check("fuente sans = IBM Plex Sans (declarada)", async () => (await page.evaluate(() => getComputedStyle(document.body).fontFamily)).includes("IBM Plex Sans"));
await page.screenshot({ path: resolve(shots, "01-light-flujo.png") });

await page.click('nav[aria-label=Vistas] a[href*="v=capex"]');
await check("navegación por nav → hash y título", async () => location_is(await page.evaluate(() => location.hash), "v=capex") && (await page.textContent("main h1")) === "CAPEX");

await page.click('button[aria-controls=mandos]');
await check("cajón Mandos abre", async () => (await page.$("aside#mandos")) !== null);
await page.waitForTimeout(400);
await page.screenshot({ path: resolve(shots, "02-light-mandos.png") });

await page.click('[role=radiogroup][aria-label=Tema] [aria-label="Tema oscuro"]');
await check("data-theme=dark aplicado", async () => (await page.getAttribute("html", "data-theme")) === "dark");
await check("body oscuro pinta #0F1216", async () => (await page.evaluate(() => getComputedStyle(document.body).backgroundColor)) === "rgb(15, 18, 22)");
await check("preferencia persistida", async () => (await page.evaluate(() => { try { return localStorage.getItem("fv-montecristi.theme"); } catch { return "n/a"; } })) === "dark" );
await page.waitForTimeout(400); // deja terminar transition-colors
await page.screenshot({ path: resolve(shots, "03-dark-mandos.png") });

await page.click('[role=radiogroup][aria-label=Tema] [aria-label="Tema del sistema"]');
await check("system quita data-theme", async () => (await page.getAttribute("html", "data-theme")) === null);

// ⌘K
await page.keyboard.press("Control+K");
await check("paleta ⌘K abre", async () => (await page.$("[cmdk-root]")) !== null);
await page.keyboard.type("Riesgos");
await page.keyboard.press("Enter");
await check("paleta navega a Riesgos", async () => /riesgos/i.test(await page.textContent("main h1")) && (await page.evaluate(() => location.hash)).includes("v=riesgos"));

// Oscuro por preferencia del sistema (sin data-theme)
const dark = await browser.newPage({ viewport: { width: 1280, height: 800 }, colorScheme: "dark" });
dark.on("pageerror", (e) => errors.push(String(e)));
await dark.goto(`${url}#v=resumen`);
await dark.waitForSelector("main h1");
await check("prefers-color-scheme: dark sin data-theme", async () => (await dark.evaluate(() => getComputedStyle(document.body).backgroundColor)) === "rgb(15, 18, 22)");
await dark.screenshot({ path: resolve(shots, "04-system-dark-resumen.png") });

// Ancho estrecho: tira de navegación, sin scroll horizontal del body
const narrow = await browser.newPage({ viewport: { width: 640, height: 900 }, colorScheme: "light" });
narrow.on("pageerror", (e) => errors.push(String(e)));
await narrow.goto(`${url}#v=supuestos`);
await narrow.waitForSelector("main h1");
await check("sin scroll horizontal en estrecho", async () => (await narrow.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)) === true);
await narrow.screenshot({ path: resolve(shots, "05-narrow-light.png") });

// Almacenamiento bloqueado: localStorage lanza → la app y el tema siguen funcionando
const blocked = await browser.newPage({ viewport: { width: 1280, height: 800 }, colorScheme: "light" });
blocked.on("pageerror", (e) => errors.push(String(e)));
await blocked.addInitScript(() => {
  Object.defineProperty(window, "localStorage", { get() { throw new Error("storage bloqueado"); } });
});
await blocked.goto(`${url}#v=resumen`);
await blocked.waitForSelector("main h1");
await blocked.click('[role=radiogroup][aria-label=Tema] [aria-label="Tema oscuro"]');
await check("localStorage lanza: renderiza y el tema cambia igual", async () => (await blocked.getAttribute("html", "data-theme")) === "dark");

// Fragmento dentro de un esqueleto tipo host (doctype/head/body + reset mínimo)
const fragmentPath = resolve(ROOT, "out", edition, "fragment.html");
const hostPath = resolve(shots, "fragment-host.html");
if (existsSync(fragmentPath)) {
  const fragment = readFileSync(fragmentPath, "utf8");
  writeFileSync(
    hostPath,
    `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>:root{color-scheme:light}body{margin:0;font:14px system-ui;background:#fafafa}img{max-width:100%}[hidden]{display:none!important}</style></head><body>\n${fragment}</body></html>`,
  );
  const host = await browser.newPage({ viewport: { width: 1280, height: 800 }, colorScheme: "light" });
  host.on("pageerror", (e) => errors.push(String(e)));
  await host.goto(`${pathToFileURL(hostPath).href}#v=guia`);
  await host.waitForSelector("main h1");
  await check("fragmento en esqueleto host: título del documento (por edición)", async () => (await host.title()) === (edition === "externo" ? "Proyecto FV Montecristi → GPM" : "Modelo FV Montecristi → GPM"));
  await check("fragmento en esqueleto host: vista renderizada", async () => /^Guía/.test(await host.textContent("main h1")));
  await check("fragmento en esqueleto host: body pinta var(--bg) sobre el reset del host", async () => (await host.evaluate(() => getComputedStyle(document.body).backgroundColor)) === "rgb(244, 245, 247)");
  await host.screenshot({ path: resolve(shots, "06-fragment-host-guia.png") });
}


// F1-01 / F1-04 (doc 25): ninguna vista muestra tokens de AST ni fórmulas crudas fuera de la columna «Fórmula del libro» de Controles,
// y ninguna desborda horizontalmente el <main> (1280 px).
const VIEWS = ["resumen","sensibilidad","supuestos","energia","capex","opex","fiscal","flujo","exergy","legal","tramites","riesgos","fuentes","controles","guia"];
const sweep = await browser.newPage({ viewport: { width: 1280, height: 800 }, colorScheme: "light" });
sweep.on("pageerror", (e) => errors.push(String(e)));
const leaks = [], overflows = [];
for (const v of VIEWS) {
  await sweep.goto(`${url}#v=${v}&c=custom`);
  await sweep.waitForSelector("main h1");
  await sweep.waitForTimeout(150);
  const r = await sweep.evaluate((view) => {
    const main = document.querySelector("main");
    const text = view === "controles" ? [...main.querySelectorAll("table tbody tr td:nth-child(-n+3)")].map((td) => td.innerText).join("\n") : main.innerText;
    const leak = /fbin&|callTEXT|\bstr#|\bname[A-Z][A-Za-z_]+str|\[object Object\]/.test(text);
    return { leak, over: main.scrollWidth - main.clientWidth };
  }, v);
  if (r.leak) leaks.push(v);
  if (r.over > 0) overflows.push(`${v}:${r.over}px`);
}
await check("sin AST ni fórmulas crudas en el DOM de las 15 vistas (F1-01)", async () => { if (leaks.length) console.log("    vistas con fuga:", leaks); return leaks.length === 0; });
await check("sin desborde horizontal de <main> en las 15 vistas (F1-04)", async () => { if (overflows.length) console.log("    desbordes:", overflows); return overflows.length === 0; });

await check("sin errores de consola/página", async () => {
  const relevant = errors.filter((e) => !/fonts\.g(oogleapis|static)\.com|net::ERR|Failed to load resource/i.test(e));
  if (relevant.length) console.log("    errores:", relevant);
  return relevant.length === 0;
});

await browser.close();
console.log(`capturas → ${shots}`);

function location_is(hash, needle) { return hash.includes(needle); }
