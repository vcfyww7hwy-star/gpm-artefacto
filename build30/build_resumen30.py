# -*- coding: utf-8 -*-
"""Modelo FV 5MWp — Resumen Directorio v2.0 (U1: motor unificado con el modelo completo).
· El Motor es el mismo build_motor de build_core v2.0 (99 casos: Custom · Conservador · Base · Favorable · sensibilidades) alimentado por
  las mismas fórmulas; ya no hay un motor propio con constantes copiadas. Todo lo que el Motor necesita y el directorio no edita vive en la
  hoja oculta «Inputs» (valores por defecto tomados de build_core.INPUTS/ESCENARIOS, vectores canónicos, tabla de consumo, derivados).
· «Supuestos» sigue la estructura de 01 del modelo: una columna de valor (diseño compartido) y el bloque B con cuatro columnas.
· «Resumen», «Resultados» y «Sensibilidad» presentan el Custom con los tres escenarios fijos como referencia (colores de caso).
· El chip «coincide con el modelo completo» compara los KPI del Motor con referencias inyectadas por el pipeline (Ref_*).
Uso: build_resumen30.py SALIDA.xlsx [--ref MODELO_calc.xlsx]"""
import sys, os
from datetime import date
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.pagebreak import Break
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.chart import Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.chart.data_source import StrRef
from openpyxl.worksheet.views import Selection
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
import xl_helpers as XH
from xl_helpers import *
import build_core as BCORE
from build_core import (RUBROS, TS, T_MIN, T_MAX, PARAM_ROWS, SCAL_ROWS, OUT_ROWS, INPUTS, ESCENARIOS, CASE_KEYS, MOTOR_CASE_COL, SM, VERSION,
                        FECHA_ANALISIS, Y50, Y90, CURVA_RECORTE, CONS_2025, CONS_2026_ENE_MAY, CONS_2025_ENE_MAY, MESES, f_loss, brow, brng,
                        build_motor, SELECTORS, YESNO)
from build_content import (build_cases, CASE_X, CASE_C, CASE_B, CASE_F, CASE_ESC, CASE_P50, CASE_P90, TORNADO, TORNADO_SHORT, MAT_START, EQ_START, T_DEDAD,
                           LEV_START, mo, mcol, T_CAPEX_UP, T_CAPEX_DN, T_PEAJE, BR0, BR1, BR2, BR3, BR4, BR5)

OUT = sys.argv[1] if len(sys.argv) > 1 else "/root/gpm13/out20/Modelo_FV_5MWp_Resumen_Directorio_v2.0.xlsx"
REF_PATH = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "/root/gpm13/out20/Modelo_FV_5MWp_GPM_v2.0_calc.xlsx"
# r3 (R3-8): la etiqueta seguía en «v3.0 · 04-sep-2026» en r2 (hallazgo 11-sep-2026); ahora sigue a la versión y a la fecha de corte del modelo
VERSION_RES = f"Resumen Directorio {VERSION}"
_MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
FECHA_RES = f"{FECHA_ANALISIS.day:02d}-{_MES[FECHA_ANALISIS.month - 1]}-{FECHA_ANALISIS.year}"
R0, R1, R2, R3, R4, R5, RI = "Resumen", "Supuestos", "Costos", "Resultados", "Sensibilidad", "Legal y riesgos", "Inputs"
RM = SM   # el Motor conserva el nombre del modelo («Motor_Sens») para que mo() y las regresiones sean las mismas
NS = 6    # hojas visibles
INP = {nm: (lab, val, u, fmt, conf, nt) for sec, nm, lab, val, u, fmt, conf, nt in INPUTS if nm}
ESC = {e[0]: e for e in ESCENARIOS}


def mcell(idx, block, t):
    return f"'{RM}'!${mcol(idx)}${brow(block, t)}"


def mblock(idx, block, t1=T_MIN, t2=T_MAX):
    return f"'{RM}'!{brng(block, mcol(idx), t1, t2)}"


def cf_scale(ws, ref, mid_num=None):
    ws.conditional_formatting.add(ref, CellIsRule(operator="lessThan", formula=["Tasa_Descuento" if mid_num is None else str(mid_num)], font=Font(color=LADRILLO, bold=True)))


def cf_dscr(ws, rng_):
    ws.conditional_formatting.add(rng_, CellIsRule(operator="lessThan", formula=["1"], font=Font(color=LADRILLO, bold=True)))
    ws.conditional_formatting.add(rng_, CellIsRule(operator="between", formula=["1", "DSCR_Objetivo"], font=Font(color=ARCILLA, bold=True)))


def esc_def(k, prefix=True):
    """Definición viva del caso k (1 = Custom … 4 = Favorable) leída del bloque B."""
    e = lambda nm: f"INDEX({nm},{k})"
    head = f'"{CASO_NOMBRE[CASE_KEYS[k-1]]} · "&' if prefix else ""
    return (f'={head}{e("Esc_Energia")}&" · CAPEX "&IF(N({e("Esc_CAPEX_Fijo_Wp")})>0,"fijo "&TEXT({e("Esc_CAPEX_Fijo_Wp")},"0.00")&" $/Wp","bottom-up × "&TEXT({e("Esc_Factor_CAPEX")},"0.00"))'
            f'&IF({e("Esc_Escalacion_CAPEX")}>0," +"&TEXT({e("Esc_Escalacion_CAPEX")},"0%")&"/año","")&" · OPEX × "&TEXT({e("Esc_Factor_OPEX")},"0.00")&" · peaje "&TEXT({e("Esc_Peaje")}*100,"0.0")&" ¢/kWh desde "&TEXT(Fecha_Peaje,"mmm-yyyy")&" · tarifa "&IF({e("Esc_EscTarifa")}=0,"plana","+"&TEXT({e("Esc_EscTarifa")},"0.0%")&"/año")&" · disp. "&TEXT({e("Esc_Disponibilidad")},"0%")')


def read_refs(path):
    """Referencias del modelo completo (KPI de los cuatro casos) para el chip de consistencia; None si no hay libro recalculado."""
    if not os.path.exists(path):
        return None
    wb = load_workbook(path, data_only=True)
    out = {}
    for tag in CASE_KEYS:
        for key in ("TIR", "TIReq", "VAN"):
            dn = wb.defined_names.get(f"{tag}_{key}")
            sh, ref = next(iter(dn.destinations))
            out[f"Ref_{tag}_{key}"] = wb[sh][ref.replace("$", "")].value
    dn = wb.defined_names.get("Meses_Construccion")
    if dn is not None:
        sh, ref = next(iter(dn.destinations)); MODEL_VALUES["Meses_Construccion"] = wb[sh][ref.replace("$", "")].value
    return out


# ------------------------------------------------------------------ Inputs (oculta): lo que el Motor necesita y el directorio no edita
def hidden_scalars():
    """Escalares de INPUTS que Supuestos no muestra (V9): van a Inputs con los mismos valores y nombres."""
    return [nm for nm in INP if nm not in SHOWN and nm not in ("Version", "Fecha_Analisis")]


def build_inputs(wb, refs):
    ws = wb.create_sheet(RI)
    widths(ws, {"A": 2, "B": 52, "C": 14, "D": 12, "E": 40})
    sheet_header(ws, "Inputs del motor (hoja oculta — no editar)", "Entradas que el Motor necesita y que el directorio no edita: mismos valores por defecto que 01_Supuestos del modelo completo (generados desde build_core), vectores canónicos (yield P50/P90, curva de recorte), tabla de consumo del medidor y derivados. Cambiar aquí equivale a cambiar el modelo completo.", 7, total=NS, last_col=5, guide=False)
    r = 5
    section(ws, r, 2, 5, "A · Escalares que Supuestos no muestra (mismos valores que 01_Supuestos del modelo completo; F = 2 si «por confirmar»)")
    r += 1
    h0 = r
    for nm in hidden_scalars():
        lab, val, u, fmt, conf, nt = INP[nm]
        if isinstance(val, str) and val.startswith("=") and nm == "Tasa_Descuento_Equity":
            val = MODEL_VALUES.get(nm, val)
        label(ws, r, 2, lab + (" · por confirmar" if conf else ""), size=9, wrap=True)
        c = canon(ws, r, 3, val, fmt=fmt)
        unit(ws, r, 4, u); note(ws, r, 5, (nt or "")[:90], border=True, valign="center", size=8.5)
        mk = ws.cell(row=r, column=6, value=(2 if conf else 1)); mk.font = Font(name=FONT, size=8.5, color=GRAFITO)
        name(wb, nm, RI, f"$C${r}")
        ws.row_dimensions[r].height = 16
        r += 1
    name(wb, "Inputs_Mark", RI, f"$F${h0}:$F${r-1}")
    for nm, (lab, val, u, fmt) in SENS_PARAMS.items():
        label(ws, r, 2, lab, size=9); canon(ws, r, 3, val, fmt=fmt); unit(ws, r, 4, u); note(ws, r, 5, "Paso del tornado (Sensibilidad)", border=True, valign="center", size=8.5)
        name(wb, nm, RI, f"$C${r}"); ws.row_dimensions[r].height = 16; r += 1
    label(ws, r, 2, "Versión del libro", size=9); canon(ws, r, 3, VERSION_RES); name(wb, "Version", RI, f"$C${r}"); ws.row_dimensions[r].height = 16; r += 1
    label(ws, r, 2, "Fecha de corte del análisis", size=9); canon(ws, r, 3, FECHA_ANALISIS, fmt=FMT_DATE); name(wb, "Fecha_Analisis", RI, f"$C${r}"); ws.row_dimensions[r].height = 16; r += 1
    label(ws, r, 2, "Demanda facturable promedio 2026 (factura de referencia)", size=9); canon(ws, r, 3, 2200, fmt=FMT_INT); unit(ws, r, 4, "kW"); name(wb, "Demanda_Prom", RI, f"$C${r}"); ws.row_dimensions[r].height = 16; r += 1
    label(ws, r, 2, "FGD promedio (factura de referencia)", size=9); canon(ws, r, 3, 0.956, fmt="0.000"); name(wb, "FGD_Prom", RI, f"$C${r}"); ws.row_dimensions[r].height = 16; r += 1
    ws.row_dimensions[r].height = 8; r += 1
    # ---- listas de sensibilidad que el Motor calcula aunque el Resumen no las muestre
    section(ws, r, 2, 5, "B · Barridos del Motor (10 §F/§H del modelo completo; el Resumen no los muestra)")
    r += 1
    for lab, vals, fmt, nm in [("Barrido de potencia DC (kWp)", [5000, 6000, 7000, 8000], FMT_INT, "Sweep_P"), ("Barrido de ratio DC/AC", [1.10, 1.20, 1.32, 1.40, 1.50], "0.00", "Sweep_Ratio"),
                               ("Apalancamientos para la deuda máxima", [0.4, 0.5, 0.6, 0.7, 0.8], FMT_PCT0, "Sweep_Lev")]:
        label(ws, r, 2, lab, size=9)
        for i, v in enumerate(vals):
            canon(ws, r, 3 + i, v, fmt=fmt)
        name(wb, nm, RI, f"$C${r}:${col(2+len(vals))}${r}"); ws.row_dimensions[r].height = 16; r += 1
    label(ws, r, 2, "Potencia AC fija del barrido §F.3", size=9); canon(ws, r, 3, 3800, fmt=FMT_INT); unit(ws, r, 4, "kWac"); name(wb, "Sweep_AC_Fija", RI, f"$C${r}"); ws.row_dimensions[r].height = 16; r += 1
    ws.row_dimensions[r].height = 8; r += 1
    # ---- vectores canónicos (horizontales, como en 04)
    section(ws, r, 2, 5, "C · Vectores canónicos (pvlib sobre TMY Solargis adaptado, 15-jul-2026; curva de recorte pvlib 02-sep-2026)")
    r += 1
    label(ws, r, 2, "Año de operación t", size=9)
    for i in range(30):
        c = ws.cell(row=r, column=3 + i, value=i + 1); c.font = font(size=8.5, color=GRAFITO)
    r += 1
    label(ws, r, 2, "Yield canónico P50 a la referencia [kWh/kWp]", size=9)
    for i, v in enumerate(Y50):
        canon(ws, r, 3 + i, v, fmt=FMT_INT)
    name(wb, "Y_P50", RI, f"$C${r}:${col(2+30)}${r}"); r += 1
    label(ws, r, 2, "Yield canónico P90 a la referencia [kWh/kWp]", size=9)
    for i, v in enumerate(Y90):
        canon(ws, r, 3 + i, v, fmt=FMT_INT)
    name(wb, "Y_P90", RI, f"$C${r}:${col(2+30)}${r}"); r += 1
    label(ws, r, 2, "Yield específico P50 año 1 (Yield_Ref)", size=9); calc(ws, r, 3, "=INDEX(Y_P50,1,1)", fmt=FMT_INT, size=9); name(wb, "Yield_Ref", RI, f"$C${r}"); r += 1
    r += 1
    # curva de recorte en columnas (vertical, como en 04: f_loss usa ROWS(CR_Ratio))
    label(ws, r, 2, "Curva de recorte pvlib · ratio DC/AC (col. C) · pérdida por recorte (col. D)", size=9)
    r += 1
    n = len(CURVA_RECORTE)
    for i, pt in enumerate(CURVA_RECORTE):
        canon(ws, r + i, 3, pt["ratio"], fmt="0.00"); canon(ws, r + i, 4, pt["clipping"], fmt=FMT_PCT2)
        ws.row_dimensions[r + i].height = 13
    name(wb, "CR_Ratio", RI, f"$C${r}:$C${r+n-1}"); name(wb, "CR_Loss", RI, f"$D${r}:$D${r+n-1}")
    r += n
    label(ws, r, 2, "Pérdida a Ratio_Ref (Loss_Ref)", size=9); calc(ws, r, 3, "=" + f_loss("Ratio_Ref"), fmt=FMT_PCT2, size=9); name(wb, "Loss_Ref", RI, f"$C${r}"); r += 1
    label(ws, r, 2, "Pérdida a Ratio_DCAC (Loss_Act)", size=9); calc(ws, r, 3, "=" + f_loss("Ratio_DCAC"), fmt=FMT_PCT2, size=9); name(wb, "Loss_Act", RI, f"$C${r}"); r += 1
    label(ws, r, 2, "Factor de recorte F_Recorte", size=9); calc(ws, r, 3, "=(1-Loss_Act)/(1-Loss_Ref)", fmt="0.0000", size=9); name(wb, "F_Recorte", RI, f"$C${r}"); r += 1
    r += 1
    label(ws, r, 2, "Eje t (−1…25) para la fracción de peaje", size=9)
    trow = r
    for i, t in enumerate(TS):
        c = ws.cell(row=r, column=3 + i, value=t); c.font = font(size=8.5, color=GRAFITO)
    r += 1
    label(ws, r, 2, "Fracción del año con peaje SGDA vigente (Frac_Peaje)", size=9)
    for i, t in enumerate(TS):
        L = col(3 + i)
        calc(ws, r, 3 + i, f"=IF({L}${trow}<1,0,MAX(0,MIN(1,(EDATE(Fecha_COD,12*{L}${trow})-MAX(Fecha_Peaje,EDATE(Fecha_COD,12*({L}${trow}-1))))/(EDATE(Fecha_COD,12*{L}${trow})-EDATE(Fecha_COD,12*({L}${trow}-1))))))", fmt="0.000", size=8.5, color=GRAFITO)
    name(wb, "Frac_Peaje", RI, f"$C${r}:${col(2+len(TS))}${r}"); r += 1
    ws.row_dimensions[r].height = 8; r += 1
    # ---- consumo del medidor (misma tabla y fórmulas que 04 T1)
    section(ws, r, 2, 5, "D · Consumo del medidor de GPM (planillas 2025 × nivel 2026) y factura de referencia — mismas fórmulas que 04_Energia")
    r += 1
    hdr(ws, r, 2, 11, ["Mes", "2025 · A", "2025 · B", "2025 · C", "2025 total", "Proy. A", "Proy. B", "Proy. C", "Proy. total [kWh]", ""], height=18)
    r += 1
    m0 = r
    for i in range(12):
        a, b, cc_ = CONS_2025[i]
        label(ws, r, 2, MESES[i], size=9)
        canon(ws, r, 3, a, fmt=FMT_INT); canon(ws, r, 4, b, fmt=FMT_INT); canon(ws, r, 5, cc_, fmt=FMT_INT)
        calc(ws, r, 6, f"=C{r}+D{r}+E{r}", fmt=FMT_INT, size=9)
        calc(ws, r, 7, f"=C{r}*Factor_Nivel_2026", fmt=FMT_INT, size=9); calc(ws, r, 8, f"=D{r}*Factor_Nivel_2026", fmt=FMT_INT, size=9); calc(ws, r, 9, f"=E{r}*Factor_Nivel_2026", fmt=FMT_INT, size=9)
        calc(ws, r, 10, f"=G{r}+H{r}+I{r}", fmt=FMT_INT, size=9, bold=True)
        ws.row_dimensions[r].height = 15
        r += 1
    label(ws, r, 2, "Año", bold=True, size=9)
    for cidx in range(3, 11):
        L = col(cidx)
        calc(ws, r, cidx, f"=SUM({L}{m0}:{L}{m0+11})", fmt=FMT_INT, bold=True, size=9)
    tot1 = r
    name(wb, "Consumo_Anual", RI, f"$J${r}")
    r += 1
    label(ws, r, 2, "Σ ene–may 2025 / 2026 (planillas)", size=9); canon(ws, r, 3, sum(CONS_2025_ENE_MAY), fmt=FMT_INT); canon(ws, r, 4, sum(CONS_2026_ENE_MAY), fmt=FMT_INT)
    r += 1
    label(ws, r, 2, "Factor de nivel 2026 (Σ 2026 / Σ 2025)", size=9); calc(ws, r, 3, f"=D{r-1}/C{r-1}", fmt="0.000", size=9, bold=True); name(wb, "Factor_Nivel_2026", RI, f"$C${r}")
    r += 1
    label(ws, r, 2, "Factura de referencia anual sin SGDA (tarifa 2026)", size=9, bold=True)
    calc(ws, r, 3, f"=G{tot1}*Tarifa_A+H{tot1}*Tarifa_A+I{tot1}*Tarifa_C+Demanda_Prom*Cargo_Demanda*FGD_Prom*12+(Cargo_Comercializacion+SAPG_mes)*12", fmt=FMT_USD, size=9, bold=True)
    name(wb, "Factura_Referencia", RI, f"$C${r}"); r += 1
    ws.row_dimensions[r].height = 8; r += 1
    # ---- derivados que el Motor y los textos usan
    section(ws, r, 2, 5, "E · Derivados (mismas fórmulas que 01 §J y 04 del modelo completo)")
    r += 1
    derived = [
        ("Escenario de energía efectivo del Custom (1 = P50 · 2 = P90)", '=IF(Escenario_Energia="P50",1,2)', "0", "Eff_Scen"),
        ("Factor OPEX efectivo del Custom", "=Factor_OPEX", "0.000", "Eff_fO"),
        ("Peaje SGDA efectivo del Custom", "=Peaje_SGDA", FMT_KWH, "Eff_Peaje"),
        ("Escalación de tarifa efectiva del Custom", "=Escalacion_Tarifa", FMT_PCT, "Eff_EscT"),
        ("Tasa efectiva marginal de SALELGI", '=IF(Incluir_Participacion="Sí",Tasa_Participacion,0)+Tasa_IR*(1-IF(Incluir_Participacion="Sí",Tasa_Participacion,0))', FMT_PCT2, "Tasa_Efectiva"),
        ("Tarifa evitable (ponderada por bloques)", "=Frac_A*Tarifa_A+Frac_B*Tarifa_A+Frac_C*Tarifa_C", "0.000000", "Tarifa_Evitable"),
        ("Potencia AC nominal", "=Potencia_DC/Ratio_DCAC", FMT_INT, "Potencia_AC"),
        ("Hectáreas requeridas", "=Potencia_DC/1000/Densidad_MWp_ha", "0.00", "Hectareas"),
        ("Años entre los precios del CAPEX y el COD (base de la escalación)", "=(Fecha_COD-Fecha_Precios)/365.25", "0.00", "Anios_Precios"),
        ("Escala de los componentes por Wp", "=(Potencia_DC/Potencia_Ref)^(1-Exponente_Escala)", "0.0000", "Escala_Wp"),
        ("Escala de los componentes por Wac", "=(Potencia_AC/(Potencia_Ref/Ratio_Ref))^(1-Exponente_Escala)", "0.0000", "Escala_Wac"),
        ("Escalación de precios hasta la compra (Custom) — como 05 del modelo", "=Fase_m1*(1+Escalacion_CAPEX)^MAX(0,Anios_Precios-1)+(1-Fase_m1)*(1+Escalacion_CAPEX)^MAX(0,Anios_Precios)", "0.0000", "Factor_Escalacion"),
        ("Factor del caso Custom (× cada rubro de Costos), incl. escalación", "=IF(N(CAPEX_Fijo_Wp)>0,CAPEX_Fijo_Wp*Potencia_DC*1000/CAPEX_Base_f1,Factor_CAPEX)*Factor_Escalacion", "0.000", "Factor_Caso"),
        ("CAPEX industrial del Custom (sin IVA) — Motor", f"='{RM}'!$B${SCAL_ROWS['K']}", FMT_USD, "CAPEX_Total"),
        ("IVA del CAPEX del Custom — Motor", f"='{RM}'!$B${SCAL_ROWS['IVA']}", FMT_USD, "IVA_Total"),
        ("Cobertura del consumo (año 1, P50 — como 04 del modelo)", f"='{RM}'!${mcol(CASE_P50)}${OUT_ROWS['Cob']}", FMT_PCT, "Cobertura_Anual"),
        ("Ahorro año 1 (Custom)", f"='{RM}'!$B${OUT_ROWS['Ahorro1']}", FMT_USD, "Ahorro_Anio1"),
        ("Reducción de la factura eléctrica (año 1, P50 — como 04 del modelo)", "=P50_Ahorro1/Factura_Referencia", FMT_PCT, "Reduccion_Factura"),
        ("Deuda total al COD (Custom) — Motor", f"='{RM}'!$B${SCAL_ROWS['Dt']}", FMT_USD, "Deuda_Total"),
        ("Deuda desembolsada (Custom) — Motor", f"='{RM}'!$B${SCAL_ROWS['D']}", FMT_USD, "Deuda_Monto"),
        ("Cuota anual (Custom) — Motor", f"='{RM}'!$B${SCAL_ROWS['PMT']}", FMT_USD, "Cuota"),
        ("VAN del negocio Exergy (Custom) — Motor", f"='{RM}'!$B${OUT_ROWS['VAN_X']}", FMT_USD, "VAN_Exergy"),
        ("Ingreso neto nominal de Exergy Σ (Custom) — Motor", f"='{RM}'!$B${OUT_ROWS['Nominal_X']}", FMT_USD, "Nominal_Exergy"),
        ("TIR del negocio Exergy (Custom)", f"=IFERROR(IRR({mblock(CASE_X, 'Fx')}),\"n/a\")", FMT_PCT2, "TIR_Exergy"),
        ("TIR consolidada del grupo (Custom) — Motor", f"='{RM}'!$B${OUT_ROWS['TIR_G']}", FMT_PCT2, "TIR_Grupo"),
        ("Servicios Exergy (fee O&M + arriendo) / ahorro año 1", '=IF(Ahorro_Anio1>0,(Fee_OM_kWp*Potencia_DC+IF(Comprador_Terreno="Exergy",Renta_Terreno_ha*Hectareas,0))/Ahorro_Anio1,0)', FMT_PCT, "Carga_Exergy"),
        ("Año del DSCR mínimo (t) del Custom", f"=IF('{RM}'!$B${SCAL_ROWS['D']}>0,INDEX('{RM}'!$A${brow('DSCR',1)}:$A${brow('DSCR',25)},MATCH('{RM}'!$B${OUT_ROWS['DSCR_min']},{mblock(CASE_X,'DSCR',1,25)},0)),\"—\")", "0", "Anio_DSCR_Min"),
    ]
    for lab, f, fmt, nm in derived:
        label(ws, r, 2, lab, size=9); calc(ws, r, 3, f, fmt=fmt, size=9); name(wb, nm, RI, f"$C${r}"); ws.row_dimensions[r].height = 16; r += 1
    ws.row_dimensions[r].height = 8; r += 1
    # ---- referencias del modelo completo (inyectadas por el pipeline desde el libro recalculado)
    section(ws, r, 2, 5, "F · Referencias del modelo completo v2.0 (para el chip de consistencia; las inyecta el pipeline)")
    r += 1
    for tag in CASE_KEYS:
        for key, fmt in (("TIR", FMT_PCT2), ("TIReq", FMT_PCT2), ("VAN", FMT_USD)):
            nm = f"Ref_{tag}_{key}"
            label(ws, r, 2, f"{nm} — {CASO_NOMBRE[tag]} · {key} del modelo completo", size=9)
            v = refs.get(nm) if refs else None
            canon(ws, r, 3, v if v is not None else 0, fmt=fmt)
            name(wb, nm, RI, f"$C${r}"); ws.row_dimensions[r].height = 15; r += 1
    setup_print(ws, landscape=True, scale=70, area=f"A1:E{r}")
    return ws


