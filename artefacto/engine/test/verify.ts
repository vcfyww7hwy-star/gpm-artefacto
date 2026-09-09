/**
 * verify.ts — compares the TypeScript engine against the LibreOffice-recalculated oracle
 * (../data/motor.json) and the defined names of the workbook (../data/names.json).
 *
 *   npx tsx test/verify.ts
 *
 * Sections: (a) derived globals · (b) case parameters · (c) scalars · (d) outputs · (e) blocks.
 * Acceptance: |got − exp| ≤ 1e-6  OR  |got − exp| / |exp| ≤ 1e-9 ; "n/a" ⇄ non-numeric.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import {
  computeDerived, computeCase, PARAM_LABELS, PARAM_KEYS, BLOCK_NAMES, T_AXIS, edate, parseISODate, formatISODate,
  type Inputs, type Derived, type CaseParams, type OutputValue, irrNewtonRaw } from "../src/engine";
import { buildCases } from "../src/caseDefinitions";
import { inputsFromWorkbookJson, type NamesJson, type SheetsJson } from "../src/inputs";

const here = path.dirname(fileURLToPath(import.meta.url));
const ENGINE = path.resolve(here, "..");
const DATA = process.env.DATA_DIR ? path.resolve(process.env.DATA_DIR) : path.resolve(ENGINE, "..", "data");   // DATA_DIR: cruce aleatorio (crosscheck_engine.py)

const ABS_TOL = 1e-6, REL_TOL = 1e-9;

interface Offender { where: string; expected: unknown; got: unknown; absDiff: number; relDiff: number }
class Section {
  n = 0; nFail = 0; maxAbs = 0; maxRel = 0; offenders: Offender[] = [];
  constructor(public name: string) {}
  cmp(where: string, expected: unknown, got: unknown): void {
    this.n++;
    const eNum = typeof expected === "number" && Number.isFinite(expected);
    const gNum = typeof got === "number" && Number.isFinite(got);
    let absDiff: number, relDiff: number, ok: boolean;
    if (eNum && gNum) {
      absDiff = Math.abs((got as number) - (expected as number));
      relDiff = expected === 0 ? (absDiff === 0 ? 0 : Infinity) : absDiff / Math.abs(expected as number);
      ok = absDiff <= ABS_TOL || relDiff <= REL_TOL;
      if (absDiff > this.maxAbs) this.maxAbs = absDiff;
      if (Number.isFinite(relDiff) && relDiff > this.maxRel) this.maxRel = relDiff;
    } else if (!eNum && !gNum) {
      // both non-numeric: "n/a" ⇄ null/"n/a"/"no cruza" ; null ⇄ null (empty DSCR)
      const e = expected === null || expected === undefined ? null : String(expected);
      const g = got === null || got === undefined ? null : String(got);
      ok = e === g || (e === "n/a" && g !== null) || (g === "n/a" && e !== null);
      absDiff = ok ? 0 : Infinity; relDiff = absDiff;
    } else {
      ok = false; absDiff = Infinity; relDiff = Infinity;
    }
    if (!ok) {
      this.nFail++;
      this.offenders.push({ where, expected, got, absDiff, relDiff });
    } else if (eNum && gNum) {
      // keep the worst passing cells too, for the "worst 5" list
      this.offenders.push({ where, expected, got, absDiff, relDiff });
    }
  }
  worst(k = 5): Offender[] {
    const score = (o: Offender) => (o.absDiff === Infinity ? Infinity : Math.min(o.relDiff, o.absDiff / ABS_TOL * REL_TOL) );
    return [...this.offenders].sort((a, b) => score(b) - score(a)).slice(0, k);
  }
  summary() {
    return { section: this.name, compared: this.n, failed: this.nFail, maxAbsDiff: this.maxAbs, maxRelDiff: this.maxRel, worst5: this.worst(5) };
  }
}

function fmt(v: unknown): string {
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toPrecision(15);
  return JSON.stringify(v);
}
function printSection(s: Section): void {
  const sm = s.summary();
  console.log(`\n=== ${sm.section} ===`);
  console.log(`  cells compared: ${sm.compared}   failed: ${sm.failed}   max |Δ|: ${sm.maxAbsDiff.toExponential(3)}   max rel Δ: ${sm.maxRelDiff.toExponential(3)}`);
  console.log(`  worst 5:`);
  for (const o of sm.worst5) {
    console.log(`    ${o.where.padEnd(64)} exp=${fmt(o.expected).padStart(22)}  got=${fmt(o.got).padStart(22)}  |Δ|=${o.absDiff.toExponential(2)}  rel=${Number.isFinite(o.relDiff) ? o.relDiff.toExponential(2) : "inf"}`);
  }
}

// ------------------------------------------------------------------------------------------------
const names = JSON.parse(fs.readFileSync(path.join(DATA, "names.json"), "utf8")) as NamesJson;
const sheets = JSON.parse(fs.readFileSync(path.join(DATA, "sheets.json"), "utf8")) as SheetsJson;
const motor = JSON.parse(fs.readFileSync(path.join(DATA, "motor.json"), "utf8")) as {
  labels: { params: string[]; scalars: string[]; outputs: string[]; blocks: string[] };
  t: number[];
  cases: { name: string; col: string; params: Record<string, number>; scalars: Record<string, number>; outputs: Record<string, number | string>; blocks: Record<string, (number | null)[]> }[];
};

const inputs: Inputs = inputsFromWorkbookJson(names, sheets);
const derived: Derived = computeDerived(inputs);

// write the defaults next to the engine (only for the delivered workbook, never for a randomized cross-check set)
if (!process.env.DATA_DIR) {
  fs.mkdirSync(path.join(ENGINE, "data"), { recursive: true });
  fs.writeFileSync(path.join(ENGINE, "data", "inputs_v31.json"), JSON.stringify(inputs, null, 1) + "\n");
}

const nv = (n: string): unknown => { const e = names[n]; return e ? (e.value !== undefined ? e.value : e.values) : undefined; };
const flat = (v: unknown): unknown[] => (Array.isArray(v) ? (v as unknown[]).flatMap((r) => (Array.isArray(r) ? r : [r])) : [v]);

// ---- (a) derived globals vs names.json -----------------------------------------------------------
const secA = new Section("(a) derived globals vs names.json");
const scalarNames: [string, number][] = [
  ["Consumo_Anual", derived.Consumo_Anual], ["Tarifa_Evitable", derived.Tarifa_Evitable], ["Loss_Ref", derived.Loss_Ref], ["Loss_Act", derived.Loss_Act],
  ["F_Recorte", derived.F_Recorte], ["Anios_Precios", derived.Anios_Precios], ["Tasa_Efectiva", derived.Tasa_Efectiva], ["Potencia_AC", derived.Potencia_AC],
  ["Hectareas", derived.Hectareas], ["Yield_Ref", derived.Yield_Ref], ["Eff_Scen", derived.Eff_Scen], ["Eff_fO", derived.Eff_fO], ["Eff_Peaje", derived.Eff_Peaje],
  ["Eff_EscT", derived.Eff_EscT], ["Escala_Wp", derived.Escala_Wp], ["Escala_Wac", derived.Escala_Wac], ["Factor_Nivel_2026", derived.Factor_Nivel_2026],
  ["Ahorro_Mensual_Anio1", derived.Ahorro_Mensual_Anio1],
  ["CAPEX_SC_Wp", derived.CAPEX_SC_Wp], ["CAPEX_SC_Wac", derived.CAPEX_SC_Wac], ["CAPEX_SC_Fijo", derived.CAPEX_SC_Fijo],
  ["CAPEX_CC_Wp", derived.CAPEX_CC_Wp], ["CAPEX_CC_Wac", derived.CAPEX_CC_Wac], ["CAPEX_CC_Fijo", derived.CAPEX_CC_Fijo],
  ["IVA_SC_Wp", derived.IVA_SC_Wp], ["IVA_SC_Wac", derived.IVA_SC_Wac], ["IVA_SC_Fijo", derived.IVA_SC_Fijo],
  ["IVA_CC_Wp", derived.IVA_CC_Wp], ["IVA_CC_Wac", derived.IVA_CC_Wac], ["IVA_CC_Fijo", derived.IVA_CC_Fijo],
  ["CAPEX_SC_f1", derived.CAPEX_SC_f1], ["CAPEX_CC_f1", derived.CAPEX_CC_f1], ["IVA_SC_f1", derived.IVA_SC_f1], ["IVA_CC_f1", derived.IVA_CC_f1],
  ["CAPEX_Base_f1", derived.CAPEX_Base_f1], ["Factor_Escalacion", derived.Factor_Escalacion], ["Factor_Caso", derived.Factor_Caso],
  ["Pct_CAPEX_Civil", derived.Pct_CAPEX_Civil], ["Reemplazo_USD", derived.Reemplazo_USD], ["Desmantelamiento_USD", derived.Desmantelamiento_USD],
  ["CAPEX_Total", derived.CAPEX_Base_f1 * derived.Factor_Caso], ["IVA_Total", (inputs.Contrato_Inversion === "Sí"
    ? derived.Escala_Wp * derived.IVA_CC_Wp + derived.Escala_Wac * derived.IVA_CC_Wac + derived.IVA_CC_Fijo
    : derived.Escala_Wp * derived.IVA_SC_Wp + derived.Escala_Wac * derived.IVA_SC_Wac + derived.IVA_SC_Fijo) * derived.Factor_Caso],
];
for (const [n, got] of scalarNames) secA.cmp(n, nv(n), got);
const fpX = flat(nv("Frac_Peaje"));
T_AXIS.forEach((t, k) => secA.cmp(`Frac_Peaje[t=${t}]`, fpX[k], derived.Frac_Peaje[k]));
for (let m = 0; m < 12; m++) secA.cmp(`04!K${17 + m} Consumo_Mensual[${m}]`, sheets["04_Energia"].cells[`K${17 + m}`]?.v, derived.Consumo_Mensual[m]);
const cf = (nv("Fin_Operacion") as string | undefined);
if (cf) {
  // Fin_Operacion = EDATE(Fecha_COD, 12*Horizonte) — check the EDATE helper on a real cell
  const got = formatISODate(edate(parseISODate(inputs.Fecha_COD), 12 * inputs.Horizonte));
  secA.cmp("Fin_Operacion (EDATE)", String(cf).slice(0, 10), got);
}

// ---- (b) case parameters vs motor.json ----------------------------------------------------------
const secB = new Section("(b) case parameters vs motor.json");
const cases = buildCases(inputs, derived);
if (cases.length !== motor.cases.length) throw new Error(`número de casos: motor ${motor.cases.length} vs engine ${cases.length}`);
const INT_KEYS = new Set<keyof CaseParams>(["scen", "part", "iva", "cont", "deb", "plazo", "gr", "terr", "finT", "rep", "ncon", "dedad"]);
cases.forEach((c, j) => {
  const mc = motor.cases[j];
  if (c.name !== mc.name) secB.cmp(`case[${j}].name`, mc.name, c.name);
  for (const k of PARAM_KEYS) {
    const exp = mc.params[PARAM_LABELS[k]];
    const got = c.params[k];
    if (INT_KEYS.has(k)) { secB.n++; if (exp !== got) { secB.nFail++; secB.offenders.push({ where: `${mc.name} · ${k}`, expected: exp, got, absDiff: Infinity, relDiff: Infinity }); } }
    else {
      // numbers to 1e-12 (stricter than the generic tolerance)
      secB.n++;
      const ad = Math.abs(exp - got);
      const rd = exp === 0 ? (ad === 0 ? 0 : Infinity) : ad / Math.abs(exp);
      if (ad > secB.maxAbs) secB.maxAbs = ad;
      if (Number.isFinite(rd) && rd > secB.maxRel) secB.maxRel = rd;
      const ok = ad <= 1e-12 || rd <= 1e-12;
      if (!ok) secB.nFail++;
      secB.offenders.push({ where: `${mc.name} · ${k}`, expected: exp, got, absDiff: ok ? ad : Infinity, relDiff: ok ? rd : Infinity });
    }
  }
});

// ---- (c)(d)(e) scalars, outputs, blocks --------------------------------------------------------
const secC = new Section("(c) scalars (22 × 111)");
const secD = new Section("(d) outputs (16 × 111)");
const secE = new Section("(e) blocks (28 × 27 × 111)");
const perBlock = new Map<string, { maxAbs: number; maxRel: number; n: number }>();
for (const b of BLOCK_NAMES) perBlock.set(b, { maxAbs: 0, maxRel: 0, n: 0 });
const perOutput = new Map<string, { maxAbs: number; maxRel: number }>();
const explainedIrr: string[] = [];

cases.forEach((c, j) => {
  const mc = motor.cases[j];
  // use the ORACLE params (already verified in (b)) so that a param mismatch does not cascade
  const p: CaseParams = { ...c.params };
  for (const k of PARAM_KEYS) p[k] = mc.params[PARAM_LABELS[k]];
  const res = computeCase(inputs, derived, p);
  for (const lab of motor.labels.scalars) secC.cmp(`${mc.name} · ${lab}`, mc.scalars[lab], (res.scalars as Record<string, number>)[lab]);
  for (const lab of motor.labels.outputs) {
    const exp = mc.outputs[lab], got = (res.outputs as Record<string, OutputValue>)[lab];
    // D-V2-9: el oráculo LibreOffice muestra «n/a» (guardia R3-5) cuando su Newton converge a una raíz espuria (≤ −100 %) o
    // no converge; Excel y el motor devuelven la raíz real en dominio. Se acepta como divergencia EXPLICADA si la fase 1
    // (Newton puro) sobre la misma serie efectivamente sale del dominio o no converge.
    const series = lab === "TIR equity" ? res.blocks.EQ : lab === "TIR proyecto" ? res.blocks.FCF_u : lab === "TIR grupo" ? res.blocks.Gx : null;
    if (series && (exp === "n/a" || (typeof exp === "number" && exp <= -1)) && typeof got === "number" && Number.isFinite(got) && got > -1) {   // r3: «n/a» (R3-5) · r2: la raíz espuria tal cual
      const raw = irrNewtonRaw(series as number[], lab === "TIR equity" ? 0.02 : 0.1);
      if (raw === null || raw <= -1) { explainedIrr.push(`${mc.name} · ${lab}: LibreOffice ${raw === null ? "no converge" : (raw * 100).toFixed(2) + " % (espuria)"} → libro ${exp === "n/a" ? "n/a" : (exp as number * 100).toFixed(2) + " %"} · motor/Excel ${(got * 100).toFixed(4)} %`); secD.n++; continue; }
    }
    secD.cmp(`${mc.name} · ${lab}`, exp, got);
    if (typeof exp === "number" && typeof got === "number") {
      const cur = perOutput.get(lab) ?? { maxAbs: 0, maxRel: 0 };
      const ad = Math.abs(got - exp); const rd = exp === 0 ? 0 : ad / Math.abs(exp);
      perOutput.set(lab, { maxAbs: Math.max(cur.maxAbs, ad), maxRel: Math.max(cur.maxRel, rd) });
    }
  }
  for (const b of motor.labels.blocks) {
    const expArr = mc.blocks[b], gotArr = res.blocks[b as keyof typeof res.blocks];
    const pb = perBlock.get(b)!;
    T_AXIS.forEach((t, k) => {
      const exp = expArr[k], got = gotArr[k];
      secE.cmp(`${mc.name} · ${b} · t=${t}`, exp, got);
      pb.n++;
      if (typeof exp === "number" && typeof got === "number") {
        const ad = Math.abs(got - exp); const rd = exp === 0 ? 0 : ad / Math.abs(exp);
        if (ad > pb.maxAbs) pb.maxAbs = ad; if (rd > pb.maxRel) pb.maxRel = rd;
      }
    });
  }
});

// ---- report ------------------------------------------------------------------------------------
const sections = [secA, secB, secC, secD, secE];
for (const s of sections) printSection(s);
console.log("\n--- per block (max |Δ| · max rel Δ) ---");
for (const [b, v] of perBlock) console.log(`  ${b.padEnd(8)} n=${v.n}  |Δ|=${v.maxAbs.toExponential(2)}  rel=${v.maxRel.toExponential(2)}`);
console.log("--- per output ---");
for (const [o, v] of perOutput) console.log(`  ${o.padEnd(32)} |Δ|=${v.maxAbs.toExponential(2)}  rel=${v.maxRel.toExponential(2)}`);

const totalFail = sections.reduce((s, x) => s + x.nFail, 0);
const totalN = sections.reduce((s, x) => s + x.n, 0);
const status = totalFail === 0 ? "PASS" : "FAIL";
if (explainedIrr.length) { console.log(`\n--- TIR: ${explainedIrr.length} divergencia(s) explicada(s) por D-V2-9 (oráculo LibreOffice) ---`); for (const e of explainedIrr) console.log("  " + e); }
console.log(`\n==== ${status}: ${totalN} cells compared, ${totalFail} outside tolerance (abs 1e-6 | rel 1e-9; params 1e-12)${explainedIrr.length ? ` · ${explainedIrr.length} TIR explicadas (D-V2-9)` : ""} ====`);

const report = {
  status, totalCompared: totalN, totalFailed: totalFail, tolerance: { abs: ABS_TOL, rel: REL_TOL, params: 1e-12 },
  oracle: "../data/motor.json (v3.1, LibreOffice recalculation)", nCases: cases.length,
  sections: sections.map((s) => s.summary()),
  perBlock: Object.fromEntries(perBlock), perOutput: Object.fromEntries(perOutput),
  generated: new Date().toISOString(),
};
fs.writeFileSync(process.env.DATA_DIR ? path.join(DATA, "verify_report.json") : path.join(ENGINE, "verify_report.json"), JSON.stringify(report, (_k, v) => (v === Infinity ? "Infinity" : v), 1) + "\n");
process.exit(totalFail === 0 ? 0 : 1);
