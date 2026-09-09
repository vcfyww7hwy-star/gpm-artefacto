# -*- coding: utf-8 -*-
"""Hojas núcleo v1.2: Supuestos, Energía, CAPEX, OPEX, Fiscal, Flujo, Exergy, Motor_Sens.
Cambios v1.2: fila t referenciada (no literal), dimensionamiento por MWp y ratio DC/AC (yield × recorte), CAPEX por drivers Wp/Wac/fijo,
selector del comprador del terreno, IDC sobre el tramo de construcción, guardas de deuda, escenarios nombrados, columna de valor base."""
import json, os, inspect
from datetime import date
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from xl_helpers import *

S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, SM = (
    "00_Portada", "01_Supuestos", "02_Legal", "03_Tramites", "04_Energia", "05_CAPEX", "06_OPEX",
    "07_Fiscal", "08_Flujo", "09_Exergy", "10_Sensibilidad", "11_Riesgos", "12_Fuentes", "13_Controles", "Motor_Sens")
NSHEETS = 16
VERSION = "v3.1"
FECHA_ANALISIS = date(2026, 9, 8)
# v3.1 (actualización legal, doc 18): fuentes verificadas del Proyecto «Marco Legal FV Ecuador — Exergy» (Atlas Regulatorio FV Ecuador v2.0, sello 08-sep-2026)
ATLAS_SELLO = "Atlas Regulatorio FV Ecuador v2.0 (sello 08-sep-2026)"
# ESC_DEF (entorno): "v30" = definición v3.0 (política del Base B, doc 13) · "v20" = definición v2.0 + parámetros de la ronda 2 en neutro
# (prueba de invariancia R1 frente a gen_v20_calc) · "v13" = definición v1.3 + neutro (prueba histórica R1 de la ronda 1)
ESC_DEF = os.environ.get("ESC_DEF", "v30")
NEUTRO = ESC_DEF in ("v20", "v13")   # parámetros nuevos de la ronda 2 en su valor neutro (≡ v2.0)
# v3.1: CUSTOM_DEF=v30 reproduce las entradas entregadas en la v3.0 (prueba de invariancia del Motor: 110 casos idénticos por etiqueta);
#       v31 (defecto) carga los 10 valores del Custom fijados por Jorge en el libro raíz (04-sep-2026 22:41, SHA ff4443b9…; doc 17 D1 / doc 18 §5.2)
V31 = os.environ.get("CUSTOM_DEF", "v31") != "v30"
T_MIN, T_MAX = -1, 25
COL0 = 4  # D = t=-1
TS = list(range(T_MIN, T_MAX + 1))
LAST_T_COL = COL0 + len(TS) - 1  # AD = 30


def C(t):
    return col(COL0 + (t + 1))


def rng(row, t1=T_MIN, t2=T_MAX):
    return f"${C(t1)}${row}:${C(t2)}${row}"


# ---------------------------------------------------------------- LAYOUT (filas fijas compartidas entre hojas)
# 04 v1.3: p1 resumen (5–13) + T1 consumo (15–29) · p2 T2 producción/inyección (31–45) + gráfico y T3 valor (47–62) · p3 bloques técnicos (64–86) · serie anual (88…)
ENERGIA = dict(res_sec=5, res0=6, t1_sec=15, t1_hdr=16, t1_0=17, t1_tot=29, t2_sec=31, t2_hdr=32, t2_0=33, t2_tot=45, val_sec=47, t3_hdr=48, t3_0=49, t3_tot=61,
               tec_sec=64, serie_sec=88, t=89, y50=91, y90=92, p50=93, p90=94, activa=95, eval=96, norec=97, yld=98, frac=99, degr=100, lost=101)   # v3.0: lost = energía perdida por indisponibilidad y degradación adicional (informativa)
CAPEX = dict(hdr=6, r0=7, cont=16, sub=17, fee=18, tot=19, tot_iva=20, terreno=21, tot_terr=22, aran=23, civil=24)
OPEX = dict(sec_comp=5, comp0=7, sec_serie=14, t=15, fee=18, seg=19, arr=20, pred=21, trib=22, total=23, unit=24, memo_sec=26, memo_cost=27, memo_predial=28)
# v3.0: + decom (desmantelamiento), deprep (depreciación del reemplazo), pool / pool_l (pérdidas arrastradas, M-b) → secA 15–32, secB 34–36, secC 38–46, totales 48
# v3.0 (V4 · render r2): «Totales del horizonte» pasa a la primera página (tras el panel) y la serie empieza en la fila 18 → el salto de fila queda
# antes de la fila de años y las páginas de años (M:U, V:AD) no se partan: 07 imprime 4 páginas (antes 6)
FISCAL = dict(panel_sec=5, panel0=7, tot_sec=12, t=18, secA=21, ahorro=22, opex=23, peaje=24, decom=25, ebitda=26, depeq=27, depciv=28, deprep=29, utap=30, part=31, utair=32, dedad=33, base=34, pool=35, ir=36, imp=37, tasa=38,
              secB=40, iva_pag=41, iva_rec=42, secC=44, int=45, utap_l=46, part_l=47, base_l=48, pool_l=49, ir_l=50, imp_l=51, escudo=52)
# v3.0: + rep (reemplazo de inversores pagado por SALELGI) entre imp y resid; la mini-tabla de los cuatro casos se mantiene hasta V3
FLUJO = dict(kpi_sec=5, kpi_hdr=6, kpi0=7, t=28, secA=31, capex=32, terr=33, iva_pag=34, iva_rec=35, ahorro=36, opex=37, peaje=38, imp=39, rep=40, resid=41, fcf=42, acum=43, df=44, fcfd=45, acumd=46,
             secB=48, scal=49, desemb=51, saldo_ini=52, int=53, amort=54, serv=55, saldo_fin=56, idc=57, cfads=58, dscr=59, eq=60, acum_eq=61, chart=63)
FLUJO = {k: (v + 15 if v >= 28 else v) for k, v in FLUJO.items()}   # v3.0 (V3): gráficos (28–41, página 1) · sin mini-tabla: la serie empieza en 43 (enlace «los cuatro casos → 10 §A» junto a los indicadores)
FLUJO.update(chart=28)
# v3.0: + rep (reemplazo de inversores a cargo de Exergy) entre costoom y util
EXERGY = dict(kpi_sec=5, kpi_hdr=6, kpi0=7, t=22, sec=25, fee=26, costo=27, terreno=28, arr=29, predial=30, feeom=31, costoom=32, rep=33, util=34, imp=35, resid=36, fcf=37, acum=38, df=39,
              sens_sec=41, ann=42, sens_hdr=44, sens0=45, grupo_sec=55, g_sal=56, g_ex=57, g_tot=58, g_tir=59, g_van=60, g_note=61, alt_sec=63, alt0=64)
EXERGY = {k: (v + 13 if v >= 22 else v) for k, v in EXERGY.items()}   # v3.0 (V3): gráfico (16–33, página 1) · sin mini-tabla: la serie empieza en 35
EXERGY.update(chart=16)

SUB = "Modelo financiero-legal FV Montecristi → Gran Piazza Machala (SALELGI S.A.) · Exergy EXG S.A.S. · USD nominal · v1.3 · 2026-09-02"

# Vectores canónicos (pvlib verificado 2026-07-15; no recalcular). Se convierten a yield específico (kWh/kWp) a la potencia y ratio de referencia (5.000 kWp · 1,32).
P50 = [6470, 6434, 6398, 6363, 6328, 6294, 6259, 6224, 6190, 6156, 6122, 6088, 6055, 6022, 5988, 5956, 5923, 5890, 5858, 5826, 5794, 5762, 5730, 5698, 5668, 5636, 5605, 5574, 5544, 5513]
P90 = [5777, 5746, 5714, 5682, 5651, 5620, 5589, 5558, 5528, 5498, 5467, 5437, 5407, 5378, 5348, 5318, 5289, 5260, 5231, 5202, 5174, 5145, 5117, 5089, 5061, 5033, 5006, 4978, 4950, 4923]
P_REF_KWP = 5000
Y50 = [v * 1000 / P_REF_KWP for v in P50]
Y90 = [v * 1000 / P_REF_KWP for v in P90]
P50_MES = [483, 457, 601, 612, 584, 513, 515, 550, 566, 552, 520, 515]
_s = sum(P50_MES)
PERFIL_MES = [m / _s for m in P50_MES]
PERFIL_MES[-1] = 1.0 - sum(PERFIL_MES[:-1])
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
CONS_2025 = [
    (446567, 167437, 147239), (445456, 163876, 103577), (528493, 189963, 112955), (483688, 172788, 116259),
    (427713, 150902, 157331), (399193, 143589, 101484), (413141, 148133, 126180), (403264, 149194, 159436),
    (418387, 153301, 142790), (406505, 151709, 156013), (409517, 157679, 189620), (487536, 180500, 177080)]
CONS_2026_ENE_MAY = [860360, 808678, 935781, 945198, 920189]
CONS_2025_ENE_MAY = [761243, 712909, 831411, 772735, 735946]
CURVA_RECORTE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "curva_recorte.json")))  # [{ratio, clipping}]


def f_loss(rcell):
    """Pérdida por recorte interpolada linealmente en la tabla CR_Ratio/CR_Loss para el ratio dado (expresión Excel)."""
    rc = f"MIN(MAX({rcell},INDEX(CR_Ratio,1)),INDEX(CR_Ratio,ROWS(CR_Ratio)))"
    m = f"MIN(MATCH({rc},CR_Ratio,1),ROWS(CR_Ratio)-1)"
    return f"(INDEX(CR_Loss,{m})+({rc}-INDEX(CR_Ratio,{m}))*(INDEX(CR_Loss,{m}+1)-INDEX(CR_Loss,{m}))/(INDEX(CR_Ratio,{m}+1)-INDEX(CR_Ratio,{m})))"


# ---------------------------------------------------------------- utilidades temporales
def time_header(ws, row, extra_cols=0, label_txt="Año (t)"):
    """Fila t (crema, regla dorada) + fila de año calendario (piedra). Las fórmulas de la hoja referencian esta fila (v1.2)."""
    for c in range(2, COL0 + len(TS) + extra_cols):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, bold=True, size=9, color=GRAFITO)
        cell.alignment = Alignment(horizontal="center", vertical="center"); cell.border = B_HDR
    ws.cell(row=row, column=2, value=label_txt).alignment = Alignment(horizontal="left", vertical="center")
    for t in TS:
        ws.cell(row=row, column=COL0 + (t + 1), value=t)
    for k in range(extra_cols):
        t = T_MAX + 1 + k
        cell = ws.cell(row=row, column=COL0 + (t + 1), value=t); cell.font = Font(name=FONT, bold=True, size=9, color=GRAFITO)
    ws.cell(row=row + 1, column=2, value="Año calendario (inicio del período)").font = font(size=8.5, color=GRAFITO)
    for t in list(TS) + [T_MAX + 1 + k for k in range(extra_cols)]:
        cell = ws.cell(row=row + 1, column=COL0 + (t + 1), value=f"=YEAR(EDATE(Fecha_COD,12*({C(t)}${row}-1)))")
        cell.font = font(size=8.5, color=GRAFITO); cell.alignment = Alignment(horizontal="center"); cell.number_format = "0"
    ws.row_dimensions[row].height = 18
    ws.row_dimensions[row + 1].height = 14


def row_formula(ws, row, label_txt, fn, fmt=FMT_USD, bold=False, color=CARBON, fill_hex=None, unit_txt=None, ts=TS, total=False, size=9, trow=None):
    """fn(t) o fn(t, T) donde T es la referencia a la celda de la fila t de la misma columna (p. ej. E$28)."""
    label(ws, row, 2, label_txt, bold=bold, size=10 if not total else 10)
    if unit_txt:
        unit(ws, row, 3, unit_txt)
    else:
        ws.cell(row=row, column=3).border = B_BOTTOM
    two = len(inspect.signature(fn).parameters) >= 2
    for t in ts:
        T = f"{C(t)}${trow}" if trow else str(t)
        calc(ws, row, COL0 + (t + 1), fn(t, T) if two else fn(t), fmt=fmt, bold=bold, color=color, fill_hex=fill_hex, size=size)
    if total:
        for c in range(2, LAST_T_COL + 1):
            ws.cell(row=row, column=c).border = Border(top=rule_thin, bottom=hair)
            ws.cell(row=row, column=c).font = Font(name=FONT, bold=True, size=ws.cell(row=row, column=c).font.size, color=CARBON)
    return row


def years_in_section(ws, row, trow):
    """Fila de años repetida al inicio de un bloque: escribe =X$t en la propia fila de sección (fondo bruma)."""
    for t in TS:
        cc = COL0 + (t + 1)
        cell = ws.cell(row=row, column=cc, value=f"={C(t)}${trow}")
        cell.font = Font(name=FONT, bold=True, size=9, color=GRAFITO)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.number_format = "0"
    ws.cell(row=row, column=3, value="t →").font = Font(name=FONT, size=8.5, color=GRAFITO)
    ws.cell(row=row, column=3).alignment = Alignment(horizontal="right", vertical="center")


def series_layout(ws, trow, breaks_t=(7, 16), scale=82, summary_last_col=12, last_row=None, split=True, row_breaks=(), summary_last_row=None, series_last_row=None):
    """Retícula común de las series anuales (D3): años 11–25 agrupados con +/− (desplegados); impresión a escala fija (Excel ignora
    los saltos manuales en modo «ajustar») con tres páginas de años (−1…7 | 8…16 | 17…25) y las columnas de etiqueta (B:C) repetidas.
    Área de impresión en dos rangos: A1:L{última} (resumen + primera página de años, paginado con los saltos de fila indicados) y
    M{t}:AD{última} (años 8…25, sólo desde la fila de años) → las filas del resumen no se repiten vacías en las páginas de años.
    `summary_last_row` (compatibilidad) añade un salto de fila tras esa fila. Escala 82 % ⇒ 9 pt se leen a ≈ 7,4 pt (v1.2: 35–40 %)."""
    from openpyxl.worksheet.pagebreak import Break
    ws.column_dimensions.group(C(11), C(T_MAX), outline_level=1, hidden=False)
    for t in breaks_t:
        ws.col_breaks.append(Break(id=COL0 + (t + 1)))
    rbs = list(row_breaks) + ([summary_last_row] if summary_last_row else [])
    for rb in sorted(set(rbs)):
        ws.row_breaks.append(Break(id=rb))
    last = last_row or ws.max_row
    # v3.0 (V4): el segundo rango (años 8…25) termina en la última fila de la serie, no en la última fila de la hoja → las tablas de resumen que siguen
    # a la serie (totales de 07, palancas y grupo de 09) no se imprimen vacías en las páginas de años
    area = f"A1:{col(summary_last_col)}{last},{C(breaks_t[0] + 1)}{trow}:{C(T_MAX)}{series_last_row or last}"
    setup_print(ws, landscape=True, title_cols="B:C", scale=scale, area=area)


def time_widths(ws, label_w=38):
    """Excel/Mac imprime 6,05 pt por carácter de ancho XML: A2 + B38 + C6 + 9 años × 11 = 145 → 877 pt → 82 % = 719 pt < 772 pt útiles."""
    widths(ws, {"A": 2, "B": min(label_w, 38), "C": 6})
    for c in range(COL0, LAST_T_COL + 6):
        ws.column_dimensions[col(c)].width = 11.0


