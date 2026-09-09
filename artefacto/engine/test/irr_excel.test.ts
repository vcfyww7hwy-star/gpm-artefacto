/**
 * irr_excel.test.ts — D-V2-9 (09-sep-2026): el motor replica el contrato observado de Excel/Mac 16.110 (prueba A2/A2b,
 * libro temporal `_borrador_v3.1/pruebas/IRR_prueba_Excel_2026-09-09*.xlsx`). Oráculo = valores leídos de Excel por AppleScript.
 * Además: invariante VAN(TIR) ≈ 0 en los 111 casos de la línea base (TIR proyecto, equity, grupo) cuando la TIR es finita.
 * Uso: npx tsx test/irr_excel.test.ts
 */
import * as fs from "node:fs"; import * as path from "node:path"; import { fileURLToPath } from "node:url";
import { irr, computeDerived, computeCase } from "../src/engine";
import { buildCases } from "../src/caseDefinitions";
import { inputsFromWorkbookJson } from "../src/inputs";

const SERIES: Record<string, number[]> = {"Conservador": [-225227.0263589681, -300302.7018119572, 338352.94042547926, -255772.9260466143, -276268.3861799381, -296988.66595333605, -317820.1061995223, -338908.49448336987, -360269.4631845141, -381919.1550651705, -403750.3443768441, -425906.33329934336, -573652.7944297215, -602267.2197461267, 200466.71751394004, 184223.701518091, -191366.18874010906, 161794.0065915038, 144634.42257799965, 127138.57038938726, 109290.44825508488, 91073.50186591924, 62554.45108259446, 31420.29580712936, 13555.38675848224, -4717.818258177942, -66312.86742494967], "PISO": [-261605.6014158181, -610413.0699702427, -388647.3372067091, -445736.7620491638, -450160.40891869494, -455012.2179468003, -460173.81863710337, -465790.94331542344, -471879.9971638032, -478457.9950487062, -485401.20042401133, -492865.353031042, -644325.6137564026, -665140.9719034148, 279575.34846835665, 272948.82115960866, -93185.39720536815, 269289.02718474163, 261330.11888717537, 252895.1776854014, 243966.75962879992, 234526.77513094482, 211769.04847941725, 201250.48403921636, 190279.89692578546, 178721.56258820486, 112577.96402664669], "M41": [-234550.47666555876, -312733.968887412, 205744.11594199907, -389972.2426147717, -392824.37657964305, -396008.17589623644, -399422.13386913657, -403188.5447721477, -407320.0523580802, -411829.77065595007, -416611.43233176775, -421795.65377912595, -568299.5089937737, -585826.5245969596, 262372.99913086666, 257663.5345005943, -106440.03353555285, 258166.5454626211, 252428.49289186904, 246323.07193441954, 239836.84265948413, 232955.86758268345, 215356.34519923755, 207643.28069006762, 199590.53791598303, 191084.6049870231, 133715.09493339423], "M51": [-250914.46340966737, -334552.6178795565, 183453.91427974176, -450445.0800132826, -453297.21397815394, -456481.0132947473, -459894.97126764746, -463661.38217065856, -467792.88975659106, -472302.608054461, -477084.2697302785, -482268.4911776367, -626130.5387201264, -644589.5675386025, 263099.0536389954, 258389.58900872298, -105713.97902742418, 258892.59997074978, 253154.5473999977, 247049.1264425482, 240562.8971676128, 233681.92209081212, 215356.34519923755, 207643.28069006762, 199590.53791598303, 191084.6049870231, 130338.78935615596]};
// Excel/Mac 16.110 · =IRR(rango, semilla) · null = #NUM!
const EXCEL: Record<string, Record<string, number | null>> = {
  Conservador: { "0.02": null, "0.1": null, "-0.5": -0.305051729168 },
  PISO: { "0.02": -0.072805017064, "0.1": -0.072805017064, "-0.5": -0.072805017064 },
  M41: { "0.02": -0.054876343301, "0.1": -0.054876343301, "-0.5": -0.054876343301 },
  M51: { "0.02": -0.064815346882, "0.1": -0.064815346882, "-0.5": -0.064815346882 },
};
let n = 0, fail = 0;
const check = (name: string, ok: boolean, detail: string) => { n++; if (!ok) fail++; console.log(`  ${ok ? "ok  " : "FAIL"} ${name}  ${detail}`); };
for (const [k, eq] of Object.entries(SERIES)) for (const g of ["0.02", "0.1", "-0.5"]) {
  const got = irr(eq, Number(g)); const exp = EXCEL[k][g];
  const ok = exp === null ? got === null : got !== null && Math.abs(got - exp) <= 1e-9;
  check(`${k} · semilla ${g}`, ok, `Excel ${exp === null ? "#NUM!" : (exp * 100).toFixed(6) + " %"} · motor ${got === null ? "n/a" : (got * 100).toFixed(6) + " %"}`);
}
// invariante VAN(TIR) ≈ 0 sobre la línea base (DATA_DIR o ../data)
const here = path.dirname(fileURLToPath(import.meta.url));
const DATA = process.env.DATA_DIR ? path.resolve(process.env.DATA_DIR) : path.resolve(here, "..", "..", "data");
const names = JSON.parse(fs.readFileSync(path.join(DATA, "names.json"), "utf8"));
const sheets = JSON.parse(fs.readFileSync(path.join(DATA, "sheets.json"), "utf8"));
const inputs = inputsFromWorkbookJson(names, sheets); const d = computeDerived(inputs);
const npv = (cfs: number[], r: number) => cfs.reduce((s, v, i) => s + v / Math.pow(1 + r, i), 0);
let checked = 0, bad: string[] = [];
for (const c of buildCases(inputs, d) as any[]) {
  const res: any = computeCase(inputs, d, c.params ?? c);
  for (const [lab, blk] of [["TIR proyecto", "FCF_u"], ["TIR equity", "EQ"], ["TIR grupo", "Gx"]] as const) {
    const t = res.outputs[lab]; if (typeof t !== "number" || !Number.isFinite(t)) continue;
    const cfs: number[] = res.blocks[blk]; const scale = cfs.reduce((s, v) => s + Math.abs(v), 0);
    checked++; const rel = Math.abs(npv(cfs, t)) / scale; if (rel > 1e-9) bad.push(`${c.name} · ${lab}: |VAN(TIR)|/Σ|cf| = ${rel.toExponential(2)}`);
  }
}
check(`invariante VAN(TIR) ≈ 0 en ${checked} TIR finitas de ${DATA.split("/").slice(-1)[0]}`, bad.length === 0, bad.slice(0, 3).join("; ") || "todas ≤ 1e-9 relativo");
console.log(`\n${fail === 0 ? "PASS" : "FAIL"}: ${n - fail}/${n} comprobaciones`);
if (fail) process.exit(1);
