# -*- coding: utf-8 -*-
"""Modelo sombra v3.0 (Python puro, lógica independiente del generador). Evolución de shadow20 + shadow30_proto (ronda 2, doc 13):
   M-a escalación del CAPEX hasta la compra (fEsc) · M-b absorción fiscal limitada + pool de pérdidas sin caducidad (art. 11 LRTI, ≤ 25 %)
   · M-c reemplazo de inversores (pagador SALELGI/Exergy/No) + desmantelamiento + payback robusto · M-d disponibilidad + degradación adicional
   · M-e IDC × Meses_Construccion/12 · M-g VAN del accionista a Tasa_Descuento_Equity · M-h peaje por potencia ($/kW-mes).
Lee el Motor **por etiqueta de fila** (columna A), no por número: los 20 parámetros v2.0 + los 9 nuevos (ausentes → valor neutro), los
escalares y las salidas. Con los parámetros nuevos en neutro reproduce shadow20.run_case (Δ = 0): sirve para el libro v2.0 y para el v3.0.
Uso: python3 shadow30.py LIBRO_calc.xlsx salida.csv [--blocks] [--tol 1e-6] [--quiet]
  --blocks : además de los KPI, compara todas las filas anuales de todos los bloques (por etiqueta) en todos los casos."""
import sys, csv, math
from datetime import date
import numpy as np
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter as gl
from build_core import TS, C, CAPEX as KL, FLUJO, EXERGY

# ---------------------------------------------------------------- etiquetas del Motor (clave interna → texto de la columna A)
LABEL_PARAM = {"fK": "Factor CAPEX (× bottom-up)", "kfix": "CAPEX fijo $/Wp (0 = bottom-up × factor)", "fT": "Factor tarifa", "scen": "Escenario energía (1=P50, 2=P90)",
               "fO": "Factor OPEX", "pj": "Peaje $/kWh", "escT": "Escalación tarifa", "part": "Participación (1/0)", "iva": "IVA recuperable (1/0)", "cont": "Contrato inversión (1/0)",
               "deb": "Deuda (1/0)", "rd": "Tasa deuda", "lev": "Apalancamiento", "plazo": "Plazo", "gr": "Gracia", "P": "Potencia DC (kWp)", "ratio": "Ratio DC/AC",
               "terr": "Terreno lo compra SALELGI (1/0)", "finT": "Banco financia terreno (1/0)", "fPre": "Factor precio terreno",
               # v3.0 (ronda 2)
               "disp": "Disponibilidad", "dK": "Escalación CAPEX (%/año hasta la compra)", "pkw": "Peaje por potencia $/kW-mes", "rep": "Reemplazo inversores (0 No · 1 SALELGI · 2 Exergy)",
               "ug": "Utilidad gravable SALELGI (−1 = ilimitada)", "ncon": "Meses de construcción", "req": "Tasa descuento accionista", "dec": "Desmantelamiento (% CAPEX en t=H)",
               "deg": "Degradación adicional (%/año)",
               # v3.1: deducción adicional aplicable (1/0); ausente en libros anteriores → 1
               "dedad": "Deducción adicional aplicable (1/0)"}
NEUTRAL = {"disp": 1.0, "dK": 0.0, "pkw": 0.0, "rep": 0, "ug": -1, "ncon": 12, "req": None, "dec": 0.0, "deg": 0.0, "dedad": 1}
LABEL_SCAL = {"frec": "Factor de recorte", "AC": "Potencia AC (kW)", "ha": "Hectáreas", "K": "CAPEX industrial sin IVA", "IVA": "IVA CAPEX", "Kdep": "CAPEX depreciable",
              "DepEq": "Dep. equipos/año", "DepCiv": "Dep. civil/año", "DedAd": "Deducción adicional/año", "Terr": "Terreno (costo total quien compra)", "Resid": "Residual terreno neto (t=H)",
              "OPEX1": "OPEX año 1 SALELGI", "Sub": "Subtotal EPC (base fee)", "D": "Deuda", "IDC": "IDC", "Dt": "Deuda total COD", "n": "Nº cuotas", "PMT": "Cuota", "fKeff": "Factor CAPEX efectivo",
              "fEsc": "Factor de escalación del CAPEX", "Krep": "Reemplazo de inversores (USD)", "Decom": "Desmantelamiento (USD)"}
