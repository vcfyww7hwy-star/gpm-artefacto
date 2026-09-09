"""Prototipo de sombra del Motor_Sens (Modelo_FV_5MWp_GPM_v3.0.xlsx).

Transliteración fiel, en Python puro, de la lógica columnar del Motor (29 parámetros por caso,
escalares, 28 bloques anuales t = -1..25, 16 salidas). Se usa como (a) prueba de viabilidad de la
portabilidad a JavaScript y (b) segundo motor de verificación (Excel · sombra · JS).
"""
import datetime as dt
import math
import json
import sys
import openpyxl
from openpyxl.utils import get_column_letter

XLSX = sys.argv[1] if len(sys.argv) > 1 else 'modelo.xlsx'
wb = openpyxl.load_workbook(XLSX, data_only=True)
wbf = openpyxl.load_workbook(XLSX, data_only=False)

# ----------------------------------------------------------------------------- nombres
import re
def name_val(n):
    ref = wb.defined_names[n].attr_text
    m = re.match(r"^'?([^'!]+)'?!\$?([A-Z]+)\$?(\d+)(?::\$?([A-Z]+)\$?(\d+))?$", ref)
    sh, c1, r1, c2, r2 = m.groups()
    ws = wb[sh]
    if c2 is None:
        return ws[f"{c1}{r1}"].value
    # rango -> lista (fila o columna)
    cells = ws[f"{c1}{r1}:{c2}{r2}"]
    vals = [c.value for row in cells for c in row]
    return vals

N = {n: name_val(n) for n in wb.defined_names.keys()}

def edate(d, months):
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    # Excel EDATE: mismo día, o último día del mes si no existe
    import calendar
    last = calendar.monthrange(y, m)[1]
    return dt.date(y, m, min(d.day, last))

def to_date(v):
    return v.date() if isinstance(v, dt.datetime) else v

# ----------------------------------------------------------------------------- globales de 01
G = {}
for k in ['Potencia_Ref','Ratio_Ref','Exponente_Escala','Densidad_MWp_ha','Fase_m1','IDC_Frac_Tramo0','Horizonte',
          'Tasa_Descuento','Tasa_IR','Tasa_Participacion','Vida_Fiscal_Equipos','Vida_Fiscal_Civil','Pct_Elegible_DedAd',
          'Tope_DedAd_Pct','Ingresos_SALELGI','Precio_Terreno_ha','Costos_Transaccion_Terreno_Pct','Residual_Terreno_Pct',
          'Apreciacion_Terreno','Tasa_Efectiva_Exergy','Fee_OM_kWp','Seguro_kWp','Predial_Terreno','Renta_Terreno_ha',
          'Tributos_Locales','Escalacion_OPEX','Fee_Gerencia_Pct','Costo_Gerencia_Pct','Costo_OM_Exergy_kWp','Reemplazo_Anio',
          'Reemplazo_USD_Wac','Crecimiento_Consumo','Tasa_IVA','FODINFA_Pct','ISD_Pct','Contingencia_Pct','Contingencia_Frac_IVA',
          'Asignacion_Compartida','Frac_A','Frac_B','Frac_C','Tarifa_A','Tarifa_C','Escudo_Negativo','Incluir_Participacion']:
    G[k] = N[k]
Fecha_COD = to_date(N['Fecha_COD']); Fecha_Peaje = to_date(N['Fecha_Peaje']); Fecha_Precios = to_date(N['Fecha_Precios'])
G['Anios_Precios'] = (Fecha_COD - Fecha_Precios).days / 365.25
G['Tasa_Efectiva'] = (G['Tasa_Participacion'] if G['Incluir_Participacion'] == 'Sí' else 0) + G['Tasa_IR'] * (1 - (G['Tasa_Participacion'] if G['Incluir_Participacion'] == 'Sí' else 0))
H = int(G['Horizonte'])

