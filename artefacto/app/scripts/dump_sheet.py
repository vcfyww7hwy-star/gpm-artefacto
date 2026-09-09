#!/usr/bin/env python3
"""dump_sheet.py HOJA [fila_min fila_max] [--cols B,C,D] [--maxlen 100]
Imprime, fila por fila, las celdas no vacías de una hoja del libro (../data/sheets.json): valor calculado o fórmula.
Uso típico para consultar la estructura exacta de una hoja (etiquetas de fila, fórmulas) antes de escribir una vista.
Ejemplos:
  python3 scripts/dump_sheet.py 07_Fiscal 1 60 --cols B,C,D,E,F
  python3 scripts/dump_sheet.py 09_Exergy --maxlen 140
  python3 scripts/dump_sheet.py list           # lista las hojas
"""
import json, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, "..", "..", "data", "sheets.json")))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = {a.split("=")[0]: (a.split("=")[1] if "=" in a else True) for a in sys.argv[1:] if a.startswith("--")}
if not args or args[0] == "list":
    for k in S:
        print(k, len(S[k]["cells"]), "celdas")
    sys.exit(0)
sheet = args[0]
rmin = int(args[1]) if len(args) > 1 else 1
rmax = int(args[2]) if len(args) > 2 else 10 ** 6
cols = None
if "--cols" in opts:
    cols = set(str(opts["--cols"]).split(","))
elif len(sys.argv) > 1 and "--cols" in " ".join(sys.argv):
    pass
for i, a in enumerate(sys.argv):
    if a == "--cols" and i + 1 < len(sys.argv):
        cols = set(sys.argv[i + 1].split(","))
    if a == "--maxlen" and i + 1 < len(sys.argv):
        opts["--maxlen"] = sys.argv[i + 1]
maxlen = int(opts.get("--maxlen", 100))
cells = S[sheet]["cells"]


def key(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (int(m.group(2)), len(m.group(1)), m.group(1))


rows = {}
for ref, c in cells.items():
    r = key(ref)[0]
    if rmin <= r <= rmax:
        rows.setdefault(r, []).append((key(ref), ref, c))
for r in sorted(rows):
    parts = []
    for k, ref, c in sorted(rows[r]):
        col = re.match(r"[A-Z]+", ref).group(0)
        if cols and col not in cols:
            continue
        f = c.get("f")
        v = c.get("v")
        txt = f if f else json.dumps(v, ensure_ascii=False)
        parts.append(f"{ref}={txt[:maxlen]}")
    if parts:
        print(" | ".join(parts))
