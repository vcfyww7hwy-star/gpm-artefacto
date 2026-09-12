# -*- coding: utf-8 -*-
"""Hojas de contenido v3.0: casos del Motor, Legal, Trámites, Riesgos, Fuentes, Controles. (10, 01 y 00 en build_sens30 / build_supuestos30 / build_portada30.)"""
from datetime import date as _d
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule, FormulaRule
from openpyxl.chart import BarChart, LineChart, DoughnutChart, Reference
from openpyxl.chart.series import SeriesLabel, DataPoint
from openpyxl.chart.label import DataLabelList
from openpyxl.worksheet.pagebreak import Break
from xl_helpers import *
from build_core import (S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, SM, C, TS, SUB, rng, COL0, LAST_T_COL, T_MIN, T_MAX,
                        OUT_ROWS, PARAM_ROWS, SCAL_ROWS, brow, ENERGIA, CAPEX, OPEX, FISCAL, FLUJO, EXERGY, NSHEETS, VERSION, CASE_KEYS, MOTOR_CASE_COL, ESCENARIOS)

# ---- v2.0: índice de casos del Motor (99 columnas). Casos 0–3 = Custom · Conservador · Base · Favorable (bloque B de 01);
# 4–5 = Custom forzado a P50 / P90 (10 §A P50 vs P90); el resto parte del Custom (columna B) y mueve un parámetro.
CASE_X, CASE_C, CASE_B, CASE_F = 0, 1, 2, 3
CASE_BASE = CASE_X            # alias histórico: «caso base del Motor» = columna B = Custom
CASE_P50, CASE_P90 = 4, 5
CASE_ESC = {"X": CASE_X, "C": CASE_C, "B": CASE_B, "F": CASE_F}
TORN0 = 6                     # tornado: 6 CAPEX− · 7 CAPEX+ · 8 Tarifa− · 9 Tarifa+ · 10 Energía alt. · 11 OPEX+ · 12 OPEX− · 13 Peaje · 14 Esc. tarifa · 15 Participación alt. · 16 IVA alt. · 17 Contrato alt.
T_CAPEX_DN, T_CAPEX_UP, T_TAR_DN, T_TAR_UP, T_ENERGIA, T_OPEX_UP, T_OPEX_DN, T_PEAJE, T_ESC, T_PART, T_IVA, T_CONTRATO = range(TORN0, TORN0 + 12)
CASE_PISO = TORN0 + 12        # 18
MAT_START = CASE_PISO + 1     # 19–43 matriz CAPEX × tarifa
EQ_START = MAT_START + 25     # 44–58 tasa × plazo
LEV_START = EQ_START + 15     # 59–62 apalancamiento
CASE_TERR_ALT = LEV_START + 4 # 63
N_SWEEP_P, N_SWEEP_R, N_SWEEP_LEV = 4, 5, 5   # v2.0: potencia 5/6/7/8 MWp (antes 7 pasos 2–8)
SWEEP_P_START = CASE_TERR_ALT + 1             # 64–67
SWEEP_R_START = SWEEP_P_START + N_SWEEP_P     # 68–72
SWEEP_A_START = SWEEP_R_START + N_SWEEP_R     # 73–77
DM_START = SWEEP_A_START + N_SWEEP_R          # 78–92
PRECIO_STEPS = (0.6, 1.0, 1.4)
TS_START = DM_START + 3 * N_SWEEP_LEV         # 93–95
TX_START = TS_START + len(PRECIO_STEPS)       # 96–98
# v3.0 (ronda 2): tornado +5 (99–103) · v3.1 (doc 18 D-L6): +1 «Sin deducción adicional» (104) · puente v2.0 → v3.0 +6 (105–110) → 111 casos
T2_START = TX_START + len(PRECIO_STEPS)       # 99
T_DISP, T_ESCK, T_PKW, T_UG, T_REP, T_DEDAD = range(T2_START, T2_START + 6)
BR_START = T2_START + 6                       # 105
BR0, BR1, BR2, BR3, BR4, BR5 = range(BR_START, BR_START + 6)
N_CASES = BR_START + 6                        # 111


def mcol(idx):
    return col(2 + idx)


def mo(idx, key):
    return f"'{SM}'!${mcol(idx)}${OUT_ROWS[key]}"


def _dtir(idx):
    """Δ TIR (pp) del caso idx frente al Custom, como texto «+0.0;-0.0» (n/a si alguna TIR no es numérica)."""
    return f'IFERROR(TEXT(({mo(idx, "TIR")}-{mo(CASE_X, "TIR")})*100,"+0.0;-0.0"),"n/a")'


# orden del tornado por amplitud esperada (v1.0): tarifa, CAPEX, escalación, peaje, energía, OPEX, IVA, participación, contrato
TORNADO = [
    ('="Tarifa evitable ±"&TEXT(Sens_Tarifa,"0%")', T_TAR_DN, T_TAR_UP, f'="(1) La tarifa evitable domina junto con el CAPEX: ±"&TEXT(Sens_Tarifa,"0%")&" mueve la TIR "&{_dtir(T_TAR_DN)}&" / "&{_dtir(T_TAR_UP)}&" pp."'),
    ('="CAPEX ±"&TEXT(Sens_CAPEX,"0%")', T_CAPEX_DN, T_CAPEX_UP, f'="(2) El CAPEX fijo del Favorable ("&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4),"0.00")&" $/Wp, deck v4) equivale a "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4)*Potencia_DC*1000/CAPEX_Base_f1-1,"+0%;-0%")&" frente al costo real bottom-up."'),
    # r3 (R3-6, G-L2 10-1): la barra se define como Custom + Sens_EscTarifa (antes «= Sens_EscTarifa», degenerada cuando el Custom ya llevaba +2 %)
    ('="Escalación tarifa +"&TEXT(Sens_EscTarifa*100,"0")&" pp/año"', T_ESC, None, f'="(3) Escalación del Custom "&TEXT(Escalacion_Tarifa,"0%")&" → "&TEXT(Escalacion_Tarifa+Sens_EscTarifa,"0%")&"/año: cada punto adicional de escalación real de la tarifa añade ≈ "&IFERROR(TEXT(({mo(T_ESC, "TIR")}-{mo(CASE_X, "TIR")})/(Sens_EscTarifa*100)*100,"+0.0;-0.0"),"n/a")&" pp de TIR."'),
    ('="Peaje SGDA 2029 = "&TEXT(Sens_Peaje*100,"0.0")&" ¢/kWh"', T_PEAJE, None, '="(4) Orden de magnitud: "&TEXT(Sens_Peaje*100,"0.0")&" ¢/kWh sobre "&IFERROR(TEXT(P50_Ahorro1/Tarifa_Evitable/1000000,"0.0"),"n/a")&" GWh ≈ "&IFERROR(TEXT(Sens_Peaje*P50_Ahorro1/Tarifa_Evitable/1000,"#,##0"),"n/a")&" k$/año desde "&TEXT(Fecha_Peaje,"yyyy")&"."'),
    ("Energía: escenario alterno (P90 si el Custom usa P50)", T_ENERGIA, None, '="(5) P90 = 90 % de probabilidad de excedencia (energía "&IFERROR(TEXT(P90_Ahorro1/P50_Ahorro1-1,"0.0%"),"n/a")&")."'),
    ('="OPEX +"&TEXT(Sens_OPEX_Up,"0%")&" / −"&TEXT(Sens_OPEX_Dn,"0%")', T_OPEX_UP, T_OPEX_DN, "(6) Incluye fee O&M, seguros, arriendo o predial y tributos."),
    ("IVA recuperable (alterno)", T_IVA, None, '="(7) Si el IVA NO fuera recuperable, el CAPEX efectivo sube ≈ "&TEXT(IVA_Total/CAPEX_Total,"0%")&"."'),
    ("Participación laboral (alterno)", T_PART, None, f'="(8) Sin participación 15 % la TIR cambia "&{_dtir(T_PART)}&" pp (base de los libros previos)."'),
    ("Contrato de Inversión (alterno)", T_CONTRATO, None, '="(9) Ahorra ≈ "&TEXT(Aranceles_ISD/1000,"#,##0")&" k$ de arancel + ISD sobre bienes de capital."'),
    # v3.0 (ronda 2): cinco barras nuevas
    ('="Disponibilidad −"&TEXT(Sens_Disponibilidad*100,"0")&" pp"', T_DISP, None, '="(10) Disponibilidad del Custom "&TEXT(Disponibilidad,"0%")&" → "&TEXT(Disponibilidad-Sens_Disponibilidad,"0%")&": cada punto de disponibilidad mueve la energía y el ahorro en la misma proporción (garantía de O&M por confirmar)."'),
    ('="Escalación CAPEX +"&TEXT(Sens_EscCAPEX*100,"0")&" pp/año"', T_ESCK, None, '="(11) Precios del CAPEX escalados al "&TEXT(Escalacion_CAPEX+Sens_EscCAPEX,"0%")&"/año desde "&TEXT(Fecha_Precios,"mmm-yyyy")&" (Custom "&TEXT(Escalacion_CAPEX,"0%")&"): el factor de escalación pasa de "&TEXT(Factor_Escalacion,"0.000")&" a "&TEXT(\'Motor_Sens\'!$' + "{X}" + '$' + "{fEsc}" + ',"0.000")&"."'),
    ('="Peaje por potencia "&TEXT(Sens_Peaje_kW,"0.0")&" $/kW-mes"', T_PKW, None, '="(12) Art. 5.17 Res. 005/24: cargos «por potencia y energía»; "&TEXT(Sens_Peaje_kW,"0.0")&" $/kW-mes sobre "&TEXT(Potencia_AC,"#,##0")&" kWac ≈ "&TEXT(Sens_Peaje_kW*Potencia_AC*12/1000,"#,##0")&" k$/año desde "&TEXT(Fecha_Peaje,"yyyy")&" (valor no publicado)."'),
    ("Sin absorción fiscal (utilidad gravable 0, con arrastre)", T_UG, None, '="(13) Si SALELGI no tuviera utilidad gravable, las pérdidas incrementales sólo se recuperan por arrastre (art. 11 LRTI, ≤ 25 %/año): la TIR del accionista cae "&' + "{DTIREQ}" + '&" pp. Dato P3 por confirmar."'),
    ('="Reemplazo de inversores pagado por "&IF(Reemplazo_Pagador="SALELGI","Exergy","SALELGI")', T_REP, None, '="(14) Quién paga el reemplazo en t = "&Reemplazo_Anio&" ("&TEXT(Reemplazo_USD,"#,##0")&" USD): hoy "&Reemplazo_Pagador&"; el alterno mueve la TIR del proyecto "&' + "{DTIR_REP}" + '&" pp y el VAN de Exergy "&TEXT(' + "{VANX_REP}" + '-X_VANX,"+#,##0;-#,##0")&" USD."'),
    # v3.1 (doc 18 D-L6): deducción adicional condicionada a la certificación ambiental previa (RLRTI art. 28 num. 6 lit. g; Atlas P-01)
    ('=IF(Aplica_DedAd="Sí","Sin deducción adicional (sin certificación ambiental)","Con deducción adicional (certificación obtenida)")', T_DEDAD, None,
     f'="(15) Deducción adicional (art. 10.7 LRTI) condicionada a certificación ambiental previa (RLRTI 28.6.g; procedimiento no publicado, P-01): sin ella la TIR cambia "&{_dtir(T_DEDAD)}&" pp y la del accionista "&IFERROR(TEXT(({mo(T_DEDAD, "TIR_eq")}-{mo(CASE_X, "TIR_eq")})*100,"+0.0;-0.0"),"n/a")&" pp; escudo "&TEXT(MIN(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos,Tope_DedAd_Pct*Ingresos_SALELGI)*Tasa_IR,"#,##0")&" USD/año × "&Vida_Fiscal_Equipos&" años."'),
]
# placeholders de las notas del tornado (referencias al Motor por índice de caso y fila de escalar)
def _tornado_fill():
    from build_core import SCAL_ROWS as _SR
    global TORNADO
    out = []
    for lab, lo, hi, nt in TORNADO:
        nt = nt.replace("{X}", mcol(T_ESCK)).replace("{fEsc}", str(_SR["fEsc"])).replace("{DTIREQ}", f'IFERROR(TEXT(({mo(T_UG, "TIR_eq")}-{mo(CASE_X, "TIR_eq")})*100,"+0.0;-0.0"),"n/a")')
        nt = nt.replace("{DTIR_REP}", _dtir(T_REP)).replace("{VANX_REP}", mo(T_REP, "VAN_X"))
        out.append((lab, lo, hi, nt))
    TORNADO = out
_tornado_fill()


def build_cases():
    """110 casos del Motor (v3.0). Columna B = Custom (lee el bloque B de 01 y el resto de entradas); C/B/F leen su columna del bloque B con
    INDEX(Esc_*, k) (k = 2, 3, 4) y comparten TODO lo demás con el Custom (capa de diseño). Los demás casos parten del Custom ($B$fila)."""
    base = dict(fK="=Factor_CAPEX", kfix="=N(CAPEX_Fijo_Wp)", fT="=1", scen="=Eff_Scen", fO="=Eff_fO", pj="=Eff_Peaje", escT="=Eff_EscT",
                part='=IF(Incluir_Participacion="Sí",1,0)', iva='=IF(IVA_Recuperable="Sí",1,0)', cont='=IF(Contrato_Inversion="Sí",1,0)',
                deb="=1", rd="=Tasa_Deuda", lev="=Pct_Apalancamiento", plazo="=Plazo_Deuda", gr="=Gracia_Deuda",
                P="=Potencia_DC", ratio="=Ratio_DCAC", terr='=IF(Comprador_Terreno="SALELGI",1,0)', finT='=IF(Deuda_Financia_Terreno="Sí",1,0)', fPre="=1",
                # v3.0 (ronda 2): disponibilidad y escalación del CAPEX del bloque B (columna Custom); el resto, capa de diseño compartida
                disp="=Disponibilidad", dK="=Escalacion_CAPEX", pkw="=Peaje_kW_mes", rep='=IF(Reemplazo_Pagador="SALELGI",1,IF(Reemplazo_Pagador="Exergy",2,0))',
                ug="=IF(ISNUMBER(Utilidad_Gravable_SALELGI),Utilidad_Gravable_SALELGI,-1)", ncon="=Meses_Construccion", req="=Tasa_Descuento_Equity",
                dec="=Desmantelamiento_Pct", deg="=Degradacion_Adicional",
                # v3.1 (doc 18 D-L6): deducción adicional aplicable (certificación ambiental previa); compartida por los cuatro casos
                dedad='=IF(Aplica_DedAd="Sí",1,0)')
    B = {k: f"=$B${r}" for k, r in PARAM_ROWS.items()}
    R = PARAM_ROWS

    def case(name, desc, **over):
        p = dict(B); p.update(over)
        return {"name": name, "desc": desc, "params": p}

    def esc(key):
        k = CASE_KEYS.index(key) + 1
        return case(CASO_NOMBRE[key], f"Escenario fijo {CASO_NOMBRE[key]}: bloque B de 01 (columna {k}); diseño compartido con el Custom",
                    scen=f'=IF(INDEX(Esc_Energia,{k})="P50",1,2)', fK=f"=INDEX(Esc_Factor_CAPEX,{k})", kfix=f"=N(INDEX(Esc_CAPEX_Fijo_Wp,{k}))",
                    fO=f"=INDEX(Esc_Factor_OPEX,{k})", pj=f"=INDEX(Esc_Peaje,{k})", escT=f"=INDEX(Esc_EscTarifa,{k})",
                    disp=f"=INDEX(Esc_Disponibilidad,{k})", dK=f"=INDEX(Esc_Escalacion_CAPEX,{k})")
    cases = [{"name": "Custom", "desc": "Caso de trabajo: bloque B (columna Custom) + resto de entradas de 01", "params": base},
             esc("C"), esc("B"), esc("F"),
             case("Custom P50", "Custom con energía P50", scen="=1"), case("Custom P90", "Custom con energía P90", scen="=2"),
             case("CAPEX −", "CAPEX del Custom × (1−Sens_CAPEX)", fK=f"=$B${R['fK']}*(1-Sens_CAPEX)", kfix=f"=$B${R['kfix']}*(1-Sens_CAPEX)"),
             case("CAPEX +", "CAPEX del Custom × (1+Sens_CAPEX)", fK=f"=$B${R['fK']}*(1+Sens_CAPEX)", kfix=f"=$B${R['kfix']}*(1+Sens_CAPEX)"),
             case("Tarifa −", "Factor tarifa 1−Sens_Tarifa", fT="=1-Sens_Tarifa"), case("Tarifa +", "Factor tarifa 1+Sens_Tarifa", fT="=1+Sens_Tarifa"),
             case("Energía alt.", "P90 si el Custom usa P50 (y viceversa)", scen=f"=IF($B${R['scen']}=1,2,1)"),
             case("OPEX +", "Factor OPEX del Custom × (1+Sens_OPEX_Up)", fO=f"=$B${R['fO']}*(1+Sens_OPEX_Up)"), case("OPEX −", "Factor OPEX del Custom × (1−Sens_OPEX_Dn)", fO=f"=$B${R['fO']}*(1-Sens_OPEX_Dn)"),
             case("Peaje", "Peaje SGDA = Sens_Peaje", pj="=Sens_Peaje"), case("Esc. tarifa", "Escalación del Custom + Sens_EscTarifa", escT=f"=$B${R['escT']}+Sens_EscTarifa"),
             case("Participación alt.", "Participación alterna", part=f"=1-$B${R['part']}"), case("IVA alt.", "IVA recuperable alterno", iva=f"=1-$B${R['iva']}"),
             case("Contrato alt.", "Contrato de Inversión alterno", cont=f"=1-$B${R['cont']}"),
             case("PISO", "P90 + CAPEX+ + OPEX+ + peaje + IVA no recuperable", scen="=2", fK=f"=$B${R['fK']}*(1+Sens_CAPEX)", kfix=f"=$B${R['kfix']}*(1+Sens_CAPEX)", fO=f"=$B${R['fO']}*(1+Sens_OPEX_Up)", pj="=Sens_Peaje", iva="=0")]
    assert len(cases) == CASE_PISO + 1
    for i in range(5):
        for j in range(5):
            cases.append(case(f"M{i+1}{j+1}", f"CAPEX paso {i+1} × tarifa paso {j+1}", fK=f"=$B${R['fK']}*(1+INDEX(Mat_CAPEX,{i+1}))", kfix=f"=$B${R['kfix']}*(1+INDEX(Mat_CAPEX,{i+1}))", fT=f"=1+INDEX(Mat_Tarifa,{j+1})"))
    for i in range(5):
        for j in range(3):
            cases.append(case(f"E{i+1}{j+1}", f"Tasa paso {i+1} × plazo paso {j+1}", rd=f"=INDEX(Sens_Tasas,{i+1})", plazo=f"=INDEX(Sens_Plazos,{j+1})"))
    for i in range(4):
        cases.append(case(f"L{i+1}", f"Apalancamiento paso {i+1}", lev=f"=INDEX(Sens_Lev,{i+1})"))
    assert len(cases) == LEV_START + 4
    cases.append(case("Terreno alt.", "Comprador del terreno alterno (Exergy ↔ SALELGI)", terr=f"=1-$B${R['terr']}"))
    for i in range(N_SWEEP_P):
        cases.append(case(f"P{i+1}", f"Potencia paso {i+1} (ratio del Custom)", P=f"=INDEX(Sweep_P,{i+1})"))
    for i in range(N_SWEEP_R):
        cases.append(case(f"R{i+1}", f"Ratio DC/AC paso {i+1} (potencia del Custom)", ratio=f"=INDEX(Sweep_Ratio,{i+1})"))
    for i in range(N_SWEEP_R):
        cases.append(case(f"A{i+1}", f"AC fija: DC = AC_fija × ratio paso {i+1}", ratio=f"=INDEX(Sweep_Ratio,{i+1})", P=f"=Sweep_AC_Fija*INDEX(Sweep_Ratio,{i+1})"))
    for j in range(3):
        for i in range(N_SWEEP_LEV):
            cases.append(case(f"DM{j+1}{i+1}", f"Deuda máxima: plazo paso {j+1} × apalancamiento paso {i+1}", plazo=f"=INDEX(Sens_Plazos,{j+1})", lev=f"=INDEX(Sweep_Lev,{i+1})"))
    for i, fp in enumerate(PRECIO_STEPS):
        cases.append(case(f"TS{i+1}", f"SALELGI compra a precio × {fp}", terr="=1", fPre=f"={fp}"))
    for i, fp in enumerate(PRECIO_STEPS):
        cases.append(case(f"TX{i+1}", f"Exergy compra a precio × {fp}", terr="=0", fPre=f"={fp}"))
    # v3.0 (ronda 2): tornado +5 sobre el Custom
    cases.append(case("Disponibilidad −", "Disponibilidad del Custom − Sens_Disponibilidad", disp=f"=MAX(0,$B${R['disp']}-Sens_Disponibilidad)"))
    cases.append(case("Escalación CAPEX +", "Escalación del CAPEX del Custom + Sens_EscCAPEX", dK=f"=$B${R['dK']}+Sens_EscCAPEX"))
    cases.append(case("Peaje kW", "Peaje por potencia = Sens_Peaje_kW", pkw="=Sens_Peaje_kW"))
    cases.append(case("Sin absorción fiscal", "Utilidad gravable disponible 0 (pérdidas sólo por arrastre)", ug="=0"))
    cases.append(case("Reemplazo alt.", "Reemplazo pagado por el otro (SALELGI ↔ Exergy; si No → SALELGI)", rep=f"=IF($B${R['rep']}=1,2,1)"))
    # v3.1 (doc 18 D-L6): deducción adicional alterna (Sí ↔ No): sin certificación ambiental previa (RLRTI 28.6.g)
    cases.append(case("Sin deducción adicional", "Deducción adicional alterna al Custom (Sí ↔ No): sin la certificación ambiental previa del RLRTI 28.6.g", dedad=f"=1-$B${R['dedad']}"))
    # v3.0 (ronda 2): puente v2.0 → v3.0 sobre el Base (columna D): cada escalón enciende un parámetro de la ronda 2
    D = {k: f"=$D${r}" for k, r in PARAM_ROWS.items()}
    neutro = dict(disp="=1", dK="=0", rep="=0", ncon="=12", req="=Tasa_Descuento", dec="=0", deg="=0", pkw="=0", ug="=-1")

    def bridge(name, desc, **on):
        p = dict(D); p.update(neutro); p.update(on)
        return {"name": name, "desc": desc, "params": p}
    cases.append(bridge("BR0 v2.0", "Base con los parámetros de la ronda 2 en neutro (≡ definición v2.0)"))
    cases.append(bridge("BR1 + escalación", "+ escalación del CAPEX del Base", dK=D["dK"]))
    cases.append(bridge("BR2 + disponibilidad", "+ disponibilidad del Base", dK=D["dK"], disp=D["disp"]))
    cases.append(bridge("BR3 + reemplazo", "+ reemplazo de inversores (pagador de 01)", dK=D["dK"], disp=D["disp"], rep=D["rep"]))
    cases.append(bridge("BR4 + construcción", "+ meses de construcción (03)", dK=D["dK"], disp=D["disp"], rep=D["rep"], ncon=D["ncon"]))
    cases.append(bridge("BR5 ≡ Base", "+ tasa del accionista y demás parámetros de diseño (peaje kW, desmantelamiento, degradación, utilidad gravable) ≡ Base",
                        dK=D["dK"], disp=D["disp"], rep=D["rep"], ncon=D["ncon"], req=D["req"], dec=D["dec"], deg=D["deg"], pkw=D["pkw"], ug=D["ug"]))
    assert len(cases) == N_CASES, (len(cases), N_CASES)
    return cases