# ----------------------------------------------------------------------------- 04 Energía
ws04 = wb['04_Energia']
cons25 = [[ws04.cell(r, c).value for c in (4, 5, 6)] for r in range(17, 29)]   # D,E,F 2025 por bloque
factor_nivel = sum(ws04.cell(r, 5).value for r in range(66, 71)) / sum(ws04.cell(r, 4).value for r in range(66, 71))
consumo_mes = [sum(x) * factor_nivel for x in cons25]
Consumo_Anual = sum(consumo_mes)
Tarifa_Evitable_calc = G['Frac_A'] * G['Tarifa_A'] + G['Frac_B'] * G['Tarifa_A'] + G['Frac_C'] * G['Tarifa_C']
Y_P50 = [ws04.cell(91, c).value for c in range(6, 36)]
Y_P90 = [ws04.cell(92, c).value for c in range(6, 36)]
CR_Ratio = [ws04.cell(r, 8).value for r in range(66, 80)]
CR_Loss = [ws04.cell(r, 9).value for r in range(66, 80)]

def loss_at(ratio):
    """INDEX/MATCH lineal sobre la curva de recorte, con ratio acotado al rango."""
    x = min(max(ratio, CR_Ratio[0]), CR_Ratio[-1])
    # MATCH(x, CR_Ratio, 1) -> mayor valor <= x (1-based), acotado a ROWS-1
    k = max(i for i, v in enumerate(CR_Ratio) if v <= x)
    k = min(k, len(CR_Ratio) - 2)
    return CR_Loss[k] + (x - CR_Ratio[k]) * (CR_Loss[k + 1] - CR_Loss[k]) / (CR_Ratio[k + 1] - CR_Ratio[k])

Loss_Ref = loss_at(G['Ratio_Ref'])

def frac_peaje(t):
    if t < 1:
        return 0.0
    ini = edate(Fecha_COD, 12 * (t - 1)); fin = edate(Fecha_COD, 12 * t)
    a = max(Fecha_Peaje, ini)
    return max(0.0, min(1.0, (fin - a).days / (fin - ini).days))

# ----------------------------------------------------------------------------- 05 CAPEX (tabla de rubros)
ws05 = wb['05_CAPEX']
rubros = []
for r in range(7, 16):
    D, E, Gext, I, O = (ws05.cell(r, 4).value, ws05.cell(r, 5).value, ws05.cell(r, 7).value, ws05.cell(r, 9).value, ws05.cell(r, 15).value)
    drv = (ws05.cell(38 + r, 4).value, ws05.cell(38 + r, 5).value, ws05.cell(38 + r, 6).value)  # filas 45..53
    rubros.append(dict(D=D, E=E, G=Gext, I=I, O=O, drv=drv))

def capex_descomposicion():
    """Devuelve CAPEX_SC/CC y IVA_SC/CC por driver (Wp, Wac, fijo) a factor 1 y 5.000 kWp, y Pct_CAPEX_Civil."""
    X = []; Y = []; Z = []; AA = []
    for rb in rubros:
        V = rb['D'] * (1 - rb['E'] * (1 - G['Asignacion_Compartida']))
        X.append(V + V * rb['G'] * G['FODINFA_Pct'] + V * rb['G'] * (rb['I'] + G['ISD_Pct']))
        Y.append(V + V * rb['G'] * G['FODINFA_Pct'])
        Z.append((V + V * rb['G'] * G['FODINFA_Pct'] + V * rb['G'] * rb['I']) * rb['O'])
        AA.append((V + V * rb['G'] * G['FODINFA_Pct']) * rb['O'])
    out = {}
    for tag, base, ivab in (('SC', X, Z), ('CC', Y, AA)):
        tot = [0.0, 0.0, 0.0]; iva = [0.0, 0.0, 0.0]
        for i, rb in enumerate(rubros):
            for j in range(3):
                tot[j] += base[i] * rb['drv'][j]
                iva[j] += ivab[i] * rb['drv'][j]
        cont = [G['Contingencia_Pct'] * v for v in tot]
        cont_iva = [c * G['Tasa_IVA'] * G['Contingencia_Frac_IVA'] for c in cont]
        sub = [tot[j] + cont[j] for j in range(3)]
        fee = [G['Fee_Gerencia_Pct'] * s for s in sub]
        fee_iva = [f * 0.15 for f in fee]  # O18 = 15 %
        out['CAPEX_' + tag] = [sub[j] + fee[j] for j in range(3)]
        out['IVA_' + tag] = [iva[j] + cont_iva[j] + fee_iva[j] for j in range(3)]
    # Pct_CAPEX_Civil = N12/N19 (hoja del Custom; a factor del Custom, cociente independiente del factor común)
    # N12 = capitalizable rubro 6 = F6 + K6 + M6 con F = V*Factor_Caso*(drv·escala). Con Escala = 1 (Custom 5.000 kWp) el cociente = X[5]/CAPEX_SC_total
    return out