# ------------------------------------------------------------------ Supuestos (una columna; bloque B con cuatro columnas)
# V9: dos páginas — mandos (A), bloque B y las entradas de diseño que deciden (C–F); el resto de los parámetros vive en «Inputs» (oculta) con los mismos valores
BLOQUES = [
    ("A · Mandos y marco general", "los maestros del diseño, compartidos por los cuatro casos", ["Potencia_DC", "Ratio_DCAC", "Comprador_Terreno", "Fecha_COD", "Meses_Construccion", "Horizonte", "Tasa_Descuento", "Tasa_Descuento_Equity"]),
    ("B · Supuestos de escenario", None, [e[0] for e in ESCENARIOS]),
    ("C · Energía, consumo y tarifa (GPM · AV1)", "un solo valor para los cuatro casos · medidor de SALELGI S.A. en CNEL El Oro", ["Consumo_Anual", "Factura_Referencia", "Tarifa_A", "Fecha_Peaje", "Peaje_kW_mes", "Degradacion_Adicional"]),
    ("D · CAPEX, reemplazo y gerencia", "compartido por los cuatro casos · rubros en Costos", ["Contrato_Inversion", "IVA_Recuperable", "Fee_Gerencia_Pct", "Reemplazo_Anio", "Reemplazo_USD_Wac", "Reemplazo_Pagador"]),
    ("E · OPEX y deuda de SALELGI", "compartido por los cuatro casos", ["Fee_OM_kWp", "Renta_Terreno_ha", "Escalacion_OPEX", "Pct_Apalancamiento", "Tasa_Deuda", "Plazo_Deuda"]),
    ("F · Fiscal y terreno", "compartido por los cuatro casos", ["Escudo_Negativo", "Utilidad_Gravable_SALELGI", "Ingresos_SALELGI", "Precio_Terreno_ha"]),
]
SHOWN = {nm for _, _, names_ in BLOQUES for nm in names_}
SENS_PARAMS = {"Sens_CAPEX": ("Tornado: variación del CAPEX (±)", 0.15, "%", FMT_PCT), "Sens_Tarifa": ("Tornado: variación de la tarifa evitable (±)", 0.15, "%", FMT_PCT),
               "Sens_OPEX_Up": ("Tornado: OPEX al alza (+)", 0.30, "%", FMT_PCT), "Sens_OPEX_Dn": ("Tornado: OPEX a la baja (−)", 0.15, "%", FMT_PCT),
               "Sens_Peaje": ("Tornado: peaje SGDA desde 28-feb-2029", 0.015, "$/kWh", FMT_KWH), "Sens_EscTarifa": ("Tornado: escalación de la tarifa, aumento frente al Custom", 0.01, "pp/año", FMT_PCT),
               "Sens_Disponibilidad": ("Tornado: disponibilidad, reducción frente al Custom", 0.02, "pp", FMT_PCT), "Sens_EscCAPEX": ("Tornado: escalación del CAPEX, aumento", 0.02, "pp/año", FMT_PCT),
               "Sens_Peaje_kW": ("Tornado: peaje por potencia", 0.5, "$/kW-mes", FMT_DEC2)}
MODEL_VALUES = {}   # valores del modelo completo recalculado que el Resumen toma como constante (Meses_Construccion = Mes_COD_Cron de 03)
CALC_ROWS = {"Consumo_Anual": ("Consumo anual del medidor (planillas 2025 × nivel 2026)", "=Consumo_Anual", "kWh/año", FMT_INT, "Tabla mensual en Inputs (misma fórmula que 04)"),
             "Factura_Referencia": ("Factura eléctrica anual de referencia sin SGDA", "=Factura_Referencia", "USD", FMT_USD, "Consumo × tarifa 2026 + demanda + fijos (como 04)")}
SHORT = {"Potencia_DC": "Mando maestro 1 · lista 5–8 MWp (mín. 5.000)", "Ratio_DCAC": "Mando maestro 2 · diseño 5.000 kWp / 3.788 kWac", "Comprador_Terreno": "SALELGI compra (v3.1) · alt. Exergy arrienda",
         "Fecha_COD": "Ruta crítica 18–32 m desde sep-2026", "Horizonte": "Vida útil del certificado SGDA (FV): 25 años", "Tasa_Descuento": "Decisión previa; VAN referido al COD",
         "Escenario_Energia": "P50 mediana pvlib · P90 −10,7 %", "Factor_CAPEX": "1,15 = rango alto del estudio CAPEX/OPEX", "CAPEX_Fijo_Wp": "0,75 = deck v4 (22-jul-2026) · vacío = bottom-up",
         "Factor_OPEX": "1,15 = rango alto del estudio", "Peaje_SGDA": "No publicado · 0,5 / 1,5 / 0,5 / 0 ¢/kWh", "Escalacion_Tarifa": "Plana · Favorable +2 %/año",
         "Tarifa_A": "Res. ARCONEL-006/25; pliego 2026 (Res. 029/25)", "Tarifa_C": "Ídem, cargo nocturno", "Frac_A": "TMY horario: 96,7 % en 08–18 h", "Frac_B": "TMY: 0,2 % (cargo = bloque A)", "Frac_C": "TMY: 3,1 % (06–08 h)",
         "Fecha_Peaje": "Disp. Trans. 005/24 = 5 años desde el RLOCE", "Contingencia_Pct": "Estudio CAPEX 5–8 %", "Fee_Gerencia_Pct": "Decisión 01-09-2026; sens. 5/7/9 %", "Asignacion_Compartida": "Conservador: 100 % (alternativa 50 %)",
         "Contrato_Inversion": "COPCI; −5 pts IR no aplica a SALELGI", "IVA_Recuperable": "SALELGI factura arriendos gravados (art. 66 LRTI)", "Tasa_IVA": "LRTI art. 65 (15 %); sin cambio 2026", "FODINFA_Pct": "COPCI art. 110",
         "ISD_Pct": "SRI 2026; costo capitalizable", "Fase_m1": "30 % desarrollo y anticipos / 70 % construcción", "Fee_OM_kWp": "Sens. 18/20/24", "Seguro_kWp": "≈ 0,4 % del CAPEX", "Renta_Terreno_ha": "10 % bruto sobre 50.000 $/ha; sens. 3/5/7 k",
         "Tributos_Locales": "Estimación; confirmar con GAD", "Escalacion_OPEX": "1–2 %", "Pct_Apalancamiento": "Sens. 50–80 %", "Tasa_Deuda": "BCE mar-2026: máx. corporativo 9,33 %", "Plazo_Deuda": "A 10 años el DSCR mejora; a 12 empeora",
         "Gracia_Deuda": "IDC del año 0 capitalizado", "IDC_Frac_Tramo0": "Decisión G2-1 (02-09-2026): medio año", "Tasa_IR": "LRTI art. 37", "Tasa_Participacion": "Código del Trabajo art. 97", "Incluir_Participacion": "Caso ácido: Sí",
         "Escudo_Negativo": "Por confirmar con contabilidad", "Vida_Fiscal_Equipos": "RALRTI 10 %", "Vida_Fiscal_Civil": "RALRTI 5 %", "Pct_Elegible_DedAd": "Maquinaria, equipos y tecnología (LRTI art. 10.7)",
         "Ingresos_SALELGI": "Rango 8–12 M; el tope no muerde si ≥ 5,4 M", "Tope_DedAd_Pct": "LRTI art. 10.7", "Costo_Gerencia_Pct": "Estimación", "Costo_OM_Exergy_kWp": "Margen = fee − costo", "Precio_Terreno_ha": "Decisión 01-09-2026",
         "Costos_Transaccion_Terreno_Pct": "Alcabala 1 % + notaría/registro ≈ 0,5 %", "Predial_Terreno": "Estimación", "Residual_Terreno_Pct": "Sin plusvalía",
         "Disponibilidad": "98 / 97 / 98 / 99 % · garantía O&M pendiente", "Escalacion_CAPEX": "3 / 5 / 3 / 0 %/año desde jul-2026",
         "Tasa_Descuento_Equity": "12 % · sólo el VAN del accionista", "Meses_Construccion": "Mes_COD_Cron del cronograma de 03 del modelo · IDC × meses/12",
         "Fecha_Precios": "Precios del deck v4 (22-jul-2026)", "Reemplazo_Anio": "Vida útil inversores 10–15 a", "Reemplazo_USD_Wac": "≈ 6 % del CAPEX · cotización pendiente",
         "Reemplazo_Pagador": "SALELGI · alt. Exergy (fee) · No", "Desmantelamiento_Pct": "0 % en Base · 2 % en tornado", "Degradacion_Adicional": "0 · 0,2 %/año en tornado",
         "Peaje_kW_mes": "Art. 5.17 005/24 · no publicado · 0,5 / 1,0 en tornado", "Utilidad_Gravable_SALELGI": "Vacío = ilimitada · dato P3 pendiente"}
