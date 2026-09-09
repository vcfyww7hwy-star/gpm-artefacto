/**
 * Formateo numérico es-EC DETERMINISTA — sin `Intl`, para que la salida sea
 * idéntica en cualquier navegador / runtime con o sin datos de locale.
 *
 * Convenciones:
 *  - miles con punto, decimales con coma:            1.234.567,89
 *  - signo menos verdadero U+2212 para negativos:     −196.736
 *  - redondeo «half away from zero» (como Excel), con corrección de coma
 *    flotante (1,005 → 1,01; 0,12345 → 12,35 %)
 *  - porcentaje con espacio fino U+2009 antes de «%»: 8,80 %
 *  - valores no finitos / nulos → «—» (raya)
 */

export const MINUS = "−"; // −
export const THIN_SPACE = " "; // espacio fino
export const NBSP = " ";
export const EM_DASH = "—"; // —
export const INFINITY = "∞"; // ∞

export type SignMode = "auto" | "always" | "never";

export interface NumberOptions {
  /** Decimales fijos (defecto 0). */
  decimals?: number;
  /** "auto": sólo negativos; "always": también «+»; "never": sin signo. */
  sign?: SignMode;
  /** Texto para NaN / null / undefined (defecto «—»). */
  empty?: string;
}

/* -------------------------------------------------------------------------- */
/* Núcleo                                                                     */
/* -------------------------------------------------------------------------- */

/** Desplaza la coma decimal `places` posiciones operando sobre la representación decimal. */
function shiftDecimal(value: number, places: number): number {
  const [mantissa, exponent] = value.toExponential().split("e");
  return Number(`${mantissa}e${Number(exponent) + places}`);
}

/**
 * Redondea a `decimals` decimales, half away from zero, sin los artefactos de
 * `toFixed` (p. ej. (1.005).toFixed(2) === "1.00").
 */
export function roundTo(x: number, decimals = 0): number {
  if (!Number.isFinite(x)) return x;
  const sign = x < 0 ? -1 : 1;
  const rounded = Math.round(shiftDecimal(Math.abs(x), decimals));
  const result = shiftDecimal(rounded, -decimals);
  return sign * result;
}

/** Inserta separadores de miles («.») en una cadena de dígitos. */
function groupThousands(digits: string): string {
  let out = "";
  for (let i = 0; i < digits.length; i++) {
    const fromEnd = digits.length - i;
    out += digits[i];
    if (fromEnd > 1 && fromEnd % 3 === 1) out += ".";
  }
  return out;
}

interface Parts {
  negative: boolean;
  integer: string; // con separadores de miles
  fraction: string; // sin coma; "" si decimals = 0
}

/**
 * Descompone |x·10^scaleExp| redondeado a `decimals` en partes ya formateadas.
 * `scaleExp` permite escalar sin multiplicar en coma flotante (porcentajes: 2).
 */
function toParts(x: number, decimals: number, scaleExp = 0): Parts {
  const d = Math.max(0, Math.trunc(decimals));
  const abs = Math.abs(x);
  const asInt = Math.round(shiftDecimal(abs, d + scaleExp));
  if (asInt > Number.MAX_SAFE_INTEGER) {
    // Fuera del rango entero seguro: se degrada a toFixed sobre el valor escalado.
    const scaled = shiftDecimal(abs, scaleExp).toFixed(d);
    const [int = "0", frac = ""] = scaled.split(".");
    return { negative: x < 0, integer: groupThousands(int), fraction: frac };
  }
  const raw = String(asInt).padStart(d + 1, "0");
  const integer = raw.slice(0, raw.length - d);
  const fraction = d > 0 ? raw.slice(raw.length - d) : "";
  // Un valor que redondea a cero nunca lleva signo («−0,00» no existe).
  const negative = x < 0 && asInt !== 0;
  return { negative, integer: groupThousands(integer), fraction };
}

function signPrefix(negative: boolean, isZero: boolean, mode: SignMode): string {
  if (mode === "never") return "";
  if (negative) return MINUS;
  if (mode === "always" && !isZero) return "+";
  return "";
}

function isEmpty(x: number | null | undefined): x is null | undefined {
  return x === null || x === undefined || Number.isNaN(x);
}

