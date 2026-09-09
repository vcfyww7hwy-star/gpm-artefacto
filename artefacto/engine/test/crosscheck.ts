/**
 * crosscheck.ts — compares computeCase against shadow30.run_case (Python) on the randomized
 * parameter sets written by test/crosscheck_shadow.py. These sets exercise branches the 111 Motor
 * columns never reach (loss pool with ug ≥ 0, plazo ≤ gracia, rd = 0, kfix + contract, Exergy land,
 * ratio outside the clipping curve, rep = 2 …).
 *
 *   python3 test/crosscheck_shadow.py 400 31 && npx tsx test/crosscheck.ts
 *
 * Known, intentional differences vs shadow30 (Excel semantics win, see README):
 *   · Payback: shadow30 → None when the last cumulative is negative / never negative; Motor → "no cruza" / −1.
 *   · TIR: shadow30 uses plain bisection on [−0.99, 1] (may pick another root when several exist);
 *          the engine uses Newton from the Excel seed (0.1 / 0.02). Both are reported; a difference is
 *          accepted when the engine's value is a genuine root (relative NPV residual ≤ 1e-9).
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { computeDerived, computeCase, BLOCK_NAMES, SCALAR_LABELS, OUTPUT_LABELS, IRR_FALLBACK_WINDOW, type CaseParams, type OutputValue } from "../src/engine";
import { inputsFromWorkbookJson, type NamesJson, type SheetsJson } from "../src/inputs";

const here = path.dirname(fileURLToPath(import.meta.url));
const ENGINE = path.resolve(here, "..");
const DATA = path.resolve(ENGINE, "..", "data");
const names = JSON.parse(fs.readFileSync(path.join(DATA, "names.json"), "utf8")) as NamesJson;
const sheets = JSON.parse(fs.readFileSync(path.join(DATA, "sheets.json"), "utf8")) as SheetsJson;
const cc = JSON.parse(fs.readFileSync(path.join(here, "crosscheck_cases.json"), "utf8")) as {
  seed: number; n: number;
  cases: { pc: CaseParams; out: Record<string, number | null>; blocks: Record<string, (number | null)[]> }[];
};
const inputs = inputsFromWorkbookJson(names, sheets);
const derived = computeDerived(inputs);

// shadow30 keys → Motor labels
const OUT_MAP: Record<string, string> = {
  TIR: OUTPUT_LABELS.TIR, VAN: OUTPUT_LABELS.VAN, PB: OUTPUT_LABELS.PB, LCOE: OUTPUT_LABELS.LCOE, TIR_eq: OUTPUT_LABELS.TIR_eq, VAN_eq: OUTPUT_LABELS.VAN_eq,
  DSCR_min: OUTPUT_LABELS.DSCR_min, DSCR_avg: OUTPUT_LABELS.DSCR_avg, Ahorro1: OUTPUT_LABELS.Ahorro1, Aporte_eq: OUTPUT_LABELS.Aporte_eq, VAN_X: OUTPUT_LABELS.VAN_X,
  TIR_G: OUTPUT_LABELS.TIR_G, E1: OUTPUT_LABELS.E1, NoRec: OUTPUT_LABELS.NoRec, Cob: OUTPUT_LABELS.Cob, Nominal_X: OUTPUT_LABELS.Nominal_X,
};
const SCAL_MAP: Record<string, string> = Object.fromEntries(Object.entries(SCALAR_LABELS));

/** scale-free NPV residual at r: |Σ cf_i/(1+r)^i| / Σ |cf_i|/(1+r)^i */
const relResidual = (cfs: (number | null)[], r: number): number => { let s = 0, a = 0; cfs.forEach((v, i) => { const x = (v ?? 0) / Math.pow(1 + r, i); s += x; a += Math.abs(x); }); return a > 0 ? Math.abs(s) / a : 0; };

let n = 0, nFail = 0, maxRel = 0, maxAbs = 0;
const fails: string[] = [];
const notes: string[] = [];
const close = (exp: number, got: number) => Math.abs(exp - got) / Math.max(1, Math.abs(exp)) <= 1e-9;
const ok = (exp: number, got: number) => { const ad = Math.abs(exp - got); const rd = ad / Math.max(1, Math.abs(exp)); maxAbs = Math.max(maxAbs, ad); maxRel = Math.max(maxRel, rd); return rd <= 1e-9; };

