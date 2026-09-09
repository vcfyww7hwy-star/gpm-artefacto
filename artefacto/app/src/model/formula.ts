/**
 * Evaluador de los «textos vivos» del libro. Las cadenas que en Excel son fórmulas de texto
 * («="Fee "&TEXT(Fee_Gerencia_Pct,"0%")&"…"») o plantillas con llaves («… {TEXT(X_TIR,"0.0%")} …») llegan
 * desde build30/xlformula.py como AST JSON (book.json) y aquí se evalúan con los valores del motor, de modo que
 * el artefacto dice exactamente lo que dice el Excel, pero con las cifras del caso y de los Mandos.
 *
 * Subconjunto de Excel cubierto: & + − * / ^, comparaciones, IF, IFERROR, INDEX (1-D), ABS, MIN, MAX, N, TEXT,
 * nombres definidos y referencias 'Hoja'!Celda (resueltas por el contexto). Semántica de coerción de Excel:
 * números en «&» con formato General; comparación de textos sin distinguir mayúsculas; IF acepta números.
 */
import { fmtNum, MINUS, MONTHS_ES_ABBR, THIN_SPACE } from "@/lib/format";

export type Node =
  | ["num", number]
  | ["str", string]
  | ["bool", boolean]
  | ["name", string]
  | ["ref", string, string]
  | ["call", string, Node[]]
  | ["bin", string, Node, Node]
  | ["neg", Node];

/** Envoltura de las constantes del generador: fórmula de celda, plantilla con llaves o texto plano. */
export type Live = ["f", Node, string?] | ["tpl", (string | Node)[]] | string | null;

export type Value = number | string | boolean | null | Value[];

export class XlError extends Error {
  code: string;
  constructor(code: string, detail?: string) {
    super(`${code}${detail ? ` ${detail}` : ""}`);
    this.code = code;
  }
}

export type Locale = "es-EC" | "en-US";

export interface EvalCtx {
  /** valor de un nombre definido; lanza XlError("#NAME?") si no existe */
  name(n: string): Value;
  /** valor de una referencia de celda 'Hoja'!C5 (sin $); lanza XlError("#REF!") si no se resuelve */
  ref(sheet: string, cell: string): Value;
  /** convención numérica de la salida: es-EC (artefacto) o en-US (igual que el libro, para pruebas) */
  locale?: Locale;
}

const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// ------------------------------------------------------------------------------------------ coerciones
function isArr(v: Value): v is Value[] {
  return Array.isArray(v);
}
function scalar(v: Value): Value {
  // Excel: una matriz en contexto escalar toma su primer elemento (bastante para nuestros textos)
  return isArr(v) ? scalar(v[0] ?? null) : v;
}
export function toNumber(v: Value): number {
  v = scalar(v);
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  if (v === null || v === "") return 0;
  if (typeof v === "string") {
    const n = Number(v.replace(",", "."));
    if (Number.isFinite(n)) return n;
    // fechas ISO se comparan/operan como números de serie (días)
    const d = parseISO(v);
    if (d) return d;
    throw new XlError("#VALUE!", `no numérico: ${v}`);
  }
  throw new XlError("#VALUE!");
}
function toBool(v: Value): boolean {
  v = scalar(v);
  if (typeof v === "boolean") return v;
  if (typeof v === "number") return v !== 0;
  if (typeof v === "string") {
    if (v.toUpperCase() === "TRUE") return true;
    if (v.toUpperCase() === "FALSE") return false;
    throw new XlError("#VALUE!", `no lógico: ${v}`);
  }
  return false;
}

/** Formato «General» de Excel para números en concatenaciones («&»). */
export function generalText(x: number, locale: Locale = "es-EC"): string {
  if (!Number.isFinite(x)) return "#NUM!";
  let s: string;
  if (Number.isInteger(x)) s = String(x);
  else {
    // Excel convierte números a texto en «&» con hasta 15 cifras significativas, sin ceros finales
    s = Number(x.toPrecision(15)).toString();
  }
  if (locale === "es-EC") s = s.replace(".", ",").replace("-", MINUS);
  return s;
}
export function toText(v: Value, locale: Locale = "es-EC"): string {
  v = scalar(v);
  if (v === null) return "";
  if (typeof v === "string") return v;
  if (typeof v === "boolean") return v ? "TRUE" : "FALSE";
  return generalText(v as number, locale);
}