LABEL_OUT = {"TIR": "TIR proyecto", "VAN": "VAN proyecto", "PB": "Payback simple", "LCOE": "LCOE $/MWh", "TIR_eq": "TIR equity", "VAN_eq": "VAN equity", "DSCR_min": "DSCR mín",
             "DSCR_avg": "DSCR prom", "Ahorro1": "Ahorro año 1", "Aporte_eq": "Aporte equity", "VAN_X": "VAN Exergy", "TIR_G": "TIR grupo", "E1": "Energía año 1 (MWh)",
             "NoRec": "Energía no reconocida Σ (MWh)", "Cob": "Cobertura año 1", "Nominal_X": "Nominal Exergy Σ"}
BLOCKS_V20 = ["E", "Eval", "Ahorro", "OPEX", "Peaje", "EBITDA", "Dep", "Part_u", "IR_u", "Terr", "FCF_u", "Cum_u", "Int", "Amort", "Part_l", "IR_l", "CFADS", "EQ", "DSCR", "DF", "Ux", "Ix", "Tx", "Fx", "Gx"]
BLOCKS_V30 = BLOCKS_V20 + ["Krep", "PoolU", "PoolL"]


def irr(cfs):
    cfs = np.array(cfs, dtype=float)
    f = lambda r: np.sum(cfs / (1 + r) ** np.arange(len(cfs)))
    lo, hi = -0.99, 1.0
    if f(lo) * f(hi) > 0:
        return float("nan")
    for _ in range(300):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0: hi = mid
        else: lo = mid
    return (lo + hi) / 2


def npv0(rate, cfs):  # cfs[0]=t−1 capitalizado; cfs[1]=t0; resto descontado
    return cfs[0] * (1 + rate) + cfs[1] + sum(cf / (1 + rate) ** t for t, cf in zip(range(1, len(cfs) - 1), cfs[2:]))


def edate(d, months):
    y = d.year + (d.month - 1 + months) // 12; m = (d.month - 1 + months) % 12 + 1
    return date(y, m, min(d.day, 28))


class Book:
    def __init__(self, path):
        self.wb = load_workbook(path, data_only=True)
        self.names = {n: d.attr_text for n, d in self.wb.defined_names.items()}

    def has(self, nm):
        return nm in self.names

    def v(self, nm, default=None):
        if nm not in self.names:
            return default
        ref = self.names[nm].split("!"); sh = ref[0].strip("'"); cell = ref[1].replace("$", "")
        if ":" in cell:
            ws = self.wb[sh]; a, b = cell.split(":")
            return [c.value for row in ws[a:b] for c in row]
        return self.wb[sh][cell].value


def motor_rows(ws):
    """Mapa etiqueta → fila del Motor (columna A). Escalares/parámetros/salidas por su texto; filas anuales por (bloque, t)."""
    rows = {}; block = None
    for r in range(1, ws.max_row + 1):
        v = ws.cell(row=r, column=1).value
        if v is None:
            continue
        if isinstance(v, str) and v.startswith("Bloque "):
            block = v.split(" ")[1]; continue
        if block is not None and isinstance(v, (int, float)) and not isinstance(v, bool):
            rows[(block, int(v))] = r
        elif isinstance(v, str):
            rows[v] = r
    return rows