cc.cases.forEach((c, j) => {
  const res = computeCase(inputs, derived, c.pc);
  const tag = `#${j}`;
  // scalars
  for (const [k, lab] of Object.entries(SCAL_MAP)) {
    const exp = c.out[k]; const got = (res.scalars as Record<string, number>)[lab];
    if (typeof exp === "number") { n++; if (!ok(exp, got)) { nFail++; fails.push(`${tag} scalar ${k}: exp ${exp} got ${got}`); } }
  }
  // outputs
  for (const [k, lab] of Object.entries(OUT_MAP)) {
    const exp = c.out[k]; const got = (res.outputs as Record<string, OutputValue>)[lab];
    n++;
    if (k === "PB") {
      if (exp === null) { if (typeof got === "number" && got !== -1) { nFail++; fails.push(`${tag} PB: shadow None, engine ${got}`); } else notes.push(`${tag} PB: shadow None ↔ engine ${JSON.stringify(got)} (Excel semantics)`); }
      else if (typeof got !== "number" || !ok(exp, got)) { nFail++; fails.push(`${tag} PB: exp ${exp} got ${got}`); }
      continue;
    }
    if (k === "TIR" || k === "TIR_eq" || k === "TIR_G") {
      const cfs = k === "TIR" ? res.blocks.FCF_u : k === "TIR_eq" ? res.blocks.EQ : res.blocks.Gx;
      if (exp === null && got === "n/a") continue;
      if (typeof got === "number" && typeof exp === "number" && close(exp, got)) { ok(exp, got); continue; }
      // accept a different root if the engine's value is a genuine root of the same flow
      if (typeof got === "number" && relResidual(cfs, got) <= 1e-9) { notes.push(`${tag} ${k}: shadow(bisection) ${exp} ↔ engine(Newton from seed) ${got} — both roots`); continue; }
      if (got === "n/a" && typeof exp === "number") {
        // Newton from the Excel seed diverged; a root exists only outside IRR_FALLBACK_WINDOW → Excel shows "n/a" as well
        if (exp < IRR_FALLBACK_WINDOW[0] || exp > IRR_FALLBACK_WINDOW[1]) { notes.push(`${tag} ${k}: shadow root ${exp} outside fallback window ↔ engine n/a (Excel #NUM!)`); continue; }
        nFail++; fails.push(`${tag} ${k}: engine n/a but shadow found ${exp} inside the fallback window`); continue;
      }
      nFail++; fails.push(`${tag} ${k}: exp ${exp} got ${got}`);
      continue;
    }
    if (exp === null) { if (got !== "n/a") { nFail++; fails.push(`${tag} ${k}: shadow None, engine ${got}`); } continue; }
    if (typeof got !== "number" || !ok(exp, got)) { nFail++; fails.push(`${tag} ${k}: exp ${exp} got ${got}`); }
  }
  // blocks
  for (const b of BLOCK_NAMES) {
    const expArr = c.blocks[b]; const gotArr = res.blocks[b];
    for (let k = 0; k < 27; k++) {
      const exp = expArr[k], got = gotArr[k];
      n++;
      if (exp === null && got === null) continue;
      if (exp === null || got === null) { nFail++; fails.push(`${tag} ${b}[${k - 1}]: exp ${exp} got ${got}`); continue; }
      if (!ok(exp, got)) { nFail++; fails.push(`${tag} ${b}[t=${k - 1}]: exp ${exp} got ${got}`); }
    }
  }
});

console.log(`crosscheck vs shadow30.run_case: ${cc.n} random cases (seed ${cc.seed}) · ${n} cells · ${nFail} fail · max |Δ| ${maxAbs.toExponential(2)} · max relΔ(max(1,|x|)) ${maxRel.toExponential(2)}`);
for (const f of fails.slice(0, 25)) console.log("  ■", f);
if (notes.length) { console.log(`  ${notes.length} accepted semantic notes (first 12):`); for (const s of notes.slice(0, 12)) console.log("   ·", s); }
process.exit(nFail === 0 ? 0 : 1);
