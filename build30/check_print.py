# -*- coding: utf-8 -*-
"""check_print.py LIBRO.xlsx — auditoría de paginación para Excel/Mac (A4 horizontal, márgenes 0,4/0,4/0,5/0,6 in).
Factor medido en los renders r11/r12 (bandas de sección en el PDF): ancho impreso a 100 % = 6,05 pt × ancho XML de la columna
(Excel/Mac: 7 px por carácter × 0,86 pt/px; ±1 %); alto impreso de una fila ≈ (altura nominal − 1,0 pt) × escala (redondeo a píxel);
los objetos de dibujo conservan su tamaño nominal × escala. Margen de seguridad 1,5 % en ancho. Comprueba además que cada gráfico
termina antes del final de su rango de impresión / salto de fila: Σ(alto fila − 1,0) desde su fila de anclaje ≥ alto del gráfico.
Para cada hoja con escala fija comprueba que cada página de columnas (rango de impresión + saltos de columna + columnas de título)
cabe en 784 pt × escala, y que cada página de filas (rango + saltos de fila) cabe en 516 pt × escala. Sale con 1 si algo desborda."""
import re, sys
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter as L, column_index_from_string as CI

W_UTIL, H_UTIL = (841.89 - 2 * 0.4 * 72) * 0.985, 595.28 - (0.5 + 0.6) * 72   # 772 (784,3 − 1,5 %) · 516,1
wb = load_workbook(sys.argv[1])
bad = 0


def cw(ws, c):
    d = ws.column_dimensions.get(L(c))
    w = d.width if d is not None and d.width else 8.43
    if d is not None and d.hidden:
        return 0
    return 6.05 * w


def rh(ws, r):
    d = ws.row_dimensions.get(r)
    if d is not None and d.hidden:
        return 0
    return d.height if d is not None and d.height else 15


for ws in wb.worksheets:
    scale = ws.page_setup.scale
    pa = ws.print_area
    if not scale:
        continue
    s = scale / 100
    top, bottom = (ws.page_margins.top or 0.75) * 72, (ws.page_margins.bottom or 0.75) * 72
    h_util = 595.28 - top - bottom
    ranges = [x.replace("$", "").split("!")[-1] for x in (pa.split(",") if pa else [f"A1:{L(ws.max_column)}{ws.max_row}"])]
    cbrks = sorted(b.id for b in ws.col_breaks.brk)
    rbrks = sorted(b.id for b in ws.row_breaks.brk)
    tcw = 0
    tcols = ws.print_title_cols
    if tcols:
        a, b = tcols.replace("$", "").split(":")
        tcw = sum(cw(ws, c) for c in range(CI(a), CI(b) + 1))
    trh = 0
    trows = ws.print_title_rows
    if trows:
        a, b = trows.replace("$", "").split(":")
        trh = sum(max(rh(ws, r) - 1.0, 0) for r in range(int(a), int(b) + 1))
    msgs = []
    for rg in ranges:
        m = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", rg)
        c1, c2, r1, r2 = CI(m.group(1)), CI(m.group(3)), int(m.group(2)), int(m.group(4))
        cuts = [b for b in cbrks if c1 <= b < c2]
        for i, (a, b) in enumerate(zip([c1] + [x + 1 for x in cuts], cuts + [c2])):
            w = sum(cw(ws, c) for c in range(a, b + 1)) + (tcw if (tcols and a > CI(tcols.replace("$", "").split(":")[1])) else 0)
            flag = "" if w * s <= W_UTIL else "  ← DESBORDA"
            msgs.append(f"cols {L(a)}:{L(b)} {w * s:.0f}/{W_UTIL:.0f} pt{flag}")
            bad += bool(flag)
        rcuts = [b for b in rbrks if r1 <= b < r2]
        for i, (a, b) in enumerate(zip([r1] + [x + 1 for x in rcuts], rcuts + [r2])):
            hh = sum(max(rh(ws, r) - 1.0, 0) for r in range(a, b + 1)) + (trh if (trows and a > int(trows.replace("$", "").split(":")[1])) else 0)
            if hh * s > h_util - 6:
                if rbrks or len(ranges) > 1:
                    flag = "  ← DESBORDA (paginación explícita rota)"
                    bad += 1
                else:
                    flag = "  (Excel pagina solo)"
            else:
                flag = ""
            msgs.append(f"filas {a}-{b} {hh * s:.0f}/{h_util:.0f} pt{flag}")
    print(f"{ws.title:16s} escala {scale:3d} · " + " · ".join(msgs))

