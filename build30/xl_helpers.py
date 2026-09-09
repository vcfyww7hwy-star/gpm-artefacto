# -*- coding: utf-8 -*-
"""Sistema visual v2.0 — «neutro con un acento» + cuatro colores de caso (Custom · Conservador · Base · Favorable). Tokens, formatos, componentes y plantillas de gráficos (openpyxl).

Reglas (doc 05 §2): el color sólo aparece con significado — tinta = editable · terracota = el dato que decide / caso activo /
umbral / enlaces · salvia-arcilla-ladrillo = estado. Todo lo demás es escala de grises cálidos. Sin rellenos de color en tablas,
sin paneles congelados, Calibri / Calibri Light, cinco tamaños (18 · 11 · 10/9 · 8,5 · 22)."""
import math
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.comments import Comment
from openpyxl.chart import BarChart, LineChart, ScatterChart, Reference
from openpyxl.chart.series import SeriesLabel, DataPoint
from openpyxl.chart import Series as XSeries
from openpyxl.chart.label import DataLabelList, DataLabel
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText, Text
from openpyxl.chart.title import Title
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.axis import ChartLines
from openpyxl.chart.data_source import NumFmt, StrRef
from openpyxl.descriptors import Typed
from openpyxl.chart.marker import Marker
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties, Font as DFont, RegularTextRun

# ---------------------------------------------------------------- tokens de color (paleta v1.3, doc 05 §2.2)
WHITE = "FFFFFF"
LINO = "FBF9F6"        # fondo de portada y del panel de mandos
BRUMA = "F1EFEB"       # fondo de fila de sección, cuadrícula de gráficos
NIEBLA = "D9D6D0"      # reglas de sección, bordes de tarjeta, barras «caso bajo»
PIEDRA = "8A857C"      # notas, unidades, ejes, texto meta
GRAFITO = "57534C"     # texto secundario, cabeceras de tabla, serie 2
CARBON = "2B2A27"      # texto principal, títulos, regla de cabecera y de totales
TERRACOTA = "A65E3F"   # único acento
TINTA = "1F4E79"       # sólo texto de celdas editables
SALVIA = "7D8B6E"      # ● ok
ARCILLA = "A67C52"     # ▲ atención · por confirmar
LADRILLO = "8E4A3A"    # ■ riesgo
# ---- v2.0 · colores de caso (doc 11 §1.3): sólo donde hay más de un caso a la vista (cabeceras, series, tira, leyenda, ◆)
X_COL = "7A3E5D"       # Custom · ciruela
C_COL = "3B4F9E"       # Conservador · índigo
B_COL = "1F6472"       # Base · petróleo
F_COL = "2E7D57"       # Favorable · verde bosque
X_TINT, C_TINT, B_TINT, F_TINT = "EFE8EC", "E7EAF3", "E4ECEE", "E6EFEB"   # tintes 12 % (chips de estado, tarjetas del Resumen)
CASO_COL = {"X": X_COL, "C": C_COL, "B": B_COL, "F": F_COL}
CASO_TINT = {"X": X_TINT, "C": C_TINT, "B": B_TINT, "F": F_TINT}
CASO_NOMBRE = {"X": "Custom", "C": "Conservador", "B": "Base", "F": "Favorable"}
CASOS = ("X", "C", "B", "F")   # orden canónico en toda tabla comparativa (d1): Custom primero
PALETTE = {WHITE, LINO, BRUMA, NIEBLA, PIEDRA, GRAFITO, CARBON, TERRACOTA, TINTA, SALVIA, ARCILLA, LADRILLO,
           X_COL, C_COL, B_COL, F_COL, X_TINT, C_TINT, B_TINT, F_TINT}
PALETTE_NAMES = {WHITE: "blanco", LINO: "lino", BRUMA: "bruma", NIEBLA: "niebla", PIEDRA: "piedra", GRAFITO: "grafito", CARBON: "carbón",
                 TERRACOTA: "terracota", TINTA: "tinta", SALVIA: "salvia", ARCILLA: "arcilla", LADRILLO: "ladrillo",
                 X_COL: "ciruela (Custom)", C_COL: "índigo (Conservador)", B_COL: "petróleo (Base)", F_COL: "verde bosque (Favorable)",
                 X_TINT: "tinte Custom", C_TINT: "tinte Conservador", B_TINT: "tinte Base", F_TINT: "tinte Favorable"}
# alias de compatibilidad con el código heredado (todos dentro de la paleta)
AZUL_IN = TINTA
ARENA_L = NIEBLA
ARENA_D = NIEBLA
OCRE = ARCILLA

FONT = "Calibri"
FONT_LIGHT = "Calibri Light"
FONTS_OK = {FONT, FONT_LIGHT}
MIN_PT = 8.5           # tamaño mínimo (check_estilo); el Gantt de 03 admite 8
SZ_TITLE, SZ_SECTION, SZ_BODY, SZ_TABLE, SZ_NOTE, SZ_KPI, SZ_KPI_LABEL = 18, 11, 10, 9, 8.5, 22, 8.5

# ---------------------------------------------------------------- formatos numéricos (Excel los muestra en el idioma del lector)
FMT_USD = '#,##0;(#,##0);"–"'
FMT_USD_D = '"$"#,##0;("$"#,##0);"–"'
FMT_INT = '#,##0;(#,##0);"–"'
FMT_PCT = '0.0%'
FMT_PCT0 = '0%'
FMT_PCT2 = '0.00%'
FMT_KWH = '0.0000'
FMT_WP = '0.000'
FMT_X = '0.00"x"'
FMT_YRS = '0.0'
FMT_DATE = 'dd-mmm-yyyy'
FMT_DEC1 = '#,##0.0'
FMT_DEC2 = '#,##0.00'
FMT_PP = '+0.00;"−"0.00;0.00'
FMT_PP1 = '+0.0;"−"0.0;0.0'
FMT_PP1_NOZERO = '+0.0;"−"0.0;'   # etiquetas del tornado: el cero no se muestra
FMT_SIGNPCT = '+0.0%;"−"0.0%;0.0%'
FMT_K = '#,##0,"k";(#,##0,"k");0'        # ejes en miles de USD
FMT_M = '#,##0.0,,"M";(#,##0.0,,"M");0'  # ejes en millones de USD