SENS_ANCHORS = {}   # clave de sección → celda ancla en 10_Sensibilidad (enlaces desde 01 y la Guía)
TORNADO_SHORT_COL = 21   # columna U: etiquetas cortas del tornado (orden de la tabla)
TORNADO_RANK_COLS = (22, 23, 24, 25, 26)   # v3.0 (V6): V amplitud con desempate · W fila · X etiqueta · Y Δ bajo · Z Δ alto, ordenados por amplitud (gráfico de 10 §B y portada)
PORTADA_TORNADO_N = 9    # la portada muestra las 9 barras de mayor amplitud (misma retícula que la v2.0)
TORNADO_SHORT = ['="Tarifa ±"&TEXT(Sens_Tarifa,"0%")', '="CAPEX ±"&TEXT(Sens_CAPEX,"0%")', '="Escalación tarifa +"&TEXT(Sens_EscTarifa*100,"0")&" pp/año"',
                 '="Peaje "&TEXT(Sens_Peaje*100,"0.0")&" ¢/kWh"', '=IF(Eff_Scen=1,"Energía P90","Energía P50")', '="OPEX +"&TEXT(Sens_OPEX_Up,"0%")&" / −"&TEXT(Sens_OPEX_Dn,"0%")',
                 '=IF(IVA_Recuperable="Sí","IVA no recuperable","IVA recuperable")', '=IF(Incluir_Participacion="Sí","Sin participación","Con participación")',
                 '=IF(Contrato_Inversion="Sí","Sin Contrato de Inversión","Con Contrato de Inversión")',
                 '="Disponibilidad −"&TEXT(Sens_Disponibilidad*100,"0")&" pp"', '="Escalación CAPEX +"&TEXT(Sens_EscCAPEX*100,"0")&" pp/año"',
                 '="Peaje "&TEXT(Sens_Peaje_kW,"0.0")&" $/kW-mes"', "Sin absorción fiscal", '="Reemplazo paga "&IF(Reemplazo_Pagador="SALELGI","Exergy","SALELGI")',
                 '=IF(Aplica_DedAd="Sí","Sin deducción adicional","Con deducción adicional")']


def cf_text(ws, ref, low, mid=None):
    """Mapa de calor «color en el texto» (D2): bajo `low` → ladrillo; entre `low` y `mid` → arcilla; resto carbón. low/mid: expresiones Excel."""
    ws.conditional_formatting.add(ref, CellIsRule(operator="lessThan", formula=[str(low)], font=Font(color=LADRILLO, bold=True)))
    if mid is not None:
        ws.conditional_formatting.add(ref, CellIsRule(operator="between", formula=[str(low), str(mid)], font=Font(color=ARCILLA, bold=True)))


def cf_scale(ws, ref, mid_num=None):
    """TIR → ladrillo bajo la tasa de descuento; VAN → ladrillo bajo 0 (D2: un solo umbral, sin banda intermedia)."""
    if mid_num is None:
        cf_text(ws, ref, "Tasa_Descuento")
    else:
        cf_text(ws, ref, mid_num)


# build_sensibilidad (v1.1) eliminado en v2.0: 10_Sensibilidad se construye en build_sens20.py