LABEL = {"Ratio_DCAC": "Ratio DC/AC (módulos / inversores)", "Escenario_Energia": "Energía del caso (P50 / P90)", "Factor_CAPEX": "Factor sobre el CAPEX bottom-up (Costos)", "CAPEX_Fijo_Wp": "CAPEX unitario fijo (vacío = bottom-up × factor)",
         "Factor_OPEX": "Factor sobre el OPEX de SALELGI", "Peaje_SGDA": "Peaje de red SGDA desde Fecha_Peaje", "Escalacion_Tarifa": "Escalación anual de la tarifa evitable", "Frac_A": "Fracción de la inyección en 08–18 h", "Frac_B": "Fracción en 18–22 h",
         "Frac_C": "Fracción en 22–08 h", "Tarifa_A": "Cargo de energía 08–22 h (bloques A y B)", "Tarifa_C": "Cargo de energía 22–08 h (bloque C)", "Asignacion_Compartida": "Rubros compartibles del sitio cargados a GPM",
         "IVA_Recuperable": "IVA del CAPEX recuperable como crédito", "Seguro_kWp": "Seguros all-risk + RC (paga SALELGI)", "Renta_Terreno_ha": "Arriendo del terreno a Exergy (si es la dueña)", "Tributos_Locales": "Tributos locales y administración",
         "Escalacion_OPEX": "Escalación anual del OPEX", "Costos_Transaccion_Terreno_Pct": "Costos de transacción de la compra", "Predial_Terreno": "Predial y gastos anuales del terreno", "Residual_Terreno_Pct": "Valor residual del terreno (% del precio)",
         "Tasa_Participacion": "Participación laboral sobre la utilidad", "Incluir_Participacion": "Incluir participación laboral (SALELGI)", "Escudo_Negativo": "Escudo fiscal de las pérdidas incrementales", "Pct_Elegible_DedAd": "% del CAPEX elegible para deducción adicional",
         "Ingresos_SALELGI": "Ingresos anuales de SALELGI (tope del 5 %)", "Tope_DedAd_Pct": "Tope de la deducción adicional (% ingresos)", "IDC_Frac_Tramo0": "IDC: fracción de año del tramo del año 0", "Costo_Gerencia_Pct": "Costo interno de Exergy por gerenciar",
         "Costo_OM_Exergy_kWp": "Costo propio de Exergy por operar el SGDA", "Fecha_COD": "Inicio de operación (COD)", "Fee_Gerencia_Pct": "Fee de gerencia del proyecto (Exergy)", "Fase_m1": "Fracción del CAPEX desembolsada en el año −1",
         "Tasa_Descuento_Equity": "Tasa de descuento del accionista (VAN equity)", "Meses_Construccion": "Meses de construcción (IDC) — de 03", "Fecha_Precios": "Fecha de los precios del CAPEX",
         "Reemplazo_Anio": "Reemplazo de inversores: año (t)", "Reemplazo_USD_Wac": "Reemplazo de inversores: costo", "Reemplazo_Pagador": "Reemplazo de inversores: quién paga",
         "Desmantelamiento_Pct": "Desmantelamiento en t = H (% del CAPEX)", "Degradacion_Adicional": "Degradación adicional sobre el yield canónico", "Peaje_kW_mes": "Peaje SGDA por potencia (desde Fecha_Peaje)",
         "Utilidad_Gravable_SALELGI": "Utilidad gravable disponible (vacío = ilimitada)", "Disponibilidad": "Disponibilidad de la planta", "Escalacion_CAPEX": "Escalación del CAPEX hasta la compra"}
W1 = {"A": 2, "B": 44, "C": 12, "D": 12, "E": 12, "F": 12, "G": 11, "H": 46, "I": 5, "J": 5, "K": 5, "L": 5, "M": 5, "N": 4}   # 163 → escala 82 % ≈ 809 pt (fit_width)
COL_CASE = {"X": 3, "C": 4, "B": 5, "F": 6}
COL_REF = {"X": 9, "C": 10, "B": 11, "F": 12}   # I..L ocultas: referencia Base del Custom · definición entregada de C/B/F
COL_NAME, COL_MARK = 13, 14


def build_supuestos(wb):
    ws = wb.create_sheet(R1)
    widths(ws, W1)
    sheet_header(ws, "Supuestos", "Lo que hay que creer para que los resultados se sostengan: tinta = editable; «· por confirmar» = sin fuente firme. El bloque B define los cuatro casos y el Custom gobierna el libro; el resto, en Inputs.", 1, total=NS, last_col=8, guide=False)
    dv_yes = DataValidation(type="list", formula1='"Sí,No"', allow_blank=False); ws.add_data_validation(dv_yes)
    dvs = {k: DataValidation(type="list", formula1=v, allow_blank=False) for k, v in SELECTORS.items()}
    for dv in dvs.values():
        ws.add_data_validation(dv)
    r = 5
    lg = ws.cell(row=r, column=2, value="Convenciones:"); lg.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO, bold=True)
    parts = [("tinta = editable", TINTA, False), ("carbón = calculado", CARBON, False), ("· por confirmar", ARCILLA, False), ("Custom", X_COL, True), ("Conservador", C_COL, True), ("Base", B_COL, True), ("Favorable", F_COL, True), ("arcilla = distinto del Base / de la definición entregada", ARCILLA, False)]
    rt = CellRichText()
    for i, (txt, colr, b) in enumerate(parts):
        if i:
            rt.append(TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=GRAFITO), "   ·   "))
        rt.append(TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=colr, b=b), txt))
    c = ws.cell(row=r, column=3, value=rt); c.alignment = Alignment(vertical="center"); ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=8); ws.row_dimensions[r].height = 16
    r = 7
    hdr(ws, r, 2, 8, ["Parámetro", "", "", "", "", "Unidad", "Fuente · nota"], height=20)
    for key, cc in COL_CASE.items():
        caso_hdr(ws, r, cc, key, size=SZ_TABLE)
    hdr_row = r
    r += 1
    first_row = r
    b_rows = []
    break_row = None
    for bname, guide, names_ in BLOQUES:
        if bname.startswith("D ·"):
            break_row = r   # V9: la página 2 empieza en el bloque D (escala fija 82 %: 614 pt + 595 pt ≤ 629 pt útiles por página)
        ws.row_dimensions[r].height = 8; r += 1
        if bname.startswith("B ·"):
            section(ws, r, 2, 8, bname)
            for key, cc in COL_CASE.items():
                t = ws.cell(row=r, column=cc, value=CASO_NOMBRE[key]); t.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=CASO_COL[key]); t.alignment = Alignment(horizontal="right", vertical="center")
            ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8)
            g = ws.cell(row=r, column=7, value="lo único que distingue a los cuatro casos; el Custom gobierna el libro"); g.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO); g.alignment = Alignment(vertical="center", indent=1)
        else:
            section(ws, r, 2, 8, bname, guide=guide, guide_col=3)
        r += 1
        for nm in names_:
            if nm in ESC:
                nm_, rng_nm, lab0, unit_txt, fmt, vals, confirm, nt = ESC[nm]
                lab = LABEL.get(nm, lab0)
                if confirm:
                    rt = CellRichText([TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=CARBON), lab), TextBlock(InlineFont(rFont=FONT, sz=SZ_NOTE, color=ARCILLA), " · por confirmar")])
                    c = ws.cell(row=r, column=2, value=rt); c.alignment = Alignment(vertical="center", wrap_text=True); c.border = B_BOTTOM
                else:
                    label(ws, r, 2, lab, size=9, wrap=True)
                for key in CASE_KEYS:
                    v = vals[key]; cc = COL_CASE[key]
                    if key == "X":
                        cell = inp(ws, r, cc, v, fmt=fmt, confirm=confirm, size=9)
                    else:
                        cell = ws.cell(row=r, column=cc, value=v); cell.font = Font(name=FONT, size=9, color=GRAFITO); cell.border = B_BOTTOM; cell.alignment = Alignment(horizontal="right", vertical="center")
                        if fmt:
                            cell.number_format = fmt
                    if nm in dvs:
                        dvs[nm].add(cell)
                    ref = ws.cell(row=r, column=COL_REF[key], value=(f'=IF(ISBLANK(E{r}),"",E{r})' if key == "X" else v)); ref.font = Font(name=FONT, size=8.5, color=GRAFITO)
                    if fmt:
                        ref.number_format = fmt
                m = ws.cell(row=r, column=COL_MARK, value=(2 if confirm else 1)); m.font = Font(name=FONT, size=8.5, color=GRAFITO)
                comment(cell, nt)
                unit(ws, r, 7, "lista ▾" if nm in SELECTORS else unit_txt)
                note(ws, r, 8, SHORT.get(nm, ""), border=True, valign="center", size=8.5)
                name(wb, nm, R1, f"$C${r}"); name(wb, rng_nm, R1, f"$C${r}:$F${r}")
                ws.cell(row=r, column=COL_NAME, value=nm).font = Font(name=FONT, size=8.5, color=GRAFITO)
                b_rows.append(r)
                ws.row_dimensions[r].height = 18
                r += 1
                continue
            if nm in CALC_ROWS:
                lab, f, u, fmt, short = CALC_ROWS[nm]
                label(ws, r, 2, lab, size=9, wrap=True)
                calc(ws, r, 3, f, fmt=fmt, size=9, color=CARBON)
                for cc in (4, 5, 6):
                    ws.cell(row=r, column=cc).border = B_BOTTOM
                unit(ws, r, 7, u); note(ws, r, 8, short, border=True, valign="center", size=8.5)
                ws.cell(row=r, column=COL_NAME, value=nm).font = Font(name=FONT, size=8.5, color=GRAFITO)
                ws.row_dimensions[r].height = 18
                r += 1
                continue
            if nm in SENS_PARAMS:
                lab, val, unit_txt, fmt = SENS_PARAMS[nm]; confirm = False; nt = "Paso del tornado (10 §B del modelo completo)."
            else:
                lab0, val, unit_txt, fmt, confirm, nt = INP[nm]
                lab = LABEL.get(nm, lab0)
                if nm == "Meses_Construccion" and isinstance(val, str):   # en el modelo es =Mes_COD_Cron (03); aquí, el valor del modelo recalculado
                    val = MODEL_VALUES.get("Meses_Construccion", 21)
                    nt = f"Valor tomado del cronograma de 03 del modelo completo (Mes_COD_Cron). {nt}"
            if confirm:
                rt = CellRichText([TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=CARBON), lab), TextBlock(InlineFont(rFont=FONT, sz=SZ_NOTE, color=ARCILLA), " · por confirmar")])
                c = ws.cell(row=r, column=2, value=rt); c.alignment = Alignment(vertical="center", wrap_text=True); c.border = B_BOTTOM
            else:
                label(ws, r, 2, lab, size=9, wrap=True)
            if isinstance(val, str) and val.startswith("="):
                cell = calc(ws, r, 3, val, fmt=fmt, size=9, color=CARBON)
            else:
                cell = inp(ws, r, 3, val, fmt=fmt, confirm=confirm, size=9)
            ref = ws.cell(row=r, column=COL_REF["X"], value=val); ref.font = Font(name=FONT, size=8.5, color=GRAFITO)
            if fmt:
                ref.number_format = fmt
            m = ws.cell(row=r, column=COL_MARK, value=(2 if confirm else 1)); m.font = Font(name=FONT, size=8.5, color=GRAFITO)
            for cc in (4, 5, 6):
                ws.cell(row=r, column=cc).border = B_BOTTOM
            if nm in YESNO or unit_txt == "Sí / No":
                dv_yes.add(cell); u_show = "lista ▾"
            elif nm in dvs:
                dvs[nm].add(cell); u_show = "lista ▾"
            else:
                u_show = {"% del valor del proyecto": "% del valor"}.get(unit_txt, unit_txt)
            comment(cell, nt)
            unit(ws, r, 7, u_show); note(ws, r, 8, SHORT.get(nm, ""), border=True, valign="center", size=8.5)
            name(wb, nm, R1, f"$C${r}")
            ws.cell(row=r, column=COL_NAME, value=nm).font = Font(name=FONT, size=8.5, color=GRAFITO)
            ws.row_dimensions[r].height = 18
            r += 1
    last_row = r - 1
    b0, b1 = min(b_rows), max(b_rows)
    ws.conditional_formatting.add(f"C{first_row}:C{last_row}", FormulaRule(formula=[f'AND($N{first_row}>0,(C{first_row}&"")<>($I{first_row}&""))'], font=Font(color=ARCILLA, bold=True)))
    for key in ("C", "B", "F"):
        cc = col(COL_CASE[key]); rc = col(COL_REF[key])
        ws.conditional_formatting.add(f"{cc}{b0}:{cc}{b1}", FormulaRule(formula=[f'({cc}{b0}&"")<>(${rc}{b0}&"")'], font=Font(color=ARCILLA, bold=True)))
    r += 1
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 8, "J · Estado del libro y derivados (no editar)")
    r += 1
    calcs = [("Entradas del Custom distintas del Base", f'=SUMPRODUCT(($N${first_row}:$N${last_row}>0)*(($C${first_row}:$C${last_row}&"")<>($I${first_row}:$I${last_row}&"")))', "0", "n.º", "N_Custom_vs_Base"),
             ("Estado del Custom", '=IF(N_Custom_vs_Base=0,"● Custom = Base","▲ Custom ≠ Base en "&N_Custom_vs_Base&" entrada(s)")', None, "", "Estado_Custom"),
             ("Supuestos de C/B/F distintos de la definición entregada", f'=SUMPRODUCT(($N${b0}:$N${b1}>0)*((($D${b0}:$D${b1}&"")<>($J${b0}:$J${b1}&""))+(($E${b0}:$E${b1}&"")<>($K${b0}:$K${b1}&""))+(($F${b0}:$F${b1}&"")<>($L${b0}:$L${b1}&""))))', "0", "n.º", "N_Fuera_Entregado"),
             ("Estado de los escenarios fijos", '=IF(N_Fuera_Entregado=0,"● C · B · F según la definición entregada","▲ "&N_Fuera_Entregado&" supuesto(s) de C/B/F fuera de la definición "&Version)', None, "", "Estado_Entregado"),
             ("Parámetros de la ronda 2 fuera de su valor neutro (0 = libro ≡ v2.0)", '=(Disponibilidad<>1)+(Escalacion_CAPEX<>0)+(Reemplazo_Pagador<>"No")+(Meses_Construccion<>12)+(ABS(Tasa_Descuento_Equity-Tasa_Descuento)>0.000001)+(Desmantelamiento_Pct<>0)+(Degradacion_Adicional<>0)+(Peaje_kW_mes<>0)+ISNUMBER(Utilidad_Gravable_SALELGI)', "0", "n.º", "N_Neutro"),
             ("Estado de la ronda 2 (alcance del motor)", '=IF(N_Neutro=0,"● Ronda 2 en neutro: el libro reproduce la v2.0","◇ Ronda 2: "&N_Neutro&" de 9 parámetros fuera de neutro (puente en Resultados)")', None, "", "Estado_Neutro"),
             ("Supuestos por confirmar (aquí y en la hoja Inputs)", f"=COUNTIF($N${first_row}:$N${last_row},2)+COUNTIF(Inputs_Mark,2)", "0", "n.º", "N_Por_Confirmar_Res"),
             ("Tarifa evitable efectiva (ponderada por bloques)", "=Tarifa_Evitable", FMT_KWH, "$/kWh", None),
             ("Ahorro año 1 (Custom) y reducción de la factura", '=TEXT(Ahorro_Anio1,"$#,##0")&" · "&TEXT(Reduccion_Factura,"0%")&" de la factura"', None, "", None),
             ("Art. 9 — producción anual ≤ demanda anual (Custom)", f'=IF({mo(CASE_X,"E1")}*1000<=Consumo_Anual,"● cumple ("&TEXT(Cobertura_Anual,"0%")&" de la demanda)","■ NO cumple: "&TEXT({mo(CASE_X,"NoRec")},"#,##0")&" MWh no reconocidos")', None, "", None)]
    for lab, f, fmt, u, nm in calcs:
        label(ws, r, 2, lab, size=9)
        if fmt is None:
            chip(ws, r, 3, f, kind=("custom" if nm == "Estado_Custom" else ("info" if nm == "Estado_Neutro" else "ok")), c2=6, size=9)
        else:
            calc(ws, r, 3, f, fmt=fmt, size=9, bold=(nm is not None))
            for cc in (4, 5, 6):
                ws.cell(row=r, column=cc).border = B_BOTTOM
        unit(ws, r, 7, u); ws.cell(row=r, column=8).border = B_BOTTOM
        if nm:
            name(wb, nm, R1, f"$C${r}")
        ws.row_dimensions[r].height = 16
        r += 1
    for cc in range(COL_REF["X"], COL_MARK + 1):
        ws.column_dimensions[col(cc)].hidden = True
    if break_row:
        ws.row_breaks.append(Break(id=break_row - 1))
    setup_print(ws, landscape=True, title_rows=f"{hdr_row}:{hdr_row}", scale=82, area=f"A1:H{r-1}")
    return ws


