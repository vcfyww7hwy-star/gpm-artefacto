/**
 * Pruebas del formateo es-EC. Ejecutar: `npx tsx test/format.test.ts`
 * (o `npm run test:format`). Sin framework: assert + tabla de resultados.
 */
import assert from "node:assert/strict";
import {
  EM_DASH,
  MINUS,
  THIN_SPACE,
  excelSerialToDate,
  fmtCompact,
  fmtDate,
  fmtMonthYear,
  fmtNum,
  fmtPP,
  fmtPct,
  fmtSigned,
  fmtUSD,
  fmtUSDCompact,
  fmtX,
  fmtYears,
  formatNumber,
  roundTo,
} from "../src/lib/format";

type Case = { name: string; actual: string; expected: string };
const cases: Case[] = [];
const t = (name: string, actual: string, expected: string) => cases.push({ name, actual, expected });

/* --- números planos ------------------------------------------------------- */
t("fmtNum miles y decimales", fmtNum(1234567.89, 2), "1.234.567,89");
t("fmtNum redondeo a 2", fmtNum(1234567.891, 2), "1.234.567,89");
t("fmtNum entero", fmtNum(214690), "214.690");
t("fmtNum negativo, half away from zero", fmtNum(-1234.5), `${MINUS}1.235`);
t("fmtNum 1,005 → 1,01 (sin artefacto toFixed)", fmtNum(1.005, 2), "1,01");
t("fmtNum 0,1+0,2", fmtNum(0.1 + 0.2, 2), "0,30");
t("fmtNum cero", fmtNum(0, 2), "0,00");
t("fmtNum −0,001 a 2 decimales no lleva signo", fmtNum(-0.001, 2), "0,00");
t("fmtNum 999,999 → 1.000,00", fmtNum(999.999, 2), "1.000,00");
t("fmtNum millones", fmtNum(5_000_000), "5.000.000");
t("fmtNum sin miles bajo 1.000", fmtNum(999), "999");
t("fmtNum NaN", fmtNum(Number.NaN), EM_DASH);
t("fmtNum null", fmtNum(null), EM_DASH);
t("fmtNum undefined", fmtNum(undefined), EM_DASH);
t("fmtNum Infinity", fmtNum(Number.POSITIVE_INFINITY), "∞");
t("fmtNum −Infinity", fmtNum(Number.NEGATIVE_INFINITY), `${MINUS}∞`);
t("fmtNum sign always", fmtNum(12.5, 1, "always"), "+12,5");
t("fmtNum sign never", fmtNum(-12.5, 1, "never"), "12,5");
t("formatNumber opciones", formatNumber(-1500.256, { decimals: 1 }), `${MINUS}1.500,3`);
t("formatNumber empty", formatNumber(null, { empty: "n/d" }), "n/d");
t("fmtSigned +", fmtSigned(2.5), "+2,5");
t("fmtSigned −", fmtSigned(-1.25, 2), `${MINUS}1,25`);
t("fmtSigned cero sin signo", fmtSigned(0), "0,0");

/* --- porcentajes ---------------------------------------------------------- */
t("fmtPct fracción", fmtPct(0.088), `8,80${THIN_SPACE}%`);
t("fmtPct redondeo exacto 0,12345 → 12,35 %", fmtPct(0.12345), `12,35${THIN_SPACE}%`);
t("fmtPct negativo", fmtPct(-0.012, 1), `${MINUS}1,2${THIN_SPACE}%`);
t("fmtPct 100 %", fmtPct(1, 0), `100${THIN_SPACE}%`);
t("fmtPct null", fmtPct(null), EM_DASH);
t("fmtPct signo always", fmtPct(0.018, 1, "always"), `+1,8${THIN_SPACE}%`);

/* --- múltiplos, años ------------------------------------------------------ */
t("fmtX", fmtX(0.83), "0,83x");
t("fmtX redondeo", fmtX(1.2345), "1,23x");
t("fmtYears", fmtYears(7.4), "7,4 años");
t("fmtYears redondeo", fmtYears(7.44), "7,4 años");
t("fmtYears singular", fmtYears(1, 0), "1 año");
t("fmtYears 1,0 plural", fmtYears(1), "1,0 años");