# ---------------------------------------------------------------- 01_Supuestos
# (sección | nombre | etiqueta | valor | unidad | formato | por_confirmar | nota)  ·  valor "=…" = calculada (gris)  ·  INFO_INPUTS = informativos
INFO_INPUTS = {"Meses_Recup_IVA"}
INPUTS = [
    ("A · General y tiempo", None, None, None, None, None, None, None),
    (None, "Version", "Versión del libro", VERSION, "texto", None, False, "Se muestra en cabeceras y pies de página."),
    (None, "Fecha_Analisis", "Fecha de corte del análisis", FECHA_ANALISIS, "fecha", FMT_DATE, False, "Fecha de corte del análisis (v3.1, 08-sep-2026). Marco legal, fiscal y de permisos conciliado con el Atlas Regulatorio FV Ecuador v2.0 (sello 08-sep-2026; Proyecto «Marco Legal FV Ecuador — Exergy»); fuentes web verificadas por última vez el 08-sep-2026. Alimenta las cabeceras de todas las hojas."),
    (None, "Fecha_COD", "Fecha objetivo de inicio de operación (COD)", date(2028, 7, 1), "fecha", FMT_DATE, True, "P10 (defecto): ruta crítica 18–32 meses desde sep-2026 (S3, 21-jul-2026) → 2028-Q1…2029-Q1; se adopta 2028-H2. Mueve el año calendario y la fracción del año con peaje."),
    (None, "Horizonte", "Horizonte de evaluación", 25, "años", "0", False, "Decisión previa (libros v2.0/v3.1). Vectores de energía disponibles a 30 años; años > horizonte valen 0."),
    (None, "Tasa_Descuento", "Tasa de descuento nominal USD", 0.10, "%", FMT_PCT, False, "Decisión previa. VAN adicional a las tasas alternas de abajo."),
    (None, "Tasa_Desc_Alt1", "Tasa de descuento alterna 1", 0.08, "%", FMT_PCT, False, "Solo para VAN alterno (08_Flujo)."),
    (None, "Tasa_Desc_Alt2", "Tasa de descuento alterna 2", 0.12, "%", FMT_PCT, False, "Solo para VAN alterno (08_Flujo)."),
    (None, "Tasa_Descuento_Equity", "Tasa de descuento del accionista (VAN del flujo con deuda)", ("=Tasa_Descuento" if NEUTRO else 0.12), "%", FMT_PCT, False, "Ronda 2 (M-g, decisión d5 04-sep-2026): 12 % = tasa del proyecto + prima por el apalancamiento (70 % · 9 %). Sólo descuenta el flujo del accionista (VAN_Equity, 08 y Motor); la TIR del accionista no depende de ella. Neutro = Tasa_Descuento."),
    (None, "Meses_Construccion", "Duración de la construcción (t = −1 y 0) para los intereses capitalizados", (12 if NEUTRO else "=Mes_COD_Cron"), "meses", "0", False, "Ronda 2 (M-e): los intereses durante la construcción (IDC) escalan con la duración real del cronograma de 03_Tramites (Mes_COD_Cron = mes del COD): IDC = D × tasa × (Fase_m1 + (1 − Fase_m1) × IDC_Frac_Tramo0) × meses / 12. Fórmula, no dato (una sola fuente: 03). El motor anual sigue comprimiendo la construcción en t = −1 y 0."),
    ("A2 · Dimensionamiento (potencia, ratio DC/AC, terreno, red)", None, None, None, None, None, None, None),
    (None, "Potencia_DC", "Potencia DC instalada", 5000, "kWp", FMT_INT, False, "Mando maestro 1. Lista 5.000 / 6.000 / 7.000 / 8.000 kWp (v2.0): 5.000 = alcance mínimo fijado por Jorge (01-09-2026); por encima de ≈ 7,4 MWp aparecen excedentes mensuales (junio) y el tope anual del art. 9 se alcanza en 8,05 MWp. Escala energía, CAPEX (drivers 05), OPEX, terreno, deuda y negocio Exergy. Compartida por los cuatro casos. Barrido 5–8 MWp en 10 §F."),
    (None, "Ratio_DCAC", "Ratio DC/AC (potencia módulos / potencia inversores)", 1.32, "×", "0.00", False, "Mando maestro 2. Diseño actual 5.000 kWp / 3.788 kWac. Mueve la energía (curva de recorte pvlib, 04), el CAPEX por Wac (inversores, MT) y la potencia AC frente al alimentador. Barrido 1,10–1,50 en 10 §F."),
    (None, "Potencia_AC", "Potencia AC nominal (calculada)", "=Potencia_DC/Ratio_DCAC", "kWac", FMT_INT, False, "Cálculo: Potencia_DC / Ratio_DCAC. Rubro CNEL: USD 4/kW con tope 10.000 (> 2 MW). Candado art. 7.a frente a Capacidad_Alimentador_kW."),
    (None, "Potencia_Ref", "Potencia de referencia del estudio CAPEX y de la simulación de energía", 5000, "kWp", FMT_INT, False, "Base a la que están cotizados los 9 rubros (estudio CAPEX/OPEX jul-2026) y simulado el yield (pvlib jul-2026). No editar salvo recalibración."),
    (None, "Ratio_Ref", "Ratio DC/AC de la simulación de referencia", 1.32, "×", "0.00", False, "La curva de recorte se aplica en forma relativa: f(Ratio_DCAC) / f(Ratio_Ref)."),
    (None, "Yield_Ref", "Yield específico P50 año 1 a la referencia (calculado)", "=INDEX(Y_P50,1,1)", "kWh/kWp", FMT_INT, False, "Cálculo: INDEX(Y_P50, 1) = 6.470 MWh / 5.000 kWp (pvlib sobre TMY Solargis adaptado, 15-jul-2026; PR ≈ 82 %)."),
    (None, "Densidad_MWp_ha", "Ocupación del terreno", 1.0, "MWp/ha", "0.00", False, "Decisión Jorge (01-09-2026): 1 MWp por hectárea."),
    (None, "Hectareas", "Terreno requerido (calculado)", "=Potencia_DC/1000/Densidad_MWp_ha", "ha", "0.00", False, "Cálculo: Potencia_DC / Densidad. 5 ha en el caso base."),
    (None, "Ha_Disponibles", "Superficie disponible del predio", 10.78, "ha", "0.00", False, "Predio Montecristi (dos proyectos de 5 MWp). Candado ▲ si Hectareas > disponibles."),
    (None, "Capacidad_Alimentador_kW", "Capacidad de inyección aprobable en el punto de conexión 13,8 kV", 3800, "kW", FMT_INT, True, "POR CONFIRMAR con la Factibilidad de Conexión de CNEL (art. 7.a 005/24: la potencia nominal se limita a la capacidad de la red aprobada por la Distribuidora). Defecto = diseño actual; el candado avisa ■ si Potencia_AC la supera."),
    (None, "Tope_SGDA_kW", "Tope regulatorio de potencia para SGDA de consumidor regulado (vacío = sin tope)", None, "kW", FMT_INT, False, "Verificado 02-sep-2026 en la 005/24 codificada (Res. 010/2024): NO existe tope absoluto; Cat. 1 ≤ 100 kW, Cat. 2 > 100 kW; > 1 MW exige estudios de estabilidad (13.5.m). Se deja vacío."),
    (None, "Exponente_Escala", "Economías de escala en los componentes por Wp/Wac: costo ∝ (P/P_ref)^(1−ε)", 0.0, "ε", "0.00", False, "Decisión Jorge D3 (02-sep-2026): 0 = lineal (ácido). Sensibilidad 0,05–0,10 si hay cotizaciones a otra escala."),
    ("B · Energía (yield canónico y curva de recorte en 04_Energia)", None, None, None, None, None, None, None),
    (None, "Frac_A", "Fracción de la inyección en bloque A (08h-18h)", 0.967, "%", FMT_PCT, False, "Derivado del TMY P50 adaptado (GHI horario): 96,7 % de la irradiación anual cae 08-18h. Aproximación: la energía AC sigue la irradiación (ligera sobre-ponderación de horas centrales → conservador para el bloque C)."),
    (None, "Frac_B", "Fracción en bloque B (18h-22h)", 0.002, "%", FMT_PCT, False, "TMY: 0,2 % (17h-18h y 18h-19h en horario solar). Cargo = bloque A (0,113), igual que en el pliego (08h-22h)."),
    (None, "Frac_C", "Fracción en bloque C (22h-08h)", 0.031, "%", FMT_PCT, False, "TMY: 3,1 % (06h-08h). Cargo nocturno 0,105 $/kWh. Suma A+B+C = 100 % (control en 13)."),
    ("C · Consumo y tarifa del medidor (SALELGI · AV1 · CNEL El Oro)", None, None, None, None, None, None, None),
    (None, "Tarifa_A", "Cargo de energía 08h00–22h00 (bloques A y B)", 0.113, "$/kWh", FMT_KWH, False, "Res. ARCONEL-006/25 (30-jun-2025), vigente desde consumo jul-2025; ratificado pliego 2026 (Res. 029/25, 31-dic-2025). Verificado en 19 planillas (análisis 17-jul-2026)."),
    (None, "Tarifa_C", "Cargo de energía 22h00–08h00 (bloque C)", 0.105, "$/kWh", FMT_KWH, False, "Pliego tarifario 2026 (Res. ARCONEL-029/25), tarifa AV1 general comercial horaria, cargo nocturno; verificado en las 19 planillas (17-jul-2026)."),
    (None, "Cargo_Demanda", "Cargo por demanda (no evitable — informativo)", 4.40, "$/kW-mes", FMT_DEC2, False, "× FGD (0,60–1,00). El SGDA remoto NO reduce la demanda del medidor (art. 27.2 005/24)."),
    (None, "Cargo_Comercializacion", "Cargo de comercialización (no evitable)", 1.414, "$/mes", FMT_DEC2, False, "Informativo."),
    (None, "SAPG_mes", "Alumbrado público SAPG (no evitable)", 300, "$/mes", FMT_INT, False, "Observado constante en las 19 planillas."),
    (None, "Crecimiento_Consumo", "Crecimiento anual de la demanda del medidor", 0.0, "%/año", FMT_PCT, False, "Ácido: 0 %. Afecta el tope del art. 9 (energía valorizable ≤ demanda) y la cobertura; relevante en los barridos por MWp."),
    (None, "Fecha_Peaje", "Fecha de inicio del peaje SGDA", date(2029, 2, 28), "fecha", FMT_DATE, False, "Disp. Transitoria Cuarta 005/24 codificada (verbatim; Auditoría D-07): los SGDA pagan peajes «desde el 28 de febrero de 2029». Matiz: el D.E. 176 (RLOCE) DT 16.ª cuenta 5 años desde su expedición (23-feb-2029); prevalece la fecha regulatoria. Atlas N20 · confianza alta."),
    (None, "Peaje_kW_mes", "Peaje SGDA por potencia (sobre la potencia AC nominal, desde Fecha_Peaje)", 0.0, "$/kW-mes", FMT_DEC2, True, "Ronda 2 (M-h): el art. 5.17 de la Res. ARCONEL-005/24 codificada define el peaje SGDA con «valores por potencia y energía»; el componente por potencia no está publicado. Base 0 (sin dato); 0,5 y 1,0 $/kW-mes en el tornado (10 §B). Se suma al peaje por energía ($/kWh, bloque B) sobre Potencia_AC × 12 × fracción del año con peaje."),
    (None, "Degradacion_Adicional", "Degradación anual adicional sobre el yield canónico", (0.01 if V31 else 0.0), "%/año", FMT_PCT2, False, "Ronda 2 (M-d): el vector canónico pvlib (jul-2026) ya incorpora ≈ 0,55 %/año; esta entrada añade (1 − d)^(t−1) sobre él para sensibilizar módulos peores o suciedad no recuperada. v3.1: 1 %/año (valor fijado por Jorge en el libro raíz, 04-sep-2026; entregado v3.0: 0). Compartida por los cuatro casos."),
    ("D · CAPEX (detalle rubro a rubro y drivers de escala en 05_CAPEX)", None, None, None, None, None, None, None),
    (None, "Fase_m1", "Fracción del CAPEX desembolsada en el año −1", 0.30, "%", FMT_PCT, False, "P10 (defecto): 30 % (desarrollo + anticipos de equipos) / 70 % en el año 0 (construcción). Estándar 30/70 en procura (estudio CAPEX)."),
    (None, "Fecha_Precios", "Fecha de los precios del CAPEX bottom-up (base de la escalación)", date(2026, 7, 22), "fecha", FMT_DATE, False, "Ronda 2 (M-a): los 9 rubros de 05 están cotizados al deck v4 (22-jul-2026). La escalación del bloque B (Escalacion_CAPEX, %/año) se aplica desde esta fecha hasta cada desembolso: Anios_Precios − 1 años para el tramo −1 y Anios_Precios para el tramo 0 (Factor_Escalacion en 05)."),
    (None, "Reemplazo_Anio", "Año de operación del reemplazo de inversores", 13, "t", "0", False, "Ronda 2 (M-c): vida útil típica de inversores string 10–15 años; base t = 13. El reemplazo se deprecia en 10 años (o hasta el horizonte) si lo paga SALELGI; rango 5–24 (control H11)."),
    (None, "Reemplazo_USD_Wac", "Costo del reemplazo de inversores por Wac", 0.06, "$/Wac", FMT_DEC2, True, "Ronda 2 (M-c): 0,06 $/Wac × Potencia_AC ≈ 6 % del CAPEX (precio de inversores string 2035 estimado, sin instalación mayor). POR CONFIRMAR con cotización; 0 = sin reemplazo."),
    (None, "Reemplazo_Pagador", "Quién paga el reemplazo de inversores", ("No" if NEUTRO else "SALELGI"), "SALELGI / Exergy / No", None, False, "Ronda 2 (M-c, decisión d4 04-sep-2026): SALELGI (dueña del activo; capex en t = Reemplazo_Anio, depreciable) como supuesto de partida; Exergy (reserva dentro del fee de O&M: gasto deducible de Exergy en t = Reemplazo_Anio, sin efecto en SALELGI); No = sin reemplazo (neutro ≡ v2.0). La cláusula real la fija el contrato de O&M; 10 §G compara ambas."),
    (None, "Desmantelamiento_Pct", "Desmantelamiento al final del horizonte (% del CAPEX industrial)", 0.0, "%", FMT_PCT, True, "Ronda 2 (M-c): gasto deducible de SALELGI en t = Horizonte (desmontaje, disposición de módulos, restitución del predio) neto del valor de chatarra. Base 0 (decisión d7); 2 % en el tornado. POR CONFIRMAR (contrato / garantía de recompra de módulos)."),
    (None, "Contingencia_Pct", "Contingencia sobre subtotal de rubros 1-9", 0.06, "%", FMT_PCT, False, "Estudio CAPEX: 5–8 % (sin margen EPC: Exergy gerencia con multi-contrato)."),
    (None, "Contingencia_Frac_IVA", "Fracción de la contingencia gravada con IVA", 0.60, "%", FMT_PCT0, False, "Mezcla de bienes y servicios gravados (antes constante 0,6 embebida en 05_CAPEX; auditoría A-11)."),
    (None, "Fee_Gerencia_Pct", "Fee de gerencia del proyecto (Exergy)", 0.07, "% del valor del proyecto", FMT_PCT, False, "Decisión Jorge (01-09-2026): base 7 % sobre el subtotal EPC (rubros 1-9 + contingencia, sin IVA, sin terreno). Sensibilidad 5/7/9 % en 09_Exergy."),
    (None, "Asignacion_Compartida", "% de los rubros compartibles del sitio (2×5 MWp) cargado a GPM", 1.0, "%", FMT_PCT, False, "P5 (defecto conservador): 100 %. Alternativa 50 % si la segunda planta comparte conexión/cerramiento/caminos."),
    (None, "Contrato_Inversion", "Contrato de Inversión (COPCI) suscrito", "No", "Sí / No", None, False, "P11 (defecto): No. Si Sí → 0 % arancel bienes de capital y 0 % ISD (art. 159.16 Ley Equidad; COPCI); FODINFA se mantiene. La reducción de −5 pts de IR NO aplica a SALELGI (solo nuevas sociedades)."),
    (None, "IVA_Recuperable", "IVA del CAPEX recuperable como crédito tributario", "Sí", "Sí / No", None, True, "P3 (defecto): SALELGI factura arriendos gravados 15 % → crédito tributario (art. 66 LRTI). Si No → IVA se capitaliza y deprecia."),
    (None, "Tasa_IVA", "Tarifa general de IVA", 0.15, "%", FMT_PCT, False, "LRTI art. 65: tarifa general 15 % (vigente desde 01-abr-2024 por el D.E. 198, acto de aplicación); sin cambio en 2026 (Circular SRI 26-dic-2025). Atlas F1/I-12 · el 0 % de módulos y accesorios FV es del art. 55 num. 19 (código Ecuapass 0719)."),
    (None, "FODINFA_Pct", "FODINFA sobre CIF", 0.005, "%", FMT_PCT2, False, "COPCI art. 110 / SENAE."),
    (None, "ISD_Pct", "ISD sobre pagos al exterior", 0.05, "%", FMT_PCT, False, "SRI 2026: tarifa general 5 %; crédito tributario por importaciones eliminado (S4). Costo capitalizable."),
    ("E · OPEX de SALELGI (detalle en 06_OPEX)", None, None, None, None, None, None, None),
    (None, "Fee_OM_kWp", "Fee de O&M todo incluido pagado a Exergy", (16 if V31 else 20), "$/kWp-año", FMT_DEC1, False, "v3.1: 16 $/kWp-año (valor fijado por Jorge en el libro raíz, 04-sep-2026; entregado v3.0: 20 = canon deck v4). Cubre O&M, limpieza, monitoreo, seguridad, repuestos/reserva de inversores y administración técnica; margen de Exergy = fee − Costo_OM_Exergy_kWp. Sensibilidad 18/20/24 en 09."),
    (None, "Seguro_kWp", "Seguros all-risk operativo + RC (pagados por SALELGI como dueño)", 3.5, "$/kWp-año", FMT_DEC1, False, "Estudio CAPEX/OPEX (jul-2026): 2,5–5 $/kWp; ≈0,35–0,5 % del CAPEX. Prima alta por costa C3/C4 y sismo."),
    (None, "Renta_Terreno_ha", "Arriendo del terreno pagado a Exergy (si Exergy es la propietaria)", 5000, "$/ha-año", FMT_USD, False, "Decisión Jorge: valor razonable y atractivo. Base = 10 % de rendimiento bruto sobre 50.000 $/ha (= tasa de descuento → línea terreno ≈ neutra en VAN para Exergy; para SALELGI ≈ 3,4 % del ahorro). Sensibilidad 3.000 / 5.000 / 7.000 en 09."),
    (None, "Tributos_Locales", "Tributos locales y administración (1,5‰ activos, patente incremental, otros)", 8000, "$/año", FMT_USD, True, "ESTIMACIÓN (S4 H.7: 30–50 k/año/proyecto para una SPV; aquí sólo el incremento marginal de SALELGI). Debe cubrir el 1,5 ‰ sobre activos totales (COOTAD art. 553; ≈ 6,2 k$/año sobre 4,1 M de activo nuevo, decreciente con el valor en libros) + patente municipal incremental (USD 10–25.000 según ordenanza) + predial rural (Ordenanza 32-2025 Montecristi). Tablas de Montecristi no públicas (Atlas I-23/I-24). Decisión D-L3 (08-sep-2026): se mantiene 8.000 «por confirmar»."),
    (None, "Escalacion_OPEX", "Escalación anual del OPEX (todas las líneas)", (0.02 if V31 else 0.015), "%/año", FMT_PCT, False, "v3.1: 2 %/año (valor fijado por Jorge en el libro raíz, 04-sep-2026; entregado v3.0: 1,5 %). Estudio CAPEX/OPEX: 1–2 %. Aplica también a la renta del terreno, al predial y al costo de O&M de Exergy."),
    ("E2 · Terreno — quién lo compra y a qué costo", None, None, None, None, None, None, None),
    (None, "Comprador_Terreno", "Comprador del terreno", ("SALELGI" if V31 else "Exergy"), "Exergy / SALELGI", None, False, "v3.1: SALELGI (valor fijado por Jorge en el libro raíz, 04-sep-2026; entregado v3.0: Exergy). SALELGI compra el terreno (CAPEX no depreciable, fuera del fee), paga el predial y no paga arriendo; Exergy pierde la línea terreno. Exergy: compra y arrienda a SALELGI a renta fija (escritura separada, inscribible; Atlas P-12). Comparativo en 10 §G y Portada."),
    (None, "Precio_Terreno_ha", "Precio de compra del terreno", 50000, "$/ha", FMT_USD, False, "Decisión Jorge (01-09-2026). Igual para cualquiera de los dos compradores."),
    (None, "Costos_Transaccion_Terreno_Pct", "Costos de transacción de la compra (alcabala + notaría + registro)", 0.015, "% del precio", FMT_PCT, True, "Alcabala 1 % (COOTAD art. 527-530) + notaría y Registro de la Propiedad ≈ 0,5 % (estimación). Se capitalizan al costo del terreno de quien compra. Decisión Jorge D1 (02-sep-2026)."),
    (None, "Predial_Terreno", "Predial rural y gastos anuales del terreno (los paga el propietario)", 1000, "$/año", FMT_USD, True, "ESTIMACIÓN S4 (<2.000 $/año). Escala con Escalacion_OPEX."),
    (None, "Residual_Terreno_Pct", "Valor residual del terreno al final del horizonte (% del precio)", 1.0, "%", FMT_PCT, False, "Base: el terreno conserva su valor nominal. Lo recupera quien lo posea (SALELGI o Exergy). Sensibilidad 0 %."),
    (None, "Apreciacion_Terreno", "Apreciación anual del terreno (sobre el residual)", 0.0, "%/año", FMT_PCT, False, "Ácido: 0 %. Si > 0, la ganancia (residual − costo) tributa a la tasa efectiva del propietario."),
    ("F · Fiscal (a nivel de SALELGI S.A. — empresa operativa)", None, None, None, None, None, None, None),
    (None, "Tasa_IR", "Impuesto a la Renta sociedades", 0.25, "%", FMT_PCT, False, "LRTI art. 37 (SRI, verificado 21-jul-2026)."),
    (None, "Tasa_Participacion", "Participación laboral sobre utilidad incremental", 0.15, "%", FMT_PCT, False, "Código del Trabajo art. 97. P3 (decisión Jorge): incluida → tasa efectiva marginal 36,25 %."),
    (None, "Incluir_Participacion", "Incluir participación laboral 15 % (SALELGI)", "Sí", "Sí / No", None, False, "Toggle para comparar con los libros previos (que no la incluían). No afecta a Exergy (Tasa_Efectiva_Exergy)."),
    (None, "Escudo_Negativo", "SALELGI tiene utilidad gravable: pérdidas incrementales generan ahorro fiscal", "Sí", "Sí / No", None, True, "P3 (defecto): Sí. Si No → impuestos incrementales nunca negativos (sin arrastre). Gobierna sólo cuando Utilidad_Gravable_SALELGI está vacía (absorción ilimitada)."),
    (None, "Utilidad_Gravable_SALELGI", "Utilidad gravable anual de SALELGI disponible para absorber pérdidas incrementales (vacío = ilimitada)", None, "USD/año", FMT_USD, True, "Ronda 2 (M-b): si tiene valor, la base negativa del proyecto sólo se absorbe hasta este monto cada año; el exceso va a un pool de pérdidas que se amortiza contra bases positivas futuras hasta el 25 % de la base gravable del año (art. 11 LRTI; pool simple, sin la caducidad de 5 años — declarado en 12 §A). Vacío = SALELGI absorbe todo (Escudo_Negativo gobierna). POR CONFIRMAR: dato P3 de la contabilidad de SALELGI; 0 en el tornado («sin absorción fiscal»)."),
    (None, "Vida_Fiscal_Equipos", "Vida fiscal maquinaria y equipos", 10, "años", "0", False, "RALRTI (10 % anual)."),
    (None, "Vida_Fiscal_Civil", "Vida fiscal obra civil", 20, "años", "0", False, "RALRTI (5 % anual edificios/construcciones). Aplica al rubro obra civil. El terreno no se deprecia."),
    (None, "Aplica_DedAd", "Deducción adicional 100 % aplicable (certificación ambiental previa obtenida)", "Sí", "Sí / No", None, True, "v3.1 (doc 18 D-L6): la deducción adicional del art. 10 num. 7 LRTI exige certificación de la Autoridad Ambiental Competente ANTES de la primera declaración que la use (RLRTI art. 28 num. 6 lit. g; D.E. 176 art. 78); el procedimiento no está publicado (Atlas pendiente P-01). Sí = se aplica (Base); No = sin deducción adicional en 07 y en el Motor (caso «Sin deducción adicional» del tornado, 10 §B). POR CONFIRMAR con la certificación."),
    (None, "Pct_Elegible_DedAd", "% del CAPEX elegible para deducción adicional 100 % (maquinaria, equipos y tecnología)", 0.65, "%", FMT_PCT, True, "ESTIMACIÓN: módulos + inversores + estructura + CT/MT + BOS ≈ 60–70 % del CAPEX industrial. Excluye obra civil, montaje, desarrollo, fee y terreno. LRTI art. 10 num. 7 (LOCE, RO 2S 475, 11-ene-2024); tope 5 % de los ingresos confirmado (Atlas I-02); requiere certificación ambiental previa (RLRTI 28.6.g; Aplica_DedAd); el exceso sobre el tope se pierde en el modelo (¿se difiere? Atlas P-14)."),
    (None, "Ingresos_SALELGI", "Ingresos totales anuales de SALELGI (para el tope del 5 %)", 10000000, "USD/año", FMT_USD, True, "P3 (defecto): rango 8–12 M → 10 M. Tope de la deducción adicional = 5 % × ingresos totales (art. 10.7 LRTI; confirmado, Atlas I-02). El exceso sobre el tope se pierde en el modelo (conservador; si se difiere, Atlas P-14). Dato a confirmar con contabilidad de SALELGI."),
    (None, "Tope_DedAd_Pct", "Tope de la deducción adicional (% de ingresos totales)", 0.05, "%", FMT_PCT, False, "LRTI art. 10.7: 'Este gasto adicional no podrá superar un valor equivalente al 5% de los ingresos totales'."),
    (None, "Meses_Recup_IVA", "Meses para absorber el crédito de IVA (informativo, no alimenta cálculos)", 6, "meses", "0", False, "P3 (defecto). En el flujo anual el IVA de cada tramo se recupera en el período siguiente (convención declarada en 12 §C)."),
    ("G · Deuda (SALELGI como deudor · segmento productivo corporativo)", None, None, None, None, None, None, None),
    (None, "Usar_Deuda", "Destacar el caso con deuda en 00_Portada", "Sí", "Sí / No", None, False, "El flujo con y sin deuda se calcula SIEMPRE; el toggle elige qué TIR destaca la segunda fila de tarjetas de la portada."),
    (None, "Pct_Apalancamiento", "Deuda / CAPEX industrial (sin IVA)", (1.0 if V31 else 0.70), "%", FMT_PCT, False, "v3.1: 100 % (valor fijado por Jorge en el libro raíz, 04-sep-2026; entregado v3.0: 70 %, P4). Sensibilidad 50–80 % en 10 §D; deuda máxima para el DSCR objetivo en 10 §H."),
    (None, "Deuda_Financia_Terreno", "¿El banco financia también el terreno cuando lo compra SALELGI?", "No", "Sí / No", None, False, "Decisión Jorge D2 (02-sep-2026): No — el terreno se aporta con capital. Si Sí, la base de la deuda incluye el terreno."),
    (None, "Tasa_Deuda", "Tasa de interés nominal anual", (0.075 if V31 else 0.09), "%", FMT_PCT, False, "v3.1: 7,5 % (valor fijado por Jorge en el libro raíz, 04-sep-2026; entregado v3.0: 9,0 %, P4). Referencia BCE ago-2026 (Atlas J): tasas referenciales corporativo 6,79 % · empresarial 8,62 % · PYME 9,18 %; máximas mar-2026: corporativo 9,33 %; única línea publicada para FV: BanEcuador 11,86 % (PYME, ≤ USD 3 MM, 60 meses, 6 de gracia); Produbanco Líneas Verdes hasta 84 meses. Sensibilidad 7,5–11 % en 10 §D."),
    (None, "Plazo_Deuda", "Plazo total (incluida gracia)", 8, "años", "0", False, "P4: 8 años. Sensibilidad 8/10/12 en 10 (el DSCR mejora a 10 años; a 12 empeora por el fin de la depreciación). Debe ser > gracia y ≤ horizonte (controles 13)."),
    (None, "Gracia_Deuda", "Período de gracia (solo intereses)", 1, "años", "0", False, "P4: 12 meses. Intereses durante construcción (año 0) se capitalizan al saldo."),
    (None, "IDC_Frac_Tramo0", "Fracción de año de intereses capitalizados sobre el tramo desembolsado en el año 0", 0.5, "años", "0.00", False, "Decisión Jorge G2-1 (02-sep-2026): 0,5 = el 70 % se desembolsa a lo largo de la obra (medio año promedio). En v1.1 era 0 (sólo el tramo −1 devengaba). IDC = D × [Fase_m1 × tasa + (1 − Fase_m1) × tasa × esta fracción]."),
    (None, "DSCR_Objetivo", "DSCR mínimo objetivo (umbral bancario)", 1.20, "x", FMT_X, False, "Regla típica de bancabilidad. Alimenta los avisos y la deuda máxima sostenible (10 §H). Antes constante embebida (auditoría A-11)."),
    ("H · Negocio Exergy (gerencia · terreno · O&M)", None, None, None, None, None, None, None),
    (None, "Costo_Gerencia_Pct", "Costo interno de Exergy por gerenciar el proyecto", 0.025, "% del valor del proyecto", FMT_PCT, True, "ESTIMACIÓN (equipo, ingeniería de dueño, viajes, legal): 2,5 % → margen neto de gerencia ≈4,5 pts."),
    (None, "Costo_OM_Exergy_kWp", "Costo propio de Exergy por operar el SGDA", 16, "$/kWp-año", FMT_DEC1, False, "Estudio CAPEX/OPEX mín. 16 $/kWp (modelo interno v2.0). Margen O&M = fee − costo."),
    (None, "Tasa_Efectiva_Exergy", "Tasa efectiva de impuestos de Exergy (participación 15 % + IR 25 %)", 0.3625, "%", FMT_PCT2, False, "15 % + 25 % × 85 % = 36,25 %. Independiente del toggle de participación de SALELGI (auditoría A-12)."),
    ("J · Umbrales y tolerancias de los controles", None, None, None, None, None, None, None),
    (None, "Umbral_Riesgo_Alto", "Score de riesgo (prob × impacto) desde el que un riesgo es ALTO", 6, "puntos", "0", False, "11_Riesgos (antes constante embebida)."),
    (None, "Umbral_Riesgo_Medio", "Score desde el que un riesgo es MEDIO", 3, "puntos", "0", False, "11_Riesgos."),
    (None, "Tol_Costo_Tramites", "Tolerancia del cronograma valorado frente al rubro 9 del CAPEX", 0.05, "%", FMT_PCT, False, "03_Tramites control «cabe en el rubro 9»."),
    (None, "Tol_Dias_COD", "Tolerancia entre el COD del cronograma y Fecha_COD", 45, "días", "0", False, "03_Tramites y 13_Controles."),
]
SELECTORS = {"Comprador_Terreno": '"Exergy,SALELGI"', "Potencia_DC": '"5000,6000,7000,8000"', "Escenario_Energia": '"P50,P90"', "Reemplazo_Pagador": '"SALELGI,Exergy,No"'}

# ---------------------------------------------------------------- 01_Supuestos · bloque B (v2.0): supuestos de escenario, cuatro columnas Custom · Conservador · Base · Favorable
# (nombre del Custom | nombre del rango de 4 | etiqueta | unidad | formato | {X, C, B, F} | por_confirmar | nota)
# Los cuatro casos comparten TODO lo demás (capa de diseño). Custom nace igual al Base. Definición revisada (doc 11 §1.2, aprobada 03-sep-2026):
#   Conservador = P90 · CAPEX ×1,15 · OPEX ×1,15 · peaje 1,5 ¢/kWh · tarifa plana      Base = P50 · costo real · peaje 0,5 ¢ · plana
#   Favorable   = P50 · CAPEX fijo 0,75 $/Wp (deck v4) · OPEX ×1 · sin peaje · +2 %/año
_V13 = ESC_DEF == "v13"
ESCENARIOS = [
    ("Escenario_Energia", "Esc_Energia", "Energía del caso (yield canónico de 04)", "P50 / P90", None, {"X": "P50", "C": "P90", "B": "P50", "F": "P50"}, False,
     "P50 = mediana de pvlib sobre TMY Solargis adaptado (15-jul-2026); P90 = percentil conservador del yield canónico de 04 (−10,7 % frente a P50 en el año 1: incertidumbre del recurso, del modelo y de la degradación). 10 §A.2 compara ambos para el Custom."),
    ("Factor_CAPEX", "Esc_Factor_CAPEX", "Factor sobre el CAPEX bottom-up (costo real, 05)", "×", "0.00", {"X": 1.0, "C": 1.15, "B": 1.0, "F": 1.0}, False,
     "Multiplica los 9 rubros + contingencia de 05_CAPEX (el IVA escala igual). 1,15 = rango alto del estudio CAPEX/OPEX (jul-2026: 1,15 vs 1,00 $/Wp). Se ignora cuando CAPEX_Fijo_Wp > 0."),
    ("CAPEX_Fijo_Wp", "Esc_CAPEX_Fijo_Wp", "CAPEX unitario fijo (vacío = bottom-up × factor)", "$/Wp", FMT_WP, {"X": None, "C": None, "B": None, "F": 0.75}, False,
     "Si tiene valor, sustituye al bottom-up: CAPEX = $/Wp × kWp × 1000 (sin IVA, incl. gerencia; el IVA se escala en proporción). 0,75 = deck v4 L14 (22-jul-2026): 750 mil US$/MWp llave en mano «todo incluido»."),
    ("Factor_OPEX", "Esc_Factor_OPEX", "Factor sobre el OPEX de SALELGI (06)", "×", "0.00", {"X": 1.0, "C": 1.15, "B": 1.0, "F": 1.0}, False,
     "Se aplica en 07_Fiscal sobre el total de 06 (fee O&M, seguros, arriendo/predial, tributos); los ingresos de Exergy no cambian. 1,15 = rango alto del estudio CAPEX/OPEX."),
    ("Peaje_SGDA", "Esc_Peaje", "Peaje de red SGDA desde Fecha_Peaje", "$/kWh inyectado", FMT_KWH, {"X": 0.0 if (_V13 or V31) else 0.005, "C": 0.010 if _V13 else 0.015, "B": 0.0 if _V13 else 0.005, "F": 0.0}, True,
     "Valor NO publicado por ARCONEL (Disp. Trans. Cuarta 005/24; RLOCE D.E. 176 art. 18 y DT 16.ª; art. 5.17 «valores por potencia y energía»). Definición v2.0: Base 0,5 ¢ (mitad del rango 0–1 ¢ de la sensibilidad), Conservador 1,5 ¢ (techo del rango), Favorable 0. Custom v3.1: 0 (fijado por Jorge, 04-sep-2026). Equivalente en $/kW-mes en 04."),
    ("Escalacion_Tarifa", "Esc_EscTarifa", "Escalación anual de la tarifa evitable", "%/año", FMT_PCT, {"X": 0.02 if V31 else 0.0, "C": 0.0, "B": 0.0, "F": 0.02}, False,
     "Base y Conservador: PLANA 0 % (P6, ácido). Favorable: +2 %/año (déficit tarifario 2026 = USD 621,9 M, Res. 029/25 → presión al alza). Custom v3.1: +2 %/año (fijado por Jorge, 04-sep-2026). Sensibilidad 1/2/3 % en 10 §B."),
    # ronda 2 (doc 13, d3): dos filas más en el bloque B; en modo neutro (v20/v13) valen 100 % y 0 % (≡ v2.0)
    ("Disponibilidad", "Esc_Disponibilidad", "Disponibilidad de la planta (factor sobre la energía producida)", "%", FMT_PCT, ({"X": 1.0, "C": 1.0, "B": 1.0, "F": 1.0} if NEUTRO else {"X": 0.97 if V31 else 0.98, "C": 0.97, "B": 0.98, "F": 0.99}), True,
     "Ronda 2 (M-d): fracción del año en que la planta produce (paradas, fallas de inversores, red). Base 98 % · Conservador 97 % · Favorable 99 %; Custom v3.1: 97 % (fijado por Jorge, 04-sep-2026); garantía de O&M típica 98–99 % — POR CONFIRMAR con el contrato de O&M de Exergy. Neutro (≡ v2.0) = 100 %. Sensibilidad ±2 pp en 10 §B."),
    ("Escalacion_CAPEX", "Esc_Escalacion_CAPEX", "Escalación anual de los precios del CAPEX desde Fecha_Precios hasta la compra", "%/año", FMT_PCT, ({"X": 0.0, "C": 0.0, "B": 0.0, "F": 0.0} if NEUTRO else {"X": 0.0 if V31 else 0.03, "C": 0.05, "B": 0.03, "F": 0.0}), True,
     "Ronda 2 (M-a): los rubros de 05 están a precios de jul-2026 y la compra es en 2027–28 (01 H4: módulos > +30 % desde dic-2025). Base 3 %/año · Conservador 5 % · Favorable 0 % (precio EPC fijo 0,75 $/Wp ya cerrado); Custom v3.1: 0 % (fijado por Jorge, 04-sep-2026). Índice POR CONFIRMAR. Neutro (≡ v2.0) = 0. Factor_Escalacion en 05; +2 pp en 10 §B."),
]
ESC_BY_NAME = {e[0]: e for e in ESCENARIOS}
YESNO = {"Contrato_Inversion", "IVA_Recuperable", "Incluir_Participacion", "Escudo_Negativo", "Usar_Deuda", "Deuda_Financia_Terreno", "Aplica_DedAd"}
CASE_KEYS = ("X", "C", "B", "F")   # orden de columnas del bloque B y del Motor (Custom · Conservador · Base · Favorable)
MOTOR_CASE_COL = {"X": "B", "C": "C", "B": "D", "F": "E"}   # columnas del Motor de los cuatro casos (casos 0–3)