# ------------------------------------------------------------------ Costos (bottom-up a factor 1 + particiones para el Motor + los cuatro casos + OPEX)
def build_costos(wb):
    ws = wb.create_sheet(R2)
    widths(ws, {"A": 2, "B": 4, "C": 32, "D": 12, "E": 7, "F": 7, "G": 8, "H": 6, "I": 13, "J": 12, "K": 11, "L": 8, "M": 8, "N": 3})
    for cc in range(15, 15 + 5 + 3 + 12):
        ws.column_dimensions[col(cc)].width = 11
    sheet_header(ws, "Costos", "CAPEX bottom-up a factor 1 (costo real, sin IVA ni terreno) y OPEX año 1; cada caso lo multiplica por su factor o usa un $/Wp fijo (bloque B). Sin margen EPC: Exergy cobra fee.", 2, total=NS, last_col=13, guide=False)
    ws.row_dimensions[4].height = 8
    r = 5
    section(ws, r, 2, 13, "CAPEX por rubro — bottom-up a factor 1 (costo real)", guide="entradas en tinta; el capitalizable depende de Contrato_Inversion", guide_col=9)
    r += 1
    hdr(ws, r, 2, 13, ["#", "Rubro", "Costo base\n[USD]", "% comp.", "% ext.", "Arancel", "IVA", "Capitalizable\nsin IVA [USD]", "Imp. importación\n[USD]", "IVA\n[USD]", "$/Wp", "% total"], height=30)
    hdr(ws, r, 15, 19, ["Cargado GPM", "Cap. SC", "Cap. CC", "IVA SC", "IVA CC"], color=GRAFITO, height=30)
    hdr(ws, r, 20, 22, ["Driver Wp", "Driver Wac", "Driver fijo"], color=GRAFITO, height=30)
    SPL0 = 23   # W.. : particiones (CAPEX_SC, CAPEX_CC, IVA_SC, IVA_CC) × (Wp, Wac, fijo)
    hdr(ws, r, SPL0, SPL0 + 11, [f"{nm_}\n{suf}" for nm_ in ("CAPEX_SC", "CAPEX_CC", "IVA_SC", "IVA_CC") for suf in ("Wp", "Wac", "fijo")], color=GRAFITO, height=30)
    SCL = SPL0 + 12   # capitalizable a la escala vigente (factor 1): I × (wp·Escala_Wp + wac·Escala_Wac + fijo)
    hdr(ws, r, SCL, SCL, ["Cap. escala\nvigente"], color=GRAFITO, height=30)
    ws.column_dimensions[col(SCL)].width = 11
    r += 1
    r0 = r
    for i, (nm, alc, cost, comp, imp, ar, iva, src, wwp, wwac, wfx) in enumerate(RUBROS):
        label(ws, r, 2, i + 1, size=9, bold=True); label(ws, r, 3, nm, size=9)
        inp(ws, r, 4, cost, fmt=FMT_USD); inp(ws, r, 5, comp, fmt=FMT_PCT0); inp(ws, r, 6, imp, fmt=FMT_PCT0); inp(ws, r, 7, ar, fmt=FMT_PCT); inp(ws, r, 8, iva, fmt=FMT_PCT0)
        calc(ws, r, 15, f"=D{r}*(1-E{r}*(1-Asignacion_Compartida))", fmt=FMT_USD, color=GRAFITO, size=9)                       # O cargado (factor 1, escala 1)
        calc(ws, r, 16, f"=O{r}+O{r}*F{r}*FODINFA_Pct+O{r}*F{r}*(G{r}+ISD_Pct)", fmt=FMT_USD, color=GRAFITO, size=9)           # P cap SC
        calc(ws, r, 17, f"=O{r}+O{r}*F{r}*FODINFA_Pct", fmt=FMT_USD, color=GRAFITO, size=9)                                    # Q cap CC
        calc(ws, r, 18, f"=(O{r}+O{r}*F{r}*FODINFA_Pct+O{r}*F{r}*G{r})*H{r}", fmt=FMT_USD, color=GRAFITO, size=9)               # R IVA SC
        calc(ws, r, 19, f"=(O{r}+O{r}*F{r}*FODINFA_Pct)*H{r}", fmt=FMT_USD, color=GRAFITO, size=9)                              # S IVA CC
        canon(ws, r, 20, wwp, fmt=FMT_PCT0); canon(ws, r, 21, wwac, fmt=FMT_PCT0); canon(ws, r, 22, wfx, fmt=FMT_PCT0)
        for k, L in enumerate(("P", "Q", "R", "S")):
            for j, drv in enumerate(("T", "U", "V")):
                calc(ws, r, SPL0 + k * 3 + j, f"={L}{r}*{drv}{r}", fmt=FMT_USD, color=GRAFITO, size=9)
        calc(ws, r, 9, f'=IF(Contrato_Inversion="Sí",Q{r},P{r})', fmt=FMT_USD, bold=True, size=9)
        calc(ws, r, SCL, f"=I{r}*(T{r}*Escala_Wp+U{r}*Escala_Wac+V{r})", fmt=FMT_USD, color=GRAFITO, size=9)
        calc(ws, r, 10, f"=I{r}-O{r}", fmt=FMT_USD, size=9)
        calc(ws, r, 11, f'=IF(Contrato_Inversion="Sí",S{r},R{r})', fmt=FMT_USD, size=9)
        calc(ws, r, 12, f"=I{r}/(Potencia_Ref*1000)", fmt=FMT_WP, size=9)
        calc(ws, r, 13, f"=I{r}/$I${r0+12}", fmt=FMT_PCT, size=9)
        ws.row_dimensions[r].height = 16
        r += 1
    rl = r - 1
    label(ws, r, 2, 10, size=9, bold=True); label(ws, r, 3, '="Contingencia ("&TEXT(Contingencia_Pct,"0%")&" sobre rubros 1-9)"', size=9)
    calc(ws, r, 9, f"=Contingencia_Pct*SUM(I{r0}:I{rl})", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 11, f"=I{r}*Tasa_IVA*Contingencia_Frac_IVA", fmt=FMT_USD, size=9); calc(ws, r, 12, f"=I{r}/(Potencia_Ref*1000)", fmt=FMT_WP, size=9); calc(ws, r, 13, f"=I{r}/$I${r0+12}", fmt=FMT_PCT, size=9)
    calc(ws, r, 16, f"=Contingencia_Pct*SUM(P{r0}:P{rl})", fmt=FMT_USD, color=GRAFITO, size=9); calc(ws, r, 17, f"=Contingencia_Pct*SUM(Q{r0}:Q{rl})", fmt=FMT_USD, color=GRAFITO, size=9)
    calc(ws, r, 18, f"=P{r}*Tasa_IVA*Contingencia_Frac_IVA", fmt=FMT_USD, color=GRAFITO, size=9); calc(ws, r, 19, f"=Q{r}*Tasa_IVA*Contingencia_Frac_IVA", fmt=FMT_USD, color=GRAFITO, size=9)
    for k in range(4):
        for j in range(3):
            cc = SPL0 + k * 3 + j
            if k < 2:
                calc(ws, r, cc, f"=Contingencia_Pct*SUM({col(cc)}{r0}:{col(cc)}{rl})", fmt=FMT_USD, color=GRAFITO, size=9)
            else:
                calc(ws, r, cc, f"={col(SPL0 + (k - 2) * 3 + j)}{r}*Tasa_IVA*Contingencia_Frac_IVA", fmt=FMT_USD, color=GRAFITO, size=9)
    for cc in (4, 5, 6, 7, 8, 10): ws.cell(row=r, column=cc).border = B_BOTTOM
    ws.row_dimensions[r].height = 16
    rc = r; r += 1
    label(ws, r, 3, "Subtotal EPC = valor del proyecto", bold=True, size=9); calc(ws, r, 9, f"=SUM(I{r0}:I{rc})", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 11, f"=SUM(K{r0}:K{rc})", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 12, f"=I{r}/(Potencia_Ref*1000)", fmt=FMT_WP, bold=True, size=9)
    for cc in list(range(16, 20)) + list(range(SPL0, SPL0 + 12)):
        calc(ws, r, cc, f"=SUM({col(cc)}{r0}:{col(cc)}{rc})", fmt=FMT_USD, color=GRAFITO, size=9)
    total_row(ws, r, 2, 13); name(wb, "Subtotal_EPC_f1", R2, f"$I${r}"); ws.row_dimensions[r].height = 16
    rs = r; r += 1
    label(ws, r, 2, 11, size=9, bold=True); label(ws, r, 3, '="Gerencia del proyecto — Exergy (fee "&TEXT(Fee_Gerencia_Pct,"0%")&")"', size=9)
    calc(ws, r, 9, f"=Fee_Gerencia_Pct*I{rs}", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 11, f"=I{r}*Tasa_IVA", fmt=FMT_USD, size=9); calc(ws, r, 12, f"=I{r}/(Potencia_Ref*1000)", fmt=FMT_WP, size=9); calc(ws, r, 13, f"=I{r}/$I${r0+12}", fmt=FMT_PCT, size=9)
    calc(ws, r, 16, f"=Fee_Gerencia_Pct*P{rs}", fmt=FMT_USD, color=GRAFITO, size=9); calc(ws, r, 17, f"=Fee_Gerencia_Pct*Q{rs}", fmt=FMT_USD, color=GRAFITO, size=9); calc(ws, r, 18, f"=P{r}*Tasa_IVA", fmt=FMT_USD, color=GRAFITO, size=9); calc(ws, r, 19, f"=Q{r}*Tasa_IVA", fmt=FMT_USD, color=GRAFITO, size=9)
    for k in range(4):
        for j in range(3):
            cc = SPL0 + k * 3 + j
            if k < 2:
                calc(ws, r, cc, f"=Fee_Gerencia_Pct*{col(cc)}{rs}", fmt=FMT_USD, color=GRAFITO, size=9)
            else:
                calc(ws, r, cc, f"={col(SPL0 + (k - 2) * 3 + j)}{r}*Tasa_IVA", fmt=FMT_USD, color=GRAFITO, size=9)
    for cc in (4, 5, 6, 7, 8, 10): ws.cell(row=r, column=cc).border = B_BOTTOM
    ws.row_dimensions[r].height = 16
    rf = r; r += 1
    assert r == r0 + 12
    label(ws, r, 3, "TOTAL CAPEX bottom-up a factor 1 (sin IVA, sin terreno)", bold=True)
    calc(ws, r, 9, f"=I{rs}+I{rf}", fmt=FMT_USD, bold=True, color=TERRACOTA); calc(ws, r, 10, f"=SUM(J{r0}:J{rl})", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 11, f"=K{rs}+K{rf}", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 12, f"=I{r}/(Potencia_Ref*1000)", fmt=FMT_WP, bold=True, size=9); calc(ws, r, 13, "=1", fmt=FMT_PCT, size=9)
    for cc in list(range(16, 20)) + list(range(SPL0, SPL0 + 12)):
        calc(ws, r, cc, f"={col(cc)}{rs}+{col(cc)}{rf}", fmt=FMT_USD, color=GRAFITO, size=9)
    total_row(ws, r, 2, 13); ws.cell(row=r, column=9).font = Font(name=FONT, bold=True, size=10, color=TERRACOTA); ws.row_dimensions[r].height = 18
    name(wb, "CAPEX_Ref_f1", R2, f"$I${r}"); name(wb, "IVA_Ref_f1", R2, f"$K${r}")
    name(wb, "CAPEX_SC_f1", R2, f"$P${r}"); name(wb, "CAPEX_CC_f1", R2, f"$Q${r}"); name(wb, "IVA_SC_f1", R2, f"$R${r}"); name(wb, "IVA_CC_f1", R2, f"$S${r}")
    for k, nm_ in enumerate(("CAPEX_SC", "CAPEX_CC", "IVA_SC", "IVA_CC")):
        for j, suf in enumerate(("Wp", "Wac", "Fijo")):
            name(wb, f"{nm_}_{suf}", R2, f"${col(SPL0 + k * 3 + j)}${r}")
    rt = r; r += 1
    label(ws, r, 3, "% del CAPEX en obra civil a la escala vigente (vida fiscal 20 años; como 05 N12/N19)", size=9)
    calc(ws, r, 9, f"={col(SCL)}{r0+5}/(SUM({col(SCL)}{r0}:{col(SCL)}{rl})*(1+Contingencia_Pct)*(1+Fee_Gerencia_Pct))", fmt=FMT_PCT, size=9); name(wb, "Pct_CAPEX_Civil", R2, f"$I${r}"); ws.row_dimensions[r].height = 16
    r += 1
    label(ws, r, 3, "Bottom-up a la potencia y contrato vigentes (factor 1) — base del factor del Custom", size=9)
    calc(ws, r, 9, '=IF(Contrato_Inversion="Sí",Escala_Wp*CAPEX_CC_Wp+Escala_Wac*CAPEX_CC_Wac+CAPEX_CC_Fijo,Escala_Wp*CAPEX_SC_Wp+Escala_Wac*CAPEX_SC_Wac+CAPEX_SC_Fijo)', fmt=FMT_USD, size=9, bold=True)
    name(wb, "CAPEX_Base_f1", R2, f"$I${r}"); calc(ws, r, 12, f"=I{r}/(Potencia_DC*1000)", fmt=FMT_WP, size=9); ws.row_dimensions[r].height = 16
    ws.column_dimensions.group("O", col(SCL), hidden=True, outline_level=1)
    r += 1
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 13, "Composición del CAPEX — capitalizable sin IVA por rubro (factor 1)", guide="los módulos son el rubro que decide; el resto son costos locales y de conexión", guide_col=8)
    r += 1
    gr = r
    chart_hbars(ws, f"B{gr}", "Capitalizable sin IVA por rubro (USD, factor 1)", Reference(ws, min_col=3, min_row=r0, max_row=rl), Reference(ws, min_col=9, min_row=r0, max_row=rl), w=19.0, h=6.5, fmt=FMT_K, accent_idx=0)
    NCH = 14
    for k in range(gr, gr + NCH):
        ws.row_dimensions[k].height = 15
    r = gr + NCH
    ws.row_breaks.append(Break(id=r - 1))
    # ---- página 2: los cuatro casos y OPEX
    section(ws, r, 2, 13, "CAPEX de los cuatro casos (sin IVA, incl. gerencia, sin terreno) — Motor", guide="Custom primero; el IVA escala en proporción", guide_col=8)
    r += 1
    hdr(ws, r, 3, 13, ["Caso", "Total sin IVA [USD]", "$/Wp", "", "vs Base", "", "IVA [USD]", "Total con IVA [USD]", "Definición del CAPEX en el caso", "", ""], height=30)
    ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6); ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8); ws.merge_cells(start_row=r, start_column=11, end_row=r, end_column=13)
    ws.cell(row=r, column=11).alignment = Alignment(horizontal="left", vertical="center")
    r += 1
    r_cases = {}
    for key in CASE_KEYS:
        r_cases[key] = r
        mc = MOTOR_CASE_COL[key]; k = CASE_KEYS.index(key) + 1
        lc = ws.cell(row=r, column=3, value=CASO_NOMBRE[key]); lc.font = Font(name=FONT, bold=True, color=CASO_COL[key], size=9); lc.border = B_BOTTOM
        calc(ws, r, 4, f"='{RM}'!${mc}${SCAL_ROWS['K']}", fmt=FMT_USD, bold=(key == "X"), size=9)
        calc(ws, r, 5, f"=D{r}/(Potencia_DC*1000)", fmt=FMT_WP, size=9); ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6)
        calc(ws, r, 7, "", fmt=FMT_SIGNPCT, color=GRAFITO, size=9); ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8)
        calc(ws, r, 9, f"='{RM}'!${mc}${SCAL_ROWS['IVA']}", fmt=FMT_USD, size=9); calc(ws, r, 10, f"=D{r}+I{r}", fmt=FMT_USD, size=9)
        if key == "X":
            defn = '=IF(N(CAPEX_Fijo_Wp)>0,"Fijo "&TEXT(CAPEX_Fijo_Wp,"0.000")&" $/Wp","Bottom-up × "&TEXT(Factor_CAPEX,"0.00"))&" · caso de trabajo"'
        else:
            defn = f'=IF(N(INDEX(Esc_CAPEX_Fijo_Wp,{k}))>0,"Fijo "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,{k}),"0.000")&" $/Wp","Bottom-up × "&TEXT(INDEX(Esc_Factor_CAPEX,{k}),"0.00"))'
            defn += {"C": '&" · rango alto del estudio CAPEX/OPEX"', "B": '&" · costo real con gerencia Exergy"', "F": '&" · deck v4 «llave en mano» (22-jul-2026)"'}[key]
        note(ws, r, 11, defn, border=True, valign="center", c2=13, size=8.5)
        ws.row_dimensions[r].height = 24
        r += 1
    # la columna «vs Base» se calcula frente a la fila Base (D de la fila B)
    for key in CASE_KEYS:
        ws.cell(row=r_cases[key], column=7).value = f"=D{r_cases[key]}/$D${r_cases['B']}-1"
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 13, '="OPEX de SALELGI — año 1 del Custom (escala "&TEXT(Escalacion_OPEX,"0.0%")&"/año; factor OPEX × "&TEXT(Factor_OPEX,"0.00")&")"')
    r += 1
    hdr(ws, r, 3, 8, ["Línea", "USD/año", "$/kWp", "", "% total", ""], height=16)
    ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6); ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8)
    r += 1
    o0 = r
    opex_lines = [("Fee O&M todo incluido → Exergy", "=Fee_OM_kWp*Potencia_DC"), ("Seguros all-risk + RC (dueño)", "=Seguro_kWp*Potencia_DC"),
                  ('=IF(Comprador_Terreno="Exergy","Arriendo del terreno → Exergy","Predial del terreno (SALELGI propietaria)")', '=IF(Comprador_Terreno="Exergy",Renta_Terreno_ha*Hectareas,Predial_Terreno)'),
                  ("Tributos locales y administración", "=Tributos_Locales")]
    for lab, f in opex_lines:
        label(ws, r, 3, lab, size=9); calc(ws, r, 4, f, fmt=FMT_USD, size=9); calc(ws, r, 5, f"=D{r}/Potencia_DC", fmt=FMT_DEC1, size=9); ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6)
        calc(ws, r, 7, f"=D{r}/$D${o0+4}", fmt=FMT_PCT, color=GRAFITO, size=9); ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8)
        ws.row_dimensions[r].height = 16
        r += 1
    label(ws, r, 3, "Total OPEX año 1 (antes del factor del caso)", bold=True, size=9); calc(ws, r, 4, f"=SUM(D{o0}:D{r-1})", fmt=FMT_USD, bold=True, size=9); calc(ws, r, 5, f"=D{r}/Potencia_DC", fmt=FMT_DEC1, bold=True, size=9); ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6)
    calc(ws, r, 7, "=1", fmt=FMT_PCT, color=GRAFITO, size=9); ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8); total_row(ws, r, 3, 8); ws.row_dimensions[r].height = 16
    name(wb, "OPEX_Anio1", R2, f"$D${r}")
    r += 1
    label(ws, r, 3, "OPEX año 1 · Custom (× factor) · Conservador →", size=9); calc(ws, r, 4, f"='{RM}'!$B${SCAL_ROWS['OPEX1']}*Factor_OPEX", fmt=FMT_USD, size=9, bold=True); calc(ws, r, 5, f"='{RM}'!$C${SCAL_ROWS['OPEX1']}*INDEX(Esc_Factor_OPEX,2)", fmt=FMT_USD, size=9, color=C_COL); ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 16
    r += 1
    ws.row_dimensions[r].height = 8; r += 1
    callout(ws, r, 2, 13, '="IVA del CAPEX del Custom ("&TEXT(IVA_Total,"$#,##0")&") recuperable como crédito tributario por SALELGI: capital de trabajo, no costo. Impuestos de importación (arancel + FODINFA + ISD sobre la fracción importada, columna «Imp. importación») "&TEXT(J' + str(rt) + ',"$#,##0")&" a factor 1; el arancel y el ISD desaparecen con Contrato de Inversión, el FODINFA (0,5 %) se mantiene. Conciliación: el deck v4 usa 750 k$/MWp como precio comercial a un cliente externo (escenario Favorable); este libro evalúa el costo real para el grupo (costo + gerencia "&TEXT(Fee_Gerencia_Pct,"0%")&"); la diferencia es margen/riesgo EPC que aquí no existe."', height=58)
    r += 1
    setup_print(ws, landscape=True, scale=78, area=f"A1:M{r}")
    return ws


