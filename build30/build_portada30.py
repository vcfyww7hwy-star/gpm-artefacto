# -*- coding: utf-8 -*-
"""00_Portada v2.0 (tres páginas impresas, una sola hoja en pantalla): la retícula y la lectura de la v1.3 con la arquitectura de casos.
  · las tarjetas muestran el caso Custom (el que gobierna el libro) y, bajo cada una, la tira «C · B · F» con el mismo indicador de los tres
    escenarios fijos (una celda por caso, texto negrita del color del caso; toda cifra es fórmula);
  · el gráfico de flujo acumulado lleva las cuatro series (Custom 2,25 pt ciruela; Conservador y Favorable 1,25 pt; Base punteada) con leyenda en celdas;
  · la página 3 compara los cuatro casos con su definición viva (bloque B de 01) y el estado del Custom y de los escenarios fijos.
Versión anterior (v1.3, D5 versión 5):

Retícula: 24 columnas iguales (B..Y) sobre fondo blanco. Cada bloque responde a una pregunta:
  Página 1 · el tablero
    ¿Qué proyecto es?          título grande · descripción en dos líneas · línea de datos técnicos
    ¿Dónde está cada cosa?     botón «? Guía de lectura» en el título; el índice es el «Mapa del libro» de la página 3 (decisión de Jorge: sin barra arriba)
    ¿Qué dicen los números?    seis tarjetas (héroe = TIR del proyecto) + cuatro tarjetas menores (CAPEX, ahorro año 1, ahorro acumulado, VAN Exergy)
    ¿Qué caso se presenta?     «Caso presentado»: ocho premisas en dos listas (etiqueta · texto), con cifras vivas
    ¿Está sano el libro?       una línea para el usuario del modelo (controles · caso Base · por confirmar)
    ¿Qué lo explica?           dos gráficos (flujo acumulado con etiquetas y año de cruce · tornado con cuadrícula)
  Página 2 · la lectura
    ¿Se puede hacer?           semáforo de condiciones habilitantes con su explicación (régimen, art. 9, comercial, alimentador, peaje, predio)
    ¿Qué concluyo?             seis lecturas: conclusión en negrita + evidencia con cifras vivas
    ¿Dónde está este caso?     escenarios Conservador · Base · Favorable (10 §I) con su definición
Nada lleva relleno salvo bandas de sección y botones; el aire entre bloques es parte del diseño. Ninguna cifra en texto está escrita: todo es fórmula."""
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.pagebreak import Break
from openpyxl.chart import Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.chart.data_source import StrRef
from xl_helpers import *
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from build_core import (S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, SM, C, TS, T_MAX, COL0, LAST_T_COL, FLUJO, ENERGIA, NSHEETS,
                        CASE_KEYS, MOTOR_CASE_COL, brow)
from build_content import CANDADOS, INDEX, CASE_TERR_ALT, T_CAPEX_UP, T_CAPEX_DN
import build_content as BC

NCOL = 24                 # columnas de contenido B..Y
LC = 1 + NCOL             # Y
CARD_W = 4                # 6 tarjetas × 4 columnas (la 4.ª de cada tarjeta es aire)
GUIDE = "00b_Guía"
TX = lambda nm, f: f'IFERROR(TEXT({nm},"{f}"),"n/a")'
AUX0 = 100                # filas auxiliares de los gráficos (fuera del área de impresión)


def esc_def(k, prefix=True):
    """Definición viva del caso k (1 = Custom … 4 = Favorable) leída del bloque B de 01: energía · CAPEX · OPEX · peaje · tarifa."""
    e = lambda nm: f"INDEX({nm},{k})"
    head = f'"{CASO_NOMBRE[CASE_KEYS[k-1]]} · "&' if prefix else ""
    return (f'={head}{e("Esc_Energia")}&" · CAPEX "&IF(N({e("Esc_CAPEX_Fijo_Wp")})>0,"fijo "&TEXT({e("Esc_CAPEX_Fijo_Wp")},"0.00")&" $/Wp","bottom-up × "&TEXT({e("Esc_Factor_CAPEX")},"0.00"))'
            f'&IF({e("Esc_Escalacion_CAPEX")}>0," +"&TEXT({e("Esc_Escalacion_CAPEX")},"0%")&"/año","")&" · OPEX × "&TEXT({e("Esc_Factor_OPEX")},"0.00")&" · peaje "&TEXT({e("Esc_Peaje")}*100,"0.0")&" ¢/kWh desde "&TEXT(Fecha_Peaje,"mmm-yyyy")&" · tarifa "&IF({e("Esc_EscTarifa")}=0,"plana","+"&TEXT({e("Esc_EscTarifa")},"0.0%")&"/año")&" · disp. "&TEXT({e("Esc_Disponibilidad")},"0%")')


def _glyph_cf(ws, rng_, bold=True):
    """Color del texto según el glifo inicial: ● salvia · ▲ arcilla · ■ ladrillo (◇ queda en grafito)."""
    first = rng_.split(":")[0]
    ws.conditional_formatting.add(rng_, FormulaRule(formula=[f'LEFT({first},1)="■"'], font=Font(color=LADRILLO, bold=bold)))
    ws.conditional_formatting.add(rng_, FormulaRule(formula=[f'LEFT({first},1)="▲"'], font=Font(color=ARCILLA, bold=bold)))
    ws.conditional_formatting.add(rng_, FormulaRule(formula=[f'LEFT({first},1)="●"'], font=Font(color=SALVIA, bold=bold)))


def _line(ws, r, c1, c2, formula, size=SZ_TABLE, color=CARBON, bold=False, align="left", height=15, wrap=False, valign="center", border=False):
    c = ws.cell(row=r, column=c1, value=formula)
    c.font = Font(name=FONT, size=size, color=color, bold=bold)
    c.alignment = Alignment(horizontal=align, vertical=valign, wrap_text=wrap)
    if c2 > c1:
        ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)
    if border:
        for cc in range(c1, c2 + 1):
            ws.cell(row=r, column=cc).border = B_BOTTOM
    ws.row_dimensions[r].height = height
    return c


def _plain(formula):
    """Longitud aproximada del texto de una fórmula (literales + 8 caracteres por valor vivo) para estimar alturas."""
    return "".join(seg if i % 2 else ("8" * 8 if seg.strip(" &()") else "") for i, seg in enumerate(formula.split('"')))


def _mini_card(ws, r, c, w, label_txt, formula, fmt, sub_formula):
    """Tarjeta menor: etiqueta MAYÚSCULAS 8,5 grafito / valor Calibri 13 negrita carbón / contexto 8,5 grafito; regla superior niebla."""
    for rr in (r, r + 1, r + 2):
        ws.merge_cells(start_row=rr, start_column=c, end_row=rr, end_column=c + w - 1)
    for cc in range(c, c + w):
        ws.cell(row=r, column=cc).border = Border(top=rule_soft)
    lab = ws.cell(row=r, column=c, value=label_txt); lab.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO); lab.alignment = Alignment(horizontal="left", vertical="bottom")
    val = ws.cell(row=r + 1, column=c, value=formula); val.font = Font(name=FONT, size=13, bold=True, color=CARBON); val.alignment = Alignment(horizontal="left", vertical="center"); val.number_format = fmt
    sub = ws.cell(row=r + 2, column=c, value=sub_formula); sub.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO); sub.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    ws.row_dimensions[r].height = 14; ws.row_dimensions[r + 1].height = 20; ws.row_dimensions[r + 2].height = 14