# build_supuestos (v1.1) eliminado en v2.0: la hoja 01 se construye en build_supuestos20.py


def mini_casos(ws, sec_row, hdr_row, r0, cols, title, guide):
    """Mini-tabla comparativa de los cuatro casos leída del Motor (v2.0). cols = [(columna, cabecera, clave OUT_ROWS, formato)]."""
    last = max(c for c, *_ in cols)
    section(ws, sec_row, 2, last, title, guide=guide, guide_col=4)
    hdr(ws, hdr_row, 2, last, [""] * (last - 1), height=26)
    ws.cell(row=hdr_row, column=2, value="Caso").alignment = Alignment(horizontal="left", vertical="center")
    for c, head, key, fmt in cols:
        ws.cell(row=hdr_row, column=c, value=head)
    for i, k in enumerate(CASE_KEYS):
        r = r0 + i
        lc = ws.cell(row=r, column=2, value=CASO_NOMBRE[k]); lc.font = Font(name=FONT, bold=True, color=CASO_COL[k], size=SZ_TABLE); lc.border = B_BOTTOM; lc.alignment = Alignment(vertical="center")
        ws.cell(row=r, column=3).border = B_BOTTOM
        for c, head, key, fmt in cols:
            if key in OUT_ROWS:
                f = f"='{SM}'!${MOTOR_CASE_COL[k]}${OUT_ROWS[key]}"
            else:
                f = key.format(X=MOTOR_CASE_COL[k], B=MOTOR_CASE_COL["B"])
            caso_val(ws, r, c, f, fmt=fmt, bold=(k == "X"), size=SZ_TABLE)
        ws.row_dimensions[r].height = 14
    ws.row_dimensions[hdr_row].height = 26


def build_energia(wb):
    """04 · Energía (v1.3): tres páginas de resumen a 82 % (B..L) + serie anual en la retícula común.
    p1 Resumen + T1 consumo del medidor · p2 T2 producción e inyección + gráfico mensual con T3 valor del ahorro · p3 bloques técnicos
    (proyección del consumo y factura de referencia · curva de recorte pvlib) · p4–p6 serie anual (−1…7 | 8…16 | 17…25).
    Sólo cambia la disposición: cada valor de la v1.2 sigue existiendo (regress.py lo comprueba)."""
    E = ENERGIA
    ws = wb.create_sheet(S4)
    time_widths(ws)
    sheet_header(ws, "4 · Energía", "Balance energético de GPM: producción = Potencia_DC × yield canónico (pvlib) × recorte por ratio × Disponibilidad × degradación; energía valorizable = MIN(producción, demanda) (art. 9); balance mensual por bloques. Alimenta 07 y el Motor.", 4, last_col=12, total=NSHEETS)
    ws.row_dimensions[4].height = 10
    LC = 12
    m1, tot1 = E["t1_0"], E["t1_tot"]          # T1 consumo del medidor (kWh): D 2025 A · E B · F C · G total · H proy A · I B · J C · K proy total · L proy [MWh]
    m2, tot2 = E["t2_0"], E["t2_tot"]          # T2 producción e inyección: D perfil · E P50 [MWh] · F iny A · G B · H C · I total · J cobertura · K ¿excedente? · L bloque A
    m3, tot3 = E["t3_0"], E["t3_tot"]          # T3 valor del ahorro (junto al gráfico): I mes · J valor evitado · K tarifa efectiva · L acumulado
    # ---- Resumen (8 filas)
    section(ws, E["res_sec"], 2, LC, "Resumen", guide="el año 1 del caso Custom; la serie anual está al final de la hoja", guide_col=6)
    res = [
        ("Potencia DC / AC · ratio DC/AC · terreno", f'=TEXT(Potencia_DC,"#,##0")&" kWp / "&TEXT(Potencia_AC,"#,##0")&" kWac · "&TEXT(Ratio_DCAC,"0.00")&" · "&TEXT(Hectareas,"0.0")&" ha"', None, "", '="Alimentador: "&TEXT(Capacidad_Alimentador_kW,"#,##0")&" kW (por confirmar) · predio "&TEXT(Ha_Disponibles,"0.00")&" ha"'),
        ("Factor de recorte vs referencia (ratio 1,32)", "=F_Recorte", "0.0000", "×", '="pérdida por recorte "&TEXT(Loss_Act,"0.00%")&" (ref. "&TEXT(Loss_Ref,"0.00%")&"); curva pvlib en la página 3"'),
        ("Tarifa evitable efectiva (ponderada por bloques)", f"=$K${tot3}", FMT_KWH, "$/kWh", "96,7 % de la inyección cae en el bloque A (0,113) y 3,1 % en el C (0,105)."),
        ("Consumo anual proyectado del medidor (año 1)", f"=$K${tot1}", FMT_INT, "kWh/año", '="Estacionalidad 2025 × nivel 2026; crecimiento "&TEXT(Crecimiento_Consumo,"0.0%")&"/año en el horizonte."'),
        ("Producción año 1 (P50 / P90)", f"=${C(1)}${E['p50']}", FMT_INT, "MWh", f'="P90: "&TEXT(${C(1)}${E["p90"]},"#,##0")&" MWh · yield "&TEXT(${C(1)}${E["yld"]},"#,##0")&" kWh/kWp"'),
        ("Cobertura del consumo (año 1)", f"=$J${tot2}", FMT_PCT, "%", f'="Potencia máxima teórica bajo el art. 9 con este consumo: "&TEXT(Potencia_DC*$K${tot1}/1000/${C(1)}${E["p50"]},"#,##0")&" kWp"'),
        ("Art. 9 — producción anual ≤ demanda anual", f'=IF(${C(1)}${E["p50"]}<=$K${tot1}/1000,"● cumple ("&TEXT(${C(1)}${E["p50"]}/($K${tot1}/1000),"0%")&" de la demanda)","■ NO cumple: "&TEXT(${C(1)}${E["norec"]},"#,##0")&" MWh no reconocidos en el año 1")', None, "", "Candado de energía del régimen SGDA. La energía por encima de la demanda anual no se valora (E_Val)."),
        ("Art. 27 — meses con generación > consumo", f'=IF(COUNTIF($K${m2}:$K${m2+11},"SÍ")=0,"● ninguno: toda la energía se netea el mismo mes; la bolsa de 24 meses no se usa","▲ "&COUNTIF($K${m2}:$K${m2+11},"SÍ")&" meses con excedente → crédito kWh (caduca a 24 meses)")', None, "", f'=COUNTIF($L${m2}:$L${m2+11},"energía equiv.")&" meses con inyección A > consumo A: se netea como energía equivalente (art. 27.3) sin perder valor en USD"'),
    ]
    for i, (lab, f, fmt, u, nt) in enumerate(res):
        r = E["res0"] + i
        label(ws, r, 2, lab)
        if fmt:
            calc(ws, r, 4, f, fmt=fmt, bold=True); unit(ws, r, 3, u)
            note(ws, r, 5, nt, border=True, valign="center", c2=LC)
        else:
            chip(ws, r, 4, f, kind="ok", c2=8); ws.cell(row=r, column=3).border = B_BOTTOM
            note(ws, r, 9, nt, border=True, valign="center", c2=LC)
        for cc in range(3, LC + 1):
            ws.cell(row=r, column=cc).border = B_BOTTOM
        ws.row_dimensions[r].height = 20 if fmt else 30   # las filas con chip llevan notas de dos líneas
    ws.row_dimensions[E["res0"] + 8].height = 8
    # ---- T1 · consumo del medidor
    section(ws, E["t1_sec"], 2, LC, "Balance mensual del año 1 · consumo del medidor por bloque horario", guide="planillas 2025 y proyección al nivel 2026 (kWh)", guide_col=6)
    hdr(ws, E["t1_hdr"], 2, LC, ["Mes", "", "2025 · A\n08–18 h", "2025 · B\n18–22 h", "2025 · C\n22–08 h", "2025\ntotal", "Proyección · A\n[kWh]", "Proyección · B\n[kWh]", "Proyección · C\n[kWh]", "Proyección\ntotal [kWh]", "Proyección\ntotal [MWh]"], height=30)
    for i in range(12):
        r = m1 + i
        a, b, cc = CONS_2025[i]
        label(ws, r, 2, MESES[i], bold=True, size=9); ws.cell(row=r, column=3).border = B_BOTTOM
        canon(ws, r, 4, a, fmt=FMT_INT); canon(ws, r, 5, b, fmt=FMT_INT); canon(ws, r, 6, cc, fmt=FMT_INT)
        calc(ws, r, 7, f"=D{r}+E{r}+F{r}", fmt=FMT_INT, size=9)
        calc(ws, r, 8, f"=D{r}*Factor_Nivel_2026", fmt=FMT_INT, size=9); calc(ws, r, 9, f"=E{r}*Factor_Nivel_2026", fmt=FMT_INT, size=9); calc(ws, r, 10, f"=F{r}*Factor_Nivel_2026", fmt=FMT_INT, size=9)
        calc(ws, r, 11, f"=H{r}+I{r}+J{r}", fmt=FMT_INT, bold=True, size=9)
        calc(ws, r, 12, f"=K{r}/1000", fmt=FMT_INT, size=9, color=GRAFITO)
        ws.row_dimensions[r].height = 16
    label(ws, tot1, 2, "Año", bold=True, size=9)
    for cidx in range(4, 13):
        L = col(cidx)
        calc(ws, tot1, cidx, f"=SUM({L}{m1}:{L}{m1+11})", fmt=FMT_INT, bold=True, size=9)
    total_row(ws, tot1, 2, LC); ws.row_dimensions[tot1].height = 16
    name(wb, "Consumo_Anual", S4, f"$K${tot1}")
    ws.row_dimensions[tot1 + 1].height = 8
    # ---- T2 · producción e inyección
    section(ws, E["t2_sec"], 2, LC, "Balance mensual del año 1 · producción P50 e inyección por bloque", guide="inyección = producción × fracción horaria del TMY; cobertura = inyección ÷ consumo proyectado", guide_col=6)
    hdr(ws, E["t2_hdr"], 2, LC, ["Mes", "", "Perfil\nmensual", "Producción\nP50 [MWh]", "Inyección · A\n[kWh]", "Inyección · B\n[kWh]", "Inyección · C\n[kWh]", "Inyección\ntotal [kWh]", "Cobertura", "¿Excedente\nmensual?", "Bloque A\nneteo"], height=30)
    for i in range(12):
        r, r1 = m2 + i, m1 + i
        label(ws, r, 2, MESES[i], bold=True, size=9); ws.cell(row=r, column=3).border = B_BOTTOM
        canon(ws, r, 4, PERFIL_MES[i], fmt="0.0000")
        calc(ws, r, 5, f"=Potencia_DC/1000*Yield_Ref*F_Recorte*Disponibilidad*D{r}", fmt=FMT_INT, size=9, bold=True)   # v3.0: × Disponibilidad (año 1: degradación adicional^0 = 1)
        calc(ws, r, 6, f"=E{r}*1000*Frac_A", fmt=FMT_INT, size=9); calc(ws, r, 7, f"=E{r}*1000*Frac_B", fmt=FMT_INT, size=9); calc(ws, r, 8, f"=E{r}*1000*Frac_C", fmt=FMT_INT, size=9)
        calc(ws, r, 9, f"=F{r}+G{r}+H{r}", fmt=FMT_INT, bold=True, size=9)
        calc(ws, r, 10, f"=I{r}/K{r1}", fmt=FMT_PCT, size=9)
        calc(ws, r, 11, f'=IF(I{r}>K{r1},"SÍ","no")', align="center", size=9, color=GRAFITO)
        calc(ws, r, 12, f'=IF(F{r}>H{r1},"energía equiv.","directo")', align="center", size=9, color=GRAFITO)
        ws.row_dimensions[r].height = 16
    label(ws, tot2, 2, "Año", bold=True, size=9)
    for cidx in (4, 5, 6, 7, 8, 9):
        L = col(cidx)
        calc(ws, tot2, cidx, f"=SUM({L}{m2}:{L}{m2+11})", fmt=("0.0000" if cidx == 4 else FMT_INT), bold=True, size=9)
    calc(ws, tot2, 10, f"=I{tot2}/K{tot1}", fmt=FMT_PCT, bold=True, size=9)
    calc(ws, tot2, 11, f'=COUNTIF(K{m2}:K{m2+11},"SÍ")&" meses"', bold=True, align="center", size=9)
    calc(ws, tot2, 12, f'=COUNTIF(L{m2}:L{m2+11},"energía equiv.")&" meses"', bold=True, align="center", size=9)
    total_row(ws, tot2, 2, LC); ws.row_dimensions[tot2].height = 16
    name(wb, "Cobertura_Anual", S4, f"$J${tot2}")
    name(wb, "Perfil_Mensual", S4, f"$D${m2}:$D${m2+11}")
    ws.row_dimensions[tot2 + 1].height = 8
    # ---- gráfico mensual (B..H) + T3 valor del ahorro (I..L)
    section(ws, E["val_sec"], 2, LC, "Año 1 · producción frente a consumo y valor del ahorro", guide="el valor evitado usa la tarifa del bloque donde se inyecta (B se valora a la tarifa A)", guide_col=6)
    hdr(ws, E["t3_hdr"], 9, LC, ["Mes", "Valor evitado\n[USD]", "Tarifa efect.\n[$/kWh]", "Acumulado\n[USD]"], height=30)
    for i in range(12):
        r, r2 = m3 + i, m2 + i
        label(ws, r, 9, MESES[i], bold=True, size=9)
        calc(ws, r, 10, f"=F{r2}*Tarifa_A+G{r2}*Tarifa_A+H{r2}*Tarifa_C", fmt=FMT_USD, size=9)
        calc(ws, r, 11, f"=J{r}/I{r2}", fmt=FMT_KWH, size=9)
        calc(ws, r, 12, f"=SUM($J${m3}:J{r})", fmt=FMT_USD, size=9, color=GRAFITO)
        ws.row_dimensions[r].height = 16
    label(ws, tot3, 9, "Año", bold=True, size=9)
    calc(ws, tot3, 10, f"=SUM(J{m3}:J{m3+11})", fmt=FMT_USD, bold=True, size=9)
    calc(ws, tot3, 11, f"=J{tot3}/I{tot2}", fmt=FMT_KWH, bold=True, size=9)
    calc(ws, tot3, 12, f"=L{m3+11}", fmt=FMT_USD, bold=True, size=9, color=GRAFITO)
    total_row(ws, tot3, 9, LC); ws.row_dimensions[tot3].height = 16
    name(wb, "Tarifa_Evitable", S4, f"$K${tot3}")
    name(wb, "Ahorro_Mensual_Anio1", S4, f"$J${tot3}")
    cats = Reference(ws, min_col=2, min_row=m2, max_row=m2 + 11)
    chart_cols(ws, f"B{E['t3_hdr']}", "Producción P50 (barras) y consumo del medidor (línea), MWh", cats,
               [dict(ref=Reference(ws, min_col=5, min_row=m2, max_row=m2 + 11), name="producción P50", color=GRAFITO)],
               lines=[dict(ref=Reference(ws, min_col=12, min_row=m1, max_row=m1 + 11), name="consumo proyectado", color=TERRACOTA, width=2.25)],
               w=15.2, h=7.4, y_fmt='#,##0', legend="b", gap=45)
    ws.row_dimensions[tot3 + 1].height = 8
    # ---- página 3 · bloques técnicos: proyección del consumo (B..F) y curva de recorte (H..L)
    pc, cc0 = 2, 8
    section(ws, E["tec_sec"], pc, 6, "Proyección del consumo y factura de referencia")
    section(ws, E["tec_sec"], cc0, LC, "Curva de recorte por ratio DC/AC (pvlib)")
    r = E["tec_sec"] + 1
    hdr(ws, r, pc, pc + 3, ["Mes", "", "kWh 2025", "kWh 2026"], height=18)   # C es la columna de unidad (6 de ancho): los valores van en D y E
    for i in range(5):
        rr = r + 1 + i
        label(ws, rr, pc, MESES[i], size=9); ws.cell(row=rr, column=pc + 1).border = B_BOTTOM
        canon(ws, rr, pc + 2, CONS_2025_ENE_MAY[i], fmt=FMT_INT); canon(ws, rr, pc + 3, CONS_2026_ENE_MAY[i], fmt=FMT_INT)
        ws.row_dimensions[rr].height = 15
    rr = r + 6
    label(ws, rr, pc, "Σ ene–may", bold=True, size=9); calc(ws, rr, pc + 2, f"=SUM({col(pc+2)}{r+1}:{col(pc+2)}{r+5})", fmt=FMT_INT, bold=True, size=9); calc(ws, rr, pc + 3, f"=SUM({col(pc+3)}{r+1}:{col(pc+3)}{r+5})", fmt=FMT_INT, bold=True, size=9)
    total_row(ws, rr, pc, pc + 3); ws.row_dimensions[rr].height = 15
    rr += 1
    label(ws, rr, pc, "Factor de nivel 2026 (Σ 2026 / Σ 2025)", bold=True, size=9); unit(ws, rr, pc + 1, "×")
    calc(ws, rr, pc + 2, f"={col(pc+3)}{rr-1}/{col(pc+2)}{rr-1}", fmt="0.000", bold=True, size=9); ws.row_dimensions[rr].height = 15
    name(wb, "Factor_Nivel_2026", S4, f"${col(pc+2)}${rr}")
    rr += 2
    label(ws, rr, pc, "Demanda facturable promedio 2026", size=9); inp(ws, rr, pc + 2, 2200, fmt=FMT_INT, comment="Planillas ene–jun 2026: 2.033–2.347 kW."); unit(ws, rr, pc + 1, "kW"); rd = rr; ws.row_dimensions[rr].height = 15
    rr += 1
    label(ws, rr, pc, "FGD promedio", size=9); inp(ws, rr, pc + 2, 0.956, fmt="0.000", comment="Promedio 19 planillas (0,912–1,000)."); rfgd = rr; ws.row_dimensions[rr].height = 15
    rr += 1
    label(ws, rr, pc, "Factura de referencia anual sin SGDA (tarifa 2026)", bold=True, size=9)
    calc(ws, rr, pc + 2, f"=H{tot1}*Tarifa_A+I{tot1}*Tarifa_A+J{tot1}*Tarifa_C+{col(pc+2)}{rd}*Cargo_Demanda*{col(pc+2)}{rfgd}*12+(Cargo_Comercializacion+SAPG_mes)*12", fmt=FMT_USD, bold=True, size=9); unit(ws, rr, pc + 1, "USD"); ws.row_dimensions[rr].height = 15
    name(wb, "Factura_Referencia", S4, f"${col(pc+2)}${rr}")
    rr += 1
    label(ws, rr, pc, "Reducción de la factura en el año 1", bold=True, size=9)
    calc(ws, rr, pc + 2, f"=J{tot3}/{col(pc+2)}{rr-1}", fmt=FMT_PCT, bold=True, size=9); ws.row_dimensions[rr].height = 15
    name(wb, "Reduccion_Factura", S4, f"${col(pc+2)}${rr}")
    rr += 1
    label(ws, rr, pc, "Peaje equivalente por potencia (informativo)", size=9)
    calc(ws, rr, pc + 2, f"=IF(Potencia_AC>0,Eff_Peaje*${C(1)}${E['p50']}*1000/Potencia_AC/12,0)", fmt=FMT_DEC2, size=9); unit(ws, rr, pc + 1, "$/kW-mes"); ws.row_dimensions[rr].height = 15
    rr += 2
    note(ws, rr, pc, "Planillas CNEL 2025 + ene–may 2026 (12 meses reales ≈ US$ 1,15 M; detalle en 12 §D). Demanda y FGD sólo para la factura de referencia; el peaje equivalente traduce el $/kWh a $/kW-mes sobre la potencia AC.", c2=6)
    fit_row(ws, rr, [("x" * 300, 38 + 6 + 3 * 11 - 2, 8.5)])
    # curva de recorte (H..L): H ratio · I pérdida · J yield rel. · K/L aire para las notas
    r = E["tec_sec"] + 1
    hdr(ws, r, cc0, cc0 + 2, ["Ratio DC/AC", "Pérdida por\nrecorte", "Yield rel.\nvs 1,32"], height=30)
    n = len(CURVA_RECORTE)
    for i, pt in enumerate(CURVA_RECORTE):
        rr = r + 1 + i
        inp(ws, rr, cc0, pt["ratio"], fmt="0.00"); inp(ws, rr, cc0 + 1, pt["clipping"], fmt=FMT_PCT2)
        calc(ws, rr, cc0 + 2, f"=(1-{col(cc0+1)}{rr})/(1-Loss_Ref)-1", fmt=FMT_SIGNPCT, size=9, color=GRAFITO)
    name(wb, "CR_Ratio", S4, f"${col(cc0)}${r+1}:${col(cc0)}${r+n}")
    name(wb, "CR_Loss", S4, f"${col(cc0+1)}${r+1}:${col(cc0+1)}${r+n}")
    rr = r + n + 1
    label(ws, rr, cc0, "Pérdida a Ratio_Ref", size=9); ws.merge_cells(start_row=rr, start_column=cc0, end_row=rr, end_column=cc0 + 1); calc(ws, rr, cc0 + 2, "=" + f_loss("Ratio_Ref"), fmt=FMT_PCT2, size=9); name(wb, "Loss_Ref", S4, f"${col(cc0+2)}${rr}"); rr += 1
    label(ws, rr, cc0, "Pérdida a Ratio_DCAC", size=9); ws.merge_cells(start_row=rr, start_column=cc0, end_row=rr, end_column=cc0 + 1); calc(ws, rr, cc0 + 2, "=" + f_loss("Ratio_DCAC"), fmt=FMT_PCT2, size=9); name(wb, "Loss_Act", S4, f"${col(cc0+2)}${rr}"); rr += 1
    label(ws, rr, cc0, "Factor de recorte F", bold=True, size=9); ws.merge_cells(start_row=rr, start_column=cc0, end_row=rr, end_column=cc0 + 1); calc(ws, rr, cc0 + 2, "=(1-Loss_Act)/(1-Loss_Ref)", fmt="0.0000", bold=True, size=9); name(wb, "F_Recorte", S4, f"${col(cc0+2)}${rr}"); rr += 1
    note(ws, rr, cc0, "Curva pvlib (TMY P50 Montecristi, 10° N, PVWatts; 12 §D): interpolación lineal, fuera de 1,00–1,60 se toma el extremo; ±0,3 pp.", c2=LC)
    fit_row(ws, rr, [("x" * 200, 5 * 11 - 2, 8.5)])
    tec_last = max(rr, E["tec_sec"] + 1 + 6 + 1 + 2 + 5 + 2)
    for k in range(E["tec_sec"] + 1, tec_last + 1):
        if ws.row_dimensions[k].height is None:
            ws.row_dimensions[k].height = 15
    ws.row_dimensions[tec_last + 1].height = 6
    assert tec_last + 1 < E["serie_sec"], (tec_last, E["serie_sec"])
    # ---- Serie anual (retícula común)
    section(ws, E["serie_sec"], 2, LAST_T_COL + 5, "Serie anual 30 años — yield canónico × potencia × recorte; años 26–30 fuera del horizonte (agrupados)")
    time_header(ws, E["t"], extra_cols=5)
    trow = E["t"]
    ext = list(range(1, 31))
    label(ws, E["y50"], 2, "Yield canónico P50 a la referencia (5.000 kWp · 1,32)", bold=True); unit(ws, E["y50"], 3, "kWh/kWp")
    label(ws, E["y90"], 2, "Yield canónico P90 a la referencia", bold=True); unit(ws, E["y90"], 3, "kWh/kWp")
    for i, t in enumerate(ext):
        canon(ws, E["y50"], COL0 + (t + 1), Y50[i], fmt=FMT_INT); canon(ws, E["y90"], COL0 + (t + 1), Y90[i], fmt=FMT_INT)
    for t in (-1, 0):
        canon(ws, E["y50"], COL0 + (t + 1), 0, fmt=FMT_INT); canon(ws, E["y90"], COL0 + (t + 1), 0, fmt=FMT_INT)
    name(wb, "Y_P50", S4, f"${C(1)}${E['y50']}:${col(COL0 + 31)}${E['y50']}")
    name(wb, "Y_P90", S4, f"${C(1)}${E['y90']}:${col(COL0 + 31)}${E['y90']}")
    all_ts = list(TS) + [26, 27, 28, 29, 30]
    # v3.0 (M-d): × Disponibilidad × (1 − Degradacion_Adicional)^(t−1) en P50, P90 y la serie activa (misma forma que el Motor)
    fdisp = lambda T: f"*Disponibilidad*(1-Degradacion_Adicional)^MAX(0,{T}-1)"
    row_formula(ws, E["p50"], "Energía anual P50 (potencia, ratio, disponibilidad y degradación adicional del Custom)", lambda t, T: f"=Potencia_DC/1000*F_Recorte*{C(t)}{E['y50']}{fdisp(T)}", fmt=FMT_INT, unit_txt="MWh", bold=True, ts=all_ts, trow=trow)
    row_formula(ws, E["p90"], "Energía anual P90", lambda t, T: f"=Potencia_DC/1000*F_Recorte*{C(t)}{E['y90']}{fdisp(T)}", fmt=FMT_INT, unit_txt="MWh", bold=True, ts=all_ts, trow=trow)
    name(wb, "E_P50", S4, f"${C(1)}${E['p50']}:${col(COL0 + 31)}${E['p50']}")
    name(wb, "E_P90", S4, f"${C(1)}${E['p90']}:${col(COL0 + 31)}${E['p90']}")
    row_formula(ws, E["activa"], "Energía producida del caso Custom (≤ horizonte)", lambda t, T: f"=IF(OR({T}<1,{T}>Horizonte),0,IF(Eff_Scen=1,{C(t)}{E['p50']},{C(t)}{E['p90']}))", fmt=FMT_INT, unit_txt="MWh", bold=True, trow=trow)
    name(wb, "E_Activa", S4, rng(E["activa"]))
    row_formula(ws, E["eval"], "Energía valorizable (≤ demanda anual, art. 9)", lambda t, T: f"=MIN({C(t)}{E['activa']},IF({T}<1,0,Consumo_Anual*(1+Crecimiento_Consumo)^({T}-1)/1000))", fmt=FMT_INT, unit_txt="MWh", bold=True, trow=trow)
    name(wb, "E_Val", S4, rng(E["eval"]))
    row_formula(ws, E["norec"], "Energía no reconocida (producción − demanda)", lambda t, T: f"={C(t)}{E['activa']}-{C(t)}{E['eval']}", fmt=FMT_INT, unit_txt="MWh", color=GRAFITO, trow=trow)
    row_formula(ws, E["yld"], "Yield específico", lambda t, T: f"=IF({C(t)}{E['activa']}>0,{C(t)}{E['activa']}*1000/Potencia_DC,0)", fmt=FMT_INT, unit_txt="kWh/kWp", trow=trow)
    row_formula(ws, E["frac"], "Fracción del año con peaje SGDA vigente", lambda t, T: f"=IF({T}<1,0,MAX(0,MIN(1,(EDATE(Fecha_COD,12*{T})-MAX(Fecha_Peaje,EDATE(Fecha_COD,12*({T}-1))))/(EDATE(Fecha_COD,12*{T})-EDATE(Fecha_COD,12*({T}-1))))))", fmt=FMT_PCT0, unit_txt="%", trow=trow)
    name(wb, "Frac_Peaje", S4, rng(E["frac"]))
    row_formula(ws, E["degr"], "Degradación acumulada vs año 1 (P50, incl. adicional)", lambda t, T: f"=IF({T}<1,0,{C(t)}{E['p50']}/${C(1)}${E['p50']}-1)", fmt=FMT_PCT, unit_txt="%", color=GRAFITO, trow=trow)
    row_formula(ws, E["lost"], "Energía no producida por indisponibilidad y degradación adicional (informativa)", lambda t, T: f"=IF(OR({T}<1,{T}>Horizonte),0,Potencia_DC/1000*F_Recorte*IF(Eff_Scen=1,{C(t)}{E['y50']},{C(t)}{E['y90']})-{C(t)}{E['activa']})", fmt=FMT_INT, unit_txt="MWh", color=GRAFITO, trow=trow)
    for k in range(E["y50"], E["lost"] + 1):
        ws.row_dimensions[k].height = 15   # v3.0: 15 pt (antes 16) para que la página 3 (bloques técnicos + años −1…7) siga cabiendo con la fila informativa (≈ 501 de 516 pt)
    ws.column_dimensions.group(col(COL0 + 27), col(COL0 + 31), hidden=True, outline_level=2)
    series_layout(ws, E["t"], summary_last_col=LC, row_breaks=(tot1 + 1, tot3 + 1))   # la serie (años −1…7) comparte la página 3 con los bloques técnicos
    return ws