/**
 * Formatea un número: `fmtNum(1234567.891, 2) === "1.234.567,89"`.
 * Con `prefix` (p. ej. «$ ») el signo va delante del prefijo: «−$ 196.736».
 */
function formatCore(
  x: number | null | undefined,
  decimals: number,
  sign: SignMode,
  empty: string,
  scaleExp = 0,
  prefix = "",
  suffix = "",
): string {
  if (isEmpty(x)) return empty;
  if (!Number.isFinite(x)) return `${x < 0 ? MINUS : ""}${INFINITY}`;
  const parts = toParts(x, decimals, scaleExp);
  const isZero = /^0*$/.test(parts.integer.replace(/\./g, "")) && /^0*$/.test(parts.fraction);
  const body = parts.fraction ? `${parts.integer},${parts.fraction}` : parts.integer;
  return `${signPrefix(parts.negative, isZero, sign)}${prefix}${body}${suffix}`;
}

/* -------------------------------------------------------------------------- */
/* API pública                                                                */
/* -------------------------------------------------------------------------- */

/** Número plano: `1.234.567,89`. */
export function fmtNum(x: number | null | undefined, decimals = 0, sign: SignMode = "auto"): string {
  return formatCore(x, decimals, sign, EM_DASH);
}

/** Variante con objeto de opciones. */
export function formatNumber(x: number | null | undefined, opts: NumberOptions = {}): string {
  return formatCore(x, opts.decimals ?? 0, opts.sign ?? "auto", opts.empty ?? EM_DASH);
}

/** Número con signo explícito: `+2,5` / `−1,2`. */
export function fmtSigned(x: number | null | undefined, decimals = 1): string {
  return formatCore(x, decimals, "always", EM_DASH);
}

/**
 * Porcentaje a partir de una FRACCIÓN (0,088 → «8,80 %»), como el formato
 * porcentual de Excel sobre la celda. Espacio fino antes de «%».
 */
export function fmtPct(x: number | null | undefined, decimals = 2, sign: SignMode = "auto"): string {
  return formatCore(x, decimals, sign, EM_DASH, 2, "", `${THIN_SPACE}%`);
}

/** Múltiplo: `0,83x`. */
export function fmtX(x: number | null | undefined, decimals = 2): string {
  return formatCore(x, decimals, "auto", EM_DASH, 0, "", "x");
}

/** Años: `7,4 años` (singular sólo para exactamente «1»). */
export function fmtYears(x: number | null | undefined, decimals = 1): string {
  const body = formatCore(x, decimals, "auto", EM_DASH);
  if (body === EM_DASH) return body;
  const unit = body === "1" ? "año" : "años";
  return `${body} ${unit}`;
}

/** Dólares: `$ 214.690` / `−$ 196.736` (signo delante del símbolo). */
export function fmtUSD(x: number | null | undefined, decimals = 0, sign: SignMode = "auto"): string {
  return formatCore(x, decimals, sign, EM_DASH, 0, "$ ");
}

/** Puntos porcentuales con signo: `+1,8 pp` / `−1,2 pp` (cero sin signo). */
export function fmtPP(x: number | null | undefined, decimals = 1): string {
  return formatCore(x, decimals, "always", EM_DASH, 0, "", " pp");
}

interface Compact {
  scaled: number;
  unit: "" | "k" | "M";
  decimals: number;
}

/**
 * Escala a k / M y elige decimales: 2 si |escalado| < 10, si no 1; sin unidad
 * (|x| < 1.000) usa 0 decimales. Un redondeo que alcance 1.000 sube de unidad.
 */
function compactParts(x: number, decimals?: number): Compact {
  const abs = Math.abs(x);
  const units: Array<{ unit: "" | "k" | "M"; div: number }> = [
    { unit: "", div: 1 },
    { unit: "k", div: 1e3 },
    { unit: "M", div: 1e6 },
  ];
  let idx = abs >= 1e6 ? 2 : abs >= 1e3 ? 1 : 0;
  for (;;) {
    const { unit, div } = units[idx]!;
    const scaled = shiftDecimal(x, -Math.log10(div));
    const d = decimals ?? (unit === "" ? 0 : Math.abs(scaled) < 10 ? 2 : 1);
    const rounded = Math.abs(roundTo(scaled, d));
    if (rounded >= 1000 && idx < units.length - 1) {
      idx += 1;
      continue;
    }
    return { scaled, unit, decimals: d };
  }
}

