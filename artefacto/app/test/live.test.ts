/**
 * Pruebas de los textos vivos y de los módulos 05/06 contra el libro v3.1 recalculado. Ejecutar: `npx tsx test/live.test.ts`
 *  (a) resolutor: cada nombre usado por los textos vivos → mismo valor que names.json (LibreOffice), salvo los congelados;
 *  (b) textos: cada fórmula de texto evaluada en en-US ≡ valor de la celda del libro que la contiene (sheets.json);
 *  (c) capexTable(Custom) ≡ 05_CAPEX N7:N19 / P7:P19; capexTable(caso).total ≡ Motor K/IVA para los 111 casos;
 *  (d) opexLines Σ ≡ bloque OPEX del Motor para los 111 casos.
 */
import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

import { computeAll, SCALAR_LABELS, T_AXIS, type Inputs } from "../src/engine";
import { capexTable } from "../src/model/capex";
import { evalNode, renderLive, type Live, type Node, type Value } from "../src/model/formula";
import { THIN_SPACE } from "../src/lib/format";
import { createResolver } from "../src/model/names";
import { opexLines } from "../src/model/opex";

const here = path.dirname(fileURLToPath(import.meta.url));
const DATA = process.env.DATA_DIR ? path.resolve(process.env.DATA_DIR) : path.resolve(here, "..", "..", "data");   // DATA_DIR: datos de otra revisión (p. ej. r3-pre)
const book = JSON.parse(fs.readFileSync(path.join(DATA, "book.json"), "utf8"));
const sheets = JSON.parse(fs.readFileSync(path.join(DATA, "sheets.json"), "utf8")) as Record<string, { cells: Record<string, { v?: unknown; f?: string }> }>;
const inputs = JSON.parse(fs.readFileSync(path.resolve(here, "..", "src", "model", "inputs_v31.json"), "utf8")) as Inputs;

const model = computeAll(inputs);
const { ctx, frozenUsed } = createResolver({ inputs, derived: model.derived, cases: model.cases }, book, "en-US");

const close = (a: number, b: number) => Math.abs(a - b) <= 1e-6 || Math.abs(a - b) / Math.max(1e-12, Math.abs(b)) <= 1e-9;
const flat = (v: unknown): unknown[] => (Array.isArray(v) ? v.flatMap(flat) : [v]);

// ---- (a) resolutor
let nOk = 0, nFrozen = 0; const bad: string[] = [];
for (const name of book.live_names as string[]) {
  if (name.includes("!")) continue; // referencias: se prueban vía los textos
  let got: Value;
  try { got = ctx.name(name); } catch (e) { bad.push(`${name}: ${(e as Error).message}`); continue; }
  const exp = book.calc_names[name];
  if (frozenUsed.has(name)) { nFrozen++; continue; }
  const g = flat(got), x = flat(exp);
  if (g.length !== x.length) { bad.push(`${name}: longitud ${g.length} ≠ ${x.length}`); continue; }
  let ok = true;
  for (let k = 0; k < g.length; k++) {
    const a = g[k], b = x[k];
    if (typeof a === "number" && typeof b === "number") { if (!close(a, b)) ok = false; }
    else if ((a === null || a === "") && (b === null || b === "")) { /* vacío */ }
    else if (String(a) !== String(b)) ok = false;
  }
  if (ok) nOk++; else bad.push(`${name}: ${JSON.stringify(got).slice(0, 80)} ≠ ${JSON.stringify(exp).slice(0, 80)}`);
}
console.log(`(a) nombres vivos: ${nOk} iguales · ${nFrozen} congelados del libro [${[...frozenUsed].join(", ")}] · ${bad.length} distintos`);
bad.forEach((b) => console.log("   ✗", b));

// ---- (b) textos: fórmula original → celda del libro con esa fórmula → valor esperado
const byFormula = new Map<string, unknown>();
for (const sh of Object.values(sheets)) for (const c of Object.values(sh.cells)) if (c.f) byFormula.set(c.f, c.v);
let tOk = 0, tMiss = 0; const tBad: string[] = [];
const walkLive = (o: unknown, where: string) => {
  if (Array.isArray(o) && o[0] === "f" && typeof o[2] === "string") {
    const got = renderLive(o as Live, ctx);
    const exp = byFormula.get(o[2]);
    if (exp === undefined) { tMiss++; return; }
    const e = typeof exp === "number" ? String(exp) : String(exp ?? "");
    if (got === e) tOk++; else tBad.push(`${where}\n      got «${got}»\n      exp «${e}»`);
    return;
  }
  if (Array.isArray(o)) { if (o[0] === "tpl" || o[0] === "f") return; o.forEach((x, k) => walkLive(x, `${where}[${k}]`)); }
  else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) if (!["calc_names", "frozen", "frozen_formulas", "sheets", "controles"].includes(k)) walkLive(v, `${where}.${k}`);
};
walkLive(book, "book");
console.log(`(b) textos-fórmula: ${tOk} idénticos al libro · ${tMiss} sin celda de referencia · ${tBad.length} distintos`);
tBad.forEach((b) => console.log("   ✗", b));
// plantillas con llaves: sólo se comprueba que evalúan sin error de Excel
let pOk = 0; const pBad: string[] = [];
const walkTpl = (o: unknown, where: string) => {
  if (Array.isArray(o) && o[0] === "tpl") {
    const s = renderLive(o as Live, ctx);
    if (/#(NAME\?|REF!|VALUE!|DIV\/0!|N\/A)/.test(s)) pBad.push(`${where}: ${s.slice(0, 120)}`); else pOk++;
    return;
  }
  if (Array.isArray(o)) { if (o[0] === "f") return; o.forEach((x, k) => walkTpl(x, `${where}[${k}]`)); }
  else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) if (!["calc_names", "frozen", "frozen_formulas", "sheets"].includes(k)) walkTpl(v, `${where}.${k}`);
};
walkTpl(book, "book");
console.log(`(b') plantillas: ${pOk} evalúan · ${pBad.length} con error`);
pBad.forEach((b) => console.log("   ✗", b));