# ---------------------------------------------------------------- bordes
hair = Side(style="thin", color=NIEBLA)          # separador de filas
rule = Side(style="thin", color=CARBON)          # regla de cabecera de tabla y de totales
rule_thin = Side(style="thin", color=CARBON)
rule_soft = Side(style="thin", color=NIEBLA)     # regla de cabecera de hoja / tarjetas
rule_hero = Side(style="medium", color=TERRACOTA)
dotted_confirm = Side(style="dotted", color=ARCILLA)
dark = Side(style="thin", color=CARBON)
B_BOTTOM = Border(bottom=hair)
B_HDR = Border(bottom=rule)
B_TOTAL = Border(top=rule, bottom=hair)
B_NONE = Border()
B_CONFIRM = Border(bottom=dotted_confirm)
BORDER_THIN = B_BOTTOM
BORDER_BOTTOM = B_BOTTOM


def font(bold=False, color=CARBON, size=SZ_BODY, italic=False, name=FONT):
    return Font(name=name, bold=bold, color=color, size=size, italic=italic)


def fill(hex_):
    assert hex_ in PALETTE, f"color fuera de paleta: {hex_}"
    return PatternFill("solid", start_color=hex_, end_color=hex_)


def col(c):
    return get_column_letter(c)


def widths(ws, mapping):
    for k, v in mapping.items():
        ws.column_dimensions[k].width = v


def name(wb, nm, sheet, ref):
    wb.defined_names[nm] = DefinedName(nm, attr_text=f"'{sheet}'!{ref}")


def comment(cell, text, author="Exergy", width=340, height=120):
    """Comentario de celda (detalle largo de una nota corta). No se imprime."""
    if not text:
        return
    cm = Comment(str(text), author)
    cm.width, cm.height = width, height
    cell.comment = cm


# ---------------------------------------------------------------- altura de fila
LINE_PT = {8: 11.6, 8.5: 12.3, 9: 13.0, 9.5: 13.6, 10: 14.4, 11: 15.8, 18: 25, 22: 30}
CHARS_PER_WIDTH = {8: 1.55, 8.5: 1.46, 9: 1.38, 9.5: 1.31, 10: 1.24, 11: 1.13, 18: 0.62, 22: 0.5}   # calibrado en el render r12 (Excel/Mac: 9 pt ≈ 1,5 caracteres por unidad de ancho; 8 % de margen)
# identidad del libro (el orquestador las sobreescribe)
VERSION_TAG = "v2.0"
HOME_SHEET = "00_Portada"
HOME_LABEL = "Portada"
GUIDE_SHEET = "00b_Guía"
GUIDE_LABEL = "? Guía"
FOOTER_TEXT = "Exergy EXG S.A.S. · Modelo FV 5 MWp Montecristi → GPM · v2.0"
META_LIVE = True   # la meta de la cabecera es una fórmula que lee los nombres Version y Fecha_Analisis


def est_lines(text, width, size=9):
    if text is None:
        return 1
    text = str(text)
    if text.startswith("="):
        # fórmula de texto: estimamos por la longitud de los literales (≈ 70 % del largo)
        text = "x" * int(len(text) * 0.7)
    cpl = max(4.0, width * CHARS_PER_WIDTH.get(size, 1.15))
    lines = 0
    for para in text.split("\n"):
        lines += max(1, math.ceil(len(para) / cpl))
    return lines


def fit_row(ws, row, specs, min_h=15.0, pad=4.0, grow=False):
    """specs: lista de (texto, ancho_columna, tamaño_fuente). Ajusta la altura de la fila al texto más largo.
    grow=True: nunca reduce una altura ya fijada (filas compartidas por dos bloques)."""
    h = min_h
    for text, width, size in specs:
        n = est_lines(text, width, size)
        h = max(h, n * LINE_PT.get(size, 13.0) + pad)
    if grow and ws.row_dimensions[row].height:
        h = max(h, ws.row_dimensions[row].height)
    ws.row_dimensions[row].height = h


def merged_width(ws, c1, c2):
    return sum((ws.column_dimensions[col(c)].width or 8.43) for c in range(c1, c2 + 1))


def link_cell(ws, row, c, text, target, size=SZ_NOTE, align="right", valign="center", chip=False, bold=False):
    """Hipervínculo interno (terracota, subrayado; bold=True para los enlaces de cabecera). target: "#'Hoja'!A1" o "#Nombre".
    chip=True: botón (fondo bruma, negrita, centrado, sin subrayado) — sólo donde la celda tiene ancho suficiente (portada)."""
    cell = ws.cell(row=row, column=c, value=text)
    if isinstance(target, str) and target.startswith("#"):
        # enlace interno como `location` (sin relación externa): Excel rechaza un Target con espacios o comillas (p. ej. #'Legal y riesgos'!A1)
        from openpyxl.worksheet.hyperlink import Hyperlink
        cell.hyperlink = Hyperlink(ref=cell.coordinate, location=target[1:], display=str(text))
    else:
        cell.hyperlink = target
    if chip:
        cell.font = Font(name=FONT, size=size, color=TERRACOTA, bold=True)
        cell.fill = fill(BRUMA)
        cell.alignment = Alignment(horizontal="center", vertical=valign)
    else:
        cell.font = Font(name=FONT, size=size, color=TERRACOTA, underline="single", bold=bold)
        cell.alignment = Alignment(horizontal=align, vertical=valign)
    return cell


def span_left(ws, end_col, need, min_col=2):
    """Primera columna de un tramo que, terminando en end_col, suma al menos `need` unidades de ancho (para enlaces/meta
    que no deben desbordar la celda: Excel imprime páginas en blanco si un texto sobresale de la última columna)."""
    w, c = 0.0, end_col
    while c >= min_col and w < need:
        w += ws.column_dimensions[col(c)].width or 8.43
        c -= 1
    return c + 1