# ---------------------------------------------------------------- 05_CAPEX
# (nombre, alcance, costo base 5 MWp, % compartible, % importado, arancel, IVA, fuente, %Wp, %Wac, %fijo)
RUBROS = [
    ("Módulos FV", "TOPCon bifacial vidrio-vidrio ~620 Wp · CIF Guayaquil/Manta (FOB ≈0,11 $/W + flete y seguro ≈0,008 $/W).", 590000, 0.00, 1.00, 0.00, 0.00,
     "OPIS CMM TOPCon 0,108 US$/W FOB (28-ago-2026, +2,9 % s/s; forward Q1-27 0,107) → base 0,11 con margen. Flete China–Guayaquil 1.400–1.950 US$/40' (estudio CAPEX). Partida 8541.43: arancel 0 % (permanente); IVA 0 % (LRTI art. 55 num. 19; código Ecuapass 0719, boletín SENAE 15-ene-2024).", 1.00, 0.00, 0.00),
    ("Inversores string", "≈330 kVA clase C5; número según Potencia_AC (12 × 330 kVA a 1,32).", 230000, 0.00, 1.00, 0.05, 0.00,
     "≈0,045 US$/Wdc FOB (estudio CAPEX). Partida 8504.40.90 ≈5 % — arancel 2026 no cotejado (Atlas I-19/P-03; COMEX 002-2025 vencida el 31-dic-2025) · por confirmar. IVA 0 % como «accesorio para la generación solar FV» (art. 55.19): ZONA GRIS (Atlas P-04) — resolver con resolución anticipada de clasificación SENAE (código 0719); decisión D-L5 (08-sep-2026): se mantiene 0 % (efecto de capital de trabajo: −0,01 pp de TIR si fuera 15 %).", 0.00, 1.00, 0.00),
    ("Estructura fija", "Acero Zn-Al-Mg (ZM275+), hincado directo, 10° N, clase C4 · hardware.", 450000, 0.00, 1.00, 0.20, 0.15,
     "0,09 $/Wp hardware (pvrack/PVH/Schletter, estudio CAPEX). Partida 7308.90.90: 20 % (COMEX 009-2021; arancel 2026 no cotejado, Atlas P-03 · por confirmar). IVA 15 % (no es «accesorio FV» inequívoco; zona gris P-04).", 1.00, 0.00, 0.00),
    ("Centros de transformación y MT", "Transformadores 0,8/13,8 kV según kVA + celdas MT + SCADA + medición.", 380000, 0.30, 0.60, 0.10, 0.15,
     "15–30 US$/kVA + celdas (estudio CAPEX). Trafos 8504.22.90 ≈11,25 %, celdas ≈5 % → 10 % promedio sobre el 60 % importado (Media; arancel 2026 no cotejado, Atlas P-03 · por confirmar). Celdas MT 30 % compartibles con la 2ª planta.", 0.00, 0.85, 0.15),
    ("BOS eléctrico DC/AC", "Cable solar, cableado BT/MT, canalización, cajas, protecciones, puesta a tierra.", 400000, 0.10, 0.40, 0.05, 0.15,
     "Benchmark utility LATAM (RatedPower/NREL EBOS) 0,07–0,12 $/Wp. 40 % importado (cable solar/protecciones) a ≈5 %.", 0.70, 0.30, 0.00),
    ("Obra civil", "Nivelación (ondulación 113–123 m), drenaje ene–abr, caminos, cerramiento, caseta.", 400000, 0.40, 0.00, 0.00, 0.15,
     "0,06–0,13 $/Wp (estudio CAPEX). Cerramiento/caminos 40 % compartibles. Contratación local, IVA 15 %.", 0.70, 0.00, 0.30),
    ("Montaje mecánico y eléctrico", "Mano de obra local + supervisión (SBU 2026 = 482 US$/mes).", 400000, 0.00, 0.00, 0.00, 0.15,
     "0,07–0,12 $/Wp (estudio CAPEX). Servicios locales, IVA 15 %.", 0.90, 0.10, 0.00),
    ("Conexión 13,8 kV", "Derivación/línea corta, celda de seccionamiento, medición comercial MV bidireccional, protecciones ANSI, estudios de flujos/estabilidad (>1 MW), rubro CNEL ≤ USD 10.000.", 300000, 0.80, 0.30, 0.05, 0.15,
     "0,03–0,08 $/Wp (estudio CAPEX). La línea CNEL cruza el polígono → tramo corto. 80 % compartible con la 2ª planta. Rubro CNEL 005/24 art. 14: USD 4/kW, tope 10.000 (>2 MW).", 0.00, 0.30, 0.70),
    ("Desarrollo, permisos e ingeniería", "Registro Ambiental ante ARCONEL (tasa USD 180 + expediente; licencia como contingencia: 1 ‰ + póliza PMA + consultor), DGAC, GAD, INPC, servidumbres, legal, ingeniería de detalle, owner's engineer, geotecnia, topografía, seguro CAR.", 250000, 0.50, 0.00, 0.00, 0.12,
     "0,03–0,07 $/Wp (estudio CAPEX). 50 % compartible (un solo trámite ambiental por las 10,78 ha). IVA 12 % efectivo = 15 % sobre ≈ 80 % de servicios gravados (tasas y permisos exentos). Decisión D-L4 (08-sep-2026): se mantiene 250 k como prudencia aunque el cronograma valorado de 03 con Registro baje a ≈ 195 k.", 0.40, 0.00, 0.60),
]
# columnas 05: B # · C rubro · D costo base · E %comp · F costo caso · G %ext · H valor ext · I arancel% · J arancel$ · K FODINFA · L ISD · M aplicado · N CAPITALIZABLE · O IVA% · P IVA$ · Q $/Wp · R nota
# drivers: S %Wp · T %Wac · U %fijo · auxiliares (ocultas): V cargado GPM · W base IVA · X cap SC f1 · Y cap CC f1 · Z IVA SC f1 · AA IVA CC f1 · AB..AM particiones Wp/Wac/fijo de X, Y, Z, AA
SPLIT0 = 28  # AB
SPLIT_NAMES = [("CAPEX_SC", "X"), ("CAPEX_CC", "Y"), ("IVA_SC", "Z"), ("IVA_CC", "AA")]


def build_capex(wb):
    K = CAPEX
    ws = wb.create_sheet(S5)
    # v3.0 (V7): la tabla de rubros queda en B..R (17 columnas; ≈ 78 % de escala); los drivers de escala pasan a una tabla propia debajo
    widths(ws, {"A": 2, "B": 4, "C": 26, "D": 11, "E": 7, "F": 11, "G": 7, "H": 11, "I": 7, "J": 10, "K": 9, "L": 10, "M": 11, "N": 12, "O": 6, "P": 10, "Q": 7, "R": 5, "S": 7, "T": 7, "U": 7})
    for cc in range(22, SPLIT0 + 12):
        ws.column_dimensions[col(cc)].width = 11
    LCC = 18   # última columna impresa (R)
    sheet_header(ws, "5 · CAPEX", "CAPEX bottom-up del Custom: costo base a 5.000 kWp × drivers × factor del caso (o $/Wp fijo) × escalación de precios, más nacionalización e IVA; debajo, cuatro casos, reemplazo y drivers. Alimenta 07, 08 y el Motor.", 5, last_col=LCC, total=NSHEETS)
    heads = ["#", "Rubro", "Costo base\n5 MWp [USD]", "% comp.", "Costo caso\nactivo [USD]", "% ext.", "Valor\nexterior", "Arancel\n%", "Arancel\n[USD]", "FODINFA\n[USD]", "ISD\n[USD]", "Arancel+ISD\naplicado", "Capitalizable\nsin IVA [USD]", "IVA\n%", "IVA\n[USD]", "$/Wp", "nota"]
    hdr(ws, K["hdr"], 2, LCC, heads, height=32)
    for i, (nm, alc, cost, comp, imp, ar, iva, src, wwp, wwac, wfx) in enumerate(RUBROS):
        r = K["r0"] + i
        label(ws, r, 2, i + 1, size=9, bold=True)
        label(ws, r, 3, nm, size=10)
        inp(ws, r, 4, cost, fmt=FMT_USD)
        inp(ws, r, 5, comp, fmt=FMT_PCT0)
        calc(ws, r, 22, f"=D{r}*(1-E{r}*(1-Asignacion_Compartida))", fmt=FMT_USD, color=GRAFITO, size=9)  # V cargado a factor 1 y escala 1
        calc(ws, r, 6, f"=V{r}*Factor_Caso*(INDEX(Drv_Wp,{i+1})*Escala_Wp+INDEX(Drv_Wac,{i+1})*Escala_Wac+INDEX(Drv_Fijo,{i+1}))", fmt=FMT_USD, size=9)   # v3.0 (V7): drivers por nombre
        inp(ws, r, 7, imp, fmt=FMT_PCT0)
        calc(ws, r, 8, f"=F{r}*G{r}", fmt=FMT_USD, size=9)
        inp(ws, r, 9, ar, fmt=FMT_PCT)
        calc(ws, r, 10, f"=H{r}*I{r}", fmt=FMT_USD, size=9)
        calc(ws, r, 11, f"=H{r}*FODINFA_Pct", fmt=FMT_USD, size=9)
        calc(ws, r, 12, f"=H{r}*ISD_Pct", fmt=FMT_USD, size=9)
        calc(ws, r, 13, f'=IF(Contrato_Inversion="Sí",0,J{r}+L{r})', fmt=FMT_USD, size=9)
        calc(ws, r, 14, f"=F{r}+K{r}+M{r}", fmt=FMT_USD, bold=True, size=9)
        inp(ws, r, 15, iva, fmt=FMT_PCT0)
        calc(ws, r, 23, f'=F{r}+K{r}+IF(Contrato_Inversion="Sí",0,J{r})', fmt=FMT_USD, color=GRAFITO, size=9)  # W base IVA
        calc(ws, r, 16, f"=W{r}*O{r}", fmt=FMT_USD, size=9)
        calc(ws, r, 17, f"=N{r}/(Potencia_DC*1000)", fmt=FMT_WP, size=9)
        c = ws.cell(row=r, column=18, value=f"({i+1})"); c.font = font(size=8.5, color=GRAFITO); c.alignment = Alignment(horizontal="center", vertical="center"); c.border = B_BOTTOM
        # auxiliares a factor 1 y escala 1 (sirven al Motor: se escalan por caso)
        calc(ws, r, 24, f"=V{r}+V{r}*G{r}*FODINFA_Pct+V{r}*G{r}*(I{r}+ISD_Pct)", fmt=FMT_USD, color=GRAFITO, size=9)   # X cap SC
        calc(ws, r, 25, f"=V{r}+V{r}*G{r}*FODINFA_Pct", fmt=FMT_USD, color=GRAFITO, size=9)                          # Y cap CC
        calc(ws, r, 26, f"=(V{r}+V{r}*G{r}*FODINFA_Pct+V{r}*G{r}*I{r})*O{r}", fmt=FMT_USD, color=GRAFITO, size=9)     # Z IVA SC
        calc(ws, r, 27, f"=(V{r}+V{r}*G{r}*FODINFA_Pct)*O{r}", fmt=FMT_USD, color=GRAFITO, size=9)                    # AA IVA CC
        for k, (nm_, L) in enumerate(SPLIT_NAMES):
            for j, drv in enumerate(("Drv_Wp", "Drv_Wac", "Drv_Fijo")):
                calc(ws, r, SPLIT0 + k * 3 + j, f"={L}{r}*INDEX({drv},{i+1})", fmt=FMT_USD, color=GRAFITO, size=9)   # v3.0 (V7): drivers por nombre
        ws.row_dimensions[r].height = 18
    r_last = K["r0"] + len(RUBROS) - 1
    r = K["cont"]
    label(ws, r, 2, 10, size=9, bold=True); label(ws, r, 3, "Contingencia (sobre rubros 1-9)")
    calc(ws, r, 14, f"=Contingencia_Pct*SUM(N{K['r0']}:N{r_last})", fmt=FMT_USD, bold=True, size=9)
    calc(ws, r, 16, f"=N{r}*Tasa_IVA*Contingencia_Frac_IVA", fmt=FMT_USD, size=9); calc(ws, r, 17, f"=N{r}/(Potencia_DC*1000)", fmt=FMT_WP, size=9)
    c = ws.cell(row=r, column=18, value="(10)"); c.font = font(size=8.5, color=GRAFITO); c.alignment = Alignment(horizontal="center"); c.border = B_BOTTOM
    for cc, L in ((24, "X"), (25, "Y")):
        calc(ws, r, cc, f"=Contingencia_Pct*SUM({L}{K['r0']}:{L}{r_last})", fmt=FMT_USD, color=GRAFITO, size=9)
    calc(ws, r, 26, f"=X{r}*Tasa_IVA*Contingencia_Frac_IVA", fmt=FMT_USD, color=GRAFITO, size=9); calc(ws, r, 27, f"=Y{r}*Tasa_IVA*Contingencia_Frac_IVA", fmt=FMT_USD, color=GRAFITO, size=9)
    for k, (nm_, L) in enumerate(SPLIT_NAMES):
        for j in range(3):
            cc = SPLIT0 + k * 3 + j
            if k < 2:
                calc(ws, r, cc, f"=Contingencia_Pct*SUM({col(cc)}{K['r0']}:{col(cc)}{r_last})", fmt=FMT_USD, color=GRAFITO, size=9)
            else:
                src_cc = SPLIT0 + (k - 2) * 3 + j   # IVA de la contingencia: sobre la partición del capitalizable
                calc(ws, r, cc, f"={col(src_cc)}{r}*Tasa_IVA*Contingencia_Frac_IVA", fmt=FMT_USD, color=GRAFITO, size=9)
    for cc in range(4, 14): ws.cell(row=r, column=cc).border = B_BOTTOM
    ws.cell(row=r, column=15).border = B_BOTTOM
    r = K["sub"]
    label(ws, r, 3, "Subtotal EPC = valor del proyecto (base del fee)", bold=True)
    calc(ws, r, 14, f"=SUM(N{K['r0']}:N{K['cont']})", fmt=FMT_USD, bold=True, size=9)
    calc(ws, r, 16, f"=SUM(P{K['r0']}:P{K['cont']})", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 17, f"=N{r}/(Potencia_DC*1000)", fmt=FMT_WP, bold=True, size=9)
    for cc in list(range(24, 28)) + list(range(SPLIT0, SPLIT0 + 12)):
        calc(ws, r, cc, f"=SUM({col(cc)}{K['r0']}:{col(cc)}{K['cont']})", fmt=FMT_USD, color=GRAFITO, size=9)
    total_row(ws, r, 2, 21)
    name(wb, "Subtotal_EPC", S5, f"$N${r}")
    r = K["fee"]
    label(ws, r, 2, 11, size=9, bold=True); label(ws, r, 3, '="Gerencia del proyecto — Exergy ("&TEXT(Fee_Gerencia_Pct,"0%")&" del valor del proyecto)"')
    calc(ws, r, 14, f"=Fee_Gerencia_Pct*N{K['sub']}", fmt=FMT_USD, bold=True, size=9)
    inp(ws, r, 15, 0.15, fmt=FMT_PCT0)
    calc(ws, r, 23, f"=N{r}", fmt=FMT_USD, color=GRAFITO, size=9); calc(ws, r, 16, f"=W{r}*O{r}", fmt=FMT_USD, size=9); calc(ws, r, 17, f"=N{r}/(Potencia_DC*1000)", fmt=FMT_WP, size=9)
    c = ws.cell(row=r, column=18, value="(11)"); c.font = font(size=8.5, color=GRAFITO); c.alignment = Alignment(horizontal="center"); c.border = B_BOTTOM
    for cc, L in ((24, "X"), (25, "Y")):
        calc(ws, r, cc, f"=Fee_Gerencia_Pct*{L}{K['sub']}", fmt=FMT_USD, color=GRAFITO, size=9)
    calc(ws, r, 26, f"=X{r}*O{r}", fmt=FMT_USD, color=GRAFITO, size=9); calc(ws, r, 27, f"=Y{r}*O{r}", fmt=FMT_USD, color=GRAFITO, size=9)
    for k, (nm_, L) in enumerate(SPLIT_NAMES):
        for j in range(3):
            cc = SPLIT0 + k * 3 + j
            if k < 2:
                calc(ws, r, cc, f"=Fee_Gerencia_Pct*{col(cc)}{K['sub']}", fmt=FMT_USD, color=GRAFITO, size=9)
            else:
                calc(ws, r, cc, f"={col(SPLIT0 + (k - 2) * 3 + j)}{r}*O{r}", fmt=FMT_USD, color=GRAFITO, size=9)
    for cc in range(4, 14): ws.cell(row=r, column=cc).border = B_BOTTOM
    name(wb, "Fee_Gerencia_USD", S5, f"$N${r}")
    r = K["tot"]
    label(ws, r, 3, "TOTAL CAPEX INDUSTRIAL SALELGI (sin IVA, sin terreno) — base del fee y de la depreciación", bold=True)
    calc(ws, r, 14, f"=N{K['sub']}+N{K['fee']}", fmt=FMT_USD, bold=True, size=10, color=TERRACOTA)
    calc(ws, r, 16, f"=P{K['sub']}+P{K['fee']}", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 17, f"=N{r}/(Potencia_DC*1000)", fmt=FMT_WP, bold=True, size=9)
    for cc in list(range(24, 28)) + list(range(SPLIT0, SPLIT0 + 12)):
        calc(ws, r, cc, f"={col(cc)}{K['sub']}+{col(cc)}{K['fee']}", fmt=FMT_USD, color=GRAFITO, size=9)
    total_row(ws, r, 2, 21)
    ws.cell(row=r, column=14).font = Font(name=FONT, bold=True, size=10, color=TERRACOTA)
    name(wb, "CAPEX_Total", S5, f"$N${r}"); name(wb, "IVA_Total", S5, f"$P${r}")
    name(wb, "CAPEX_SC_f1", S5, f"$X${r}"); name(wb, "CAPEX_CC_f1", S5, f"$Y${r}"); name(wb, "IVA_SC_f1", S5, f"$Z${r}"); name(wb, "IVA_CC_f1", S5, f"$AA${r}")
    for k, (nm_, L) in enumerate(SPLIT_NAMES):
        for j, suf in enumerate(("Wp", "Wac", "Fijo")):
            name(wb, f"{nm_}_{suf}", S5, f"${col(SPLIT0 + k * 3 + j)}${r}")
    r = K["tot_iva"]
    label(ws, r, 3, "Total industrial con IVA", bold=True); calc(ws, r, 14, f"=N{K['tot']}+P{K['tot']}", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 17, f"=N{r}/(Potencia_DC*1000)", fmt=FMT_WP, bold=True, size=9)
    r = K["terreno"]
    label(ws, r, 2, 12, size=9, bold=True); label(ws, r, 3, '="Terreno comprado por SALELGI ("&TEXT(Hectareas,"0.0")&" ha × "&TEXT(Precio_Terreno_ha,"#,##0")&" $/ha + "&TEXT(Costos_Transaccion_Terreno_Pct,"0.0%")&" transacción) — sólo si Comprador_Terreno = SALELGI"')
    calc(ws, r, 14, '=IF(Comprador_Terreno="SALELGI",Precio_Terreno_ha*Hectareas*(1+Costos_Transaccion_Terreno_Pct),0)', fmt=FMT_USD, bold=True, size=9)
    calc(ws, r, 17, f"=N{r}/(Potencia_DC*1000)", fmt=FMT_WP, size=9)
    c = ws.cell(row=r, column=18, value="(12)"); c.font = font(size=8.5, color=GRAFITO); c.alignment = Alignment(horizontal="center"); c.border = B_BOTTOM
    name(wb, "Terreno_SALELGI", S5, f"$N${r}")
    r = K["tot_terr"]
    label(ws, r, 3, "TOTAL CAPEX SALELGI con terreno (sin IVA)", bold=True); calc(ws, r, 14, f"=N{K['tot']}+N{K['terreno']}", fmt=FMT_USD, bold=True, size=10, color=TERRACOTA); calc(ws, r, 17, f"=N{r}/(Potencia_DC*1000)", fmt=FMT_WP, bold=True, size=9)
    total_row(ws, r, 2, 21); ws.cell(row=r, column=14).font = Font(name=FONT, bold=True, size=10, color=TERRACOTA)
    name(wb, "CAPEX_Total_Terreno", S5, f"$N${r}")
    r = K["aran"]
    label(ws, r, 3, "Aranceles + ISD dentro del total (costo fiscal de importación; FODINFA aparte)"); calc(ws, r, 14, f"=SUM(M{K['r0']}:M{r_last})", fmt=FMT_USD, size=9); name(wb, "Aranceles_ISD", S5, f"$N${r}")
    calc(ws, r, 16, f"=SUM(K{K['r0']}:K{r_last})", fmt=FMT_USD, size=9, color=GRAFITO); label(ws, r, 15, "FODINFA →", size=8.5, color=GRAFITO)
    r = K["civil"]
    label(ws, r, 3, "% del CAPEX industrial en obra civil (vida fiscal 20 años)"); calc(ws, r, 14, f"=N{K['r0']+5}/N{K['tot']}", fmt=FMT_PCT, size=9)
    name(wb, "Pct_CAPEX_Civil", S5, f"$N${r}")
    # encabezado auxiliar y ocultas (S:U quedan libres y ocultas: los drivers viven en su tabla)
    hdr(ws, K["hdr"], 22, 27, ["Cargado a GPM\n(aux., f=1)", "Base IVA\n(aux.)", "Cap. sin\ncontrato @f1", "Cap. con\ncontrato @f1", "IVA sin\ncontrato @f1", "IVA con\ncontrato @f1"], fill_hex=LINO, color=GRAFITO, height=32)
    hdr(ws, K["hdr"], SPLIT0, SPLIT0 + 11, [f"{nm_}\n{suf}" for nm_, L in SPLIT_NAMES for suf in ("Wp", "Wac", "fijo")], fill_hex=LINO, color=GRAFITO, height=32)
    ws.column_dimensions.group("S", col(SPLIT0 + 11), hidden=True, outline_level=1)
    # ---- Caso activo y comparativo
    r = K["civil"] + 2
    section(ws, r, 2, 9, "Caso Custom y comparativo de los cuatro casos (sin IVA, incl. gerencia, sin terreno)")
    r += 1
    label(ws, r, 3, "Definición del CAPEX Custom"); link(ws, r, 4, '=IF(N(CAPEX_Fijo_Wp)>0,"fijo "&TEXT(CAPEX_Fijo_Wp,"0.000")&" $/Wp","bottom-up × "&TEXT(Factor_CAPEX,"0.00"))', bold=True); ws.cell(row=r, column=4).alignment = Alignment(horizontal="right")
    r += 1
    label(ws, r, 3, "Bottom-up a factor 1 (potencia y contrato de 01)"); calc(ws, r, 4, f'=IF(Contrato_Inversion="Sí",Escala_Wp*CAPEX_CC_Wp+Escala_Wac*CAPEX_CC_Wac+CAPEX_CC_Fijo,Escala_Wp*CAPEX_SC_Wp+Escala_Wac*CAPEX_SC_Wac+CAPEX_SC_Fijo)', fmt=FMT_USD)
    r_b1 = r
    name(wb, "CAPEX_Base_f1", S5, f"$D${r}")
    r += 1
    label(ws, r, 3, "Escalación de precios hasta la compra (Custom)"); calc(ws, r, 4, "=Fase_m1*(1+Escalacion_CAPEX)^MAX(0,Anios_Precios-1)+(1-Fase_m1)*(1+Escalacion_CAPEX)^MAX(0,Anios_Precios)", fmt="0.0000")
    name(wb, "Factor_Escalacion", S5, f"$D${r}")
    note(ws, r, 5, '="Precios de "&TEXT(Fecha_Precios,"mmm-yyyy")&" escalados al "&TEXT(Escalacion_CAPEX,"0.0%")&"/año: tramo −1 ("&TEXT(Fase_m1,"0%")&") a "&TEXT(MAX(0,Anios_Precios-1),"0.0")&" años · tramo 0 a "&TEXT(Anios_Precios,"0.0")&" años (COD "&TEXT(Fecha_COD,"mmm-yyyy")&"). Bloque B: C "&TEXT(INDEX(Esc_Escalacion_CAPEX,2),"0%")&" · B "&TEXT(INDEX(Esc_Escalacion_CAPEX,3),"0%")&" · F "&TEXT(INDEX(Esc_Escalacion_CAPEX,4),"0%")', border=True, valign="center", c2=14)
    r += 1
    label(ws, r, 3, "Factor del Custom (× cada rubro), incl. escalación", bold=True)
    calc(ws, r, 4, f'=IF(N(CAPEX_Fijo_Wp)>0,CAPEX_Fijo_Wp*Potencia_DC*1000/D{r_b1},Factor_CAPEX)*Factor_Escalacion', fmt="0.000", bold=True)
    name(wb, "Factor_Caso", S5, f"$D${r}")
    r += 2
    hdr(ws, r, 3, 14, ["Caso", "Total sin IVA [USD]", "$/Wp", "IVA [USD]", "", "Total con IVA [USD]", "Definición del CAPEX en el caso"] + [""] * 5, height=30)
    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7)
    ws.cell(row=r, column=6, value="IVA [USD]")
    ws.merge_cells(start_row=r, start_column=9, end_row=r, end_column=14)
    ws.cell(row=r, column=9).alignment = Alignment(horizontal="left", vertical="center")
    # v2.0: los cuatro casos se leen del Motor (misma lógica que 05 para la potencia y el contrato vigentes); Custom primero (d1)
    tails = {"X": '" · caso de trabajo: gobierna 04–09 y la portada"',
             "C": '" · rango alto del estudio CAPEX/OPEX (jul-2026)"',
             "B": '" · costo real para el grupo con gerencia Exergy al "&TEXT(Fee_Gerencia_Pct,"0%")',
             "F": None}
    r_cases = {}
    for key in CASE_KEYS:
        r += 1
        r_cases[key] = r
        mc = MOTOR_CASE_COL[key]; k = CASE_KEYS.index(key) + 1
        lc = ws.cell(row=r, column=3, value=CASO_NOMBRE[key]); lc.font = Font(name=FONT, bold=True, color=CASO_COL[key], size=SZ_BODY); lc.border = B_BOTTOM; lc.alignment = Alignment(vertical="center")
        calc(ws, r, 4, f"='{SM}'!${mc}${SCAL_ROWS['K']}", fmt=FMT_USD, bold=(key == "X")); calc(ws, r, 5, f"=D{r}/(Potencia_DC*1000)", fmt=FMT_WP, bold=(key == "X"))
        calc(ws, r, 6, f"='{SM}'!${mc}${SCAL_ROWS['IVA']}", fmt=FMT_USD); ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7); calc(ws, r, 8, f"=D{r}+F{r}", fmt=FMT_USD)
        if key == "X":
            defn = '=IF(N(CAPEX_Fijo_Wp)>0,"Fijo "&TEXT(CAPEX_Fijo_Wp,"0.000")&" $/Wp","Bottom-up × "&TEXT(Factor_CAPEX,"0.00"))&IF(Escalacion_CAPEX>0," · precios +"&TEXT(Escalacion_CAPEX,"0.0%")&"/año","")'
        else:
            defn = f'=IF(N(INDEX(Esc_CAPEX_Fijo_Wp,{k}))>0,"Fijo "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,{k}),"0.000")&" $/Wp","Bottom-up × "&TEXT(INDEX(Esc_Factor_CAPEX,{k}),"0.00"))&IF(INDEX(Esc_Escalacion_CAPEX,{k})>0," · precios +"&TEXT(INDEX(Esc_Escalacion_CAPEX,{k}),"0.0%")&"/año","")'
        if key == "F":
            defn += f'&" · precio «llave en mano todo incluido» del deck v4 (22-jul-2026) para cliente externo; exige "&TEXT(D{r}/D{r_cases["B"]}-1,"+0%;-0%")&" vs costo real → verificar con 3 cotizaciones EPC"'
        else:
            defn += "&" + tails[key]
        note(ws, r, 9, defn, border=True, valign="center", c2=14); fit_row(ws, r, [("x" * 125, 60, 8.5)], min_h=16)
    # ---- v3.0 (M-c): reemplazo de inversores y desmantelamiento (capa de diseño; el Motor los aplica a los cuatro casos)
    r += 2
    section(ws, r, 2, 14, "Reemplazo de inversores y desmantelamiento", guide="capa de diseño compartida por los cuatro casos; el pagador lo fija el contrato de O&M", guide_col=4)
    r += 1
    hdr(ws, r, 3, 14, ["Partida", "Año (t)", "Base", "", "Monto [USD]", "Pagador", "Nota"] + [""] * 5, height=18)
    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7); ws.merge_cells(start_row=r, start_column=9, end_row=r, end_column=14)
    ws.cell(row=r, column=9).alignment = Alignment(horizontal="left", vertical="center")
    r += 1
    label(ws, r, 3, "Reemplazo de inversores"); calc(ws, r, 4, "=Reemplazo_Anio", fmt="0"); calc(ws, r, 5, '=TEXT(Reemplazo_USD_Wac,"0.00")&" $/Wac × "&TEXT(Potencia_AC,"#,##0")&" kWac"', align="right", color=GRAFITO, size=9)
    ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=7)
    calc(ws, r, 8, '=IF(Reemplazo_Pagador="No",0,Reemplazo_USD_Wac*Potencia_AC*1000)', fmt=FMT_USD, bold=True); name(wb, "Reemplazo_USD", S5, f"$H${r}")
    calc(ws, r, 9, "=Reemplazo_Pagador", align="center")
    note(ws, r, 10, '=IF(Reemplazo_Pagador="SALELGI","Capex de SALELGI en t = "&Reemplazo_Anio&", depreciado en "&MIN(Vida_Fiscal_Equipos,Horizonte-Reemplazo_Anio)&" años (07, 08)",IF(Reemplazo_Pagador="Exergy","Gasto de Exergy en t = "&Reemplazo_Anio&" con cargo a la reserva del fee de O&M (09); sin efecto en SALELGI","Sin reemplazo (neutro ≡ v2.0): la reserva de inversores se supone dentro del fee de O&M"))', border=True, valign="center", c2=14)
    ws.row_dimensions[r].height = 16
    r += 1
    label(ws, r, 3, "Desmantelamiento al final del horizonte"); calc(ws, r, 4, "=Horizonte", fmt="0"); calc(ws, r, 5, '=TEXT(Desmantelamiento_Pct,"0.0%")&" del CAPEX industrial"', align="right", color=GRAFITO, size=9)
    ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=7)
    calc(ws, r, 8, "=Desmantelamiento_Pct*CAPEX_Total", fmt=FMT_USD, bold=True); name(wb, "Desmantelamiento_USD", S5, f"$H${r}")
    calc(ws, r, 9, "SALELGI", align="center")
    note(ws, r, 10, "Gasto deducible de SALELGI en t = Horizonte (desmontaje y disposición, neto de chatarra); 0 en el Base, 2 % en el tornado", border=True, valign="center", c2=14)
    ws.row_dimensions[r].height = 16
    # ---- v3.0 (V7): drivers de escala en tabla propia (C..H) con su control (A6); nombres Drv_Wp / Drv_Wac / Drv_Fijo (los lee la tabla de rubros y la sombra)
    r += 2
    section(ws, r, 2, LCC, "Drivers de escala de cada rubro (· por confirmar)", guide="qué parte de cada rubro sigue a la potencia DC (Wp), a la AC (Wac) o es fija; costo = base × [%Wp × Escala_Wp + %Wac × Escala_Wac + %fijo]", guide_col=5)
    r += 1
    hdr(ws, r, 2, 8, ["#", "Rubro", "% Wp", "% Wac", "% fijo", "Σ", "Control"], height=18)
    r += 1
    d0 = r
    for i, (nm, alc, cost, comp, imp, ar, iva, src, wwp, wwac, wfx) in enumerate(RUBROS):
        label(ws, r, 2, i + 1, size=9, bold=True); label(ws, r, 3, nm, size=9)
        inp(ws, r, 4, wwp, fmt=FMT_PCT0, confirm=True); inp(ws, r, 5, wwac, fmt=FMT_PCT0, confirm=True); inp(ws, r, 6, wfx, fmt=FMT_PCT0, confirm=True)
        calc(ws, r, 7, f"=D{r}+E{r}+F{r}", fmt=FMT_PCT0, size=9, color=GRAFITO)
        calc(ws, r, 8, f'=IF(ABS(G{r}-1)<0.0005,"●","■ ≠ 100 %")', align="center", size=9, color=GRAFITO)
        ws.row_dimensions[r].height = 15
        r += 1
    d1 = r - 1
    name(wb, "Drv_Wp", S5, f"$D${d0}:$D${d1}"); name(wb, "Drv_Wac", S5, f"$E${d0}:$E${d1}"); name(wb, "Drv_Fijo", S5, f"$F${d0}:$F${d1}")
    label(ws, r, 3, "Control de drivers (13 A6)", size=9)
    label(ws, r, 4, f'=IF(SUMPRODUCT(--(ABS(D{d0}:D{d1}+E{d0}:E{d1}+F{d0}:F{d1}-1)>0.0005))=0,"● drivers OK","■ drivers ≠ 100 %")', size=9, bold=True, color=SALVIA, border=False)
    name(wb, "Check_Drivers", S5, f"$D${r}")
    note(ws, r, 6, '="Escala_Wp = "&TEXT(Escala_Wp,"0.000")&" · Escala_Wac = "&TEXT(Escala_Wac,"0.000")&" (potencia "&TEXT(Potencia_DC,"#,##0")&" kWp / "&TEXT(Potencia_AC,"#,##0")&" kWac; ε = "&TEXT(Exponente_Escala,"0.00")&"). Pesos estimados; validez 3–8 MWp."', border=True, valign="center", c2=LCC)
    ws.row_dimensions[r].height = 15
    r += 2
    # gráfico de barras (debajo de los drivers, B..H)
    chart_hbars(ws, f"B{r}", "CAPEX capitalizable por rubro (USD, sin IVA)", Reference(ws, min_col=3, min_row=K["r0"], max_row=r_last),
                Reference(ws, min_col=14, min_row=K["r0"], max_row=r_last), w=15.5, h=7.6, fmt=FMT_USD, accent_idx=0)
    NCH5 = 16
    for k in range(r, r + NCH5):
        ws.row_dimensions[k].height = 15   # 16 × 14 = 224 pt ≥ 7,6 cm (215 pt)
    r += NCH5
    # ---- Notas al pie
    section(ws, r, 2, LCC, "Notas — alcance y fuente de cada rubro")
    r += 1
    for i, (nm, alc, cost, comp, imp, ar, iva, src, wwp, wwac, wfx) in enumerate(RUBROS):
        txt = f"({i+1}) {nm}. {alc} {src} Drivers de escala: {wwp:.0%} Wp · {wwac:.0%} Wac · {wfx:.0%} fijo."
        note(ws, r, 2, txt, c2=LCC, valign="top")
        fit_row(ws, r, [(txt, merged_width(ws, 2, LCC) - 4, 8.5)])
        r += 1
    for txt in ["(10) Contingencia 6 % (estudio CAPEX: 5–8 %). IVA sobre la fracción Contingencia_Frac_IVA (mezcla de bienes y servicios gravados).",
                "(11) Fee de gerencia (decisión Jorge 01-09-2026), servicio gravado con IVA 15 % (recuperable por SALELGI). Se capitaliza y deprecia como parte del activo. Base: subtotal EPC sin terreno.",
                "(12) Terreno: si lo compra SALELGI entra al CAPEX con sus costos de transacción (alcabala 1 % + notaría/registro); no se deprecia, no es elegible para la deducción adicional ni base del fee; se recupera al final del horizonte (Residual_Terreno_Pct). Si lo compra Exergy (defecto) va al flujo de Exergy (09) y SALELGI paga arriendo (06).",
                "Drivers de escala: cada rubro se descompone en la parte que sigue a la potencia DC (Wp), a la potencia AC (Wac: inversores, transformación, parte del BOS/montaje) y la parte fija (conexión, permisos, obra civil de acceso). Costo = base × [%Wp × (P/5.000)^(1−ε) + %Wac × (AC/3.788)^(1−ε) + %fijo]. Pesos estimados, marcados «por confirmar»; validez 3–8 MWp; ε = Exponente_Escala (0 = lineal, ácido).",
                "Conciliación con el deck v4 (22-jul-2026): el deck usa 750 k$/MWp como precio comercial a un cliente externo; este libro evalúa el costo real para el grupo (SALELGI paga costo + gerencia 7 %). La diferencia (≈ 0,07–0,10 $/Wp) es margen/riesgo EPC que aquí no existe porque Exergy gerencia con multi-contrato. Estudio interno 0,85–1,15 $/Wp (10 MWp, con terreno, margen EPC e IVA de BOS) → aquí 0,82 sin IVA, sin terreno y sin margen EPC, con IVA recuperable.",
                "Si IVA_Recuperable = Sí, el IVA es capital de trabajo (se recupera en el período siguiente); si No, se capitaliza y deprecia. Con Contrato de Inversión, aranceles e ISD sobre bienes de capital = 0 (exoneración arancelaria + exención ISD art. 159.16); el FODINFA se mantiene.",
                "Escalación de precios: Escalacion_CAPEX (bloque B, desde Fecha_Precios) multiplica cada rubro a través de Factor_Caso (Factor_Escalacion); el reemplazo de inversores y el desmantelamiento son partidas aparte que el Motor aplica a los cuatro casos según la capa de diseño de 01."]:
        note(ws, r, 2, txt, c2=LCC, valign="top"); fit_row(ws, r, [(txt, merged_width(ws, 2, LCC) - 4, 8.5)]); r += 1
    setup_print(ws, landscape=True, area=f"A1:{col(LCC)}{r}")
    return ws