# ---- gráficos: ¿caben en las filas hasta el siguiente corte?
import zipfile, re as _re
z = zipfile.ZipFile(sys.argv[1])
names = z.namelist()
wbx = z.read("xl/workbook.xml").decode("utf8")
rels = z.read("xl/_rels/workbook.xml.rels").decode("utf8")
rid2target = dict(_re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)) | {b: a for a, b in _re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', rels)}
for m in _re.finditer(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="(rId\d+)"', wbx):
    sname, rid = m.group(1), m.group(2)
    target = rid2target.get(rid, "")
    sheet_xml = "xl/" + target.lstrip("/xl/") if not target.startswith("/") else target[1:]
    sheet_xml = sheet_xml if sheet_xml in names else "xl/" + target
    rel_path = sheet_xml.replace("worksheets/", "worksheets/_rels/") + ".rels"
    if rel_path not in names:
        continue
    srels = z.read(rel_path).decode("utf8")
    dr = _re.search(r'Target="[^"]*?(drawing\d+\.xml)"', srels)
    if not dr:
        continue
    dxml = z.read("xl/drawings/" + dr.group(1)).decode("utf8")
    ws = wb[sname]
    scale = ws.page_setup.scale
    pa = ws.print_area
    rbrks = sorted(b.id for b in ws.row_breaks.brk)
    ends = set(rbrks)
    if pa:
        for rg in pa.split(","):
            mm = _re.search(r"(\d+)$", rg.replace("$", ""))
            ends.add(int(mm.group(1)))
    for a in _re.finditer(r'<(?:xdr:)?oneCellAnchor>.*?<(?:xdr:)?row>(\d+)</(?:xdr:)?row>.*?<(?:xdr:)?ext [^>]*cy="(\d+)".*?</(?:xdr:)?oneCellAnchor>', dxml, _re.S):
        r0 = int(a.group(1)) + 1
        hpt = int(a.group(2)) / 12700
        stop = min([e for e in ends if e >= r0], default=None)
        if stop is None:
            continue
        avail = sum(max(rh(ws, r) - 1.0, 0) for r in range(r0, stop + 1))
        flag = "" if avail >= hpt + 6 else "  ← EL GRÁFICO CRUZA EL CORTE (Excel imprime el resto en otra página; margen mínimo 6 pt)"
        bad += bool(flag)
        print(f"   gráfico {sname} fila {r0}: alto {hpt:.0f} pt · filas hasta {stop}: {avail:.0f} pt{flag}")
# --- celdas combinadas con texto que cruzan dos rangos del área de impresión (Excel las parte entre páginas y el texto se corta;
#     caso real: notas de 09_Exergy combinadas H:N con área A1:L81 + M43:AD81, render r4 04-sep-2026)
from openpyxl.utils import range_boundaries as _rb
for ws in wb.worksheets:
    if ws.sheet_state != "visible" or not ws.print_area:
        continue
    areas = [_rb(a.split("!")[-1].replace("$", "")) for a in ws.print_area.split(",")]
    def _in_one(r1, c1, r2, c2):
        return any(mc <= c1 and c2 <= xc and mr <= r1 and r2 <= xr for mc, mr, xc, xr in areas)
    def _starts(r, c):
        return any(mc <= c <= xc and mr <= r <= xr for mc, mr, xc, xr in areas)
    for m in ws.merged_cells.ranges:
        v = ws.cell(m.min_row, m.min_col).value
        if v in (None, ""):
            continue
        if _starts(m.min_row, m.min_col) and not _in_one(m.min_row, m.min_col, m.max_row, m.max_col):
            bad += 1
            print(f"   {ws.title} {m}: celda combinada con texto partida entre dos rangos de impresión  ← SE CORTA AL IMPRIMIR")
print("✔ paginación dentro de página" if not bad else f"✖ {bad} desborde(s)")
sys.exit(1 if bad else 0)