# ---------------------------------------------------------------- componentes
def sheet_header(ws, title, purpose, n, total=16, last_col=12, wb=None, guide=True, home=True):
    """Cabecera común: título 18 Light carbón (fila 1) · meta viva a la derecha + enlaces «← Portada» y «? Guía» ·
    lectura 9 piedra (fila 2) · regla niebla (fila 3)."""
    c = ws.cell(row=1, column=2, value=title)
    c.font = Font(name=FONT_LIGHT, size=SZ_TITLE, color=CARBON)
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 30
    if META_LIVE:
        meta = f'="Hoja {n}/{total}  ·  "&Version&"  ·  "&TEXT(Fecha_Analisis,"dd-mmm-yyyy")'
    else:
        meta = f"Hoja {n}/{total}  ·  {VERSION_TAG}"
    # enlaces «← Portada» y «? Guía»: texto terracota negrita subrayado, alineado a la derecha, sobre tramos de columnas con
    # ancho suficiente (≥ 11 / ≥ 8 unidades) para que nunca sobresalgan de la última columna (Excel añadiría páginas en blanco)
    end = last_col
    if guide:
        g0 = span_left(ws, end, 8.0, min_col=4)
        link_cell(ws, 1, g0, GUIDE_LABEL, f"#'{GUIDE_SHEET}'!A1", size=SZ_TABLE, bold=True)
        if end > g0:
            ws.merge_cells(start_row=1, start_column=g0, end_row=1, end_column=end)
        end = g0 - 1
    if home:
        h0 = span_left(ws, end, 11.0, min_col=4)
        link_cell(ws, 1, h0, f"← {HOME_LABEL}", f"#'{HOME_SHEET}'!A1", size=SZ_TABLE, bold=True)
        if end > h0:
            ws.merge_cells(start_row=1, start_column=h0, end_row=1, end_column=end)
        end = h0 - 1
    mc_end = end
    mc = max(4, min(mc_end, span_left(ws, mc_end, 24.0, min_col=4)))   # la meta empieza en D como mínimo: el título puede desbordar sobre C
    r = ws.cell(row=1, column=mc, value=meta)
    r.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO)
    r.alignment = Alignment(horizontal="right", vertical="center")
    if mc_end > mc:
        ws.merge_cells(start_row=1, start_column=mc, end_row=1, end_column=mc_end)
    c = ws.cell(row=2, column=2, value=purpose)
    c.font = font(size=SZ_TABLE, color=GRAFITO)
    c.alignment = Alignment(vertical="top", wrap_text=True)
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=last_col)
    fit_row(ws, 2, [(purpose, merged_width(ws, 2, last_col) - 2, 9)], min_h=14, pad=6)
    for cc in range(2, last_col + 1):
        ws.cell(row=3, column=cc).border = Border(bottom=rule_soft)
    ws.row_dimensions[3].height = 6
    ws.sheet_view.showGridLines = False


def section(ws, row, c1, c2, text, guide=None, guide_col=None, fill_hex=None):
    """Sección: fila con fondo bruma, texto 11 semibold carbón (sin mayúsculas forzadas) y guía de una frase en gris."""
    for cc in range(c1, c2 + 1):
        cell = ws.cell(row=row, column=cc)
        cell.fill = fill(BRUMA)
        cell.border = B_NONE
    c = ws.cell(row=row, column=c1, value=text)
    c.font = font(bold=True, size=SZ_SECTION, color=CARBON)
    c.alignment = Alignment(vertical="center")
    if guide:
        gc = guide_col or (c1 + 1)
        g = ws.cell(row=row, column=gc, value=guide)
        g.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO)
        g.alignment = Alignment(vertical="center", horizontal="left", wrap_text=False)
        if c2 > gc:
            ws.merge_cells(start_row=row, start_column=gc, end_row=row, end_column=c2)
    ws.row_dimensions[row].height = max(20, ws.row_dimensions[row].height or 0)


def hdr(ws, row, c1, c2, texts=None, fill_hex=None, color=GRAFITO, height=None, wrap=True, align="center", size=SZ_TABLE):
    """Encabezado de tabla: blanco, 9 semibold grafito, regla inferior carbón."""
    for c in range(c1, c2 + 1):
        cell = ws.cell(row=row, column=c)
        if fill_hex:
            cell.fill = fill(fill_hex)
        cell.font = Font(name=FONT, bold=True, color=color, size=size)
        cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
        cell.border = B_HDR
    if texts:
        for i, t in enumerate(texts):
            ws.cell(row=row, column=c1 + i, value=t)
            if i == 0:
                ws.cell(row=row, column=c1).alignment = Alignment(horizontal="left", vertical="center", wrap_text=wrap)
    ws.row_dimensions[row].height = max(height or 18, ws.row_dimensions[row].height or 0)


def label(ws, row, c, text, bold=False, color=CARBON, italic=False, size=SZ_BODY, wrap=False, indent=0, valign="center", border=True):
    cell = ws.cell(row=row, column=c, value=text)
    cell.font = Font(name=FONT, bold=bold, color=color, italic=italic, size=size)
    cell.alignment = Alignment(vertical=valign, wrap_text=wrap, indent=indent)
    if border:
        cell.border = B_BOTTOM
    return cell


def unit(ws, row, c, text, size=SZ_TABLE):
    cell = ws.cell(row=row, column=c, value=text)
    cell.font = font(size=size, color=GRAFITO)
    cell.alignment = Alignment(vertical="center", horizontal="left")
    cell.border = B_BOTTOM
    return cell


def note(ws, row, c, text, size=SZ_NOTE, valign="top", border=False, c2=None, color=GRAFITO, italic=False):
    cell = ws.cell(row=row, column=c, value=text)
    cell.font = Font(name=FONT, size=size, color=color, italic=italic)
    cell.alignment = Alignment(vertical=valign, wrap_text=True)
    if border:
        cell.border = B_BOTTOM
    if c2 and c2 > c:
        ws.merge_cells(start_row=row, start_column=c, end_row=row, end_column=c2)
    return cell


def inp(ws, row, c, value, fmt=None, confirm=False, comment_text=None, size=SZ_BODY, comment=None):
    """Entrada editable: texto tinta sin relleno, regla inferior niebla; «por confirmar» = subrayado punteado arcilla."""
    cell = ws.cell(row=row, column=c, value=value)
    cell.font = Font(name=FONT, color=TINTA, size=size)
    cell.border = B_CONFIRM if confirm else B_BOTTOM
    cell.alignment = Alignment(horizontal="right", vertical="center")
    if fmt:
        cell.number_format = fmt
    txt = comment_text or comment
    if txt:
        globals()["comment"](cell, txt)
    return cell


def calc(ws, row, c, formula, fmt=None, bold=False, color=CARBON, fill_hex=None, border=True, align="right", size=SZ_BODY):
    cell = ws.cell(row=row, column=c, value=formula)
    cell.font = Font(name=FONT, color=color, size=size, bold=bold)
    cell.alignment = Alignment(horizontal=align, vertical="center")
    if fmt:
        cell.number_format = fmt
    if fill_hex:
        cell.fill = fill(fill_hex)
    if border:
        cell.border = B_BOTTOM
    return cell