def build_portada(wb, ws_flujo, ws_fiscal, ws_capex, ws_sens, tornado_rows):
    ws = wb.create_sheet(S0, 0)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 1.5
    for cidx in range(2, LC + 1):
        ws.column_dimensions[col(cidx)].width = 6.0   # Excel/Mac imprime 6,05 pt por carácter de ancho XML: (24 × 6,0 + 2 × 1,5) × 6,05 = 889 pt → 82 % = 729 pt < 772 pt útiles
    ws.column_dimensions[col(LC + 1)].width = 1.5
    t0, t1 = tornado_rows
    # ================================================================ PÁGINA 1 · el tablero
    # ---- qué proyecto es
    r = 1
    c = ws.cell(row=r, column=2, value='="Proyecto fotovoltaico "&TEXT(Potencia_DC/1000,"0.0")&" MWp Montecristi → Gran Piazza Machala"')
    c.font = Font(name=FONT, size=24, color=CARBON); c.alignment = Alignment(vertical="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=LC - 3)
    link_cell(ws, r, LC - 2, "? Guía de lectura", f"#'{GUIDE}'!A1", size=SZ_TABLE, chip=True)
    ws.merge_cells(start_row=r, start_column=LC - 2, end_row=r, end_column=LC)
    for cc in range(LC - 2, LC + 1):
        ws.cell(row=r, column=cc).fill = fill(BRUMA)
    ws.row_dimensions[r].height = 32
    _line(ws, 2, 2, LC, '="Modelo financiero-legal de una planta solar de "&TEXT(Potencia_DC/1000,"0.0")&" MWp en Montecristi que autoabastece a Gran Piazza Machala (SALELGI S.A.) bajo la ARCONEL-005/24. SALELGI es dueña; Exergy la gerencia y opera"&IF(Comprador_Terreno="Exergy"," y le arrienda el terreno.","; SALELGI compra el terreno.")',
          size=SZ_BODY, color=CARBON, height=28, wrap=True, valign="top")
    _line(ws, 3, 2, 15, '=TEXT(Potencia_DC,"#,##0")&" kWp · "&TEXT(Potencia_AC,"#,##0")&" kWac (DC/AC "&TEXT(Ratio_DCAC,"0.00")&") · "&TEXT(Hectareas,"0.0")&" ha · USD nominal · "&Horizonte&" años desde el COD ("&TEXT(Fecha_COD,"mmm-yyyy")&") · VAN al "&TEXT(Tasa_Descuento,"0%")',
          size=SZ_TABLE, color=GRAFITO, bold=True, height=15)
    # estado del libro, para quien usa el modelo (controles · caso y versión · por confirmar), a la derecha de la fila 3
    for (c1, c2, f) in ((16, 18, '=IF(N_Controles_Fail=0,"● Controles "&N_Controles_OK&"/"&N_Controles,"■ "&N_Controles_Fail&" control(es) fallan")'),
                        (19, 22, '=IF(LEFT(Estado_Custom,1)="●","◇ Custom = Base · "&Version&" · "&TEXT(Fecha_Analisis,"dd-mmm-yyyy"),"▲ Custom ≠ Base en "&N_Custom_vs_Base&" entrada(s) · "&Version)'),
                        (23, LC, '="▲ "&N_Por_Confirmar&" por confirmar"')):
        _line(ws, 3, c1, c2, f, size=SZ_TABLE, color=GRAFITO, bold=True, align="right", height=15)
    _glyph_cf(ws, "P3:Y3")
    # fila 4: qué caso muestran las tarjetas y qué significa la tira «C · B · F» bajo cada una
    rt = CellRichText([TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, b=True, color=X_COL), "CASO CUSTOM"),
                       TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=GRAFITO), "  ·  las tarjetas muestran el caso de trabajo (gobierna todo el libro); bajo cada una, el mismo indicador en los tres escenarios fijos:")])
    c4 = ws.cell(row=4, column=2, value=rt); c4.alignment = Alignment(vertical="center")
    ws.merge_cells(start_row=4, start_column=2, end_row=4, end_column=17)
    for k_, (key_, cc_) in enumerate((("C", 18), ("B", 21), ("F", 24))):
        lc_ = ws.cell(row=4, column=cc_, value=f"{key_} = {CASO_NOMBRE[key_]}"); lc_.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=CASO_COL[key_]); lc_.alignment = Alignment(horizontal="left", vertical="center")
        ws.merge_cells(start_row=4, start_column=cc_, end_row=4, end_column=min(cc_ + 2, LC))
    ws.row_dimensions[4].height = 13
    # ---- qué dicen los números: 6 tarjetas uniformes
    r = 5
    cards = [
        # (etiqueta, valor Custom, formato, contexto, héroe, [fórmulas de la tira C · B · F])
        ("TIR DEL PROYECTO", "=X_TIR", FMT_PCT2, f'="Sin deuda · tasa exigida "&TEXT(Tasa_Descuento,"0%")&" · con energía P90: "&{TX("P90_TIR","0.0%")}&"."', True, ("TIR", "0.0%")),
        ('="VAN @ "&TEXT(Tasa_Descuento,"0%")', "=X_VAN", FMT_USD_D, f'="USD en el COD (t = 0) · con energía P90: "&{TX("P90_VAN","$#,##0;($#,##0)")}&"."', False, ("VAN", "M")),
        ("PAYBACK", "=X_PB", '0.0" años"', f'="Años desde el COD · con energía P90: "&{TX("P90_PB","0.0")}&" años."', False, ("PB", "0.0")),
        ("LCOE", "=X_LCOE", '#,##0.0', f'="$/MWh · tarifa evitable de la red: "&TEXT(Tarifa_MWh,"#,##0")&" → ahorro "&{TX("Ahorro_kWh","0%")}&" por kWh."', False, ("LCOE", "0")),
        ('=IF(Usar_Deuda="Sí","TIR DEL ACCIONISTA","TIR DEL PROYECTO (SIN DEUDA)")', '=IF(Usar_Deuda="Sí",X_TIReq,X_TIR)', FMT_PCT2, f'=IF(Usar_Deuda="Sí","Deuda "&TEXT(Pct_Apalancamiento,"0%")&" · "&TEXT(Tasa_Deuda,"0.0%")&" · "&Plazo_Deuda&" años · aporte de capital "&{TX("Aporte_Equity/1000000","0.00")}&" M.","La portada destaca el caso sin deuda (Usar_Deuda = No).")', False, ("TIReq", "0.0%")),
        ("DSCR MÍNIMO", "=X_DSCR", FMT_X, f'=IF(Deuda_Monto=0,"Sin deuda.",IF(X_DSCR<1,"■ Bajo 1,00x en t = "&Anio_DSCR_Min&".",IF(X_DSCR<DSCR_Objetivo,"▲ Bajo el objetivo "&TEXT(DSCR_Objetivo,"0.00")&"x en t = "&Anio_DSCR_Min&".","● Cumple el objetivo "&TEXT(DSCR_Objetivo,"0.00")&"x."))&" Deuda máxima para "&TEXT(DSCR_Objetivo,"0.00")&"x: "&TEXT(Deuda_Max_Plazo2,"0%")&" a "&INDEX(Sens_Plazos,2)&" años.")', False, ("DSCR", "0.00x")),
    ]

    def strip_f(tag, key, fmt):
        nm = f"{tag}_{key}"
        if fmt == "M":
            return f'="{tag} "&IFERROR(TEXT({nm}/1000000,"+0.0;-0.0"),"n/a")&"M"'
        if fmt == "0.00x":
            return f'="{tag} "&IFERROR(TEXT({nm},"0.00"),"n/a")&"x"'
        return f'="{tag} "&IFERROR(TEXT({nm},"{fmt}"),"n/a")'
    for k, (lab, f, fmt, sub, hero, (key, sfmt)) in enumerate(cards):
        c0 = 2 + k * CARD_W
        kpi_card(ws, r, c0, CARD_W, lab, f, fmt, sub, hero=hero, heights=(16, 34, 30))
        ws.cell(row=r, column=c0 + CARD_W - 1).border = B_NONE   # la 4.ª columna no lleva regla: aire entre tarjetas
        ws.cell(row=r + 2, column=c0).font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO)   # contexto a 9 pt
        # tira «C · B · F»: el mismo indicador en los tres escenarios fijos (una celda por caso, sin merges: la 4.ª columna es aire)
        caso_strip(ws, r + 3, c0, [strip_f(tag, key, sfmt) for tag in ("C", "B", "F")], size=SZ_NOTE)
    _glyph_cf(ws, f"V{r + 2}:V{r + 2}", bold=False)
    ws.row_dimensions[r + 3].height = 13
    ws.row_dimensions[r + 4].height = 4
    # ---- cuatro tarjetas menores (antes una línea de texto que se perdía)
    r = 10
    minis = [("CAPEX SALELGI (SIN IVA, INCL. GERENCIA)", "=CAPEX_Total_Terreno", FMT_USD_D, '=TEXT(CAPEX_Total/(Potencia_DC*1000),"0.000")&" $/Wp"&IF(Terreno_SALELGI>0," incl. terreno","")&" · IVA "&TEXT(IVA_Total,"$#,##0")&" · Favorable: "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4),"0.00")&" fijo"'),
             ("AHORRO EN LA FACTURA · AÑO 1", "=X_Ahorro1", FMT_USD_D, '=TEXT(Reduccion_Factura,"0%")&" de la factura de GPM · C (P90): "&TEXT(C_Ahorro1,"$#,##0")'),
             ('="AHORRO ACUMULADO · "&Horizonte&" AÑOS"', "=Ahorro_Acum", FMT_USD_D, '=TEXT(SUM(E_Activa)/1000,"0.0")&" GWh a "&TEXT(Tarifa_Evitable,"0.0000")&" $/kWh (tarifa evitable)"'),
             ('="VAN DEL NEGOCIO EXERGY @ "&TEXT(Tasa_Descuento,"0%")', "=VAN_Exergy", FMT_USD_D, f'="gerencia "&TEXT(Fee_Gerencia_Pct,"0%")&IF(Comprador_Terreno="Exergy"," + arriendo","")&" + O&M · TIR grupo "&{TX("TIR_Grupo","0.0%")}')]
    for k, (lab, f, fmt, sub) in enumerate(minis):
        _mini_card(ws, r, 2 + k * 6, 6, lab, f, fmt, sub)
        ws.cell(row=r, column=2 + k * 6 + 5).border = B_NONE
    ws.row_dimensions[r + 3].height = 6
    # ---- qué caso se presenta: ocho premisas en dos listas (etiqueta · texto)
    r = 14
    section(ws, r, 2, LC, "Caso Custom", guide='=IF(LEFT(Estado_Custom,1)="●","las ocho premisas que definen los números de esta página: el Custom coincide con el Base entregado (01_Supuestos) — el caso central, no el más favorable; los cuatro casos están en la página 3","▲ el Custom tiene "&N_Custom_vs_Base&" entrada(s) distinta(s) del Base entregado: estas ocho premisas describen el Custom")', guide_col=6)
    prem_left = [
        ("Energía", '=Escenario_Energia&" · "&TEXT(INDEX(E_Activa,1,3),"#,##0")&" MWh en el año 1 · yield "&TEXT(Yield_Ref,"#,##0")&" kWh/kWp · degradación −0,55 %/año"'),
        ("CAPEX y OPEX", '=IF(N(CAPEX_Fijo_Wp)>0,"CAPEX fijo "&TEXT(CAPEX_Fijo_Wp,"0.00")&" $/Wp","CAPEX bottom-up (costo real) × "&TEXT(Factor_CAPEX,"0.00"))&" = "&TEXT(CAPEX_Total/(Potencia_DC*1000),"0.000")&" $/Wp sin IVA · OPEX × "&TEXT(Factor_OPEX,"0.00")&" · deck v4: "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4),"0.00")&" $/Wp"'),
        ("Tarifa evitable", '=TEXT(Tarifa_Evitable,"0.0000")&" $/kWh (cargos 0,113 / 0,105 ponderados por la inyección horaria) · "&IF(Eff_EscT=0,"plana, sin escalación","escalación "&TEXT(Eff_EscT,"0.0%")&"/año")'),
        ("Peaje SGDA", '=TEXT(Eff_Peaje*100,"0.0")&" ¢/kWh desde "&TEXT(Fecha_Peaje,"mmm-yyyy")&" · fecha fijada por la regulación, valor aún no publicado · Conservador "&TEXT(INDEX(Esc_Peaje,2)*100,"0.0")&" ¢ (10 §B)"'),
    ]
    # textos representativos (caso Base) para estimar la altura: _plain suma las dos ramas de cada IF y sobreestima
    PREM_EST = [
        ("P50 · 6,470 MWh en el año 1 · yield 1,294 kWh/kWp · degradación −0,55 %/año", "0% del CAPEX · 8.5% · 10 años · 1 año de gracia · cuota francesa"),
        ("CAPEX bottom-up (costo real) × 1.00 = 0.824 $/Wp sin IVA · OPEX × 1.00 · deck v4: 0.75 $/Wp", "compra Exergy y arrienda a SALELGI 5,000 $/ha·año · 50,000 $/ha"),
        ("0.1128 $/kWh (cargos 0,113 / 0,105 ponderados por la inyección horaria) · plana, sin escalación", "participación 15% + IR 25% · deducción adicional 100 % topada · IVA recuperable"),
        ("0.5 ¢/kWh desde feb-2029 · fecha fijada por la regulación, valor aún no publicado · Conservador 1.5 ¢ (10 §B)", "25 años desde el COD (jul-2028) · tasa de descuento 10% · con Contrato de Inversión"),
    ]
    prem_right = [
        ("Deuda", '=TEXT(Pct_Apalancamiento,"0%")&" del CAPEX · "&TEXT(Tasa_Deuda,"0.0%")&" · "&Plazo_Deuda&" años · "&Gracia_Deuda&" año"&IF(Gracia_Deuda=1,"","s")&" de gracia · cuota francesa"'),
        ("Terreno", '=IF(Comprador_Terreno="Exergy","compra Exergy y arrienda a SALELGI "&TEXT(Renta_Terreno_ha,"#,##0")&" $/ha·año","compra SALELGI · sin arriendo, paga el predial")&" · "&TEXT(Precio_Terreno_ha,"#,##0")&" $/ha"'),
        ("Fiscal", '="participación "&TEXT(Tasa_Participacion,"0%")&" + IR "&TEXT(Tasa_IR,"0%")&" · deducción adicional 100 % topada · IVA "&IF(IVA_Recuperable="Sí","recuperable","no recuperable")'),
        ("Marco", '=Horizonte&" años desde el COD ("&TEXT(Fecha_COD,"mmm-yyyy")&") · tasa de descuento "&TEXT(Tasa_Descuento,"0%")&" · "&IF(Contrato_Inversion="Sí","con","sin")&" Contrato de Inversión"'),
    ]
    for k in range(4):
        rr = r + 1 + k
        for (lab, f), c1 in ((prem_left[k], 2), (prem_right[k], 14)):
            l = ws.cell(row=rr, column=c1, value=lab); l.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=CARBON); l.alignment = Alignment(vertical="center")
            ws.merge_cells(start_row=rr, start_column=c1, end_row=rr, end_column=c1 + 2)
            t_ = ws.cell(row=rr, column=c1 + 3, value=f); t_.font = Font(name=FONT, size=SZ_TABLE, color=CARBON); t_.alignment = Alignment(vertical="center", wrap_text=True)
            ws.merge_cells(start_row=rr, start_column=c1 + 3, end_row=rr, end_column=c1 + 11)
            for cc in range(c1, c1 + 12):
                ws.cell(row=rr, column=cc).border = B_BOTTOM
        fit_row(ws, rr, [(PREM_EST[k][0], merged_width(ws, 5, 13) - 2, 9), (PREM_EST[k][1], merged_width(ws, 17, LC) - 2, 9)], min_h=26, pad=2)
    ws.row_dimensions[r + 5].height = 6
    # ---- qué lo explica: dos gráficos
    gr = 20
    F = FLUJO
    ar = AUX0   # auxiliares fuera del área de impresión (los marcadores NA() siguen en las filas AUX0+3 y AUX0+4 = lista blanca de check_errors)
    ws.cell(row=ar - 1, column=2, value="Auxiliares de los gráficos (fuera del área de impresión; no editar)").font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar, column=2, value=f'="Custom · fin "&TEXT({C(T_MAX)}{ar}/1000000,"0.00")&" M"').font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 1, column=2, value=f'="Base · fin "&TEXT({C(T_MAX)}{ar + 1}/1000000,"0.00")&" M"').font = font(size=SZ_NOTE, color=PIEDRA)
    AR_C, AR_F = ar + 21, ar + 22   # acumulados de Conservador y Favorable (leídos del Motor)
    ws.cell(row=AR_C, column=2, value=f'="Conservador · fin "&TEXT({C(T_MAX)}{AR_C}/1000000,"0.00")&" M"').font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=AR_F, column=2, value=f'="Favorable · fin "&TEXT({C(T_MAX)}{AR_F}/1000000,"0.00")&" M"').font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 2, column=2, value="Año (t)").font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 3, column=2, value="positivo desde t =").font = font(size=SZ_NOTE, color=PIEDRA)   # nombre de la serie del marcador (serie 1): etiqueta = nombre + año
    ws.cell(row=ar + 4, column=2, value="positivo desde t =").font = font(size=SZ_NOTE, color=PIEDRA)   # ídem (serie 2)
    rng_a = f"{C(-1)}{ar}:{C(T_MAX)}{ar}"; rng_b = f"{C(-1)}{ar + 1}:{C(T_MAX)}{ar + 1}"
    # primer cruce de negativo a ≥ 0 (filas ar+8/ar+9 marcan cada cruce hacia arriba; MIN toma el primero; "n/a" si nunca cruza)
    ws.cell(row=ar + 5, column=2, value="Primer año con acumulado ≥ 0 (serie 1 / serie 2)").font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 5, column=3, value=f'=IF(COUNT({C(-1)}{ar + 8}:{C(T_MAX)}{ar + 8})=0,"n/a",MIN({C(-1)}{ar + 8}:{C(T_MAX)}{ar + 8}))').font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 5, column=4, value=f'=IF(COUNT({C(-1)}{ar + 9}:{C(T_MAX)}{ar + 9})=0,"n/a",MIN({C(-1)}{ar + 9}:{C(T_MAX)}{ar + 9}))').font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 8, column=2, value="Cruces hacia arriba · serie 1 (año)").font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 9, column=2, value="Cruces hacia arriba · serie 2 (año)").font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 6, column=2, value="Título del gráfico de flujo").font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 6, column=3, value='="Flujo acumulado del proyecto (sin deuda) · millones de USD"').font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 7, column=2, value="Título del tornado").font = font(size=SZ_NOTE, color=PIEDRA)
    ws.cell(row=ar + 7, column=3, value='="Tornado · Δ TIR del proyecto en pp · las 9 variables de mayor amplitud (14 en 10 §B) · "&IF(LEFT(Estado_Custom,1)="●","Custom (= Base)","Custom (≠ Base)")').font = font(size=SZ_NOTE, color=PIEDRA)
    for t in TS:
        cc = COL0 + (t + 1)
        a = ws.cell(row=ar, column=cc, value=f"='{S8}'!{C(t)}{F['acum']}")                                  # Custom = 08 (control D12 lo concilia con el Motor)
        b = ws.cell(row=ar + 1, column=cc, value=f"='{SM}'!${MOTOR_CASE_COL['B']}${brow('Cum_u', t)}")     # Base (Motor)
        for rr_, key_ in ((AR_C, "C"), (AR_F, "F")):
            x_ = ws.cell(row=rr_, column=cc, value=f"='{SM}'!${MOTOR_CASE_COL[key_]}${brow('Cum_u', t)}"); x_.font = font(size=SZ_NOTE, color=PIEDRA); x_.number_format = FMT_USD
        y = ws.cell(row=ar + 2, column=cc, value=f"='{S8}'!{C(t)}{F['t']}")
        # marcador del año de cruce: valor sólo en ese año, #N/A en el resto (Excel no dibuja los #N/A) — únicas celdas del libro que pueden dar error
        ma = ws.cell(row=ar + 3, column=cc, value=f"=IF({C(t)}${ar + 2}=$C${ar + 5},{C(t)}{ar},NA())")
        mb = ws.cell(row=ar + 4, column=cc, value=f"=IF(AND({C(t)}${ar + 2}=$D${ar + 5},N_Custom_vs_Base>0),{C(t)}{ar + 1},NA())")   # el marcador del Base sólo si el Custom difiere
        prev = "" if t == -1 else f"{C(t - 1)}"
        xa = ws.cell(row=ar + 8, column=cc, value=(f"=IF({C(t)}{ar}>=0,{C(t)}{ar + 2},\"\")" if t == -1 else f"=IF(AND({C(t)}{ar}>=0,{prev}{ar}<0),{C(t)}{ar + 2},\"\")"))
        xb = ws.cell(row=ar + 9, column=cc, value=(f"=IF({C(t)}{ar + 1}>=0,{C(t)}{ar + 2},\"\")" if t == -1 else f"=IF(AND({C(t)}{ar + 1}>=0,{prev}{ar + 1}<0),{C(t)}{ar + 2},\"\")"))
        for x in (xa, xb):
            x.font = font(size=SZ_NOTE, color=PIEDRA); x.number_format = "0"
        for x in (a, b, ma, mb):
            x.font = font(size=SZ_NOTE, color=PIEDRA); x.number_format = FMT_USD
        y.font = font(size=SZ_NOTE, color=PIEDRA); y.number_format = "0"
    # v3.0 (V6): las 9 barras de mayor amplitud, leídas del bloque de ranking de 10 §B (etiqueta · Δ bajo · Δ alto)
    RK_AMP, RK_IDX, RK_LAB, RK_LO, RK_HI = BC.TORNADO_RANK_COLS
    NTP = min(BC.PORTADA_TORNADO_N, t1 - t0 + 1)
    ws.cell(row=ar + 10, column=2, value="Tornado: las 9 barras de mayor amplitud (etiqueta con espacio final · Δ bajo · Δ alto), del ranking de 10 §B").font = font(size=SZ_NOTE, color=PIEDRA)
    for k in range(NTP):
        rt = t0 + k
        ws.cell(row=ar + 11 + k, column=2, value=f"='{S10}'!{col(RK_LAB)}{rt}&\"    \"").font = font(size=SZ_NOTE, color=PIEDRA)
        for cc, src in ((3, RK_LO), (4, RK_HI)):
            c_ = ws.cell(row=ar + 11 + k, column=cc, value=f"='{S10}'!{col(src)}{rt}"); c_.font = font(size=SZ_NOTE, color=PIEDRA); c_.number_format = "0.00"
    torn_cats = Reference(ws, min_col=2, min_row=ar + 11, max_row=ar + 11 + NTP - 1)
    cats = Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=ar + 2)
    lbl_idx = [t + 1 for t in (0, T_MAX)]   # el hueco inicial y el final; los años intermedios se leen en el eje y el cruce lo marca el punto
    ch = chart_lines(ws, f"B{gr}", "Flujo de caja acumulado del proyecto", cats,
                     # cuatro casos: Custom 2,25 pt ciruela (etiqueta final), Conservador y Favorable 1,25 pt, Base punteada 1,25 pt (d5)
                     [dict(ref=Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=ar), color=X_COL, width=2.25, labels=[T_MAX + 1], label_fmt=FMT_M, label_pos="r", label_color=X_COL),
                      dict(ref=Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=ar + 1), color=B_COL, width=1.25, dash="sysDot"),   # sin etiqueta final: coincide con el Custom cuando Custom = Base; su «fin» está en la leyenda
                      dict(ref=Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=AR_C), color=C_COL, width=1.25, labels=[T_MAX + 1], label_fmt=FMT_M, label_pos="b", label_color=C_COL),
                      dict(ref=Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=AR_F), color=F_COL, width=1.25, labels=[T_MAX + 1], label_fmt=FMT_M, label_pos="t", label_color=F_COL),
                      # marcador del año de cruce del Custom (etiqueta a la derecha) y del Base (a la izquierda)
                      dict(ref=Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=ar + 3), color=X_COL, marker_only=True, marker="circle", marker_size=9, labels="all", label_ser=True, label_cat=True, label_sep=" ", label_pos="r", label_color=X_COL),
                      dict(ref=Reference(ws, min_col=COL0, max_col=LAST_T_COL, min_row=ar + 4), color=B_COL, marker_only=True, marker="diamond", marker_size=7, labels="all", label_ser=True, label_cat=True, label_sep=" ", label_pos="l", label_color=B_COL)],
                     w=14.0, h=8.8, y_fmt=FMT_M, legend=None, from_rows=True, x_title="año t (0 = COD)", x_skip=2, title_ref=f"'{S0}'!$C${ar + 6}")
    ch.series[0].tx = SeriesLabel(strRef=StrRef(f"'{S0}'!$B${ar}"))
    ch.series[1].tx = SeriesLabel(strRef=StrRef(f"'{S0}'!$B${ar + 1}"))
    ch.series[2].tx = SeriesLabel(strRef=StrRef(f"'{S0}'!$B${AR_C}"))
    ch.series[3].tx = SeriesLabel(strRef=StrRef(f"'{S0}'!$B${AR_F}"))
    ch.series[4].tx = SeriesLabel(strRef=StrRef(f"'{S0}'!$B${ar + 3}"))
    ch.series[5].tx = SeriesLabel(strRef=StrRef(f"'{S0}'!$B${ar + 4}"))
    chart_tornado(ws, f"N{gr}", "Tornado · Δ TIR del proyecto (puntos porcentuales)", torn_cats,
                  Reference(ws, min_col=3, min_row=ar + 11, max_row=ar + 11 + NTP - 1), Reference(ws, min_col=4, min_row=ar + 11, max_row=ar + 11 + NTP - 1), w=14.0, h=8.8, title_ref=f"'{S0}'!$C${ar + 7}")
    NCH = 19   # 18 filas × (15 − 1) = 252 pt ≥ 8,8 cm (249 pt) de gráfico; la 19.ª fila (libre bajo el gráfico) lleva la leyenda manual del flujo
    for k in range(gr, gr + NCH):
        ws.row_dimensions[k].height = 15
    # leyenda manual del gráfico de flujo (Excel/Mac ignora la supresión de entradas de leyenda: sin leyenda automática,
    # las dos series se nombran aquí con su color; los marcadores del cruce no necesitan leyenda)
    lg = gr + NCH - 1
    for (c1, c2, f, colr) in ((2, 4, f'="▬ "&$B${ar}', X_COL), (5, 7, f'="▬ "&$B${AR_C}', C_COL), (8, 10, f'="┄ "&$B${ar + 1}', B_COL), (11, 13, f'="▬ "&$B${AR_F}', F_COL)):
        _line(ws, lg, c1, c2, f, size=SZ_NOTE, color=colr, bold=True, align="left", height=15)
    r = gr + NCH   # 39
    ws.row_dimensions[r].height = 6
    ws.row_breaks.append(Break(id=r))
    # ================================================================ PÁGINA 2 · la lectura
    r += 1
    # ---- se puede hacer: semáforo con explicación
    section(ws, r, 2, LC, "Condiciones habilitantes del proyecto", guide="estado en vivo · el marco legal completo está en 02, los trámites en 03 y los riesgos en 11", guide_col=8)
    r += 1
    hdr(ws, r, 2, LC, ["Condición"] + [""] * 4 + ["Estado"] + [""] * 5 + ["Qué significa"] + [""] * 12, height=18, align="left")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6); ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=12); ws.merge_cells(start_row=r, start_column=13, end_row=r, end_column=LC)
    r += 1
    sem0 = r
    sem = [
        ("Régimen SGDA remoto", '="● Habilitado (Res. ARCONEL-010/2024)"', "La planta (Montecristi, CNEL Manabí) puede abastecer la cuenta de GPM (Machala, CNEL El Oro): la regulación admite el autoabastecimiento entre unidades de negocio de CNEL EP."),
        ("Energía (art. 9)", f"=IF('{S4}'!${C(1)}${ENERGIA['p50']}<=Consumo_Anual/1000,\"● Cubre el \"&TEXT(Cobertura_Anual,\"0%\")&\" de la demanda\",\"■ Excede la demanda anual\")",
         f'="La producción anual ("&TEXT(\'{S4}\'!${C(1)}${ENERGIA["p50"]},"#,##0")&" MWh) debe ser ≤ que el consumo anual del medidor ("&TEXT(Consumo_Anual/1000,"#,##0")&" MWh); con este consumo cabrían hasta ≈ "&TEXT(Consumo_Anual/Yield_Ref/F_Recorte/1000,"0.0")&" MWp."'),
        ("Comercial (art. 8 y Disp. Décima)", '="● Servicios y arriendo a renta fija, sin venta de kWh"', "Exergy cobra gerencia, O&M y arriendo; nunca un precio por kWh, que sería comercialización prohibida y causa de revocatoria del certificado."),
        ("Físico (art. 7a)", '=IF(Potencia_AC>Capacidad_Alimentador_kW,"■ La potencia AC supera el alimentador","▲ Alimentador por confirmar con CNEL")',
         '="La potencia AC ("&TEXT(Potencia_AC,"#,##0")&" kW) debe caber en la capacidad que CNEL apruebe para el alimentador de 13,8 kV (marcador "&TEXT(Capacidad_Alimentador_kW,"#,##0")&" kW). Hito binario: pedir la factibilidad antes de comprometer capital."'),
        ("Económico (peaje de red)", '="▲ Peaje SGDA desde "&TEXT(Fecha_Peaje,"mmm-yyyy")&" · valor no publicado"',
         f'="La regulación fija la fecha, no el valor. El Custom usa "&TEXT(Eff_Peaje*100,"0.0")&" ¢/kWh (Conservador "&TEXT(INDEX(Esc_Peaje,2)*100,"0.0")&" ¢); con "&TEXT(Sens_Peaje*100,"0.0")&" ¢/kWh la TIR cambia "&TEXT(\'{S10}\'!$E${t0 + 3},"+0.0;-0.0")&" pp (10 §B). Mitigante: cláusula de reapertura en los contratos."'),
        ("Predio", '=IF(Hectareas<=Ha_Disponibles,"● "&TEXT(Hectareas,"0.0")&" de "&TEXT(Ha_Disponibles,"0.00")&" ha disponibles","■ Faltan hectáreas")',
         '="La planta ocupa "&TEXT(Hectareas,"0.0")&" ha ("&TEXT(Densidad_MWp_ha,"0.0")&" MWp por hectárea) del predio de "&TEXT(Ha_Disponibles,"0.00")&" ha; el resto queda libre para una segunda fase."'),
    ]
    for lab, f, expl in sem:
        l = ws.cell(row=r, column=2, value=lab); l.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=CARBON); l.alignment = Alignment(vertical="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        st = ws.cell(row=r, column=7, value=f); st.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=GRAFITO); st.alignment = Alignment(vertical="center", wrap_text=True)
        ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=12)
        e = ws.cell(row=r, column=13, value=expl); e.font = Font(name=FONT, size=SZ_TABLE, color=CARBON); e.alignment = Alignment(vertical="center", wrap_text=True)
        ws.merge_cells(start_row=r, start_column=13, end_row=r, end_column=LC)
        for cc in range(2, LC + 1): ws.cell(row=r, column=cc).border = B_BOTTOM
        fit_row(ws, r, [(_plain(expl) if expl.startswith("=") else expl, merged_width(ws, 13, LC) - 2, 9), (_plain(f), merged_width(ws, 7, 12) - 2, 9)], min_h=24, pad=5)
        r += 1
    _glyph_cf(ws, f"G{sem0}:G{r - 1}")
    ws.row_dimensions[r].height = 10; r += 1
    # ---- qué concluyo: conclusión en negrita + evidencia
    section(ws, r, 2, LC, "Lectura ejecutiva", guide="siete conclusiones con cifras vivas; el detalle está en 02, 08, 09 y 10", guide_col=8)
    r += 1
    msgs = [
        ("Viabilidad", '="El proyecto es legalmente viable y encaja en el régimen SGDA remoto; el encaje no depende de la Ley 2026 (en litigio)."',
         '="La Res. ARCONEL-005/24 codificada permite autoabastecerse entre unidades de negocio de CNEL EP (Atlas Regulatorio v2.0, 08-sep-2026); "&TEXT(Potencia_DC/1000,"0.0")&" MWp cubren el "&TEXT(Cobertura_Anual,"0%")&" del consumo"&IF(SUM(E_Activa)-SUM(E_Val)>0.5," pero exceden la demanda anual (art. 9)"," sin excedentes mensuales")&"; el art. 9 admitiría hasta ≈ "&TEXT(Consumo_Anual/Yield_Ref/F_Recorte/1000,"0.0")&" MWp. Riesgo binario: capacidad del alimentador (Manta al límite) → pre-consulta y factibilidad temprana."'),
        ("Economía", f'=IF(ISNUMBER(X_TIR),IF(X_TIR>=Tasa_Descuento,"La rentabilidad del Custom supera la tasa exigida","La rentabilidad del Custom queda bajo la tasa exigida")&": TIR "&TEXT(X_TIR,"0.0%")&" frente al "&TEXT(Tasa_Descuento,"0%")&" (VAN "&TEXT(X_VAN,"$#,##0;($#,##0)")&").","TIR del Custom no calculable.")',
         f'="Conservador "&{TX("C_TIR","0.0%")}&" · Base "&{TX("B_TIR","0.0%")}&" · Favorable "&{TX("F_TIR","0.0%")}&". LCOE "&{TX("X_LCOE","0")}&" frente a "&TEXT(Tarifa_Evitable*1000,"0")&" $/MWh de la red. Deciden el CAPEX y la tarifa: ±"&TEXT(Sens_CAPEX,"0%")&" de CAPEX ≈ ±"&TEXT(ABS({BC.mo(T_CAPEX_UP,"TIR")}-{BC.mo(T_CAPEX_DN,"TIR")})/2*100,"0.0")&" pp de TIR."'),
        ("Deuda", f'="La deuda sube la TIR del accionista a "&{TX("X_TIReq","0.0%")}&", pero el DSCR mínimo cae a "&{TX("X_DSCR","0.00")}&"x en t = "&Anio_DSCR_Min&"."',
         f'="Con "&TEXT(Pct_Apalancamiento,"0%")&" al "&TEXT(Tasa_Deuda,"0.0%")&" a "&Plazo_Deuda&" años. Para un DSCR de "&TEXT(DSCR_Objetivo,"0.00")&"x la deuda máxima es "&TEXT(Deuda_Max_Plazo1,"0%")&" a "&INDEX(Sens_Plazos,1)&" años o "&TEXT(Deuda_Max_Plazo2,"0%")&" a "&INDEX(Sens_Plazos,2)&" años (10 §H)."'),
        ("Dimensionamiento", '="La potencia AC ("&TEXT(Potencia_AC,"#,##0")&" kW) está al límite de la capacidad aprobable del alimentador ("&TEXT(Capacidad_Alimentador_kW,"#,##0")&" kW, por confirmar)."',
         '="Subir el ratio DC/AC a 1,50 costaría ≈ "&TEXT(1-(1-INDEX(CR_Loss,MATCH(1.5,CR_Ratio,1)))/(1-Loss_Ref),"0.0%")&" de energía y abarataría inversores y transformación (10 §F)."'),
        ("Fiscal y regulación", '="A favor: deducción adicional (condicionada a certificación ambiental previa) e IVA recuperable. En contra: participación + IR, arancel + ISD y el peaje SGDA desde "&TEXT(Fecha_Peaje,"mmm-yyyy")&"."',
         f'="Deducción adicional "&TEXT(DedAd_Anual,"$#,##0")&"/año (topada al 5 % de los ingresos; procedimiento de certificación no publicado): sin ella la TIR sería "&TEXT({BC.mo(BC.T_DEDAD,"TIR")},"0.0%")&". Tasa efectiva marginal "&TEXT(Tasa_Efectiva,"0.00%")&"; arancel + ISD ≈ "&TEXT(Aranceles_ISD,"$#,##0")&" sin Contrato de Inversión. GPM es cliente AV1: el D.E. 32 le exige acreditar generación propia (18-dic-2026)."'),
        ("Puente con el libro anterior", f'="El Base pasa de "&TEXT({BC.mo(BC.BR0,"TIR")},"0.00%")&" a "&TEXT({BC.mo(BC.BR5,"TIR")},"0.00%")&" de TIR frente al libro anterior: escalación del CAPEX, disponibilidad y reemplazo de inversores."',
         f'="Escalones (10 §A.3): escalación "&TEXT(({BC.mo(BC.BR1,"TIR")}-{BC.mo(BC.BR0,"TIR")})*100,"+0.00;−0.00")&" pp · disponibilidad "&TEXT(({BC.mo(BC.BR2,"TIR")}-{BC.mo(BC.BR1,"TIR")})*100,"+0.00;−0.00")&" pp · reemplazo "&TEXT(({BC.mo(BC.BR3,"TIR")}-{BC.mo(BC.BR2,"TIR")})*100,"+0.00;−0.00")&" pp. El accionista pasa de "&TEXT({BC.mo(BC.BR0,"TIR_eq")},"0.0%")&" a "&TEXT({BC.mo(BC.BR5,"TIR_eq")},"0.0%")&": la construcción de "&Meses_Construccion&" meses y su tasa del "&TEXT(Tasa_Descuento_Equity,"0%")&" sólo lo mueven a él. "&Estado_Neutro&"."'),
        ("Terreno y Exergy", '=IF(Comprador_Terreno="Exergy","Que Exergy compre el terreno y lo arriende es casi neutro para SALELGI y da a Exergy una renta estable.","Que SALELGI compre el terreno es casi neutro para SALELGI; Exergy pierde la línea terreno.")',
         "=\"VAN Exergy \"&" + TX("VAN_Exergy", "$#,##0;($#,##0)") + "&\" (gerencia \"&TEXT(Fee_Gerencia_Pct,\"0%\")&IF(Comprador_Terreno=\"Exergy\",\", arriendo \"&TEXT(Renta_Terreno_ha,\"#,##0\")&\" $/ha\",\"\")&\", O&M \"&TEXT(Fee_OM_kWp,\"0\")&\" $/kWp) con el \"&TEXT(Carga_Exergy,\"0%\")&\" del ahorro del cliente. Si compra \"&IF(Comprador_Terreno=\"Exergy\",\"SALELGI\",\"Exergy\")&\": TIR \"&" + TX(BC.mo(CASE_TERR_ALT, "TIR"), "0.0%") + "&\" y VAN Exergy \"&" + TX(BC.mo(CASE_TERR_ALT, "VAN_X"), "$#,##0;($#,##0)") + "&\" (10 §G).\""),
    ]
    for topic, head, ev in msgs:
        t_ = ws.cell(row=r, column=2, value=topic); t_.font = Font(name=FONT, size=SZ_BODY, bold=True, color=CARBON); t_.alignment = Alignment(vertical="top")
        ws.merge_cells(start_row=r, start_column=2, end_row=r + 1, end_column=4)
        h_ = ws.cell(row=r, column=5, value=head); h_.font = Font(name=FONT, size=SZ_BODY, bold=True, color=CARBON); h_.alignment = Alignment(vertical="center", wrap_text=True)
        ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=LC)
        e_ = ws.cell(row=r + 1, column=5, value=ev); e_.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO); e_.alignment = Alignment(vertical="top", wrap_text=True)
        ws.merge_cells(start_row=r + 1, start_column=5, end_row=r + 1, end_column=LC)
        for cc in range(2, LC + 1): ws.cell(row=r + 1, column=cc).border = B_BOTTOM
        ws.row_dimensions[r].height = 17        # conclusión: una línea de 10 pt
        ws.row_dimensions[r + 1].height = 30    # evidencia: hasta dos líneas de 9 pt (ritmo uniforme)
        r += 2
    c = ws.cell(row=r, column=2, value='="P90 = 90 % de probabilidad de excedencia (energía "&IFERROR(TEXT(P90_Ahorro1/P50_Ahorro1-1,"0.0%"),"n/a")&" vs P50) · tarifa evitable del Custom "&IF(Eff_EscT=0,"plana: cualquier alza tarifaria mejora estos resultados","con escalación "&TEXT(Eff_EscT,"0.0%")&"/año")&" · definición de los cuatro casos en la página 3 y en 01 bloque B · cifras indicativas, no constituyen oferta ni opinión legal"'); c.font = font(size=SZ_NOTE, color=GRAFITO); c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=LC)
    ws.row_dimensions[r].height = 24   # dos líneas: en Excel/Mac la nota (~250 car.) no cabe en una y se recortaba al imprimir (render r3)
    r += 1
    ws.row_dimensions[r].height = 10
    ws.row_breaks.append(Break(id=r))   # página 3: los escenarios nombrados
    r += 1
    # ---- los cuatro casos (10 §A): Custom · Conservador · Base · Favorable con su definición viva
    section(ws, r, 2, LC, "Los cuatro casos", guide="calculados siempre en el Motor con la potencia, el contrato, el terreno y la deuda de 01; el Custom es el caso de las páginas 1 y 2 (10 §A)", guide_col=6)
    r += 1
    hdr(ws, r, 2, LC, ["Indicador"] + [""] * 4 + [""] * 12 + ["Definición del caso (01 bloque B)"] + [""] * 6, height=18, align="right")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    for j, key in enumerate(CASE_KEYS):
        c1 = 7 + j * 3
        caso_hdr(ws, r, c1, key, c2=c1 + 2, size=SZ_TABLE)
    ws.merge_cells(start_row=r, start_column=19, end_row=r, end_column=LC)
    ws.cell(row=r, column=19).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    r += 1
    esc_rows = [("Energía año 1 (MWh)", "E1", FMT_INT), ("TIR del proyecto (sin deuda)", "TIR", FMT_PCT2), ("VAN @ tasa de descuento (USD)", "VAN", FMT_USD),
                ("Payback desde el COD (años)", "PB", FMT_YRS), ("LCOE ($/MWh)", "LCOE", FMT_DEC1), ("TIR del accionista (con deuda)", "TIReq", FMT_PCT2), ("DSCR mínimo", "DSCR", FMT_X), ("VAN negocio Exergy (USD)", "VANX", FMT_USD)]
    defs = [esc_def(1), esc_def(2), esc_def(3), esc_def(4),
            "Comparten potencia, ratio DC/AC, terreno, deuda y fiscalidad (capa de diseño de 01); el Custom nace igual al Base.",
            "=Estado_Custom", "=Estado_Entregado",
            "Texto en ladrillo: TIR bajo la tasa de descuento, VAN negativo o DSCR bajo 1,00x; en arcilla: DSCR bajo el objetivo."]
    e0 = r
    for i, (lab, key, fmt) in enumerate(esc_rows):
        c = ws.cell(row=r, column=2, value=lab); c.font = font(size=SZ_TABLE, color=CARBON, bold=(key in ("TIR", "VAN"))); c.alignment = Alignment(vertical="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        for j, tag in enumerate(CASE_KEYS):
            v = ws.cell(row=r, column=7 + j * 3, value=f"={tag}_{key}"); v.font = Font(name=FONT, size=SZ_TABLE, color=CARBON, bold=(tag == "X")); v.number_format = fmt
            v.alignment = Alignment(horizontal="right", vertical="center")
            ws.merge_cells(start_row=r, start_column=7 + j * 3, end_row=r, end_column=9 + j * 3)
        d = ws.cell(row=r, column=19, value=defs[i])
        d.font = Font(name=FONT, size=SZ_NOTE, color=(CASO_COL[CASE_KEYS[i]] if i < 4 else GRAFITO), bold=(i < 4)); d.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
        ws.merge_cells(start_row=r, start_column=19, end_row=r, end_column=LC)
        for cc in range(2, LC + 1):
            ws.cell(row=r, column=cc).border = B_BOTTOM
        ws.row_dimensions[r].height = 28
        r += 1
    _glyph_cf(ws, f"S{e0 + 5}:S{e0 + 6}", bold=False)
    BC.cf_scale(ws, f"G{e0 + 1}:R{e0 + 1}"); BC.cf_scale(ws, f"G{e0 + 2}:R{e0 + 2}", mid_num=0); BC.cf_scale(ws, f"G{e0 + 5}:R{e0 + 5}")
    BC.cf_text(ws, f"G{e0 + 6}:R{e0 + 6}", 1, "DSCR_Objetivo")
    ws.row_dimensions[r].height = 12; r += 1
    # ---- mapa del libro: qué encuentro en cada hoja (la barra de arriba navega; esto explica; útil también impreso)
    section(ws, r, 2, LC, "Mapa del libro", guide="qué encuentro en cada hoja; los botones abren la hoja", guide_col=6)
    ws.row_dimensions[r].height = 20; r += 1
    MAPA = [
        (GUIDE, "Guía de lectura", '="Cómo leer el libro: pasos, convenciones de color, preguntas frecuentes y glosario."'),
        (S1, None, '="Todas las entradas (texto tinta): el bloque B define los cuatro casos y el Custom gobierna el libro; es la única hoja que se edita."'),
        (S2, None, '="Qué permite y qué prohíbe el régimen SGDA remoto (ARCONEL-005/24 y 010/2024): los candados legales."'),
        (S3, None, '="Cronograma de permisos y conexión (Gantt) con la ruta crítica hasta el COD."'),
        (S4, None, '="Consumo del medidor, producción mensual P50/P90, recorte por autoconsumo e inyección valorada."'),
        (S5, None, '="Presupuesto de inversión por partidas y drivers ($/Wp), con el CAPEX de los cuatro casos."'),
        (S6, None, '="Costos de operación de SALELGI (O&M, gerencia, arriendo, seguros) y memo de costos propios de Exergy."'),
        (S7, None, '="Impuesto a la renta, participación laboral, deducción adicional e IVA del proyecto."'),
        (S8, None, '="Flujo de caja de SALELGI a "&Horizonte&" años, con y sin deuda: TIR, VAN, payback y DSCR."'),
        (S9, None, '="El negocio de Exergy: gerencia, O&M y arriendo del terreno frente a sus costos propios."'),
        (S10, None, '="Los cuatro casos, cuánto cambia la TIR por variable (tornado), matrices y dimensionamiento 5–8 MWp."'),
        (S11, None, '="Matriz de riesgos legales, técnicos y económicos con probabilidad, impacto y mitigante."'),
        (S12, None, '="De dónde sale cada dato (fuente y fecha), supuestos por confirmar y checks de calidad."'),
        (S13, None, '="Las "&N_Controles&" identidades contables y de consistencia que el libro verifica en vivo."'),
        (SM, "Motor de casos", '="Motor de cálculo de los 99 casos (Custom · Conservador · Base · Favorable y sensibilidades); no se edita."'),
    ]
    SHORT = {S1: "Supuestos", S2: "Legal", S3: "Trámites", S4: "Energía", S5: "CAPEX", S6: "OPEX", S7: "Fiscal", S8: "Flujo",
             S9: "Exergy", S10: "Sensibilidad", S11: "Riesgos", S12: "Fuentes", S13: "Controles"}
    m0 = r
    for k, (sh, lab, desc) in enumerate(MAPA):
        rr = m0 + k // 2
        c1 = 2 + (k % 2) * 12
        txt = lab or f"{sh.split('_')[0]} · {SHORT.get(sh, ' '.join(sh.split('_')[1:]))}"
        link_cell(ws, rr, c1, txt, f"#'{sh}'!A1", size=SZ_TABLE, chip=True)
        ws.merge_cells(start_row=rr, start_column=c1, end_row=rr, end_column=c1 + 2)
        for cc in range(c1, c1 + 3):
            ws.cell(row=rr, column=cc).fill = fill(BRUMA)
            ws.cell(row=rr, column=cc).border = Border(left=Side(style="thin", color=WHITE), right=Side(style="thin", color=WHITE), top=Side(style="thin", color=WHITE), bottom=Side(style="thin", color=WHITE))
        d = ws.cell(row=rr, column=c1 + 3, value=desc); d.font = Font(name=FONT, size=SZ_TABLE, color=CARBON); d.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
        ws.merge_cells(start_row=rr, start_column=c1 + 3, end_row=rr, end_column=c1 + 11)
        ws.row_dimensions[rr].height = 28
    r = m0 + (len(MAPA) + 1) // 2
    ws.row_dimensions[r].height = 8; r += 1
    ws.cell(row=r, column=2, value='="Exergy EXG S.A.S. · Modelo financiero-legal FV Montecristi → GPM · "&Version&" · "&TEXT(Fecha_Analisis,"dd-mmm-yyyy")&" · Investigación de decisión, no opinión legal ni oferta."').font = font(size=SZ_NOTE, color=GRAFITO)
    ws.row_dimensions[r].height = 15
    assert r < AUX0 - 2, (r, AUX0)
    ws.print_area = f"A1:{col(LC + 1)}{r}"
    setup_print(ws, landscape=True, scale=82)   # escala fija: el salto de fila manual sólo se respeta fuera del modo «ajustar»; anchos comprobados con el factor Mac
    ws.page_margins.top = 0.45; ws.page_margins.bottom = 0.55
    ws.sheet_properties.tabColor = CARBON
    return ws
