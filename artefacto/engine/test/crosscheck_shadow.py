# -*- coding: utf-8 -*-
"""Cross-check generator: runs shadow30.run_case (the authoritative Python transliteration) on
randomized parameter sets that exercise branches the 111 Motor cases do not reach, and writes
test/crosscheck_cases.json for test/crosscheck.ts to compare against the TypeScript engine.

    python3 test/crosscheck_shadow.py [N=400] [seed=31]
"""
import json, os, random, sys, math
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)
DATA = os.path.join(os.path.dirname(ENGINE), "data")

# --- load shadow30 without build_core (only TS and the 05_CAPEX row constants are needed)
src = open(os.path.join(ENGINE, "shadow30.py"), encoding="utf-8").read()
src = src.replace("from build_core import TS, C, CAPEX as KL, FLUJO, EXERGY",
                  "TS = list(range(-1, 26)); KL = dict(r0=7, fee=18); C = None; FLUJO = None; EXERGY = None")
ns = {"__name__": "shadow30_embedded"}
exec(compile(src, "shadow30.py", "exec"), ns)
run_case = ns["run_case"]

names = json.load(open(os.path.join(DATA, "names.json"), encoding="utf-8"))
sheets = json.load(open(os.path.join(DATA, "sheets.json"), encoding="utf-8"))


def nv(n):
    e = names[n]
    return e.get("value", e.get("values"))


def flat(v):
    if isinstance(v, list):
        out = []
        for r in v:
            out.extend(r if isinstance(r, list) else [r])
        return out
    return [v]


def cellv(sheet, ref):
    c = sheets[sheet]["cells"].get(ref)
    return None if c is None else c.get("v")


def d(s):
    y, m, dd = s[:10].split("-")
    return date(int(y), int(m), int(dd))


# --- P as shadow30.load_inputs would build it (values straight from the workbook extract)
P = {}
for nm in ["Horizonte", "Tasa_Descuento", "Fase_m1", "Tasa_IVA", "FODINFA_Pct", "ISD_Pct", "Contingencia_Pct", "Contingencia_Frac_IVA", "Fee_Gerencia_Pct", "Asignacion_Compartida",
           "Fee_OM_kWp", "Seguro_kWp", "Renta_Terreno_ha", "Tributos_Locales", "Escalacion_OPEX", "Precio_Terreno_ha", "Costos_Transaccion_Terreno_Pct", "Predial_Terreno", "Residual_Terreno_Pct", "Apreciacion_Terreno",
           "Tasa_IR", "Tasa_Participacion", "Vida_Fiscal_Equipos", "Vida_Fiscal_Civil", "Pct_Elegible_DedAd", "Ingresos_SALELGI", "Tope_DedAd_Pct", "IDC_Frac_Tramo0",
           "Costo_Gerencia_Pct", "Costo_OM_Exergy_kWp", "Tasa_Efectiva_Exergy", "Potencia_Ref", "Ratio_Ref", "Densidad_MWp_ha", "Exponente_Escala", "Crecimiento_Consumo",
           "Tarifa_Evitable", "Consumo_Anual", "Pct_CAPEX_Civil", "Tasa_Efectiva", "Anios_Precios", "Reemplazo_Anio", "Reemplazo_USD_Wac"]:
    P[nm] = nv(nm)
P["escudo"] = nv("Escudo_Negativo") == "Sí"
P["Fecha_COD"] = d(nv("Fecha_COD")); P["Fecha_Peaje"] = d(nv("Fecha_Peaje")); P["Fecha_Precios"] = d(nv("Fecha_Precios"))
P["cod"] = P["Fecha_COD"]; P["fpeaje"] = P["Fecha_Peaje"]
P["Y50"] = flat(nv("Y_P50")); P["Y90"] = flat(nv("Y_P90"))
P["cr_ratio"] = flat(nv("CR_Ratio")); P["cr_loss"] = flat(nv("CR_Loss"))
dwp, dwac, dfx = flat(nv("Drv_Wp")), flat(nv("Drv_Wac")), flat(nv("Drv_Fijo"))
P["rubros"] = [dict(cost=cellv("05_CAPEX", f"D{r}") or 0, comp=cellv("05_CAPEX", f"E{r}") or 0, ext=cellv("05_CAPEX", f"G{r}") or 0, ar=cellv("05_CAPEX", f"I{r}") or 0,
                    iva=cellv("05_CAPEX", f"O{r}") or 0, wp=dwp[i], wac=dwac[i], wf=dfx[i]) for i, r in enumerate(range(7, 16))]
