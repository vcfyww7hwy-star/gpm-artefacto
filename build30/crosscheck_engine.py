# -*- coding: utf-8 -*-
"""crosscheck_engine.py RAW.xlsx OUT_DIR N [SEED] [--replay RESUMEN.json:K] — cruce ALEATORIO motor JS ≡ LibreOffice fuera del punto de entrega.

Para cada muestra: elige valores al azar (dentro de los rangos de Mandos/Supuestos) para ~25 entradas de 01_Supuestos
(y una duración del cronograma de 03), los escribe en una copia del libro RAW, recalcula con LibreOffice, extrae el Motor
(extract_model.py) y ejecuta engine/test/verify.ts con DATA_DIR = la carpeta de la muestra: el motor TS recibe las
entradas leídas del propio libro modificado y sus 111 casos deben coincidir celda a celda (tolerancia 1e-6 abs / 1e-9 rel).
Escribe OUT_DIR/resumen.json y un renglón por muestra.
"""
import sys, os, json, random, subprocess, shutil, datetime as dt, time
from openpyxl import load_workbook

# --replay RESUMEN.json:K — repite la muestra K de un cruce anterior (mismas entradas) sobre el RAW indicado (p. ej. r3-pre)
REPLAY = None
if "--replay" in sys.argv:
    i = sys.argv.index("--replay"); rp, rk = sys.argv[i + 1].rsplit(":", 1); del sys.argv[i:i + 2]
    REPLAY = [x for x in json.load(open(rp))["results"] if x["sample"] == int(rk)][0]["inputs"]