def load_inputs(B):
    P = {}
    for nm in ["Horizonte", "Tasa_Descuento", "Fase_m1", "Tasa_IVA", "FODINFA_Pct", "ISD_Pct", "Contingencia_Pct", "Contingencia_Frac_IVA", "Fee_Gerencia_Pct", "Asignacion_Compartida",
               "Fee_OM_kWp", "Seguro_kWp", "Renta_Terreno_ha", "Tributos_Locales", "Escalacion_OPEX", "Precio_Terreno_ha", "Costos_Transaccion_Terreno_Pct", "Predial_Terreno", "Residual_Terreno_Pct", "Apreciacion_Terreno",
               "Tasa_IR", "Tasa_Participacion", "Vida_Fiscal_Equipos", "Vida_Fiscal_Civil", "Pct_Elegible_DedAd", "Ingresos_SALELGI", "Tope_DedAd_Pct", "IDC_Frac_Tramo0",
               "Costo_Gerencia_Pct", "Costo_OM_Exergy_kWp", "Tasa_Efectiva_Exergy", "Potencia_Ref", "Ratio_Ref", "Densidad_MWp_ha", "Exponente_Escala", "Crecimiento_Consumo",
               "Tarifa_Evitable", "Consumo_Anual", "Pct_CAPEX_Civil", "Tasa_Efectiva"]:
        P[nm] = B.v(nm)
    P["escudo"] = B.v("Escudo_Negativo") == "Sí"
    for k in ("Fecha_COD", "Fecha_Peaje", "Fecha_Precios"):
        d = B.v(k); P[k] = d.date() if hasattr(d, "date") else d
    if P["Fecha_Precios"] is None:
        P["Fecha_Precios"] = date(2026, 7, 22)   # fecha de precios del deck v4 (doc 13 §2.1): valor de la ronda 2 si el libro no la define (v2.0)
    P["cod"] = P["Fecha_COD"]; P["fpeaje"] = P["Fecha_Peaje"]
    # v3.0 compartidos (ausentes en v2.0 → neutros)
    if B.has("Anios_Precios"):
        P["Anios_Precios"] = B.v("Anios_Precios")
    elif P.get("Fecha_Precios") is not None:
        P["Anios_Precios"] = (P["cod"] - P["Fecha_Precios"]).days / 365.25
    else:
        P["Anios_Precios"] = 0.0
    P["Reemplazo_Anio"] = B.v("Reemplazo_Anio", 0) or 0
    P["Reemplazo_USD_Wac"] = B.v("Reemplazo_USD_Wac", 0.0) or 0.0
    P["Y50"] = [x for x in B.v("Y_P50")]; P["Y90"] = [x for x in B.v("Y_P90")]
    P["cr_ratio"] = B.v("CR_Ratio"); P["cr_loss"] = B.v("CR_Loss")
    # rubros de 05_CAPEX: costo base D, %comp E, %ext G, arancel I, IVA O; drivers por nombre (V7: Drv_Wp/Drv_Wac/Drv_Fijo) o columnas S T U (v2.0)
    ws = B.wb["05_CAPEX"]
    r0 = KL["r0"]
    if B.has("Drv_Wp"):
        dwp, dwac, dfx = B.v("Drv_Wp"), B.v("Drv_Wac"), B.v("Drv_Fijo")
    else:
        dwp = [ws[f"S{r}"].value for r in range(r0, r0 + 9)]; dwac = [ws[f"T{r}"].value for r in range(r0, r0 + 9)]; dfx = [ws[f"U{r}"].value for r in range(r0, r0 + 9)]
    P["rubros"] = [dict(cost=ws[f"D{r}"].value, comp=ws[f"E{r}"].value, ext=ws[f"G{r}"].value, ar=ws[f"I{r}"].value, iva=ws[f"O{r}"].value, wp=dwp[i], wac=dwac[i], wf=dfx[i])
                   for i, r in enumerate(range(r0, r0 + 9))]
    P["iva_fee"] = ws[f"O{KL['fee']}"].value
    return P


def loss(P, r):
    xs, ys = P["cr_ratio"], P["cr_loss"]
    r = min(max(r, xs[0]), xs[-1])
    for i in range(len(xs) - 1):
        if xs[i] <= r <= xs[i + 1]:
            return ys[i] + (r - xs[i]) * (ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i])
    return ys[-1]