P["iva_fee"] = cellv("05_CAPEX", "O18")

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 31
rng = random.Random(seed)

custom = dict(fK=1, fT=1, scen=1, fO=1, pj=0, escT=0.02, part=1, iva=1, cont=0, deb=1, rd=0.075, lev=1, plazo=8, gr=1, P=5000, ratio=1.32, terr=1, finT=0, fPre=1, kfix=0,
              disp=0.97, dK=0, pkw=0, rep=1, ug=-1, ncon=21, req=0.12, dec=0, deg=0.01, dedad=1)


def rand_case(k):
    pc = dict(custom)
    pc["fK"] = round(rng.uniform(0.7, 1.4), 4)
    pc["fT"] = round(rng.uniform(0.7, 1.3), 4)
    pc["scen"] = rng.choice([1, 2])
    pc["fO"] = round(rng.uniform(0.7, 1.4), 4)
    pc["pj"] = rng.choice([0, 0, 0.005, 0.015, round(rng.uniform(0, 0.03), 4)])
    pc["escT"] = rng.choice([0, 0.02, round(rng.uniform(-0.01, 0.04), 4)])
    pc["part"] = rng.choice([0, 1]); pc["iva"] = rng.choice([0, 1]); pc["cont"] = rng.choice([0, 1])
    pc["deb"] = rng.choice([0, 1, 1, 1])
    pc["rd"] = rng.choice([0, 0.05, 0.075, 0.09, 0.11, round(rng.uniform(0.02, 0.14), 4)])
    pc["lev"] = rng.choice([0.4, 0.6, 0.8, 1.0, round(rng.uniform(0.2, 1.0), 3)])
    pc["plazo"] = rng.choice([1, 3, 5, 8, 10, 12, 15, 20, 25])
    pc["gr"] = rng.choice([0, 1, 2, 3, 5, 8, 12])   # may exceed plazo → balloon branch
    pc["P"] = rng.choice([3000, 4180, 5000, 6000, 7000, 8000, round(rng.uniform(2000, 9000), 0)])
    pc["ratio"] = rng.choice([1.0, 1.1, 1.2, 1.32, 1.4, 1.5, 1.6, round(rng.uniform(0.95, 1.7), 3)])   # outside the CR curve → clamping
    pc["terr"] = rng.choice([0, 1]); pc["finT"] = rng.choice([0, 1])
    pc["fPre"] = round(rng.uniform(0.4, 1.6), 3)
    pc["kfix"] = rng.choice([0, 0, 0, 0.65, 0.75, 0.9, round(rng.uniform(0.5, 1.1), 3)])
    pc["disp"] = round(rng.uniform(0.9, 1.0), 4)
    pc["dK"] = rng.choice([0, 0.02, 0.03, 0.05, round(rng.uniform(0, 0.08), 4)])
    pc["pkw"] = rng.choice([0, 0, 0.5, 1.0, round(rng.uniform(0, 2), 3)])
    pc["rep"] = rng.choice([0, 1, 2])
    pc["ug"] = rng.choice([-1, -1, 0, 0, 50000, 200000, 1000000, round(rng.uniform(0, 3e6), 0)])
    pc["ncon"] = rng.choice([12, 18, 21, 24])
    pc["req"] = rng.choice([0.1, 0.12, 0.15, round(rng.uniform(0.06, 0.2), 4)])
    pc["dec"] = rng.choice([0, 0, 0.02, 0.05, round(rng.uniform(0, 0.1), 4)])
    pc["deg"] = rng.choice([0, 0.005, 0.01, round(rng.uniform(0, 0.02), 4)])
    pc["dedad"] = rng.choice([0, 1])
    return pc


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if hasattr(v, "item"):
        v = v.item()
    return v


cases = []
for k in range(N):
    pc = rand_case(k)
    out, blocks = run_case(P, pc)
    cases.append({
        "pc": pc,
        "out": {kk: clean(v) for kk, v in out.items()},
        "blocks": {b: [clean(blocks[b][t]) for t in ns["TS"]] for b in ns["BLOCKS_V30"]},
    })
json.dump({"seed": seed, "n": N, "cases": cases}, open(os.path.join(HERE, "crosscheck_cases.json"), "w"), indent=0)
print(f"wrote {N} random cases (seed {seed}) to test/crosscheck_cases.json")
