/**
 * inputs.ts — build `Inputs` from the two workbook extracts:
 *   names.json  : { name: { sheet, ref, value | values, formula | formulas } }   (317 defined names)
 *   sheets.json : { sheetName: { state, cells: { "A1": { v, f? } } } }
 *
 * Everything primitive is read by its Excel defined name; the 05_CAPEX rubro table (rows 7–15,
 * columns C/D/E/G/I/O) and the 04_Energia consumption tables (D17:F28, D66:E70) are read by cell.
 */
import type { Inputs, Rubro, SiNo } from "./engine";

export interface NameEntry {
  sheet?: string;
  ref?: string;
  value?: unknown;
  values?: unknown;
  formula?: unknown;
  formulas?: unknown;
}
export type NamesJson = Record<string, NameEntry>;
export interface CellJson { v?: unknown; f?: string }
export type SheetsJson = Record<string, { state?: string; cells: Record<string, CellJson> }>;

function nameValue(names: NamesJson, name: string): unknown {
  const e = names[name];
  if (!e) throw new Error(`Nombre definido ausente en names.json: ${name}`);
  return e.value !== undefined ? e.value : e.values;
}

function num(names: NamesJson, name: string): number {
  const v = nameValue(names, name);
  if (typeof v !== "number" || !Number.isFinite(v)) throw new Error(`${name}: se esperaba un número, llegó ${JSON.stringify(v)}`);
  return v;
}
function numOrNull(names: NamesJson, name: string): number | null {
  const v = nameValue(names, name);
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}
function str(names: NamesJson, name: string): string {
  const v = nameValue(names, name);
  if (typeof v !== "string") throw new Error(`${name}: se esperaba texto, llegó ${JSON.stringify(v)}`);
  return v;
}
function siNo(names: NamesJson, name: string): SiNo {
  const v = str(names, name);
  if (v !== "Sí" && v !== "No") throw new Error(`${name}: se esperaba "Sí"/"No", llegó ${JSON.stringify(v)}`);
  return v;
}
/** Flatten a 2-D range value (rows × cols) into a 1-D array (row-major). */
function flat(v: unknown): unknown[] {
  if (!Array.isArray(v)) return [v];
  const out: unknown[] = [];
  for (const row of v) { if (Array.isArray(row)) out.push(...row); else out.push(row); }
  return out;
}
function numArr(names: NamesJson, name: string): number[] {
  return flat(nameValue(names, name)).map((x, k) => {
    if (typeof x !== "number" || !Number.isFinite(x)) throw new Error(`${name}[${k}]: se esperaba un número, llegó ${JSON.stringify(x)}`);
    return x;
  });
}
function numOrNullArr(names: NamesJson, name: string): (number | null)[] {
  return flat(nameValue(names, name)).map((x) => (typeof x === "number" && Number.isFinite(x) ? x : null));
}
function strArr(names: NamesJson, name: string): string[] {
  return flat(nameValue(names, name)).map((x) => String(x));
}
/** Dates arrive as ISO strings ("2028-07-01" or "2028-07-01T00:00:00"). */
function isoDate(names: NamesJson, name: string): string {
  const v = nameValue(names, name);
  if (typeof v === "string") {
    const m = /^(\d{4}-\d{2}-\d{2})/.exec(v);
    if (m) return m[1];
  }
  throw new Error(`${name}: se esperaba una fecha ISO, llegó ${JSON.stringify(v)}`);
}

function cell(sheets: SheetsJson, sheet: string, ref: string): unknown {
  const sh = sheets[sheet];
  if (!sh) throw new Error(`Hoja ausente en sheets.json: ${sheet}`);
  const c = sh.cells[ref];
  return c ? c.v : undefined;
}
function cellNum(sheets: SheetsJson, sheet: string, ref: string, dflt?: number): number {
  const v = cell(sheets, sheet, ref);
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (v === undefined || v === null || v === "") { if (dflt !== undefined) return dflt; }
  throw new Error(`${sheet}!${ref}: se esperaba un número, llegó ${JSON.stringify(v)}`);
}