LEGAL_ROWS = [
    ("Régimen habilitante", "Regulación ARCONEL-005/24 codificada (Resol. ARCONEL-010/2024, 27-oct-2024; RO 689, 22-nov-2024 ⚠ fuente secundaria)", "Marco normativo de la GD para autoabastecimiento de consumidores regulados. Cadena 003/18 → 001/21 → 008/23 → 005/24: deroga la ARCERNNR-008/23 (techo 2 MW); la 002/21 (empresas generadoras en GD) fue derogada por la ARCONEL-006/24 (Resol. 011/2024, 27-oct-2024). Sin reformas hasta la Resol. ARCONEL-008/26 (02-sep-2026).", "El SGDA de GPM se habilita ante CNEL EP (distribuidora), sin título ministerial. No citar 002/21 ni 008/23.", "Vigente · Atlas N7bis/N6 · verificada 08-sep-2026", "Alta"),
    ("Modalidad", "Art. 10.3 — modalidad 2a (individual remoto)", "«El SGDA está ubicado remotamente, y está asociado a una sola cuenta contrato del Consumidor Regulado.»", "Planta en Montecristi ↔ cuenta contrato 201013346360 (SALELGI, Machala).", "Vigente · verbatim (Auditoría Fases 1–2, 07-sep-2026)", "Alta"),
    ("Ubicación remota entre unidades de negocio", "Art. 6 lit. c) + nota 1 (codificada)", "«Encontrarse ubicado dentro de la misma Área de Servicio de la Distribuidora en la que se encuentran sus consumidores» — nota 1: «O entre unidades de negocio de CNEL EP.» La nota 1 ya existía en la versión original (Resol. 008/2024); la codificación (Resol. 010/2024) eliminó el lit. d) que exigía la misma unidad de negocio.", "Montecristi (U.N. Manabí) → Machala (U.N. El Oro) PERMITIDO: ambas son CNEL EP. Duda operativa abierta (sin fuente): qué U.N. tramita y cómo se liquida el crédito → consulta escrita a CNEL EP antes de la factibilidad.", "Vigente · Auditoría D-05 · Atlas · 08-sep-2026", "Alta"),
    ("Potencia", "Art. 7 lit. a)", "«Si hay inyección… la Potencia Nominal de un SGDA estará limitada a la capacidad de la red en el punto de conexión aprobada por la Distribuidora.» Sin techo de MW en el articulado («2 MW» solo topa el rubro).", '="La capacidad del alimentador de Montecristi para "&TEXT(Potencia_AC,"#,##0")&" kWac en 13,8 kV (flujo inverso ≤ 60 % nominal, manual CNEL) es el riesgo binario. Evidencia: CENACE sitúa Manta entre las subestaciones al límite (Expreso, 30-jun-2026); refuerzos de 6–18 meses (Expreso, 20-ago-2026) → pre-consulta escrita de capacidad (RC-00) y factibilidad (RC-09)."', "Vigente · verbatim (S5) · evidencia de red: prensa (M)", "Alta / Media (red)"),
    ("Energía", "Art. 9", "«La producción anual de energía del SGDA deberá ser igual o menor que la demanda de energía anual de los Consumidores Regulados» (24 meses de consumos para consumidores existentes).", f'="Año 1 (P50): "&TEXT(\'{S4}\'!${C(1)}${ENERGIA["p50"]},"#,##0")&" MWh ≤ "&TEXT(Consumo_Anual/1000,"#,##0")&" MWh de demanda ("&TEXT(\'{S4}\'!${C(1)}${ENERGIA["p50"]}/(Consumo_Anual/1000),"0%")&") — margen amplio; potencia máxima teórica ≈ "&TEXT(Consumo_Anual/Yield_Ref/F_Recorte/1000,"0.0")&" MWp."', "Vigente · verificado · cifras en fórmula (v3.1)", "Alta"),
    ("Titularidad y rol de Exergy", "Art. 8 lit. a) y b) 005/24 · art. innumerado tras el art. 44 LOSPEE (texto de la Ley 2026, art. 23; antes LOCE 2024)", "El consumidor puede ser propietario (declaración juramentada) aunque un tercero financie; puede contratar a terceros «para el financiamiento, gestión, operación, vigilancia, instalación, mantenimiento y desmantelamiento». LOSPEE (Ley 2026, art. 23): «Los consumidores regulados y no regulados podrán instalar sistemas de generación exclusivamente para su autoabastecimiento, conectados a la red de distribución o transmisión…» — mantiene la propiedad de terceros, la tercerización y el principio de exclusividad de comercialización. «El instrumento legal… no podrá establecer la actividad de comercialización (compra o venta) de la energía… esto deberá ser verificado por la Distribuidora.»", "SALELGI dueña (art. 8a); Exergy = gerencia + O&M (+ arriendo del terreno si es la propietaria) a renta fija; jamás precio por kWh (revocatoria). La Ley 2026 está en litigio constitucional (14 demandas, 1 admitida, sin sentencia a jun-2026): si cayera vuelve el texto LOCE 2024, que ya habilitaba a terceros → el encaje NO depende de la Ley 2026.", "Vigente · Auditoría D-09 · Atlas N1/N3b · 08-sep-2026", "Alta"),
    ("Prohibición de venta", "Disp. General Décima", "«Bajo ninguna de las modalidades… los propietarios del SGDA (Consumidores Regulados o terceros) o el Representante Legal podrán comercializar energía eléctrica.»", "Los contratos Exergy–SALELGI se redactan como servicios/arriendo con renta fija indexable (no a kWh). Blindaje: arriendo en escritura separada; O&M por kWp-año o disponibilidad; gerencia por hitos; consulta DG 17.ª ante duda.", "Vigente · verbatim (Auditoría) · 08-sep-2026", "Alta"),
    ("Mecanismo de excedentes", "Arts. 26-27 (27.3 para tarifas con demanda horaria)", "Balance mensual: si generación > consumo → Crédito de Energía (kWh) acumulado en SEA/SEEA y debitado en meses deficitarios; «cada 24 meses el SEEA se reiniciará a cero, sin que la Distribuidora deba otorgar una compensación económica». El remanente se valora a Tm (mayor cargo) sólo en tarifa horaria (27.3); en residencial/general, a la tarifa correspondiente (27.1–27.2).", "GPM consume cada mes 755–990 MWh vs 457–612 MWh generados → nunca hay excedente mensual: toda la energía se netea el mismo mes y la bolsa de 24 meses no se usa (04_Energia). SALELGI es tarifa horaria: el excedente de bloque A en meses de bajo consumo se netea como energía equivalente (conserva valor).", "Vigente · verbatim (S2/S5) · Atlas corrección v1.1 · 08-sep-2026", "Alta"),
    ("Qué se netea y qué no", "Arts. 27.2-27.3 y 29", "Solo el cargo por energía. Se siguen pagando cargo por demanda (USD/kW × FGD), comercialización, SAPG y cargos de terceros sobre la energía facturable.", "El modelo NO asume ahorro en demanda (remoto), comercialización ni alumbrado. Tarifa evitable = 0,113 (bloques A/B) y 0,105 (bloque C) ponderados por la inyección horaria ≈ 0,1127 $/kWh. Efecto FGD (Auditoría D-11): un SGDA en sitio puede bajar la demanda media y encarecer el cargo por demanda; en la modalidad remota 2a la demanda medida de GPM no cambia → no aplica.", "Vigente · verificado · 08-sep-2026", "Alta"),
    ("Medición", "Art. 25 y 28 · Anexo F · Regulación ARCONEL-008/24 (Resol. 015/2024, 15-nov-2024; sucede a la 001/20) · calidad: ARCONEL-009/24", "Modalidades remotas: medidor en el punto de entrega del consumidor + medidor (uni/bidireccional) en el punto de conexión del SGDA, a costo del consumidor; −2 % si se mide en el secundario del transformador.", "Medición comercial en 13,8 kV (lado MT) para evitar el descuento del 2 %. Costo del medidor en CAPEX (rubro conexión).", "Vigente · arts. 25/28 verbatim (Auditoría D-14) · Atlas N17/N18 (M)", "Alta / Media (regulación de medición)"),
    ("Peaje de red", "Disp. Transitoria Cuarta 005/24 · RLOCE (D.E. 176, RO 28-feb-2024) art. 18 y DT 16.ª (arts. 5 y 24: definición de peajes — verificar en el PDF)", "RLOCE: los SGDA «pagarán cargos por el uso o disponibilidad de la red de distribución, según la regulación» de ARCONEL; peaje de distribución = «valores por potencia y energía» (005/24 art. 5.17). 005/24 DT Cuarta: los SGDA pagan peajes «desde el 28 de febrero de 2029». D.E. 176 DT 16.ª: 5 años desde su expedición (23-feb-2029); prevalece la fecha regulatoria.", "Obligación cierta, valor no publicado. Con COD 2028-H2 el peaje llega en el año 1-2 de operación → sensibilidad 0,5/1,0/1,5 ¢/kWh y 0,5–1,0 $/kW-mes (10_Sensibilidad). Cláusula de reapertura en contratos.", "Vigente · fecha Alta (Auditoría D-07) · monto no publicado", "Alta / Baja"),
    ("Trámite y costo", "Arts. 12-16 · CNEL (Cat. 2 > 100 kW)", "Factibilidad de Conexión (17-22 días; vigencia 6 meses en Cat. 2; carta a la máxima autoridad de la U.N. con proyectista registrado en el portal CNEL) → pago USD 4/kW con tope USD 10.000 (> 2 MW) → Certificado de Habilitación (≈ 18 días; vigencia = vida útil, FV 25 años) → obra según cronograma → pruebas (5 días) → medidor MT (≤ 30 días) → Contrato de Conexión (Anexo C) + Contrato de Suministro (inicia el reloj de 24 meses del SEA). > 1 MW: estudios de estabilidad. Sin garantía/póliza.", "Trámite eléctrico rápido (3-6 meses reales); incumplir el cronograma sin justificación = revocatoria (art. 16). La factibilidad vence a los 6 meses: preparar el expediente de habilitación durante la factibilidad (03, control F12).", "Vigente · Atlas hitos 7/11/14/15 · 08-sep-2026", "Alta"),
    ("Obligación de autogenerar (cliente AV1)", "Decreto Ejecutivo 32 (15-jun-2025; RO Supl. 62, 18-jun-2025) — reforma RGLOSPEE, DT 14.ª", "Clientes con tarifa AV1 (167) y AV2 (4) deben instalar generación para abastecer su demanda en 18 meses desde la vigencia del decreto → 18-dic-2026 (la prensa dice 15-dic); CENACE puede ordenar su desconexión en períodos de déficit. Seguimiento: oficio MAE-VEER-2026-0255-OF (7-jul-2026); reportes mensuales de las distribuidoras al Viceministerio desde jul-2026 (Expreso, 23-jul-2026).", '="GPM es AV1 → muy probablemente obligado (confirmar notificación de CNEL El Oro). El proyecto (COD "&TEXT(Fecha_COD,"yyyy")&") NO llega al plazo: su valor es acreditar un proyecto en curso. "&TEXT(Potencia_DC/1000,"0")&" MWp cubren ≈ "&TEXT(Cobertura_Anual,"0%")&" de la demanda; la regla de cumplimiento (total/parcial) la debe definir ARCONEL."', "Vigente · plazo: RO Supl. 62 (Atlas N12 · A) · seguimiento: prensa (M)", "Alta (plazo) / Baja (mecánica)"),
    ("Impuesto a la Renta y participación", "LRTI art. 37 · Código del Trabajo art. 97", "IR 25 %. Participación laboral 15 % sobre utilidades. Sin exoneración de IR aplicable a un SGDA de autoabastecimiento: la LOCE (2024) no la creó (Atlas I-05); el estado 2026 del art. 9.1 LRTI está por verificar.", "El ahorro eleva la utilidad de SALELGI → tasa efectiva marginal 36,25 %. Los libros previos omitían la participación.", "Vigente · Atlas F1/I-05 · art. 9.1 ❓", "Alta / ❓ (art. 9.1)"),
    ("Deducción adicional 100 % (doble depreciación)", "LRTI art. 10 num. 7 (LOCE, RO 2S 475, 11-ene-2024) · RLRTI art. 28 num. 6 lit. g (D.E. 176 art. 78)", "«…sistemas de generación distribuida para autoabastecimiento a base de energías renovables no convencionales… se deducirán con el 100 % adicional… Este gasto adicional no podrá superar un valor equivalente al 5 % de los ingresos totales.» Requisito: certificación de la Autoridad Ambiental Competente ANTES de la primera declaración que la aplique (RLRTI 28.6.g); procedimiento no publicado (Atlas P-01). La adquisición no debe ser exigida por la autoridad ambiental como condición.", f'="Aplica a SALELGI (el art. 10.7 nombra a los SGDA). Con ingresos de "&TEXT(Ingresos_SALELGI/1000000,"0.0")&" M el tope ("&TEXT(Tope_DedAd_Pct*Ingresos_SALELGI/1000,"#,##0")&" k$) "&IF(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos>Tope_DedAd_Pct*Ingresos_SALELGI,"muerde","no muerde")&". Aplica_DedAd = "&Aplica_DedAd&"; el caso alterno (10 §B) da TIR "&TEXT({mo(T_DEDAD, "TIR")},"0.00%")&" frente a "&TEXT(X_TIR,"0.00%")&". El exceso sobre el tope se pierde en el modelo (¿diferible? P-14)."', "Vigente · tope confirmado (Atlas I-02; errata v1.1 Informe F3) · certificación ❓ (P-01)", "Alta (tope) / Media (certificación)"),
    ("IVA", "LRTI art. 65 (15 %) · art. 55 num. 19 (0 % FV, LOCE) · art. 66 (crédito tributario)", "IVA 15 % general (art. 65); 0 % para «paneles solares… y accesorios para la generación solar fotovoltaica» — código Ecuapass 0719 (boletín SENAE 15-ene-2024); el alcance de «accesorios» es indefinido (inversores, estructuras, cables, transformadores). Crédito tributario si hay ventas gravadas (art. 66).", '="SALELGI factura arriendos gravados → el IVA del CAPEX ("&TEXT(IVA_Total/1000000,"0.00")&" M) es crédito recuperable (capital de trabajo), no costo. Inversores a 0 %: ZONA GRIS (Atlas P-04; decisión D-L5) → resolución anticipada de clasificación SENAE; estructura y BOS a 15 %."', "Vigente · Atlas F1/I-12/P-04 (texto del art. 65 no cotejado: M)", "Alta / Media (alcance)"),
    ("ISD y aranceles", "Ley Reformatoria para la Equidad Tributaria art. 159 · RAISD art. 17.1 · Arancel del Ecuador (COMEX; D.E. 272 y Acuerdo MPCEI-2026-0003-A) · COPCI", "ISD 5 % sobre pagos al exterior (sin crédito tributario); tarifas diferenciadas 2026 sin partidas FV. Módulos 8541.43: 0 %; inversores 8504.40 ≈ 5 %; estructuras 7308.90.90: 20 %; trafos 8504.22 ≈ 11,25 %; FODINFA 0,5 %. Exención de ISD en bienes de capital sólo con Contrato de Inversión con anexo de subpartidas (RAISD 17.1); techo de gasto tributario 2026 desconocido (2025: USD 60 MM «por única ocasión», P-02). Arancel 2026 no cotejado (P-03); COMEX 002-2025 (0 % temporal) vencida el 31-dic-2025 sin prórroga localizada.", '="≈ "&TEXT(Aranceles_ISD/1000,"#,##0")&" k$ de arancel + ISD en el caso activo (05_CAPEX). Toggle Contrato_Inversion. La reducción de −5 pts de IR NO aplica a SALELGI (no es sociedad nueva). Duda #19: ¿autoconsumo = inversión productiva? Aranceles de 05 marcados «por confirmar (P-03)»."', "Vigente · Atlas I-15/I-16/I-19/I-20 · ADV pendiente SENAE", "Media"),
    ("Partes relacionadas", "LRTI art. 4.1 / RALRTI (precios de transferencia)", "Operaciones con partes relacionadas > USD 3 M/ejercicio → Anexo OPR; > 15 M → Informe Integral. Deben pactarse a valor de mercado.", '="EPC/gerencia (≈ "&TEXT(CAPEX_Total/1000000,"0.0")&" M) y O&M"&IF(Comprador_Terreno="Exergy"," y arriendo","")&" Exergy–SALELGI: documentar comparables (fee "&TEXT(Fee_Gerencia_Pct,"0%")&IF(Comprador_Terreno="Exergy",", arriendo "&TEXT(Renta_Terreno_ha,"#,##0")&" $/ha","")&", O&M "&TEXT(Fee_OM_kWp,"0")&" $/kWp). Las retenciones 2026 (fila siguiente) son anticipos del IR de Exergy."', "Vigente · 08-sep-2026", "Media"),
    ("Retenciones en la fuente 2026 (Exergy)", "Resol. SRI NAC-DGERCGC26-00000009 (27-feb-2026; vigente desde 01-mar-2026)", "Porcentajes de retención: construcción/obra 2 % · servicios prestados por sociedades 5 % · arrendamiento de inmuebles 10 % · transferencia de bienes 2 %.", "SALELGI retiene a Exergy en cada factura (gerencia y O&M 5 %; arriendo 10 % si Exergy es la dueña del terreno): anticipos del IR de Exergy (no costo), pero adelantan caja. No afecta el flujo de SALELGI (interno).", "Vigente · Atlas F2 · 08-sep-2026", "Alta"),
    ("Ambiental", "COA + RCOA · Resol. MAATE-2025-0002-R (22-abr-2025) · Resol. ARCONEL-005/25 (RO Supl. 67, 25-jun-2025): arts. 19–22 (Registro) y 23–35 (Licencia) · A.M. 083-B (tasas)", "Autoridad Ambiental Competente del sector eléctrico = ARCONEL (Unidad Técnica Ambiental) desde may-2025, vía SUIA. FV > 1 y ≤ 10 MW → Registro Ambiental: automático en la norma, USD 180 (+ USD 80), sin consultor calificado, 5–6 meses observados en otros sectores. Licencia Ambiental (75 + 15 + 15 días, EIA, participación ciudadana, póliza 100 % del PMA; 1 ‰ del proyecto, mín. USD 500/1.000) sólo > 10 MW o interés nacional / SNAP (MAATE). Umbrales del CCAN en SUIA por confirmar (P-06).", "Base = Registro Ambiental (RC-04, meses 3–8; decisión D-L1). La «unidad de proyecto» de las 10,78 ha (2 × 5 MWp = 10,0 MWp DC / 7,6 MWac) queda como riesgo documentado (11) y contingencia: Licencia = +3 meses y ≈ +70 k (memo de 03).", "Vigente · Atlas N22 (A) · plazos observados (M)", "Alta (ruta) / Media (plazo)"),
    ("Institucional", "D.E. 256 (ARCONEL) · D.E. 94 (Ministerio de Ambiente y Energía) · D.E. 376 (ministro J.C. Blum, 7-may-2026) · Resol. MAATE-2025-0002-R", "Regulador: ARCONEL — además Autoridad Ambiental Competente del sector eléctrico (UTA). Rector: Ministerio de Ambiente y Energía. Ventanilla del SGDA: CNEL EP.", "Citar sólo entidades vigentes; el trámite ambiental no va al Ministerio sino a ARCONEL (SUIA).", "Vigente · Atlas instituciones · 08-sep-2026", "Alta"),
    ("Ley de Sectores Estratégicos 2026", "Ley Orgánica para el Fortalecimiento de los Sectores Estratégicos de Minería y Energía (RO 5.º Supl. 234, 02-mar-2026)", "Vigente pero no operativa: sin reglamento, sin cupo anual (art. 25.1) ni regulación del DAE. Refuerza la propiedad y los servicios de terceros en autoabastecimiento (art. 23: texto nuevo del art. innumerado tras el 44 LOSPEE); excluye de la reversión los bienes del usuario final (art. 33); despacho preferente para ERNC ≤ 10 MW (art. 48). Litigio constitucional: 14 demandas, 1 admitida, sin medidas cautelares ni sentencia (El Universo, 06-jun-2026).", "Contexto favorable pero no necesario: el encaje SALELGI–Exergy se sostiene en la 005/24 y en el texto LOCE 2024 si la Ley cayera. Monitorear reglamento y sentencia (P-13).", "Vigente-no-operativa · Atlas N3b · 08-sep-2026", "Alta"),
    ("Sentencia de la Corte Constitucional", "Sentencia 112-21-IN/25 (11-dic-2025)", "Declara la inconstitucionalidad del num. 1 del art. 25 LOSPEE (texto 2021) con efectos a futuro; no paraliza proyectos; valida la figura del autogenerador. Superada por la sustitución del art. 25 en la Ley 2026.", "Sin efecto directo sobre un SGDA de consumidor regulado; contexto del marco y del litigio de la Ley 2026.", "Ejecutoriada · Atlas N19 · 08-sep-2026", "Alta"),
    ("Uso de suelo rural del predio", "LOTRTA art. 6 y art. 32 lit. l · Reglamento LOTRTA art. 3 · COOTAD / LOOTUGS (PUGS Montecristi)", "Si el predio es agrícola, el GAD solicita al MAG el informe técnico de no aptitud agropecuaria (90 días) para declararlo zona industrial / de infraestructura; la compatibilidad de uso la certifica el GAD (línea de fábrica).", "Clasificación catastral/PDOT del predio POR CONFIRMAR (P-07): si es agrícola, +4 meses (RC-08b) antes del permiso de construcción. Verificar antes de comprar (RC-01).", "Vigente · Atlas K1 · 08-sep-2026", "Alta (norma) / ❓ (predio)"),
    ("Servidumbre de la línea y altura", "Regulación ARCONEL-001/18 (franjas de servidumbre) · RDAC 154 Enmienda 3 (jun-2024)", "Franja de servidumbre de 6 m para líneas de V ≤ 13,8 kV. Aeronáutica: consulta de altura caso por caso ante la DGAC; no exige estudio de deslumbramiento.", "La línea 13,8 kV al punto de conexión requiere franja y, si cruza vías, permisos de Prefectura/MTOP/GAD (RC-15, «por confirmar»). ¿Resolución ministerial para la servidumbre de una línea privada de SGDA o basta el diseño aprobado por CNEL? ❓", "Vigente · Atlas N23/K2 · 08-sep-2026", "Alta / ❓ (línea privada)"),
]
CANDADOS = [
    ("1 · Régimen", "SGDA 005/24 codificada · modalidad 2a remota entre unidades de negocio de CNEL EP", '="● Habilitado (Res. ARCONEL-005/24 codificada; sin reformas a sep-2026)"', "ok"),
    ("2 · Energía (art. 9)", "Producción anual ≤ demanda anual del consumidor", f"=IF('{S4}'!${C(1)}${ENERGIA['p50']}<=Consumo_Anual/1000,\"● \"&TEXT('{S4}'!${C(1)}${ENERGIA['p50']}/(Consumo_Anual/1000),\"0%\")&\" de la demanda\",\"■ excede: \"&TEXT('{S4}'!${C(1)}${ENERGIA['norec']},\"#,##0\")&\" MWh no reconocidos\")", "ok"),
    ("3 · Comercial (art. 8 / Décima / LOSPEE art. innumerado tras el 44)", "Exergy cobra servicios y arriendo a renta fija — nunca $/kWh (exclusividad de comercialización)", '="● Sin venta de kWh · blindaje: arriendo en escritura separada, O&M por kWp-año, gerencia por hitos; consulta DG 17.ª ante duda"', "ok"),
    ("4 · Físico (art. 7a)", '="Capacidad del alimentador 13,8 kV para "&TEXT(Potencia_AC,"#,##0")&" kWac (aprobable: "&TEXT(Capacidad_Alimentador_kW,"#,##0")&" kW, por confirmar)"', '=IF(Potencia_AC>Capacidad_Alimentador_kW,"■ Potencia AC supera la capacidad por confirmar del alimentador","▲ Pendiente: pre-consulta escrita de capacidad (RC-00) + factibilidad CNEL (RC-09) — Manta al límite (CENACE, 30-jun-2026)")', "warn"),
    ("5 · Económico (Disp. Trans. Cuarta)", '="Peaje de red desde "&TEXT(Fecha_Peaje,"dd-mmm-yyyy")&" — valor no publicado (por potencia y energía)"', '="▲ Sensibilizado 0–"&TEXT(Sens_Peaje*100,"0.0")&" ¢/kWh y "&TEXT(Sens_Peaje_kW,"0.0")&" $/kW-mes (activo: "&TEXT(Eff_Peaje*100,"0.0")&" ¢ · "&TEXT(Peaje_kW_mes,"0.00")&" $/kW-mes)"', "warn"),
]
CONTRATOS = [
    ("Contrato de gerencia y desarrollo del proyecto", "Exergy → SALELGI", '="Fee "&TEXT(Fee_Gerencia_Pct,"0%")&" del valor del proyecto (hitos 30/70). Alcance: ingeniería de dueño, permisos, procura multi-contrato, supervisión, puesta en marcha."', "Partes relacionadas: documentar comparables. Retención 5 % (servicios) como anticipo del IR de Exergy; IVA 15 %."),
    ("Contratos de suministro e instalación (multi-contrato)", "Proveedores → SALELGI", "Módulos, inversores, estructura, CT/MT, BOS, obra civil, montaje, conexión. SALELGI importa (ISD/arancel a su cargo) o compra DDP.", "Sin margen EPC integrado; riesgo de integración lo gestiona Exergy. IVA: bienes FV 0 % (código 0719) y servicios 15 %, desglosados en la facturación."),
    ('="Contrato de arriendo / usufructo del terreno ("&TEXT(Hectareas,"0.0")&" ha)"', "Exergy → SALELGI", '=IF(Comprador_Terreno="SALELGI","No aplica en el caso activo: SALELGI compra el terreno (Comprador_Terreno). Si Exergy comprara: renta fija "&TEXT(Renta_Terreno_ha,"#,##0")&" $/ha-año indexada ("&TEXT(Escalacion_OPEX,"0.0%")&"/año), plazo ≥ 25 años, escritura separada del EPC/gerencia/O&M, figura inscribible y oponible ≥ plazo del crédito.","Renta fija "&TEXT(Renta_Terreno_ha,"#,##0")&" $/ha-año indexada ("&TEXT(Escalacion_OPEX,"0.0%")&"/año), plazo ≥ 25 años (vida útil del certificado), en escritura separada del EPC/gerencia/O&M; figura inscribible y oponible por plazo ≥ al del crédito (usufructo o derecho de superficie; figura óptima por confirmar, P-12).")', "Arrendamiento/posesión notariado = documento del Certificado de Habilitación (005/24 art. 15 lit. a.2). Retención 10 % (arriendo)."),
    ("Contrato de O&M", "Exergy → SALELGI", '="Fee fijo "&TEXT(Fee_OM_kWp,"0")&" $/kWp-año indexado ("&TEXT(Escalacion_OPEX,"0.0%")&"/año) o por disponibilidad garantizada (SLA "&TEXT(Disponibilidad,"0%")&"); incluye limpieza, seguridad, monitoreo, repuestos y reserva de inversores."', "Renta fija: no indexar a kWh producidos (recaracterización). Cláusula de reemplazo de inversores: quién paga (10 §G.2)."),
    ("Declaración juramentada de propiedad del SGDA", "SALELGI → CNEL", "Art. 8 lit. a) 005/24: SALELGI acredita ser dueña aunque el proyecto lo gerencie/financie un tercero.", "Previo al inicio de operación."),
    ("Pre-consulta de capacidad + Factibilidad de Conexión + Certificado de Habilitación + Contrato de Conexión (Anexo C) + Contrato de Suministro", "SALELGI ↔ CNEL EP (U.N. Manabí / El Oro)", "Carta a la máxima autoridad de la U.N. con proyectista registrado en el portal CNEL; Cat. 2, > 1 MW: estudios de estabilidad; factibilidad 17–22 días (vigencia 6 meses); rubro USD 4/kW ≤ 10.000; certificado ≈ 18 días; medidor bidireccional MT; el Contrato de Suministro inicia el reloj de 24 meses del SEA.", "Confirmar la U.N. competente para el trámite remoto inter-U.N.; preparar el expediente de habilitación durante la factibilidad (vigencia 6 meses; control F12)."),
    ("Consulta a la Administración de ARCONEL (Disp. General 17.ª) — opcional", "SALELGI / Exergy → ARCONEL", "«Los casos especiales… serán resueltos por la Administración de la ARCONEL»: vía para obtener certeza sobre el esquema de terceros (arriendo + gerencia + O&M) y la agregación inter-U.N. antes de firmar.", "Sin precedentes públicos de recaracterización (P-11); la consulta reduce el riesgo contractual (11)."),
    ("Contrato de crédito (si aplica)", "Banco → SALELGI", "Corporativo: garantía real sobre el SGDA + cesión de flujos/contratos + cuenta de reserva; DSCR ≥ 1,2x exigible.", "Ver 08_Flujo bloque B y 10 §D/§H. Líneas verdes: BanEcuador 11,86 % (PYME), Produbanco hasta 84 meses (Atlas J)."),
]
DUDAS = [("#9 · P-08", "Capacidad real del alimentador 13,8 kV Montecristi (flujo inverso ≤ 60 %); Manta entre las subestaciones al límite (CENACE, 30-jun-2026)", "Binario para inyectar 3,8 MWac; refuerzos de 6–18 meses (Expreso, 20-ago-2026)", "Pre-consulta escrita de capacidad a CNEL EP U.N. Manabí (RC-00) + Factibilidad de Conexión (RC-09)", "Alta"),
         ("#8 · P-06", "«Unidad de proyecto» ambiental por las 10,78 ha (2 × 5 MWp): Registro (≤ 10 MW) o Licencia (> 10 MW); umbrales del CCAN en SUIA", "±3–6 meses de cronograma y ≈ 70 k (memo de 03)", "Consulta a ARCONEL — Unidad Técnica Ambiental (SUIA), no al Ministerio", "Alta"),
         ("Nueva", "Trámite remoto inter-U.N.: qué unidad de negocio de CNEL tramita y cómo se liquida el crédito entre Manabí y El Oro", "Operativa de facturación (el encaje legal está confirmado: art. 6 nota 1)", "Consulta escrita a CNEL EP (Gerencia Comercial)", "Alta"),
         ("Nueva", "D.E. 32: ¿SALELGI fue notificada como cliente AV1 obligado? ¿Cómo se acredita cumplimiento parcial y un proyecto en curso al 18-dic-2026?", "Riesgo de desconexión en déficit; narrativa del proyecto", "CNEL El Oro / Viceministerio de Electricidad (oficio MAE-VEER-2026-0255-OF; reportes mensuales desde jul-2026)", "Alta"),
         ("#17 → P-01 / P-14", "Certificación ambiental previa para la deducción adicional (RLRTI 28.6.g): procedimiento y autoridad no publicados; ¿el exceso sobre el tope del 5 % se pierde o se difiere?", f'="Sin certificación no hay deducción: TIR "&TEXT(X_TIR,"0.00%")&" → "&TEXT({mo(T_DEDAD, "TIR")},"0.00%")&"; accionista "&TEXT(X_TIReq,"0.0%")&" → "&TEXT({mo(T_DEDAD, "TIR_eq")},"0.0%")&" (10 §B)"', "Consulta a ARCONEL (autoridad ambiental del sector) + consulta vinculante SRI", "Alta"),
         ("#18 → P-04", "Alcance del IVA 0 % «accesorios para la generación solar FV» (inversores, estructura, BOS)", "Capital de trabajo (recuperable): −0,01 pp de TIR si los inversores fueran 15 %", "Resolución anticipada de clasificación arancelaria SENAE (código 0719)", "Media"),
         ("#19 → P-02", "¿SGDA de autoconsumo califica como «inversión productiva» (Contrato de Inversión)? Techo de gasto tributario 2026 y cupo renovables (2025: USD 60 MM «por única ocasión»)", '="≈ "&TEXT(Aranceles_ISD/1000,"#,##0")&" k$ de arancel + ISD (caso activo)"', "CEPAI / MPCEI", "Media"),
         ("#23 → P-11", "Estructura de arriendo y O&M a renta fija (anti-recaracterización): sin precedentes públicos; la Ley 2026 legaliza expresamente a terceros", "Conserva el certificado", "Abogado eléctrico + revisión previa de la Distribuidora (art. 8b) + consulta DG 17.ª", "Alta"),
         ("Nueva · P-13", "Litigio constitucional de la Ley 2026 (14 demandas, 1 admitida, sin sentencia a jun-2026): efecto en cascada sobre arts. 25/25.1, DAE y art. 3", "Contexto: el encaje del esquema no depende de la Ley 2026", "Monitoreo de la Corte Constitucional y del reglamento", "Alta"),
         ("Nueva · P-07", "Clasificación catastral/PDOT del predio: si es agrícola → cambio de uso de suelo rural (LOTRTA art. 6: informe MAG 90 días + GAD)", "+4 meses antes del permiso de construcción (RC-08b)", "Certificado de uso de suelo del GAD Montecristi antes de comprar (RC-01)", "Alta"),
         ("Nueva · P-12", "Figura inscribible del derecho de SALELGI sobre el terreno de Exergy (arriendo / usufructo / superficie), oponible por plazo ≥ al del crédito", "Bancabilidad y documento de posesión (005/24 art. 15 a.2); no aplica si SALELGI compra", "Abogado inmobiliario + Registro de la Propiedad Montecristi", "Alta"),
         ("Nueva", "Vías y derecho de vía de la línea 13,8 kV: clasificación de la vía (Prefectura de Manabí / MTOP / GAD) y permisos de cruce", "Costo y plazo de RC-15 «por confirmar»", "Consulta a Prefectura/MTOP/GAD con el trazado de RC-14", "Media"),
         ("Nueva", "Servidumbre de la línea privada del SGDA: ¿resolución ministerial o basta el diseño aprobado por CNEL? (ARCONEL-001/18: franja 6 m a ≤ 13,8 kV)", "Trámite adicional potencial", "CNEL EP U.N. Manabí / Ministerio de Ambiente y Energía", "Media"),
         ("Nueva · P-09", "Textos ilegibles: Resol. ARCONEL-005/26 (codificación del Código de Conexión) publicada sin capa de texto; reglamento de la Ley 2026 pendiente", "Requisitos técnicos de conexión y régimen de excedentes", "Monitoreo ARCONEL / RO; pedir versión editable", "Media"),
         ("Resuelta", "Fecha exacta del plazo del D.E. 32: 18-dic-2026 (18 meses desde el RO Supl. 62, 18-jun-2025; la prensa dice 15-dic)", "Precisión citacional", "Registro Oficial Supl. 62 (Atlas N12)", "Baja")]

