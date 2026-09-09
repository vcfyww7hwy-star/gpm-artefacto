# -*- coding: utf-8 -*-
"""extract_book.py DATA_DIR OUT.json — F1 del artefacto: «libro» estático del modelo para las vistas.

Fuente única de los textos = las constantes del generador (build_core, build_content, build_supuestos30, build_guia,
build_sens30): así el artefacto y el Excel dicen exactamente lo mismo. Las cadenas que en Excel son fórmulas
(«="Fee "&TEXT(Fee_Gerencia_Pct,"0%")…») o plantillas con llaves («{TEXT(X_TIR,"0.0%")}») se entregan como AST
(xlformula.py) para que el motor JS las evalúe en vivo con los valores del caso.

DATA_DIR debe contener names.json y sheets.json (salida de extract_model.py del mismo libro _calc): de ahí salen
los valores «congelados» del libro (controles, estados, conteos) y los textos de las hojas que no viven en constantes.
"""
import sys, os, json, re, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlformula import live, names_in
import build_core as bc, build_content as bt, build_supuestos30 as bs, build_guia as bg, build_sens30 as bsn

data_dir, out_path = sys.argv[1], sys.argv[2]
NAMES = json.load(open(os.path.join(data_dir, "names.json")))
SHEETS = json.load(open(os.path.join(data_dir, "sheets.json")))
META = json.load(open(os.path.join(data_dir, "meta.json")))