/** Compacto: `214,7 k` · `4,12 M` · `850`. */
export function fmtCompact(x: number | null | undefined, decimals?: number, sign: SignMode = "auto"): string {
  if (isEmpty(x)) return EM_DASH;
  if (!Number.isFinite(x)) return `${x < 0 ? MINUS : ""}${INFINITY}`;
  const c = compactParts(x, decimals);
  return formatCore(c.scaled, c.decimals, sign, EM_DASH, 0, "", c.unit ? ` ${c.unit}` : "");
}

/** Dólares compactos: `$ 4,12 M` · `−$ 214,7 k`. */
export function fmtUSDCompact(x: number | null | undefined, decimals?: number, sign: SignMode = "auto"): string {
  if (isEmpty(x)) return EM_DASH;
  if (!Number.isFinite(x)) return `${x < 0 ? MINUS : ""}${INFINITY}`;
  const c = compactParts(x, decimals);
  return formatCore(c.scaled, c.decimals, sign, EM_DASH, 0, "$ ", c.unit ? ` ${c.unit}` : "");
}

/* -------------------------------------------------------------------------- */
/* Fechas                                                                     */
/* -------------------------------------------------------------------------- */

export const MONTHS_ES_ABBR = [
  "ene", "feb", "mar", "abr", "may", "jun",
  "jul", "ago", "sep", "oct", "nov", "dic",
] as const;

export const MONTHS_ES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
] as const;

/** Serial de fecha de Excel (sistema 1900) → Date en UTC a medianoche. */
export function excelSerialToDate(serial: number): Date {
  // 1899-12-30 es el día 0 del sistema 1900 (Excel cuenta el falso 29-feb-1900).
  const epoch = Date.UTC(1899, 11, 30);
  return new Date(epoch + Math.round(serial) * 86_400_000);
}

interface CalendarDate {
  y: number;
  m: number; // 1..12
  d: number;
}

function toCalendar(value: Date | string | number, utc: boolean): CalendarDate | null {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) return null;
    const dt = excelSerialToDate(value);
    return { y: dt.getUTCFullYear(), m: dt.getUTCMonth() + 1, d: dt.getUTCDate() };
  }
  if (typeof value === "string") {
    // ISO «YYYY-MM-DD…»: se lee como fecha de calendario, sin corrimiento de zona.
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value.trim());
    if (m) return { y: Number(m[1]), m: Number(m[2]), d: Number(m[3]) };
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    return toCalendar(parsed, utc);
  }
  if (Number.isNaN(value.getTime())) return null;
  return utc
    ? { y: value.getUTCFullYear(), m: value.getUTCMonth() + 1, d: value.getUTCDate() }
    : { y: value.getFullYear(), m: value.getMonth() + 1, d: value.getDate() };
}

export interface DateOptions {
  /** Leer objetos Date en UTC (defecto: hora local). Cadenas ISO y seriales Excel no dependen de esto. */
  utc?: boolean;
  empty?: string;
}

/** Fecha `dd-mmm-yyyy` en español: `08-sep-2026`. Acepta Date, ISO o serial Excel. */
export function fmtDate(value: Date | string | number | null | undefined, opts: DateOptions = {}): string {
  if (value === null || value === undefined) return opts.empty ?? EM_DASH;
  const cal = toCalendar(value, opts.utc ?? false);
  if (!cal || cal.m < 1 || cal.m > 12) return opts.empty ?? EM_DASH;
  const dd = String(cal.d).padStart(2, "0");
  const mmm = MONTHS_ES_ABBR[cal.m - 1];
  return `${dd}-${mmm}-${cal.y}`;
}

/** Mes y año: `sep-2026` (útil para ejes temporales). */
export function fmtMonthYear(value: Date | string | number | null | undefined, opts: DateOptions = {}): string {
  if (value === null || value === undefined) return opts.empty ?? EM_DASH;
  const cal = toCalendar(value, opts.utc ?? false);
  if (!cal || cal.m < 1 || cal.m > 12) return opts.empty ?? EM_DASH;
  return `${MONTHS_ES_ABBR[cal.m - 1]}-${cal.y}`;
}