def table_rows(ws, r, rows, cols, sizes, bold_first=True, height_pad=4):
    """Escribe filas de tabla con altura calculada. cols: lista de índices de columna; sizes: tamaño por columna."""
    for row in rows:
        specs = []
        for i, v in enumerate(row):
            c = ws.cell(row=r, column=cols[i], value=v)
            c.font = Font(name=FONT, size=sizes[i], bold=(bold_first and i == 0), color=CARBON)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = B_BOTTOM
            # v3.1: las celdas con fórmula se estiman por el largo del texto que muestran (≈ 60 % del largo de la fórmula; ≈ 35 % si es un IF con dos ramas)
            est = v if not (isinstance(v, str) and v.startswith("=")) else "x" * int(len(v) * (0.35 if v.startswith("=IF(") else 0.6))
            specs.append((est, ws.column_dimensions[col(cols[i])].width or 10, sizes[i]))
        fit_row(ws, r, specs, min_h=16, pad=height_pad)
        r += 1
    return r


def build_legal(wb):
    ws = wb.create_sheet(S2)
    widths(ws, {"A": 2, "B": 18, "C": 24, "D": 44, "E": 40, "F": 22, "G": 8})   # 158 caracteres × 6,05 = 956 pt → 80 % = 765 pt < 772 (Excel/Mac)
    sheet_header(ws, "2 · Marco legal y regulatorio", "Lo que habilita, lo que limita y cómo se estructura; investigación de decisión, no opinión legal. Conciliado con el Atlas Regulatorio FV Ecuador v2.0 (sello 08-sep-2026). Sustenta los supuestos regulatorios de 01, los candados de 13 y los riesgos de 11 (fuentes en 12 §D).", 2, last_col=7)
    r = 5
    section(ws, r, 2, 7, "Los 5 candados del régimen elegido (estado en vivo)")
    r += 1
    hdr(ws, r, 2, 4, ["Candado", "Qué exige", "Estado"], height=18)
    for cc in (5, 6, 7): ws.cell(row=r, column=cc).border = B_HDR
    r += 1
    for lab, req, f, kind in CANDADOS:
        label(ws, r, 2, lab, bold=True, size=9, wrap=True, valign="top"); c = label(ws, r, 3, req, wrap=True, size=9, valign="top")
        chip(ws, r, 4, f, kind=kind, c2=7); ws.cell(row=r, column=4).alignment = Alignment(vertical="top", wrap_text=True)
        for cc in range(4, 8): ws.cell(row=r, column=cc).border = B_BOTTOM
        fit_row(ws, r, [(lab, 18, 9), (req, 24, 9), (f, 44 + 40 + 22 + 8, 9)], min_h=16)
        r += 1
    r += 1
    section(ws, r, 2, 7, "Matriz normativa verificada")
    r += 1
    hdr(ws, r, 2, 7, ["Tema", "Norma / artículo", "Qué dice (verificado)", "Implicación para GPM / Exergy", "Estado · verificación", "Confianza"], height=20)
    r += 1
    r = table_rows(ws, r, LEGAL_ROWS, [2, 3, 4, 5, 6, 7], [9, 8.5, 8.5, 8.5, 8.5, 8.5])
    r += 1
    section(ws, r, 2, 7, "Arquitectura contractual (SALELGI dueña · Exergy gerencia, arrienda y opera)")
    r += 1
    hdr(ws, r, 2, 5, ["Instrumento", "Partes", "Contenido esencial", "Nota"], height=18)
    for cc in (6, 7): ws.cell(row=r, column=cc).border = B_HDR
    r += 1
    r = table_rows(ws, r, CONTRATOS, [2, 3, 4, 5], [9, 8.5, 8.5, 8.5])
    r += 1
    section(ws, r, 2, 7, "Zonas grises vivas (con dueño y urgencia) — dudas del Informe Maestro y pendientes P-xx del Atlas Regulatorio v2.0")
    r += 1
    hdr(ws, r, 2, 6, ["#", "Duda", "Por qué importa", "Resolver con", "Urgencia"], height=18)
    ws.cell(row=r, column=7).border = B_HDR
    r += 1
    for row in DUDAS:
        for i, v in enumerate(row[:4]):
            c = ws.cell(row=r, column=2 + i, value=v); c.font = Font(name=FONT, size=8.5 if i else 9, bold=(i == 0), color=CARBON); c.alignment = Alignment(wrap_text=True, vertical="top"); c.border = B_BOTTOM
        chip(ws, r, 6, row[4], kind=("risk" if row[4] == "Alta" else ("warn" if row[4] == "Media" else "info")))
        ws.cell(row=r, column=6).border = B_BOTTOM; ws.cell(row=r, column=6).alignment = Alignment(vertical="top")
        fit_row(ws, r, [(row[1], 24, 8.5), (row[2], 44, 8.5), (row[3], 40, 8.5)], min_h=16)
        r += 1
    setup_print(ws, landscape=True, scale=80)
    return ws


# ---------------------------------------------------------------- 03_Tramites
TRAMITES = [
    ("RC-00", "Consultas previas y pre-consulta escrita de capacidad a CNEL EP U.N. Manabí (SRI, CEPAI, arancel)", "CNEL EP · SRI · MPCEI · SENAE", "005/24 · LRTI · COPCI", 1, 3, 15000, "—", "No", "Medio", "Anticipa refuerzos de red (Manta al límite, CENACE 30-jun-2026)."),
    ("RC-01", "Control del predio: compra de 5 ha, uso de suelo (PDOT/PUGS), figura inscribible a SALELGI", "Notaría · Registro · GAD", "Código Civil · LOTRTA art. 6", 1, 3, 8000, "—", "Sí", "Medio", "Posesión para CNEL (art. 15 a.2); si es agrícola → RC-08b; figura P-12."),
    ("RC-02", "Debida diligencia registral, topografía y geotecnia (hincado, corrosividad)", "Consultores", "—", 1, 2, 25000, "—", "No", "Medio", "Fija movimiento de tierras y drenaje."),
    ("RC-03", "Certificado de intersección (SNAP / bosques protectores)", "ARCONEL — UTA (SUIA)", "COA · RCOA", 2, 1, 500, "RC-01", "No", "Bajo", "Automático en SUIA; probablemente gratuito ❓ (500 como holgura)."),
    ("RC-04", "Registro Ambiental (FV > 1 ≤ 10 MW) ante ARCONEL — UTA, vía SUIA (PMA del expediente)", "ARCONEL — UTA (SUIA)", "ARCONEL-005/25 arts. 19–22", 3, 6, 5000, "RC-03", "Sí", "Alto", "Tasa 180 + expediente (estim.); 5–6 meses observados; Licencia: memo."),
    ("RC-06", "Certificado de altura DGAC (aeropuerto de Manta ~6 km)", "DGAC", "RDAC 154 Enm. 3 (jun-2024)", 3, 2, 2000, "RC-01", "No", "Medio", "La RDAC 154 no exige estudio de deslumbramiento."),
    ("RC-07", "Descarte arqueológico (zona manteña)", "INPC", "Ley Orgánica de Cultura", 3, 3, 12000, "RC-01", "Parcial", "Medio-Alto", "Prospección antes del movimiento de tierras."),
    ("RC-08a", "Compatibilidad de uso de suelo y línea de fábrica", "GAD Montecristi", "COOTAD · LOOTUGS · PUGS", 4, 2, 3000, "RC-01", "No", "Medio", "Sin ficha pública en Montecristi (referencia Manta); costo por confirmar."),
    ("RC-08b", "Cambio de uso de suelo rural (sólo si agrícola): informe MAG 90 días + GAD", "GAD Montecristi · MAG", "LOTRTA art. 6 · Regl. art. 3", 5, 4, 2000, "RC-08a", "No", "Medio-Alto", "Condicional (P-07); costo por confirmar."),
    ("RC-08c", "Permiso de construcción + visto bueno de Bomberos", "GAD Montecristi · Bomberos", "COOTAD · ordenanzas", 9, 3, 5000, "RC-08a, RC-08b", "No", "Medio", "Costo por confirmar (tablas no públicas); holgura 1 mes."),
    ("RC-09", "Factibilidad de Conexión (Cat. 2; estudios de flujos y estabilidad > 1 MW)", "CNEL EP U.N. Manabí", "005/24 arts. 12-16 · Código de Conexión", 7, 2, 15000, "RC-00, RC-14", "Sí", "Alto", "17-22 días; vigencia 6 meses → RC-10 en plazo (control F12); duda #9."),
    ("RC-10", "Certificado de Habilitación (USD 4/kW ≤ 10.000); posesión notariada del predio", "CNEL EP", "005/24 arts. 14-15", 12, 1, 10000, "RC-09, RC-01", "Sí", "Medio", "≈ 18 días; expediente listo en la factibilidad (art. 16)."),
    ("RC-11", "Importación y nacionalización (módulos, inversores, estructura, trafos)", "SENAE · agente afianzado", "COPCI · Arancel · LRTI 55.19", 10, 5, 15000, "RC-00, RC-04", "Sí", "Medio", "Arancel 2026 por confirmar (P-03); resolución anticipada SENAE (P-04)."),
    ("RC-12", "Construcción y montaje (civil → hincado → módulos → BOS → CT/MT → conexión)", "Contratistas bajo gerencia Exergy", "—", 13, 7, 0, "RC-08c, RC-10, RC-11", "Sí", "Medio", "Costo en CAPEX. Drenaje antes de la temporada ene–abr."),
    ("RC-13", "Pruebas, medidor MT, Contrato de Conexión (Anexo C) y de Suministro → COD", "CNEL EP", "005/24 · ARCONEL-008/24", 20, 2, 12000, "RC-12", "Sí", "Bajo", "5 + ≤ 30 días; el Contrato de Suministro inicia los 24 meses del SEA."),
    ("RC-14", "Ingeniería de detalle y owner's engineer (transversal); estudios para RC-09", "Exergy / consultores", "—", 2, 10, 60000, "RC-02", "No", "Medio", "Parte del rubro 9 del CAPEX."),
    ("RC-15", "Servidumbre y derecho de vía de la línea 13,8 kV (franja 6 m); cruces de vías", "CNEL · Prefectura · MTOP · GAD", "ARCONEL-001/18 · vial", 9, 4, 5000, "RC-01, RC-14", "No", "Medio", "Duración y costo por confirmar; ¿resolución ministerial? (02)."),
]

def build_tramites(wb):
    ws = wb.create_sheet(S3)
    # impresión a 74 % en dos páginas de columnas: tabla (A..M = 157 caracteres → 703 pt) y Gantt (B:C repetidas + N..AQ = 2 + 30 × 3 → 600 pt); una página de filas cada una
    widths(ws, {"A": 2, "B": 5, "C": 38, "D": 17, "E": 17, "F": 5, "G": 5, "H": 5, "I": 9, "J": 9, "K": 6, "L": 7, "M": 32, "N": 2})
    G0, NM = 15, 30
    for m in range(1, NM + 1):
        ws.column_dimensions[col(G0 + m - 1)].width = 3.0
    sheet_header(ws, "3 · Trámites", "Ruta crítica a COD y costos de desarrollo (Base: Registro Ambiental ante ARCONEL; pre-consulta de capacidad; factibilidad en los meses 7–8 para no agotar su vigencia de 6 meses). Edite inicio y duración (tinta); Mes_COD_Cron fija los meses de construcción de 08. Plazos del Atlas Regulatorio v2.0 (08-sep-2026).", 3, last_col=13)
    r = 5
    label(ws, r, 3, "Mes 1 del cronograma", bold=True, size=9); c = inp(ws, r, 4, _d(2026, 10, 1), fmt=FMT_DATE); name(wb, "Mes1_Cronograma", S3, "$D$5")
    label(ws, r, 5, "Mes de COD (fin de RC-13)", bold=True, size=9); calc(ws, r, 6, f"=MAX(H8:H{7 + len(TRAMITES)})", fmt="0", bold=True); ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=8); name(wb, "Mes_COD_Cron", S3, "$F$5")
    label(ws, r, 9, "Fecha de COD implícita", bold=True, size=9); ws.merge_cells(start_row=r, start_column=9, end_row=r, end_column=10)
    calc(ws, r, 11, "=EDATE(Mes1_Cronograma,Mes_COD_Cron)", fmt=FMT_DATE, bold=True); ws.merge_cells(start_row=r, start_column=11, end_row=r, end_column=12)
    chip(ws, r, 13, '=IF(ABS(EDATE(Mes1_Cronograma,Mes_COD_Cron)-Fecha_COD)<=Tol_Dias_COD,"● coherente con Fecha_COD del modelo","▲ revisar Fecha_COD")', kind="ok")
    name(wb, "Check_Cron", S3, "$M$5")
    r = 7
    heads = ["ID", "Trámite", "Autoridad", "Base legal", "Inicio\n(mes)", "Dur.\n(m)", "Fin\n(mes)", "Costo\n[USD]", "Predecesor", "Ruta\ncrítica", "Riesgo", "Nota"]
    hdr(ws, r, 2, 13, heads, height=30)
    for m in range(1, NM + 1):
        cell = ws.cell(row=r, column=G0 + m - 1, value=m); cell.font = Font(name=FONT, bold=True, size=8.5, color=GRAFITO); cell.alignment = Alignment(horizontal="center", vertical="center"); cell.border = B_HDR
        cell2 = ws.cell(row=r - 1, column=G0 + m - 1, value=f"=TEXT(EDATE(Mes1_Cronograma,{m-1}),\"mmm-yy\")"); cell2.font = Font(name=FONT, size=8.5, color=GRAFITO); cell2.alignment = Alignment(horizontal="center", textRotation=90)
    ws.row_dimensions[r - 1].height = 30
    r += 1
    r0 = r
    for tid, tr, aut, base, ini, dur, cost, pred, crit, risk, nt in TRAMITES:
        label(ws, r, 2, tid, bold=True, size=9, valign="top"); label(ws, r, 3, tr, wrap=True, size=9, valign="top"); label(ws, r, 4, aut, wrap=True, size=8.5, valign="top"); label(ws, r, 5, base, wrap=True, size=8.5, valign="top")
        inp(ws, r, 6, ini, fmt="0"); inp(ws, r, 7, dur, fmt="0"); calc(ws, r, 8, f"=F{r}+G{r}-1", fmt="0", size=9); inp(ws, r, 9, cost, fmt=FMT_USD)
        label(ws, r, 10, pred, size=8.5, valign="top")
        c = label(ws, r, 11, crit, size=9, valign="top"); c.font = Font(name=FONT, size=9, bold=(crit == "Sí"), color=(TERRACOTA if crit == "Sí" else GRAFITO))
        c = label(ws, r, 12, risk, size=8.5, valign="top"); c.font = Font(name=FONT, size=8.5, color=(LADRILLO if risk.startswith("Alto") else (OCRE if "Medio" in risk else GRAFITO)))
        label(ws, r, 13, nt, wrap=True, size=8.5, valign="top")
        ws.cell(row=r, column=14).border = Border(bottom=hair)
        for m in range(1, NM + 1):
            cc = ws.cell(row=r, column=G0 + m - 1, value=f'=IF(AND({m}>=$F{r},{m}<=$H{r}),IF($K{r}="Sí","■","▪"),"")')
            cc.font = Font(name=FONT, size=8, color=WHITE); cc.alignment = Alignment(horizontal="center", vertical="center"); cc.border = Border(bottom=hair)
        fit_row(ws, r, [(tr, 38, 9), (aut, 17, 8.5), (base, 17, 8.5), (nt, 32, 8.5)], min_h=18, pad=3)
        if tid == "RC-09": name(wb, "Fin_RC09", S3, f"$H${r}")   # v3.1: vigencia de la factibilidad (control F12)
        if tid == "RC-10": name(wb, "Fin_RC10", S3, f"$H${r}")
        r += 1
    r1 = r - 1
    ws.conditional_formatting.add(f"{col(G0)}{r0}:{col(G0+NM-1)}{r1}", CellIsRule(operator="equal", formula=['"■"'], fill=fill(TERRACOTA), font=Font(color=TERRACOTA)))
    ws.conditional_formatting.add(f"{col(G0)}{r0}:{col(G0+NM-1)}{r1}", CellIsRule(operator="equal", formula=['"▪"'], fill=fill(PIEDRA), font=Font(color=PIEDRA)))
    label(ws, r, 3, "Costos de desarrollo y permisos (sin terreno; sin construcción)", bold=True, size=9); calc(ws, r, 9, f"=SUM(I{r0}:I{r1})", fmt=FMT_USD, bold=True); total_row(ws, r, 2, 13)
    name(wb, "Costo_Desarrollo_Cron", S3, f"$I${r}")
    r += 1
    label(ws, r, 3, "Rubro 9 del CAPEX (desarrollo, permisos e ingeniería) — caso activo, cargado a GPM", size=9); calc(ws, r, 9, f"='{S5}'!$F${CAPEX['r0']+8}", fmt=FMT_USD)
    r += 1
    label(ws, r, 3, "Control: el cronograma valorado cabe en el rubro 9", size=9); chip(ws, r, 9, f'=IF(I{r-2}<=I{r-1}*(1+Tol_Costo_Tramites),"● cabe","▲ excede el rubro 9 — revisar")', kind="ok", c2=13)
    name(wb, "Check_Tramites", S3, f"$I${r}")
    r += 1
    ws.row_dimensions[r].height = 6   # v3.1: separador corto (17 hitos: la tabla debe caber en una página a 74 %)
    r += 1
    # leyenda en la columna C (columna de título): se imprime en la página de la tabla y en la del Gantt
    c = ws.cell(row=r, column=3, value="Gantt: ■ terracota = ruta crítica · ▪ piedra = no crítico · un cuadro = un mes desde Mes1_Cronograma"); c.font = font(size=8.5, color=GRAFITO); c.alignment = Alignment(wrap_text=True, vertical="top")
    c = ws.cell(row=r, column=4, value="Hitos binarios: RC-09 (capacidad del alimentador; pre-consulta escrita en RC-00) y RC-04 (Registro Ambiental ante ARCONEL; la Licencia es contingencia). Escenarios de cronograma y D.E. 32 en la página siguiente."); c.font = font(size=8.5, color=GRAFITO); c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=13); ws.row_dimensions[r].height = 24
    r_leg = r
    r += 3
    # v3.1 (doc 18 D-L1 / D-L2): escenarios de cronograma NO recogidos por el motor (Fecha_COD y Meses_Construccion son globales) → memo estático
    # en una segunda área de impresión (tercera página), para que no se parta entre la página de la tabla y la del Gantt
    memo0 = r
    section(ws, r, 2, 13, "Escenarios de cronograma — memo estático (sombra Python ≡ Motor, 08-sep-2026; recalcular si cambian las entradas)")
    r += 1
    for t in ["Hitos binarios y plazos legales: la Factibilidad de Conexión vence a los 6 meses (005/24 art. 13) → el Certificado de Habilitación (RC-10) debe caer dentro de esa vigencia (control F12 de 13); por eso RC-09 se pide en los meses 7–8 con los estudios de RC-14 y tras la pre-consulta escrita de capacidad de RC-00. Decreto Ejecutivo 32: el plazo (18-dic-2026, RO Supl. 62) cae en el mes 3 → el proyecto se acredita ante CNEL/Viceministerio como «en curso» en los reportes mensuales.",
              "Caso Conservador ambiental (Licencia en vez de Registro): RC-04′ Licencia Ambiental meses 3–11 (9 meses, ≈ USD 60.000: EIA + consultor + tasa 1 ‰ + póliza 100 % del PMA) y RC-05 participación ciudadana meses 6–8 (≈ USD 10.000) → COD +3 meses (24). Efecto (Custom): TIR del proyecto sin cambio (el VAN se refiere al COD), TIR del accionista 18,5 % → 18,0 %, DSCR mínimo 0,731 → 0,723; Base: TIR 7,98 % → 7,90 %, accionista 10,9 % → 10,3 %.",
              "Retraso por red (refuerzos del alimentador, 6–18 meses según prensa; Manta al límite, CENACE 30-jun-2026): COD +12 meses (33 meses de construcción). Efecto (Custom): TIR del proyecto sin cambio (peaje 0 y escalación del CAPEX 0), TIR del accionista 18,5 % → 16,5 % (IDC), DSCR mínimo 0,731 → 0,701; Base (peaje 0,5 ¢ y +3 %/año): TIR 7,98 % → 7,69 %, accionista 10,9 % → 8,5 %. No incluye el costo de oportunidad del ahorro no percibido durante el retraso (≈ el ahorro del año 1 por cada 12 meses) ni el riesgo del D.E. 32. En el artefacto interactivo este escenario es un preset vivo.",
              "Nota: RC-05 (participación ciudadana) no existe en el caso Base porque el Registro Ambiental no la exige (por confirmar, Atlas N22); los IDs de los hitos se conservan para trazabilidad con las versiones anteriores."]:
        note(ws, r, 3, "• " + t, c2=13, size=8.5); fit_row(ws, r, [(t, 38 + 17 + 17 + 5 + 5 + 5 + 9 + 9 + 6 + 7 + 32, 8.5)], min_h=14); r += 1
    memo1 = r - 1
    ws.col_breaks.append(Break(id=13))   # página 1: tabla A..M · página 2: Gantt (B:C repetidas + N..AQ) · página 3: memo (segunda área)
    setup_print(ws, landscape=True, scale=74, title_rows="6:7", title_cols="B:C", area=[f"A1:{col(G0 + NM - 1)}{r_leg}", f"A{memo0}:M{memo1}"])   # 74 %: tabla y Gantt caben cada uno en una página
    return ws