export function inputsFromWorkbookJson(names: NamesJson, sheets: SheetsJson): Inputs {
  // ---- 05_CAPEX rubro table (rows 7–15) + drivers (names Drv_*)
  const dwp = numArr(names, "Drv_Wp"), dwac = numArr(names, "Drv_Wac"), dfx = numArr(names, "Drv_Fijo");
  const rubros: Rubro[] = [];
  for (let k = 0; k < 9; k++) {
    const r = 7 + k;
    rubros.push({
      nombre: String(cell(sheets, "05_CAPEX", `C${r}`) ?? `Rubro ${k + 1}`),
      costo: cellNum(sheets, "05_CAPEX", `D${r}`, 0),
      pctComp: cellNum(sheets, "05_CAPEX", `E${r}`, 0),
      pctExt: cellNum(sheets, "05_CAPEX", `G${r}`, 0),
      arancel: cellNum(sheets, "05_CAPEX", `I${r}`, 0),
      iva: cellNum(sheets, "05_CAPEX", `O${r}`, 0),
      drvWp: dwp[k], drvWac: dwac[k], drvFijo: dfx[k],
    });
  }
  const iva_fee = cellNum(sheets, "05_CAPEX", "O18");

  // ---- 04_Energia consumption tables
  const col12 = (c: string, r0: number) => Array.from({ length: 12 }, (_, m) => cellNum(sheets, "04_Energia", `${c}${r0 + m}`, 0));
  const col5 = (c: string, r0: number) => Array.from({ length: 5 }, (_, m) => cellNum(sheets, "04_Energia", `${c}${r0 + m}`, 0));

  const inputs: Inputs = {
    // A
    Potencia_DC: num(names, "Potencia_DC"),
    Ratio_DCAC: num(names, "Ratio_DCAC"),
    Comprador_Terreno: str(names, "Comprador_Terreno") as Inputs["Comprador_Terreno"],
    Usar_Deuda: siNo(names, "Usar_Deuda"),
    Tasa_Descuento: num(names, "Tasa_Descuento"),
    Tasa_Descuento_Equity: num(names, "Tasa_Descuento_Equity"),
    Horizonte: num(names, "Horizonte"),
    Fecha_COD: isoDate(names, "Fecha_COD"),
    Meses_Construccion: num(names, "Meses_Construccion"),
    // B
    Esc_Energia: strArr(names, "Esc_Energia"),
    Esc_Factor_CAPEX: numArr(names, "Esc_Factor_CAPEX"),
    Esc_CAPEX_Fijo_Wp: numOrNullArr(names, "Esc_CAPEX_Fijo_Wp"),
    Esc_Factor_OPEX: numArr(names, "Esc_Factor_OPEX"),
    Esc_Peaje: numArr(names, "Esc_Peaje"),
    Esc_EscTarifa: numArr(names, "Esc_EscTarifa"),
    Esc_Disponibilidad: numArr(names, "Esc_Disponibilidad"),
    Esc_Escalacion_CAPEX: numArr(names, "Esc_Escalacion_CAPEX"),
    // C
    Potencia_Ref: num(names, "Potencia_Ref"),
    Ratio_Ref: num(names, "Ratio_Ref"),
    Densidad_MWp_ha: num(names, "Densidad_MWp_ha"),
    Degradacion_Adicional: num(names, "Degradacion_Adicional"),
    Frac_A: num(names, "Frac_A"), Frac_B: num(names, "Frac_B"), Frac_C: num(names, "Frac_C"),
    Tarifa_A: num(names, "Tarifa_A"), Tarifa_C: num(names, "Tarifa_C"),
    Crecimiento_Consumo: num(names, "Crecimiento_Consumo"),
    Fecha_Peaje: isoDate(names, "Fecha_Peaje"),
    Peaje_kW_mes: num(names, "Peaje_kW_mes"),
    Y_P50: numArr(names, "Y_P50"),
    Y_P90: numArr(names, "Y_P90"),
    CR_Ratio: numArr(names, "CR_Ratio"),
    CR_Loss: numArr(names, "CR_Loss"),
    Perfil_Mensual: numArr(names, "Perfil_Mensual"),
    Consumo_2025_A: col12("D", 17), Consumo_2025_B: col12("E", 17), Consumo_2025_C: col12("F", 17),
    Consumo_2025_EneMay: col5("D", 66), Consumo_2026_EneMay: col5("E", 66),
    // D
    Fase_m1: num(names, "Fase_m1"),
    Fecha_Precios: isoDate(names, "Fecha_Precios"),
    Contingencia_Pct: num(names, "Contingencia_Pct"),
    Contingencia_Frac_IVA: num(names, "Contingencia_Frac_IVA"),
    Fee_Gerencia_Pct: num(names, "Fee_Gerencia_Pct"),
    Asignacion_Compartida: num(names, "Asignacion_Compartida"),
    Exponente_Escala: num(names, "Exponente_Escala"),
    Contrato_Inversion: siNo(names, "Contrato_Inversion"),
    IVA_Recuperable: siNo(names, "IVA_Recuperable"),
    Tasa_IVA: num(names, "Tasa_IVA"),
    FODINFA_Pct: num(names, "FODINFA_Pct"),
    ISD_Pct: num(names, "ISD_Pct"),
    Reemplazo_Anio: num(names, "Reemplazo_Anio"),
    Reemplazo_USD_Wac: num(names, "Reemplazo_USD_Wac"),
    Reemplazo_Pagador: str(names, "Reemplazo_Pagador") as Inputs["Reemplazo_Pagador"],
    Desmantelamiento_Pct: num(names, "Desmantelamiento_Pct"),
    Precio_Terreno_ha: num(names, "Precio_Terreno_ha"),
    Costos_Transaccion_Terreno_Pct: num(names, "Costos_Transaccion_Terreno_Pct"),
    Predial_Terreno: num(names, "Predial_Terreno"),
    Residual_Terreno_Pct: num(names, "Residual_Terreno_Pct"),
    Apreciacion_Terreno: num(names, "Apreciacion_Terreno"),
    rubros, iva_fee,
    // E
    Fee_OM_kWp: num(names, "Fee_OM_kWp"),
    Seguro_kWp: num(names, "Seguro_kWp"),
    Renta_Terreno_ha: num(names, "Renta_Terreno_ha"),
    Tributos_Locales: num(names, "Tributos_Locales"),
    Escalacion_OPEX: num(names, "Escalacion_OPEX"),
    // F
    Pct_Apalancamiento: num(names, "Pct_Apalancamiento"),
    Tasa_Deuda: num(names, "Tasa_Deuda"),
    Plazo_Deuda: num(names, "Plazo_Deuda"),
    Gracia_Deuda: num(names, "Gracia_Deuda"),
    IDC_Frac_Tramo0: num(names, "IDC_Frac_Tramo0"),
    DSCR_Objetivo: num(names, "DSCR_Objetivo"),
    Deuda_Financia_Terreno: siNo(names, "Deuda_Financia_Terreno"),
    // G
    Tasa_IR: num(names, "Tasa_IR"),
    Tasa_Participacion: num(names, "Tasa_Participacion"),
    Incluir_Participacion: siNo(names, "Incluir_Participacion"),
    Escudo_Negativo: siNo(names, "Escudo_Negativo"),
    Utilidad_Gravable_SALELGI: numOrNull(names, "Utilidad_Gravable_SALELGI"),
    Vida_Fiscal_Equipos: num(names, "Vida_Fiscal_Equipos"),
    Vida_Fiscal_Civil: num(names, "Vida_Fiscal_Civil"),
    Aplica_DedAd: siNo(names, "Aplica_DedAd"),
    Pct_Elegible_DedAd: num(names, "Pct_Elegible_DedAd"),
    Ingresos_SALELGI: num(names, "Ingresos_SALELGI"),
    Tope_DedAd_Pct: num(names, "Tope_DedAd_Pct"),
    // H
    Costo_Gerencia_Pct: num(names, "Costo_Gerencia_Pct"),
    Costo_OM_Exergy_kWp: num(names, "Costo_OM_Exergy_kWp"),
    Tasa_Efectiva_Exergy: num(names, "Tasa_Efectiva_Exergy"),
    // 10_Sensibilidad
    Sens_CAPEX: num(names, "Sens_CAPEX"),
    Sens_Tarifa: num(names, "Sens_Tarifa"),
    Sens_OPEX_Up: num(names, "Sens_OPEX_Up"),
    Sens_OPEX_Dn: num(names, "Sens_OPEX_Dn"),
    Sens_Peaje: num(names, "Sens_Peaje"),
    Sens_EscTarifa: num(names, "Sens_EscTarifa"),
    Sens_Disponibilidad: num(names, "Sens_Disponibilidad"),
    Sens_EscCAPEX: num(names, "Sens_EscCAPEX"),
    Sens_Peaje_kW: num(names, "Sens_Peaje_kW"),
    Sweep_AC_Fija: num(names, "Sweep_AC_Fija"),
    Mat_CAPEX: numArr(names, "Mat_CAPEX"),
    Mat_Tarifa: numArr(names, "Mat_Tarifa"),
    Sens_Tasas: numArr(names, "Sens_Tasas"),
    Sens_Plazos: numArr(names, "Sens_Plazos"),
    Sens_Lev: numArr(names, "Sens_Lev"),
    Sweep_P: numArr(names, "Sweep_P"),
    Sweep_Ratio: numArr(names, "Sweep_Ratio"),
    Sweep_Lev: numArr(names, "Sweep_Lev"),
  };
  return inputs;
}