def js(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()[:10]
    return v


def L(v):
    """valor de constante → JSON vivo (AST si fórmula/plantilla; fechas ISO)."""
    v = js(v)
    return live(v) if isinstance(v, str) else v


def cell(sheet, ref, what="v"):
    c = SHEETS[sheet]["cells"].get(ref)
    return None if c is None else c.get(what)


def rows_of(sheet, cols, r0, r1):
    """Filas no vacías de una hoja: v = valores calculados, f = fórmulas (texto), live = AST de las fórmulas de texto
    (sólo las que el evaluador JS entiende; las demás se omiten y la vista usa v)."""
    out = []
    for r in range(r0, r1 + 1):
        row = {c: cell(sheet, f"{c}{r}") for c in cols}
        rowf = {c: cell(sheet, f"{c}{r}", "f") for c in cols}
        if any(v is not None for v in row.values()):
            lv = {}
            for k, f in rowf.items():
                if f:
                    try:
                        ast = live(f)
                        used = names_in(ast)
                        # sólo fórmulas construidas con nombres definidos (y las dos referencias que el resolutor JS conoce):
                        # las referencias locales de celda (F18, D7…) no son evaluables fuera de la hoja
                        if all((n in NAMES) or n in ("04_Energia!F93", "04_Energia!F97") or n.startswith("Motor_Sens!") for n in used):
                            lv[k] = ast
                    except Exception:
                        pass
            out.append({"row": r, "v": row, "f": {k: v for k, v in rowf.items() if v}, "live": lv})
    return out


book = {"meta": {"version": bc.VERSION, "fecha_analisis": js(bc.FECHA_ANALISIS), "calc_sha256": META["calc"]["sha256"],
                 "extracted": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "generator": "build30 (extract_book.py)"}}

# ---------------------------------------------------------------- 01 · Supuestos
inputs = []
sec = None
for (s, nm, lab, val, u, fmt, conf, nt) in bc.INPUTS:
    if nm is None:
        sec = s
        inputs.append({"section": s})
        continue
    is_calc = isinstance(val, str) and val.startswith("=")
    inputs.append({
        "name": nm, "label": lab, "value": L(val) if not is_calc else None, "formula": L(val) if is_calc else None,
        "calc": is_calc, "unit": u, "fmt": fmt, "confirm": bool(conf), "note": L(nt) if nt else None,
        "info": nm in bc.INFO_INPUTS, "yesno": nm in bc.YESNO, "selector": bc.SELECTORS.get(nm, "").strip('"').split(",") if nm in bc.SELECTORS else None,
        "short": L(bs.SHORT.get(nm)) if nm in bs.SHORT else None, "label2": bs.LABEL.get(nm),
        "sens": list(bs.SENS[nm]) if nm in bs.SENS else None, "confirm_why": bt.CONFIRM_WHY.get(nm), "section": sec,
    })
book["inputs"] = {
    "rows": inputs,
    "bloques": [{"title": t, "guide": g, "names": list(ns)} for (t, g, ns) in bs.BLOQUES],
    "escenarios": [{"name": e[0], "esc_name": e[1], "label": e[2], "unit": e[3], "fmt": e[4], "values": {k: js(v) for k, v in e[5].items()}, "confirm": bool(e[6]), "note": L(e[7]),
                    "sens": list(bs.SENS[e[0]]) if e[0] in bs.SENS else None, "short": L(bs.SHORT.get(e[0])) if e[0] in bs.SHORT else None, "label2": bs.LABEL.get(e[0]), "confirm_why": bt.CONFIRM_WHY.get(e[0])} for e in bc.ESCENARIOS],
    "panel": [{"label": p[0], "value": L(p[1]), "sub": L(p[2]), "name": p[3], "extra": L(p[4]) if len(p) > 4 else None} for p in bs.PANEL],
    "case_keys": list(bc.CASE_KEYS),
    "confirm_list": bt.CONFIRM_LIST(),
    "n_por_confirmar_esperado": NAMES["N_Por_Confirmar_Esperado"]["value"],
    "n_por_confirmar_marcadas": sum(1 for r in bc.INPUTS if r[1] and r[6]) + sum(1 for e in bc.ESCENARIOS if e[6]),
}

# ---------------------------------------------------------------- 05 · CAPEX (rubros)
book["capex"] = {
    "rubros": [{"n": i + 1, "name": r[0], "desc": r[1], "base_5mwp": r[2], "pct_comp": r[3], "pct_ext": r[4], "arancel": r[5], "iva": r[6],
                "source": L(r[7]), "drv_wp": r[8], "drv_wac": r[9], "drv_fijo": r[10]} for i, r in enumerate(bc.RUBROS)],
    "notas": [cell("05_CAPEX", f"B{r}") for r in range(73, 90) if cell("05_CAPEX", f"B{r}")],
    "intro": cell("05_CAPEX", "B2"),
    "headers": {c: cell("05_CAPEX", f"{c}6") for c in "BCDEFGHIJKLMNOPQR"},
    "labels": {r: cell("05_CAPEX", f"C{r}") for r in (16, 17, 18, 19, 20, 21, 22, 23, 24, 27, 28, 29, 30)},
    "reemplazo": rows_of("05_CAPEX", list("CDEHIJ"), 39, 41),
}

# ---------------------------------------------------------------- 06 · OPEX
book["opex"] = {"intro": cell("06_OPEX", "B2"), "lines": rows_of("06_OPEX", list("BCDEFH"), 7, 12), "serie_labels": [cell("06_OPEX", f"B{r}") for r in range(18, 25)],
                "memo_exergy": [cell("06_OPEX", f"B{r}") for r in range(26, 30) if cell("06_OPEX", f"B{r}")]}

# ---------------------------------------------------------------- 02 · Legal
book["legal"] = {
    "intro": cell("02_Legal", "B2"),
    "rows": [{"tema": L(r[0]), "norma": L(r[1]), "texto": L(r[2]), "aplicacion": L(r[3]), "estado": L(r[4]), "confianza": L(r[5])} for r in bt.LEGAL_ROWS],
    "candados": [{"label": L(c[0]), "criterio": L(c[1]), "estado": L(c[2]), "kind": c[3]} for c in bt.CANDADOS],
    "contratos": [{"contrato": L(c[0]), "partes": L(c[1]), "alcance": L(c[2]), "nota": L(c[3])} for c in bt.CONTRATOS],
    "dudas": [{"id": L(d[0]), "duda": L(d[1]), "impacto": L(d[2]), "accion": L(d[3]), "prioridad": L(d[4])} for d in bt.DUDAS],
    "headers": {k: [cell("02_Legal", f"{c}{r}") for c in "BCDEFG"] for k, r in (("rows", 5),)},
}
# cabeceras reales de las tablas de 02 (para no inventar títulos de columna)
def header_row(sheet, text_in_B):
    for ref, c in SHEETS[sheet]["cells"].items():
        if ref.startswith("B") and c.get("v") == text_in_B:
            r = int(ref[1:])
            return [cell(sheet, f"{col}{r}") for col in "BCDEFGHI"]
    return None
book["legal"]["table_headers"] = {"marco": header_row("02_Legal", "Tema"), "candados": header_row("02_Legal", "Candado"), "contratos": header_row("02_Legal", "Contrato"), "dudas": header_row("02_Legal", "#")}

# ---------------------------------------------------------------- 03 · Trámites
book["tramites"] = {
    "intro": cell("03_Tramites", "B2"),
    "mes1": cell("03_Tramites", "D5"),
    "headers": [cell("03_Tramites", f"{c}7") for c in "BCDEFGHIJKLM"],
    "rows": [{"id": t[0], "tramite": L(t[1]), "autoridad": L(t[2]), "base_legal": L(t[3]), "inicio": t[4], "dur": t[5], "fin": t[4] + t[5] - 1, "costo": t[6], "predecesor": t[7], "critica": t[8], "riesgo": t[9], "nota": L(t[10])} for t in bt.TRAMITES],
    "totales": {r: {"label": cell("03_Tramites", f"C{r}"), "formula": cell("03_Tramites", f"I{r}", "f"), "value": cell("03_Tramites", f"I{r}")} for r in (25, 26, 27)},
    "gantt_leyenda": [cell("03_Tramites", "C29"), cell("03_Tramites", "D29")],
    "memo": [cell("03_Tramites", f"B{r}") or cell("03_Tramites", f"C{r}") for r in range(32, 40) if (cell("03_Tramites", f"B{r}") or cell("03_Tramites", f"C{r}"))],
    "controles": {"cron": {"formula": cell("03_Tramites", "M5", "f"), "value": cell("03_Tramites", "M5")}},
}

# ---------------------------------------------------------------- 11 · Riesgos
book["riesgos"] = {
    "intro": cell("11_Riesgos", "B2"),
    "rows": [{"categoria": L(r[0]), "riesgo": L(r[1]), "prob": r[2], "impacto": r[3], "mitigacion": L(r[4]), "dueno": L(r[5]), "disparador": L(r[6])} for r in bt.RIESGOS],
    "headers": header_row("11_Riesgos", "#") or header_row("11_Riesgos", "Categoría"),
    "umbrales": {"alto": NAMES["Umbral_Riesgo_Alto"]["value"], "medio": NAMES["Umbral_Riesgo_Medio"]["value"]},
}

# ---------------------------------------------------------------- 12 · Fuentes
book["fuentes"] = {"intro": cell("12_Fuentes", "B2"), "rows": [{"texto": f[0], "url": f[1]} for f in bt.FUENTES],
                   "secciones": [cell("12_Fuentes", f"B{r}") for r in range(1, 200) if isinstance(cell("12_Fuentes", f"B{r}"), str) and re.match(r"^[A-F] · ", cell("12_Fuentes", f"B{r}"))]}
# texto completo de 12 (secciones B..F) para que la vista no invente nada
book["fuentes"]["cells"] = rows_of("12_Fuentes", list("BCDEF"), 3, 200)

# ---------------------------------------------------------------- 13 · Controles (valores del libro)
ctrl = []
grp = None
for r in range(6, 94):
    b, c, d, f = cell("13_Controles", f"B{r}"), cell("13_Controles", f"C{r}"), cell("13_Controles", f"D{r}"), cell("13_Controles", f"F{r}")
    if b and not c:
        grp = b; continue
    if b and c:
        ctrl.append({"group": grp, "id": c, "desc": b, "status": d, "formula": cell("13_Controles", f"D{r}", "f"), "prueba": f})
book["controles"] = {"intro": cell("13_Controles", "B2"), "rows": ctrl,
                     "resumen": {cell("13_Controles", f"B{r}"): cell("13_Controles", f"D{r}") for r in (96, 97, 98, 99)}}

# ---------------------------------------------------------------- 00b · Guía
book["guia"] = {
    "intro": cell("00b_Guía", "B2"),
    "pasos": [{"title": p[0], "text": L(p[1]), "sheet": p[2]} for p in bg.PASOS],
    "convenciones": [{"a": c[0], "b": c[1], "color": c[2], "bold": bool(c[3])} for c in bg.CONVENCIONES],
    "grupos": [{"title": t, "items": [{"term": i[0], "def": L(i[1]), "live": L(i[2]) if len(i) > 2 and i[2] else None, "anchor": i[3] if len(i) > 3 else None} for i in items]} for (t, items) in bg.GRUPOS],
    "faq": [{"q": L(q), "a": L(a)} for (q, a) in bg.FAQ],
    "index": [{"sheet": s, "title": t} for (s, t) in bt.INDEX],
}

# ---------------------------------------------------------------- 10 · Sensibilidad (definiciones)
book["sens"] = {"tornado": [{"label": L(t[0]), "lo": t[1], "hi": t[2], "note": L(t[3])} for t in bt.TORNADO],
                "tornado_short": [L(s) for s in bt.TORNADO_SHORT], "precio_steps": list(bt.PRECIO_STEPS),
                "intro": cell("10_Sensibilidad", "B2")}

# ---------------------------------------------------------------- 04/07/08/09 · introducciones y etiquetas de fila (para las vistas)
book["sheets"] = {}
for sh in SHEETS:
    cells = SHEETS[sh]["cells"]
    labels, labels_b, labels_c, labels_f = {}, {}, {}, {}
    for ref, c in cells.items():
        if re.match(r"^[BCF]\d+$", ref) and isinstance(c.get("v"), str) and not c.get("f"):
            if ref[0] == "F":                      # columna F («Lectura» en 08; notas estáticas en otras hojas)
                labels_f[int(ref[1:])] = c["v"]; continue
            labels[int(ref[1:])] = c["v"]
            (labels_b if ref[0] == "B" else labels_c)[int(ref[1:])] = c["v"]
    book["sheets"][sh] = {"intro": cell(sh, "B2"), "title": cell(sh, "B1"), "labels": labels, "labels_b": labels_b, "labels_c": labels_c, "labels_f": labels_f}

# ---------------------------------------------------------------- constantes de hoja fuera de 01 (para reconstrucciones en las vistas)
book["energia"] = {"intro": cell("04_Energia", "B2"),
                   "demanda_facturable_kW": {"label": cell("04_Energia", "B74"), "value": cell("04_Energia", "D74"), "formula": cell("04_Energia", "D74", "f")},
                   "fgd": {"label": cell("04_Energia", "B75"), "value": cell("04_Energia", "D75"), "formula": cell("04_Energia", "D75", "f")},
                   "factura_referencia": {"label": cell("04_Energia", "B76"), "formula": cell("04_Energia", "D76", "f"), "value": cell("04_Energia", "D76")}}
book["exergy"] = {"intro": cell("09_Exergy", "B2"), "palancas": rows_of("09_Exergy", list("BCDEFGH"), 55, 68)}

# ---------------------------------------------------------------- valores del libro (baseline) para resolutor y respaldo
frozen_keys = ["N_Controles", "N_Controles_OK", "N_Controles_Fail", "N_Por_Confirmar", "N_Por_Confirmar_Esperado", "N_Custom_vs_Base", "N_Fuera_Entregado", "N_Neutro",
               "Estado_Custom", "Estado_Neutro", "Estado_Entregado", "Estado_Controles", "Deuda_Max_Plazo1", "Deuda_Max_Plazo2", "Deuda_Max_Plazo3",
               "Mes_COD_Cron", "Costo_Desarrollo_Cron", "Fin_RC09", "Fin_RC10", "Check_Cron", "Check_Drivers", "Check_Tramites", "Mes1_Cronograma"]
book["frozen"] = {k: NAMES[k]["value"] for k in frozen_keys if k in NAMES}
book["frozen_formulas"] = {k: NAMES[k]["formula"] for k in frozen_keys if k in NAMES}
book["calc_names"] = {k: v["value"] for k, v in NAMES.items() if "value" in v}

# ---------------------------------------------------------------- nombres usados por los textos vivos (para el test del resolutor)
used = set()
def walk(o):
    if isinstance(o, list) and o and o[0] in ("f", "tpl"):
        names_in(o, used)
    elif isinstance(o, list):
        for x in o: walk(x)
    elif isinstance(o, dict):
        for x in o.values(): walk(x)
walk(book)
book["live_names"] = sorted(used)

json.dump(book, open(out_path, "w"), ensure_ascii=False, indent=0)
print(f"book.json → {out_path}: inputs {sum(1 for r in inputs if 'name' in r)} · legal {len(bt.LEGAL_ROWS)} filas · trámites {len(bt.TRAMITES)} · riesgos {len(bt.RIESGOS)} · fuentes {len(bt.FUENTES)} · controles {len(ctrl)} · nombres vivos {len(used)}")
