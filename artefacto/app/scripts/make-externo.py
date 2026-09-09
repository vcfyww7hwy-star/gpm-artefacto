#!/usr/bin/env python3
"""make-externo.py — datos de la EDICIÓN EXTERNA (SALELGI / banco): exclusión física de los internos de Exergy.

Genera, a partir de los datos internos:
  src/model/book_v31.externo.json     libro sin la hoja 09, sin el bloque H de 01 (costos internos de Exergy), sin el
                                      término del glosario «Negocio Exergy», sin el grupo E de controles, sin el memo de
                                      costos propios de 06, sin los nombres/valores internos y sin los textos que los citan
                                      (se ELIMINAN, nunca se reescriben; cada eliminación se lista en la salida)
  src/model/inputs_v31.externo.json   entradas con los tres costos internos de Exergy a 0 (sólo alimentan Ux/Ix/Fx/Gx)
  src/model/oracle_v31.externo.json   oráculo sin las salidas «VAN Exergy», «TIR grupo» y «Nominal Exergy Σ»
La edición externa se compila con VITE_EDITION=externo; el empaquetador elimina los módulos internos (check-exclusion.mjs).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "src", "model")

INTERNAL_INPUTS = ["Costo_Gerencia_Pct", "Costo_OM_Exergy_kWp", "Tasa_Efectiva_Exergy"]
INTERNAL_NAMES = INTERNAL_INPUTS + ["VAN_Exergy", "TIR_Exergy", "Nominal_Exergy", "VAN_Gerencia", "VAN_OM", "VAN_Terreno", "Carga_Exergy",
                                    "Ann_Esc", "Yield_Terreno", "X_VANX", "C_VANX", "B_VANX", "F_VANX", "X_TIRG", "C_TIRG", "B_TIRG", "F_TIRG",
                                    "TIR_Grupo", "VAN_Grupo", "P50_VANX", "P90_VANX"]
# términos cuya presencia en un TEXTO obliga a eliminar ese texto (deleción, no reescritura)
INTERNAL_TERMS = INTERNAL_INPUTS + ["VAN_Exergy", "TIR_Exergy", "Nominal_Exergy", "VAN_Gerencia", "VAN_OM", "VAN_Terreno", "Carga_Exergy",
                                    "margen de Exergy", "margen O&M", "margen neto", "Negocio Exergy", "negocio Exergy", "costo interno de Exergy",
                                    "Costo propio", "costo propio", "utilidad de Exergy", "09_Exergy", "VAN negocio Exergy", "negocio Exergy (USD)"]
removed = []


def has_internal(text):
    return isinstance(text, str) and any(t in text for t in INTERNAL_TERMS)


def live_text(v):
    """texto plano de un valor Live (para inspección): cadena, o fórmula original, o literales de la plantilla."""
    if isinstance(v, str):
        return v
    if isinstance(v, list) and v and v[0] == "f":
        return v[2] if len(v) > 2 and isinstance(v[2], str) else json.dumps(v, ensure_ascii=False)
    if isinstance(v, list) and v and v[0] == "tpl":
        return " ".join(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False) for p in v[1])
    return json.dumps(v, ensure_ascii=False) if v is not None else ""


def drop(path, why):
    removed.append((path, why))


book = json.load(open(os.path.join(MODEL, "book_v31.json")))
inputs = json.load(open(os.path.join(MODEL, "inputs_v31.json")))
oracle = json.load(open(os.path.join(MODEL, "oracle_v31.json")))

# ---- 01 · Supuestos: bloque H y sus filas; textos que citan internos
rows = []
for r in book["inputs"]["rows"]:
    if r.get("section") and "Negocio Exergy" in r["section"] and not r.get("name"):
        drop(f"inputs.rows[{r['section']}]", "cabecera del bloque H"); continue
    if r.get("name") in INTERNAL_INPUTS:
        drop(f"inputs.rows[{r['name']}]", "entrada interna de Exergy"); continue
    r = dict(r)
    if r.get("section") and "Negocio Exergy" in r["section"]:
        r["section"] = None
    for fld in ("note", "short"):
        if fld in r and has_internal(live_text(r[fld])):
            drop(f"inputs.rows[{r.get('name')}].{fld}", "texto que cita un interno"); r[fld] = None
    if r.get("sens") and any(has_internal(str(x)) for x in r["sens"]):
        drop(f"inputs.rows[{r.get('name')}].sens", "«sensibilizado en» apunta a la hoja 09"); r["sens"] = None
    rows.append(r)
for e in book["inputs"]["escenarios"]:
    for fld in ("note", "short"):
        if fld in e and has_internal(live_text(e[fld])):
            drop(f"inputs.escenarios[{e['name']}].{fld}", "texto que cita un interno"); e[fld] = None
    if e.get("sens") and any(has_internal(str(x)) for x in e["sens"]):
        drop(f"inputs.escenarios[{e['name']}].sens", "apunta a la hoja 09"); e["sens"] = None
book["inputs"]["rows"] = rows
book["inputs"]["bloques"] = [bl for bl in book["inputs"]["bloques"] if not any(n in INTERNAL_INPUTS for n in bl["names"])]
drop("inputs.bloques[H]", "bloque H · Negocio Exergy")
cl = []
for t in book["inputs"]["confirm_list"]:
    if has_internal(t): drop("inputs.confirm_list", t[:60])
    else: cl.append(t)
book["inputs"]["confirm_list"] = cl

# ---- 06 · memo de costos propios
if book["opex"].get("memo_exergy"):
    drop("opex.memo_exergy", "memo de costos propios de Exergy"); book["opex"]["memo_exergy"] = []

# ---- 09 y palancas
book.pop("exergy", None); drop("exergy", "hoja 09 (palancas)")
book["sheets"].pop("09_Exergy", None); drop("sheets.09_Exergy", "hoja 09 (intro y etiquetas)")
for sh, sd in book["sheets"].items():
    for key in ("labels", "labels_b", "labels_c", "labels_f"):
        if key in sd:
            for row, txt in list(sd[key].items()):
                if has_internal(txt):
                    sd[key].pop(row); drop(f"sheets.{sh}.{key}[{row}]", txt[:60])

# ---- Guía: término «Negocio Exergy · carga», índice 09
for g in book["guia"]["grupos"]:
    keep = []
    for it in g["items"]:
        if has_internal(it["term"]) or has_internal(live_text(it.get("def"))) or has_internal(live_text(it.get("live"))) or has_internal(it.get("anchor") or ""):
            drop(f"guia.grupos[{g['title']}].{it['term']}", "término del glosario con internos")
        else:
            keep.append(it)
    g["items"] = keep
book["guia"]["index"] = [x for x in book["guia"]["index"] if x["sheet"] != "09_Exergy"]
faq = []
for q in book["guia"]["faq"]:
    if has_internal(live_text(q["q"])) or has_internal(live_text(q["a"])): drop("guia.faq", live_text(q["q"])[:60])
    else: faq.append(q)
book["guia"]["faq"] = faq
pasos = []
for p in book["guia"]["pasos"]:
    if has_internal(live_text(p["text"])): drop("guia.pasos", p["title"])
    else: pasos.append(p)
book["guia"]["pasos"] = pasos

# ---- Fuentes: filas que citan internos
cells = []
for c in book["fuentes"]["cells"]:
    txt = " ".join(str(v) for v in c["v"].values() if isinstance(v, str))
    if has_internal(txt): drop(f"fuentes.cells[row {c['row']}]", txt[:70])
    else: cells.append(c)
book["fuentes"]["cells"] = cells

# ---- Controles: grupo E entero; fórmulas que citan internos se vacían (el control se conserva)
ctrl = []
for r in book["controles"]["rows"]:
    if r["group"] and r["group"].startswith("E ·"):
        drop(f"controles.rows[{r['id']}]", "grupo E · Exergy y grupo"); continue
    r = dict(r)
    if has_internal(r.get("formula") or "") or has_internal(r.get("desc") or ""):
        if has_internal(r.get("desc") or ""):
            drop(f"controles.rows[{r['id']}]", "descripción con internos"); continue
        drop(f"controles.rows[{r['id']}].formula", "fórmula que cita un interno"); r["formula"] = ""
    ctrl.append(r)
book["controles"]["rows"] = ctrl
n_ok = sum(1 for r in ctrl if str(r.get("status", "")).startswith("●"))
n_fail = sum(1 for r in ctrl if str(r.get("status", "")).startswith("■"))
book["frozen"]["N_Controles"] = len(ctrl); book["frozen"]["N_Controles_OK"] = n_ok; book["frozen"]["N_Controles_Fail"] = n_fail
book["frozen"]["Estado_Controles"] = f"● Controles {n_ok}/{len(ctrl)} en orden" if n_fail == 0 else f"■ {n_fail} control(es) fuera de orden"
book["controles"]["resumen"] = {"Controles evaluados": len(ctrl), "Controles en ● (ok o no aplicable)": n_ok, "Controles en ■ (inconsistencia o fuera de rango)": n_fail, "Estado": book["frozen"]["Estado_Controles"]}

# ---- nombres y valores internos
for k in list(book["calc_names"]):
    if k in INTERNAL_NAMES: book["calc_names"].pop(k); drop(f"calc_names.{k}", "valor interno")
for k in list(book["frozen"]):
    if k in INTERNAL_NAMES: book["frozen"].pop(k)
book["live_names"] = [n for n in book["live_names"] if n not in INTERNAL_NAMES]
book["meta"]["edicion"] = "externo"

# ---- textos vivos que citan internos en cualquier otra parte (comprobación final: no debe quedar ninguno)
def scan(o, path):
    if isinstance(o, str):
        if has_internal(o): leftovers.append((path, o[:80]))
    elif isinstance(o, list):
        for i, x in enumerate(o): scan(x, f"{path}[{i}]")
    elif isinstance(o, dict):
        for k, v in o.items(): scan(v, f"{path}.{k}")
leftovers = []
for k in book:
    if k in ("live_names",): continue
    scan(book[k], k)

# ---- entradas y oráculo
inputs_ext = dict(inputs)
for k in INTERNAL_INPUTS:
    if k in inputs_ext: inputs_ext[k] = 0
drop_labels = {"VAN Exergy", "TIR grupo", "Nominal Exergy Σ"}
idx = [i for i, l in enumerate(oracle["outputLabels"]) if l not in drop_labels]
oracle_ext = dict(oracle)
oracle_ext["outputLabels"] = [oracle["outputLabels"][i] for i in idx]
oracle_ext["cases"] = [{"name": c["name"], "outputs": [c["outputs"][i] for i in idx]} for c in oracle["cases"]]
oracle_ext["edicion"] = "externo"

json.dump(book, open(os.path.join(MODEL, "book_v31.externo.json"), "w"), ensure_ascii=False, indent=0)
json.dump(inputs_ext, open(os.path.join(MODEL, "inputs_v31.externo.json"), "w"), ensure_ascii=False, indent=1)
json.dump(oracle_ext, open(os.path.join(MODEL, "oracle_v31.externo.json"), "w"), ensure_ascii=False, indent=0)

print(f"edición externa: {len(removed)} eliminaciones · controles {len(ctrl)} ({n_ok} ●) · salidas del oráculo {len(idx)}/{len(oracle['outputLabels'])}")
for p, why in removed:
    print(f"  − {p}: {why}")
if leftovers:
    print("\n⚠ textos con términos internos que siguen en el libro externo (revisar):")
    for p, t in leftovers: print(f"  ! {p}: {t}")
    sys.exit(1)
print("✔ sin términos internos residuales")