def link(ws, row, c, formula, fmt=None, bold=False, size=SZ_BODY):
    return calc(ws, row, c, formula, fmt=fmt, bold=bold, color=GRAFITO, size=size)


def canon(ws, row, c, value, fmt=None, size=SZ_BODY):
    """Valor canónico (vectores pvlib, consumos): texto grafito, sin relleno."""
    cell = ws.cell(row=row, column=c, value=value)
    cell.font = Font(name=FONT, color=GRAFITO, size=size)
    cell.border = B_BOTTOM
    cell.alignment = Alignment(horizontal="right", vertical="center")
    if fmt:
        cell.number_format = fmt
    return cell


def total_row(ws, row, c1, c2):
    """Fila total: negrita + regla superior carbón, sin relleno."""
    for c in range(c1, c2 + 1):
        cell = ws.cell(row=row, column=c)
        colr = cell.font.color.rgb if (cell.font and cell.font.color and isinstance(cell.font.color.rgb, str)) else CARBON
        if len(colr) == 8:
            colr = colr[2:]
        cell.font = Font(name=FONT, bold=True, size=cell.font.size or SZ_BODY, color=colr if colr in PALETTE else CARBON)
        cell.border = B_TOTAL


CHIP_COLORS = {"ok": SALVIA, "warn": ARCILLA, "risk": LADRILLO, "info": GRAFITO, "acc": TERRACOTA, "custom": X_COL}


def chip(ws, row, c, formula, kind="ok", size=SZ_TABLE, c2=None, bold=True):
    """Estado como texto coloreado (sin relleno): ok=salvia, warn=arcilla, risk=ladrillo, info=piedra, acc=terracota."""
    cell = ws.cell(row=row, column=c, value=formula)
    cell.font = Font(name=FONT, size=size, bold=bold, color=CHIP_COLORS[kind])
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    if c2 and c2 > c:
        ws.merge_cells(start_row=row, start_column=c, end_row=row, end_column=c2)
    return cell


def callout(ws, row, c1, c2, text, size=SZ_TABLE, height=None):
    """Nota destacada: celda combinada con regla izquierda niebla y texto grafito."""
    cell = ws.cell(row=row, column=c1, value=text)
    cell.font = Font(name=FONT, size=size, color=GRAFITO)
    cell.alignment = Alignment(vertical="top", wrap_text=True, indent=1)
    ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
    cell.border = Border(left=Side(style="medium", color=NIEBLA))
    if height:
        ws.row_dimensions[row].height = height
    else:
        fit_row(ws, row, [(text, merged_width(ws, c1, c2) - 2, size)], min_h=18)
    return cell


def kpi_card(ws, r, c, w, label_txt, formula, fmt, sub_formula=None, hero=False, color=None, heights=(16, 30, 26)):
    """Tarjeta KPI: 3 filas (etiqueta MAYÚSCULAS 8,5 piedra / valor Calibri Light 22 / contexto 8,5) con regla superior
    niebla (héroe: terracota) y sin relleno. `color` se ignora salvo hero (compatibilidad)."""
    for rr in (r, r + 1, r + 2):
        ws.merge_cells(start_row=rr, start_column=c, end_row=rr, end_column=c + w - 1)
    for cc in range(c, c + w):
        ws.cell(row=r, column=cc).border = Border(top=rule_hero if hero else rule_soft)
    lab = ws.cell(row=r, column=c, value=label_txt)
    lab.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO)
    lab.alignment = Alignment(horizontal="left", vertical="bottom", wrap_text=True)
    val = ws.cell(row=r + 1, column=c, value=formula)
    val.font = Font(name=FONT_LIGHT, size=SZ_KPI, color=TERRACOTA if hero else CARBON)
    val.alignment = Alignment(horizontal="left", vertical="center")
    val.number_format = fmt
    if sub_formula is not None:
        sub = ws.cell(row=r + 2, column=c, value=sub_formula)
        sub.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO)
        sub.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    ws.row_dimensions[r].height = heights[0]
    ws.row_dimensions[r + 1].height = heights[1]
    ws.row_dimensions[r + 2].height = heights[2]


def status_line(ws, row, c, formula, kind="ok", size=SZ_TABLE):
    """Estado de la portada (● ◇ ▲ ■) como texto; sin relleno ni borde."""
    cell = ws.cell(row=row, column=c, value=formula)
    cell.font = Font(name=FONT, size=size, bold=False, color=CHIP_COLORS[kind])
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
    return cell


# ---------------------------------------------------------------- v2.0 · componentes de caso
rule_caso = {k: Side(style="medium", color=v) for k, v in CASO_COL.items()}   # regla superior 1,5 pt del color del caso


def caso_hdr(ws, row, c, caso, text=None, c2=None, align="right", size=SZ_TABLE, height=None):
    """Cabecera de columna de caso: texto negrita del color del caso + regla superior 1,5 pt del mismo color + regla inferior carbón.
    Sin relleno (doc 11 §1.3). `caso` ∈ X/C/B/F; text por defecto = nombre del caso."""
    cell = ws.cell(row=row, column=c, value=text if text is not None else CASO_NOMBRE[caso])
    cell.font = Font(name=FONT, bold=True, color=CASO_COL[caso], size=size)
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
    for cc in range(c, (c2 or c) + 1):
        ws.cell(row=row, column=cc).border = Border(top=rule_caso[caso], bottom=rule)
    if c2 and c2 > c:
        ws.merge_cells(start_row=row, start_column=c, end_row=row, end_column=c2)
    if height:
        ws.row_dimensions[row].height = max(height, ws.row_dimensions[row].height or 0)
    return cell


def caso_val(ws, row, c, formula, caso=None, fmt=None, bold=False, size=SZ_TABLE, color=None):
    """Valor de una tabla comparativa: carbón por defecto (el color de caso va en la cabecera); `color` fuerza otro."""
    cell = ws.cell(row=row, column=c, value=formula)
    cell.font = Font(name=FONT, color=color or CARBON, size=size, bold=bold)
    cell.alignment = Alignment(horizontal="right", vertical="center")
    cell.border = B_BOTTOM
    if fmt:
        cell.number_format = fmt
    return cell