# ---------------------------------------------------------------- 06_OPEX
def build_opex(wb):
    O = OPEX
    ws = wb.create_sheet(S6)
    time_widths(ws)
    sheet_header(ws, "6 · OPEX de SALELGI", "Costo anual del dueño del SGDA: fee de O&M a Exergy, seguros, arriendo o predial del terreno y tributos locales; todo escala con Escalacion_OPEX. Alimenta 07 (con el Factor_OPEX del caso) y el Motor.", 6, last_col=12, total=NSHEETS)
    section(ws, O["sec_comp"], 2, 12, "Composición del año 1", guide="año 1 del caso Custom; el detalle anual está debajo", guide_col=8)
    hdr(ws, O["comp0"] - 1, 2, 6, ["Línea", "", "USD/año", "$/kWp", "% del total"], height=16)
    comp = [("Fee O&M todo incluido → Exergy", O["fee"]), ("Seguros all-risk + RC (dueño)", O["seg"]), ("Arriendo del terreno → Exergy (si Exergy es dueña)", O["arr"]), ("Predial y gastos del terreno (si SALELGI es dueña)", O["pred"]), ("Tributos locales y administración", O["trib"])]
    for i, (lab, src_row) in enumerate(comp):
        r = O["comp0"] + i
        label(ws, r, 2, lab); unit(ws, r, 3, "USD"); calc(ws, r, 4, f"={C(1)}{src_row}", fmt=FMT_USD); calc(ws, r, 5, f"=D{r}/Potencia_DC", fmt=FMT_DEC1); calc(ws, r, 6, f"=IF($D${O['comp0']+5}>0,D{r}/$D${O['comp0']+5},0)", fmt=FMT_PCT)
        ws.row_dimensions[r].height = 16
    r = O["comp0"] + 5
    label(ws, r, 2, "Total OPEX año 1", bold=True); unit(ws, r, 3, "USD"); calc(ws, r, 4, f"=SUM(D{O['comp0']}:D{r-1})", fmt=FMT_USD, bold=True); calc(ws, r, 5, f"=D{r}/Potencia_DC", fmt=FMT_DEC1, bold=True); calc(ws, r, 6, f"=SUM(F{O['comp0']}:F{r-1})", fmt=FMT_PCT, bold=True)
    total_row(ws, r, 2, 6); ws.row_dimensions[r].height = 16
    cbox = ws.cell(row=O["comp0"], column=8, value="Referencia: estudio CAPEX/OPEX (jul-2026), 20 $/kWp-año «todo incluido» a suelo (desglose en 12 §D). SALELGI paga fee 20 + seguros 3,5 + arriendo o predial + tributos ≈ 30 $/kWp-año; el IVA de estos servicios es crédito y no se modela.")
    cbox.font = Font(name=FONT, size=8.5, color=GRAFITO); cbox.alignment = Alignment(vertical="top", wrap_text=True, indent=1)
    cbox.border = Border(left=Side(style="medium", color=ARENA_D))
    ws.merge_cells(start_row=O["comp0"], start_column=8, end_row=O["comp0"] + 5, end_column=12)
    ws.row_dimensions[O["sec_serie"] - 1].height = 8
    section(ws, O["sec_serie"], 2, LAST_T_COL, "Serie anual")
    time_header(ws, O["t"])
    tr = O["t"]
    g = lambda T: f"(1+Escalacion_OPEX)^({T}-1)"
    row_formula(ws, O["fee"], "Fee O&M todo incluido → Exergy", lambda t, T: f"=IF(OR({T}<1,{T}>Horizonte),0,Fee_OM_kWp*Potencia_DC*{g(T)})", unit_txt="USD", trow=tr)
    row_formula(ws, O["seg"], "Seguros all-risk + RC (SALELGI dueño)", lambda t, T: f"=IF(OR({T}<1,{T}>Horizonte),0,Seguro_kWp*Potencia_DC*{g(T)})", unit_txt="USD", trow=tr)
    row_formula(ws, O["arr"], "Arriendo del terreno → Exergy (0 si SALELGI compra)", lambda t, T: f'=IF(OR({T}<1,{T}>Horizonte,Comprador_Terreno="SALELGI"),0,Renta_Terreno_ha*Hectareas*{g(T)})', unit_txt="USD", trow=tr)
    row_formula(ws, O["pred"], "Predial y gastos del terreno (SALELGI dueña)", lambda t, T: f'=IF(OR({T}<1,{T}>Horizonte,Comprador_Terreno<>"SALELGI"),0,Predial_Terreno*{g(T)})', unit_txt="USD", trow=tr)
    row_formula(ws, O["trib"], "Tributos locales y administración", lambda t, T: f"=IF(OR({T}<1,{T}>Horizonte),0,Tributos_Locales*{g(T)})", unit_txt="USD", trow=tr)
    row_formula(ws, O["total"], "Total OPEX SALELGI", lambda t, T: f"=SUM({C(t)}{O['fee']}:{C(t)}{O['trib']})", unit_txt="USD", bold=True, total=True, trow=tr)
    name(wb, "OPEX_Anio1", S6, f"${C(1)}${O['total']}"); name(wb, "OPEX_Row", S6, rng(O["total"]))
    row_formula(ws, O["unit"], "OPEX unitario", lambda t, T: f"=IF({C(t)}{O['total']}>0,{C(t)}{O['total']}/Potencia_DC,0)", fmt=FMT_DEC1, unit_txt="$/kWp", color=GRAFITO, trow=tr)
    section(ws, O["memo_sec"], 2, LAST_T_COL, "Memo · costos propios de Exergy (→ 09)")
    years_in_section(ws, O["memo_sec"], O["t"])
    row_formula(ws, O["memo_cost"], "Costo propio de O&M de Exergy", lambda t, T: f"=IF(OR({T}<1,{T}>Horizonte),0,Costo_OM_Exergy_kWp*Potencia_DC*{g(T)})", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, O["memo_predial"], "Predial y gastos del terreno (Exergy dueña)", lambda t, T: f'=IF(OR({T}<1,{T}>Horizonte,Comprador_Terreno="SALELGI"),0,Predial_Terreno*{g(T)})', unit_txt="USD", color=GRAFITO, trow=tr)
    series_layout(ws, O["t"], summary_last_col=12)
    return ws