def capex(P, fK, cont, Pkw, ratio, kfix=0.0):
    """CAPEX industrial sin IVA, IVA y subtotal EPC a factor de caso (sin escalación): bottom-up × fK, o kfix $/Wp × kWp × 1000 si kfix > 0."""
    a = (Pkw / P["Potencia_Ref"]) ** (1 - P["Exponente_Escala"]); b = ((Pkw / ratio) / (P["Potencia_Ref"] / P["Ratio_Ref"])) ** (1 - P["Exponente_Escala"])
    cap = iva = 0.0
    for rb in P["rubros"]:
        S = rb["cost"] * (1 - rb["comp"] * (1 - P["Asignacion_Compartida"]))
        esc = rb["wp"] * a + rb["wac"] * b + rb["wf"]
        F = S * esc
        vext = F * rb["ext"]; ar = vext * rb["ar"]; fod = vext * P["FODINFA_Pct"]; isd = vext * P["ISD_Pct"]
        cap += F + fod + (0 if cont else ar + isd)
        iva += (F + fod + (0 if cont else ar)) * rb["iva"]
    contg = P["Contingencia_Pct"] * cap
    iva += contg * P["Tasa_IVA"] * P["Contingencia_Frac_IVA"]
    sub = cap + contg
    fee = P["Fee_Gerencia_Pct"] * sub
    iva += fee * P["iva_fee"]
    base = sub + fee
    f = (kfix * Pkw * 1000 / base) if (kfix and kfix > 0) else fK
    return base * f, iva * f, sub * f, f


def _num(x, default):
    return default if x is None or (isinstance(x, str)) else x