def caso_strip(ws, row, c0, formulas, size=SZ_NOTE, casos=("C", "B", "F"), align="left"):
    """Tira «C · B · F» bajo una tarjeta: una celda por caso (fórmula viva), texto negrita del color del caso. Toda cifra es fórmula."""
    cells = []
    for k, (caso, f) in enumerate(zip(casos, formulas)):
        cell = ws.cell(row=row, column=c0 + k, value=f)
        cell.font = Font(name=FONT, size=size, bold=True, color=CASO_COL[caso])
        cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=False)
        cells.append(cell)
    return cells


def caso_legend(ws, row, c0, casos=CASOS, size=SZ_NOTE, glyph="■", step=1, merge=None):
    """Leyenda de casos: «■ Custom  ■ Conservador  ■ Base  ■ Favorable», una celda por caso (texto estático, sin cifras)."""
    for k, caso in enumerate(casos):
        c = c0 + k * step
        cell = ws.cell(row=row, column=c, value=f"{glyph} {CASO_NOMBRE[caso]}")
        cell.font = Font(name=FONT, size=size, bold=True, color=CASO_COL[caso])
        cell.alignment = Alignment(horizontal="left", vertical="center")
        if merge and merge > 1:
            ws.merge_cells(start_row=row, start_column=c, end_row=row, end_column=c + merge - 1)


def caso_tag(ws, row, c, caso="X", text=None, size=SZ_TABLE):
    """Etiqueta de caso en un título o sección (p. ej. «CUSTOM» en ciruela)."""
    cell = ws.cell(row=row, column=c, value=(text if text is not None else CASO_NOMBRE[caso]).upper())
    cell.font = Font(name=FONT, size=size, bold=True, color=CASO_COL[caso])
    cell.alignment = Alignment(horizontal="left", vertical="center")
    return cell


def setup_print(ws, landscape=True, fit_width=True, title_rows=None, title_cols=None, one_page=False, width_pages=1, scale=None, area=None):
    """Impresión A4: ajustar a `width_pages` de ancho (alto libre) o a 1 página; títulos repetidos; pie común."""
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    if scale:
        ws.sheet_properties.pageSetUpPr.fitToPage = False
        ws.page_setup.scale = scale
    else:
        ws.page_setup.fitToWidth = width_pages
        ws.page_setup.fitToHeight = 1 if one_page else 0
        ws.sheet_properties.pageSetUpPr.fitToPage = fit_width
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.6
    ws.page_margins.footer = 0.25
    ws.oddFooter.left.text = FOOTER_TEXT
    ws.oddFooter.left.size = 7
    ws.oddFooter.right.text = "&A · pág. &P/&N"
    ws.oddFooter.right.size = 7
    if title_rows:
        ws.print_title_rows = title_rows
    if title_cols:
        ws.print_title_cols = title_cols
    if area:
        ws.print_area = area
    ws.sheet_view.showGridLines = False


# ---------------------------------------------------------------- gráficos: plantilla v2
# numFmt de las etiquetas con sourceLinked="0" (openpyxl sólo escribe formatCode y Excel usa entonces el formato de la celda origen)
for _cls in (DataLabelList, DataLabel):
    _cls.numFmt = Typed(expected_type=NumFmt, allow_none=True, name="numFmt")
    _cls.__nested__ = tuple(x for x in _cls.__nested__ if x != "numFmt")


def _nf(fmt):
    return NumFmt(formatCode=fmt, sourceLinked=False) if fmt else None


CHART_STYLE_ID = 2          # marcador de la plantilla (check_estilo lo exige en todo gráfico)
AXIS_PT = 9


def _cp(size, color, bold=False):
    return CharacterProperties(sz=int(size * 100), b=bold, solidFill=color, latin=DFont(typeface=FONT))


def _txpr(size, color, bold=False):
    cp = _cp(size, color, bold)
    return RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), endParaRPr=cp, r=[])])


def _title(text, size=10, color=CARBON, bold=True):
    cp = _cp(size, color, bold)
    return Title(tx=Text(rich=RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), r=[RegularTextRun(rPr=cp, t=text)])])), overlay=False)


def _gridlines(color=NIEBLA, w_pt=0.5):
    gl = ChartLines()
    gl.spPr = GraphicalProperties(ln=LineProperties(solidFill=color, w=int(w_pt * 12700)))
    return gl


def _style_axis(ax, fmt=None, title=None, line=False, gridlines=False, tick_low=True, tick_marks=False, lbl_offset=None):
    ax.delete = False
    ax.txPr = _txpr(AXIS_PT, GRAFITO, bold=True)   # los valores de los ejes siempre en negrita (Jorge, 03-sep)
    ax.majorTickMark = "out" if tick_marks else "none"
    ax.minorTickMark = "none"
    if lbl_offset is not None:
        try:
            ax.lblOffset = lbl_offset
        except Exception:
            pass
    if tick_low:
        ax.tickLblPos = "low"
    if fmt:
        ax.numFmt = fmt
    ax.spPr = GraphicalProperties(ln=LineProperties(solidFill=NIEBLA, w=9525)) if line else GraphicalProperties(ln=LineProperties(noFill=True))
    ax.majorGridlines = _gridlines() if gridlines else None
    if title:
        ax.title = _title(title, size=SZ_TABLE, color=GRAFITO, bold=False)


def _title_ref(ref, size=10, color=CARBON, bold=True):
    """Título enlazado a una celda (texto vivo): la fórmula de la celda decide el texto; el formato va en txPr."""
    t = Title(tx=Text(strRef=StrRef(ref)), overlay=False)
    t.txPr = _txpr(size, color, bold)
    return t


def style_chart_v2(ch, title, w=16, h=8, legend=None, y_fmt='#,##0', x_fmt=None, x_title=None, y_title=None, gridlines=True, x_line=True, title_ref=None):
    """Plantilla común v2: sin borde, cuadrícula horizontal bruma (o ninguna), ejes grafito 9 negrita, título corto a la izquierda
    (Calibri 10 semibold carbón; `title_ref` = celda con el texto vivo), leyenda sólo si se pide."""
    ch.width, ch.height = w, h
    ch.style = CHART_STYLE_ID
    ch.roundedCorners = False
    ch.display_blanks = "gap"
    try:
        ch.plotVisOnly = False   # las series pueden vivir en hojas ocultas (Motor del Resumen)
    except Exception:
        pass
    try:
        ch.varyColors = False
    except Exception:
        pass
    ch.title = _title_ref(title_ref) if title_ref else _title(title)
    try:
        ch.title.layout = Layout(manualLayout=ManualLayout(xMode="edge", yMode="edge", x=0.01, y=0.02))
    except Exception:
        pass
    ch.graphical_properties = GraphicalProperties(ln=LineProperties(noFill=True))
    ch.graphical_properties.noFill = False
    if getattr(ch, "x_axis", None) is not None:
        _style_axis(ch.x_axis, fmt=x_fmt, title=x_title, line=x_line, gridlines=False)
    if getattr(ch, "y_axis", None) is not None:
        _style_axis(ch.y_axis, fmt=y_fmt, title=y_title, line=False, gridlines=gridlines, tick_low=False)
    if legend:
        ch.legend.position = legend
        ch.legend.txPr = _txpr(SZ_TABLE, GRAFITO)
        ch.legend.overlay = False
    else:
        ch.legend = None
    return ch