# ---------------------------------------------------------------- 07_Fiscal
def build_fiscal(wb):
    Fz = FISCAL
    ws = wb.create_sheet(S7)
    time_widths(ws, label_w=50)
    sheet_header(ws, "7 · Fiscal", "Impuestos incrementales de SALELGI: participación 15 % e IR 25 % con deducción adicional topada (art. 10.7); pérdidas absorbidas sin límite (Escudo_Negativo) o hasta Utilidad_Gravable_SALELGI con pool de arrastre (art. 11). Alimenta 08 y el Motor.", 7, last_col=12, total=NSHEETS)
    section(ws, Fz["panel_sec"], 2, 12, "Cifras fiscales clave")
    p = Fz["panel0"]
    label(ws, p, 2, "CAPEX depreciable (sin IVA; + IVA si no se recupera)"); calc(ws, p, 4, '=CAPEX_Total+IF(IVA_Recuperable="No",IVA_Total,0)', fmt=FMT_USD, bold=True); unit(ws, p, 3, "USD")
    name(wb, "CAPEX_Depreciable", S7, f"$D${p}")
    label(ws, p + 1, 2, "Deducción adicional anual (años 1–10, topada; 0 si Aplica_DedAd = No)"); calc(ws, p + 1, 4, '=IF(Aplica_DedAd="Sí",1,0)*MIN(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos,Tope_DedAd_Pct*Ingresos_SALELGI)', fmt=FMT_USD, bold=True); unit(ws, p + 1, 3, "USD/año")
    name(wb, "DedAd_Anual", S7, f"$D${p+1}")
    label(ws, p + 2, 2, "¿El tope del 5 % de ingresos es vinculante?"); ws.cell(row=p + 2, column=3).border = B_BOTTOM
    chip(ws, p + 2, 4, '=IF(Aplica_DedAd="No","◇ n/a — sin deducción adicional (Aplica_DedAd = No)",IF(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos>Tope_DedAd_Pct*Ingresos_SALELGI,"▲ SÍ — tope activo","● No — cabe completa"))', kind="ok", c2=6)
    for cc in (4, 5, 6): ws.cell(row=p + 2, column=cc).border = B_BOTTOM
    label(ws, p + 3, 2, "Ingreso mínimo para deducir el 100 % (tope 5 %)"); calc(ws, p + 3, 4, "=CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos/Tope_DedAd_Pct", fmt=FMT_USD); unit(ws, p + 3, 3, "USD/año")
    cbox = ws.cell(row=p, column=7, value='="Deducción adicional del 100 % sobre «maquinarias, equipos y tecnologías» de SGDA con ERNC (art. 10 num. 7 LRTI; tope 5 % de los ingresos confirmado). Exige certificación ambiental previa a la primera declaración (RLRTI art. 28.6.g; procedimiento no publicado, Atlas P-01): Aplica_DedAd = "&Aplica_DedAd&". Con ingresos de "&TEXT(Ingresos_SALELGI/1000000,"0.0")&" M el tope "&IF(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos>Tope_DedAd_Pct*Ingresos_SALELGI,"SÍ muerde","no muerde")&"; por debajo de "&TEXT(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos/Tope_DedAd_Pct/1000000,"0.0")&" M sí. Sin la certificación: caso «Sin deducción adicional» del tornado (10 §B)."')
    cbox.font = Font(name=FONT, size=8.5, color=GRAFITO); cbox.alignment = Alignment(vertical="top", wrap_text=True, indent=1)
    cbox.border = Border(left=Side(style="medium", color=ARENA_D))
    ws.merge_cells(start_row=p, start_column=7, end_row=p + 3, end_column=12)
    time_header(ws, Fz["t"])
    tr = Fz["t"]
    section(ws, Fz["secA"], 2, LAST_T_COL, "A · Sin deuda (proyecto puro)")
    row_formula(ws, Fz["ahorro"], "Ahorro por energía evitada (energía valorizable × tarifa)", lambda t, T: f"=IF(OR({T}<1,{T}>Horizonte),0,INDEX(E_Val,1,{T}+2)*1000*Tarifa_Evitable*(1+Eff_EscT)^({T}-1))", unit_txt="USD", trow=tr)
    name(wb, "Ahorro_Row", S7, rng(Fz["ahorro"]))
    row_formula(ws, Fz["opex"], "OPEX SALELGI (× Factor_OPEX del caso)", lambda t, T: f"='{S6}'!{C(t)}{OPEX['total']}*Eff_fO", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, Fz["peaje"], "Peaje SGDA: energía inyectada × $/kWh + potencia AC × $/kW-mes × 12", lambda t, T: f"=IF({T}<1,0,INDEX(E_Activa,1,{T}+2)*1000*Eff_Peaje*INDEX(Frac_Peaje,1,{T}+2)+IF({T}<=Horizonte,Potencia_AC*Peaje_kW_mes*12*INDEX(Frac_Peaje,1,{T}+2),0))", unit_txt="USD", trow=tr)
    name(wb, "Peaje_Row", S7, rng(Fz["peaje"]))
    row_formula(ws, Fz["decom"], "Desmantelamiento en t = Horizonte (gasto deducible)", lambda t, T: f"=IF({T}=Horizonte,Desmantelamiento_USD,0)", unit_txt="USD", trow=tr)
    row_formula(ws, Fz["ebitda"], "EBITDA incremental (ahorro − OPEX − peaje − desmantelamiento)", lambda t, T: f"={C(t)}{Fz['ahorro']}-{C(t)}{Fz['opex']}-{C(t)}{Fz['peaje']}-{C(t)}{Fz['decom']}", unit_txt="USD", bold=True, trow=tr)
    row_formula(ws, Fz["depeq"], "Depreciación equipos (10 años)", lambda t, T: f"=IF(AND({T}>=1,{T}<=Vida_Fiscal_Equipos),CAPEX_Depreciable*(1-Pct_CAPEX_Civil)/Vida_Fiscal_Equipos,0)", unit_txt="USD", trow=tr)
    row_formula(ws, Fz["depciv"], "Depreciación obra civil (20 años)", lambda t, T: f"=IF(AND({T}>=1,{T}<=Vida_Fiscal_Civil,{T}<=Horizonte),CAPEX_Depreciable*Pct_CAPEX_Civil/Vida_Fiscal_Civil,0)", unit_txt="USD", trow=tr)
    row_formula(ws, Fz["deprep"], "Depreciación del reemplazo de inversores (si lo paga SALELGI; 10 años o hasta el horizonte)", lambda t, T: f'=IF(AND(Reemplazo_Pagador="SALELGI",Reemplazo_Anio<Horizonte,{T}>Reemplazo_Anio,{T}<=MIN(Horizonte,Reemplazo_Anio+Vida_Fiscal_Equipos)),Reemplazo_USD/MIN(Vida_Fiscal_Equipos,Horizonte-Reemplazo_Anio),0)', unit_txt="USD", trow=tr)
    row_formula(ws, Fz["utap"], "Utilidad contable incremental antes de participación", lambda t, T: f"={C(t)}{Fz['ebitda']}-{C(t)}{Fz['depeq']}-{C(t)}{Fz['depciv']}-{C(t)}{Fz['deprep']}", unit_txt="USD", trow=tr)
    UG = "Utilidad_Gravable_SALELGI"
    Ut = lambda T: f"IF({T}>=1,{UG},0)"
    row_formula(ws, Fz["part"], "Participación laboral 15 % (absorción limitada si hay utilidad gravable)", lambda t, T: f'=IF(Incluir_Participacion="Sí",IF(ISNUMBER({UG}),IF({C(t)}{Fz["utap"]}>=0,Tasa_Participacion*{C(t)}{Fz["utap"]},-Tasa_Participacion*MIN(-{C(t)}{Fz["utap"]},{Ut(T)})),IF(Escudo_Negativo="Sí",Tasa_Participacion*{C(t)}{Fz["utap"]},MAX(0,Tasa_Participacion*{C(t)}{Fz["utap"]}))),0)', unit_txt="USD", trow=tr)
    row_formula(ws, Fz["utair"], "Utilidad antes de IR", lambda t, T: f"={C(t)}{Fz['utap']}-{C(t)}{Fz['part']}", unit_txt="USD", trow=tr)
    row_formula(ws, Fz["dedad"], "Deducción adicional 100 % (art. 10.7, topada)", lambda t, T: f"=IF(AND({T}>=1,{T}<=Vida_Fiscal_Equipos),DedAd_Anual,0)", unit_txt="USD", trow=tr)
    row_formula(ws, Fz["base"], "Base imponible incremental", lambda t, T: f"={C(t)}{Fz['utair']}-{C(t)}{Fz['dedad']}", unit_txt="USD", trow=tr)
    prev = lambda t, row: ("0" if t == T_MIN else f"{C(t-1)}{row}")
    row_formula(ws, Fz["pool"], "Pool de pérdidas arrastradas (art. 11 LRTI, ≤ 25 %/año) — sólo con utilidad gravable limitada", lambda t, T: f"=IF(ISNUMBER({UG}),{prev(t, Fz['pool'])}+IF({C(t)}{Fz['base']}<0,-{C(t)}{Fz['base']}-MIN(-{C(t)}{Fz['base']},{Ut(T)}),-MIN({prev(t, Fz['pool'])},0.25*({C(t)}{Fz['base']}+{Ut(T)}))),0)", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, Fz["ir"], "Impuesto a la Renta 25 % (con absorción limitada y arrastre si hay utilidad gravable)", lambda t, T: f'=IF(ISNUMBER({UG}),IF({C(t)}{Fz["base"]}>=0,Tasa_IR*({C(t)}{Fz["base"]}-MIN({prev(t, Fz["pool"])},0.25*({C(t)}{Fz["base"]}+{Ut(T)}))),-Tasa_IR*MIN(-{C(t)}{Fz["base"]},{Ut(T)})),IF(Escudo_Negativo="Sí",Tasa_IR*{C(t)}{Fz["base"]},MAX(0,Tasa_IR*{C(t)}{Fz["base"]})))', unit_txt="USD", trow=tr)
    row_formula(ws, Fz["imp"], "Impuestos incrementales (participación + IR)", lambda t, T: f"={C(t)}{Fz['part']}+{C(t)}{Fz['ir']}", unit_txt="USD", bold=True, total=True, trow=tr)
    name(wb, "Imp_U_Row", S7, rng(Fz["imp"]))
    row_formula(ws, Fz["tasa"], "Tasa efectiva sobre EBITDA", lambda t, T: f"=IF({C(t)}{Fz['ebitda']}<>0,{C(t)}{Fz['imp']}/{C(t)}{Fz['ebitda']},0)", fmt=FMT_PCT, unit_txt="%", color=GRAFITO, trow=tr)
    section(ws, Fz["secB"], 2, LAST_T_COL, "B · IVA del CAPEX (capital de trabajo si es recuperable)")
    years_in_section(ws, Fz["secB"], tr)
    row_formula(ws, Fz["iva_pag"], "IVA pagado", lambda t, T: f"=IF({T}=-1,IVA_Total*Fase_m1,IF({T}=0,IVA_Total*(1-Fase_m1),0))", unit_txt="USD", trow=tr)
    row_formula(ws, Fz["iva_rec"], "IVA recuperado (período siguiente)", lambda t, T: f'=IF(IVA_Recuperable="Sí",IF({T}=0,IVA_Total*Fase_m1,IF({T}=1,IVA_Total*(1-Fase_m1),0)),0)', unit_txt="USD", trow=tr)
    section(ws, Fz["secC"], 2, LAST_T_COL, "C · Con deuda (intereses deducibles)")
    years_in_section(ws, Fz["secC"], tr)
    row_formula(ws, Fz["int"], "Intereses de la deuda", lambda t, T: f"='{S8}'!{C(t)}{FLUJO['int']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, Fz["utap_l"], "Utilidad contable antes de participación (con intereses)", lambda t, T: f"={C(t)}{Fz['ebitda']}-{C(t)}{Fz['depeq']}-{C(t)}{Fz['depciv']}-{C(t)}{Fz['deprep']}-{C(t)}{Fz['int']}", unit_txt="USD", trow=tr)
    row_formula(ws, Fz["part_l"], "Participación laboral 15 % (absorción limitada si hay utilidad gravable)", lambda t, T: f'=IF(Incluir_Participacion="Sí",IF(ISNUMBER({UG}),IF({C(t)}{Fz["utap_l"]}>=0,Tasa_Participacion*{C(t)}{Fz["utap_l"]},-Tasa_Participacion*MIN(-{C(t)}{Fz["utap_l"]},{Ut(T)})),IF(Escudo_Negativo="Sí",Tasa_Participacion*{C(t)}{Fz["utap_l"]},MAX(0,Tasa_Participacion*{C(t)}{Fz["utap_l"]}))),0)', unit_txt="USD", trow=tr)
    row_formula(ws, Fz["base_l"], "Base imponible (con intereses)", lambda t, T: f"={C(t)}{Fz['utap_l']}-{C(t)}{Fz['part_l']}-{C(t)}{Fz['dedad']}", unit_txt="USD", trow=tr)
    row_formula(ws, Fz["pool_l"], "Pool de pérdidas arrastradas con deuda", lambda t, T: f"=IF(ISNUMBER({UG}),{prev(t, Fz['pool_l'])}+IF({C(t)}{Fz['base_l']}<0,-{C(t)}{Fz['base_l']}-MIN(-{C(t)}{Fz['base_l']},{Ut(T)}),-MIN({prev(t, Fz['pool_l'])},0.25*({C(t)}{Fz['base_l']}+{Ut(T)}))),0)", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, Fz["ir_l"], "Impuesto a la Renta 25 % (con absorción limitada y arrastre si hay utilidad gravable)", lambda t, T: f'=IF(ISNUMBER({UG}),IF({C(t)}{Fz["base_l"]}>=0,Tasa_IR*({C(t)}{Fz["base_l"]}-MIN({prev(t, Fz["pool_l"])},0.25*({C(t)}{Fz["base_l"]}+{Ut(T)}))),-Tasa_IR*MIN(-{C(t)}{Fz["base_l"]},{Ut(T)})),IF(Escudo_Negativo="Sí",Tasa_IR*{C(t)}{Fz["base_l"]},MAX(0,Tasa_IR*{C(t)}{Fz["base_l"]})))', unit_txt="USD", trow=tr)
    row_formula(ws, Fz["imp_l"], "Impuestos incrementales con deuda", lambda t, T: f"={C(t)}{Fz['part_l']}+{C(t)}{Fz['ir_l']}", unit_txt="USD", bold=True, total=True, trow=tr)
    name(wb, "Imp_L_Row", S7, rng(Fz["imp_l"]))
    row_formula(ws, Fz["escudo"], "Escudo fiscal de los intereses", lambda t, T: f"={C(t)}{Fz['imp']}-{C(t)}{Fz['imp_l']}", unit_txt="USD", color=GRAFITO, trow=tr)
    section(ws, Fz["tot_sec"], 2, 8, "Totales del horizonte")
    r = Fz["tot_sec"] + 1
    label(ws, r, 2, "Impuestos incrementales sin deuda (Σ)"); calc(ws, r, 4, f"=SUM({rng(Fz['imp'])})", fmt=FMT_USD); unit(ws, r, 3, "USD")
    label(ws, r + 1, 2, "Impuestos incrementales con deuda (Σ)"); calc(ws, r + 1, 4, f"=SUM({rng(Fz['imp_l'])})", fmt=FMT_USD); unit(ws, r + 1, 3, "USD")
    label(ws, r + 2, 2, "Escudo de la deducción adicional (Σ, a la tasa de IR)"); calc(ws, r + 2, 4, f"=SUM({rng(Fz['dedad'])})*Tasa_IR", fmt=FMT_USD); unit(ws, r + 2, 3, "USD")
    label(ws, r + 3, 2, "IVA total pagado / recuperado"); calc(ws, r + 3, 4, f"=SUM({rng(Fz['iva_pag'])})", fmt=FMT_USD); calc(ws, r + 3, 5, f"=SUM({rng(Fz['iva_rec'])})", fmt=FMT_USD); unit(ws, r + 3, 3, "USD")
    series_layout(ws, Fz["t"], summary_last_col=12, split=False, row_breaks=(Fz["t"] - 1,), series_last_row=Fz["escudo"])
    return ws


# ---------------------------------------------------------------- 08_Flujo
def build_flujo(wb):
    F = FLUJO
    ws = wb.create_sheet(S8)
    time_widths(ws, label_w=48)
    widths(ws, {"C": 6, "D": 10.5, "E": 10.5})
    sheet_header(ws, "8 · Flujo de caja de SALELGI", "Flujo del Custom sin y con deuda: t = −1 desarrollo/procura (30 % del CAPEX), t = 0 construcción (70 %), t = 1…25 operación; VAN y payback a t = 0 (COD). Los cuatro casos: portada y 10 §A.", 8, last_col=11, total=NSHEETS)
    section(ws, F["kpi_sec"], 2, 11, "Indicadores del caso Custom — sin deuda vs con deuda")
    hdr(ws, F["kpi_hdr"], 2, 11, ["Indicador", "Unidad", "Sin deuda", "Con deuda", "Lectura"] + [""] * 5, height=18)
    ws.merge_cells(start_row=F["kpi_hdr"], start_column=6, end_row=F["kpi_hdr"], end_column=11)
    fcf, eq, acum, acum_eq, df, fcfd, acumd, dscr = F["fcf"], F["eq"], F["acum"], F["acum_eq"], F["df"], F["fcfd"], F["acumd"], F["dscr"]

    def pb(cum_row, flow_row):
        # v3.0 (V-b): robusto a varios cruces — interpola en el ÚLTIMO año con acumulado negativo (≡ fórmula simple si hay un solo cruce; control H6)
        cu, fl = rng(cum_row), rng(flow_row)
        i = f"SUMPRODUCT(MAX(({cu}<0)*(COLUMN({cu})-COLUMN(${C(T_MIN)}${cum_row})+1)))"
        return f'=IF(INDEX({cu},1,COUNT({cu}))<0,"no cruza",IF({i}=0,-1,({i}-2)+(-INDEX({cu},1,{i}))/INDEX({fl},1,{i}+1)))'

    def van(row, rate):
        return f"={C(-1)}{row}*(1+{rate})+{C(0)}{row}+NPV({rate},{rng(row,1,25)})"
    kp = [
        ("TIR", "%", FMT_PCT2, f'=IFERROR(IRR({rng(fcf)}),"n/a")', f'=IFERROR(IRR({rng(eq)},0.02),"n/a")', "TIR_Proyecto", "TIR_Equity", "Apalancamiento positivo si la TIR del accionista supera la del proyecto."),
        ("VAN en el COD (t = 0): proyecto @ tasa de descuento · accionista @ tasa del accionista", "USD", FMT_USD, van(fcf, "Tasa_Descuento"), van(eq, "Tasa_Descuento_Equity"), "VAN_Proyecto", "VAN_Equity", '="El VAN del accionista se descuenta al "&TEXT(Tasa_Descuento_Equity,"0.0%")&" (Tasa_Descuento_Equity; proyecto al "&TEXT(Tasa_Descuento,"0.0%")&") e incluye el escudo fiscal de los intereses."'),
        ("VAN @ tasa alterna 1", "USD", FMT_USD, van(fcf, "Tasa_Desc_Alt1"), None, "VAN_Alt1", None, ""),
        ("VAN @ tasa alterna 2", "USD", FMT_USD, van(fcf, "Tasa_Desc_Alt2"), None, "VAN_Alt2", None, ""),
        ("Payback simple (años desde COD)", "años", FMT_YRS, pb(acum, fcf), pb(acum_eq, eq), "Payback_Simple", "Payback_Equity", "Interpolado en el último año con acumulado negativo (robusto si el reemplazo de inversores vuelve a hundirlo)."),
        ("Payback descontado (años desde COD)", "años", FMT_YRS, pb(acumd, fcfd), None, "Payback_Desc", None, ""),
        ("LCOE (sin impuestos)", "$/MWh", FMT_DEC1, f"=(CAPEX_Total+SUMPRODUCT('{S7}'!{rng(FISCAL['opex'],1,25)}+'{S7}'!{rng(FISCAL['peaje'],1,25)},{rng(df,1,25)}))/SUMPRODUCT('{S4}'!{rng(ENERGIA['activa'],1,25)},{rng(df,1,25)})", None, "LCOE", None, "[CAPEX industrial + VP(OPEX + peaje)] / VP(energía producida); sin terreno ni impuestos."),
        ("Tarifa evitable de la red", "$/MWh", FMT_DEC1, "=Tarifa_Evitable*1000", None, "Tarifa_MWh", None, "Ponderada por bloques horarios (04_Energia)."),
        ("Ahorro por kWh vs LCOE", "%", FMT_PCT, f'=IF(D{F["kpi0"]+7}>0,1-D{F["kpi0"]+6}/D{F["kpi0"]+7},"n/a")', None, "Ahorro_kWh", None, "1 − LCOE / tarifa evitable."),
        ("Ahorro año 1", "USD", FMT_USD, f"={C(1)}{F['ahorro']}", None, "Ahorro_Anio1", None, ""),
        ("Ahorro acumulado (nominal)", "USD", FMT_USD, f"=SUM({rng(F['ahorro'])})", None, "Ahorro_Acum", None, ""),
        ("Reducción de la factura (año 1)", "%", FMT_PCT, "=Reduccion_Factura", None, "Red_Factura", None, "Ahorro / factura de referencia 2026."),
        ("Aporte de capital (años −1 y 0)", "USD", FMT_USD, f"=-SUM({C(-1)}{F['capex']}:{C(0)}{F['iva_rec']})", f"=-SUM({C(-1)}{eq}:{C(0)}{eq})", "Aporte_SinDeuda", "Aporte_Equity", "CAPEX + terreno (si SALELGI) + IVA neto − deuda desembolsada (caso con deuda)."),
        ("DSCR mínimo (años con servicio)", "x", FMT_X, None, f'=IF(Deuda_Monto>0,MIN({rng(dscr,1,25)}),"n/a")', None, "DSCR_Min", '=IF(Deuda_Monto=0,"—",IF(DSCR_Min<1,"■ DSCR < 1,00x: el flujo no cubre la cuota en t = "&Anio_DSCR_Min&" — ver 10 §D y §H",IF(DSCR_Min<DSCR_Objetivo,"▲ DSCR < "&TEXT(DSCR_Objetivo,"0.00")&"x: bajo el umbral bancario","● DSCR ≥ "&TEXT(DSCR_Objetivo,"0.00")&"x")))'),
        ("DSCR promedio", "x", FMT_X, None, f'=IF(Deuda_Monto>0,AVERAGE({rng(dscr,1,25)}),"n/a")', None, "DSCR_Prom", ""),
        ("Deuda total al COD (incl. IDC)", "USD", FMT_USD, None, "=Deuda_Total", None, "Deuda_KPI", '="IDC "&TEXT(IDC,"#,##0")&": (tramo −1 un año + tramo 0 × "&TEXT(IDC_Frac_Tramo0,"0.00")&" años) × "&Meses_Construccion&" meses de construcción / 12 (03)"'),
        ("Cuota anual (francesa, post-gracia)", "USD", FMT_USD, None, "=Cuota", None, "Cuota_KPI", ""),
        ("Servicio de la deuda (Σ)", "USD", FMT_USD, None, f"=SUM({rng(F['serv'])})", None, "Servicio_Total", f'="intereses Σ "&TEXT(SUM({rng(F["int"])}),"#,##0")'),
        ("Año del DSCR mínimo (t)", "t", "0", None, f'=IF(Deuda_Monto>0,INDEX({rng(F["t"],1,25)},1,MATCH(DSCR_Min,{rng(dscr,1,25)},0)),"—")', None, "Anio_DSCR_Min", "Año en que el CFADS cubre peor la cuota (tarifa plana, OPEX escalado, menos escudo)."),
    ]
    for i, (lab, u, fmt, fs, fc, ns, nc, lect) in enumerate(kp):
        r = F["kpi0"] + i
        bold = i in (0, 1, 4, 13)
        label(ws, r, 2, lab, bold=bold, wrap=True); unit(ws, r, 3, u)
        if fs is not None:
            calc(ws, r, 4, fs, fmt=fmt, bold=bold)
            if ns: name(wb, ns, S8, f"$D${r}")
        else:
            calc(ws, r, 4, "—", align="center", color=GRAFITO)
        if fc is not None:
            calc(ws, r, 5, fc, fmt=fmt, bold=bold)
            if nc: name(wb, nc, S8, f"$E${r}")
        else:
            calc(ws, r, 5, "—", align="center", color=GRAFITO)
        if lect.startswith("="):
            c = chip(ws, r, 6, lect, kind="risk" if i == 13 else "info", c2=11); c.font = Font(name=FONT, size=8.5, bold=(i == 13), color=(LADRILLO if i == 13 else GRAFITO))
        else:
            note(ws, r, 6, lect, border=True, valign="center", c2=11)
        for cc in range(6, 12): ws.cell(row=r, column=cc).border = B_BOTTOM
        fit_row(ws, r, [(lab, 38, 10)], min_h=16, pad=1.6)   # una línea → 16 pt; dos líneas → 30,4 pt
    ws.row_dimensions[4].height = 10
    # ---- v3.0 (V3): sin mini-tabla de los cuatro casos; enlace a la comparación completa de 10 §A (la portada lleva la tira C · B · F)
    import build_content as _BC
    link_cell(ws, F["kpi0"] + len(kp), 2, "Los cuatro casos (Custom · Conservador · Base · Favorable) con estos indicadores → 10 §A", f"#'{S10}'!{_BC.SENS_ANCHORS.get('A', 'B5')}", size=SZ_TABLE, align="left")
    ws.row_dimensions[F["kpi0"] + len(kp)].height = 15
    # ---- Serie temporal
    time_header(ws, F["t"])
    tr = F["t"]
    section(ws, F["secA"], 2, LAST_T_COL, "A · Proyecto sin deuda")
    Fz = FISCAL
    row_formula(ws, F["capex"], "CAPEX industrial (sin IVA)", lambda t, T: f"=IF({T}=-1,-CAPEX_Total*Fase_m1,IF({T}=0,-CAPEX_Total*(1-Fase_m1),0))", unit_txt="USD", trow=tr)
    row_formula(ws, F["terr"], "Terreno SALELGI (−), con costos de transacción", lambda t, T: f"=IF({T}=-1,-Terreno_SALELGI,0)", unit_txt="USD", trow=tr)
    row_formula(ws, F["iva_pag"], "IVA pagado", lambda t, T: f"=-'{S7}'!{C(t)}{Fz['iva_pag']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["iva_rec"], "IVA recuperado", lambda t, T: f"='{S7}'!{C(t)}{Fz['iva_rec']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["ahorro"], "Ahorro por energía evitada", lambda t, T: f"='{S7}'!{C(t)}{Fz['ahorro']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["opex"], "OPEX SALELGI", lambda t, T: f"=-'{S7}'!{C(t)}{Fz['opex']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["peaje"], "Peaje SGDA", lambda t, T: f"=-'{S7}'!{C(t)}{Fz['peaje']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["imp"], "Impuestos incrementales (participación + IR)", lambda t, T: f"=-'{S7}'!{C(t)}{Fz['imp']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["rep"], "Reemplazo de inversores (−), si lo paga SALELGI", lambda t, T: f'=IF(AND(Reemplazo_Pagador="SALELGI",{T}=Reemplazo_Anio),-Reemplazo_USD,0)', unit_txt="USD", trow=tr)
    row_formula(ws, F["resid"], "Residual del terreno SALELGI, neto de impuesto (+)", lambda t, T: f"=IF(AND({T}=Horizonte,Terreno_SALELGI>0),Terreno_SALELGI/(1+Costos_Transaccion_Terreno_Pct)*Residual_Terreno_Pct*(1+Apreciacion_Terreno)^(Horizonte+1)-MAX(0,Terreno_SALELGI/(1+Costos_Transaccion_Terreno_Pct)*Residual_Terreno_Pct*(1+Apreciacion_Terreno)^(Horizonte+1)-Terreno_SALELGI)*Tasa_Efectiva,0)", unit_txt="USD", trow=tr)
    row_formula(ws, F["fcf"], "Flujo de caja libre del proyecto", lambda t, T: f"=SUM({C(t)}{F['capex']}:{C(t)}{F['resid']})", unit_txt="USD", bold=True, total=True, trow=tr)
    name(wb, "FCF_U_Row", S8, rng(F["fcf"]))
    row_formula(ws, F["acum"], "Acumulado", lambda t, T: f"={C(t)}{F['fcf']}" if t == T_MIN else f"={C(t-1)}{F['acum']}+{C(t)}{F['fcf']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["df"], "Factor de descuento (t=0 base)", lambda t, T: f"=1/(1+Tasa_Descuento)^{T}", fmt="0.0000", unit_txt="", color=GRAFITO, trow=tr)
    row_formula(ws, F["fcfd"], "FCF descontado", lambda t, T: f"={C(t)}{F['fcf']}*{C(t)}{F['df']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["acumd"], "Acumulado descontado", lambda t, T: f"={C(t)}{F['fcfd']}" if t == T_MIN else f"={C(t-1)}{F['acumd']}+{C(t)}{F['fcfd']}", unit_txt="USD", color=GRAFITO, trow=tr)
    section(ws, F["secB"], 2, LAST_T_COL, "B · Con deuda (SALELGI deudor)")
    years_in_section(ws, F["secB"], tr)
    r = F["scal"]
    scal = [("Deuda desembolsada (% × CAPEX, + terreno si se financia)", '=Pct_Apalancamiento*(CAPEX_Total+IF(Deuda_Financia_Terreno="Sí",Terreno_SALELGI,0))', "Deuda_Monto"),
            ("Intereses capitalizados en construcción (IDC) × meses / 12", "=Deuda_Monto*Tasa_Deuda*(Fase_m1+(1-Fase_m1)*IDC_Frac_Tramo0)*Meses_Construccion/12", "IDC"),
            ("Deuda total al COD", "=Deuda_Monto+IDC", "Deuda_Total"),
            ("Cuota anual (francesa, tras la gracia)", "=IF(Deuda_Total=0,0,IF(Plazo_Deuda>Gracia_Deuda,PMT(Tasa_Deuda,Plazo_Deuda-Gracia_Deuda,-Deuda_Total),Deuda_Total*(1+Tasa_Deuda)))", "Cuota")]
    for j, (lab, f, nm) in enumerate(scal):
        rr = r + j // 2
        if j % 2 == 0:
            label(ws, rr, 2, lab, size=9); unit(ws, rr, 3, "USD"); calc(ws, rr, 4, f, fmt=FMT_USD, bold=True, size=9)
            name(wb, nm, S8, f"$D${rr}")
        else:
            cell = ws.cell(row=rr, column=6, value=lab); cell.font = font(size=9, color=GRAFITO); cell.alignment = Alignment(horizontal="right", vertical="center")
            ws.merge_cells(start_row=rr, start_column=6, end_row=rr, end_column=9)
            for cc in range(6, 10): ws.cell(row=rr, column=cc).border = B_BOTTOM
            calc(ws, rr, 10, f, fmt=FMT_USD, bold=True, size=9)
            name(wb, nm, S8, f"$J${rr}")
        ws.row_dimensions[rr].height = 16
    row_formula(ws, F["desemb"], "Desembolso de deuda (+)", lambda t, T: f"=IF({T}=-1,Deuda_Monto*Fase_m1,IF({T}=0,Deuda_Monto*(1-Fase_m1),0))", unit_txt="USD", trow=tr)
    row_formula(ws, F["saldo_ini"], "Saldo inicial", lambda t, T: ("=0" if t == -1 else (f"={C(-1)}{F['desemb']}" if t == 0 else f"={C(t-1)}{F['saldo_fin']}")), unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["int"], "Intereses", lambda t, T: f"=IF(OR({T}<1,{T}>Plazo_Deuda),0,{C(t)}{F['saldo_ini']}*Tasa_Deuda)", unit_txt="USD", trow=tr)
    row_formula(ws, F["amort"], "Amortización (bullet si plazo ≤ gracia)", lambda t, T: f"=IF(Deuda_Total=0,0,IF(Plazo_Deuda<=Gracia_Deuda,IF({T}=Plazo_Deuda,{C(t)}{F['saldo_ini']},0),IF(AND({T}>Gracia_Deuda,{T}<=Plazo_Deuda),MIN({C(t)}{F['saldo_ini']},Cuota-{C(t)}{F['int']}),0)))", unit_txt="USD", trow=tr)
    row_formula(ws, F["serv"], "Servicio de la deuda", lambda t, T: f"={C(t)}{F['int']}+{C(t)}{F['amort']}", unit_txt="USD", bold=True, trow=tr)
    row_formula(ws, F["saldo_fin"], "Saldo final", lambda t, T: f"={C(t)}{F['saldo_ini']}+{C(t)}{F['desemb']}+IF({T}=0,IDC,0)-{C(t)}{F['amort']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["idc"], "IDC capitalizados (memo)", lambda t, T: f"=IF({T}=0,IDC,0)", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, F["cfads"], "CFADS (EBITDA − impuestos + IVA rec. + residual − reemplazo)", lambda t, T: f"=IF({T}<1,0,'{S7}'!{C(t)}{Fz['ebitda']}-'{S7}'!{C(t)}{Fz['imp_l']}+'{S7}'!{C(t)}{Fz['iva_rec']}+{C(t)}{F['resid']}+{C(t)}{F['rep']})", unit_txt="USD", trow=tr)
    row_formula(ws, F["dscr"], "DSCR", lambda t, T: f'=IF({C(t)}{F["serv"]}>0,{C(t)}{F["cfads"]}/{C(t)}{F["serv"]},"")', fmt=FMT_X, unit_txt="x", trow=tr)
    row_formula(ws, F["eq"], "Flujo de caja del accionista (equity)", lambda t, T: (f"={C(t)}{F['fcf']}+{C(t)}{F['desemb']}" if t <= 0 else f"={C(t)}{F['cfads']}-{C(t)}{F['serv']}"), unit_txt="USD", bold=True, total=True, trow=tr)
    name(wb, "FCF_E_Row", S8, rng(F["eq"]))
    row_formula(ws, F["acum_eq"], "Acumulado equity", lambda t, T: f"={C(t)}{F['eq']}" if t == T_MIN else f"={C(t-1)}{F['acum_eq']}+{C(t)}{F['eq']}", unit_txt="USD", color=GRAFITO, trow=tr)
    # fila auxiliar: DSCR objetivo constante (referencia del gráfico)
    ra = F["acum_eq"] + 2
    label(ws, ra, 2, "DSCR objetivo (referencia del gráfico)", color=GRAFITO, size=9)
    for t in range(1, 26):
        c_ = ws.cell(row=ra, column=COL0 + (t + 1), value="=DSCR_Objetivo"); c_.font = font(size=9, color=GRAFITO); c_.number_format = FMT_X
    # ventana de la deuda: t = 1…12 cubre cualquier plazo de Sens_Plazos (8/10/12); fuera de ella no hay servicio y el gráfico sólo añadiría vacío
    TW = 12
    cats = Reference(ws, min_col=COL0 + 2, max_col=COL0 + 1 + TW, min_row=F["t"])
    chart_cols(ws, f"B{F['chart']}", "CFADS y cuota de la deuda · años 1–12 · miles de USD", cats,
               [dict(ref=Reference(ws, min_col=COL0 + 2, max_col=COL0 + 1 + TW, min_row=F["cfads"]), name="CFADS", color=GRAFITO)],
               lines=[dict(ref=Reference(ws, min_col=COL0 + 2, max_col=COL0 + 1 + TW, min_row=F["serv"]), name="cuota", color=TERRACOTA, width=2.25)],
               w=12.6, h=6.5, y_fmt=FMT_K, legend="r", from_rows=True, gap=45, x_title="año t")
    chart_cols(ws, f"F{F['chart']}", "DSCR anual y objetivo · años 1–12", cats,
               [dict(ref=Reference(ws, min_col=COL0 + 2, max_col=COL0 + 1 + TW, min_row=F["dscr"]), name="DSCR", color=GRAFITO)],
               ref=dict(ref=Reference(ws, min_col=COL0 + 2, max_col=COL0 + 1 + TW, min_row=ra), name="objetivo", color=TERRACOTA, width=1.5, dash="dash"),
               w=11.4, h=6.5, y_fmt='0.00"x"', legend="r", from_rows=True, gap=45, x_title="año t")
    ws.row_dimensions[F["chart"] - 2].height = 6
    ws.row_dimensions[F["chart"] - 1].height = 6
    for rr in range(F["chart"], F["chart"] + 14):
        ws.row_dimensions[rr].height = 15   # 14 × (15 − 1) = 196 pt ≥ 6,5 cm (184 pt): Excel/Mac imprime cada fila ≈ 1 pt más baja; el rango termina bajo el gráfico
    series_layout(ws, F["t"], summary_last_col=12, summary_last_row=F["chart"] + 13, series_last_row=F["acum_eq"])
    return ws


# ---------------------------------------------------------------- 09_Exergy
def build_exergy(wb):
    X = EXERGY
    ws = wb.create_sheet(S9)
    time_widths(ws, label_w=50)
    widths(ws, {"C": 7, "D": 12})
    sheet_header(ws, "9 · Negocio Exergy", "Negocio de Exergy: gerencia, O&M y arriendo del terreno a renta fija; no vende energía (art. 8, 005/24). Impuestos a Tasa_Efectiva_Exergy sobre la utilidad positiva anual, sin arrastre; línea terreno sólo si Comprador_Terreno = Exergy.", 9, last_col=12, total=NSHEETS)
    hdr(ws, X["kpi_hdr"], 2, 12, ["Indicador", "Unidad", "Valor", "Definición"] + [""] * 7, height=18)
    ws.merge_cells(start_row=X["kpi_hdr"], start_column=5, end_row=X["kpi_hdr"], end_column=12)
    kp = [
        ("VAN del negocio Exergy @ tasa de descuento", "USD", FMT_USD, f"={C(-1)}{X['fcf']}*(1+Tasa_Descuento)+{C(0)}{X['fcf']}+NPV(Tasa_Descuento,{rng(X['fcf'],1,25)})", "Neto de impuestos; incluye compra y residual del terreno si Exergy es la propietaria.", "VAN_Exergy"),
        ("TIR del negocio Exergy", "%", FMT_PCT2, f'=IFERROR(IRR({rng(X["fcf"])}),"n/a")', "Alta por el fee inicial; el VAN es la métrica relevante.", "TIR_Exergy"),
        ("Ingreso neto nominal acumulado (Σ FCF)", "USD", FMT_USD, f"=SUM({rng(X['fcf'])})", "", "Nominal_Exergy"),
        ("VAN línea gerencia (antes de impuestos)", "USD", FMT_USD, f"=SUMPRODUCT({rng(X['fee'])}+{rng(X['costo'])},{rng(X['df'])})", "Fee − costo interno.", "VAN_Gerencia"),
        ("VAN línea terreno (antes de impuestos)", "USD", FMT_USD, f"=SUMPRODUCT({rng(X['terreno'])}+{rng(X['arr'])}+{rng(X['predial'])}+{rng(X['resid'])},{rng(X['df'])})", "Compra + arriendo − predial + residual (0 si compra SALELGI).", "VAN_Terreno"),
        ("VAN línea O&M (antes de impuestos)", "USD", FMT_USD, f"=SUMPRODUCT({rng(X['feeom'])}+{rng(X['costoom'])},{rng(X['df'])})", "Fee − costo propio.", "VAN_OM"),
        ("Rendimiento bruto del arriendo sobre el precio del terreno", "%", FMT_PCT, '=IF(Precio_Terreno_ha>0,Renta_Terreno_ha/Precio_Terreno_ha,"n/a")', "", "Yield_Terreno"),
        ("Costo anual de Exergy para SALELGI (fee O&M + arriendo) / ahorro año 1", "%", FMT_PCT, f"=IF(Ahorro_Anio1>0,('{S6}'!{C(1)}{OPEX['fee']}+'{S6}'!{C(1)}{OPEX['arr']})/Ahorro_Anio1,0)", "Cuánto del ahorro del cliente se queda en servicios Exergy.", "Carga_Exergy"),
    ]
    for i, (lab, u, fmt, f, dfn, nm) in enumerate(kp):
        r = X["kpi0"] + i
        label(ws, r, 2, lab, bold=(i == 0), wrap=True); unit(ws, r, 3, u); calc(ws, r, 4, f, fmt=fmt, bold=(i == 0))
        note(ws, r, 5, dfn, border=True, valign="center", c2=12)
        for cc in range(5, 13): ws.cell(row=r, column=cc).border = B_BOTTOM
        name(wb, nm, S9, f"$D${r}")
        fit_row(ws, r, [(lab, 36, 10), (dfn, merged_width(ws, 5, 12) - 2, 8.5)], min_h=17)
    section(ws, X["kpi_sec"], 2, 12, "Indicadores del negocio Exergy")
    # ---- v3.0 (V3): sin mini-tabla de los cuatro casos; enlace a 10 §A (VAN Exergy y TIR del grupo de los cuatro casos)
    import build_content as _BC
    link_cell(ws, X["chart"] - 1, 2, "VAN Exergy y TIR del grupo en los cuatro casos → 10 §A", f"#'{S10}'!{_BC.SENS_ANCHORS.get('A', 'B5')}", size=SZ_TABLE, align="left")
    cats9 = Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=X["t"])
    chart_cols(ws, f"B{X['chart']}", "Flujo de caja anual de Exergy (miles de USD)", cats9,
               [dict(ref=Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=X["fcf"]), name="flujo anual", color=GRAFITO, labels=[0, len(TS) - 1], label_fmt=FMT_K, label_pos="outEnd")],
               w=12.4, h=8.4, y_fmt=FMT_K, legend=None, from_rows=True, gap=40, x_title="año t (−1 y 0: fee y compra del terreno · 25: residual)", x_skip=2)
    chart_lines(ws, f"G{X['chart']}", "Flujo acumulado de Exergy (miles de USD)", cats9,
                [dict(ref=Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=X["acum"]), name="acumulado", color=TERRACOTA, width=2.25, labels=[len(TS) - 1], label_fmt=FMT_K, label_pos="l")],
                w=11.6, h=8.4, y_fmt=FMT_K, legend=None, from_rows=True, x_title="año t", x_skip=2)
    time_header(ws, X["t"])
    tr = X["t"]
    section(ws, X["sec"], 2, LAST_T_COL, "Flujo de caja de Exergy")
    ex = '(Comprador_Terreno="Exergy")'
    row_formula(ws, X["fee"], "Fee de gerencia del proyecto (+)", lambda t, T: f"=IF({T}=-1,Fee_Gerencia_USD*Fase_m1,IF({T}=0,Fee_Gerencia_USD*(1-Fase_m1),0))", unit_txt="USD", trow=tr)
    row_formula(ws, X["costo"], "Costo interno de gerencia (−)", lambda t, T: f"=IF({T}=-1,-Costo_Gerencia_Pct*Subtotal_EPC*Fase_m1,IF({T}=0,-Costo_Gerencia_Pct*Subtotal_EPC*(1-Fase_m1),0))", unit_txt="USD", trow=tr)
    row_formula(ws, X["terreno"], "Compra del terreno incl. costos de transacción (−) — si Exergy es la compradora", lambda t, T: f"=IF(AND({T}=-1,{ex}),-Precio_Terreno_ha*Hectareas*(1+Costos_Transaccion_Terreno_Pct),0)", unit_txt="USD", trow=tr)
    row_formula(ws, X["arr"], "Arriendo del terreno cobrado a SALELGI (+)", lambda t, T: f"='{S6}'!{C(t)}{OPEX['arr']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, X["predial"], "Predial y gastos del terreno (−)", lambda t, T: f"=-'{S6}'!{C(t)}{OPEX['memo_predial']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, X["feeom"], "Fee de O&M cobrado a SALELGI (+)", lambda t, T: f"='{S6}'!{C(t)}{OPEX['fee']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, X["costoom"], "Costo propio de O&M (−)", lambda t, T: f"=-'{S6}'!{C(t)}{OPEX['memo_cost']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, X["rep"], "Reemplazo de inversores a cargo de Exergy (−), con la reserva del fee de O&M", lambda t, T: f'=IF(AND(Reemplazo_Pagador="Exergy",{T}=Reemplazo_Anio),-Reemplazo_USD,0)', unit_txt="USD", trow=tr)
    row_formula(ws, X["util"], "Utilidad operativa antes de impuestos (sin compra/venta de terreno)", lambda t, T: f"={C(t)}{X['fee']}+{C(t)}{X['costo']}+{C(t)}{X['arr']}+{C(t)}{X['predial']}+{C(t)}{X['feeom']}+{C(t)}{X['costoom']}+{C(t)}{X['rep']}", unit_txt="USD", bold=True, trow=tr)
    row_formula(ws, X["imp"], "Impuestos Exergy (participación + IR sobre utilidad positiva)", lambda t, T: f"=-MAX(0,{C(t)}{X['util']})*Tasa_Efectiva_Exergy", unit_txt="USD", trow=tr)
    resid_g = "Precio_Terreno_ha*Hectareas*Residual_Terreno_Pct*(1+Apreciacion_Terreno)^(Horizonte+1)"
    row_formula(ws, X["resid"], "Valor residual del terreno, neto de impuesto sobre la ganancia (+)", lambda t, T: f"=IF(AND({T}=Horizonte,{ex}),{resid_g}-MAX(0,{resid_g}-Precio_Terreno_ha*Hectareas*(1+Costos_Transaccion_Terreno_Pct))*Tasa_Efectiva_Exergy,0)", unit_txt="USD", trow=tr)
    row_formula(ws, X["fcf"], "Flujo de caja de Exergy", lambda t, T: f"={C(t)}{X['util']}+{C(t)}{X['imp']}+{C(t)}{X['terreno']}+{C(t)}{X['resid']}", unit_txt="USD", bold=True, total=True, trow=tr)
    name(wb, "FCF_X_Row", S9, rng(X["fcf"]))
    row_formula(ws, X["acum"], "Acumulado", lambda t, T: f"={C(t)}{X['fcf']}" if t == T_MIN else f"={C(t-1)}{X['acum']}+{C(t)}{X['fcf']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, X["df"], "Factor de descuento", lambda t, T: f"=1/(1+Tasa_Descuento)^{T}", fmt="0.0000", unit_txt="", color=GRAFITO, trow=tr)
    # ---- Sensibilidad de palancas
    section(ws, X["sens_sec"], 2, 14, "Sensibilidad del negocio Exergy (ΔVAN lineal, neto de impuestos) y carga para SALELGI")
    label(ws, X["ann"], 2, "Factor de anualidad escalado Σ (1+esc)^(t−1)/(1+r)^t, t = 1…horizonte", color=GRAFITO, size=9)
    for t in range(1, 26):
        c_ = ws.cell(row=X["ann"], column=COL0 + (t + 1), value=f"=IF({C(t)}${tr}<=Horizonte,(1+Escalacion_OPEX)^({C(t)}${tr}-1)*{C(t)}{X['df']},0)")
        c_.font = font(size=8.5, color=GRAFITO); c_.number_format = "0.0000"
    calc(ws, X["ann"], 4, f"=SUM({rng(X['ann'],1,25)})", fmt="0.000", bold=True)
    name(wb, "Ann_Esc", S9, f"$D${X['ann']}")
    ann = "Ann_Esc"
    hdr(ws, X["sens_hdr"], 2, 8, ["Palanca", "Valor", "VAN Exergy [USD]", "Δ vs base [USD]", "Costo para SALELGI [USD]", "% del ahorro año 1", "Nota"], height=30)
    rr = X["sens0"]
    for v in (0.05, 0.07, 0.09):
        label(ws, rr, 2, "Fee de gerencia (% del valor del proyecto) — pago único")
        inp(ws, rr, 3, v, fmt=FMT_PCT0)
        calc(ws, rr, 4, f"=VAN_Exergy+(C{rr}-Fee_Gerencia_Pct)*Subtotal_EPC*(Fase_m1*(1+Tasa_Descuento)+(1-Fase_m1))*(1-Tasa_Efectiva_Exergy)", fmt=FMT_USD)
        calc(ws, rr, 5, f"=D{rr}-VAN_Exergy", fmt=FMT_USD); calc(ws, rr, 6, f"=C{rr}*Subtotal_EPC", fmt=FMT_USD); calc(ws, rr, 7, f"=IF(Ahorro_Anio1>0,F{rr}/Ahorro_Anio1,0)", fmt=FMT_PCT)
        note(ws, rr, 8, '="Pago único capitalizado en el CAPEX de SALELGI; % = veces el ahorro del año 1. Decisión Jorge: base "&TEXT(Fee_Gerencia_Pct,"0%")&"."', border=True, valign="center", c2=12); fit_row(ws, rr, [("x" * 105, 55, 8.5)], min_h=16)
        rr += 1
    for v in (3000, 5000, 7000):
        label(ws, rr, 2, "Arriendo del terreno ($/ha-año) — sólo si Exergy es la propietaria")
        inp(ws, rr, 3, v, fmt=FMT_USD)
        calc(ws, rr, 4, f'=IF(Comprador_Terreno="Exergy",VAN_Exergy+(C{rr}-Renta_Terreno_ha)*Hectareas*{ann}*(1-Tasa_Efectiva_Exergy),VAN_Exergy)', fmt=FMT_USD)
        calc(ws, rr, 5, f"=D{rr}-VAN_Exergy", fmt=FMT_USD); calc(ws, rr, 6, f'=IF(Comprador_Terreno="Exergy",C{rr}*Hectareas,0)', fmt=FMT_USD); calc(ws, rr, 7, f"=IF(Ahorro_Anio1>0,F{rr}/Ahorro_Anio1,0)", fmt=FMT_PCT)
        note(ws, rr, 8, f'="Rendimiento bruto sobre "&TEXT(Precio_Terreno_ha,"#,##0")&" $/ha: "&IFERROR(TEXT(C{rr}/Precio_Terreno_ha,"0%"),"n/a")&". A la tasa de descuento del "&TEXT(Tasa_Descuento,"0%")&", la línea terreno es ≈ neutra con "&TEXT(Precio_Terreno_ha*Tasa_Descuento,"#,##0")&"."', border=True, valign="center", c2=12); fit_row(ws, rr, [("x" * 125, 55, 8.5)], min_h=16)
        rr += 1
    for v in (18, 20, 24):
        label(ws, rr, 2, "Fee de O&M ($/kWp-año)")
        inp(ws, rr, 3, v, fmt=FMT_DEC1)
        calc(ws, rr, 4, f"=VAN_Exergy+(C{rr}-Fee_OM_kWp)*Potencia_DC*{ann}*(1-Tasa_Efectiva_Exergy)", fmt=FMT_USD)
        calc(ws, rr, 5, f"=D{rr}-VAN_Exergy", fmt=FMT_USD); calc(ws, rr, 6, f"=C{rr}*Potencia_DC", fmt=FMT_USD); calc(ws, rr, 7, f"=IF(Ahorro_Anio1>0,F{rr}/Ahorro_Anio1,0)", fmt=FMT_PCT)
        note(ws, rr, 8, f'="Costo propio Exergy "&TEXT(Costo_OM_Exergy_kWp,"0")&" $/kWp → margen "&TEXT(C{rr}-Costo_OM_Exergy_kWp,"0")&" $/kWp."', border=True, valign="center", c2=12)
        rr += 1
    # ---- Vista consolidada
    section(ws, X["grupo_sec"], 2, LAST_T_COL, "Memo — vista consolidada del grupo (SALELGI sin deuda + Exergy): los pagos entre partes relacionadas se netean")
    years_in_section(ws, X["grupo_sec"], tr)
    row_formula(ws, X["g_sal"], "FCF SALELGI sin deuda", lambda t, T: f"='{S8}'!{C(t)}{FLUJO['fcf']}", unit_txt="USD", color=GRAFITO, trow=tr)
    row_formula(ws, X["g_ex"], "FCF Exergy", lambda t, T: f"={C(t)}{X['fcf']}", unit_txt="USD", trow=tr)
    row_formula(ws, X["g_tot"], "FCF grupo", lambda t, T: f"={C(t)}{X['g_sal']}+{C(t)}{X['g_ex']}", unit_txt="USD", bold=True, total=True, trow=tr)
    label(ws, X["g_tir"], 2, "TIR del grupo", bold=True); calc(ws, X["g_tir"], 4, f'=IFERROR(IRR({rng(X["g_tot"])}),"n/a")', fmt=FMT_PCT2, bold=True); unit(ws, X["g_tir"], 3, "%"); name(wb, "TIR_Grupo", S9, f"$D${X['g_tir']}")
    label(ws, X["g_van"], 2, "VAN del grupo @ tasa de descuento", bold=True); calc(ws, X["g_van"], 4, f"={C(-1)}{X['g_tot']}*(1+Tasa_Descuento)+{C(0)}{X['g_tot']}+NPV(Tasa_Descuento,{rng(X['g_tot'],1,25)})", fmt=FMT_USD, bold=True); unit(ws, X["g_van"], 3, "USD"); name(wb, "VAN_Grupo", S9, f"$D${X['g_van']}")
    callout(ws, X["g_note"], 2, 12, "Lectura: si el grupo consolida, el fee, el arriendo y el margen de O&M son transferencias internas; lo que queda es el ahorro de energía menos el costo real (CAPEX + costo propio de O&M + terreno) y los impuestos de cada entidad. El comparativo «quién compra el terreno» está en 10 §G (calculado en Motor_Sens para ambas alternativas).")
    for rr in range(X["chart"] - 1, X["chart"] + 18):
        ws.row_dimensions[rr].height = 15   # 18 × (15 − 1) = 252 pt ≥ 8,4 cm (238 pt) con las filas impresas ≈ 1 pt más bajas
    series_layout(ws, X["t"], summary_last_col=12, row_breaks=(X["sens_sec"] - 1,), summary_last_row=X["chart"] + 17, series_last_row=X["df"])
    return ws


# ---------------------------------------------------------------- Motor_Sens
# v3.0 (ronda 2, doc 13 §8): 9 filas de parámetro nuevas (25–33), escalares 34–52 + fEsc 53 · Krep 54 · Decom 55, salidas 56–71, bloques desde 74
# (+ Krep, PoolU, PoolL = 28 bloques). Toda referencia al Motor (13, 12, portada, Resumen, sombra) pasa por estos diccionarios o por brow()/brng().
PARAM_ROWS = {"fK": 5, "fT": 6, "scen": 7, "fO": 8, "pj": 9, "escT": 10, "part": 11, "iva": 12, "cont": 13, "deb": 14, "rd": 15, "lev": 16, "plazo": 17, "gr": 18,
              "P": 19, "ratio": 20, "terr": 21, "finT": 22, "fPre": 23, "kfix": 24,   # v2.0: kfix = CAPEX fijo $/Wp del caso (0 = bottom-up × fK)
              "disp": 25, "dK": 26, "pkw": 27, "rep": 28, "ug": 29, "ncon": 30, "req": 31, "dec": 32, "deg": 33,   # v3.0 (neutro: 1 · 0 · 0 · 0 · −1 · 12 · tasa · 0 · 0)
              "dedad": 34}   # v3.1 (doc 18 D-L6): deducción adicional aplicable (1/0) — certificación ambiental previa (RLRTI 28.6.g)
PARAM_NEW = ("disp", "dK", "pkw", "rep", "ug", "ncon", "req", "dec", "deg")
SCAL_ROWS = {"frec": 35, "AC": 36, "ha": 37, "K": 38, "IVA": 39, "Kdep": 40, "DepEq": 41, "DepCiv": 42, "DedAd": 43, "Terr": 44, "Resid": 45, "OPEX1": 46, "Sub": 47,
             "D": 48, "IDC": 49, "Dt": 50, "n": 51, "PMT": 52, "fKeff": 53,   # v2.0: fKeff = factor CAPEX efectivo (fijo → kfix·P·1000/bottom-up; si no, fK)   · v3.1: +1 fila (parámetro dedad)
             "fEsc": 54, "Krep": 55, "Decom": 56}   # v3.0: factor de escalación del CAPEX · reemplazo de inversores (USD) · desmantelamiento (USD)
OUT_ROWS = {"TIR": 57, "VAN": 58, "PB": 59, "LCOE": 60, "TIR_eq": 61, "VAN_eq": 62, "DSCR_min": 63, "DSCR_avg": 64, "Ahorro1": 65, "Aporte_eq": 66,
            "VAN_X": 67, "TIR_G": 68, "E1": 69, "NoRec": 70, "Cob": 71, "Nominal_X": 72}   # v3.1: +1 fila
BLOCKS = ["E", "Eval", "Ahorro", "OPEX", "Peaje", "EBITDA", "Dep", "Part_u", "IR_u", "Terr", "FCF_u", "Cum_u", "Int", "Amort", "Part_l", "IR_l", "CFADS", "EQ", "DSCR", "DF",
          "Ux", "Ix", "Tx", "Fx", "Gx", "Krep", "PoolU", "PoolL"]
BLOCK0 = 75   # v3.1: +1 fila (parámetro dedad)
BLOCK_H = 28


def brow(block, t):
    return BLOCK0 + BLOCKS.index(block) * BLOCK_H + 1 + (t + 1)


def brng(block, X, t1=T_MIN, t2=T_MAX):
    return f"{X}${brow(block, t1)}:{X}${brow(block, t2)}"


def build_motor(wb, cases):
    ws = wb.create_sheet(SM)
    ws.column_dimensions["A"].width = 36
    for j in range(len(cases)):
        ws.column_dimensions[col(2 + j)].width = 12
    sheet_header(ws, "Motor de casos — no editar", "Un caso por columna con la lógica de 04–09; alimenta 05, 08–10, 13 y la portada. Columnas B–E = Custom · Conservador · Base · Favorable (la Custom coincide con 08 y 09); los demás mueven una palanca.", NSHEETS, last_col=12, total=NSHEETS)
    ws.cell(row=3, column=1, value="fila").font = font(size=8.5, color=GRAFITO)
    hdr(ws, 4, 2, 1 + len(cases), [c["name"] for c in cases], height=30)
    for j_, key_ in enumerate(CASE_KEYS):   # v2.0: los cuatro casos con su color (texto negrita + regla superior)
        caso_hdr(ws, 4, 2 + j_, key_, text=cases[j_]["name"], align="center", size=SZ_TABLE)
    ws.cell(row=4, column=1, value="Caso").font = font(bold=True, size=9)
    plabels = {"fK": "Factor CAPEX (× bottom-up)", "kfix": "CAPEX fijo $/Wp (0 = bottom-up × factor)", "fT": "Factor tarifa", "scen": "Escenario energía (1=P50, 2=P90)", "fO": "Factor OPEX", "pj": "Peaje $/kWh", "escT": "Escalación tarifa", "part": "Participación (1/0)", "iva": "IVA recuperable (1/0)", "cont": "Contrato inversión (1/0)", "deb": "Deuda (1/0)", "rd": "Tasa deuda", "lev": "Apalancamiento", "plazo": "Plazo", "gr": "Gracia",
               "P": "Potencia DC (kWp)", "ratio": "Ratio DC/AC", "terr": "Terreno lo compra SALELGI (1/0)", "finT": "Banco financia terreno (1/0)", "fPre": "Factor precio terreno",
               "disp": "Disponibilidad", "dK": "Escalación CAPEX (%/año hasta la compra)", "pkw": "Peaje por potencia $/kW-mes", "rep": "Reemplazo inversores (0 No · 1 SALELGI · 2 Exergy)",
               "ug": "Utilidad gravable SALELGI (−1 = ilimitada)", "ncon": "Meses de construcción", "req": "Tasa descuento accionista", "dec": "Desmantelamiento (% CAPEX en t=H)",
               "deg": "Degradación adicional (%/año)", "dedad": "Deducción adicional aplicable (1/0)"}
    for k, rr in PARAM_ROWS.items():
        label(ws, rr, 1, plabels[k], size=9, border=False)
    slabels = {"frec": "Factor de recorte", "AC": "Potencia AC (kW)", "ha": "Hectáreas", "K": "CAPEX industrial sin IVA", "IVA": "IVA CAPEX", "Kdep": "CAPEX depreciable", "DepEq": "Dep. equipos/año", "DepCiv": "Dep. civil/año", "DedAd": "Deducción adicional/año",
               "Terr": "Terreno (costo total quien compra)", "Resid": "Residual terreno neto (t=H)", "OPEX1": "OPEX año 1 SALELGI", "Sub": "Subtotal EPC (base fee)", "D": "Deuda", "IDC": "IDC", "Dt": "Deuda total COD", "n": "Nº cuotas", "PMT": "Cuota", "fKeff": "Factor CAPEX efectivo",
               "fEsc": "Factor de escalación del CAPEX", "Krep": "Reemplazo de inversores (USD)", "Decom": "Desmantelamiento (USD)"}
    for k, rr in SCAL_ROWS.items():
        label(ws, rr, 1, slabels[k], size=9, border=False)
    olabels = {"TIR": "TIR proyecto", "VAN": "VAN proyecto", "PB": "Payback simple", "LCOE": "LCOE $/MWh", "TIR_eq": "TIR equity", "VAN_eq": "VAN equity", "DSCR_min": "DSCR mín", "DSCR_avg": "DSCR prom", "Ahorro1": "Ahorro año 1", "Aporte_eq": "Aporte equity",
               "VAN_X": "VAN Exergy", "TIR_G": "TIR grupo", "E1": "Energía año 1 (MWh)", "NoRec": "Energía no reconocida Σ (MWh)", "Cob": "Cobertura año 1", "Nominal_X": "Nominal Exergy Σ"}
    for k, rr in OUT_ROWS.items():
        label(ws, rr, 1, olabels[k], size=9, bold=True, border=False)
    for b in BLOCKS:
        r0 = BLOCK0 + BLOCKS.index(b) * BLOCK_H
        section(ws, r0, 1, 1 + len(cases), f"Bloque {b} (filas = años t)")
        for t in TS:
            ws.cell(row=brow(b, t), column=1, value=t).font = font(size=8.5, color=GRAFITO)
    for j, c in enumerate(cases):
        X = col(2 + j)
        P = {k: f"{X}${rr}" for k, rr in PARAM_ROWS.items()}
        S = {k: f"{X}${rr}" for k, rr in SCAL_ROWS.items()}
        for k, rr in PARAM_ROWS.items():
            v = c["params"][k]
            cell = ws.cell(row=rr, column=2 + j, value=v)
            cell.font = font(size=9, color=AZUL_IN if not (isinstance(v, str) and v.startswith("=")) else CARBON)
            cell.number_format = FMT_PCT if k in ("escT", "rd", "lev", "disp", "dK", "req", "dec") else ("0.0000" if k in ("pj", "deg") else ("#,##0" if k in ("P", "ug") else ("0.00" if k == "pkw" else ("0" if k in ("rep", "ncon", "dedad") else "0.000"))))
        # escalares
        ws[f"{X}{SCAL_ROWS['frec']}"] = f"=(1-{f_loss(P['ratio'])})/(1-Loss_Ref)"
        ws[f"{X}{SCAL_ROWS['AC']}"] = f"={P['P']}/{P['ratio']}"
        ws[f"{X}{SCAL_ROWS['ha']}"] = f"={P['P']}/1000/Densidad_MWp_ha"
        a = f"({P['P']}/Potencia_Ref)^(1-Exponente_Escala)"; b_ = f"({S['AC']}/(Potencia_Ref/Ratio_Ref))^(1-Exponente_Escala)"
        kbase = f"IF({P['cont']}=1,{a}*CAPEX_CC_Wp+{b_}*CAPEX_CC_Wac+CAPEX_CC_Fijo,{a}*CAPEX_SC_Wp+{b_}*CAPEX_SC_Wac+CAPEX_SC_Fijo)"
        ws[f"{X}{SCAL_ROWS['fKeff']}"] = f"=IF({P['kfix']}>0,{P['kfix']}*{P['P']}*1000/{kbase},{P['fK']})"
        ws[f"{X}{SCAL_ROWS['K']}"] = f"={S['fKeff']}*{S['fEsc']}*{kbase}"   # v3.0 (M-a): × factor de escalación de precios hasta la compra
        ws[f"{X}{SCAL_ROWS['IVA']}"] = f"={S['fKeff']}*{S['fEsc']}*IF({P['cont']}=1,{a}*IVA_CC_Wp+{b_}*IVA_CC_Wac+IVA_CC_Fijo,{a}*IVA_SC_Wp+{b_}*IVA_SC_Wac+IVA_SC_Fijo)"
        ws[f"{X}{SCAL_ROWS['Kdep']}"] = f"={S['K']}+(1-{P['iva']})*{S['IVA']}"
        ws[f"{X}{SCAL_ROWS['DepEq']}"] = f"={S['Kdep']}*(1-Pct_CAPEX_Civil)/Vida_Fiscal_Equipos"
        ws[f"{X}{SCAL_ROWS['DepCiv']}"] = f"={S['Kdep']}*Pct_CAPEX_Civil/Vida_Fiscal_Civil"
        ws[f"{X}{SCAL_ROWS['DedAd']}"] = f"={P['dedad']}*MIN({S['Kdep']}*Pct_Elegible_DedAd/Vida_Fiscal_Equipos,Tope_DedAd_Pct*Ingresos_SALELGI)"   # v3.1: × deducción aplicable (1/0)
        ws[f"{X}{SCAL_ROWS['Terr']}"] = f"=Precio_Terreno_ha*{P['fPre']}*{S['ha']}*(1+Costos_Transaccion_Terreno_Pct)"
        resid_g = f"Precio_Terreno_ha*{P['fPre']}*{S['ha']}*Residual_Terreno_Pct*(1+Apreciacion_Terreno)^(Horizonte+1)"
        ws[f"{X}{SCAL_ROWS['Resid']}"] = f"={resid_g}-MAX(0,{resid_g}-{S['Terr']})*IF({P['terr']}=1,Tasa_Efectiva,Tasa_Efectiva_Exergy)"
        ws[f"{X}{SCAL_ROWS['OPEX1']}"] = f"=(Fee_OM_kWp+Seguro_kWp)*{P['P']}+IF({P['terr']}=1,Predial_Terreno,Renta_Terreno_ha*{S['ha']})+Tributos_Locales"
        ws[f"{X}{SCAL_ROWS['Sub']}"] = f"={S['K']}/(1+Fee_Gerencia_Pct)"
        ws[f"{X}{SCAL_ROWS['D']}"] = f"={P['deb']}*{P['lev']}*({S['K']}+{P['finT']}*{P['terr']}*{S['Terr']})"
        ws[f"{X}{SCAL_ROWS['IDC']}"] = f"={S['D']}*{P['rd']}*(Fase_m1+(1-Fase_m1)*IDC_Frac_Tramo0)*{P['ncon']}/12"   # v3.0 (M-e): × meses de construcción / 12
        ws[f"{X}{SCAL_ROWS['Dt']}"] = f"={S['D']}+{S['IDC']}"
        ws[f"{X}{SCAL_ROWS['n']}"] = f"=MAX(1,{P['plazo']}-{P['gr']})"
        ws[f"{X}{SCAL_ROWS['PMT']}"] = f"=IF({S['Dt']}>0,IF({P['rd']}=0,{S['Dt']}/{S['n']},{S['Dt']}*{P['rd']}/(1-(1+{P['rd']})^(-{S['n']}))),0)"
        # v3.0: escalación de precios hasta la compra (M-a), reemplazo de inversores (M-c) y desmantelamiento (M-c)
        ws[f"{X}{SCAL_ROWS['fEsc']}"] = f"=Fase_m1*(1+{P['dK']})^MAX(0,Anios_Precios-1)+(1-Fase_m1)*(1+{P['dK']})^MAX(0,Anios_Precios)"
        ws[f"{X}{SCAL_ROWS['Krep']}"] = f"=IF({P['rep']}>0,Reemplazo_USD_Wac*{S['AC']}*1000,0)"
        ws[f"{X}{SCAL_ROWS['Decom']}"] = f"={P['dec']}*{S['K']}"
        for t in TS:
            rE = brow("E", t)
            tt = f"$A{rE}"   # índice t de la fila (columna A) — misma t en todos los bloques
            E = f"{X}{rE}"; EV = f"{X}{brow('Eval', t)}"; AH = f"{X}{brow('Ahorro', t)}"; OP = f"{X}{brow('OPEX', t)}"; PJ = f"{X}{brow('Peaje', t)}"
            EB = f"{X}{brow('EBITDA', t)}"; DP = f"{X}{brow('Dep', t)}"; PU = f"{X}{brow('Part_u', t)}"; IU = f"{X}{brow('IR_u', t)}"; TR = f"{X}{brow('Terr', t)}"
            FU = f"{X}{brow('FCF_u', t)}"; CU = f"{X}{brow('Cum_u', t)}"; IN = f"{X}{brow('Int', t)}"; AM = f"{X}{brow('Amort', t)}"
            PL = f"{X}{brow('Part_l', t)}"; IL = f"{X}{brow('IR_l', t)}"; CF = f"{X}{brow('CFADS', t)}"; EQ = f"{X}{brow('EQ', t)}"; DS = f"{X}{brow('DSCR', t)}"; DF = f"{X}{brow('DF', t)}"
            UX = f"{X}{brow('Ux', t)}"; IX = f"{X}{brow('Ix', t)}"; TX = f"{X}{brow('Tx', t)}"; FX = f"{X}{brow('Fx', t)}"; GX = f"{X}{brow('Gx', t)}"
            def tcell(block):
                return f"$A{brow(block, t)}"
            # cada fórmula usa el índice t de SU propia fila (columna A) para que la fila sea copiable
            ws[E] = f"=IF(OR({tcell('E')}<1,{tcell('E')}>Horizonte),0,{P['P']}/1000*{S['frec']}*IF({P['scen']}=1,INDEX(Y_P50,1,MAX(1,{tcell('E')})),INDEX(Y_P90,1,MAX(1,{tcell('E')})))*{P['disp']}*(1-{P['deg']})^({tcell('E')}-1))"
            ws[EV] = f"=MIN({E},IF({tcell('Eval')}<1,0,Consumo_Anual*(1+Crecimiento_Consumo)^({tcell('Eval')}-1)/1000))"
            ws[AH] = f"={EV}*1000*Tarifa_Evitable*{P['fT']}*(1+{P['escT']})^MAX(0,{tcell('Ahorro')}-1)"
            ws[OP] = f"=IF(OR({tcell('OPEX')}<1,{tcell('OPEX')}>Horizonte),0,{S['OPEX1']}*{P['fO']}*(1+Escalacion_OPEX)^({tcell('OPEX')}-1))"
            ws[PJ] = f"={E}*1000*{P['pj']}*INDEX(Frac_Peaje,1,{tcell('Peaje')}+2)+IF(AND({tcell('Peaje')}>=1,{tcell('Peaje')}<=Horizonte),{S['AC']}*{P['pkw']}*12*INDEX(Frac_Peaje,1,{tcell('Peaje')}+2),0)"   # v3.0 (M-h): + peaje por potencia
            ws[EB] = f"={AH}-{OP}-{PJ}-IF({tcell('EBITDA')}=Horizonte,{S['Decom']},0)"   # v3.0 (M-c): desmantelamiento deducible en t = H
            td = tcell("Dep")
            ws[DP] = (f"=IF(AND({td}>=1,{td}<=Vida_Fiscal_Equipos),{S['DepEq']},0)+IF(AND({td}>=1,{td}<=Vida_Fiscal_Civil,{td}<=Horizonte),{S['DepCiv']},0)"
                      f"+IF(AND({P['rep']}=1,Reemplazo_Anio<Horizonte,{td}>Reemplazo_Anio,{td}<=MIN(Horizonte,Reemplazo_Anio+Vida_Fiscal_Equipos)),{S['Krep']}/MIN(Vida_Fiscal_Equipos,Horizonte-Reemplazo_Anio),0)")   # v3.0 (M-c): depreciación del reemplazo
            # v3.0 (M-b): con utilidad gravable limitada (ug ≥ 0) la base negativa se absorbe hasta ug y el exceso va al pool de pérdidas, que se
            # amortiza contra bases positivas hasta el 25 % de la base gravable del año (art. 11 LRTI; pool simple sin caducidad). ug < 0 → v2.0 (Escudo_Negativo)
            PU_ = f"{X}{brow('PoolU', t)}"; PL_ = f"{X}{brow('PoolL', t)}"
            PU_prev = "0" if t == T_MIN else f"{X}{brow('PoolU', t - 1)}"; PL_prev = "0" if t == T_MIN else f"{X}{brow('PoolL', t - 1)}"
            Ut = f"IF({tcell('Part_u')}>=1,{P['ug']},0)"
            ws[PU] = (f'=IF({P["part"]}=1,IF({P["ug"]}>=0,IF({EB}-{DP}>=0,Tasa_Participacion*({EB}-{DP}),-Tasa_Participacion*MIN(-({EB}-{DP}),{Ut})),'
                      f'IF(Escudo_Negativo="Sí",Tasa_Participacion*({EB}-{DP}),MAX(0,Tasa_Participacion*({EB}-{DP})))),0)')
            dedad_t = f"IF(AND({tcell('IR_u')}>=1,{tcell('IR_u')}<=Vida_Fiscal_Equipos),{S['DedAd']},0)"
            base_u = f"({EB}-{DP}-{PU}-{dedad_t})"
            Ut_i = f"IF({tcell('IR_u')}>=1,{P['ug']},0)"
            ws[IU] = (f'=IF({P["ug"]}>=0,IF({base_u}>=0,Tasa_IR*({base_u}-MIN({PU_prev},0.25*({base_u}+{Ut_i}))),-Tasa_IR*MIN(-{base_u},{Ut_i})),'
                      f'IF(Escudo_Negativo="Sí",Tasa_IR*{base_u},MAX(0,Tasa_IR*{base_u})))')
            Ut_p = f"IF({tcell('PoolU')}>=1,{P['ug']},0)"
            ws[PU_] = f"=IF({P['ug']}>=0,{PU_prev}+IF({base_u}<0,-{base_u}-MIN(-{base_u},{Ut_p}),-MIN({PU_prev},0.25*({base_u}+{Ut_p}))),0)"
            ws[TR] = f"=IF({P['terr']}=1,IF({tcell('Terr')}=-1,-{S['Terr']},IF({tcell('Terr')}=Horizonte,{S['Resid']},0)),0)"
            tf = tcell("FCF_u")
            KR = f"{X}{brow('Krep', t)}"
            ws[FU] = f"=IF({tf}=-1,-({S['K']}+{S['IVA']})*Fase_m1,IF({tf}=0,-({S['K']}+{S['IVA']})*(1-Fase_m1)+{P['iva']}*{S['IVA']}*Fase_m1,{EB}-{PU}-{IU}+IF({tf}=1,{P['iva']}*{S['IVA']}*(1-Fase_m1),0)+{KR}))+{TR}"   # v3.0 (M-c): + bloque Krep (−reemplazo si paga SALELGI)
            ws[CU] = f"={FU}" if t == T_MIN else f"={X}{brow('Cum_u', t-1)}+{FU}"
            ti = tcell("Int")
            ws[IN] = f"=IF(OR({S['D']}=0,{ti}<1,{ti}>{P['plazo']}),0,IF({ti}<={P['gr']},{S['Dt']}*{P['rd']},IF({P['rd']}=0,0,{P['rd']}*{S['Dt']}*(1-((1+{P['rd']})^({ti}-{P['gr']}-1)-1)/((1+{P['rd']})^{S['n']}-1)))))"
            ta = tcell("Amort")
            ws[AM] = f"=IF({S['D']}=0,0,IF({P['plazo']}<={P['gr']},IF({ta}={P['plazo']},{S['Dt']},0),IF(AND({ta}>{P['gr']},{ta}<={P['plazo']}),{S['PMT']}-{IN},0)))"
            Ut_l = f"IF({tcell('Part_l')}>=1,{P['ug']},0)"
            ws[PL] = (f'=IF({P["part"]}=1,IF({P["ug"]}>=0,IF({EB}-{DP}-{IN}>=0,Tasa_Participacion*({EB}-{DP}-{IN}),-Tasa_Participacion*MIN(-({EB}-{DP}-{IN}),{Ut_l})),'
                      f'IF(Escudo_Negativo="Sí",Tasa_Participacion*({EB}-{DP}-{IN}),MAX(0,Tasa_Participacion*({EB}-{DP}-{IN})))),0)')
            dedad_l = f"IF(AND({tcell('IR_l')}>=1,{tcell('IR_l')}<=Vida_Fiscal_Equipos),{S['DedAd']},0)"
            base_l = f"({EB}-{DP}-{IN}-{PL}-{dedad_l})"
            Ut_il = f"IF({tcell('IR_l')}>=1,{P['ug']},0)"
            ws[IL] = (f'=IF({P["ug"]}>=0,IF({base_l}>=0,Tasa_IR*({base_l}-MIN({PL_prev},0.25*({base_l}+{Ut_il}))),-Tasa_IR*MIN(-{base_l},{Ut_il})),'
                      f'IF(Escudo_Negativo="Sí",Tasa_IR*{base_l},MAX(0,Tasa_IR*{base_l})))')
            Ut_pl = f"IF({tcell('PoolL')}>=1,{P['ug']},0)"
            ws[PL_] = f"=IF({P['ug']}>=0,{PL_prev}+IF({base_l}<0,-{base_l}-MIN(-{base_l},{Ut_pl}),-MIN({PL_prev},0.25*({base_l}+{Ut_pl}))),0)"
            tc = tcell("CFADS")
            ws[CF] = f"=IF({tc}<1,0,{EB}-{PL}-{IL}+IF({tc}=1,{P['iva']}*{S['IVA']}*(1-Fase_m1),0)+IF({tc}>=1,{TR},0)+{KR})"   # v3.0 (M-c): + Krep
            te_ = tcell("EQ")
            ws[EQ] = f"=IF({te_}=-1,{FU}+{S['D']}*Fase_m1,IF({te_}=0,{FU}+{S['D']}*(1-Fase_m1),{CF}-{IN}-{AM}))"
            ws[DS] = f'=IF({IN}+{AM}>0,{CF}/({IN}+{AM}),"")'
            ws[DF] = f"=IF({tcell('DF')}<1,0,1/(1+Tasa_Descuento)^{tcell('DF')})"
            # Exergy por caso
            tu = tcell("Ux")
            g = f"(1+Escalacion_OPEX)^({tu}-1)"
            ws[UX] = (f"=IF({tu}=-1,Fee_Gerencia_Pct*{S['Sub']}*Fase_m1-Costo_Gerencia_Pct*{S['Sub']}*Fase_m1,IF({tu}=0,Fee_Gerencia_Pct*{S['Sub']}*(1-Fase_m1)-Costo_Gerencia_Pct*{S['Sub']}*(1-Fase_m1),0))"
                      f"+IF(AND({tu}>=1,{tu}<=Horizonte),(1-{P['terr']})*(Renta_Terreno_ha*{S['ha']}-Predial_Terreno)*{g}+(Fee_OM_kWp-Costo_OM_Exergy_kWp)*{P['P']}*{g},0)"
                      f"-IF(AND({P['rep']}=2,{tu}=Reemplazo_Anio),{S['Krep']},0)")   # v3.0 (M-c): reemplazo a cargo de Exergy (reserva del fee de O&M)
            ws[IX] = f"=-MAX(0,{UX})*Tasa_Efectiva_Exergy"
            tx = tcell("Tx")
            ws[TX] = f"=IF({P['terr']}=1,0,IF({tx}=-1,-{S['Terr']},IF({tx}=Horizonte,{S['Resid']},0)))"
            ws[FX] = f"={UX}+{IX}+{TX}"
            ws[GX] = f"={FU}+{FX}"
            ws[KR] = f"=IF(AND({P['rep']}=1,{tcell('Krep')}=Reemplazo_Anio),-{S['Krep']},0)"
        fu = brng("FCF_u", X); cu = brng("Cum_u", X); eq = brng("EQ", X); fx = brng("Fx", X); gx = brng("Gx", X)
        ws[f"{X}{OUT_ROWS['TIR']}"] = f'=IFERROR(IRR({fu}),"n/a")'
        ws[f"{X}{OUT_ROWS['VAN']}"] = f"={X}{brow('FCF_u',-1)}*(1+Tasa_Descuento)+{X}{brow('FCF_u',0)}+NPV(Tasa_Descuento,{brng('FCF_u',X,1,25)})"
        # v3.0 (M-c / V-b): payback robusto = último año con acumulado negativo (coincide con el simple si hay un solo cruce; control H6)
        i_last = f"SUMPRODUCT(MAX(({cu}<0)*(ROW({cu})-ROW({X}${brow('Cum_u', T_MIN)})+1)))"
        ws[f"{X}{OUT_ROWS['PB']}"] = f'=IF(INDEX({cu},COUNT({cu}),1)<0,"no cruza",IF({i_last}=0,-1,({i_last}-2)+(-INDEX({cu},{i_last},1))/INDEX({fu},{i_last}+1,1)))'
        ws[f"{X}{OUT_ROWS['LCOE']}"] = f"=({S['K']}+SUMPRODUCT({brng('OPEX',X,1,25)}+{brng('Peaje',X,1,25)},{brng('DF',X,1,25)}))/SUMPRODUCT({brng('E',X,1,25)},{brng('DF',X,1,25)})"
        ws[f"{X}{OUT_ROWS['TIR_eq']}"] = f'=IF({S["D"]}>0,IFERROR(IRR({eq},0.02),"n/a"),"n/a")'   # v3.1: semilla 2 % — con 100 % de deuda LibreOffice no converge desde la semilla por defecto (Excel: mismo valor)
        ws[f"{X}{OUT_ROWS['VAN_eq']}"] = f"={X}{brow('EQ',-1)}*(1+{P['req']})+{X}{brow('EQ',0)}+NPV({P['req']},{brng('EQ',X,1,25)})"   # v3.0 (M-g): a la tasa del accionista
        ws[f"{X}{OUT_ROWS['DSCR_min']}"] = f'=IF({S["D"]}>0,MIN({brng("DSCR",X,1,25)}),"n/a")'
        ws[f"{X}{OUT_ROWS['DSCR_avg']}"] = f'=IF({S["D"]}>0,AVERAGE({brng("DSCR",X,1,25)}),"n/a")'
        ws[f"{X}{OUT_ROWS['Ahorro1']}"] = f"={X}{brow('Ahorro',1)}"
        ws[f"{X}{OUT_ROWS['Aporte_eq']}"] = f"=-({X}{brow('EQ',-1)}+{X}{brow('EQ',0)})"
        ws[f"{X}{OUT_ROWS['VAN_X']}"] = f"={X}{brow('Fx',-1)}*(1+Tasa_Descuento)+{X}{brow('Fx',0)}+NPV(Tasa_Descuento,{brng('Fx',X,1,25)})"
        ws[f"{X}{OUT_ROWS['TIR_G']}"] = f'=IFERROR(IRR({gx}),"n/a")'
        ws[f"{X}{OUT_ROWS['E1']}"] = f"={X}{brow('E',1)}"
        ws[f"{X}{OUT_ROWS['NoRec']}"] = f"=SUM({brng('E',X,1,25)})-SUM({brng('Eval',X,1,25)})"
        ws[f"{X}{OUT_ROWS['Cob']}"] = f"=IF(Consumo_Anual>0,{X}{brow('E',1)}*1000/Consumo_Anual,0)"
        ws[f"{X}{OUT_ROWS['Nominal_X']}"] = f"=SUM({fx})"
        for rr in list(SCAL_ROWS.values()) + list(OUT_ROWS.values()):
            cell = ws.cell(row=rr, column=2 + j); cell.font = font(size=9); cell.number_format = FMT_USD
        for k, fmt_ in (("TIR", FMT_PCT2), ("TIR_eq", FMT_PCT2), ("TIR_G", FMT_PCT2), ("Cob", FMT_PCT), ("PB", FMT_YRS), ("LCOE", FMT_DEC1), ("DSCR_min", FMT_X), ("DSCR_avg", FMT_X), ("E1", FMT_INT), ("NoRec", FMT_INT)):
            ws.cell(row=OUT_ROWS[k], column=2 + j).number_format = fmt_
        for k, fmt_ in (("n", "0"), ("frec", "0.0000"), ("AC", FMT_INT), ("ha", "0.00"), ("fKeff", "0.0000")):
            ws.cell(row=SCAL_ROWS[k], column=2 + j).number_format = fmt_
        for b in BLOCKS:
            for t in TS:
                cell = ws.cell(row=brow(b, t), column=2 + j); cell.font = font(size=8.5, color=GRAFITO)
                cell.number_format = FMT_INT if b in ("E", "Eval") else (FMT_X if b == "DSCR" else ("0.0000" if b == "DF" else FMT_USD))
    # D12: se imprime sólo el bloque de casos principales (A1:M{última fila de salidas}); las 102 columnas siguen visibles en pantalla
    setup_print(ws, landscape=True, area=f"A1:M{OUT_ROWS['Nominal_X']}")
    return ws