# ------------------------------------------------------------------ Resultados (dos páginas · 82 %)
def build_resultados(wb):
    ws = wb.create_sheet(R3)
    widths(ws, {"A": 2, "B": 30, "C": 10.5, "D": 10.5, "E": 10.5, "F": 10.5, "G": 10.5, "H": 10.5, "I": 10.5, "J": 24, "K": 11, "L": 11})   # 151,5 → 82 % = 752 pt
    sheet_header(ws, "Resultados", "Los cuatro casos sin y con deuda, el Custom en detalle, el negocio de Exergy, el flujo por quinquenios y el puente que explica el cambio del Base frente al libro anterior (casos: bloque B).", 3, total=NS, last_col=12, guide=False)
    ws.row_dimensions[4].height = 8
    r = 5
    section(ws, r, 2, 6, "Los cuatro casos — proyecto y accionista")
    section(ws, r, 10, 12, "Custom — sin deuda vs con deuda")
    r += 1
    hdr(ws, r, 2, 6, ["Indicador", "", "", "", ""], height=18)
    for j, key in enumerate(CASE_KEYS):
        caso_hdr(ws, r, 3 + j, key, size=SZ_TABLE)
    hdr(ws, r, 10, 12, ["Indicador", "Sin deuda", "Con deuda"], height=18)
    r += 1
    rows = [("Energía año 1 [MWh]", "E1", FMT_INT), ("CAPEX sin IVA [USD]", "K", FMT_USD), ("Ahorro año 1 [USD]", "Ahorro1", FMT_USD), ("TIR del proyecto (sin deuda)", "TIR", FMT_PCT2), ("VAN @ tasa de descuento [USD]", "VAN", FMT_USD),
            ("Payback simple desde COD [años]", "PB", FMT_YRS), ("LCOE [$/MWh]", "LCOE", FMT_DEC1), ("TIR del accionista (con deuda)", "TIR_eq", FMT_PCT2), ("VAN del accionista [USD]", "VAN_eq", FMT_USD), ("DSCR mínimo", "DSCR_min", FMT_X),
            ("Aporte de capital con deuda [USD]", "Aporte_eq", FMT_USD), ("VAN negocio Exergy [USD]", "VAN_X", FMT_USD), ("TIR consolidada del grupo", "TIR_G", FMT_PCT2)]
    sc0 = r
    for lab, key, fmt in rows:
        label(ws, r, 2, lab, size=9, bold=(key in ("TIR", "TIR_eq")))
        for j, tag in enumerate(CASE_KEYS):
            idx = CASE_ESC[tag]
            f = f"='{RM}'!${mcol(idx)}${SCAL_ROWS['K']}" if key == "K" else f"={mo(idx, key)}"
            caso_val(ws, r, 3 + j, f, fmt=fmt, bold=(tag == "X"), size=9)
        ws.row_dimensions[r].height = 16
        r += 1
    for j, key in enumerate(["E1", "K", "Ahorro1", "TIR", "VAN", "PB", "LCOE", "TIReq", "VANeq", "DSCR", "Aporte", "VANX", "TIRG"]):
        for k, tag in enumerate(CASE_KEYS):
            name(wb, f"{tag}_{key}", R3, f"${col(3+k)}${sc0+j}")
    cf_scale(ws, f"C{sc0+3}:F{sc0+3}"); cf_scale(ws, f"C{sc0+4}:F{sc0+4}", mid_num=0); cf_scale(ws, f"C{sc0+7}:F{sc0+7}")
    cf_dscr(ws, f"C{sc0+9}:F{sc0+9}")
    for k in range(4):
        c = ws.cell(row=r, column=2, value=esc_def(k + 1)); c.font = Font(name=FONT, size=8.5, bold=True, color=CASO_COL[CASE_KEYS[k]]); c.alignment = Alignment(vertical="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9); ws.row_dimensions[r].height = 14
        r += 1
    note(ws, r, 2, "Tarifa evitable, consumo, potencia, terreno y deuda iguales en los cuatro casos. Texto ladrillo: TIR bajo la tasa de descuento, VAN negativo, DSCR bajo 1,00x; arcilla: DSCR bajo el objetivo.", c2=9); fit_row(ws, r, [("x" * 190, 72, 8.5)])
    r_left = r + 1
    # Custom sin / con deuda (derecha)
    rr = 7
    for lab, ks, kc, fmt in [("TIR", "TIR", "TIR_eq", FMT_PCT2), ("VAN @ tasa de descuento", "VAN", "VAN_eq", FMT_USD), ("Aporte de capital (años −1 y 0)", None, "Aporte_eq", FMT_USD), ("DSCR mínimo / promedio", None, "DSCR_min", FMT_X), ("Payback desde COD (años)", "PB", None, FMT_YRS), ("LCOE ($/MWh)", "LCOE", None, FMT_DEC1)]:
        label(ws, rr, 10, lab, size=9, wrap=True)
        if ks:
            calc(ws, rr, 11, f"={mo(CASE_X, ks)}", fmt=fmt, size=9)
        elif lab.startswith("Aporte"):
            calc(ws, rr, 11, f"=-({mcell(CASE_X,'FCF_u',-1)}+{mcell(CASE_X,'FCF_u',0)})", fmt=FMT_USD, size=9)
        else:
            calc(ws, rr, 11, "—", align="center", color=GRAFITO, size=9)
        if kc == "DSCR_min":
            calc(ws, rr, 12, f'=TEXT({mo(CASE_X,"DSCR_min")},"0.00")&"x / "&TEXT({mo(CASE_X,"DSCR_avg")},"0.00")&"x"', size=9)
        elif kc:
            calc(ws, rr, 12, f"={mo(CASE_X, kc)}", fmt=fmt, size=9)
        else:
            calc(ws, rr, 12, "—", align="center", color=GRAFITO, size=9)
        ws.row_dimensions[rr].height = 16
        rr += 1
    label(ws, rr, 10, "Deuda total al COD / cuota anual", size=9, wrap=True); calc(ws, rr, 11, "=Deuda_Total", fmt=FMT_USD, size=9); calc(ws, rr, 12, "=Cuota", fmt=FMT_USD, size=9)
    ws.row_dimensions[rr].height = 16
    rr += 1
    chip(ws, rr, 10, f'=IF({mo(CASE_X,"DSCR_min")}<1,"■ DSCR < 1,00x con "&Plazo_Deuda&" años y "&TEXT(Pct_Apalancamiento,"0%")&" (t = "&Anio_DSCR_Min&"): ir a 10 años o deuda 50–60 %",IF({mo(CASE_X,"DSCR_min")}<DSCR_Objetivo,"▲ DSCR < "&TEXT(DSCR_Objetivo,"0.00")&"x: bajo el umbral bancario típico","● DSCR ≥ "&TEXT(DSCR_Objetivo,"0.00")&"x"))', kind="risk", size=8.5, c2=12)
    ws.cell(row=rr, column=10).alignment = Alignment(wrap_text=True, vertical="top"); ws.row_dimensions[rr].height = 40
    r = max(r_left, rr + 1)
    ws.row_dimensions[r].height = 8; r += 1
    # Exergy
    section(ws, r, 2, 12, '="Negocio Exergy (fee "&TEXT(Fee_Gerencia_Pct,"0%")&" · arriendo · O&M) — Custom"', guide="palancas: ΔVAN de Exergy neto de impuestos y su costo para SALELGI", guide_col=6)
    r += 1
    x0 = r
    for lab, nm, fmt in [("VAN Exergy @ tasa de descuento", "VAN_Exergy", FMT_USD), ("TIR Exergy", "TIR_Exergy", FMT_PCT2), ("Ingreso neto nominal 25 años", "Nominal_Exergy", FMT_USD),
                         ("Servicios Exergy / ahorro anual del cliente", "Carga_Exergy", FMT_PCT), ("TIR consolidada del grupo (SALELGI + Exergy)", "TIR_Grupo", FMT_PCT2)]:
        label(ws, r, 2, lab, size=9, bold=(nm == "VAN_Exergy")); calc(ws, r, 3, f"={nm}", fmt=fmt, bold=(nm == "VAN_Exergy"), size=9)
        ws.row_dimensions[r].height = 16
        r += 1
    rx = x0
    hdr(ws, rx, 7, 12, ["Palanca (ΔVAN Exergy, neto de imp.)", "", "bajo", "base", "alto", "costo para SALELGI"], height=30)
    ws.merge_cells(start_row=rx, start_column=7, end_row=rx, end_column=8)
    rx += 1
    ann_f = "+".join([f"(1+Escalacion_OPEX)^{t-1}/(1+Tasa_Descuento)^{t}" for t in range(1, 26)])
    for lab, vals, base_nm, mult, cost_f in [("Fee de gerencia (% del valor)", (0.05, 0.07, 0.09), "Fee_Gerencia_Pct", "Subtotal_EPC_Custom*(Fase_m1*(1+Tasa_Descuento)+(1-Fase_m1))", "Subtotal_EPC_Custom"),
                                              ("Arriendo del terreno ($/ha-año)", (3000, 5000, 7000), "Renta_Terreno_ha", f"Hectareas*({ann_f})", "Hectareas"),
                                              ("Fee de O&M ($/kWp-año)", (18, 20, 24), "Fee_OM_kWp", f"Potencia_DC*({ann_f})", "Potencia_DC")]:
        label(ws, rx, 7, lab, size=9); ws.merge_cells(start_row=rx, start_column=7, end_row=rx, end_column=8); ws.cell(row=rx, column=8).border = B_BOTTOM
        for j, v in enumerate(vals):
            calc(ws, rx, 9 + j, f"=VAN_Exergy+({v}-{base_nm})*{mult}*(1-Tasa_Efectiva_Exergy)", fmt=FMT_USD, size=9)
        calc(ws, rx, 12, f'=TEXT({vals[0]}*{cost_f}/1000,"#,##0")&"k / "&TEXT({vals[1]}*{cost_f}/1000,"#,##0")&"k / "&TEXT({vals[2]}*{cost_f}/1000,"#,##0")&"k"', size=8.5, color=GRAFITO)
        ws.row_dimensions[rx].height = 16
        rx += 1
    note(ws, rx, 7, "Palancas: fee 5/7/9 % · arriendo 3.000/5.000/7.000 $/ha (sólo si Exergy es la propietaria) · O&M 18/20/24 $/kWp (costo propio 16). ΔVAN lineal neto de impuestos de Exergy; «para SALELGI» = costo asociado (fee: pago único; resto: anual).", c2=12); fit_row(ws, rx, [("x" * 200, 78, 8.5)])
    r = max(r, rx + 1)
    ws.row_dimensions[r].height = 8; r += 1
    ws.row_breaks.append(Break(id=r - 1))
    # ---- página 2: quinquenios + gráficos
    section(ws, r, 2, 12, "Custom — flujo de caja de SALELGI por quinquenio (sin deuda)")
    r += 1
    hdr(ws, r, 2, 9, ["Concepto [USD]", "Años −1 y 0", "Años 1-5", "Años 6-10", "Años 11-15", "Años 16-20", "Años 21-25", "Total"], height=18)
    r += 1

    def s(block, t1, t2):
        return f"SUM({mblock(CASE_X, block, t1, t2)})"
    lines = [("Inversión (CAPEX + IVA neto + terreno)", lambda t1, t2: f"={s('FCF_u', t1, t2)}-{s('EBITDA', t1, t2)}+{s('Part_u', t1, t2)}+{s('IR_u', t1, t2)}" if t1 < 1 else "=0"),
             ("Ahorro por energía", lambda t1, t2: f"={s('Ahorro', t1, t2)}"),
             ("OPEX", lambda t1, t2: f"=-{s('OPEX', t1, t2)}"),
             ("Peaje SGDA", lambda t1, t2: f"=-{s('Peaje', t1, t2)}"),
             ("Impuestos incrementales (participación + IR)", lambda t1, t2: f"=-{s('Part_u', t1, t2)}-{s('IR_u', t1, t2)}"),
             ("Residual del terreno (si lo compra SALELGI)", lambda t1, t2: f"={s('Terr', t1, t2)}" if t1 >= 1 else "=0"),
             ("Flujo de caja libre", lambda t1, t2: f"={s('FCF_u', t1, t2)}"),
             ("Flujo acumulado al cierre del período", lambda t1, t2: f"={mcell(CASE_X, 'Cum_u', t2)}")]
    periods = [(-1, 0), (1, 5), (6, 10), (11, 15), (16, 20), (21, 25)]
    for i, (lab, fn) in enumerate(lines):
        label(ws, r, 2, lab, size=9, bold=(i >= 6))
        for j, (t1, t2) in enumerate(periods):
            calc(ws, r, 3 + j, fn(t1, t2), fmt=FMT_USD, size=9, bold=(i >= 6))
        if i < 7:
            calc(ws, r, 9, f"=SUM(C{r}:H{r})", fmt=FMT_USD, size=9, bold=(i >= 6))
        else:
            calc(ws, r, 9, f"=H{r}", fmt=FMT_USD, size=9, bold=True)
        if i == 6:
            total_row(ws, r, 2, 9)
        ws.row_dimensions[r].height = 16
        r += 1
    ws.row_dimensions[r].height = 8; r += 1
    gr = r
    wm = wb[RM]
    cats = Reference(wm, min_col=1, min_row=brow("FCF_u", -1), max_row=brow("FCF_u", 25))
    chart_cols(ws, f"B{gr}", "Custom · flujo de caja anual de SALELGI (barras) y acumulado (línea), miles de USD", cats,
               [dict(ref=Reference(wm, min_col=2, min_row=brow("FCF_u", -1), max_row=brow("FCF_u", 25)), name="FCF anual (sin deuda)", color=GRAFITO)],
               lines=[dict(ref=Reference(wm, min_col=2, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="acumulado", color=X_COL, width=2.25)],
               w=13.0, h=8.0, y_fmt=FMT_K, legend="b", gap=45, x_title="año t (0 = COD)", x_skip=2)
    cats2 = Reference(wm, min_col=1, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25))
    chart_lines(ws, f"G{gr}", "Flujo acumulado sin deuda · los cuatro casos (miles de USD)", cats2,
                [dict(ref=Reference(wm, min_col=2 + CASE_X, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="Custom", color=X_COL, width=2.25),
                 dict(ref=Reference(wm, min_col=2 + CASE_C, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="Conservador", color=C_COL, width=1.25),
                 dict(ref=Reference(wm, min_col=2 + CASE_B, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="Base", color=B_COL, width=1.25, dash="sysDot"),
                 dict(ref=Reference(wm, min_col=2 + CASE_F, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="Favorable", color=F_COL, width=1.25)],
                w=13.0, h=8.0, y_fmt=FMT_K, legend="b", x_title="año t (0 = COD)", x_skip=2)
    NCH = 17
    for k in range(gr, gr + NCH):
        ws.row_dimensions[k].height = 15
    r = gr + NCH
    # ---- puente v2.0 → v3.0 (V9): media página — del Base con los parámetros nuevos en neutro al Base actual, un parámetro por escalón (10 §A.3 del modelo)
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 12, "Puente v2.0 → v3.0 — por qué cambió el Base (un parámetro por escalón)", guide="del libro anterior, con los parámetros nuevos en neutro, al Base actual; el último escalón ≡ Base", guide_col=7)
    r += 1
    hdr(ws, r, 2, 12, ["Escalón", "TIR proyecto", "Δ (pp)", "VAN proyecto", "TIR accionista", "Δ (pp)", "VAN accionista", "DSCR mín", "", "VAN Exergy", "Payback · LCOE"], height=18)
    ws.merge_cells(start_row=r, start_column=9, end_row=r, end_column=10)
    r += 1
    br0 = r
    BR_ROWS = [(BR0, "Libro anterior (parámetros nuevos en neutro)"),
               (BR1, '="+ escalación del CAPEX "&TEXT(INDEX(Esc_Escalacion_CAPEX,3),"0%")&"/año desde "&TEXT(Fecha_Precios,"mmm-yyyy")'),
               (BR2, '="+ disponibilidad "&TEXT(INDEX(Esc_Disponibilidad,3),"0%")'),
               (BR3, '="+ reemplazo de inversores en t = "&Reemplazo_Anio&" ("&Reemplazo_Pagador&")"'),
               (BR4, '="+ construcción de "&Meses_Construccion&" meses (IDC)"'),
               (BR5, '="+ tasa del accionista "&TEXT(Tasa_Descuento_Equity,"0%")&" (≡ Base actual)"')]
    for k, (ci, lab) in enumerate(BR_ROWS):
        label(ws, r, 2, lab, size=9, bold=(k in (0, 5)))
        calc(ws, r, 3, f"={mo(ci,'TIR')}", fmt=FMT_PCT2, size=9, bold=(k in (0, 5)))
        calc(ws, r, 4, ("=0" if k == 0 else f'=IFERROR((C{r}-C{r-1})*100,"")'), fmt=FMT_PP, color=GRAFITO, size=9)
        calc(ws, r, 5, f"={mo(ci,'VAN')}", fmt=FMT_USD, size=9)
        calc(ws, r, 6, f"={mo(ci,'TIR_eq')}", fmt=FMT_PCT2, size=9)
        calc(ws, r, 7, ("=0" if k == 0 else f'=IFERROR((F{r}-F{r-1})*100,"")'), fmt=FMT_PP, color=GRAFITO, size=9)
        calc(ws, r, 8, f"={mo(ci,'VAN_eq')}", fmt=FMT_USD, size=9)
        calc(ws, r, 9, f"={mo(ci,'DSCR_min')}", fmt=FMT_X, size=9); ws.merge_cells(start_row=r, start_column=9, end_row=r, end_column=10); ws.cell(row=r, column=10).border = B_BOTTOM
        calc(ws, r, 11, f"={mo(ci,'VAN_X')}", fmt=FMT_USD, size=9)
        calc(ws, r, 12, f'=TEXT({mo(ci,"PB")},"0.0")&" a · "&TEXT({mo(ci,"LCOE")},"0.0")', size=9, color=GRAFITO)
        ws.row_dimensions[r].height = 16
        r += 1
    br5 = r - 1
    for cc in range(2, 13):
        ws.cell(row=br5, column=cc).border = Border(top=Side(style="thin", color=CARBON), bottom=Side(style="thin", color=CARBON))
    note(ws, r, 2, '="Lectura: la TIR del proyecto pasa de "&TEXT(C' + str(br0) + ',"0.00%")&" a "&TEXT(C' + str(br5) + ',"0.00%")&" y la del accionista de "&TEXT(F' + str(br0) + ',"0.00%")&" a "&TEXT(F' + str(br5) + ',"0.00%")&"; cada escalón enciende un parámetro con los anteriores ya activos. Con los nuevos parámetros en neutro el libro reproduce el anterior celda a celda ("&Estado_Neutro&")."', c2=12)
    fit_row(ws, r, [("x" * 260, 151, 8.5)])
    r += 1
    setup_print(ws, landscape=True, scale=82, area=f"A1:L{r}")
    return ws


# ------------------------------------------------------------------ Sensibilidad (dos páginas · 82 %)
def build_sensibilidad(wb):
    ws = wb.create_sheet(R4)
    widths(ws, {"A": 2, "B": 40, "C": 12, "D": 12, "E": 12, "F": 12, "G": 12, "H": 12, "I": 12, "J": 12, "K": 12})
    sheet_header(ws, "Sensibilidad", "Qué mueve el resultado sobre el Custom, una variable a la vez (tornado), y las dos matrices que importan al directorio: CAPEX × tarifa (TIR del proyecto) y tasa × plazo de la deuda (accionista y DSCR).", 4, total=NS, last_col=11, guide=False)
    ws.row_dimensions[4].height = 8
    r = 5
    section(ws, r, 2, 11, "Pasos de las matrices (editables)")
    r += 1
    label(ws, r, 2, "Pasos matriz CAPEX (Δ sobre el Custom)", size=9)
    for i, v in enumerate([-0.15, -0.075, 0, 0.075, 0.15]): inp(ws, r, 3 + i, v, fmt=FMT_SIGNPCT)
    for cc in range(8, 12): ws.cell(row=r, column=cc).border = B_BOTTOM
    name(wb, "Mat_CAPEX", R4, f"$C${r}:$G${r}"); ws.row_dimensions[r].height = 16
    r += 1
    label(ws, r, 2, "Pasos matriz tarifa (Δ sobre la tarifa evitable)", size=9)
    for i, v in enumerate([-0.15, -0.075, 0, 0.075, 0.15]): inp(ws, r, 3 + i, v, fmt=FMT_SIGNPCT)
    for cc in range(8, 12): ws.cell(row=r, column=cc).border = B_BOTTOM
    name(wb, "Mat_Tarifa", R4, f"$C${r}:$G${r}"); ws.row_dimensions[r].height = 16
    r += 1
    label(ws, r, 2, "Tasas de deuda a evaluar", size=9)
    for i, v in enumerate([0.075, 0.0825, 0.09, 0.10, 0.11]): inp(ws, r, 3 + i, v, fmt=FMT_PCT2)
    for cc in range(8, 12): ws.cell(row=r, column=cc).border = B_BOTTOM
    name(wb, "Sens_Tasas", R4, f"$C${r}:$G${r}"); ws.row_dimensions[r].height = 16
    r += 1
    label(ws, r, 2, "Plazos de deuda (años, incl. gracia) · apalancamientos", size=9)
    for i, v in enumerate([8, 10, 12]): inp(ws, r, 3 + i, v, fmt="0")
    name(wb, "Sens_Plazos", R4, f"$C${r}:$E${r}")
    for i, v in enumerate([0.5, 0.6, 0.7, 0.8]): inp(ws, r, 6 + i, v, fmt=FMT_PCT0)
    name(wb, "Sens_Lev", R4, f"$F${r}:$I${r}")
    for cc in range(10, 12): ws.cell(row=r, column=cc).border = B_BOTTOM
    ws.row_dimensions[r].height = 16
    r += 1
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 11, "Tornado — TIR del proyecto sin deuda", guide="una variable a la vez sobre el Custom; ordenado por amplitud esperada", guide_col=6)
    r += 1
    hdr(ws, r, 2, 9, ["Variable", "TIR bajo", "TIR alto", "Δ bajo (pp)", "Δ alto (pp)", "VAN bajo", "VAN alto", "Amplitud (pp)"], height=28)
    r += 1
    label(ws, r, 2, "Custom (referencia)", bold=True, size=9); calc(ws, r, 3, f"={mo(CASE_X,'TIR')}", fmt=FMT_PCT2, bold=True); calc(ws, r, 7, f"={mo(CASE_X,'VAN')}", fmt=FMT_USD, bold=True)
    for cc in (4, 5, 6, 8, 9): ws.cell(row=r, column=cc).border = B_BOTTOM
    ws.row_dimensions[r].height = 16
    base_r = r; r += 1; t0 = r
    for lab, lo, hi, nt in TORNADO:
        label(ws, r, 2, lab, size=9)
        calc(ws, r, 3, f"={mo(lo,'TIR')}", fmt=FMT_PCT2, size=9)
        if hi is not None:
            calc(ws, r, 4, f"={mo(hi,'TIR')}", fmt=FMT_PCT2, size=9); calc(ws, r, 8, f"={mo(hi,'VAN')}", fmt=FMT_USD, size=9)
        else:
            calc(ws, r, 4, f"=$C${base_r}", fmt=FMT_PCT2, color=GRAFITO, size=9); calc(ws, r, 8, f"=$G${base_r}", fmt=FMT_USD, color=GRAFITO, size=9)
        calc(ws, r, 5, f"=IFERROR((C{r}-$C${base_r})*100,0)", fmt=FMT_PP, size=9); calc(ws, r, 6, f"=IFERROR((D{r}-$C${base_r})*100,0)", fmt=FMT_PP, size=9)
        calc(ws, r, 7, f"={mo(lo,'VAN')}", fmt=FMT_USD, size=9); calc(ws, r, 9, f"=ABS(F{r}-E{r})", fmt="0.00", bold=True, size=9)
        ws.row_dimensions[r].height = 13   # v3.0: 14 barras · v3.1: 15 barras a 13 pt (la tabla y el gráfico comparten página)
        r += 1
    t1 = r - 1
    NT = t1 - t0 + 1
    # v3.0 (V6/V9): etiquetas cortas en N y ranking por amplitud en O:S (fuera del área de impresión); el gráfico y la portada leen el ranking
    ws.column_dimensions["N"].width = 26; ws.column_dimensions["Q"].width = 26
    c = ws.cell(row=t0 - 1, column=14, value="Etiquetas cortas (orden de la tabla) · O amplitud con desempate · P fila · Q etiqueta · R Δ bajo · S Δ alto (ranking; no editar)"); c.font = font(size=8.5, color=GRAFITO)
    amp_rng = f"$O${t0}:$O${t1}"
    for k, f in enumerate(TORNADO_SHORT):
        rr = t0 + k
        c = ws.cell(row=rr, column=14, value=f); c.font = font(size=8.5, color=GRAFITO)
        c = ws.cell(row=rr, column=15, value=f"=I{rr}+({NT}-{k})*0.000000001"); c.font = font(size=8.5, color=GRAFITO); c.number_format = "0.00"
        c = ws.cell(row=rr, column=16, value=f"=MATCH(LARGE({amp_rng},{k+1}),{amp_rng},0)"); c.font = font(size=8.5, color=GRAFITO); c.number_format = "0"
        c = ws.cell(row=rr, column=17, value=f"=INDEX($N${t0}:$N${t1},P{rr})"); c.font = font(size=8.5, color=GRAFITO)
        c = ws.cell(row=rr, column=18, value=f"=INDEX($E${t0}:$E${t1},P{rr})"); c.font = font(size=8.5, color=GRAFITO); c.number_format = FMT_PP
        c = ws.cell(row=rr, column=19, value=f"=INDEX($F${t0}:$F${t1},P{rr})"); c.font = font(size=8.5, color=GRAFITO); c.number_format = FMT_PP
    ws.row_dimensions[r].height = 6; r += 1
    gr = r
    chart_tornado(ws, f"B{gr}", "Tornado · Δ TIR del proyecto en puntos porcentuales, ordenado por amplitud (caso bajo niebla · caso alto terracota)", Reference(ws, min_col=17, min_row=t0, max_row=t1),
                  Reference(ws, min_col=18, min_row=t0, max_row=t1), Reference(ws, min_col=19, min_row=t0, max_row=t1), w=19.0, h=7.0)
    NCH = 15
    for k in range(gr, gr + NCH):
        ws.row_dimensions[k].height = 15   # 15 × 14 = 210 pt ≥ 7,0 cm (198 pt)
    r = gr + NCH
    ws.row_breaks.append(Break(id=r - 1))
    # ---- página 2: matrices
    section(ws, r, 2, 11, "Matriz TIR del proyecto: Δ CAPEX (filas) × Δ tarifa evitable (columnas)", guide="la celda con borde es el Custom (0 %, 0 %)", guide_col=7)
    r += 1
    hdr(ws, r, 2, 7, ["TIR proyecto  ·  Δ CAPEX ↓  Δ tarifa →"] + [f"=INDEX(Mat_Tarifa,{j+1})" for j in range(5)], height=18)
    for j in range(5): ws.cell(row=r, column=3 + j).number_format = FMT_SIGNPCT
    h1 = r
    r += 1; m0 = r
    for i in range(5):
        calc(ws, r, 2, f"=INDEX(Mat_CAPEX,{i+1})", fmt=FMT_SIGNPCT, bold=True, align="left", size=9)
        for j in range(5): calc(ws, r, 3 + j, f"={mo(MAT_START + i*5 + j, 'TIR')}", fmt=FMT_PCT2, size=9)
        ws.row_dimensions[r].height = 16
        r += 1
    cf_scale(ws, f"C{m0}:G{m0+4}")
    act = Border(left=Side(style="thin", color=X_COL), right=Side(style="thin", color=X_COL), top=Side(style="thin", color=X_COL), bottom=Side(style="thin", color=X_COL))
    ws.conditional_formatting.add(f"C{m0}:G{m0+4}", FormulaRule(formula=[f"AND($B{m0}=0,C${h1}=0)"], border=act, font=Font(bold=True, color=CARBON)))
    note(ws, r, 2, '="Celda central = Custom. El CAPEX fijo del Favorable ("&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4),"0.00")&" $/Wp) equivale a "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4)*Potencia_DC*1000/CAPEX_Base_f1-1,"+0%;-0%")&" de CAPEX sobre el bottom-up. Texto ladrillo: TIR bajo la tasa de descuento."', c2=11); ws.row_dimensions[r].height = 16
    r += 1
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 11, "Con deuda — TIR del accionista y DSCR mínimo: tasa (filas) × plazo (columnas)", guide="borde = tasa y plazo del Custom; ladrillo < 1,00x, arcilla < objetivo", guide_col=7)
    r += 1
    hdr(ws, r, 2, 5, ["TIR del accionista  ·  tasa ↓  plazo →"] + [f'=INDEX(Sens_Plazos,{j+1})&" años"' for j in range(3)], height=18)
    hdr(ws, r, 7, 10, ["DSCR mínimo"] + [f'=INDEX(Sens_Plazos,{j+1})&" años"' for j in range(3)], height=18)
    r += 1; e0 = r
    for i in range(5):
        calc(ws, r, 2, f"=INDEX(Sens_Tasas,{i+1})", fmt=FMT_PCT2, bold=True, align="left", size=9); calc(ws, r, 7, f"=INDEX(Sens_Tasas,{i+1})", fmt=FMT_PCT2, bold=True, align="left", size=9)
        for j in range(3):
            calc(ws, r, 3 + j, f"={mo(EQ_START + i*3 + j, 'TIR_eq')}", fmt=FMT_PCT2, size=9); calc(ws, r, 8 + j, f"={mo(EQ_START + i*3 + j, 'DSCR_min')}", fmt=FMT_X, size=9)
        ws.row_dimensions[r].height = 16
        r += 1
    cf_scale(ws, f"C{e0}:E{e0+4}")
    cf_dscr(ws, f"H{e0}:J{e0+4}")
    ws.conditional_formatting.add(f"C{e0}:E{e0+4}", FormulaRule(formula=[f"AND($B{e0}=Tasa_Deuda,INDEX(Sens_Plazos,COLUMN()-2)=Plazo_Deuda)"], border=act, font=Font(bold=True, color=CARBON)))
    ws.conditional_formatting.add(f"H{e0}:J{e0+4}", FormulaRule(formula=[f"AND($G{e0}=Tasa_Deuda,INDEX(Sens_Plazos,COLUMN()-7)=Plazo_Deuda)"], border=act, font=Font(bold=True, color=CARBON)))
    ws.row_dimensions[r].height = 8; r += 1
    hdr(ws, r, 2, 6, ["Apalancamiento (deuda / CAPEX)", "TIR accionista", "DSCR mín", "Aporte de capital\n[USD]", "VAN accionista\n[USD]"], height=30)
    r += 1
    l0 = r
    for i in range(4):
        calc(ws, r, 2, f"=INDEX(Sens_Lev,{i+1})", fmt=FMT_PCT0, bold=True, align="left", size=9)
        calc(ws, r, 3, f"={mo(LEV_START+i,'TIR_eq')}", fmt=FMT_PCT2, size=9); calc(ws, r, 4, f"={mo(LEV_START+i,'DSCR_min')}", fmt=FMT_X, size=9); calc(ws, r, 5, f"={mo(LEV_START+i,'Aporte_eq')}", fmt=FMT_USD, size=9); calc(ws, r, 6, f"={mo(LEV_START+i,'VAN_eq')}", fmt=FMT_USD, size=9)
        ws.row_dimensions[r].height = 16
        r += 1
    cf_dscr(ws, f"D{l0}:D{l0+3}")
    ws.conditional_formatting.add(f"B{l0}:F{l0+3}", FormulaRule(formula=[f"$B{l0}=Pct_Apalancamiento"], border=Border(top=Side(style="thin", color=X_COL), bottom=Side(style="thin", color=X_COL)), font=Font(bold=True, color=CARBON)))
    ws.row_dimensions[r].height = 8; r += 1
    callout(ws, r, 2, 11, f'="Lectura: CAPEX y tarifa dominan (±"&TEXT(Sens_CAPEX,"0%")&" de CAPEX ≈ ±"&TEXT(ABS({mo(T_CAPEX_UP,"TIR")}-{mo(T_CAPEX_DN,"TIR")})/2*100,"0.0")&" pp de TIR). Con "&Plazo_Deuda&" años y "&TEXT(Pct_Apalancamiento,"0%")&" el DSCR mínimo del Custom es "&TEXT(X_DSCR,"0.00")&"x; 10 años lo mejora y 12 años empeora porque las cuotas de los años 11-12 coinciden con el fin de la depreciación fiscal. Umbral bancario típico: DSCR ≥ "&TEXT(DSCR_Objetivo,"0.00")&"x."', height=32)
    r += 1
    setup_print(ws, landscape=True, scale=82, area=f"A1:K{r}")
    return ws, (t0, t1)


# ------------------------------------------------------------------ Legal, trámites y riesgos (textos de la v1.2 con cifras vivas del Custom)
def build_legal(wb):
    ws = wb.create_sheet(R5)
    widths(ws, {"A": 2, "B": 28, "C": 62, "D": 30, "E": 30})
    sheet_header(ws, "Legal, trámites y riesgos", "Lo que habilita el proyecto, lo que lo condiciona y qué puede salir mal. Investigación de decisión, no opinión legal (Informe Maestro Regulatorio 21-jul-2026 + verificaciones del 01/02-sep-2026). Detalle: 02_Legal, 03_Tramites y 11_Riesgos del modelo completo.", 5, total=NS, last_col=5, guide=False)
    ws.row_dimensions[4].height = 8
    r = 5
    section(ws, r, 2, 5, "Los 5 candados del régimen (ARCONEL-005/24 codificada)")
    r += 1
    hdr(ws, r, 2, 5, ["Candado", "Qué exige · base legal", "Estado", ""], height=16)
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=5)
    r += 1
    cand = [("1 · Régimen", "SGDA de consumidor regulado, modalidad 2a (remoto). La Regulación ARCONEL-005/24 codificada (Resol. 010/2024) permite el autoabastecimiento entre unidades de negocio de CNEL EP: planta en Manabí, medidor en El Oro. Sin reformas a sep-2026; el encaje no depende de la Ley 2026 (en litigio constitucional).", '="● Habilitado"', "ok"),
            ("2 · Energía (art. 9)", "Producción anual ≤ demanda anual del consumidor (24 meses de consumos).", f'=IF({mo(CASE_X,"E1")}*1000<=Consumo_Anual,"● "&TEXT(Cobertura_Anual,"0%")&" de la demanda","■ excede")', "ok"),
            ("3 · Comercial (art. 8 / Décima)", "Prohibido comercializar kWh: Exergy cobra gerencia, O&M y arriendo a renta fija; SALELGI es dueña (declaración juramentada).", '="● Estructura sin venta de kWh"', "ok"),
            ("4 · Físico (art. 7a)", "Potencia limitada por la capacidad del alimentador 13,8 kV (flujo inverso ≤ 60 %): riesgo binario → pre-consulta escrita de capacidad y factibilidad temprana CNEL. Manta figura entre las subestaciones al límite (CENACE, 30-jun-2026); refuerzos de 6–18 meses.", '=IF(Potencia_AC>Capacidad_Alimentador_kW,"■ La potencia AC ("&TEXT(Potencia_AC,"#,##0")&" kW) supera el marcador de "&TEXT(Capacidad_Alimentador_kW,"#,##0")&" kW","▲ Pendiente: factibilidad CNEL ("&TEXT(Potencia_AC,"#,##0")&" kW)")', "warn"),
            ("5 · Económico (Disp. Trans. Cuarta)", "Peaje de red para SGDA desde el 28-feb-2029 (005/24 DT Cuarta; RLOCE D.E. 176 art. 18 y DT 16.ª), por potencia y energía. Valor no publicado.", '="▲ Custom "&TEXT(Peaje_SGDA*100,"0.0")&" ¢/kWh · Conservador "&TEXT(INDEX(Esc_Peaje,2)*100,"0.0")&" ¢"', "warn")]
    for lab, req, f, kind in cand:
        label(ws, r, 2, lab, bold=True, size=9, valign="top", wrap=True); label(ws, r, 3, req, wrap=True, size=8.5, valign="top"); chip(ws, r, 4, f, kind=kind, c2=5)
        for cc in (4, 5): ws.cell(row=r, column=cc).border = B_BOTTOM
        ws.cell(row=r, column=4).alignment = Alignment(vertical="top", wrap_text=True)
        fit_row(ws, r, [(lab, 28, 9), (req, 62, 8.5)], min_h=16, grow=True); r += 1
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 5, "Tres hechos regulatorios que el directorio debe conocer")
    r += 1
    callout(ws, r, 2, 5, "Decreto Ejecutivo 32 (15-jun-2025; RO Supl. 62, 18-jun-2025): los clientes con tarifa AV1 (167) y AV2 (4) deben instalar generación propia en 18 meses → 18-dic-2026 (la prensa dice 15-dic); seguimiento mensual vía distribuidoras al Viceministerio (oficio MAE-VEER-2026-0255-OF); en déficit CENACE puede desconectarlos. GPM es AV1 → muy probablemente obligado. El proyecto (COD 2028) no llega al plazo: su valor es acreditar un proyecto en curso. Confirmar notificación de CNEL El Oro.", size=8.5, height=40); r += 1
    callout(ws, r, 2, 5, f'="Deducción adicional del 100 % (art. 10.7 LRTI, topada al 5 % de los ingresos): exige certificación ambiental previa a la primera declaración (RLRTI 28.6.g); el procedimiento no está publicado. Sin ella, la TIR del proyecto sería "&TEXT({mo(T_DEDAD, "TIR")},"0.0%")&" en vez de "&TEXT(X_TIR,"0.0%")&" y la del accionista "&TEXT({mo(T_DEDAD, "TIR_eq")},"0.0%")&" en vez de "&TEXT(X_TIReq,"0.0%")&" (Sensibilidad, tornado). El permiso ambiental de la planta (> 1 ≤ 10 MW) es un Registro Ambiental ante ARCONEL, no una licencia."', size=8.5, height=40); r += 1
    callout(ws, r, 2, 5, f'="Peaje de red 2029: obligación cierta (el RLOCE ordena cargos por uso o disponibilidad de la red, por potencia y energía) diferida al 28-feb-2029; metodología y valor no publicados. Orden de magnitud: 1–2 $/kW-mes sobre "&TEXT(Potencia_AC/1000,"0.0")&" MW ≈ 0,7–1,4 ¢/kWh inyectado; con "&TEXT(Sens_Peaje*100,"0.0")&" ¢/kWh la TIR del Custom cambia "&TEXT(({mo(T_PEAJE,"TIR")}-{mo(CASE_X,"TIR")})*100,"+0.0;-0.0")&" pp. Mitigante: cláusula de reapertura en los contratos Exergy–SALELGI."', size=8.5, height=40); r += 1
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 5, "Arquitectura contractual")
    r += 1
    for a, b in [("Gerencia y desarrollo", '="Exergy → SALELGI · fee "&TEXT(Fee_Gerencia_Pct,"0%")&" del valor del proyecto (hitos 30/70) · partes relacionadas: documentar comparables."'),
                 ("Suministro e instalación", "Proveedores → SALELGI (multi-contrato) · SALELGI importa o compra DDP · sin margen EPC integrado."),
                 ('="Arriendo / usufructo del terreno ("&TEXT(Hectareas,"0.0")&" ha)"', '=IF(Comprador_Terreno="Exergy","Exergy → SALELGI · "&TEXT(Renta_Terreno_ha,"#,##0")&" $/ha-año indexado · ≥ 25 años · inscribible (usufructo o derecho de superficie).","SALELGI compra el terreno ("&TEXT(Precio_Terreno_ha,"#,##0")&" $/ha + transacción); no hay arriendo.")'),
                 ("O&M", '="Exergy → SALELGI · "&TEXT(Fee_OM_kWp,"0")&" $/kWp-año fijo indexado · SLA de disponibilidad · nunca ligado a kWh."'),
                 ("Habilitación CNEL", "Pre-consulta escrita de capacidad → Factibilidad (Cat. 2, 17-22 días, vigencia 6 meses) → rubro ≤ USD 10.000 → Certificado de Habilitación (vida útil 25 años) → Contrato de Conexión + Contrato de Suministro.")]:
        label(ws, r, 2, a, bold=True, size=9, valign="top", wrap=True); label(ws, r, 3, b, wrap=True, size=8.5, valign="top"); ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        for cc in (4, 5): ws.cell(row=r, column=cc).border = B_BOTTOM
        fit_row(ws, r, [("x" * 40 if a.startswith("=") else a, 28, 9), ("x" * 140 if b.startswith("=") else b, 120, 8.5)], min_h=16, grow=True); r += 1
    ws.row_dimensions[r].height = 8; r += 1
    ws.row_breaks.append(Break(id=r - 1))
    section(ws, r, 2, 5, "Ruta crítica a COD", guide="mes 1 editable; las fechas se recalculan", guide_col=4)
    r += 1
    label(ws, r, 2, "Mes 1 del cronograma", size=9); inp(ws, r, 3, date(2026, 10, 1), fmt=FMT_DATE); name(wb, "Mes1_Cronograma", R5, f"$C${r}")
    ws.cell(row=r, column=3).alignment = Alignment(horizontal="left", vertical="center")
    for cc in (4, 5): ws.cell(row=r, column=cc).border = B_BOTTOM
    ws.row_dimensions[r].height = 16; r += 1
    hdr(ws, r, 2, 5, ["Hito", "", "Meses", "Fecha estimada"], height=16); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3); r += 1
    for hito, m1, m2 in [("Consultas previas, pre-consulta de capacidad (CNEL) y control del predio", 1, 3), ("Registro Ambiental ante ARCONEL (SUIA; licencia sólo si > 10 MW)", 3, 8), ("Factibilidad de conexión CNEL — capacidad del alimentador (binario; vigencia 6 meses)", 7, 8), ("Permisos municipales (uso de suelo, construcción, Bomberos)", 4, 11), ("Certificado de habilitación CNEL", 12, 12), ("Importación y nacionalización de equipos", 10, 14), ("Construcción y montaje", 13, 19), ("Pruebas, medidor MT, contrato de conexión → COD", 20, 21)]:
        label(ws, r, 2, hito, wrap=True, size=9, valign="center"); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        calc(ws, r, 4, f'="{m1}–{m2}"', align="center", size=9)
        calc(ws, r, 5, f'=TEXT(EDATE(Mes1_Cronograma,{m1-1}),"mmm-yy")&" → "&TEXT(EDATE(Mes1_Cronograma,{m2-1}),"mmm-yy")', align="center", size=9)
        ws.row_dimensions[r].height = 16; r += 1
    label(ws, r, 2, "COD implícito vs COD del modelo", size=9); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    chip(ws, r, 4, '=IF(ABS(EDATE(Mes1_Cronograma,21)-Fecha_COD)<=45,"● coherente ("&TEXT(Fecha_COD,"mmm-yyyy")&")","▲ revisar Fecha_COD")', kind="ok", c2=5); ws.row_dimensions[r].height = 16; r += 1
    ws.row_dimensions[r].height = 8; r += 1
    section(ws, r, 2, 5, "Riesgos principales (probabilidad × impacto)")
    r += 1
    hdr(ws, r, 2, 5, ["Riesgo", "Mitigación", "Nivel", ""], height=16); ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=5); r += 1
    for rk, mit, lvl in [("Peaje de red 2029 sin valor publicado", "Sensibilidad 0–1,5 ¢; cláusula de reapertura; seguimiento ARCONEL", "■ ALTO"),
                         ('="Alimentador sin capacidad para "&TEXT(Potencia_AC/1000,"0.0")&" MWac"', "Factibilidad temprana; plan B: refuerzo o menor potencia", "■ ALTO"),
                         ("Ambiental: «unidad de proyecto» → licencia en vez de registro (+3 meses, ≈ +70 k)", "Consulta de categorización a ARCONEL-UTA; contingencia en el modelo", "■ ALTO"),
                         ("Recaracterización de arriendo/O&M como venta de kWh", "Renta fija; revisión previa de CNEL; abogado eléctrico", "■ ALTO"),
                         ("D.E. 32: GPM sin autogeneración al 18-dic-2026", "Notificar proyecto en curso; respaldo transitorio", "■ ALTO"),
                         ("Fiscal: deducción adicional sin certificación ambiental previa (procedimiento no publicado)", "Solicitar la certificación a ARCONEL antes de la primera declaración; consulta SRI", "■ ALTO"),
                         ('="DSCR mínimo "&TEXT(X_DSCR,"0.00")&"x con "&Plazo_Deuda&" años / "&TEXT(Pct_Apalancamiento,"0%")', "Plazo 10 años y/o deuda 50–60 %; cuenta de reserva", "■ ALTO"),
                         ("CAPEX real > base (módulos +30 % desde dic-2025)", "3 cotizaciones; fijar precio de módulos; contingencia 6 %", "▲ MEDIO"),
                         ("Cambio tarifario / subsidios (déficit 2026 621,9 M$)", "Escenarios ±15 % y escalación; el alza favorece", "▲ MEDIO")]:
        label(ws, r, 2, rk, wrap=True, size=9, valign="top"); label(ws, r, 3, mit, wrap=True, size=8.5, valign="top")
        c = ws.cell(row=r, column=4, value=lvl); c.font = Font(name=FONT, size=9, bold=True, color=(LADRILLO if lvl.startswith("■") else ARCILLA)); c.alignment = Alignment(vertical="top"); c.border = B_BOTTOM
        ws.cell(row=r, column=5).border = B_BOTTOM
        fit_row(ws, r, [(rk if not rk.startswith("=") else "x" * 44, 28, 9), (mit, 62, 8.5)], min_h=16, grow=True); r += 1
    setup_print(ws, landscape=True, scale=82, area=f"A1:E{r}")
    return ws