CAP = capex_descomposicion()

# Pct_CAPEX_Civil exacto según la hoja 05 del Custom (depende de Escala_Wp/Wac del Custom y del contrato)
def pct_capex_civil(P_dc, ratio, contrato):
    esc_wp = (P_dc / G['Potencia_Ref']) ** (1 - G['Exponente_Escala'])
    esc_wac = ((P_dc / ratio) / (G['Potencia_Ref'] / G['Ratio_Ref'])) ** (1 - G['Exponente_Escala'])
    Ns = []
    for rb in rubros:
        V = rb['D'] * (1 - rb['E'] * (1 - G['Asignacion_Compartida']))
        F = V * (rb['drv'][0] * esc_wp + rb['drv'][1] * esc_wac + rb['drv'][2])  # Factor_Caso se cancela en el cociente
        Hh = F * rb['G']; J = Hh * rb['I']; K = Hh * G['FODINFA_Pct']; L = Hh * G['ISD_Pct']
        M = 0 if contrato else J + L
        Ns.append(F + K + M)
    cont = G['Contingencia_Pct'] * sum(Ns)
    sub = sum(Ns) + cont
    total = sub + G['Fee_Gerencia_Pct'] * sub
    return Ns[5] / total

# ----------------------------------------------------------------------------- finanzas
def npv(rate, vals):
    return sum(v / (1 + rate) ** (i + 1) for i, v in enumerate(vals))

def irr(vals, guess=0.1):
    """IRR estilo Excel: Newton desde guess con salvaguarda de bisección; precisión alta."""
    def f(r):
        return sum(v / (1 + r) ** i for i, v in enumerate(vals))
    def df(r):
        return sum(-i * v / (1 + r) ** (i + 1) for i, v in enumerate(vals))
    r = guess
    for _ in range(100):
        fv = f(r); d = df(r)
        if d == 0:
            break
        nr = r - fv / d
        if nr <= -0.999999:
            nr = (r - 0.999999) / 2
        if abs(nr - r) < 1e-14:
            r = nr; break
        r = nr
    if not math.isfinite(r) or abs(f(r)) > 1e-6:
        # bisección de respaldo
        lo, hi = -0.99, 10.0
        flo = f(lo)
        for _ in range(300):
            mid = (lo + hi) / 2; fm = f(mid)
            if (fm > 0) == (flo > 0):
                lo, flo = mid, fm
            else:
                hi = mid
        r = (lo + hi) / 2
        if abs(f(r)) > 1e-6:
            return None
    return r

def payback(cum, fcf):
    """Réplica de Motor!B58: interpolación en el último año con acumulado negativo."""
    n = len(cum)
    if cum[-1] < 0:
        return 'no cruza'
    k = max((i + 1 for i in range(n) if cum[i] < 0), default=0)  # 1-based del último negativo
    if k == 0:
        return -1
    return (k - 2) + (-cum[k - 1]) / fcf[k]  # fcf[k] es el elemento k+1 (1-based)

# ----------------------------------------------------------------------------- motor de un caso
PARAM_KEYS = ['fCAPEX','fTarifa','scen','fOPEX','peaje','escT','part','ivaRec','contrato','deuda','rDeuda','lev','plazo','gracia',
              'P','ratio','S','bank','fPrecio','fijo','disp','escCAPEX','peajeKW','rep','UG','meses','rEq','desm','degr']