# ---------------------------------------------------------------- 11_Riesgos
RIESGOS = [
    ("Regulatorio", "Peaje de red para SGDA desde 28-feb-2029 (valor no publicado; por potencia y energía) erosiona el ahorro", 3, 3, "Sensibilidad 0–1,5 ¢/kWh y 0,5–1,0 $/kW-mes (10 §B); cláusula de reapertura en contratos; monitoreo de borradores ARCONEL; el alza tarifaria compensa parcialmente.", "Exergy (regulatorio)", "Borrador de regulación ARCONEL / consulta pública"),
    ("Técnico-regulatorio", "Alimentador 13,8 kV sin capacidad para 3,8 MWac: Manta entre las subestaciones al límite (CENACE vía Expreso, 30-jun-2026); refuerzos de 6–18 meses (Expreso, 20-ago-2026)", 3, 3, "Pre-consulta escrita de capacidad (RC-00) y factibilidad temprana (RC-09); alimentadores con margen; contingencia para refuerzos; producción ≤ demanda. Retraso de 12 meses: TIR del accionista 18,5 % → 16,5 % (Custom; memo estático de 03).", "Exergy (ingeniería)", "Respuesta de la pre-consulta / factibilidad"),
    ("Ambiental", "«Unidad de proyecto» (10,78 ha; 2 × 5 MWp) → Licencia Ambiental en vez de Registro ante ARCONEL (+3 meses, ≈ +70 k)", 2, 3, "Consulta de categorización a ARCONEL-UTA (SUIA); umbrales del CCAN (P-06); separar predios/plazos si conviene; Base = Registro (decisión D-L1); contingencia en el memo de 03.", "Exergy (permisos)", "Pronunciamiento de ARCONEL-UTA en SUIA"),
    ("Contractual", "Recaracterización del arriendo/O&M como venta encubierta de energía → revocatoria del certificado (sin precedentes públicos, P-11; la Ley 2026 legaliza a terceros)", 2, 3, "Renta fija indexada, nunca por kWh; arriendo en escritura separada; revisión previa de la Distribuidora (art. 8b); consulta DG 17.ª; abogado eléctrico. Probabilidad 2 por prudencia hasta la consulta (D-L8).", "Exergy (legal)", "Observaciones de CNEL al instrumento"),
    ("Comercial / regulatorio", "D.E. 32: SALELGI (AV1) sin autogeneración al 18-dic-2026 → desconexión en déficit / pérdida de tarifa preferente", 2, 3, "Notificar a CNEL/Viceministerio el proyecto en curso (reportes mensuales desde jul-2026); evaluar respaldo transitorio; documentar avance (pre-consulta, factibilidad, permisos).", "SALELGI + Exergy", "Oficios CNEL El Oro / MAE-VEER"),
    ("Mercado", "CAPEX real > base (módulos +30 % desde dic-2025; estructura ZM con arancel 20 %; trafos con lead time largo; arancel 2026 no cotejado, P-03)", 2, 2, "3 cotizaciones (EPC llave en mano vs multi-contrato); fijar precio de módulos con ventana; contingencia 6 %; caso Conservador +15 % y +5 %/año.", "Exergy (procura)", "Cotizaciones firmes vs 05_CAPEX"),
    ("Tarifario / político", "Cambio del pliego o de subsidios (déficit 2026 USD 621,9 M): la tarifa evitable puede subir o bajar", 2, 2, "Escenarios ±15 % y escalación 0–3 %; el alza favorece el ahorro; diversificar valor (I-REC, Alcance 2).", "Exergy", "Resoluciones ARCONEL anuales (nov-dic)"),
    ("Fiscal", "Deducción adicional no aplicable: certificación ambiental previa (RLRTI 28.6.g) no obtenible o tardía (procedimiento no publicado, P-01); IVA 0 % «accesorios» más restrictivo (P-04)", 2, 3, f'="Solicitar la certificación a ARCONEL-UTA antes de la primera declaración; consulta vinculante SRI; resolución anticipada SENAE. Cuantificado en el tornado (10 §B): sin deducción, TIR "&TEXT({mo(T_DEDAD, "TIR")},"0.0%")&" frente a "&TEXT(X_TIR,"0.0%")&"; accionista "&TEXT({mo(T_DEDAD, "TIR_eq")},"0.0%")&" frente a "&TEXT(X_TIReq,"0.0%")&"."', "SALELGI (tributario) + Exergy (permisos)", "Certificación ARCONEL / absolución SRI"),
    ("Financiero", '="DSCR mínimo "&TEXT(P50_DSCR,"0.00")&"x en t = "&Anio_DSCR_Min&" con "&Plazo_Deuda&" años / "&TEXT(Pct_Apalancamiento,"0%")&" (objetivo "&TEXT(DSCR_Objetivo,"0.00")&"x)"', 3, 2, "Plazo 10 años (alineado con la depreciación fiscal; a 12 años el DSCR cae tras el año 10) o apalancamiento 50–60 %; período de gracia; cuenta de reserva; líneas verdes (BanEcuador 11,86 %; Produbanco hasta 84 meses).", "SALELGI (finanzas)", "Term sheet bancario"),
    ("Operativo", "Soiling (6–7 meses secos, garúa), corrosión C3/C4, seguridad física", 2, 1, "Limpieza 3–4/año en el fee de O&M; estructura ZM275+ e inversores C5; seguridad 24/7 incluida.", "Exergy (O&M)", "PR mensual vs 82,5 %"),
    ("Cronograma", "Retrasos: Registro Ambiental «meses en la práctica» (5–6), permisos municipales sin fichas públicas, cambio de uso de suelo rural (90 días MAG), importación/aduana (INEN, clasificación), lluvias ene–abr", 2, 2, "Expediente de habilitación preparado durante la factibilidad (vigencia 6 meses, control F12); resolución anticipada de clasificación; agente afianzado; drenaje antes de la temporada; holguras en RC-08c y RC-15.", "Exergy (gerencia)", "Hitos RC-04 / RC-08 / RC-11 / RC-12"),
    ("Regulatorio", "Cambio regulatorio antes de operar: más de seis hitos legales entre 2021 y 2026; el patrón amplía la participación privada", 3, 2, "La Disp. Transitoria Única de la 005/24 protege lo otorgado; obtener el Certificado de Habilitación cuanto antes; monitoreo trimestral de ARCONEL (Atlas).", "Exergy (regulatorio)", "Borradores ARCONEL / Registro Oficial"),
    ("Regulatorio", "Vacío reglamentario y litigio constitucional de la Ley 2026 (14 demandas, 1 admitida): régimen de excedentes remitido al reglamento", 2, 2, "El modelo no depende de excedentes (art. 9: producción ≤ demanda) ni de la Ley 2026 (encaje en la 005/24 + LOCE 2024); monitoreo (P-13).", "Exergy (legal)", "Sentencia CC / reglamento de la Ley 2026"),
    ("Institucional", "Inestabilidad institucional: dos ministros en 20 meses, fusión Ambiente-Energía, ARCONEL con director encargado y nuevo rol ambiental", 2, 2, "Trámites por escrito y con acuse; expedientes completos; no depender de criterios verbales; consulta DG 17.ª para casos especiales.", "Exergy (permisos)", "Cambios de autoridades / reorganizaciones"),
    ("Fiscal (Exergy)", "IVA de Exergy no recuperable por proporcionalidad (art. 66) si mezcla ventas gravadas y 0 %; precios de transferencia con SALELGI; retenciones 2026 (2 / 5 / 10 %) como anticipo", 2, 2, "Facturar bienes 0 % y servicios 15 % por separado; estudio de comparables (fee, O&M, arriendo); planificar la caja de las retenciones. Interno: no afecta el flujo de SALELGI.", "Exergy (tributario)", "Declaraciones de IVA / Anexo OPR"),
]

def build_riesgos(wb):
    ws = wb.create_sheet(S11)
    widths(ws, {"A": 2, "B": 14, "C": 40, "D": 6, "E": 7, "F": 6, "G": 8, "H": 44, "I": 14, "J": 17})   # 158 caracteres × 6,05 = 956 pt → 80 % = 765 pt
    sheet_header(ws, "11 · Matriz de riesgos", "Probabilidad × impacto (1–3 en cada eje; umbrales en 01 §I), mitigación, dueño y alerta temprana. Peaje, red y fiscal (certificación de la deducción) dominan la decisión; los de mercado, fiscal y financiero se cuantifican en 10. Conciliada con el Atlas Regulatorio v2.0 (08-sep-2026).", 11, last_col=10)
    r = 5
    hdr(ws, r, 2, 10, ["Categoría", "Riesgo", "Prob.\n(1-3)", "Impacto\n(1-3)", "Score", "Nivel", "Mitigación", "Dueño", "Alerta temprana"], height=30)
    r += 1
    r0 = r
    for cat, desc, p, i, mit, own, alert in RIESGOS:
        label(ws, r, 2, cat, bold=True, size=9, valign="top", wrap=True); label(ws, r, 3, desc, wrap=True, size=9, valign="top")
        inp(ws, r, 4, p, fmt="0"); inp(ws, r, 5, i, fmt="0")
        calc(ws, r, 6, f"=D{r}*E{r}", fmt="0", bold=True)
        c = calc(ws, r, 7, f'=IF(F{r}>=Umbral_Riesgo_Alto,"■ ALTO",IF(F{r}>=Umbral_Riesgo_Medio,"▲ MEDIO","● BAJO"))', align="left", bold=True, size=9)
        label(ws, r, 8, mit, wrap=True, size=8.5, valign="top"); label(ws, r, 9, own, wrap=True, size=8.5, valign="top"); label(ws, r, 10, alert, wrap=True, size=8.5, valign="top")
        fit_row(ws, r, [(cat, 14, 9), (desc, 40, 9), (mit, 44, 8.5), (own, 14, 8.5), (alert, 17, 8.5)], min_h=18)
        r += 1
    r1 = r - 1
    ws.conditional_formatting.add(f"G{r0}:G{r1}", FormulaRule(formula=[f'LEFT(G{r0},1)="■"'], font=Font(color=LADRILLO, bold=True)))
    ws.conditional_formatting.add(f"G{r0}:G{r1}", FormulaRule(formula=[f'LEFT(G{r0},1)="▲"'], font=Font(color=OCRE, bold=True)))
    ws.conditional_formatting.add(f"G{r0}:G{r1}", FormulaRule(formula=[f'LEFT(G{r0},1)="●"'], font=Font(color=SALVIA, bold=True)))
    setup_print(ws, landscape=True, scale=80)
    return ws


# ---------------------------------------------------------------- 12_Fuentes
FUENTES = [
    ("Regulación ARCONEL-005/24 codificada (Res. ARCONEL-010/2024), PDF oficial — arts. 5.17, 6, 7, 8, 9, 10, 12–16, 25, 27, 28, Disp. Gral. Décima y 17.ª, Disp. Trans. Cuarta (leído 01-sep-2026; verbatim cotejados por la Auditoría Fases 1–2, 07-sep-2026).", "https://arconel.gob.ec/wp-content/uploads/downloads/2024/10/Regulacion-005_24-Codificada-signed-1.pdf"),
    ("ARCONEL — Regulaciones vigentes al 23-abr-2026 (01-sep-2026).", "https://arconel.gob.ec/wp-content/uploads/downloads/2026/04/Regulaciones_vigentes_23ABRIL26.pdf"),
    ("CorralRosales — Reformas a la regulación de SGDA (Res. ARCONEL-010/2024, RO 689, 22-nov-2024) (01-sep-2026).", "https://corralrosales.com/reformas-a-la-regulacion-de-sgda-para-consumidores-regulados/"),
    ("Reglamento LOCE — D.E. 176 (RO 28-feb-2024): art. 18 y DT 16.ª (peajes SGDA; arts. 5 y 24 por verificar), art. 78 → RLRTI art. 28 num. 6 lit. g (certificación ambiental previa para la deducción adicional) — PDF SRI (01-sep-2026; Atlas N20).", "https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/97730389-223f-42e0-a19b-5fbbd0883bb1/Reglamento_Ley_competitividad_energetica_publicacion28022024.pdf"),
    ("Decreto Ejecutivo 32 (15-jun-2025; RO Supl. 62, 18-jun-2025; DT 14.ª: 18 meses → 18-dic-2026): PBP Law; El Universo (jun-2025); Expreso (22/23-jul y 20-ago-2026: seguimiento mensual del Viceministerio); El Oriente (24-jul-2026); DMEGC Solar LATAM (01-sep-2026).", "https://www.expreso.ec/economia-y-negocios/plazo-empresas-generen-propia-energia-acerca-ecuador-gobierno-activa-seguimiento-290110.html"),
    ("Res. ARCONEL-006/25 (30-jun-2025) y Res. ARCONEL-029/25 (31-dic-2025) — pliego 2025 codificado y pliego 2026; INF-DTRET-2025-087 (costo 12,83 vs 10,61 ¢/kWh).", "https://www.cnelep.gob.ec/wp-content/uploads/2026/01/Resoluci%C3%B3n-Nro.-ARCONEL-029-2025-y-anexos-cert-signed.pdf"),
    ("Análisis de 19 planillas CNEL EP de SALELGI S.A. (cuenta 201013346360), 17-jul-2026 — 19/19 correctas; 2025 completo + ene–may 2026 (+17,2 % interanual); últimos 12 meses reales (jun-25 → may-26) ≈ US$ 1,15 M; demanda promedio y FGD sólo para la factura de referencia.", None),
    ("Informe Maestro Marco Regulatorio FV Ecuador (S5) · Régimen Fiscal, Financiamiento y Riesgos (S4) · Conexión, Permisos, Sitio, Importación (S3) · Investigación S2 — Exergy, 21-jul-2026.", None),
    ("Estimación CAPEX y OPEX — planta FV 10 MWp Montecristi (jul-2026): OPEX 20 $/kWp-año «todo incluido» a suelo = O&M 8 · limpieza 3,5 · seguridad 3 · seguros 3,5 · monitoreo 1,5 · administración 2 · reserva de inversores 1,5 (en 06 la reserva queda dentro del fee y el reemplazo se modela aparte en 05); OPIS/pv magazine: CMM TOPCon 0,108 US$/W FOB (28-ago-2026).", "https://pv-magazine-usa.com/2026/08/28/china-topcon-solar-module-prices-rise-on-upstream-cost-pressure-as-deals-lag-offers/"),
    ("Recurso solar Montecristi (15-jul-2026): GHI 1.575 kWh/m²; TMY P50/P90 adaptado (Solargis + GSA); pvlib 0.15.2, inclinación 10° N, PVWatts, η de inversor constante, Pdc máx 0,90 kW/kWp: 6.470 / 5.777 MWh año 1; curva de recorte por ratio DC/AC relativa a 1,32 (incertidumbre ±0,3 pp).", None),
    ("BCE — tasas referenciales ago-2026 (Atlas J): corporativo 6,79 % · empresarial 8,62 % · PYME 9,18 %; máximas mar-2026 (VerifacturaEC): corporativo 9,33 %, empresarial 10,21 %, PYMES 11,83 %; Primicias (05-ago-2026): efectiva promedio corporativo 6,74 % (jun-2026). Financiamiento verde: BanEcuador 11,86 % (PYME, ≤ USD 3 MM, 60 meses, 6 de gracia), Produbanco Líneas Verdes hasta 84 meses; riesgo país 386 pb (12-jun-2026); S&P B (14-ago-2026).", "https://www.primicias.ec/economia/tasas-interes-ecuador-reduccion-creditos-prestamos-bancos-129529/"),
    ("Informe de auditoría del deck v3/v4 (22-jul-2026) — decisiones vinculantes del deck (750 k$/MWp; LCOE 85 vs 111; payback 6,2); fecha de los precios del CAPEX bottom-up (Fecha_Precios = 22-jul-2026).", None),
    # ronda 2 (v3.0)
    ("LRTI art. 11 (amortización de pérdidas: hasta 5 años siguientes, ≤ 25 % de la utilidad gravable de cada año) — texto codificado SRI; verificar la redacción vigente en la consulta SRI #17/#18 (pendiente).", "https://www.sri.gob.ec/ley-de-regimen-tributario-interno"),
    ("Res. ARCONEL-005/24 codificada, art. 5.17: peaje SGDA con «valores por potencia y energía» (componente por potencia no publicado → Peaje_kW_mes = 0 en el Base; 0,5 y 1,0 $/kW-mes en el tornado) (verificado 02-sep-2026).", "https://arconel.gob.ec/wp-content/uploads/downloads/2024/10/Regulacion-005_24-Codificada-signed-1.pdf"),
    ("03_Tramites: cronograma valorado y mes del COD (Mes_COD_Cron = 21 meses) → Meses_Construccion de 01 (una sola fuente para los intereses durante la construcción).", None),
    ("Vida útil de inversores string 10–15 años (garantías de fabricante 10 años ampliables; IEA-PVPS T13, 2021) → reemplazo en t = 13 a 0,06 $/Wac (estimación; cotización pendiente); disponibilidad garantizada típica en contratos de O&M 98–99 % (por confirmar con el contrato de Exergy).", None),
    ("01 H4: precios de módulos > +30 % desde dic-2025 (OPIS/pv magazine, 28-ago-2026) → escalación del CAPEX 3 %/año Base · 5 % Conservador · 0 % Favorable hasta la compra (2027–28); índice por confirmar.", None),
    # v3.1 (actualización legal, doc 18): Proyecto «Marco Legal FV Ecuador — Exergy»
    ("Atlas Regulatorio FV Ecuador v2.0 — Exergy (Proyecto «Marco Legal FV Ecuador», claude.ai; sello 08-sep-2026 con pasada adversarial): 32 normas con vigencia y cadena, 16 hitos de permisos, 24 conceptos fiscales, 24 pendientes (P-01…P-14, D-01…D-11), 18 correcciones, 45 fuentes primarias. Base de la conciliación legal v3.1 (doc 18, 08-sep-2026).", "https://claude.ai/code/artifact/a807297c-b6d9-4df8-a041-fbabd8dc70c4"),
    ("Informe Fase 3 v1.1 — Fiscal, financiamiento, permisos y riesgos (07/08-sep-2026; errata: el tope del 5 % subsiste) e Informe de Auditoría Fases 1–2 (92 filas verificadas contra fuentes primarias, 07-sep-2026), Proyecto «Marco Legal FV Ecuador — Exergy».", None),
    ("Ley Orgánica para el Fortalecimiento de los Sectores Estratégicos de Minería y Energía (RO 5.º Supl. 234, 02-mar-2026): arts. 23 (art. innumerado tras el 44 LOSPEE), 33 y 48; vigente-no-operativa; litigio constitucional 14 demandas / 1 admitida (El Universo, 06-jun-2026). Sentencia CC 112-21-IN/25 (11-dic-2025).", None),
    ("Resol. ARCONEL-005/25 — Procedimiento para la regularización, prevención, control y seguimiento ambiental de actividades eléctricas (RO Supl. 67, 25-jun-2025): arts. 19–22 Registro Ambiental (FV > 1 ≤ 10 MW), 23–35 Licencia; Resol. MAATE-2025-0002-R (22-abr-2025): ARCONEL como Autoridad Ambiental Competente del sector eléctrico; A.M. 083-B (tasa USD 180).", None),
    ("Regulación ARCONEL-008/24 (Resol. 015/2024, 15-nov-2024) — prestación del servicio de distribución y comercialización (sucede a la 001/20: medición) y ARCONEL-009/24 (calidad, codificada); ARCONEL-006/24 (Resol. 011/2024, 27-oct-2024) deroga la 002/21.", None),
    ("Resol. SRI NAC-DGERCGC26-00000009 (27-feb-2026; vigente 01-mar-2026) — porcentajes de retención en la fuente 2026 (obra 2 % · servicios de sociedades 5 % · arriendo 10 % · bienes 2 %). LRTI art. 65 (IVA 15 %), art. 55 num. 19 (0 % FV), art. 10 num. 7 (deducción adicional, tope 5 %), art. 11 (arrastre de pérdidas).", None),
    ("SENAE — boletín 15-ene-2024: código Ecuapass 0719 para bienes con IVA 0 % «paneles solares y accesorios para la generación solar FV»; COMEX 002-2025 (0 % temporal) vencida el 31-dic-2025 sin prórroga localizada; ISD 2026: D.E. 272 y Acuerdo MPCEI-2026-0003-A (tarifas diferenciadas sin partidas FV); RAISD art. 17.1 (exención con contrato de inversión).", None),
    ("LOTRTA art. 6 y 32 lit. l; Reglamento art. 3 — cambio de uso de suelo rural (informe MAG en 90 días, lo solicita el GAD). Regulación ARCONEL-001/18 — franjas de servidumbre (6 m a ≤ 13,8 kV). RDAC 154 Enmienda 3 (jun-2024) — consulta de altura DGAC, sin estudio de deslumbramiento.", None),
    ("Prensa verificada por el Atlas: Expreso 30-jun-2026 (CENACE: subestaciones al límite, Manta; 643 MW privados contenidos) · Expreso 20-ago-2026 (refuerzos de red 6–18 meses) · Expreso 23-jul-2026 (seguimiento mensual del D.E. 32) · El Universo 06-jun-2026 (litigio de la Ley 2026).", None),
]