# ------------------------------------------------------------------ Resumen (dos páginas · 82 %, retícula de 24 columnas)
def build_resumen(wb, ws_sens, tornado_rows):
    ws = wb.create_sheet(R0, 0)
    ws.sheet_view.showGridLines = False
    NCOL = 24
    for cidx in range(2, 2 + NCOL):
        ws.column_dimensions[col(cidx)].width = 6.0
    ws.column_dimensions["A"].width = 1.5
    ws.column_dimensions[col(NCOL + 2)].width = 1.5
    LC = NCOL + 1   # Y
    c = ws.cell(row=1, column=2, value='="Proyecto fotovoltaico "&TEXT(Potencia_DC/1000,"0.0")&" MWp Montecristi → Gran Piazza Machala"'); c.font = Font(name=FONT_LIGHT, size=18, color=CARBON); c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 34
    m = ws.cell(row=1, column=LC - 4, value=f"{VERSION_RES} · {FECHA_RES}"); m.font = font(size=SZ_TABLE, color=GRAFITO); m.alignment = Alignment(horizontal="right", vertical="center"); ws.merge_cells(start_row=1, start_column=LC - 4, end_row=1, end_column=LC)
    c = ws.cell(row=2, column=2, value='="SALELGI S.A. (GPM) sería dueña de un SGDA de "&TEXT(Potencia_DC/1000,"0.0")&" MWp en Montecristi para su cuenta en Machala (ARCONEL-005/24, remoto); Exergy gerencia (fee "&TEXT(Fee_Gerencia_Pct,"0%")&"), "&IF(Comprador_Terreno="Exergy","arrienda el terreno y ","")&"opera. USD nominal · "&Horizonte&" años · VAN al "&TEXT(Tasa_Descuento,"0%")&"."'); c.font = font(size=SZ_TABLE, color=GRAFITO); c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=LC); ws.row_dimensions[2].height = 26
    for cc in range(2, LC + 1): ws.cell(row=3, column=cc).border = Border(bottom=rule_soft)
    ws.row_dimensions[3].height = 6
    # la decisión (Custom)
    callout(ws, 4, 2, LC, '="La decisión: invertir "&TEXT(CAPEX_Total,"$#,##0")&" (sin IVA, incl. gerencia) para producir "&TEXT(X_E1,"#,##0")&" MWh/año que cubren el "&TEXT(Cobertura_Anual,"0%")&" del consumo de GPM y ahorran "&TEXT(Ahorro_Anio1,"$#,##0")&" en el primer año (≈ "&TEXT(Reduccion_Factura,"0%")&" de la factura eléctrica). Caso Custom: TIR "&TEXT(X_TIR,"0.0%")&" sin deuda y "&TEXT(X_TIReq,"0.0%")&" para el accionista con "&TEXT(Pct_Apalancamiento,"0%")&" de deuda; payback "&TEXT(X_PB,"0.0")&" años desde el COD. Los tres escenarios fijos (Conservador · Base · Favorable) acompañan cada cifra."', size=SZ_BODY, height=34)
    # fila 5: declaración del caso + leyenda de la tira
    rt = CellRichText([TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, b=True, color=X_COL), "CASO CUSTOM"),
                       TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=GRAFITO), "  ·  las tarjetas muestran el caso de trabajo; bajo cada una, el mismo indicador en los tres escenarios fijos:")])
    c5 = ws.cell(row=5, column=2, value=rt); c5.alignment = Alignment(vertical="center"); ws.merge_cells(start_row=5, start_column=2, end_row=5, end_column=17)
    for key_, cc_ in (("C", 18), ("B", 21), ("F", 24)):
        lc_ = ws.cell(row=5, column=cc_, value=f"{key_} = {CASO_NOMBRE[key_]}"); lc_.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=CASO_COL[key_]); lc_.alignment = Alignment(horizontal="left", vertical="center")
        ws.merge_cells(start_row=5, start_column=cc_, end_row=5, end_column=min(cc_ + 2, LC))
    ws.row_dimensions[5].height = 14
    # tarjetas 2 × 4 con tira C · B · F
    CW = 6

    def strip_f(tag, key, fmt):
        nm = f"{tag}_{key}"
        if fmt == "M":
            return f'="{tag} "&IFERROR(TEXT({nm}/1000000,"+0.0;-0.0"),"n/a")&"M"'
        if fmt == "x":
            return f'="{tag} "&IFERROR(TEXT({nm},"0.00"),"n/a")&"x"'
        return f'="{tag} "&IFERROR(TEXT({nm},"{fmt}"),"n/a")'

    def cards_row(r, cards):
        for i, (lab, f, fmt, sub, hero, strip) in enumerate(cards):
            c0 = 2 + i * CW
            kpi_card(ws, r, c0, CW, lab, f, fmt, sub, hero=hero, heights=(16, 30, 26))
            ws.cell(row=r, column=c0 + CW - 1).border = B_NONE
            if strip:
                key, sfmt = strip
                caso_strip(ws, r + 3, c0, [strip_f(tag, key, sfmt) for tag in ("C", "B", "F")], size=SZ_NOTE)
                for k_ in range(3):
                    ws.cell(row=r + 3, column=c0 + k_).alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[r + 3].height = 13
    r = 6
    cards1 = [("TIR DEL PROYECTO (SIN DEUDA)", "=X_TIR", FMT_PCT2, '="Tasa exigida "&TEXT(Tasa_Descuento,"0%")&" · con energía P90: "&IFERROR(TEXT(P90_TIR,"0.0%"),"n/a")', True, ("TIR", "0.0%")),
              ('="VAN @ "&TEXT(Tasa_Descuento,"0%")', "=X_VAN", FMT_USD_D, '="USD en el COD (t = 0) · con energía P90: "&IFERROR(TEXT(P90_VAN,"$#,##0;($#,##0)"),"n/a")', False, ("VAN", "M")),
              ("PAYBACK (AÑOS DESDE COD)", "=X_PB", FMT_YRS, '="Con energía P90: "&IFERROR(TEXT(P90_PB,"0.0"),"n/a")&" años"', False, ("PB", "0.0")),
              ("LCOE VS TARIFA EVITABLE ($/MWh)", "=X_LCOE", FMT_DEC1, '="tarifa de red "&TEXT(Tarifa_Evitable*1000,"0")&" → ahorro "&TEXT(1-X_LCOE/(Tarifa_Evitable*1000),"0%")&" por kWh"', False, ("LCOE", "0"))]
    cards_row(r, cards1)
    ws.row_dimensions[r + 4].height = 6
    r = 11
    cards2 = [("CAPEX SALELGI (SIN IVA, INCL. GERENCIA)", "=CAPEX_Total", FMT_USD_D, '=TEXT(CAPEX_Total/(Potencia_DC*1000),"0.000")&" $/Wp · IVA recuperable "&TEXT(IVA_Total,"$#,##0")', False, ("K", "0.00")),
              ("TIR DEL ACCIONISTA", "=X_TIReq", FMT_PCT2, '="deuda "&TEXT(Pct_Apalancamiento,"0%")&" a "&TEXT(Tasa_Deuda,"0.0%")&", "&Plazo_Deuda&" años · aporte "&TEXT(X_Aporte,"$#,##0")', False, ("TIReq", "0.0%")),
              ("DSCR MÍNIMO", "=X_DSCR", FMT_X, '=IF(X_DSCR<1,"■ < 1,00x en t = "&Anio_DSCR_Min&" → plazo 10 años o deuda 50–60 %",IF(X_DSCR<DSCR_Objetivo,"▲ bajo el umbral bancario "&TEXT(DSCR_Objetivo,"0.00")&"x","● ≥ "&TEXT(DSCR_Objetivo,"0.00")&"x"))', False, ("DSCR", "x")),
              ('="VAN DEL NEGOCIO EXERGY @ "&TEXT(Tasa_Descuento,"0%")', "=VAN_Exergy", FMT_USD_D, '="gerencia "&TEXT(Fee_Gerencia_Pct,"0%")&IF(Comprador_Terreno="Exergy"," + arriendo "&TEXT(Renta_Terreno_ha,"#,##0")&" $/ha","")&" + O&M "&TEXT(Fee_OM_kWp,"0")&" $/kWp · TIR grupo "&TEXT(TIR_Grupo,"0.0%")', False, ("VANX", "M"))]
    cards_row(r, cards2)
    # tira del CAPEX en $/Wp (la tarjeta muestra el total): C/B/F = K/(kWp·1000)
    for k_, tag in enumerate(("C", "B", "F")):
        ws.cell(row=r + 3, column=2 + k_).value = f'="{tag} "&TEXT({tag}_K/(Potencia_DC*1000),"0.000")'
    ws.conditional_formatting.add(f"N{r+2}", FormulaRule(formula=['LEFT(N%d,1)="■"' % (r + 2)], font=Font(color=LADRILLO, bold=True)))
    ws.conditional_formatting.add(f"N{r+2}", FormulaRule(formula=['LEFT(N%d,1)="▲"' % (r + 2)], font=Font(color=ARCILLA, bold=True)))
    ws.row_dimensions[r + 4].height = 8
    r = 16
    # gráficos
    gr = r
    wm = wb[RM]
    cats2 = Reference(wm, min_col=1, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25))
    chart_lines(ws, f"B{gr}", "Flujo acumulado de SALELGI sin deuda · los cuatro casos (millones de USD)", cats2,
                [dict(ref=Reference(wm, min_col=2 + CASE_X, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="Custom", color=X_COL, width=2.25),
                 dict(ref=Reference(wm, min_col=2 + CASE_C, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="Conservador", color=C_COL, width=1.25),
                 dict(ref=Reference(wm, min_col=2 + CASE_B, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="Base", color=B_COL, width=1.25, dash="sysDot"),
                 dict(ref=Reference(wm, min_col=2 + CASE_F, min_row=brow("Cum_u", -1), max_row=brow("Cum_u", 25)), name="Favorable", color=F_COL, width=1.25)],
                w=14.0, h=7.0, y_fmt=FMT_M, legend="b", x_title="año t (0 = COD)", x_skip=2)
    t0, t1 = tornado_rows
    t9 = t0 + min(9, t1 - t0 + 1) - 1   # v3.0: las 9 barras de mayor amplitud del ranking (Q:S de Sensibilidad), como la portada del modelo
    chart_tornado(ws, f"N{gr}", "Tornado · Δ TIR del proyecto (pp) sobre el Custom · las 9 variables de mayor amplitud", Reference(ws_sens, min_col=17, min_row=t0, max_row=t9),
                  Reference(ws_sens, min_col=18, min_row=t0, max_row=t9), Reference(ws_sens, min_col=19, min_row=t0, max_row=t9), w=14.0, h=7.0)
    NCH = 15
    for k in range(gr, gr + NCH):
        ws.row_dimensions[k].height = 15
    r = gr + NCH
    ws.row_dimensions[r].height = 8
    r += 1
    # ---- semáforo (cierra la página 1)
    section(ws, r, 2, LC, "Semáforo legal y de dimensionamiento", guide="detalle en «Legal, trámites y riesgos»", guide_col=8)
    r += 1
    sem = [("Régimen y ubicación remota", '="● habilitado (Res. ARCONEL-010/2024)"'), ("Energía (art. 9)", f'=IF({mo(CASE_X,"E1")}*1000<=Consumo_Anual,"● "&TEXT(Cobertura_Anual,"0%")&" de la demanda","■ excede la demanda anual")'), ("Comercial (sin venta de kWh)", '="● contratos a renta fija"'),
           ("Capacidad del alimentador", '=IF(Potencia_AC>Capacidad_Alimentador_kW,"■ "&TEXT(Potencia_AC,"#,##0")&" kW > marcador","▲ factibilidad CNEL pendiente ("&TEXT(Potencia_AC,"#,##0")&" kW)")'), ("Peaje de red 2029", '="▲ Custom "&TEXT(Peaje_SGDA*100,"0.0")&" ¢ · sensibilizado 0–1,5 ¢/kWh"'), ("D.E. 32 (GPM es AV1)", '="▲ acreditar proyecto en curso"')]
    s1 = r
    for k, (lab, f) in enumerate(sem):
        rr = r + k // 2
        c0 = 2 + (k % 2) * 12
        c = ws.cell(row=rr, column=c0, value=lab); c.font = font(size=SZ_TABLE, color=CARBON); c.alignment = Alignment(vertical="center"); ws.merge_cells(start_row=rr, start_column=c0, end_row=rr, end_column=c0 + 4)
        v = ws.cell(row=rr, column=c0 + 5, value=f); v.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=GRAFITO); v.alignment = Alignment(vertical="center"); ws.merge_cells(start_row=rr, start_column=c0 + 5, end_row=rr, end_column=c0 + 11)
        for cc in range(c0, c0 + 12): ws.cell(row=rr, column=cc).border = B_BOTTOM
        ws.row_dimensions[rr].height = 16
    r += 3
    for g, colr in (("●", SALVIA), ("▲", ARCILLA), ("■", LADRILLO)):
        ws.conditional_formatting.add(f"B{s1}:Y{s1+2}", FormulaRule(formula=[f'LEFT(B{s1},1)="{g}"'], font=Font(bold=True, color=colr)))
    ws.row_dimensions[r].height = 10
    ws.row_breaks.append(Break(id=r))   # página 2: los cuatro casos, lectura, consistencia
    r += 1
    # ---- los cuatro casos (página 2)
    section(ws, r, 2, LC, "Los cuatro casos (cada uno sin y con deuda)", guide="Custom = caso de trabajo (gobierna el libro) · Conservador · Base · Favorable = escenarios fijos definidos en Supuestos (bloque B)", guide_col=8)
    r += 1
    hdr(ws, r, 2, LC, ["Indicador"] + [""] * 3 + [""] * 12 + ["Definición del caso"] + [""] * 8, height=18, align="right")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    for j, key in enumerate(CASE_KEYS):
        c1 = 6 + j * 3
        caso_hdr(ws, r, c1, key, c2=c1 + 2, size=SZ_TABLE)
    ws.merge_cells(start_row=r, start_column=18, end_row=r, end_column=LC)
    ws.cell(row=r, column=18).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    r += 1
    sc_rows = [("TIR del proyecto", "TIR", FMT_PCT2), ("VAN @ tasa de descuento [USD]", "VAN", FMT_USD), ("Payback desde COD [años]", "PB", FMT_YRS), ("Ahorro año 1 [USD]", "Ahorro1", FMT_USD), ("TIR del accionista", "TIReq", FMT_PCT2), ("DSCR mínimo", "DSCR", FMT_X), ("VAN negocio Exergy [USD]", "VANX", FMT_USD)]
    defs = [esc_def(1), esc_def(2), esc_def(3), esc_def(4), "Comparten potencia, consumo, tarifa evitable, terreno y deuda; el Custom nace igual al Base.", "=Estado_Custom", "=Estado_Entregado"]
    s0 = r
    for k, (lab, key, fmt) in enumerate(sc_rows):
        label(ws, r, 2, lab, size=9, bold=(key in ("TIR", "TIReq"))); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        for j, tag in enumerate(CASE_KEYS):
            calc(ws, r, 6 + j * 3, f"={tag}_{key}", fmt=fmt, size=9, bold=(tag == "X")); ws.merge_cells(start_row=r, start_column=6 + j * 3, end_row=r, end_column=8 + j * 3)
        d = ws.cell(row=r, column=18, value=defs[k]); d.font = Font(name=FONT, size=SZ_NOTE, color=(CASO_COL[CASE_KEYS[k]] if k < 4 else GRAFITO), bold=(k < 4)); d.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
        ws.merge_cells(start_row=r, start_column=18, end_row=r, end_column=LC)
        for cc in range(2, LC + 1): ws.cell(row=r, column=cc).border = B_BOTTOM
        ws.row_dimensions[r].height = 24
        r += 1
    ws.conditional_formatting.add(f"R{s0+5}:R{s0+6}", FormulaRule(formula=[f'LEFT(R{s0+5},1)="●"'], font=Font(bold=True, color=SALVIA)))
    ws.conditional_formatting.add(f"R{s0+5}:R{s0+6}", FormulaRule(formula=[f'LEFT(R{s0+5},1)="▲"'], font=Font(bold=True, color=ARCILLA)))
    cf_scale(ws, f"F{s0}:Q{s0}"); cf_scale(ws, f"F{s0+1}:Q{s0+1}", mid_num=0); cf_scale(ws, f"F{s0+4}:Q{s0+4}"); cf_dscr(ws, f"F{s0+5}:Q{s0+5}")
    ws.row_dimensions[r].height = 10; r += 1
    section(ws, r, 2, LC, "Lectura", guide="cinco frases con cifras vivas del Custom", guide_col=8)
    r += 1
    msgs = [("Viable y con encaje legal", '="SGDA remoto entre unidades de negocio de CNEL EP, cobertura "&TEXT(Cobertura_Anual,"0%")&" del consumo; Exergy cobra servicios y arriendo, no kWh."'),
            ("Rentabilidad ajustada", f'=IF(ISNUMBER(X_TIR),IF(X_TIR>=Tasa_Descuento,"TIR Custom "&TEXT(X_TIR,"0.0%")&" supera el "&TEXT(Tasa_Descuento,"0%")&" exigido","TIR Custom "&TEXT(X_TIR,"0.0%")&" queda bajo el "&TEXT(Tasa_Descuento,"0%")&" exigido (VAN "&TEXT(X_VAN,"$#,##0;($#,##0)")&")")&" · Conservador "&TEXT(C_TIR,"0.0%")&" · Base "&TEXT(B_TIR,"0.0%")&" · Favorable "&TEXT(F_TIR,"0.0%")&". CAPEX y tarifa dominan: ±"&TEXT(Sens_CAPEX,"0%")&" de CAPEX ≈ ±"&TEXT(ABS({mo(T_CAPEX_UP,"TIR")}-{mo(T_CAPEX_DN,"TIR")})/2*100,"0.0")&" pp de TIR.","TIR no calculable.")'),
            ("Deuda", '="La deuda sube la TIR del accionista a "&TEXT(X_TIReq,"0.0%")&", pero a "&Plazo_Deuda&" años el DSCR cae a "&TEXT(X_DSCR,"0.00")&"x en t = "&Anio_DSCR_Min&": financiar a 10 años (≈ vida fiscal) o al 50–60 %."'),
            ("Dos hitos binarios", "Antes de comprometer capital: factibilidad de conexión CNEL (capacidad del alimentador) y categorización ambiental (registro vs licencia)."),
            ("Exergy", '="VAN "&TEXT(VAN_Exergy,"$#,##0")&" y "&TEXT(Nominal_Exergy,"$#,##0")&" nominales en 25 años; sus servicios toman "&TEXT(Carga_Exergy,"0%")&" del ahorro anual del cliente."')]
    for topic, txt in msgs:
        t_ = ws.cell(row=r, column=2, value=topic); t_.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=CARBON); t_.alignment = Alignment(vertical="top")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        c = ws.cell(row=r, column=6, value=txt); c.font = font(size=SZ_TABLE, color=CARBON); c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=LC)
        for cc in range(2, LC + 1): ws.cell(row=r, column=cc).border = B_BOTTOM
        ws.row_dimensions[r].height = 30
        r += 1
    ws.row_dimensions[r].height = 10; r += 1
    section(ws, r, 2, LC, "Índice y consistencia con el modelo completo")
    r += 1
    for k, (sh, desc) in enumerate([(R1, "Supuestos (editable)"), (R2, "Costos"), (R3, "Resultados"), (R4, "Sensibilidad"), (R5, "Legal, trámites y riesgos")]):
        link_cell(ws, r, 2 + k * 4, desc, f"#'{sh}'!A1", size=SZ_TABLE, align="left"); ws.merge_cells(start_row=r, start_column=2 + k * 4, end_row=r, end_column=5 + k * 4)
    ws.row_dimensions[r].height = 16; r += 1
    tests = "+".join([f"(ABS({tag}_{key}-Ref_{tag}_{key})>{tol})" for tag in CASE_KEYS for key, tol in (("TIR", "0.000001"), ("TIReq", "0.000001"), ("VAN", "1"))])
    chip(ws, r, 2, f'=IF(({tests})=0,"● Coincide con el modelo completo (TIR Custom "&TEXT(Ref_X_TIR,"0.00%")&" · Conservador "&TEXT(Ref_C_TIR,"0.00%")&" · Base "&TEXT(Ref_B_TIR,"0.00%")&" · Favorable "&TEXT(Ref_F_TIR,"0.00%")&")","▲ Los supuestos difieren del modelo completo entregado (TIR Custom "&TEXT(Ref_X_TIR,"0.00%")&" · Base "&TEXT(Ref_B_TIR,"0.00%")&") — resultados recalculados con los valores de este libro · "&Estado_Custom)', kind="ok", size=SZ_TABLE, c2=LC)
    ws.row_dimensions[r].height = 16; r += 1
    c = ws.cell(row=r, column=2, value="Documento de trabajo interno de Exergy EXG S.A.S. · cifras indicativas, no constituyen oferta ni opinión legal · Detalle en Modelo_FV_5MWp_GPM_v3.1.xlsx · Motor de cálculo (111 casos, idéntico al del modelo completo) en la hoja oculta «Motor_Sens»; entradas no editables por el directorio en la hoja oculta «Inputs» (clic derecho en una pestaña → Mostrar)."); c.font = font(size=SZ_NOTE, color=GRAFITO); c.alignment = Alignment(vertical="top", wrap_text=True); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=LC); ws.row_dimensions[r].height = 26
    ws.print_area = f"A1:{col(LC+1)}{r}"
    setup_print(ws, landscape=True, scale=82)
    ws.page_margins.top = 0.45; ws.page_margins.bottom = 0.55
    ws.sheet_properties.tabColor = CARBON
    return ws


