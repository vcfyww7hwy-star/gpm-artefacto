# -*- coding: utf-8 -*-
"""check_render.py RENDER.pdf [--budget "Hoja=n,Hoja=n,…"] [--total N] [--strict]
v3.0 (V10): control del render de Excel/Mac (pdfplumber):
 (a) texto cortado: palabras que empiezan dentro de la página y cuyo borde derecho la supera (x0 < 841,9 < x1) o que pisan el pie; las palabras
     que empiezan fuera de la caja (x0 ≥ ancho: celdas ajenas al área de impresión que Excel/Mac emite igualmente) no se imprimen y sólo se informan;
 (b) páginas por hoja (leídas del pie «<hoja> · pág. n/N») frente al presupuesto del doc 13 §9;
 (c) páginas vacías (sin texto salvo el pie).
Sale con 1 si hay cortes o páginas vacías; con --strict también si alguna hoja supera su presupuesto."""
import sys, re
from collections import OrderedDict
import pdfplumber

BUDGET_V30 = OrderedDict([("00_Portada", 3), ("00b_Guía", 5), ("01_Supuestos", 5), ("02_Legal", 6), ("03_Tramites", 3), ("04_Energia", 5), ("05_CAPEX", 3), ("06_OPEX", 3),
                          ("07_Fiscal", 4), ("08_Flujo", 4), ("09_Exergy", 5), ("10_Sensibilidad", 9), ("11_Riesgos", 2), ("12_Fuentes", 4), ("13_Controles", 4), ("Motor_Sens", 2)])   # v3.1: 00b 5 · 02 6 · 03 3 (tabla · Gantt · memo) · 11 2 · 12 4
BUDGET_RES = OrderedDict([("Resumen", 2), ("Supuestos", 2), ("Costos", 2), ("Resultados", 2), ("Sensibilidad", 2), ("Legal y riesgos", 2)])

path = sys.argv[1]
strict = "--strict" in sys.argv
budget = None
if "--budget" in sys.argv:
    budget = OrderedDict()
    for kv in sys.argv[sys.argv.index("--budget") + 1].split(","):
        k, v = kv.split("="); budget[k.strip()] = int(v)
total_budget = int(sys.argv[sys.argv.index("--total") + 1]) if "--total" in sys.argv else None

pdf = pdfplumber.open(path)
W, H = pdf.pages[0].width, pdf.pages[0].height
FOOT_Y = H - 0.6 * 72 + 4   # el pie empieza bajo el margen inferior (0,6 in)
per_sheet = OrderedDict(); cuts = []; blanks = []; overlaps = []; outside = []
for i, p in enumerate(pdf.pages, start=1):
    words = p.extract_words(keep_blank_chars=False)
    foot = [w for w in words if w["top"] >= FOOT_Y]
    body = [w for w in words if w["top"] < FOOT_Y]
    ftxt = " ".join(w["text"] for w in foot)
    m = re.search(r"(\S.*?)\s·\spág\.\s(\d+)/(\d+)", ftxt)
    sheet = None
    if m:
        # el nombre de hoja es el último tramo antes de « · pág.»; la parte anterior es el pie fijo (Exergy … · v3.0)
        sheet = re.sub(r"^(Resumen Directorio )?v\d+\.\d+\s+", "", m.group(1).split(" · ")[-1].strip())   # el pie une la versión y la hoja con un espacio
    per_sheet.setdefault(sheet or f"?p{i}", []).append(i)
    if not body:
        blanks.append(i)
    for w in body:
        if w["x0"] >= W:
            # texto que Excel emite fuera de la caja de página (celdas ajenas al área de impresión, p. ej. auxiliares de un gráfico): no se imprime → informativo
            outside.append((i, sheet, w["text"], round(w["x0"], 1)))
        elif w["x1"] > W + 0.5:
            cuts.append((i, sheet, w["text"], round(w["x1"], 1)))
        elif w["bottom"] > FOOT_Y + 2:
            overlaps.append((i, sheet, w["text"], round(w["bottom"], 1)))
if budget is None:
    budget = BUDGET_RES if "Resumen" in per_sheet else BUDGET_V30
print(f"check_render · {path.split('/')[-1]} · {len(pdf.pages)} páginas · {W:.0f}×{H:.0f} pt")
over = []
print(f"  {'hoja':18s} {'págs.':>5s} {'presup.':>7s}")
for sh, pages in per_sheet.items():
    b = budget.get(sh)
    flag = ""
    if b is not None and len(pages) > b:
        flag = "  ← supera el presupuesto"; over.append(sh)
    print(f"  {sh:18s} {len(pages):5d} {('%d' % b) if b is not None else '—':>7s}{flag}   (págs. {pages[0]}–{pages[-1]})")
tot = len(pdf.pages)
tb = total_budget or sum(v for k, v in budget.items() if k in per_sheet)
print(f"  TOTAL {tot} páginas · presupuesto {tb}{'  ← supera' if tot > tb else ''}")
print(f"  cortes (x1 > ancho de página): {len(cuts)}" + ("" if not cuts else " → " + "; ".join(f"p.{i} {sh} «{t}» x1={x}" for i, sh, t, x in cuts[:12])))
print(f"  palabras fuera de la caja de página (no impresas; informativo): {len(outside)}" + ("" if not outside else " → págs. " + ", ".join(sorted({str(i) for i, *_ in outside}))))
print(f"  palabras sobre el pie: {len(overlaps)}" + ("" if not overlaps else " → " + "; ".join(f"p.{i} {sh} «{t}»" for i, sh, t, x in overlaps[:8])))
print(f"  páginas vacías: {len(blanks)}" + ("" if not blanks else " → " + ", ".join(map(str, blanks))))
bad = bool(cuts or blanks) or (strict and (over or tot > tb))
print("  ✖ revisar" if bad else "  ✔ render sin cortes ni páginas vacías" + ("" if not over else f" (hojas sobre presupuesto: {over})"))
sys.exit(1 if bad else 0)