def compute_case(p, pct_civil):
    T = list(range(-1, H + 1))
    esc_wp = (p['P'] / G['Potencia_Ref']) ** (1 - G['Exponente_Escala'])
    AC = p['P'] / p['ratio']
    esc_wac = (AC / (G['Potencia_Ref'] / G['Ratio_Ref'])) ** (1 - G['Exponente_Escala'])
    FR = (1 - loss_at(p['ratio'])) / (1 - Loss_Ref)
    ha = p['P'] / 1000 / G['Densidad_MWp_ha']
    tag = 'CC' if p['contrato'] == 1 else 'SC'
    bottom = esc_wp * CAP['CAPEX_' + tag][0] + esc_wac * CAP['CAPEX_' + tag][1] + CAP['CAPEX_' + tag][2]
    bottom_iva = esc_wp * CAP['IVA_' + tag][0] + esc_wac * CAP['IVA_' + tag][1] + CAP['IVA_' + tag][2]
    fEff = (p['fijo'] * p['P'] * 1000 / bottom) if p['fijo'] > 0 else p['fCAPEX']
    AP = G['Anios_Precios']
    fEsc = G['Fase_m1'] * (1 + p['escCAPEX']) ** max(0, AP - 1) + (1 - G['Fase_m1']) * (1 + p['escCAPEX']) ** max(0, AP)
    CAPEX = fEff * fEsc * bottom
    IVA = fEff * fEsc * bottom_iva
    CAPEXdep = CAPEX + (1 - p['ivaRec']) * IVA
    DepEq = CAPEXdep * (1 - pct_civil) / G['Vida_Fiscal_Equipos']
    DepCiv = CAPEXdep * pct_civil / G['Vida_Fiscal_Civil']
    DedAd = min(CAPEXdep * G['Pct_Elegible_DedAd'] / G['Vida_Fiscal_Equipos'], G['Tope_DedAd_Pct'] * G['Ingresos_SALELGI'])
    TerrCost = G['Precio_Terreno_ha'] * p['fPrecio'] * ha * (1 + G['Costos_Transaccion_Terreno_Pct'])
    resid_bruto = G['Precio_Terreno_ha'] * p['fPrecio'] * ha * G['Residual_Terreno_Pct'] * (1 + G['Apreciacion_Terreno']) ** (H + 1)
    Residual = resid_bruto - max(0, resid_bruto - TerrCost) * (G['Tasa_Efectiva'] if p['S'] == 1 else G['Tasa_Efectiva_Exergy'])
    OPEX1 = (G['Fee_OM_kWp'] + G['Seguro_kWp']) * p['P'] + (G['Predial_Terreno'] if p['S'] == 1 else G['Renta_Terreno_ha'] * ha) + G['Tributos_Locales']
    EPC = CAPEX / (1 + G['Fee_Gerencia_Pct'])
    Deuda = p['deuda'] * p['lev'] * (CAPEX + p['bank'] * p['S'] * TerrCost)
    IDC = Deuda * p['rDeuda'] * (G['Fase_m1'] + (1 - G['Fase_m1']) * G['IDC_Frac_Tramo0']) * p['meses'] / 12
    DeudaTot = Deuda + IDC
    Ncuotas = max(1, p['plazo'] - p['gracia'])
    r = p['rDeuda']
    Cuota = (DeudaTot / Ncuotas if r == 0 else DeudaTot * r / (1 - (1 + r) ** (-Ncuotas))) if DeudaTot > 0 else 0
    RepUSD = G['Reemplazo_USD_Wac'] * AC * 1000 if p['rep'] > 0 else 0
    Desm = p['desm'] * CAPEX
    RA = G['Reemplazo_Anio']; VFE = G['Vida_Fiscal_Equipos']; VFC = G['Vida_Fiscal_Civil']
    UG = p['UG']; tp = G['Tasa_Participacion']; tir_ = G['Tasa_IR']; esc_neg = (G['Escudo_Negativo'] == 'Sí')
    Y = Y_P50 if p['scen'] == 1 else Y_P90

    B = {k: [] for k in ['E','Eval','Ahorro','OPEX','Peaje','EBITDA','Dep','Part_u','IR_u','Terr','FCF_u','Cum_u','Int','Amort','Part_l','IR_l',
                          'CFADS','EQ','DSCR','DF','Ux','Ix','Tx','Fx','Gx','Krep','PoolU','PoolL']}
    poolU_prev = 0.0; poolL_prev = 0.0; cum = 0.0
    def part(base, t):
        if p['part'] != 1: return 0.0
        if UG >= 0:
            return tp * base if base >= 0 else -tp * min(-base, UG if t >= 1 else 0)
        return tp * base if esc_neg else max(0.0, tp * base)
    def ir_and_pool(base, t, pool_prev):
        if UG >= 0:
            ug = UG if t >= 1 else 0
            if base >= 0:
                ir_v = tir_ * (base - min(pool_prev, 0.25 * (base + ug)))
            else:
                ir_v = -tir_ * min(-base, ug)
            pool = pool_prev + ((-base - min(-base, ug)) if base < 0 else -min(pool_prev, 0.25 * (base + ug)))
            return ir_v, pool
        return (tir_ * base if esc_neg else max(0.0, tir_ * base)), 0.0

    for t in T:
        E = 0.0 if (t < 1 or t > H) else p['P'] / 1000 * FR * Y[max(1, t) - 1] * p['disp'] * (1 - p['degr']) ** (t - 1)
        Eval = min(E, 0 if t < 1 else Consumo_Anual * (1 + G['Crecimiento_Consumo']) ** (t - 1) / 1000)
        Ahorro = Eval * 1000 * Tarifa_Evitable_calc * p['fTarifa'] * (1 + p['escT']) ** max(0, t - 1)
        OPEX = 0.0 if (t < 1 or t > H) else OPEX1 * p['fOPEX'] * (1 + G['Escalacion_OPEX']) ** (t - 1)
        fp = frac_peaje(t)
        Peaje = E * 1000 * p['peaje'] * fp + (AC * p['peajeKW'] * 12 * fp if 1 <= t <= H else 0)
        EBITDA = Ahorro - OPEX - Peaje - (Desm if t == H else 0)
        Dep = (DepEq if 1 <= t <= VFE else 0) + (DepCiv if (1 <= t <= VFC and t <= H) else 0) + \
              (RepUSD / min(VFE, H - RA) if (p['rep'] == 1 and RA < H and t > RA and t <= min(H, RA + VFE)) else 0)
        Krep = -RepUSD if (p['rep'] == 1 and t == RA) else 0.0
        dedad = DedAd if 1 <= t <= VFE else 0
        Part_u = part(EBITDA - Dep, t)
        base_u = EBITDA - Dep - Part_u - dedad
        IR_u, poolU = ir_and_pool(base_u, t, poolU_prev)
        Terr = (( -TerrCost if t == -1 else (Residual if t == H else 0)) if p['S'] == 1 else 0)
        if t == -1:
            FCF = -(CAPEX + IVA) * G['Fase_m1']
        elif t == 0:
            FCF = -(CAPEX + IVA) * (1 - G['Fase_m1']) + p['ivaRec'] * IVA * G['Fase_m1']
        else:
            FCF = EBITDA - Part_u - IR_u + (p['ivaRec'] * IVA * (1 - G['Fase_m1']) if t == 1 else 0) + Krep
        FCF += Terr
        cum += FCF
        # deuda
        if Deuda == 0 or t < 1 or t > p['plazo']:
            Int = 0.0
        elif t <= p['gracia']:
            Int = DeudaTot * r
        else:
            Int = 0.0 if r == 0 else r * DeudaTot * (1 - ((1 + r) ** (t - p['gracia'] - 1) - 1) / ((1 + r) ** Ncuotas - 1))
        if Deuda == 0:
            Amort = 0.0
        elif p['plazo'] <= p['gracia']:
            Amort = DeudaTot if t == p['plazo'] else 0.0
        else:
            Amort = (Cuota - Int) if (p['gracia'] < t <= p['plazo']) else 0.0
        Part_l = part(EBITDA - Dep - Int, t)
        base_l = EBITDA - Dep - Int - Part_l - dedad
        IR_l, poolL = ir_and_pool(base_l, t, poolL_prev)
        CFADS = 0.0 if t < 1 else EBITDA - Part_l - IR_l + (p['ivaRec'] * IVA * (1 - G['Fase_m1']) if t == 1 else 0) + (Terr if t >= 1 else 0) + Krep
        if t == -1:
            EQ = FCF + Deuda * G['Fase_m1']
        elif t == 0:
            EQ = FCF + Deuda * (1 - G['Fase_m1'])
        else:
            EQ = CFADS - Int - Amort
        DSCR = CFADS / (Int + Amort) if (Int + Amort) > 0 else None
        DF = 0.0 if t < 1 else 1 / (1 + G['Tasa_Descuento']) ** t
        Ux = (((G['Fee_Gerencia_Pct'] - G['Costo_Gerencia_Pct']) * EPC * G['Fase_m1']) if t == -1 else
              ((G['Fee_Gerencia_Pct'] - G['Costo_Gerencia_Pct']) * EPC * (1 - G['Fase_m1'])) if t == 0 else 0.0)
        if 1 <= t <= H:
            Ux += (1 - p['S']) * (G['Renta_Terreno_ha'] * ha - G['Predial_Terreno']) * (1 + G['Escalacion_OPEX']) ** (t - 1) + \
                  (G['Fee_OM_kWp'] - G['Costo_OM_Exergy_kWp']) * p['P'] * (1 + G['Escalacion_OPEX']) ** (t - 1)
        if p['rep'] == 2 and t == RA:
            Ux -= RepUSD
        Ix = -max(0.0, Ux) * G['Tasa_Efectiva_Exergy']
        Tx = 0.0 if p['S'] == 1 else (-TerrCost if t == -1 else (Residual if t == H else 0.0))
        Fx = Ux + Ix + Tx
        Gx = FCF + Fx
        for k, v in [('E',E),('Eval',Eval),('Ahorro',Ahorro),('OPEX',OPEX),('Peaje',Peaje),('EBITDA',EBITDA),('Dep',Dep),('Part_u',Part_u),
                     ('IR_u',IR_u),('Terr',Terr),('FCF_u',FCF),('Cum_u',cum),('Int',Int),('Amort',Amort),('Part_l',Part_l),('IR_l',IR_l),
                     ('CFADS',CFADS),('EQ',EQ),('DSCR',DSCR),('DF',DF),('Ux',Ux),('Ix',Ix),('Tx',Tx),('Fx',Fx),('Gx',Gx),('Krep',Krep),
                     ('PoolU',poolU),('PoolL',poolL)]:
            B[k].append(v)
        poolU_prev, poolL_prev = poolU, poolL

    rd = G['Tasa_Descuento']
    out = {}
    out['TIR'] = irr(B['FCF_u'])
    out['VAN'] = B['FCF_u'][0] * (1 + rd) + B['FCF_u'][1] + npv(rd, B['FCF_u'][2:])
    out['PB'] = payback(B['Cum_u'], B['FCF_u'])
    ix = slice(2, 2 + H)
    out['LCOE'] = (CAPEX + sum((o + pj) * d for o, pj, d in zip(B['OPEX'][ix], B['Peaje'][ix], B['DF'][ix]))) / sum(e * d for e, d in zip(B['E'][ix], B['DF'][ix]))
    out['TIReq'] = irr(B['EQ']) if Deuda > 0 else None
    out['VANeq'] = B['EQ'][0] * (1 + p['rEq']) + B['EQ'][1] + npv(p['rEq'], B['EQ'][2:])
    ds = [d for d in B['DSCR'][ix] if d is not None]
    out['DSCRmin'] = min(ds) if (Deuda > 0 and ds) else None
    out['DSCRprom'] = sum(ds) / len(ds) if (Deuda > 0 and ds) else None
    out['Ahorro1'] = B['Ahorro'][2]
    out['Aporte'] = -(B['EQ'][0] + B['EQ'][1])
    out['VANX'] = B['Fx'][0] * (1 + rd) + B['Fx'][1] + npv(rd, B['Fx'][2:])
    out['TIRG'] = irr(B['Gx'])
    out['E1'] = B['E'][2]
    out['EnoRec'] = sum(B['E'][ix]) - sum(B['Eval'][ix])
    out['Cobertura'] = B['E'][2] * 1000 / Consumo_Anual if Consumo_Anual > 0 else 0
    out['NominalX'] = sum(B['Fx'])
    scal = dict(FR=FR, AC=AC, ha=ha, CAPEX=CAPEX, IVA=IVA, CAPEXdep=CAPEXdep, DepEq=DepEq, DepCiv=DepCiv, DedAd=DedAd, TerrCost=TerrCost,
                Residual=Residual, OPEX1=OPEX1, EPC=EPC, Deuda=Deuda, IDC=IDC, DeudaTot=DeudaTot, Ncuotas=Ncuotas, Cuota=Cuota,
                fEff=fEff, fEsc=fEsc, RepUSD=RepUSD, Desm=Desm)
    return out, B, scal