def series_line(s, color, width_pt=2.0, dash=None, marker=None, marker_size=7, smooth=False):
    s.graphicalProperties.line.solidFill = color
    s.graphicalProperties.line.width = int(width_pt * 12700)
    if dash:
        s.graphicalProperties.line.prstDash = dash
    s.smooth = smooth
    if marker:
        s.marker = Marker(symbol=marker, size=marker_size)
        s.marker.graphicalProperties = GraphicalProperties(solidFill=color)
        s.marker.graphicalProperties.line.solidFill = color
    else:
        s.marker = Marker(symbol="none")
    return s


def series_bar(s, color):
    s.graphicalProperties.solidFill = color
    s.graphicalProperties.line.noFill = True
    try:
        s.invertIfNegative = False   # Excel invierte a blanco las barras negativas si se omite
    except Exception:
        pass
    return s


def series_marker_only(s, color, size=7, symbol="circle"):
    """Serie de un punto (caso activo): sin línea, marcador relleno."""
    s.graphicalProperties.line.noFill = True
    s.marker = Marker(symbol=symbol, size=size)
    s.marker.graphicalProperties = GraphicalProperties(solidFill=color)
    s.marker.graphicalProperties.line.solidFill = color
    return s


def series_fill(s, color, line=False, width_pt=2.0):
    """Compatibilidad: barra (line=False) o línea (line=True)."""
    return series_line(s, color, width_pt=width_pt) if line else series_bar(s, color)


def point_color(s, idx, color):
    pt = DataPoint(idx=idx)
    pt.graphicalProperties.solidFill = color
    pt.graphicalProperties.line.noFill = True
    s.dPt.append(pt)
    return pt


def labels(s, idxs=None, fmt=None, pos=None, size=SZ_NOTE, color=GRAFITO, show_all=False, bold=True, cat_name=False, ser_name=False, separator=None):
    """Etiquetas de datos (negrita por defecto): sólo en los índices dados (o en todos con show_all).
    cat_name / ser_name: mostrar la categoría (p. ej. el año t) o el nombre de la serie en lugar del valor.
    pos: posición común ("t", "b", "l", "r", "outEnd"…) o una lista paralela a idxs (posición por punto)."""
    dl = DataLabelList()
    pos_list = list(pos) if isinstance(pos, (list, tuple)) else None
    if pos_list:
        pos = pos_list[0]
    dl.showVal = bool(show_all) and not (cat_name or ser_name)
    dl.showSerName = bool(show_all) and ser_name
    dl.showCatName = bool(show_all) and cat_name
    dl.showLegendKey = False
    dl.showPercent = False
    dl.showLeaderLines = False
    if separator:
        dl.separator = separator
    if fmt:
        dl.numFmt = _nf(fmt)
    dl.txPr = _txpr(size, color, bold)
    if pos:
        dl.dLblPos = pos
    if idxs and not show_all:
        for k, i in enumerate(idxs):
            d = DataLabel(idx=i, showVal=not (cat_name or ser_name), showSerName=ser_name, showCatName=cat_name, showLegendKey=False, showPercent=False)
            if separator:
                d.separator = separator
            if fmt:
                d.numFmt = _nf(fmt)
            if pos_list:
                d.dLblPos = pos_list[k % len(pos_list)]
            elif pos:
                d.dLblPos = pos
            d.txPr = _txpr(size, color, bold)
            dl.dLbl.append(d)
    s.dLbls = dl
    return dl


def _add(ch, ref, title_txt, from_rows=False):
    ch.add_data(ref, titles_from_data=False, from_rows=from_rows)
    s = ch.series[-1]
    s.tx = SeriesLabel(v=title_txt)
    return s


def chart_lines(ws, anchor, title, cats, series, w=16, h=8, y_fmt='#,##0', x_fmt=None, legend=None, ref=None, x_title=None, y_title=None, gridlines=True, from_rows=False, x_skip=None, title_ref=None, hide_legend_idx=()):
    """Líneas por categoría (años). series: [dict(ref, name, color, width, dash, marker, marker_size, marker_only, labels=[idx]|'all',
    label_fmt, label_pos, label_cat (etiqueta = categoría), label_ser (etiqueta = nombre de serie), label_sep)].
    ref: dict(ref, name, color, dash) → serie constante de referencia (punteada). hide_legend_idx: series sin entrada en la leyenda."""
    ch = LineChart()
    for sp in series:
        s = _add(ch, sp["ref"], sp.get("name", ""), from_rows=from_rows)
        if sp.get("marker_only"):
            series_marker_only(s, sp.get("color", TERRACOTA), sp.get("marker_size", 8), sp.get("marker", "circle"))
        else:
            series_line(s, sp.get("color", TERRACOTA), sp.get("width", 2.0), sp.get("dash"), sp.get("marker"), sp.get("marker_size", 7))
        if sp.get("labels"):
            labels(s, None if sp["labels"] == "all" else sp["labels"], sp.get("label_fmt", y_fmt), sp.get("label_pos", "t"), color=sp.get("label_color", GRAFITO),
                   show_all=(sp["labels"] == "all"), cat_name=sp.get("label_cat", False), ser_name=sp.get("label_ser", False), separator=sp.get("label_sep"))
    if ref:
        s = _add(ch, ref["ref"], ref.get("name", "referencia"), from_rows=from_rows)
        series_line(s, ref.get("color", GRAFITO), ref.get("width", 1.25), ref.get("dash", "dash"))
        if ref.get("labels"):
            labels(s, ref["labels"], ref.get("label_fmt", y_fmt), ref.get("label_pos", "r"), color=ref.get("color", GRAFITO))
    ch.set_categories(cats)
    style_chart_v2(ch, title, w=w, h=h, legend=legend, y_fmt=y_fmt, x_fmt=x_fmt, x_title=x_title, y_title=y_title, gridlines=gridlines, title_ref=title_ref)
    if x_skip:
        ch.x_axis.tickLblSkip = x_skip
        ch.x_axis.tickMarkSkip = x_skip
    if legend and hide_legend_idx:
        from openpyxl.chart.legend import LegendEntry
        ch.legend.legendEntry = [LegendEntry(idx=i, delete=True) for i in hide_legend_idx]
    ws.add_chart(ch, anchor)
    return ch