raw, out_dir, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20260908
random.seed(seed)
os.makedirs(out_dir, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.environ.get("ENGINE_DIR", os.path.normpath(os.path.join(HERE, "..", "..", "artefacto", "engine")))  # R-F0-1: antes ruta absoluta del contenedor anterior


def sample():
    """valores aleatorios dentro de los rangos que el artefacto permite editar."""
    s = {
        "Potencia_DC": random.choice([5000, 6000, 7000, 8000]),
        "Ratio_DCAC": round(random.uniform(1.10, 1.50), 2),
        "Comprador_Terreno": random.choice(["SALELGI", "Exergy"]),
        "Tasa_Descuento": round(random.uniform(0.06, 0.14), 3),
        "Tasa_Descuento_Equity": round(random.uniform(0.08, 0.18), 3),
        "Pct_Apalancamiento": round(random.choice([0, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]), 2),
        "Tasa_Deuda": round(random.uniform(0.05, 0.12), 4),
        "Plazo_Deuda": random.choice([6, 8, 10, 12, 15]),
        "Gracia_Deuda": random.choice([0, 1, 2]),
        "Aplica_DedAd": random.choice(["Sí", "No"]),
        "Escenario_Energia": random.choice(["P50", "P90"]),
        "Factor_CAPEX": round(random.uniform(0.8, 1.3), 2),
        "Peaje_SGDA": round(random.uniform(0, 0.02), 4),
        "Escalacion_Tarifa": round(random.uniform(0, 0.04), 3),
        "Disponibilidad": round(random.uniform(0.90, 1.0), 3),
        "Escalacion_CAPEX": round(random.uniform(0, 0.08), 3),
        "Fee_OM_kWp": round(random.uniform(12, 24), 1),
        "Seguro_kWp": round(random.uniform(2.5, 5), 1),
        "Escalacion_OPEX": round(random.uniform(0, 0.04), 3),
        "IVA_Recuperable": random.choice(["Sí", "No"]),
        "Incluir_Participacion": random.choice(["Sí", "No"]),
        "Contrato_Inversion": random.choice(["Sí", "No"]),
        "Reemplazo_Pagador": random.choice(["SALELGI", "Exergy", "No"]),
        "Reemplazo_Anio": random.choice([8, 10, 13, 15, 20]),
        "Degradacion_Adicional": round(random.uniform(0, 0.01), 4),
        "Desmantelamiento_Pct": round(random.choice([0, 0.01, 0.02, 0.03]), 3),
        "Utilidad_Gravable_SALELGI": random.choice([None, 0, 200000, 1000000]),
        "Fecha_COD": dt.datetime(random.choice([2028, 2029]), random.choice([1, 4, 7, 10]), 1),
        "Fecha_Peaje": dt.datetime(2029, 2, 28),
        "Sens_CAPEX": round(random.uniform(0.05, 0.3), 3),
        "Sens_Tarifa": round(random.uniform(0.05, 0.3), 3),
        "Sens_Peaje": round(random.uniform(0.0025, 0.03), 4),
        "DSCR_Objetivo": round(random.uniform(1.1, 1.4), 2),
        "03_Tramites!G21": random.choice([5, 7, 9, 12, 16]),   # duración de RC-12 → Mes_COD_Cron → Meses_Construccion
    }
    return s


def dest(wb, nm):
    if "!" in nm:
        sh, ref = nm.split("!", 1)
        return wb[sh.strip("'")], ref.replace("$", "")
    for sh, ref in wb.defined_names[nm].destinations:
        return wb[sh], ref.replace("$", "")


results = []
t_all = time.time()
for k in range(n):
    t0 = time.time()
    vals = sample() if REPLAY is None else {kk: (dt.datetime.fromisoformat(vv) if kk in ("Fecha_COD", "Fecha_Peaje") else vv) for kk, vv in REPLAY.items()}
    d = os.path.join(out_dir, f"s{k:02d}")
    os.makedirs(d, exist_ok=True)
    wb = load_workbook(raw)
    for nm, v in vals.items():
        ws, ref = dest(wb, nm)
        ws[ref].value = v
    raw_k = os.path.join(d, "raw.xlsx"); calc_k = os.path.join(d, "calc.xlsx")
    wb.save(raw_k)
    shutil.copy(raw_k, calc_k)
    r = subprocess.run(["python3", "/mnt/skills/public/xlsx/scripts/recalc.py", calc_k, "600"], capture_output=True, text=True)
    r2 = subprocess.run(["python3", os.path.join(HERE, "extract_model.py"), raw_k, calc_k, d], capture_output=True, text=True)
    env = dict(os.environ, DATA_DIR=d)
    r3 = subprocess.run(["npx", "tsx", "test/verify.ts"], cwd=ENGINE, capture_output=True, text=True, env=env)
    rep_path = os.path.join(d, "verify_report.json")
    rep = json.load(open(rep_path)) if os.path.exists(rep_path) else None
    status = rep["status"] if rep else f"ERROR ({r3.returncode})"
    row = {"sample": k, "status": status, "compared": rep["totalCompared"] if rep else None, "failed": rep["totalFailed"] if rep else None,
           "inputs": {kk: (vv.isoformat()[:10] if isinstance(vv, dt.datetime) else vv) for kk, vv in vals.items()}, "seconds": round(time.time() - t0)}
    if not rep:
        row["stderr"] = (r3.stderr or r3.stdout)[-1500:]
    results.append(row)
    print(f"s{k:02d} {status} {row['compared']} celdas · {row['failed']} fuera · {row['seconds']} s · " + ", ".join(f"{a}={b}" for a, b in list(row['inputs'].items())[:6]), flush=True)
    json.dump({"seed": seed, "raw": raw, "results": results, "elapsed_s": round(time.time() - t_all)}, open(os.path.join(out_dir, "resumen.json"), "w"), ensure_ascii=False, indent=1)
    # limpiar libros pesados de la muestra (se conservan los JSON y el informe)
    for f in ("raw.xlsx", "calc.xlsx"):
        try: os.remove(os.path.join(d, f))
        except OSError: pass
ok = sum(1 for r in results if r["status"] == "PASS")
print(f"\n{ok}/{n} muestras PASS · {round(time.time() - t_all)} s")