// ------------------------------------------------------------------------------------------ fechas
/** Excel serial (sistema 1900) de una fecha ISO «YYYY-MM-DD…»; null si no es ISO. */
export function parseISO(s: string): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s.trim());
  if (!m) return null;
  const ms = Date.UTC(+m[1], +m[2] - 1, +m[3]);
  return Math.round((ms - Date.UTC(1899, 11, 30)) / 86400000);
}
function serialToYMD(serial: number): { y: number; m: number; d: number } {
  const dt = new Date(Date.UTC(1899, 11, 30) + Math.round(serial) * 86400000);
  return { y: dt.getUTCFullYear(), m: dt.getUTCMonth() + 1, d: dt.getUTCDate() };
}

// ------------------------------------------------------------------------------------------ TEXT()
/**
 * TEXT(valor, formato) para los códigos usados en el libro: 0 · 0.0 · 0.00 · 0.000 · 0.0000 · #,##0 · #,##0.00 ·
 * 0% · 0.0% · 0.00% · secciones «pos;neg» (+0.0;-0.0 · +0%;-0% · +#,##0;-#,##0) · yyyy · mmm-yyyy · mmm-yy · dd-mmm-yyyy.
 * En es-EC sigue la convención del artefacto (miles «.», decimales «,», espacio fino antes de «%», menos U+2212);
 * en en-US reproduce la salida de Excel/LibreOffice (para las pruebas contra el libro).
 */