def chart_cols(ws, anchor, title, cats, cols, lines=(), w=16, h=8, y_fmt='#,##0', legend=None, stacked=False, gap=60, x_title=None, y_title=None, gridlines=True, from_rows=False, ref=None, secondary=False, y2_fmt=None, y2_title=None, x_skip=None):
    """Columnas (opcionalmente apiladas) + líneas superpuestas en el mismo eje (o en un eje secundario a la derecha si secondary=True).
    cols/lines: [dict(ref, name, color, width, dash, labels, label_fmt, label_pos)]."""
    ch = BarChart()
    ch.type = "col"
    ch.grouping = "stacked" if stacked else "clustered"
    if stacked:
        ch.overlap = 100
    ch.gapWidth = gap
    for sp in cols:
        s = _add(ch, sp["ref"], sp.get("name", ""), from_rows=from_rows)
        series_bar(s, sp.get("color", GRAFITO))
        for k_, colr_ in enumerate(sp.get("point_colors") or ()):   # v2.0: una barra por caso, cada una con su color
            point_color(s, k_, colr_)
        if sp.get("labels"):
            labels(s, None if sp["labels"] == "all" else sp["labels"], sp.get("label_fmt", y_fmt), sp.get("label_pos", "outEnd"), color=sp.get("label_color", GRAFITO), show_all=(sp["labels"] == "all"))
    ch.set_categories(cats)
    style_chart_v2(ch, title, w=w, h=h, legend=legend, y_fmt=y_fmt, x_title=x_title, y_title=y_title, gridlines=gridlines)
    if x_skip:
        ch.x_axis.tickLblSkip = x_skip
        ch.x_axis.tickMarkSkip = x_skip
    if lines or ref:
        ln = LineChart()
        for sp in lines:
            s = _add(ln, sp["ref"], sp.get("name", ""), from_rows=from_rows)
            series_line(s, sp.get("color", TERRACOTA), sp.get("width", 2.0), sp.get("dash"), sp.get("marker"), sp.get("marker_size", 7))
            if sp.get("labels"):
                labels(s, sp["labels"], sp.get("label_fmt", y_fmt), sp.get("label_pos", "t"), color=sp.get("label_color", GRAFITO))
        if ref:
            s = _add(ln, ref["ref"], ref.get("name", "referencia"), from_rows=from_rows)
            series_line(s, ref.get("color", GRAFITO), ref.get("width", 1.25), ref.get("dash", "dash"))
            if ref.get("labels"):
                labels(s, ref["labels"], ref.get("label_fmt", y_fmt), ref.get("label_pos", "r"), color=ref.get("color", GRAFITO))
        ln.set_categories(cats)
        if secondary:
            ln.y_axis.axId = 200
            ln.y_axis.crosses = "max"
            _style_axis(ln.y_axis, fmt=y2_fmt or y_fmt, title=y2_title, line=False, gridlines=False, tick_low=False)
        ch += ln
    ws.add_chart(ch, anchor)
    return ch


def chart_tornado(ws, anchor, title, cats, low_ref, high_ref, w=16, h=8, fmt=FMT_PP1_NOZERO, names=("caso bajo", "caso alto"), x_title=None, title_ref=None, gridlines=True, lbl_offset=400):
    """Barras horizontales desde 0: bajo = niebla, alto = terracota; etiquetas ±; cuadrícula vertical niebla en los puntos
    porcentuales, marcas en el eje de valores y etiquetas de categoría separadas del eje; primera variable arriba."""
    ch = BarChart()
    ch.type = "bar"
    ch.grouping = "clustered"
    ch.overlap = 100
    ch.gapWidth = 55
    s0 = _add(ch, low_ref, names[0]); series_bar(s0, NIEBLA); labels(s0, fmt=fmt, pos="outEnd", show_all=True, color=GRAFITO)
    s1 = _add(ch, high_ref, names[1]); series_bar(s1, TERRACOTA); labels(s1, fmt=fmt, pos="outEnd", show_all=True, color=TERRACOTA)
    ch.set_categories(cats)
    style_chart_v2(ch, title, w=w, h=h, legend=None, y_fmt=fmt, gridlines=False, x_title=x_title, title_ref=title_ref)
    ch.x_axis.scaling.orientation = "maxMin"
    ch.x_axis.tickLblPos = "low"
    ch.y_axis.tickLblPos = "low"
    if gridlines:
        ch.y_axis.majorGridlines = _gridlines()
    # ejes visibles: línea piedra con marcas («índice») en el eje de valores; el eje de categorías es la línea del cero
    ch.y_axis.majorTickMark = "out"
    ch.y_axis.spPr = GraphicalProperties(ln=LineProperties(solidFill=PIEDRA, w=9525))
    ch.x_axis.spPr = GraphicalProperties(ln=LineProperties(solidFill=PIEDRA, w=9525))
    ch.x_axis.majorTickMark = "none"
    if lbl_offset:
        ch.x_axis.lblOffset = lbl_offset
    ws.add_chart(ch, anchor)
    return ch


def chart_hbars(ws, anchor, title, cats, vals, w=16, h=8, fmt=FMT_USD, accent_idx=None, name_txt="", gridlines=False, x_title=None):
    """Barras horizontales grafito con etiquetas; acento terracota en `accent_idx`; categorías en el orden de la tabla."""
    ch = BarChart()
    ch.type = "bar"
    ch.grouping = "clustered"
    ch.gapWidth = 60
    s = _add(ch, vals, name_txt)
    series_bar(s, GRAFITO)
    if accent_idx is not None:
        point_color(s, accent_idx, TERRACOTA)
    labels(s, fmt=fmt, pos="outEnd", show_all=True, color=GRAFITO)
    ch.set_categories(cats)
    style_chart_v2(ch, title, w=w, h=h, legend=None, y_fmt=fmt, gridlines=gridlines, x_title=x_title)
    ch.x_axis.scaling.orientation = "maxMin"
    ch.y_axis.delete = True
    ws.add_chart(ch, anchor)
    return ch