/* --- USD -------------------------------------------------------------------- */
t("fmtUSD positivo", fmtUSD(214690), "$ 214.690");
t("fmtUSD negativo (signo delante de $)", fmtUSD(-196736), `${MINUS}$ 196.736`);
t("fmtUSD decimales", fmtUSD(1234.567, 2), "$ 1.234,57");
t("fmtUSD cero", fmtUSD(0), "$ 0");
t("fmtUSD −0,4 redondea a $ 0 sin signo", fmtUSD(-0.4), "$ 0");
t("fmtUSD always", fmtUSD(1000, 0, "always"), "+$ 1.000");

/* --- compacto ---------------------------------------------------------------- */
t("fmtCompact k (1 decimal ≥ 10)", fmtCompact(214690), "214,7 k");
t("fmtCompact M (2 decimales < 10)", fmtCompact(4_120_000), "4,12 M");
t("fmtCompact k 45,2", fmtCompact(45200), "45,2 k");
t("fmtCompact k 1,50", fmtCompact(1500), "1,50 k");
t("fmtCompact decimales explícitos", fmtCompact(1500, 1), "1,5 k");
t("fmtCompact sube de unidad al redondear", fmtCompact(999_950), "1,00 M");
t("fmtCompact bajo 1.000", fmtCompact(850), "850");
t("fmtCompact negativo", fmtCompact(-4_120_000), `${MINUS}4,12 M`);
t("fmtCompact miles de millones se quedan en M", fmtCompact(1_234_000_000), "1.234,0 M");
t("fmtCompact cero", fmtCompact(0), "0");
t("fmtCompact null", fmtCompact(null), EM_DASH);
t("fmtUSDCompact M", fmtUSDCompact(4_120_000), "$ 4,12 M");
t("fmtUSDCompact negativo k", fmtUSDCompact(-214690), `${MINUS}$ 214,7 k`);

/* --- pp ---------------------------------------------------------------------- */
t("fmtPP +", fmtPP(1.8), "+1,8 pp");
t("fmtPP −", fmtPP(-1.2), `${MINUS}1,2 pp`);
t("fmtPP cero", fmtPP(0), "0,0 pp");
t("fmtPP redondea a cero sin signo", fmtPP(0.04), "0,0 pp");
t("fmtPP 2 decimales", fmtPP(-0.456, 2), `${MINUS}0,46 pp`);

/* --- fechas ------------------------------------------------------------------ */
t("fmtDate ISO", fmtDate("2026-09-08"), "08-sep-2026");
t("fmtDate ISO con hora", fmtDate("2027-12-31T10:00:00"), "31-dic-2027");
t("fmtDate Date local", fmtDate(new Date(2026, 0, 1)), "01-ene-2026");
t("fmtDate Date UTC", fmtDate(new Date(Date.UTC(2026, 4, 15)), { utc: true }), "15-may-2026");
t("fmtDate serial Excel 46273", fmtDate(46273), "08-sep-2026");
t("fmtDate serial Excel 45658", fmtDate(45658), "01-ene-2025");
t("fmtDate inválida", fmtDate("no es fecha"), EM_DASH);
t("fmtDate null", fmtDate(null), EM_DASH);
t("fmtMonthYear", fmtMonthYear("2026-09-08"), "sep-2026");
t("excelSerialToDate", excelSerialToDate(46273).toISOString(), "2026-09-08T00:00:00.000Z");

/* --- roundTo ------------------------------------------------------------------ */
t("roundTo 1,005 → 1,01", String(roundTo(1.005, 2)), "1.01");
t("roundTo −2,5 → −3 (away from zero)", String(roundTo(-2.5)), "-3");
t("roundTo 2,5 → 3", String(roundTo(2.5)), "3");
t("roundTo 1234,5678 → 1234,57", String(roundTo(1234.5678, 2)), "1234.57");

/* --- informe -------------------------------------------------------------------- */
let failures = 0;
for (const c of cases) {
  try {
    assert.equal(c.actual, c.expected);
    console.log(`  ok   ${c.name}  →  ${JSON.stringify(c.actual)}`);
  } catch {
    failures++;
    console.log(`  FAIL ${c.name}\n       esperado ${JSON.stringify(c.expected)}\n       obtenido ${JSON.stringify(c.actual)}`);
  }
}
console.log(`\n${cases.length - failures}/${cases.length} pruebas de formato correctas`);
if (failures > 0) process.exit(1);