export function xlText(v: Value, fmt: string, locale: Locale = "es-EC"): string {
  v = scalar(v);
  // fechas
  if (/[ymd]/i.test(fmt) && !/[#0]/.test(fmt)) {
    const serial = typeof v === "number" ? v : typeof v === "string" ? parseISO(v) : null;
    if (serial === null) throw new XlError("#VALUE!", `fecha inválida: ${String(v)}`);
    const { y, m, d } = serialToYMD(serial);
    const mmm = locale === "es-EC" ? MONTHS_ES_ABBR[m - 1] : MONTHS_EN[m - 1];
    return fmt
      .replace(/yyyy/i, String(y))
      .replace(/yy/i, String(y).slice(2))
      .replace(/mmm/i, mmm)
      .replace(/dd/i, String(d).padStart(2, "0"));
  }
  const x = toNumber(v);
  // secciones «positivo;negativo[;cero]»: la sección elegida lleva su propio signo literal y formatea el valor absoluto
  const sections = fmt.split(";");
  let section = sections[0];
  if (sections.length >= 2 && x < 0) section = sections[1];
  if (sections.length >= 3 && x === 0) section = sections[2];
  const literalSign = sections.length >= 2 ? (/^[+-]/.exec(section)?.[0] ?? "") : "";
  const body = section.replace(/^[+-]/, "");
  const pct = body.endsWith("%");
  const numPart = pct ? body.slice(0, -1) : body;
  const grouped = numPart.includes(",");
  const decimals = numPart.includes(".") ? numPart.split(".")[1].replace(/[^0#]/g, "").length : 0;
  const val = pct ? x * 100 : x;
  const magnitude = sections.length >= 2 ? Math.abs(val) : val;
  let out: string;
  if (locale === "es-EC") {
    out = fmtNum(magnitude, decimals, "auto");
    if (!grouped) out = out.replace(/\./g, "");
    if (pct) out += `${THIN_SPACE}%`;
    if (literalSign) out = (literalSign === "-" ? MINUS : "+") + out;
  } else {
    const rounded = roundHalfAway(Math.abs(magnitude), decimals);
    let s = rounded.toFixed(decimals);
    if (grouped) {
      const [i, f] = s.split(".");
      s = i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f !== undefined ? `.${f}` : "");
    }
    const neg = magnitude < 0 && rounded !== 0;
    out = (literalSign || (neg ? "-" : "")) + s + (pct ? "%" : "");
  }
  return out;
}
function roundHalfAway(x: number, decimals: number): number {
  const p = Math.pow(10, decimals);
  return Math.round(x * p + Number.EPSILON * (x * p)) / p;
}

// ------------------------------------------------------------------------------------------ evaluación
export function evalNode(n: Node, ctx: EvalCtx): Value {
  switch (n[0]) {
    case "num":
      return n[1];
    case "str":
      return n[1];
    case "bool":
      return n[1];
    case "name":
      return ctx.name(n[1]);
    case "ref":
      return ctx.ref(n[1], n[2]);
    case "neg":
      return -toNumber(evalNode(n[1], ctx));
    case "bin": {
      const op = n[1];
      const a = evalNode(n[2], ctx);
      const b = evalNode(n[3], ctx);
      switch (op) {
        case "&":
          return toText(a, ctx.locale) + toText(b, ctx.locale);
        case "+":
          return toNumber(a) + toNumber(b);
        case "-":
          return toNumber(a) - toNumber(b);
        case "*":
          return toNumber(a) * toNumber(b);
        case "/": {
          const d = toNumber(b);
          if (d === 0) throw new XlError("#DIV/0!");
          return toNumber(a) / d;
        }
        case "^":
          return Math.pow(toNumber(a), toNumber(b));
        case "=":
          return compare(a, b) === 0;
        case "<>":
          return compare(a, b) !== 0;
        case "<":
          return compare(a, b) < 0;
        case ">":
          return compare(a, b) > 0;
        case "<=":
          return compare(a, b) <= 0;
        case ">=":
          return compare(a, b) >= 0;
        default:
          throw new XlError("#NAME?", `operador ${op}`);
      }
    }
    case "call":
      return call(n[1], n[2], ctx);
  }
}

/** Comparación de Excel: número < texto < lógico; textos sin distinguir mayúsculas; vacío = 0 = "". */
function compare(a: Value, b: Value): number {
  a = scalar(a); b = scalar(b);
  const rank = (v: Value) => (typeof v === "boolean" ? 2 : typeof v === "string" ? 1 : 0);
  if (a === null) a = typeof b === "string" ? "" : 0;
  if (b === null) b = typeof a === "string" ? "" : 0;
  if (rank(a) !== rank(b)) return rank(a) - rank(b);
  if (typeof a === "string" && typeof b === "string") {
    const x = a.toLowerCase(), y = b.toLowerCase();
    return x < y ? -1 : x > y ? 1 : 0;
  }
  const x = toNumber(a), y = toNumber(b);
  return x < y ? -1 : x > y ? 1 : 0;
}

function flatNums(vals: Value[]): number[] {
  const out: number[] = [];
  const walk = (v: Value) => {
    if (isArr(v)) v.forEach(walk);
    else if (typeof v === "number") out.push(v);
    else if (typeof v === "boolean") out.push(v ? 1 : 0);
    else if (typeof v === "string") { const n = Number(v); if (Number.isFinite(n) && v.trim() !== "") out.push(n); }
  };
  vals.forEach(walk);
  return out;
}

function call(fn: string, args: Node[], ctx: EvalCtx): Value {
  switch (fn) {
    case "IF": {
      const c = toBool(evalNode(args[0], ctx));
      if (c) return args[1] ? evalNode(args[1], ctx) : true;
      return args[2] ? evalNode(args[2], ctx) : false;
    }
    case "IFERROR": {
      try {
        const v = evalNode(args[0], ctx);
        if (typeof v === "number" && !Number.isFinite(v)) return evalNode(args[1], ctx);
        return v;
      } catch (e) {
        if (e instanceof XlError) return evalNode(args[1], ctx);
        throw e;
      }
    }
    case "TEXT":
      return xlText(evalNode(args[0], ctx), toText(evalNode(args[1], ctx)), ctx.locale);
    case "INDEX": {
      const arr = evalNode(args[0], ctx);
      const k = Math.trunc(toNumber(evalNode(args[1], ctx)));
      const list = isArr(arr) ? (arr.length === 1 && isArr(arr[0]) ? arr[0] : arr) : [arr];
      // INDEX(rango, fila, col) sobre una fila única (Y_P50 etc.): el tercer argumento manda
      const idx = args.length >= 3 ? Math.trunc(toNumber(evalNode(args[2], ctx))) : k;
      if (idx < 1 || idx > list.length) throw new XlError("#REF!", `INDEX ${idx}/${list.length}`);
      return list[idx - 1];
    }
    case "ABS":
      return Math.abs(toNumber(evalNode(args[0], ctx)));
    case "MIN": {
      const xs = flatNums(args.map((a) => evalNode(a, ctx)));
      return xs.length ? Math.min(...xs) : 0;
    }
    case "MAX": {
      const xs = flatNums(args.map((a) => evalNode(a, ctx)));
      return xs.length ? Math.max(...xs) : 0;
    }
    case "N": {
      const v = scalar(evalNode(args[0], ctx));
      return typeof v === "number" ? v : typeof v === "boolean" ? (v ? 1 : 0) : 0;
    }
    case "ISNUMBER":
      return typeof scalar(evalNode(args[0], ctx)) === "number";
    case "ROUND": {
      const x = toNumber(evalNode(args[0], ctx)), d = Math.trunc(toNumber(evalNode(args[1], ctx)));
      const p = Math.pow(10, d);
      return Math.sign(x) * Math.round(Math.abs(x) * p) / p;
    }
    case "AND":
      return args.every((a) => toBool(evalNode(a, ctx)));
    case "OR":
      return args.some((a) => toBool(evalNode(a, ctx)));
    case "NOT":
      return !toBool(evalNode(args[0], ctx));
    case "SUM":
      return flatNums(args.map((a) => evalNode(a, ctx))).reduce((s, x) => s + x, 0);
    case "YEAR": {
      const v = scalar(evalNode(args[0], ctx));
      const serial = typeof v === "number" ? v : typeof v === "string" ? parseISO(v) : null;
      if (serial === null) throw new XlError("#VALUE!");
      return serialToYMD(serial).y;
    }
    case "LEFT": {
      const s = toText(evalNode(args[0], ctx), ctx.locale);
      const k = args[1] ? Math.trunc(toNumber(evalNode(args[1], ctx))) : 1;
      return s.slice(0, k);
    }
    default:
      throw new XlError("#NAME?", `función ${fn}`);
  }
}

/** Evalúa un texto vivo a cadena. Un error de Excel se devuelve como su código («#N/A» etc.), nunca lanza. */
export function renderLive(l: Live | undefined, ctx: EvalCtx): string {
  if (l === null || l === undefined) return "";
  if (typeof l === "string") return l;
  try {
    if (l[0] === "f") return toText(evalNode(l[1], ctx), ctx.locale);
    return l[1].map((p) => (typeof p === "string" ? p : toText(evalNode(p, ctx), ctx.locale))).join("");
  } catch (e) {
    if (e instanceof XlError) return e.code;
    throw e;
  }
}

/** Nombres y referencias que usa un texto vivo (para saber si depende del libro «congelado»). */
export function namesIn(l: Live | undefined, acc: Set<string> = new Set()): Set<string> {
  const walk = (n: Node) => {
    switch (n[0]) {
      case "name": acc.add(n[1]); break;
      case "ref": acc.add(`${n[1]}!${n[2]}`); break;
      case "call": n[2].forEach(walk); break;
      case "bin": walk(n[2]); walk(n[3]); break;
      case "neg": walk(n[1]); break;
      default: break;
    }
  };
  if (l && typeof l !== "string") {
    if (l[0] === "f") walk(l[1]);
    else l[1].forEach((p) => { if (typeof p !== "string") walk(p); });
  }
  return acc;
}