def _main():
    # ----------------------------------------------------------------------------- comparación con el Motor
    wsM = wb['Motor_Sens']
    BLOCK_ROWS = {'E':74,'Eval':102,'Ahorro':130,'OPEX':158,'Peaje':186,'EBITDA':214,'Dep':242,'Part_u':270,'IR_u':298,'Terr':326,'FCF_u':354,
                  'Cum_u':382,'Int':410,'Amort':438,'Part_l':466,'IR_l':494,'CFADS':522,'EQ':550,'DSCR':578,'DF':606,'Ux':634,'Ix':662,'Tx':690,
                  'Fx':718,'Gx':746,'Krep':774,'PoolU':802,'PoolL':830}
    OUT_ROWS = {'TIR':56,'VAN':57,'PB':58,'LCOE':59,'TIReq':60,'VANeq':61,'DSCRmin':62,'DSCRprom':63,'Ahorro1':64,'Aporte':65,'VANX':66,'TIRG':67,
                'E1':68,'EnoRec':69,'Cobertura':70,'NominalX':71}
    SCAL_ROWS = {'FR':34,'AC':35,'ha':36,'CAPEX':37,'IVA':38,'CAPEXdep':39,'DepEq':40,'DepCiv':41,'DedAd':42,'TerrCost':43,'Residual':44,'OPEX1':45,
                 'EPC':46,'Deuda':47,'IDC':48,'DeudaTot':49,'Ncuotas':50,'Cuota':51,'fEff':52,'fEsc':53,'RepUSD':54,'Desm':55}

    def cell(c, r):
        return wsM.cell(r, c).value

    # comprobaciones de globales
    checks = []
    checks.append(('Consumo_Anual', Consumo_Anual, N['Consumo_Anual']))
    checks.append(('Tarifa_Evitable', Tarifa_Evitable_calc, N['Tarifa_Evitable']))
    checks.append(('Loss_Ref', Loss_Ref, N['Loss_Ref']))
    checks.append(('Anios_Precios', G['Anios_Precios'], N['Anios_Precios']))
    checks.append(('Tasa_Efectiva', G['Tasa_Efectiva'], N['Tasa_Efectiva']))
    for i, k in enumerate(['CAPEX_SC_Wp','CAPEX_SC_Wac','CAPEX_SC_Fijo']): checks.append((k, CAP['CAPEX_SC'][i], N[k]))
    for i, k in enumerate(['CAPEX_CC_Wp','CAPEX_CC_Wac','CAPEX_CC_Fijo']): checks.append((k, CAP['CAPEX_CC'][i], N[k]))
    for i, k in enumerate(['IVA_SC_Wp','IVA_SC_Wac','IVA_SC_Fijo']): checks.append((k, CAP['IVA_SC'][i], N[k]))
    for i, k in enumerate(['IVA_CC_Wp','IVA_CC_Wac','IVA_CC_Fijo']): checks.append((k, CAP['IVA_CC'][i], N[k]))
    pcc = pct_capex_civil(N['Potencia_DC'], N['Ratio_DCAC'], N['Contrato_Inversion'] == 'Sí')
    checks.append(('Pct_CAPEX_Civil', pcc, N['Pct_CAPEX_Civil']))
    fp_x = [wb['04_Energia'].cell(99, c).value for c in range(4, 31)]
    checks.append(('Frac_Peaje[max]', max(abs(frac_peaje(t) - fp_x[t + 1]) for t in range(-1, 26)), 0))
    print('=== Globales derivados (sombra vs Excel) ===')
    worst_g = 0
    for k, a, b in checks:
        d = abs(a - b); worst_g = max(worst_g, d)
        print(f"  {k:18} sombra={a!s:22} excel={b!s:22} |Δ|={d:.3e}")

    # 110 casos
    ncols = wsM.max_column
    results = []
    worst_out = {}; worst_blk = {}; worst_scal = {}
    for c in range(2, ncols + 1):
        hdr = cell(c, 4)
        p = {k: cell(c, 5 + i) for i, k in enumerate(PARAM_KEYS)}
        out, B, scal = compute_case(p, pcc)
        row = {'col': get_column_letter(c), 'caso': hdr}
        for k, r in SCAL_ROWS.items():
            xv = cell(c, r); d = abs(scal[k] - xv) if isinstance(xv, (int, float)) else (0 if scal[k] is None else 1)
            worst_scal[k] = max(worst_scal.get(k, 0), d)
        for k, r in OUT_ROWS.items():
            xv = cell(c, r); sv = out[k]
            if isinstance(xv, (int, float)) and isinstance(sv, (int, float)):
                d = abs(sv - xv); rel = d / max(1e-12, abs(xv))
            else:
                d = 0 if (str(xv) in ('n/a', 'no cruza', None) and sv in (None, 'no cruza')) or (xv == sv) else float('inf')
                rel = d
            worst_out[k] = max(worst_out.get(k, 0), d if k in ('TIR','TIReq','TIRG','DSCRmin','DSCRprom','Cobertura','FR') else rel)
            row[k] = (sv, xv, d)
        for k, r0 in BLOCK_ROWS.items():
            for i, t in enumerate(range(-1, H + 1)):
                xv = cell(c, r0 + 1 + i); sv = B[k][i]
                if xv in (None, '') and sv is None:
                    d = 0
                elif isinstance(xv, (int, float)) and isinstance(sv, (int, float)):
                    d = abs(sv - xv) / max(1.0, abs(xv))
                else:
                    d = float('inf')
                worst_blk[k] = max(worst_blk.get(k, 0), d)
        results.append(row)

    print('\n=== Escalares (peor |Δ| absoluto sobre 110 casos) ===')
    for k, v in worst_scal.items(): print(f"  {k:10} {v:.3e}")
    print('\n=== Salidas (peor Δ sobre 110 casos; abs para tasas/ratios, rel para USD) ===')
    for k, v in worst_out.items(): print(f"  {k:10} {v:.3e}")
    print('\n=== Bloques anuales (peor Δ relativo a max(1,|x|) sobre 110 casos × 27 años) ===')
    for k, v in worst_blk.items(): print(f"  {k:8} {v:.3e}")
    print(f"\nCasos: {len(results)}  ·  peor Δ globales: {worst_g:.3e}")
    json.dump({'worst_out': worst_out, 'worst_blk': worst_blk, 'worst_scal': worst_scal, 'n_cases': len(results)}, open('shadow_report.json', 'w'), indent=1)

if __name__ == '__main__':
    _main()