def chart_scatter(ws, anchor, title, series, w=16, h=8, x_fmt='#,##0', y_fmt='#,##0', x_title=None, y_title=None, legend=None,
                  x_min=None, x_max=None, y_min=None, y_max=None, gridlines=True):
    """Dispersión con líneas rectas (eje X numérico): barridos §F. series: [dict(x, y, name, color, width, dash, marker, marker_size,
    kind='line'|'point'|'ref', labels=[idx]|'all', label_fmt, label_pos)]."""
    ch = ScatterChart()
    ch.scatterStyle = "lineMarker"
    for sp in series:
        s = XSeries(sp["y"], sp["x"], title=sp.get("name", ""))
        ch.series.append(s)
        kind = sp.get("kind", "line")
        colr = sp.get("color", TERRACOTA)
        if kind == "point":
            series_marker_only(s, colr, sp.get("marker_size", 7), sp.get("marker", "circle"))
        elif kind == "ref":
            series_line(s, sp.get("color", GRAFITO), sp.get("width", 1.25), sp.get("dash", "dash"))
        else:
            series_line(s, colr, sp.get("width", 2.0), sp.get("dash"), sp.get("marker"), sp.get("marker_size", 7))
        if sp.get("labels") is not None:
            labels(s, None if sp["labels"] == "all" else sp["labels"], sp.get("label_fmt", y_fmt), sp.get("label_pos", "r"),
                   color=sp.get("label_color", colr if kind != "line" else GRAFITO), show_all=(sp["labels"] == "all"))
    style_chart_v2(ch, title, w=w, h=h, legend=legend, y_fmt=y_fmt, x_fmt=x_fmt, x_title=x_title, y_title=y_title, gridlines=gridlines)
    ch.x_axis.tickLblPos = "low"
    if x_min is not None:
        ch.x_axis.scaling.min = x_min
    if x_max is not None:
        ch.x_axis.scaling.max = x_max
    if y_min is not None:
        ch.y_axis.scaling.min = y_min
    if y_max is not None:
        ch.y_axis.scaling.max = y_max
    ws.add_chart(ch, anchor)
    return ch


# compatibilidad con el código heredado (hasta que cada builder migre a las plantillas)
def style_chart(ch, title, w=16, h=8, legend="b", y_fmt='#,##0', x_title=None, y_title=None):
    return style_chart_v2(ch, title, w=w, h=h, legend=("tr" if legend else None), y_fmt=y_fmt, x_title=x_title, y_title=y_title)


# ---------------------------------------------------------------- v3.0 (V-b): literales de texto > 255 caracteres
MAX_LITERAL = 255


def _literal_spans(formula):
    """Posiciones (inicio, fin) de cada literal "…" de una fórmula (las comillas dobladas "" son una comilla dentro del literal)."""
    spans, i, n = [], 0, len(formula)
    while i < n:
        if formula[i] == '"':
            j = i + 1
            while j < n:
                if formula[j] == '"':
                    if j + 1 < n and formula[j + 1] == '"':
                        j += 2; continue
                    break
                j += 1
            spans.append((i, j)); i = j + 1
        else:
            i += 1
    return spans


def split_long_literals(formula, limit=MAX_LITERAL):
    """Divide cada literal de más de `limit` caracteres en trozos concatenados con & (en un espacio, si lo hay), para que Excel no
    lo reescriba como _xlfn._LONGTEXT (riesgo #NAME? en versiones antiguas). El valor mostrado no cambia."""
    if not isinstance(formula, str) or not formula.startswith("=") or '"' not in formula:
        return formula
    out, last = [], 0
    for a, b in _literal_spans(formula):
        inner = formula[a + 1:b]
        if len(inner) <= limit:
            continue
        parts = []
        while len(inner) > limit:
            cut = inner.rfind(" ", limit // 2, limit)
            cut = cut + 1 if cut > 0 else limit
            # no cortar entre dos comillas dobladas
            if inner[cut - 1:cut + 1] == '""':
                cut -= 1
            parts.append(inner[:cut]); inner = inner[cut:]
        parts.append(inner)
        out.append(formula[last:a]); out.append("&".join(f'"{p}"' for p in parts)); last = b + 1
    if not out:
        return formula
    out.append(formula[last:])
    return "".join(out)


def long_literals(formula, limit=MAX_LITERAL):
    """Lista de literales > limit de una fórmula (para check_estilo)."""
    if not isinstance(formula, str) or not formula.startswith("=") or '"' not in formula:
        return []
    return [formula[a + 1:b] for a, b in _literal_spans(formula) if b - a - 1 > limit]


def chart_cascade(ws, anchor, title, cats, base_ref, delta_ref, point_colors, w=16, h=6.5, y_fmt='0.0%', label_fmt='0.00%', from_rows=True, x_title=None, title_ref=None, y_min=None, label_idxs=None):
    """v3.0: gráfico de cascada (puente): columnas apiladas con una serie base invisible y una serie Δ coloreada por punto
    (totales en grafito, descensos en terracota, ascensos en salvia); etiqueta = altura de la barra (nivel en los extremos, |Δ| en los escalones)."""
    ch = BarChart()
    ch.type = "col"; ch.grouping = "stacked"; ch.overlap = 100; ch.gapWidth = 55
    s0 = _add(ch, base_ref, "base", from_rows=from_rows)
    s0.graphicalProperties.noFill = True
    s0.graphicalProperties.line.noFill = True
    s1 = _add(ch, delta_ref, "Δ", from_rows=from_rows)
    series_bar(s1, GRAFITO)
    for k_, colr_ in enumerate(point_colors):
        point_color(s1, k_, colr_)
    # etiquetas: por defecto en todos los puntos; con label_idxs sólo en los índices dados (los totales), porque en los escalones pequeños la etiqueta
    # blanca desborda la barra (render r2/r3) y la categoría ya lleva el Δ en pp
    if label_idxs is None:
        labels(s1, None, label_fmt, "inEnd", color=WHITE, show_all=True)
    else:
        labels(s1, list(label_idxs), label_fmt, "inEnd", color=WHITE)
    ch.set_categories(cats)
    style_chart_v2(ch, title, w=w, h=h, legend=None, y_fmt=y_fmt, x_title=x_title, gridlines=True, title_ref=title_ref)
    if y_min is not None:
        ch.y_axis.scaling.min = y_min
    ws.add_chart(ch, anchor)
    return ch