def main():
    XH.VERSION_TAG = VERSION_RES; XH.HOME_SHEET = R0; XH.HOME_LABEL = "Resumen"; XH.META_LIVE = False
    XH.FOOTER_TEXT = f"Exergy EXG S.A.S. · Modelo FV 5 MWp Montecristi → GPM · {VERSION_RES}"
    refs = read_refs(REF_PATH)
    wb = Workbook(); wb.remove(wb.active)
    wsi = build_inputs(wb, refs)
    ws1 = build_supuestos(wb)
    ws2 = build_costos(wb)
    cases = build_cases()
    wsm = build_motor(wb, cases)
    name(wb, "Subtotal_EPC_Custom", RM, f"$B${SCAL_ROWS['Sub']}")
    for tag, idx in (("P50", CASE_P50), ("P90", CASE_P90)):   # Custom con P50 / con P90 (como 10 §A.2 del modelo)
        for key in ("TIR", "VAN", "PB", "LCOE", "TIR_eq", "VAN_eq", "DSCR_min", "Ahorro1"):
            k2 = {"TIR_eq": "TIReq", "VAN_eq": "VANeq", "DSCR_min": "DSCR"}.get(key, key)
            name(wb, f"{tag}_{k2}", RM, f"${mcol(idx)}${OUT_ROWS[key]}")
    wsm.freeze_panes = None; wsm.sheet_view.pane = None
    wsm.sheet_view.selection = [Selection(activeCell="A1", sqref="A1")]
    wsm.sheet_view.showGridLines = False
    for c in list(wsm[1]):   # sin hoja de guía en el Resumen
        if c.hyperlink is not None and "Guía" in str(c.hyperlink.location or ""):
            c.hyperlink = None; c.value = None
            c.font = Font(name=FONT, size=8.5); c.fill = __import__("openpyxl").styles.PatternFill(fill_type=None)
    for row in wsm.iter_rows():
        for c in row:
            if c.font is not None and c.font.size is not None and c.font.size < 8.5:
                f = c.font; c.font = Font(name=f.name, size=8.5, bold=f.bold, italic=f.italic, color=f.color)
    ws3 = build_resultados(wb)
    ws4, trows = build_sensibilidad(wb)
    ws5 = build_legal(wb)
    ws0 = build_resumen(wb, ws4, trows)
    order = [R0, R1, R2, R3, R4, R5, RI, RM]
    wb._sheets = [wb[n] for n in order]
    wb.active = 0
    for n in order:
        wb[n].sheet_view.zoomScale = 90
        wb[n].sheet_view.showGridLines = False
        if wb[n].sheet_view.pane is not None or len(wb[n].sheet_view.selection) > 1:
            wb[n].sheet_view.pane = None
            wb[n].sheet_view.selection = [Selection(activeCell="A1", sqref="A1")]
        wb[n].sheet_properties.tabColor = None
    wb[R0].sheet_properties.tabColor = CARBON
    wb[RI].sheet_state = "hidden"
    wb[RM].sheet_state = "hidden"
    wb.calculation.fullCalcOnLoad = True
    wb.properties.creator = "Exergy EXG S.A.S. · Claude"
    wb.properties.title = "Modelo FV 5MWp — Resumen Directorio v2.0"
    # v3.0 (V-b): ningún literal de texto > 255 caracteres
    n_split = 0
    for ws_ in wb.worksheets:
        for row in ws_.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("=") and XH.long_literals(c.value):
                    c.value = XH.split_long_literals(c.value); n_split += 1
    print(f"  literales > 255 partidos: {n_split}")
    wb.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