def run_case(P, pc):
    """Un caso: pc = parámetros de la columna del Motor (claves de LABEL_PARAM; los v3.0 ausentes valen neutro). Devuelve (KPI, bloques)."""
    H = int(P["Horizonte"]); T = list(range(-1, H + 1)); r = P["Tasa_Descuento"]
    disp = _num(pc.get("disp"), 1.0); dK = _num(pc.get("dK"), 0.0); pkw = _num(pc.get("pkw"), 0.0); rep = int(_num(pc.get("rep"), 0))
    ug_raw = pc.get("ug"); ug = None if (ug_raw is None or isinstance(ug_raw, str) or ug_raw < 0) else float(ug_raw)
    ncon = _num(pc.get("ncon"), 12); req = pc.get("req"); r_eq = r if (req is None or isinstance(req, str)) else req
    dec = _num(pc.get("dec"), 0.0); deg = _num(pc.get("deg"), 0.0)
    Pkw, ratio, terr, finT, fPre = pc["P"], pc["ratio"], int(pc["terr"]), int(pc["finT"]), pc["fPre"]
    Pac = Pkw / ratio
    frec = (1 - loss(P, ratio)) / (1 - loss(P, P["Ratio_Ref"]))
    ha = Pkw / 1000 / P["Densidad_MWp_ha"]
    K0, IVA0, sub0, fKeff = capex(P, pc["fK"], int(pc["cont"]) == 1, Pkw, ratio, kfix=(pc.get("kfix") or 0.0))
    fase = P["Fase_m1"]
    # M-a: escalación de precios hasta el desembolso (t = −1: Anios_Precios − 1; t = 0: Anios_Precios)
    y0 = P["Anios_Precios"]; y1 = max(0.0, y0 - 1.0)
    fEsc = fase * (1 + dK) ** y1 + (1 - fase) * (1 + dK) ** y0
    K, IVA, sub = K0 * fEsc, IVA0 * fEsc, sub0 * fEsc
    recup = int(pc["iva"]) == 1; part_on = int(pc["part"]) == 1; esc = P["escudo"]
    Kdep = K + (0 if recup else IVA)
    dep_eq = Kdep * (1 - P["Pct_CAPEX_Civil"]) / P["Vida_Fiscal_Equipos"]; dep_civ = Kdep * P["Pct_CAPEX_Civil"] / P["Vida_Fiscal_Civil"]
    dedad = int(pc.get("dedad", 1)) * min(Kdep * P["Pct_Elegible_DedAd"] / P["Vida_Fiscal_Equipos"], P["Tope_DedAd_Pct"] * P["Ingresos_SALELGI"])   # v3.1: × aplicable
    terr_cost = P["Precio_Terreno_ha"] * fPre * ha * (1 + P["Costos_Transaccion_Terreno_Pct"])
    resid_g = P["Precio_Terreno_ha"] * fPre * ha * P["Residual_Terreno_Pct"] * (1 + P["Apreciacion_Terreno"]) ** (H + 1)
    te_owner = P["Tasa_Efectiva"] if terr else P["Tasa_Efectiva_Exergy"]
    resid_net = resid_g - max(0, resid_g - terr_cost) * te_owner
    opex1 = (P["Fee_OM_kWp"] + P["Seguro_kWp"]) * Pkw + (P["Predial_Terreno"] if terr else P["Renta_Terreno_ha"] * ha) + P["Tributos_Locales"]
    Y = P["Y50"] if int(pc["scen"]) == 1 else P["Y90"]
    def frac_peaje(t):
        a_ = edate(P["cod"], 12 * (t - 1)); b_ = edate(P["cod"], 12 * t)
        return max(0, min(1, (b_ - max(P["fpeaje"], a_)).days / (b_ - a_).days))
    # M-c: reemplazo de inversores (Krep) y desmantelamiento (Decom)
    t_rep = int(P["Reemplazo_Anio"] or 0)
    Krep = (P["Reemplazo_USD_Wac"] * Pac * 1000) if rep > 0 else 0.0
    vida_rep = min(P["Vida_Fiscal_Equipos"], H - t_rep) if (rep == 1 and 0 < t_rep < H) else 0
    Decom = dec * K
    E = {}; EV = {}; AH = {}; OP = {}; PJ = {}; EB = {}; DP = {}; TR = {}; KX = {}; FU = {}; CU = {}
    for t in T:
        E[t] = 0 if (t < 1 or t > H) else Pkw / 1000 * frec * Y[t - 1] * disp * (1 - deg) ** (t - 1)
        EV[t] = 0 if t < 1 else min(E[t], P["Consumo_Anual"] * (1 + P["Crecimiento_Consumo"]) ** (t - 1) / 1000)
        AH[t] = EV[t] * 1000 * P["Tarifa_Evitable"] * pc["fT"] * (1 + pc["escT"]) ** max(0, t - 1)
        OP[t] = 0 if (t < 1 or t > H) else opex1 * pc["fO"] * (1 + P["Escalacion_OPEX"]) ** (t - 1)
        fp = frac_peaje(t) if t >= 1 else 0
        PJ[t] = E[t] * 1000 * pc["pj"] * fp + (Pac * pkw * 12 * fp if (1 <= t <= H) else 0)   # M-h
        EB[t] = AH[t] - OP[t] - PJ[t] - (Decom if t == H else 0)
        dep_rep = (Krep / vida_rep) if (vida_rep > 0 and t_rep < t <= t_rep + vida_rep) else 0.0
        DP[t] = (dep_eq if 1 <= t <= P["Vida_Fiscal_Equipos"] else 0) + (dep_civ if 1 <= t <= min(P["Vida_Fiscal_Civil"], H) else 0) + dep_rep
        KX[t] = Krep if (rep == 1 and t == t_rep) else 0.0
        TR[t] = (-terr_cost if t == -1 else (resid_net if t == H else 0)) if terr else 0
    # fiscal: absorción ilimitada (ug vacío: gobierna Escudo_Negativo) o limitada a ug con pool de pérdidas sin caducidad (art. 11 LRTI, ≤ 25 %)
    def fiscal(IN):
        PL = {}; IL = {}; POOL = {}; pool = 0.0
        for t in T:
            da = dedad if 1 <= t <= P["Vida_Fiscal_Equipos"] else 0
            base_part = (EB[t] - DP[t] - IN[t]) if part_on else 0.0
            if ug is None:
                pl = P["Tasa_Participacion"] * base_part if part_on else 0
                PL[t] = pl if esc else max(0, pl)
                il = P["Tasa_IR"] * (EB[t] - DP[t] - IN[t] - PL[t] - da); IL[t] = il if esc else max(0, il)
                POOL[t] = 0.0
            else:
                U = ug if t >= 1 else 0.0
                PL[t] = (P["Tasa_Participacion"] * base_part) if base_part >= 0 else -P["Tasa_Participacion"] * min(-base_part, U)
                if not part_on: PL[t] = 0.0
                base_ir = EB[t] - DP[t] - IN[t] - PL[t] - da
                if base_ir >= 0:
                    use = min(pool, 0.25 * (base_ir + U))
                    IL[t] = P["Tasa_IR"] * (base_ir - use); pool -= use
                else:
                    absorbed = min(-base_ir, U)
                    IL[t] = -P["Tasa_IR"] * absorbed; pool += (-base_ir - absorbed)
                POOL[t] = pool
        return PL, IL, POOL
    ZERO = {t: 0.0 for t in T}
    PU, IU, POOLU = fiscal(ZERO)
    for t in T:
        if t == -1: FU[t] = -(K + IVA) * fase + TR[t]
        elif t == 0: FU[t] = -(K + IVA) * (1 - fase) + (IVA * fase if recup else 0) + TR[t]
        else: FU[t] = EB[t] - PU[t] - IU[t] + (IVA * (1 - fase) if (t == 1 and recup) else 0) + TR[t] - KX[t]
        CU[t] = FU[t] + (CU[t - 1] if t > -1 else 0)
    # deuda (M-e: IDC × meses de construcción / 12)
    D = int(pc["deb"]) * pc["lev"] * (K + finT * terr * terr_cost); rd = pc["rd"]; gr = int(pc["gr"]); pl = int(pc["plazo"])
    idc = D * rd * (fase + (1 - fase) * P["IDC_Frac_Tramo0"]) * (ncon / 12.0); Dt = D + idc; n = max(1, pl - gr)
    pmt = 0 if Dt <= 0 else (Dt / n if rd == 0 else Dt * rd / (1 - (1 + rd) ** (-n)))
    IN = {}; AM = {}; bal = Dt
    for t in T:
        if t < 1 or D == 0 or t > pl: IN[t] = 0; AM[t] = 0
        elif t <= gr:
            IN[t] = Dt * rd; AM[t] = Dt if (pl <= gr and t == pl) else 0
        else:
            IN[t] = bal * rd; AM[t] = pmt - IN[t] if pl > gr else 0; bal -= AM[t]
    PL, IL, POOLL = fiscal(IN)
    CF = {}; EQ = {}; DS = {}; DFc = {}
    for t in T:
        CF[t] = 0 if t < 1 else EB[t] - PL[t] - IL[t] + (IVA * (1 - fase) if (t == 1 and recup) else 0) + TR[t] - KX[t]
        if t == -1: EQ[t] = FU[t] + D * fase
        elif t == 0: EQ[t] = FU[t] + D * (1 - fase)
        else: EQ[t] = CF[t] - IN[t] - AM[t]
        DS[t] = (CF[t] / (IN[t] + AM[t])) if IN[t] + AM[t] > 0 else None
        DFc[t] = 0 if t < 1 else 1 / (1 + r) ** t
    # Exergy (reemplazo pagado por Exergy: gasto deducible en t = Reemplazo_Anio)
    UX = {}; IX = {}; TX = {}; FX = {}; GX = {}
    for t in T:
        g = (1 + P["Escalacion_OPEX"]) ** (t - 1)
        ux = 0
        if t == -1: ux = (P["Fee_Gerencia_Pct"] - P["Costo_Gerencia_Pct"]) * sub * fase
        elif t == 0: ux = (P["Fee_Gerencia_Pct"] - P["Costo_Gerencia_Pct"]) * sub * (1 - fase)
        if 1 <= t <= H:
            ux += (1 - terr) * (P["Renta_Terreno_ha"] * ha - P["Predial_Terreno"]) * g + (P["Fee_OM_kWp"] - P["Costo_OM_Exergy_kWp"]) * Pkw * g
        if rep == 2 and t == t_rep: ux -= Krep
        UX[t] = ux
        IX[t] = -max(0, ux) * P["Tasa_Efectiva_Exergy"]
        TX[t] = 0 if terr else (-terr_cost if t == -1 else (resid_net if t == H else 0))
        FX[t] = ux + IX[t] + TX[t]; GX[t] = FU[t] + FX[t]
    fu = [FU[t] for t in T]; eq = [EQ[t] for t in T]; fx = [FX[t] for t in T]; gx = [GX[t] for t in T]
    cum = np.cumsum(fu)
    # payback robusto: último año con acumulado negativo (coincide con el simple si hay un solo cruce)
    neg = [i for i, c in enumerate(cum) if c < 0]
    if neg and neg[-1] + 1 < len(fu):
        i = neg[-1]; pb = (i - 1) + (-cum[i]) / fu[i + 1]   # T[i] = i − 1
    else: pb = None
    ds_vals = [v for t, v in DS.items() if v is not None and t >= 1]
    lcoe = (K + sum((OP[t] + PJ[t]) * DFc[t] for t in T)) / sum(E[t] * DFc[t] for t in T)
    out = dict(TIR=irr(fu), VAN=npv0(r, fu), PB=pb, LCOE=lcoe, TIR_eq=(irr(eq) if D > 0 else None), VAN_eq=npv0(r_eq, eq),
               DSCR_min=(min(ds_vals) if (D > 0 and ds_vals) else None), DSCR_avg=(sum(ds_vals) / len(ds_vals) if (D > 0 and ds_vals) else None),
               Ahorro1=AH[1], Aporte_eq=-(EQ[-1] + EQ[0]), VAN_X=npv0(r, fx), TIR_G=irr(gx), E1=E[1], NoRec=sum(E[t] - EV[t] for t in T),
               Cob=E[1] * 1000 / P["Consumo_Anual"], Nominal_X=sum(fx),
               # escalares (v2.0 + v3.0)
               frec=frec, AC=Pac, ha=ha, K=K, IVA=IVA, Kdep=Kdep, DepEq=dep_eq, DepCiv=dep_civ, DedAd=dedad, Terr=terr_cost, Resid=resid_net, OPEX1=opex1, Sub=sub,
               D=D, IDC=idc, Dt=Dt, n=n, PMT=pmt, fKeff=fKeff, fEsc=fEsc, Krep=Krep, Decom=Decom)
    blocks = dict(E=E, Eval=EV, Ahorro=AH, OPEX=OP, Peaje=PJ, EBITDA=EB, Dep=DP, Part_u=PU, IR_u=IU, Terr=TR, FCF_u=FU, Cum_u=CU, Int=IN, Amort=AM, Part_l=PL, IR_l=IL,
                  CFADS=CF, EQ=EQ, DSCR=DS, DF=DFc, Ux=UX, Ix=IX, Tx=TX, Fx=FX, Gx=GX, Krep={t: -KX[t] for t in T}, PoolU=POOLU, PoolL=POOLL)
    return out, blocks