CONFIRM_WHY = {   # por qué cada supuesto marcado «· por confirmar» sigue abierto (12 §B); las claves deben cubrir todas las entradas marcadas
    "Fecha_COD": "depende de RC-04 (ambiental) y RC-09 (capacidad).",
    "Capacidad_Alimentador_kW": "Factibilidad de Conexión de CNEL pendiente (art. 7.a 005/24); candado F4.",
    "Peaje_SGDA": "valor no publicado por ARCONEL (los cuatro casos llevan su valor en el bloque B); 10 §B y §E lo barren.",
    "IVA_Recuperable": "confirmar con contabilidad de SALELGI (ventas gravadas y capacidad de absorber ≈ 0,46 M de crédito en ~6 meses).",
    "Escudo_Negativo": "SALELGI con utilidad gravable positiva.",
    "Ingresos_SALELGI": "rango 8–12 M (tope 5 % del art. 10.7).",
    "Pct_Elegible_DedAd": "porción «maquinaria, equipos y tecnología» del CAPEX.",
    "Tributos_Locales": "GAD Montecristi/Machala.",
    "Costo_Gerencia_Pct": "costo interno de Exergy.",
    "Predial_Terreno": "estimación S4 (< 2.000 $/año).",
    "Costos_Transaccion_Terreno_Pct": "alcabala 1 % (COOTAD) + notaría y registro ≈ 0,5 % (estimación).",
    # ronda 2 (doc 13 P5)
    "Disponibilidad": "garantía de disponibilidad del contrato de O&M de Exergy (típica 98–99 %); cada caso lleva la suya en el bloque B.",
    "Escalacion_CAPEX": "índice de precios de módulos e inversores hasta la compra (2027–28) desde el 22-jul-2026 (Fecha_Precios); cada caso lleva el suyo en el bloque B.",
    "Reemplazo_USD_Wac": "cotización del reemplazo de inversores (0,06 $/Wac ≈ 6 % del CAPEX); el pagador lo fija el contrato de O&M.",
    "Desmantelamiento_Pct": "costo de desmontaje y disposición neto de chatarra al final del horizonte (0 % en el Base; 2 % en el tornado).",
    "Peaje_kW_mes": "componente por potencia del peaje SGDA (art. 5.17 Res. 005/24 codificada): valor no publicado; 0 en el Base.",
    "Utilidad_Gravable_SALELGI": "dato P3 (contabilidad de SALELGI): utilidad gravable disponible para absorber pérdidas incrementales; vacío = ilimitada.",
    # v3.1 (doc 18 D-L6)
    "Aplica_DedAd": "certificación ambiental previa exigida por el RLRTI art. 28 num. 6 lit. g (procedimiento no publicado, Atlas P-01); Sí en el Base; el tornado (10 §B) muestra el caso sin deducción.",
}


def CONFIRM_LIST():
    """Lista de 12 §B generada desde INPUTS/ESCENARIOS: toda entrada marcada «por confirmar» aparece con su valor entregado y el motivo."""
    from build_core import INPUTS as _INPUTS, ESCENARIOS as _ESC
    out = []

    def fmtv(v, fmt):
        if v is None:
            return "vacío"
        if hasattr(v, "year"):
            return f"{v.day:02d}-{('ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic')[v.month - 1]}-{v.year}"
        if isinstance(v, (int, float)) and not isinstance(v, bool) and fmt and "%" in fmt:
            return (f"{v:.1%}".replace(".", ",") if abs(v * 100 - round(v * 100)) > 1e-9 else f"{v:.0%}").replace("%", " %")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if float(v).is_integer() and abs(v) >= 1000:
                return f"{int(v):,}".replace(",", ".")
            return f"{v:g}".replace(".", ",")
        return str(v)

    def unit_of(u, fmt, val):
        """Unidad que se añade tras el valor: sin repetir el «%» ya impreso ni el texto de una lista (Sí / No) ni la palabra «fecha»."""
        if not u or u == "fecha" or (isinstance(val, str) and val in u):
            return ""
        if fmt and "%" in fmt:
            return u[1:].strip() if u.startswith("%") else u
        return u
    for sec, nm, lab, val, u, fmt, conf, nt in _INPUTS:
        if nm and conf:
            assert nm in CONFIRM_WHY, f"falta el motivo de {nm} en CONFIRM_WHY"
            uu = unit_of(u, fmt, val)
            out.append(f"{nm} = {fmtv(val, fmt)}{('' if uu.startswith('/') else ' ') + uu if uu else ''} — {CONFIRM_WHY[nm]}")
    for nm, rng_nm, lab, u, fmt, vals, conf, nt in _ESC:
        if conf:
            assert nm in CONFIRM_WHY, f"falta el motivo de {nm} en CONFIRM_WHY"
            uu = unit_of(u, fmt, None)
            out.append(f"{nm} (bloque B: Custom {fmtv(vals['X'], fmt)} · C {fmtv(vals['C'], fmt)} · B {fmtv(vals['B'], fmt)} · F {fmtv(vals['F'], fmt)}{('' if uu.startswith('/') else ' ') + uu if uu else ''}) — {CONFIRM_WHY[nm]}")
    out.append("Drivers de escala Wp / Wac / fijo de cada rubro (05_CAPEX, tabla «Drivers de escala») — pesos estimados; validez del CAPEX por drivers 3–8 MWp.")
    out.append("Además (no contados): aranceles 2026 de inversores 5 % / estructura 20 % / trafos 10 % — no cotejados en 2026 (Atlas P-03; COMEX 002-2025 vencida el 31-dic-2025); demanda promedio 2.200 kW y FGD 0,956 (sólo para la factura de referencia).")
    out.append("Pendientes legales del Atlas Regulatorio v2.0 (no son entradas del modelo y no cuentan en N_Por_Confirmar; detalle en 02 zonas grises): P-01 certificación ambiental de la deducción · P-02 techo de gasto tributario 2026 · P-03 arancel 2026 · P-04 alcance del IVA 0 % · P-06 umbrales del CCAN en SUIA · P-07 uso de suelo del predio · P-08 capacidad remanente del alimentador · P-09 textos ilegibles · P-11 precedentes de recaracterización · P-12 figura inscribible · P-13 litigio de la Ley 2026 · P-14 exceso sobre el tope.")
    return out


def build_fuentes(wb, motor_fcf_base_terms):
    ws = wb.create_sheet(S12)
    widths(ws, {"A": 2, "B": 50, "C": 30, "D": 30, "E": 24, "F": 22})   # 158 caracteres × 6,05 = 956 pt → 80 % = 765 pt
    sheet_header(ws, "12 · Fuentes y calidad", "Metodología: supuestos por confirmar (§A), simplificaciones declaradas (§B), conciliación con los libros previos (§C), fuentes con enlace (§D) y convenciones e historial (§E). El control de calidad en vivo está en 13.", 12, last_col=6, total=NSHEETS)
    r = 5
    F, Fz, E, K = FLUJO, FISCAL, ENERGIA, CAPEX
    section(ws, r, 2, 6, "A · Supuestos por confirmar", guide='="marcados «· por confirmar» (subrayado punteado) en 01_Supuestos y en los drivers de 05_CAPEX · "&N_Por_Confirmar&" en el libro · control I2"', guide_col=3)
    r += 1
    for t in CONFIRM_LIST():
        note(ws, r, 2, "• " + t, c2=6, size=9); fit_row(ws, r, [(t, 150, 9)], min_h=14); r += 1
    r += 1
    section(ws, r, 2, 6, "B · Simplificaciones declaradas")
    r += 1
    for t in ["Periodicidad anual; t=−1 (30 % CAPEX) y t=0 (70 %); COD = inicio del año 1. El IVA de cada tramo se recupera en el período siguiente.",
              "Ahorro = energía inyectada × tarifa por bloque (0,113 / 0,105) ponderada por el perfil horario del TMY; no se modela ahorro en demanda, comercialización ni SAPG (remoto).",
              "Impuestos incrementales de SALELGI: participación 15 % sobre utilidad contable incremental e IR 25 % sobre base imponible con deducción adicional topada. Absorción de pérdidas: ilimitada si Utilidad_Gravable_SALELGI está vacía (Escudo_Negativo gobierna) o limitada a ese monto anual con un pool de pérdidas amortizable hasta el 25 % de la base gravable del año (art. 11 LRTI) — pool simple, sin la caducidad de 5 años por añada (más favorable que la ley cuando quedan pérdidas antiguas; el saldo no amortizado se declara en el control H5).",
              "Depreciación lineal: equipos 10 años, obra civil 20 años; el fee de gerencia, desarrollo y contingencia se capitalizan.",
              "Deuda: francesa anual post-gracia; intereses durante la construcción capitalizados en proporción a los meses del cronograma de 03 (IDC × Meses_Construccion / 12; el eje anual sigue comprimiendo la construcción en t = −1 y 0); sin comisiones ni seguros de crédito. El VAN del accionista se descuenta a Tasa_Descuento_Equity.",
              "Exergy: impuestos 36,25 % sobre utilidad positiva de cada año (sin arrastre); terreno sin depreciación; residual = precio de compra nominal (sensibilidad 0 %).",
              "Peaje SGDA modelado con dos componentes desde 28-feb-2029 (fracción del año según Fecha_COD): $/kWh inyectado (bloque B) y $/kW-mes sobre la potencia AC nominal (Peaje_kW_mes, 0 hasta que ARCONEL publique el valor; art. 5.17 de la 005/24 codificada).",
              "El IVA sobre servicios recurrentes (O&M, arriendo, seguros) es crédito para SALELGI y no se modela. Reemplazo de inversores como partida explícita en Reemplazo_Anio (Reemplazo_USD_Wac × Potencia_AC), pagado por SALELGI (capex depreciable en 10 años o hasta el horizonte), por Exergy (gasto de Exergy con cargo a la reserva del fee de O&M) o sin reemplazo; desmantelamiento como gasto deducible en t = Horizonte (Desmantelamiento_Pct × CAPEX).",
              "Energía = yield canónico × recorte × Disponibilidad × (1 − Degradacion_Adicional)^(t−1); el vector canónico pvlib ya incluye ≈ 0,55 %/año de degradación. Escalación de los precios del CAPEX desde Fecha_Precios hasta cada desembolso (Anios_Precios − 1 y Anios_Precios años) con la tasa del bloque B; se aplica también al $/Wp fijo si el caso lo usa (Favorable: 0 %).",
              "Payback interpolado en el último año con acumulado negativo (robusto si el reemplazo de inversores vuelve a hundir el acumulado; con un solo cruce coincide con la fórmula simple — control H6). DSCR mínimo y promedio con MIN/AVERAGE sobre la fila de DSCR, que vale «» en los años sin servicio de deuda (Excel y LibreOffice ignoran el texto).",
              "No se modela la segunda planta de 5 MWp ni la venta de I-REC (argumento comercial: ≈ 1.550 tCO₂e/año de Alcance 2 con factor 0,12 tCO₂/MWh — estimación).",
              "v3.1 · Deducción adicional condicionada: Aplica_DedAd (Sí/No) multiplica la deducción en 07 (DedAd_Anual) y en el Motor (fila «Deducción adicional aplicable»); el tornado incluye el caso alterno (barra 15). Permiso ambiental: 03 y el rubro 9 asumen Registro Ambiental ante ARCONEL; la Licencia y el retraso por red se documentan como memo estático en 03 (calculado con la sombra, no con el motor: Fecha_COD y Meses_Construccion son globales) y como riesgos en 11. El IVA del rubro 9 (12 %) es 15 % sobre ≈ 80 % de servicios gravados."]:
        note(ws, r, 2, "• " + t, c2=6, size=9); fit_row(ws, r, [(t, 150, 9)], min_h=14); r += 1
    r += 1
    section(ws, r, 2, 6, "C · Conciliación con los libros previos y el deck v4")
    r += 1
    hdr(ws, r, 2, 6, ["Pieza", "CAPEX", "OPEX año 1", "Fiscal", "Resultado reportado"], height=18)
    r += 1
    r = table_rows(ws, r, [("Modelo interno v2.0 (15-jul-2026)", "4,65 M (0,93 costo)", "80 k", "IR 25 %; doble depreciación sin tope; sin participación", "TIR 11,3 % · VAN +405 k · payback 7,5"),
                           ("Modelo cliente v3.1 (17-jul-2026)", "5,00 M (1,00 precio)", "100 k", "ídem", "TIR 9,6 % · VAN −131 k · payback 8,3"),
                           ("Deck v4 L14 (22-jul-2026, cliente externo)", "3,75 M (0,75 comercial)", "100 k esc. 1,5 %", "no muestra TIR/VAN", "LCOE ≈ 85 vs 111 $/MWh · payback ≈ 6,2"),
                           ('="Este libro "&Version&" ("&TEXT(Fecha_Analisis,"dd-mmm-yyyy")&")"', '="Bottom-up "&TEXT(CAPEX_Base_f1/(Potencia_DC*1000),"0.00")&" $/Wp sin IVA a "&TEXT(Potencia_DC/1000,"0.0")&" MWp (Base y Custom); × "&TEXT(INDEX(Esc_Factor_CAPEX,2),"0.00")&" en el Conservador; "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4),"0.00")&" $/Wp fijo en el Favorable; escala por drivers Wp/Wac/fijo"', '=TEXT(OPEX_Anio1/1000,"#,##0")&" k (fee O&M "&TEXT(Fee_OM_kWp*Potencia_DC/1000,"0")&" k + seguros "&TEXT(Seguro_kWp*Potencia_DC/1000,"0.0")&" k + arriendo/predial + tributos "&TEXT(Tributos_Locales/1000,"0")&" k)"', "IR 25 % + participación 15 %; deducción adicional topada al 5 % de ingresos; IVA recuperable; ISD/arancel explícitos; peaje 2029 parametrizado; IDC sobre ambos tramos", "Ver 00_Portada (Custom con la tira C · B · F) y 10 §A (los cuatro casos)")],
                   [2, 3, 4, 5, 6], [9, 8.5, 8.5, 8.5, 8.5])
    callout(ws, r, 2, 6, "Por qué cambian los resultados frente a los libros previos: (1) participación laboral 15 % (−≈0,9 pp de TIR); (2) OPEX de SALELGI incluye arriendo del terreno y seguros del dueño (+50 k/año vs 100 k); (3) tarifa evitable 0,1127 vs 0,1114 (+); (4) CAPEX sin IVA y sin margen EPC (−) pero con gerencia 7 % (+); (5) deducción adicional topada (neutral con ingresos ≈ 10 M); (6) fases 30/70 y VAN referido al COD.")
    r += 2
    section(ws, r, 2, 6, "D · Fuentes (fecha de verificación) — con enlace cuando existe")
    r += 1
    for txt, url in FUENTES:
        c = note(ws, r, 2, "• " + txt, c2=(5 if url else 6), size=9)
        if url:
            h = ws.cell(row=r, column=6, value="abrir ↗"); h.hyperlink = url; h.font = Font(name=FONT, size=9, color=TERRACOTA, underline="single"); h.alignment = Alignment(horizontal="right", vertical="top")
        fit_row(ws, r, [(txt, 128 if url else 150, 9)], min_h=14)
        r += 1
    r += 1
    section(ws, r, 2, 6, "E · Convenciones e historial")
    r += 1
    for t in ["USD nominal (economía dolarizada) · español · Calibri · sin macros ni VBA · fórmulas nativas Excel 2007+ (compatibles con LibreOffice) · rangos con nombre para todos los parámetros (cero números mágicos).",
              "Colores: texto tinta = entrada editable, sin relleno (01_Supuestos; 05_CAPEX columnas D/E/G/I/O y drivers S:U; 03_Tramites inicio/duración/costo; 10 parámetros; 11 prob./impacto) · «· por confirmar» con subrayado punteado = supuesto sin fuente firme · texto grafito = enlace entre hojas, unidades, notas y valores canónicos · carbón = fórmula · terracota = acento del dato que decide · ladrillo / arcilla en el texto = bajo el umbral (TIR < tasa de descuento, VAN < 0, DSCR < 1,00x / < objetivo) · ● ok / ▲ pendiente / ■ riesgo / ◇ informativo. Colores de caso (sólo donde hay más de un caso a la vista: cabeceras, series, tira, leyenda, ◆): ciruela = Custom · índigo = Conservador · petróleo = Base · verde bosque = Favorable; nunca como fondo de tabla.",
              "Historial: v1.0 (01-sep-2026) modelo completo · v1.1 (01-sep-2026) rediseño visual «minimalismo tierra» · v1.2 (02-sep-2026) auditoría integral (65 tie-outs, sombra a 10⁻¹³), dimensionamiento por MWp y ratio DC/AC, CAPEX por drivers, comprador del terreno, IDC, 13_Controles · v1.3 (03-sep-2026) portada de dos páginas, guía 00b, panel de mandos, series a escala fija, impresión verificada en Excel/Mac; motor intacto · v2.0 (04-sep-2026) arquitectura de casos: Custom que gobierna el libro y Conservador · Base · Favorable definidos en el bloque B y calculados en el Motor (99 casos); CAPEX fijo $/Wp; potencia como lista 5–8 MWp; controles G1–G6 · v3.0 (sep-2026) ronda 2 de motor: escalación del CAPEX hasta la compra, disponibilidad y degradación adicional, peaje por potencia, reemplazo de inversores y desmantelamiento, pool de pérdidas (art. 11 LRTI), IDC × meses de construcción de 03, tasa del accionista, payback robusto; bloque B de 8 filas; 110 casos (tornado de 14 barras, puente en 10 §A.3); controles H1–H13 e I1–I3; Base realista moderado (98 % · 3 %/año · reemplazo SALELGI en t = 13 · 21 meses · tasa del accionista 12 %) con la definición v2.0 reproducible en neutro · v3.1 (08-sep-2026) actualización legal conciliada con el Atlas Regulatorio FV Ecuador v2.0 (doc 18): 02 con 25 normas (Ley 2026, Sentencia CC, retenciones 2026, suelo rural, servidumbres; ARCONEL como autoridad ambiental; D.E. 32 al 18-dic-2026; medición 008/24; cifras en fórmula) y 15 zonas grises con los pendientes P-xx; 03 con Registro Ambiental, pre-consulta de capacidad, factibilidad en los meses 7–8 (vigencia 6 meses, control F12), RC-08a/b/c, RC-15 y memo estático de escenarios; 11 con 15 riesgos (red ↑, certificación de la deducción); 12 con las fuentes del Atlas y BCE ago-2026; Motor con el parámetro «deducción adicional aplicable» (caso 111 «Sin deducción adicional», barra 15 del tornado, control H14); Custom con los diez valores fijados por Jorge el 04-sep-2026 (SALELGI compra el terreno, peaje 0, tarifa +2 %/año, disponibilidad 97 %, escalación del CAPEX 0, degradación 1 %/año, fee O&M 16, OPEX +2 %/año, deuda 100 % al 7,5 %); Meses_Construccion vuelve a leer Mes_COD_Cron. Elaborado por Claude (Anthropic) para Exergy EXG S.A.S. bajo las decisiones de Jorge A. Baquerizo (01-sep a la fecha de corte). Documento de trabajo interno; no constituye oferta ni opinión legal."]:
        note(ws, r, 2, "• " + t, c2=6, size=9); fit_row(ws, r, [(t, 150, 9)], min_h=14); r += 1
    setup_print(ws, landscape=True, scale=80)
    return ws