// ---- (c) capexTable
const c05 = sheets["05_CAPEX"].cells;
const X = model.cases[0];
const tab = capexTable(inputs, model.derived, X.params);
let cOk = 0; const cBad: string[] = [];
tab.rubros.forEach((r, k) => {
  const row = 7 + k;
  for (const [col, val] of [["N", r.capitalizable], ["P", r.iva], ["F", r.costo], ["Q", r.usdWp], ["M", r.arancelIsd]] as const) {
    const exp = c05[`${col}${row}`]?.v as number;
    if (close(val, exp)) cOk++; else cBad.push(`${col}${row}: ${val} ≠ ${exp}`);
  }
});
for (const [ref, val] of [["N16", tab.contingencia.capitalizable], ["N17", tab.subtotal.capitalizable], ["N18", tab.gerencia.capitalizable], ["N19", tab.total.capitalizable], ["P19", tab.total.iva], ["N20", tab.total_con_iva], ["N21", tab.terreno], ["N22", tab.total_con_terreno], ["N23", tab.aranceles_isd], ["P23", tab.fodinfa], ["N24", tab.pct_civil], ["D30", tab.factor_caso]] as const) {
  const exp = c05[ref]?.v as number;
  if (close(val, exp)) cOk++; else cBad.push(`${ref}: ${val} ≠ ${exp}`);
}
let cCases = 0; const cCaseBad: string[] = [];
for (const c of model.cases) {
  const t = capexTable(inputs, model.derived, c.params);
  const K = c.result.scalars[SCALAR_LABELS.K], IVA = c.result.scalars[SCALAR_LABELS.IVA], Terr = c.result.scalars[SCALAR_LABELS.Terr];
  if (close(t.total.capitalizable, K) && close(t.total.iva, IVA) && (c.params.terr !== 1 || close(t.terreno, Terr))) cCases++;
  else cCaseBad.push(`${c.name}: K ${t.total.capitalizable} vs ${K} · IVA ${t.total.iva} vs ${IVA} · terr ${t.terreno} vs ${Terr}`);
}
console.log(`(c) capexTable Custom: ${cOk} celdas iguales · ${cBad.length} distintas; casos con K/IVA/terreno ≡ Motor: ${cCases}/${model.cases.length}`);
cBad.forEach((b) => console.log("   ✗", b)); cCaseBad.slice(0, 5).forEach((b) => console.log("   ✗", b));

// ---- (d) opexLines
let oCases = 0; const oBad: string[] = [];
for (const c of model.cases) {
  let ok = true;
  T_AXIS.forEach((t, k) => { const l = opexLines(inputs, model.derived, c.params, t); const e = c.result.blocks.OPEX[k] ?? 0; if (!close(l.total, e as number)) ok = false; });
  if (ok) oCases++; else oBad.push(c.name);
}
console.log(`(d) opexLines Σ ≡ Motor OPEX: ${oCases}/${model.cases.length} casos` + (oBad.length ? ` · distintos: ${oBad.slice(0, 5).join(", ")}` : ""));
// 06 hoja: líneas del año 1 del Custom
const c06 = sheets["06_OPEX"].cells;
const l1 = opexLines(inputs, model.derived, X.params, 1);
for (const [ref, val] of [["D7", l1.fee], ["D8", l1.seguros], ["D9", l1.arriendo], ["D10", l1.predial], ["D11", l1.tributos], ["D12", l1.total]] as const) {
  assert.ok(close(val, c06[ref]?.v as number), `06!${ref}: ${val} ≠ ${String(c06[ref]?.v)}`);
}
console.log("(d') 06_OPEX año 1 del Custom: 6 celdas iguales");

// ---- sanity del evaluador
const t1: Node = ["call", "TEXT", [["num", 0.1064], ["str", "0.00%"]]];
assert.equal(evalNode(t1, { ...ctx, locale: "en-US" }), "10.64%");
assert.equal(evalNode(t1, { ...ctx, locale: "es-EC" }), `10,64${THIN_SPACE}%`);
assert.equal(evalNode(["call", "TEXT", [["num", -1234.5], ["str", "+#,##0;-#,##0"]]], { ...ctx, locale: "en-US" }), "-1,235");
assert.equal(evalNode(["call", "TEXT", [["num", 0.0123], ["str", "+0.0;-0.0"]]], { ...ctx, locale: "en-US" }), "+0.0");
assert.equal(evalNode(["call", "TEXT", [["str", "2028-07-01"], ["str", "mmm-yyyy"]]], { ...ctx, locale: "en-US" }), "Jul-2028");
assert.equal(evalNode(["call", "TEXT", [["str", "2028-07-01"], ["str", "dd-mmm-yyyy"]]], { ...ctx, locale: "es-EC" }), "01-jul-2028");

const fail = bad.length + tBad.length + pBad.length + cBad.length + cCaseBad.length + oBad.length;
console.log(fail === 0 ? "\nPASS" : `\nFAIL (${fail})`);
process.exit(fail === 0 ? 0 : 1);