def read_case(wsm, rows, X):
    pc = {}
    for k, lab in LABEL_PARAM.items():
        if lab in rows:
            pc[k] = wsm[f"{X}{rows[lab]}"].value
        elif k in NEUTRAL:
            pc[k] = NEUTRAL[k]
        else:
            raise KeyError(f"fila de parámetro no encontrada en el Motor: {lab!r}")
    return pc


def main():
    VAL, OUT = sys.argv[1], sys.argv[2]
    do_blocks = "--blocks" in sys.argv; quiet = "--quiet" in sys.argv
    tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 1e-6
    B = Book(VAL); P = load_inputs(B)
    wsm = B.wb["Motor_Sens"]; rows = motor_rows(wsm)
    present_new = [k for k in NEUTRAL if LABEL_PARAM[k] in rows]
    ncases = 0
    while wsm.cell(row=4, column=2 + ncases).value is not None:
        ncases += 1
    rows_csv = []; worst = 0.0; nfail = 0; ncmp = 0; nb_cmp = nb_fail = 0; worst_b = 0.0; bad_b = []
    scal_keys = [k for k in LABEL_SCAL if LABEL_SCAL[k] in rows]
    blocks_present = [b for b in BLOCKS_V30 if (b, 1) in rows]
    for j in range(ncases):
        X = gl(2 + j); name = wsm[f"{X}4"].value
        pc = read_case(wsm, rows, X)
        out, blk = run_case(P, pc)
        for k, lab in list(LABEL_OUT.items()) + [(k, LABEL_SCAL[k]) for k in scal_keys]:
            if lab not in rows:
                continue
            book = wsm[f"{X}{rows[lab]}"].value; mine = out[k]
            if isinstance(book, (int, float)) and not isinstance(book, bool) and isinstance(mine, (int, float)) and not (isinstance(mine, float) and math.isnan(mine)):
                d = abs(book - mine) / max(1.0, abs(book)); ok = d <= tol; worst = max(worst, d); nfail += (not ok); ncmp += 1
                rows_csv.append((j, name, k, book, mine, d, "●" if ok else "■"))
                if not ok and nfail <= 15 and not quiet: print("  ■", j, name, k, book, mine)
            else:
                rows_csv.append((j, name, k, book, mine, None, "—"))
        if do_blocks:
            for b in blocks_present:
                for t in TS:
                    if (b, t) not in rows: continue
                    book = wsm[f"{X}{rows[(b, t)]}"].value; mine = blk[b][t]
                    if isinstance(book, (int, float)) and not isinstance(book, bool) and isinstance(mine, (int, float)):
                        d = abs(book - mine) / max(1.0, abs(book)); nb_cmp += 1; worst_b = max(worst_b, d)
                        if d > tol:
                            nb_fail += 1
                            if len(bad_b) < 10: bad_b.append((name, b, t, book, mine))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["caso", "nombre", "kpi", "libro", "sombra", "delta_rel", "estado"]); [w.writerow(x) for x in rows_csv]
    tag = "v3.0" if present_new else "v2.0 (parámetros nuevos ausentes → neutro)"
    print(f"sombra30 sobre Motor {tag}: {ncases} casos · {ncmp} KPI/escalares comparados · {nfail} difieren · peor Δrel {worst:.3g}")
    if do_blocks:
        print(f"  bloques ({len(blocks_present)}: {', '.join(blocks_present)}): {nb_cmp} celdas anuales comparadas · {nb_fail} difieren · peor Δrel {worst_b:.3g}")
        for x in bad_b: print("   ■ bloque", x)
    # hojas principales (Custom = columna B): 08 FCF sin deuda, equity; 09 FCF Exergy
    pc = read_case(wsm, rows, "B"); out, blk = run_case(P, pc)
    ws8 = B.wb["08_Flujo"]; ws9 = B.wb["09_Exergy"]
    d8 = max(abs(ws8[f"{C(t)}{FLUJO['fcf']}"].value - blk["FCF_u"][t]) for t in TS)
    de = max(abs(ws8[f"{C(t)}{FLUJO['eq']}"].value - blk["EQ"][t]) for t in TS)
    d9 = max(abs(ws9[f"{C(t)}{EXERGY['fcf']}"].value - blk["Fx"][t]) for t in TS)
    print(f"08_Flujo FCF Δmáx {d8:.3g} · equity Δmáx {de:.3g} · 09_Exergy FCF Δmáx {d9:.3g} · TIR_Proyecto libro {B.v('TIR_Proyecto'):.6%} sombra {out['TIR']:.6%} · VAN_Exergy {B.v('VAN_Exergy'):,.2f} / {out['VAN_X']:,.2f}")
    if nfail or (do_blocks and nb_fail) or d8 > 1e-6 or de > 1e-6 or d9 > 1e-6:
        sys.exit(1)


if __name__ == "__main__":
    main()