# ---------------------------------------------------------------- 00_Portada
INDEX = [(S1, "Supuestos (editable)"), (S2, "Marco legal"), (S3, "Trámites y Gantt"), (S4, "Energía y recorte"),
         (S5, "CAPEX y drivers"), (S6, "OPEX SALELGI"), (S7, "Fiscal"), (S8, "Flujo ± deuda"), (S9, "Exergy"),
         (S10, "Sensibilidad"), (S11, "Riesgos"), (S12, "Fuentes y QC"), (S13, "Controles"), (SM, "Motor de casos (cálculo)")]


# build_portada (v1.1) eliminado en v2.0: 00_Portada se construye en build_portada20.py


def build_controles(wb, motor_fcf_base_terms):
    POOL_TERMS = ("+".join(f"ABS('{S7}'!{C(t)}{FISCAL['pool']}-'{SM}'!$B${brow('PoolU', t)})" for t in TS) + "+"
                  + "+".join(f"ABS('{S7}'!{C(t)}{FISCAL['pool_l']}-'{SM}'!$B${brow('PoolL', t)})" for t in TS))   # H5 sin TRANSPOSE (Excel/Mac)
    ws = wb.create_sheet(S13)
    widths(ws, {"A": 2, "B": 64, "C": 7, "D": 16, "E": 18, "F": 34})   # 141 caracteres → ajuste al ancho ≈ 90 %
    sheet_header(ws, "13 · Controles", "Único control de calidad: identidades contables, candados regulatorios y de rango (A–F, incl. F12 vigencia de la factibilidad), casos (G), ronda 2 y v3.1 (H) y libro (I). Todo debe estar en ●; ■ = inconsistencia o entrada fuera de rango; la portada lee el contador.", 13, last_col=6, total=NSHEETS)
    F, Fz, E, K, O, X = FLUJO, FISCAL, ENERGIA, CAPEX, OPEX, EXERGY
    S8_, S7_, S6_, S4_, S5_, S9_, SM_ = f"'{S8}'!", f"'{S7}'!", f"'{S6}'!", f"'{S4}'!", f"'{S5}'!", f"'{S9}'!", f"'{SM}'!"

    def sabs(row_a, sheet_a, row_b, sheet_b, sign=1):
        return f"SUMPRODUCT(ABS({sheet_a}{rng(row_a)}-({sign})*{sheet_b}{rng(row_b)}))"

    def ok1(expr, tol="1"):
        return f'=IF({expr}<{tol},"● ok","■ Δ = "&TEXT({expr},"#,##0.00"))'
    r0k = K["r0"]; rl = K["r0"] + 8
    checks = [
        ("A · CAPEX", None),
        ("A1", "Subtotal EPC = Σ rubros 1-9 + contingencia", ok1(f"ABS(SUM({S5_}$N${r0k}:$N${rl})+{S5_}$N${K['cont']}-Subtotal_EPC)")),
        ("A2", "Contingencia = % × Σ rubros 1-9", ok1(f"ABS({S5_}$N${K['cont']}-Contingencia_Pct*SUM({S5_}$N${r0k}:$N${rl}))")),
        ("A3", "Fee de gerencia = % × subtotal EPC; CAPEX industrial = subtotal + fee", ok1(f"ABS(Fee_Gerencia_USD-Fee_Gerencia_Pct*Subtotal_EPC)+ABS(CAPEX_Total-Subtotal_EPC-Fee_Gerencia_USD)")),
        ("A4", "Capitalizable por rubro = costo + FODINFA + arancel + ISD (según contrato)", ok1(f"SUMPRODUCT(ABS({S5_}$N${r0k}:$N${rl}-{S5_}$F${r0k}:$F${rl}-{S5_}$K${r0k}:$K${rl}-{S5_}$M${r0k}:$M${rl}))")),
        ("A5", "IVA por rubro = base IVA × % IVA; IVA total = Σ rubros + contingencia + fee", ok1(f"ABS(IVA_Total-SUM({S5_}$P${r0k}:$P${K['cont']})-{S5_}$P${K['fee']})")),
        ("A6", "Drivers de escala suman 100 % en cada rubro", "=Check_Drivers"),
        ("A7", "Descomposición Wp/Wac/fijo reproduce el CAPEX a factor 1 (sin y con contrato)", ok1(f"ABS(CAPEX_SC_Wp+CAPEX_SC_Wac+CAPEX_SC_Fijo-CAPEX_SC_f1)+ABS(CAPEX_CC_Wp+CAPEX_CC_Wac+CAPEX_CC_Fijo-CAPEX_CC_f1)+ABS(IVA_SC_Wp+IVA_SC_Wac+IVA_SC_Fijo-IVA_SC_f1)+ABS(IVA_CC_Wp+IVA_CC_Wac+IVA_CC_Fijo-IVA_CC_f1)")),
        ("A8", "Motor (columna Custom) CAPEX e IVA = 05_CAPEX", ok1(f"ABS({SM_}$B${SCAL_ROWS['K']}-CAPEX_Total)+ABS({SM_}$B${SCAL_ROWS['IVA']}-IVA_Total)")),
        ("A9", "Terreno de SALELGI = precio × ha × (1 + transacción) sólo si compra SALELGI", ok1(f'ABS(Terreno_SALELGI-IF(Comprador_Terreno="SALELGI",Precio_Terreno_ha*Hectareas*(1+Costos_Transaccion_Terreno_Pct),0))')),
        ("B · Energía", None),
        ("B1", "Fracciones por bloque suman 100 %", '=IF(ABS(Frac_A+Frac_B+Frac_C-1)<0.0005,"● ok","■ revisar")'),
        ("B2", "Perfil mensual suma 100 %; Σ producción mensual = producción anual año 1 (P50)", ok1(f"ABS(SUM(Perfil_Mensual)-1)*1000+ABS({S4_}$E${E['t2_tot']}-{S4_}${C(1)}${E['p50']})", tol="0.5")),
        ("B3", "Valor evitado mensual (Σ) = ahorro fiscal del año 1 (Custom con P50)", f'=IF(Eff_Scen<>1,"● n/a (Custom con P90)",IF(ABS(Ahorro_Mensual_Anio1-{S7_}${C(1)}${Fz["ahorro"]})<1,"● ok","■ Δ = "&TEXT(Ahorro_Mensual_Anio1-{S7_}${C(1)}${Fz["ahorro"]},"#,##0")))'),
        ("B4", "Energía año 1 = Potencia_DC × Yield_Ref × F_Recorte × Disponibilidad (P50)", ok1(f"ABS({S4_}${C(1)}${E['p50']}-Potencia_DC/1000*Yield_Ref*F_Recorte*Disponibilidad)", tol="0.01")),
        ("B5", "Art. 9: producción año 1 ≤ demanda anual (energía no reconocida = 0)", f'=IF({S4_}${C(1)}${E["norec"]}<0.5,"● ok","■ "&TEXT({S4_}${C(1)}${E["norec"]},"#,##0")&" MWh no reconocidos")'),
        ("B6", "Art. 27: sin excedentes mensuales", f'=IF(COUNTIF({S4_}$K${E["t2_0"]}:$K${E["t2_0"]+11},"SÍ")=0,"● ok","▲ "&COUNTIF({S4_}$K${E["t2_0"]}:$K${E["t2_0"]+11},"SÍ")&" meses con excedente")'),
        ("B7", "Factor de recorte = 1 al ratio de referencia", f'=IF(ABS(Ratio_DCAC-Ratio_Ref)<0.001,IF(ABS(F_Recorte-1)<0.000001,"● ok","■ F ≠ 1"),"● n/a (ratio ≠ referencia): F = "&TEXT(F_Recorte,"0.0000"))'),
        ("C · OPEX y fiscal", None),
        ("C1", "OPEX total = Σ líneas (fee, seguros, arriendo, predial, tributos)", ok1(f"SUMPRODUCT(ABS({S6_}{rng(O['total'])}-{S6_}{rng(O['fee'])}-{S6_}{rng(O['seg'])}-{S6_}{rng(O['arr'])}-{S6_}{rng(O['pred'])}-{S6_}{rng(O['trib'])}))")),
        ("C2", "OPEX año 1 = (fee + seguro) × kWp + arriendo o predial + tributos", ok1(f'ABS(OPEX_Anio1-((Fee_OM_kWp+Seguro_kWp)*Potencia_DC+IF(Comprador_Terreno="SALELGI",Predial_Terreno,Renta_Terreno_ha*Hectareas)+Tributos_Locales))')),
        ("C3", "Arriendo y predial según el comprador (año 1)", f'=IF(Comprador_Terreno="SALELGI",IF(AND({S6_}${C(1)}${O["arr"]}=0,ABS({S6_}${C(1)}${O["pred"]}-Predial_Terreno)<0.01),"● ok","■ revisar"),IF(AND({S6_}${C(1)}${O["pred"]}=0,ABS({S6_}${C(1)}${O["arr"]}-Renta_Terreno_ha*Hectareas)<0.01),"● ok","■ revisar"))'),
        ("C4", "EBITDA = ahorro − OPEX − peaje − desmantelamiento", ok1(f"SUMPRODUCT(ABS({S7_}{rng(Fz['ebitda'])}-{S7_}{rng(Fz['ahorro'])}+{S7_}{rng(Fz['opex'])}+{S7_}{rng(Fz['peaje'])}+{S7_}{rng(Fz['decom'])}))")),
        ("C5", "Σ depreciación (equipos + civil + reemplazo) = CAPEX depreciable + reemplazo pagado por SALELGI (horizonte ≥ 20 años)", f'=IF(Horizonte<Vida_Fiscal_Civil,"● n/a (horizonte < vida civil)",IF(ABS(SUM({S7_}{rng(Fz["depeq"])})+SUM({S7_}{rng(Fz["depciv"])})+SUM({S7_}{rng(Fz["deprep"])})-CAPEX_Depreciable-IF(AND(Reemplazo_Pagador="SALELGI",Reemplazo_Anio<Horizonte),Reemplazo_USD,0))<1,"● ok","■ revisar"))'),
        ("C6", "Deducción adicional ≤ tope y sólo en t = 1…vida equipos", f'=IF(AND(SUMPRODUCT(--({S7_}{rng(Fz["dedad"])}>Tope_DedAd_Pct*Ingresos_SALELGI+0.01))=0,COUNTIF({S7_}{rng(Fz["dedad"])},">0")<=Vida_Fiscal_Equipos),"● ok","■ revisar")'),
        ("C7", "Impuestos = participación + IR (sin y con deuda)", ok1(f"SUMPRODUCT(ABS({S7_}{rng(Fz['imp'])}-{S7_}{rng(Fz['part'])}-{S7_}{rng(Fz['ir'])}))+SUMPRODUCT(ABS({S7_}{rng(Fz['imp_l'])}-{S7_}{rng(Fz['part_l'])}-{S7_}{rng(Fz['ir_l'])}))")),
        ("C8", "Participación = 15 % × utilidad antes de participación (con escudo ilimitado)", f'=IF(Incluir_Participacion="No","● n/a (participación excluida)",IF(ISNUMBER(Utilidad_Gravable_SALELGI),"● n/a (absorción limitada a la utilidad gravable: ver H4)",IF(Escudo_Negativo="No","● n/a (sin escudo: piso en 0)",IF(SUMPRODUCT(ABS({S7_}{rng(Fz["part"])}-Tasa_Participacion*{S7_}{rng(Fz["utap"])}))<1,"● ok","■ revisar"))))'),
        ("C9", "IVA pagado (Σ) = IVA recuperado (Σ) = IVA total (si recuperable)", f'=IF(IVA_Recuperable="No",IF(SUM({S7_}{rng(Fz["iva_rec"])})=0,"● ok (no recuperable)","■ revisar"),IF(ABS(SUM({S7_}{rng(Fz["iva_pag"])})-SUM({S7_}{rng(Fz["iva_rec"])}))+ABS(SUM({S7_}{rng(Fz["iva_pag"])})-IVA_Total)<1,"● ok","■ revisar"))'),
        ("D · Flujo y deuda", None),
        ("D1", "FCF = Σ componentes (CAPEX, terreno, IVA ±, ahorro, OPEX, peaje, impuestos, reemplazo, residual)", ok1(f"SUMPRODUCT(ABS({S8_}{rng(F['fcf'])}-{S8_}{rng(F['capex'])}-{S8_}{rng(F['terr'])}-{S8_}{rng(F['iva_pag'])}-{S8_}{rng(F['iva_rec'])}-{S8_}{rng(F['ahorro'])}-{S8_}{rng(F['opex'])}-{S8_}{rng(F['peaje'])}-{S8_}{rng(F['imp'])}-{S8_}{rng(F['rep'])}-{S8_}{rng(F['resid'])}))")),
        ("D2", "Σ CAPEX en el flujo = −CAPEX industrial; Σ terreno = −Terreno_SALELGI", ok1(f"ABS(SUM({S8_}{rng(F['capex'])})+CAPEX_Total)+ABS(SUM({S8_}{rng(F['terr'])})+Terreno_SALELGI)")),
        ("D3", "Acumulado_t = acumulado_{t−1} + FCF_t", ok1(f"ABS({S8_}${C(25)}${F['acum']}-SUM({S8_}{rng(F['fcf'])}))")),
        ("D4", "VAN (KPI) = FCF₋₁(1+r) + FCF₀ + Σ FCF_t/(1+r)^t", ok1(f"ABS(VAN_Proyecto-SUMPRODUCT({S8_}{rng(F['fcf'],1,25)},{S8_}{rng(F['df'],1,25)})-{S8_}${C(-1)}${F['fcf']}*(1+Tasa_Descuento)-{S8_}${C(0)}${F['fcf']})")),
        ("D5", "VAN a la TIR ≈ 0 (autochequeo IRR/NPV)", f'=IF(ISNUMBER(TIR_Proyecto),IF(ABS({S8_}${C(-1)}${F["fcf"]}*(1+TIR_Proyecto)+{S8_}${C(0)}${F["fcf"]}+NPV(TIR_Proyecto,{S8_}{rng(F["fcf"],1,25)}))<100,"● ok","■ revisar"),"● n/a (sin TIR)")'),
        ("D6", "Deuda = apalancamiento × (CAPEX industrial [+ terreno]); IDC = D × tasa × (fase₋₁ + fase₀ × fracción) × meses de construcción / 12", ok1(f'ABS(Deuda_Monto-Pct_Apalancamiento*(CAPEX_Total+IF(Deuda_Financia_Terreno="Sí",Terreno_SALELGI,0)))+ABS(IDC-Deuda_Monto*Tasa_Deuda*(Fase_m1+(1-Fase_m1)*IDC_Frac_Tramo0)*Meses_Construccion/12)')),
        ("D7", "Saldo final = saldo inicial + desembolso + IDC − amortización; saldo al fin del plazo = 0", ok1(f"SUMPRODUCT(ABS({S8_}{rng(F['saldo_fin'])}-{S8_}{rng(F['saldo_ini'])}-{S8_}{rng(F['desemb'])}-{S8_}{rng(F['idc'])}+{S8_}{rng(F['amort'])}))+ABS(INDEX({S8_}{rng(F['saldo_fin'])},1,MIN(Plazo_Deuda,Horizonte)+2))")),
        ("D8", "Intereses = saldo inicial × tasa (t = 1…plazo); servicio = intereses + amortización", ok1(f"SUMPRODUCT(ABS({S8_}{rng(F['int'],1,25)}-{S8_}{rng(F['saldo_ini'],1,25)}*Tasa_Deuda*({S8_}{rng(F['t'],1,25)}<=Plazo_Deuda)))+SUMPRODUCT(ABS({S8_}{rng(F['serv'])}-{S8_}{rng(F['int'])}-{S8_}{rng(F['amort'])}))")),
        ("D9", "Cuota francesa constante en t = gracia+1…plazo (Σ amortización = deuda total)", f'=IF(Deuda_Monto=0,"● n/a (sin deuda)",IF(ABS(SUM({S8_}{rng(F["amort"])})-Deuda_Total)<1,"● ok","■ Δ = "&TEXT(SUM({S8_}{rng(F["amort"])})-Deuda_Total,"#,##0")))'),
        ("D10", "CFADS = EBITDA − impuestos con deuda + IVA recuperado + residual − reemplazo (t ≥ 1)", ok1(f"SUMPRODUCT(ABS({S8_}{rng(F['cfads'],1,25)}-{S7_}{rng(Fz['ebitda'],1,25)}+{S7_}{rng(Fz['imp_l'],1,25)}-{S7_}{rng(Fz['iva_rec'],1,25)}-{S8_}{rng(F['resid'],1,25)}-{S8_}{rng(F['rep'],1,25)}))")),
        ("D11", "Equity = FCF + desembolsos (t ≤ 0); CFADS − servicio (t ≥ 1)", ok1(f"SUMPRODUCT(ABS({S8_}{rng(F['eq'],-1,0)}-{S8_}{rng(F['fcf'],-1,0)}-{S8_}{rng(F['desemb'],-1,0)}))+SUMPRODUCT(ABS({S8_}{rng(F['eq'],1,25)}-{S8_}{rng(F['cfads'],1,25)}+{S8_}{rng(F['serv'],1,25)}))")),
        ("D12", "Motor (columna Custom) reproduce el FCF de 08_Flujo", f'=IF(({motor_fcf_base_terms})<1,"● ok","■ diferencia")'),
        ("D13", "Motor (columna Custom) reproduce el equity (Σ, VAN, aporte) y el DSCR mínimo de 08_Flujo", ok1(f"ABS(SUM({SM_}$B${brow('EQ',-1)}:$B${brow('EQ',25)})-SUM({S8_}{rng(F['eq'])}))+ABS({SM_}$B${OUT_ROWS['VAN_eq']}-VAN_Equity)+ABS({SM_}$B${OUT_ROWS['Aporte_eq']}-Aporte_Equity)+IF(Deuda_Monto>0,ABS({SM_}$B${OUT_ROWS['DSCR_min']}-DSCR_Min)*1000,0)")),
        ("E · Exergy y grupo", None),
        ("E1", "Fee cobrado por Exergy = fee del CAPEX; arriendo y fee O&M cobrados = pagados por SALELGI", ok1(f"ABS(SUM({S9_}{rng(X['fee'])})-Fee_Gerencia_USD)+SUMPRODUCT(ABS({S9_}{rng(X['arr'])}-{S6_}{rng(O['arr'])}))+SUMPRODUCT(ABS({S9_}{rng(X['feeom'])}-{S6_}{rng(O['fee'])}))")),
        ("E2", "Utilidad Exergy = Σ líneas (incl. reemplazo a su cargo); FCF = utilidad + impuestos + terreno + residual", ok1(f"SUMPRODUCT(ABS({S9_}{rng(X['util'])}-{S9_}{rng(X['fee'])}-{S9_}{rng(X['costo'])}-{S9_}{rng(X['arr'])}-{S9_}{rng(X['predial'])}-{S9_}{rng(X['feeom'])}-{S9_}{rng(X['costoom'])}-{S9_}{rng(X['rep'])}))+SUMPRODUCT(ABS({S9_}{rng(X['fcf'])}-{S9_}{rng(X['util'])}-{S9_}{rng(X['imp'])}-{S9_}{rng(X['terreno'])}-{S9_}{rng(X['resid'])}))")),
        ("E3", "Impuestos Exergy = −tasa × MAX(0, utilidad)", ok1(f"SUMPRODUCT(ABS({S9_}{rng(X['imp'])}+Tasa_Efectiva_Exergy*(({S9_}{rng(X['util'])}>0)*{S9_}{rng(X['util'])})))")),
        ("E4", "Línea terreno de Exergy existe sólo si Exergy compra (compra = −precio × ha × (1 + transacción))", f'=IF(Comprador_Terreno="Exergy",IF(ABS(SUM({S9_}{rng(X["terreno"])})+Precio_Terreno_ha*Hectareas*(1+Costos_Transaccion_Terreno_Pct))<0.01,"● ok","■ revisar"),IF(ABS(SUM({S9_}{rng(X["terreno"])}))+ABS(SUM({S9_}{rng(X["arr"])}))+ABS(SUM({S9_}{rng(X["predial"])}))+ABS(SUM({S9_}{rng(X["resid"])}))<0.01,"● ok","■ revisar"))'),
        ("E5", "Grupo = SALELGI + Exergy (los pagos intragrupo se cancelan)", ok1(f"SUMPRODUCT(ABS({S9_}{rng(X['g_tot'])}-{S8_}{rng(F['fcf'])}-{S9_}{rng(X['fcf'])}))")),
        ("E6", "Motor (columna Custom) reproduce el FCF de Exergy (Σ nominal y VAN) y la TIR del grupo", ok1(f"ABS(SUM({SM_}$B${brow('Fx',-1)}:$B${brow('Fx',25)})-Nominal_Exergy)+ABS({SM_}$B${OUT_ROWS['VAN_X']}-VAN_Exergy)+IF(AND(ISNUMBER({SM_}$B${OUT_ROWS['TIR_G']}),ISNUMBER(TIR_Grupo)),ABS({SM_}$B${OUT_ROWS['TIR_G']}-TIR_Grupo)*1000000,0)")),
        ("F · Rango de entradas y candados", None),
        ("F1", "Plazo de la deuda > gracia", '=IF(Plazo_Deuda>Gracia_Deuda,"● ok","■ plazo ≤ gracia: la deuda se paga en un solo pago (bullet) — revisar")'),
        ("F2", "Plazo de la deuda ≤ horizonte", '=IF(Plazo_Deuda<=Horizonte,"● ok","■ la deuda vence después del horizonte")'),
        ("F3", "Tasa de deuda ≥ 0; apalancamiento entre 0 y 100 %", '=IF(AND(Tasa_Deuda>=0,Pct_Apalancamiento>=0,Pct_Apalancamiento<=1),"● ok","■ fuera de rango")'),
        ("F4", "Potencia AC ≤ capacidad aprobable del alimentador (art. 7.a)", '=IF(Potencia_AC<=Capacidad_Alimentador_kW,"● ok ("&TEXT(Potencia_AC,"#,##0")&" ≤ "&TEXT(Capacidad_Alimentador_kW,"#,##0")&" kW, por confirmar)","■ "&TEXT(Potencia_AC,"#,##0")&" kW > "&TEXT(Capacidad_Alimentador_kW,"#,##0")&" kW")'),
        ("F5", "Hectáreas requeridas ≤ disponibles", '=IF(Hectareas<=Ha_Disponibles,"● ok ("&TEXT(Hectareas,"0.0")&" ≤ "&TEXT(Ha_Disponibles,"0.00")&" ha)","■ "&TEXT(Hectareas,"0.0")&" ha > "&TEXT(Ha_Disponibles,"0.00")&" ha")'),
        ("F6", "Tope regulatorio de potencia (si está definido)", '=IF(OR(Tope_SGDA_kW="",Tope_SGDA_kW=0),"● sin tope en la 005/24 codificada",IF(Potencia_AC<=Tope_SGDA_kW,"● ok","■ supera el tope"))'),
        ("F7", "Ratio DC/AC dentro de la curva de recorte (1,00–1,60)", '=IF(AND(Ratio_DCAC>=INDEX(CR_Ratio,1),Ratio_DCAC<=INDEX(CR_Ratio,ROWS(CR_Ratio))),"● ok","▲ fuera de la curva: se usa el extremo")'),
        ("F8", "Cronograma coherente con Fecha_COD", "=Check_Cron"),
        ("F9", "Cronograma valorado cabe en el rubro 9", "=Check_Tramites"),
        ("F10", "Custom frente al Base (bloque B y capa de diseño de 01)", "=Estado_Custom"),
        ("F11", "Cero errores en los KPI principales", '=IF(ISERROR(VAN_Proyecto+VAN_Equity+VAN_Exergy+P90_VAN+C_VAN+B_VAN+F_VAN),"■ error","● ok")'),
        ("F12", "Vigencia de la Factibilidad de Conexión (6 meses, 005/24 art. 13): el Certificado de Habilitación (RC-10) termina ≤ 6 meses después de la factibilidad (RC-09)", '=IF(Fin_RC10-Fin_RC09<=6,"● ok ("&(Fin_RC10-Fin_RC09)&" meses)","■ "&(Fin_RC10-Fin_RC09)&" meses > 6: la factibilidad vence antes de la habilitación — reordenar 03")'),
        ("G · Casos", None),
        ("G1", "Custom ≡ Base ⇒ KPI idénticos (TIR, VAN, VAN Exergy) en el Motor", '=IF(N_Custom_vs_Base>0,"● n/a (Custom ≠ Base en "&N_Custom_vs_Base&" entrada(s))",IF(AND(ABS(X_VAN-B_VAN)<1,ABS(X_VANX-B_VANX)<1,IF(AND(ISNUMBER(X_TIR),ISNUMBER(B_TIR)),ABS(X_TIR-B_TIR)<0.000001,TRUE)),"● ok","■ Custom = Base en entradas pero KPI distintos — revisar el Motor"))'),
        ("G2", "Potencia DC en la lista 5.000 / 6.000 / 7.000 / 8.000 kWp", '=IF(OR(Potencia_DC=5000,Potencia_DC=6000,Potencia_DC=7000,Potencia_DC=8000),"● ok ("&TEXT(Potencia_DC,"#,##0")&" kWp)","■ "&TEXT(Potencia_DC,"#,##0")&" kWp fuera de la lista (mínimo 5.000)")'),
        ("G3", "Bloque B dentro de rango: energía P50/P90, factores 0,5–2, CAPEX fijo vacío o 0,3–2 $/Wp, peaje 0–0,05, escalación 0–10 %", '=IF(AND(SUMPRODUCT(--(Esc_Energia="P50"))+SUMPRODUCT(--(Esc_Energia="P90"))=4,MIN(Esc_Factor_CAPEX)>=0.5,MAX(Esc_Factor_CAPEX)<=2,MIN(Esc_Factor_OPEX)>=0.5,MAX(Esc_Factor_OPEX)<=2,SUMPRODUCT((Esc_CAPEX_Fijo_Wp<>"")*(Esc_CAPEX_Fijo_Wp<>0)*((Esc_CAPEX_Fijo_Wp<0.3)+(Esc_CAPEX_Fijo_Wp>2)))=0,MIN(Esc_Peaje)>=0,MAX(Esc_Peaje)<=0.05,MIN(Esc_EscTarifa)>=0,MAX(Esc_EscTarifa)<=0.1),"● ok","■ algún supuesto del bloque B está fuera de rango")'),
        ("G4", "Escenarios fijos (Conservador · Base · Favorable) en su definición entregada", "=Estado_Entregado"),
        ("G5", "Horizonte ≤ 25 años (los vectores anuales del libro llegan a t = 25)", '=IF(Horizonte<=25,"● ok ("&Horizonte&" años)","■ Horizonte "&Horizonte&" > 25: las series se truncan en t = 25 (resultados no válidos)")'),
        ("G6", "Motor: los casos C/B/F leen el bloque B (energía, factor CAPEX, fijo, OPEX, peaje, escalación de tarifa, disponibilidad, escalación del CAPEX)", ok1(f"ABS({SM_}$C${PARAM_ROWS['fK']}-INDEX(Esc_Factor_CAPEX,2))+ABS({SM_}$D${PARAM_ROWS['fK']}-INDEX(Esc_Factor_CAPEX,3))+ABS({SM_}$E${PARAM_ROWS['kfix']}-N(INDEX(Esc_CAPEX_Fijo_Wp,4)))+ABS({SM_}$C${PARAM_ROWS['fO']}-INDEX(Esc_Factor_OPEX,2))+ABS({SM_}$C${PARAM_ROWS['pj']}-INDEX(Esc_Peaje,2))+ABS({SM_}$E${PARAM_ROWS['escT']}-INDEX(Esc_EscTarifa,4))+ABS({SM_}$C${PARAM_ROWS['scen']}-IF(INDEX(Esc_Energia,2)=\"P50\",1,2))+ABS({SM_}$C${PARAM_ROWS['disp']}-INDEX(Esc_Disponibilidad,2))+ABS({SM_}$E${PARAM_ROWS['disp']}-INDEX(Esc_Disponibilidad,4))+ABS({SM_}$C${PARAM_ROWS['dK']}-INDEX(Esc_Escalacion_CAPEX,2))+ABS({SM_}$D${PARAM_ROWS['dK']}-INDEX(Esc_Escalacion_CAPEX,3))", tol="0.000001")),
        ("H · Ronda 2 (parámetros nuevos del motor)", None),
        # H1/H4/H5 (render r2): sin TRANSPOSE dentro de SUMPRODUCT — Excel/Mac devuelve #VALUE! en fórmulas no matriciales; se compara año a año como D12
        ("H1", "04 energía producida (E_Activa) ≡ Motor bloque E y 07 peaje (energía + potencia) ≡ Motor bloque Peaje (columna Custom)", ok1("(" + "+".join(f"ABS({S4_}{C(t)}{E['activa']}-{SM_}$B${brow('E', t)})" for t in TS) + ")*100+" + "+".join(f"ABS({S7_}{C(t)}{Fz['peaje']}-{SM_}$B${brow('Peaje', t)})" for t in TS))),
        ("H2", "05 CAPEX_Total = bottom-up a factor 1 × Factor_Caso (incl. escalación); Factor_Escalacion de 05 ≡ Motor fEsc (Custom)", ok1(f"ABS(CAPEX_Total-CAPEX_Base_f1*Factor_Caso)+ABS(Factor_Escalacion-{SM_}$B${SCAL_ROWS['fEsc']})*1000000")),
        ("H3", "Reemplazo 05 (Reemplazo_USD) ≡ Motor Krep y Σ fila de 08 (si paga SALELGI) ≡ Σ bloque Krep; desmantelamiento 05 ≡ Motor Decom (Custom)", ok1(f'ABS(IF(Reemplazo_Pagador="No",0,Reemplazo_USD)-{SM_}$B${SCAL_ROWS["Krep"]})+ABS(SUM({S8_}{rng(F["rep"])})-SUM({SM_}$B${brow("Krep",-1)}:$B${brow("Krep",25)}))+ABS(SUM({S9_}{rng(X["rep"])})+IF(Reemplazo_Pagador="Exergy",Reemplazo_USD,0))+ABS(Desmantelamiento_USD-{SM_}$B${SCAL_ROWS["Decom"]})')),
        ("H4", "07 impuestos (participación + IR, sin y con deuda) ≡ Motor bloques Part_u + IR_u y Part_l + IR_l (Custom)", ok1("+".join(f"ABS({S7_}{C(t)}{Fz['imp']}-{SM_}$B${brow('Part_u', t)}-{SM_}$B${brow('IR_u', t)})" for t in TS) + "+" + "+".join(f"ABS({S7_}{C(t)}{Fz['imp_l']}-{SM_}$B${brow('Part_l', t)}-{SM_}$B${brow('IR_l', t)})" for t in TS))),
        ("H5", "Pool de pérdidas ≥ 0 en 07 y en el Motor; 07 ≡ Motor; saldo al final del horizonte declarado", f'=IF(MIN({S7_}{rng(Fz["pool"])},{S7_}{rng(Fz["pool_l"])},{SM_}$B${brow("PoolU",-1)}:$B${brow("PoolU",25)},{SM_}$B${brow("PoolL",-1)}:$B${brow("PoolL",25)})<-0.01,"■ pool negativo",IF({POOL_TERMS}>1,"■ pool de 07 ≠ Motor",IF(ISNUMBER(Utilidad_Gravable_SALELGI),"● ok · saldo no amortizado en t = "&Horizonte&": sin deuda "&TEXT({S7_}${C(25)}${Fz["pool"]},"#,##0")&" · con deuda "&TEXT({S7_}${C(25)}${Fz["pool_l"]},"#,##0")&" (pool simple sin caducidad, 12 §B)","● n/a (utilidad gravable ilimitada: sin pool)")))'),
        ("H6", "Payback robusto (último cruce) ≡ payback simple (primer cruce) cuando el acumulado cruza una sola vez", f'=IF(COUNTIF({S8_}{rng(F["acum"])},"<0")=SUMPRODUCT(MAX(({S8_}{rng(F["acum"])}<0)*(COLUMN({S8_}{rng(F["acum"])})-COLUMN({S8_}${C(-1)}${F["acum"]})+1))),IF(OR(NOT(ISNUMBER(Payback_Simple)),ABS(Payback_Simple-((COUNTIF({S8_}{rng(F["acum"])},"<0")-2)+(-INDEX({S8_}{rng(F["acum"])},1,COUNTIF({S8_}{rng(F["acum"])},"<0")))/INDEX({S8_}{rng(F["fcf"])},1,COUNTIF({S8_}{rng(F["acum"])},"<0")+1)))<0.000001),"● ok (un solo cruce)","■ payback robusto ≠ simple con un solo cruce"),"● n/a (varios cruces: payback desde el último; hasta t = "&SUMPRODUCT(MAX(({S8_}{rng(F["acum"])}<0)*{S8_}{rng(F["t"])}))&")")'),
        ("H11", "Año del reemplazo entero entre 5 y 24", '=IF(AND(Reemplazo_Anio>=5,Reemplazo_Anio<=24,Reemplazo_Anio=INT(Reemplazo_Anio)),"● ok (t = "&Reemplazo_Anio&")","■ Reemplazo_Anio fuera de 5–24")'),
        ("H7", "Puente v2.0 → v3.0: el último escalón (BR5) ≡ Base y el primero (BR0) ≡ Base con la ronda 2 en neutro (TIR, VAN, TIR acc., VAN Exergy)", ok1(f"ABS({mo(BR5,'VAN')}-B_VAN)+ABS({mo(BR5,'VAN_X')}-B_VANX)+IF(AND(ISNUMBER({mo(BR5,'TIR')}),ISNUMBER(B_TIR)),ABS({mo(BR5,'TIR')}-B_TIR)*1000000,0)+IF(AND(ISNUMBER({mo(BR5,'TIR_eq')}),ISNUMBER(B_TIReq)),ABS({mo(BR5,'TIR_eq')}-B_TIReq)*1000000,0)+ABS({mo(BR5,'VAN_eq')}-B_VANeq)")),
        ("H8", "Bloque B · disponibilidad entre 90 % y 100 % en los cuatro casos", '=IF(AND(MIN(Esc_Disponibilidad)>=0.9,MAX(Esc_Disponibilidad)<=1),"● ok","■ disponibilidad fuera de 90–100 %")'),
        ("H10", "Meses de construcción (de 03, Mes_COD_Cron) entre 6 y 36", '=IF(AND(Meses_Construccion>=6,Meses_Construccion<=36),"● ok ("&Meses_Construccion&" meses)","■ Meses_Construccion = "&Meses_Construccion&" fuera de 6–36: revisar el cronograma de 03")'),
        ("H13", "Tasa de descuento del accionista ≥ tasa de descuento del proyecto", '=IF(Tasa_Descuento_Equity>=Tasa_Descuento-0.000001,"● ok ("&TEXT(Tasa_Descuento_Equity,"0.0%")&")","■ Tasa_Descuento_Equity < Tasa_Descuento")'),
        ("H12", "Peaje por potencia entre 0 y 5 $/kW-mes", '=IF(AND(Peaje_kW_mes>=0,Peaje_kW_mes<=5),"● ok","■ Peaje_kW_mes fuera de 0–5 $/kW-mes")'),
        ("H9", "Bloque B · escalación del CAPEX entre 0 y 15 %/año en los cuatro casos; Fecha_Precios ≤ Fecha_COD", '=IF(AND(MIN(Esc_Escalacion_CAPEX)>=0,MAX(Esc_Escalacion_CAPEX)<=0.15,Fecha_Precios<=Fecha_COD),"● ok","■ escalación fuera de 0–15 % o fecha de precios posterior al COD")'),
        ("H14", "Deducción adicional aplicable (v3.1): Motor DedAd (Custom) ≡ 07 DedAd_Anual; el caso «Sin deducción adicional» tiene DedAd = 0 si Aplica_DedAd = Sí (y la deducción completa si es No)", ok1(f'ABS({SM_}$B${SCAL_ROWS["DedAd"]}-DedAd_Anual)+ABS({SM_}${mcol(T_DEDAD)}${SCAL_ROWS["DedAd"]}-IF(Aplica_DedAd="Sí",0,MIN(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos,Tope_DedAd_Pct*Ingresos_SALELGI)))')),
        ("I · Libro", None),
        ("I1", "P90 < P50 en TIR, VAN y ahorro (Custom con P50 y con P90)", '=IF(AND(P90_TIR<P50_TIR,P90_VAN<P50_VAN,P90_Ahorro1<P50_Ahorro1),"● ok","■ revisar")'),
        ("I2", "Lista de supuestos por confirmar (12 §A) al día", '=IF(N_Por_Confirmar=N_Por_Confirmar_Esperado,"● ok ("&N_Por_Confirmar&")","▲ revisar la lista: "&N_Por_Confirmar&" marcados en el libro, "&N_Por_Confirmar_Esperado&" al entregar")'),
        ("I3", "Alcance de la ronda 2 coherente: Estado_Neutro cuenta los parámetros fuera de neutro (0–9) y su chip lo refleja", '=IF(AND(ISNUMBER(N_Neutro),N_Neutro>=0,N_Neutro<=9,LEFT(Estado_Neutro,1)=IF(N_Neutro=0,"●","◇")),"● ok · "&Estado_Neutro,"■ revisar Estado_Neutro")'),
    ]
    # ordenar los controles de cada grupo por su número (H1…H13)
    import re as _re
    ordered, grp = [], []
    def _flush():
        grp.sort(key=lambda it: int(_re.sub(r"\D", "", it[0]) or 0)); ordered.extend(grp); grp.clear()
    for item in checks:
        if item[1] is None:
            _flush(); ordered.append(item)
        else:
            grp.append(item)
    _flush(); checks = ordered
    r = 5
    hdr(ws, r, 2, 6, ["Control", "#", "Estado", "", "Qué prueba"], height=18)
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=5)
    r += 1
    first = r
    for item in checks:
        if item[1] is None:
            section(ws, r, 2, 6, item[0]); r += 1; continue
        idn, lab, f = item
        label(ws, r, 2, lab, wrap=True, size=9); label(ws, r, 3, idn, bold=True, size=9)
        c = chip(ws, r, 4, f, kind="ok", size=9, c2=5); c.border = B_BOTTOM; ws.cell(row=r, column=5).border = B_BOTTOM
        note(ws, r, 6, "", border=True)
        fit_row(ws, r, [(lab, 70, 9)], min_h=16)
        r += 1
    last = r - 1
    ws.conditional_formatting.add(f"D{first}:D{last}", FormulaRule(formula=[f'LEFT(D{first},1)="■"'], font=Font(color=LADRILLO, bold=True)))
    ws.conditional_formatting.add(f"D{first}:D{last}", FormulaRule(formula=[f'LEFT(D{first},1)="▲"'], font=Font(color=OCRE, bold=True)))
    r += 1
    section(ws, r, 2, 6, "Resumen")
    r += 1
    label(ws, r, 2, "Controles evaluados", bold=True); calc(ws, r, 4, f'=COUNTIF($D${first}:$D${last},"●*")+COUNTIF($D${first}:$D${last},"■*")+COUNTIF($D${first}:$D${last},"▲*")', fmt="0", bold=True); name(wb, "N_Controles", S13, f"$D${r}"); r += 1
    label(ws, r, 2, "Controles en ● (ok o no aplicable)", bold=True); calc(ws, r, 4, f'=COUNTIF($D${first}:$D${last},"●*")', fmt="0", bold=True); name(wb, "N_Controles_OK", S13, f"$D${r}"); r += 1
    label(ws, r, 2, "Controles en ■ (inconsistencia o fuera de rango)", bold=True); calc(ws, r, 4, f'=COUNTIF($D${first}:$D${last},"■*")', fmt="0", bold=True); name(wb, "N_Controles_Fail", S13, f"$D${r}"); r += 1
    label(ws, r, 2, "Estado", bold=True); chip(ws, r, 4, '=IF(N_Controles_Fail=0,"● Controles "&N_Controles_OK&"/"&N_Controles&" en orden","■ "&N_Controles_Fail&" control(es) fallan — ver 13_Controles")', kind="ok", c2=6); name(wb, "Estado_Controles", S13, f"$D${r}")
    setup_print(ws)
    return ws
