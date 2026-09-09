# -*- coding: utf-8 -*-
"""00b_Guía (v3.0 · V1, ≤ 4 páginas): el libro en cinco minutos · convenciones (dos columnas) · preguntas frecuentes (6) · glosario (30 términos, 4 grupos).
Toda cifra es fórmula (lee los nombres definidos); cada término enlaza a la celda donde vive."""
import re
from openpyxl.worksheet.pagebreak import Break
from openpyxl.styles import Font, Alignment, Border
from xl_helpers import *
from build_core import (S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, SM, NSHEETS, C, rng, FLUJO, ENERGIA, OUT_ROWS)
from build_content import mo, CASE_X, T_TAR_UP, T_TAR_DN, T_ESC, T_UG, T_REP, T_DEDAD, BR0, BR5, N_CASES

SG = "00b_Guía"
W_B, W_C, W_D, W_E, W_F = 23, 40, 20, 54, 6   # 143 + A(2) = 145 caracteres × 6,05 pt (factor Excel/Mac) = 877 pt → 87 % = 763 pt < 772 útiles (784 − 1,5 %)


def fx(s):
    """Convierte «texto {expresión} texto» en una fórmula Excel; los literales se parten en trozos ≤ 200 caracteres."""
    if s is None or "{" not in s:
        return s
    parts = re.split(r"(\{[^{}]*\})", s)
    out = []
    for p in parts:
        if not p:
            continue
        if p.startswith("{") and p.endswith("}"):
            out.append(p[1:-1])
        else:
            lit = p.replace('"', '""')
            for i in range(0, len(lit), 200):
                out.append('"' + lit[i:i + 200] + '"')
    return "=" + "&".join(out)


def plain(s):
    """Texto aproximado que se verá en pantalla (para estimar la altura de fila): cada {expresión} ≈ 8 caracteres; los chips de estado (Estado_*) ≈ 45."""
    return re.sub(r"\{[^{}]*\}", lambda m: "#" * (45 if "Estado_" in m.group(0) else 8), s or "")


def pct(nm, d=1):
    return f'{{TEXT({nm},"0.{"0" * d}%")}}' if d else f'{{TEXT({nm},"0%")}}'


def usd(nm):
    return f'{{TEXT({nm},"#,##0")}}'


def num(nm, f="#,##0"):
    return f'{{TEXT({nm},"{f}")}}'


# ------------------------------------------------------------------ contenido (v3.0 · V1: ≤ 4 páginas)
PASOS = [
    ("1 · Qué calcula", "La planta de Montecristi (SGDA remoto, 005/24) abastece la cuenta de GPM: SALELGI es dueña y paga CAPEX, OPEX, peaje e impuestos incrementales; Exergy gerencia, opera y arrienda el terreno. Cadena: 04 energía → 05 CAPEX → 06 OPEX → 07 fiscal → 08 flujo sin y con deuda → 09 Exergy; el Motor repite esa lógica para " + str(N_CASES) + " casos.", S4),
    ("2 · Lee la portada", f"Las tarjetas muestran el caso Custom (gobierna todo el libro) y, bajo cada una, la tira C · B · F (Conservador · Base · Favorable). La TIR del proyecto se compara con la tasa exigida {pct('Tasa_Descuento', 0)}. La fila de estados: ● controles {{N_Controles_OK}}/{{N_Controles}} · {{Estado_Custom}} · ▲ {{N_Por_Confirmar}} por confirmar.", S0),
    ("3 · Edita sólo tinta (01)", "El bloque B define los cuatro casos (energía, CAPEX, OPEX, peaje, escalación de tarifa, disponibilidad, escalación del CAPEX): la columna Custom es la suya; C · B · F son fijos (G4 avisa si los toca). Lo demás es capa de diseño compartida. «Sensibilizado en» enlaza a la sección de 10 que barre cada parámetro; el panel de mandos resume los maestros.", S1),
    ("4 · Decide con 10", "§A los cuatro casos · §A.3 puente v2.0 → v3.0 (por qué cambió el Base) · §B tornado de 15 palancas · §C matriz CAPEX × tarifa · §D/§H deuda y deuda máxima · §E piso · §F potencia y ratio · §G terreno y reemplazo. ◆ o borde ciruela = Custom.", S10),
    ("5 · Verifica antes de compartir", f"13 en ● {{N_Controles_OK}}/{{N_Controles}} (A–F identidades y candados · G casos · H ronda 2 · I libro); {{Estado_Neutro}}; supuestos por confirmar y fuentes en 12. Cada hoja imprime en su área definida; las series anuales a tres páginas de años con títulos repetidos.", S13),
]

# dos columnas de (elemento, significado corto)
CONVENCIONES = [
    ("texto en tinta", "entrada editable (01; pasos de 10, drivers de 05, cronograma de 03, 11)", TINTA, False),
    ("● ok · ▲ atención · ■ riesgo · ◇ informativo", "estados de controles y candados; ◇ = neutro / informativo", SALVIA, True),
    ("carbón · grafito · piedra", "texto calculado · notas, unidades, enlaces y canónicos · meta y auxiliares", CARBON, False),
    ("«· por confirmar» (subrayado punteado)", "supuesto sin fuente firme; lista viva en 12 §A", ARCILLA, True),
    ("terracota", "el dato que decide, la serie principal, el umbral, los hipervínculos", TERRACOTA, True),
    ("arcilla en 01", "Custom distinto del Base, o C/B/F distintos de la definición entregada", ARCILLA, False),
    ("ciruela · Custom", "caso de trabajo: cabeceras, serie, ◆ y borde en 10, tira de la portada", X_COL, True),
    ("fila bruma", "cabecera de sección con su frase de guía", GRAFITO, False),
    ("índigo · Conservador", "P90 · CAPEX y OPEX × 1,15 · peaje 1,5 ¢ · disp. 97 % · precios +5 %/año", C_COL, True),
    ("+/− en columnas", "años 11–25 agrupados en las series anuales; nada congelado", GRAFITO, False),
    ("petróleo · Base", "P50 · costo real · peaje 0,5 ¢ · plana · disp. 98 % · precios +3 %/año", B_COL, True),
    ("ladrillo / arcilla en cifras", "bajo el umbral: TIR < tasa, VAN < 0, DSCR < 1,00x / < objetivo", LADRILLO, False),
    ("verde bosque · Favorable", "P50 · fijo 0,75 $/Wp · sin peaje · +2 %/año · disp. 99 % · precios fijos", F_COL, True),
    ("toda cifra en texto es fórmula", "cambia con 01; ningún número escrito a mano en las hojas", GRAFITO, False),
]

_REP_DELTA = 'ABS(X_VANX-' + mo(T_REP, 'VAN_X') + ')'
_TAR_PP = "ABS(" + mo(T_TAR_UP, 'TIR') + "-" + mo(T_TAR_DN, 'TIR') + ")/2*100"

# glosario: (término ≤ 29 caracteres, qué es y dónde vive ≤ 84, cómo leerlo con la cifra viva ≤ 73 en pantalla, destino) → una línea por término
G_CASOS = [
    ("Custom", "Caso de trabajo (columna Custom de 01); gobierna 04–09, la portada y el Motor.", f"Nace igual al Base; hoy {{Estado_Custom}}.", "#Estado_Custom"),
    ("Conservador · Base · Favorable", "Escenarios fijos del bloque B (cols. D/E/F de 01); mismo diseño que el Custom.", f"TIR {pct('C_TIR')} · {pct('B_TIR')} · {pct('F_TIR')}; definición vigilada por G4.", "#B_TIR"),
    ("Bloque B · capa de diseño", "8 filas que distinguen a los casos; el resto de 01 es común a los cuatro.", "Custom mueve el libro; C/B/F mueven la referencia (candado G4).", "#Esc_Energia"),
    ("Neutro (ronda 2)", "Los 9 parámetros nuevos en los valores con que el libro reproduce la v2.0.", f"Hoy {{Estado_Neutro}}.", "#Estado_Neutro"),
    ("Puente v2.0 → v3.0", "BR0–BR5 del Motor: del Base en neutro al Base actual, un parámetro por escalón.", "Explica cada décima del cambio de Base; control H7.", f"#'{S10}'!B5"),
    ("Por confirmar", "Supuesto sin fuente firme (arcilla, punteado); lista en 12 §A; control I2.", f"{{N_Por_Confirmar}} hoy: alimentador, peaje, utilidad gravable, drivers, reemplazo.", "#N_Por_Confirmar"),
    ("Controles (13)", "Identidades y candados con dos caminos de cálculo (tol. 1 USD o 10⁻⁶); A–I.", f"{{N_Controles_OK}}/{{N_Controles}} en ●; un ■ es inconsistencia o entrada fuera de rango.", "#Estado_Controles"),
    ("Motor_Sens", str(N_CASES) + " casos, uno por columna, con la lógica de 04–09; alimenta 05, 08–10, 13 y 00.", "No editar; su columna B ≡ 08/09 (A8, D12, D13, E6, H1–H5).", f"#'{SM}'!A1"),
]
G_ENERGIA = [
    ("Potencia DC / AC · ratio", "Potencia_DC (lista 5–8 MWp); AC = DC / Ratio_DCAC, la que ve la red (art. 7.a).", f"{num('Potencia_DC')} kWp · {num('Potencia_AC')} kWac vs {num('Capacidad_Alimentador_kW')} kW aprobables (por confirmar).", "#Potencia_DC"),
    ("Yield · P50 / P90", "Energía anual por kWp (pvlib jul-2026); P90 = 90 % de probabilidad de superarse.", f"{num('Yield_Ref')} kWh/kWp año 1; P90 {pct('P90_Ahorro1/P50_Ahorro1-1')} bajo P50.", "#Y_P50"),
    ("Factor de recorte", "Pérdida por exceso de DC frente al inversor (curva pvlib relativa al ratio 1,32).", f"F = {num('F_Recorte', '0.0000')} con el ratio activo (10 §F.2).", "#F_Recorte"),
    ("Disponibilidad · degradación", "Fracción del año en producción (bloque B) y pérdida anual extra al canónico.", f"Custom {pct('Disponibilidad', 0)} · adicional {pct('Degradacion_Adicional', 1)}/año; garantía O&M por confirmar.", "#Disponibilidad"),
    ("Energía valorizable (art. 9)", "Genera ahorro: MIN(producción, demanda anual del medidor); el exceso no cuenta.", f"Cobertura {pct('Cobertura_Anual', 0)}; el exceso aparece desde ≈ {num('Consumo_Anual/Yield_Ref/F_Recorte/1000', '0.0')} MWp (10 §F.1).", "#E_Val"),
    ("Tarifa evitable", "Lo que GPM deja de pagar por kWh: cargos A/B y C ponderados por inyección (04).", f"{num('Tarifa_Evitable', '0.0000')} $/kWh; ±{pct('Sens_Tarifa', 0)} mueve la TIR ≈ {num(_TAR_PP, '0.0')} pp.", "#Tarifa_Evitable"),
    ("Peaje SGDA (kWh y kW)", "Uso de red desde feb-2029: $/kWh inyectado (bloque B) + $/kW-mes sobre la AC.", f"Custom {num('Peaje_SGDA*100', '0.0')} ¢/kWh + {num('Peaje_kW_mes', '0.00')} $/kW-mes; tornado {num('Sens_Peaje*100', '0.0')} ¢ y {num('Sens_Peaje_kW', '0.0')}.", "#Peaje_SGDA"),
]
G_COSTOS = [
    ("CAPEX · factor o fijo $/Wp", "Rubros 1–9 + contingencia + fee (05) × Factor_CAPEX, o CAPEX_Fijo_Wp × kWp.", f"{usd('CAPEX_Total')} USD = {num('CAPEX_Total/(Potencia_DC*1000)', '0.000')} $/Wp; Favorable fijo {num('INDEX(Esc_CAPEX_Fijo_Wp,4)', '0.00')} $/Wp.", "#CAPEX_Total"),
    ("Escalación del CAPEX", "Alza anual de precios desde Fecha_Precios hasta la compra (bloque B; factor 05).", f"Custom {pct('Escalacion_CAPEX', 0)}/año → factor {num('Factor_Escalacion', '0.000')} sobre precios de {{TEXT(Fecha_Precios,\"mmm-yyyy\")}}.", "#Factor_Escalacion"),
    ("Drivers de escala", "Parte de cada rubro que sigue a la DC, a la AC o es fija (05; por confirmar).", f"Costo = base × [%Wp·Escala_Wp + %Wac·Escala_Wac + %fijo]; ε = {num('Exponente_Escala', '0.00')}.", "#Drv_Wp"),
    ("Reemplazo · desmantelamiento", "Inversores en Reemplazo_Anio (SALELGI, Exergy o nadie); cierre en t = H.", f"{usd('Reemplazo_USD')} USD en t = {{Reemplazo_Anio}}, paga {{Reemplazo_Pagador}}; cierre {pct('Desmantelamiento_Pct', 0)} (10 §G.2).", "#Reemplazo_USD"),
    ("OPEX de SALELGI", "Fee de O&M, seguros, arriendo o predial y tributos; escalan por Escalacion_OPEX.", f"{usd('OPEX_Anio1')} USD en el año 1 (≈ {num('OPEX_Anio1/Potencia_DC', '0.0')} $/kWp).", "#OPEX_Anio1"),
    ("Impuestos incrementales", "Participación 15 % + IR 25 % sobre el ahorro, con deducción adicional (07).", f"Tasa efectiva {pct('Tasa_Efectiva', 2)}; deducción adicional {usd('DedAd_Anual')} USD/año (10.7).", "#Imp_U_Row"),
    ("Utilidad gravable · pool", "Pérdidas: absorción ilimitada (vacío) o topada, arrastre ≤ 25 %/año (art. 11).", "Vacío = v2.0; 0 = sólo arrastre (tornado); pool sin caducidad (12 §B).", "#Utilidad_Gravable_SALELGI"),
]
G_FLUJO = [
    ("FCF · TIR · VAN (t = 0 = COD)", "Flujo libre sin deuda (08 §A); VAN al COD: FCF₋₁(1+r) + FCF₀ + NPV(r, FCF₁…₂₅).", f"Custom TIR {pct('X_TIR')} vs tasa {pct('Tasa_Descuento', 0)}; VAN {usd('X_VAN')} USD.", "#TIR_Proyecto"),
    ("Payback (último cruce)", "Años hasta que el acumulado queda positivo, interpolado en el último cruce.", f"Custom {num('X_PB', '0.0')} años; «no cruza» si nunca llega a 0 (H6).", "#Payback_Simple"),
    ("LCOE", "(CAPEX + VP(OPEX + peaje)) ÷ VP(energía), sin impuestos (08).", f"{num('LCOE', '0.0')} vs {num('Tarifa_MWh', '0.0')} $/MWh de la red → ahorro {pct('Ahorro_kWh', 0)} por kWh.", "#LCOE"),
    ("Deuda · IDC · construcción", "Préstamo corporativo (% del CAPEX), cuota francesa tras gracia; IDC × meses/12.", f"{pct('Pct_Apalancamiento', 0)} a {pct('Tasa_Deuda')}, {{Plazo_Deuda}} años; IDC {usd('IDC')} USD ({{Meses_Construccion}} meses).", "#Deuda_Monto"),
    ("CFADS · DSCR", "EBITDA − impuestos + IVA recuperado + residual − reemplazo, ÷ servicio (08 §B).", f"Mínimo {num('DSCR_Min', '0.00')}x en t = {{Anio_DSCR_Min}}; bancos piden ≥ {num('DSCR_Objetivo', '0.00')}x (10 §H).", "#DSCR_Min"),
    ("TIR y VAN del accionista", "FCF + desembolsos (t ≤ 0), CFADS − servicio (t ≥ 1); VAN a tasa del accionista. «n/a»: sin deuda o sin solución (TIR ≤ −100 %).", f"TIR {pct('X_TIReq')} vs proyecto {pct('X_TIR')}; VAN {usd('X_VANeq')} USD; léala con el DSCR.", "#TIR_Equity"),
    ("Negocio Exergy · carga", "Fee de gerencia − costo, margen O&M, terreno; impuestos 36,25 % si hay utilidad.", f"VAN {usd('VAN_Exergy')} USD; carga {pct('Carga_Exergy', 0)} del ahorro del cliente.", "#VAN_Exergy"),
    ("Grupo consolidado", "SALELGI sin deuda + Exergy; los pagos intragrupo se netean (09 memo).", f"TIR del grupo {pct('TIR_Grupo')}.", "#TIR_Grupo"),
    ("Tornado · matrices · piso", "Una palanca a la vez (15 barras) · CAPEX × tarifa · tasa × plazo · piso (10).", f"Piso = P90 + CAPEX +{pct('Sens_CAPEX', 0)} + OPEX +{pct('Sens_OPEX_Up', 0)} + peaje + IVA no recup.", f"#'{S10}'!B5"),
]
# v3.1 (doc 18 L-79): marco legal y permisos
G_LEGAL = [
    ("Registro Ambiental (ARCONEL)", "Permiso ambiental de FV > 1 ≤ 10 MW ante ARCONEL — Unidad Técnica Ambiental, vía SUIA (03 RC-04).", "Base: meses 3–8, USD 180 + expediente; la Licencia (> 10 MW) es contingencia (+3 meses).", f"#'{S3}'!B5"),
    ("Certificado de Habilitación", "Título del SGDA que emite CNEL EP (005/24 art. 14) tras la Factibilidad de Conexión (vigencia 6 meses).", "RC-09 meses 7–8 → RC-10 mes 12: control F12 vigila los 6 meses.", "#Fin_RC10"),
    ("Certificación ambiental (deducción)", "Requisito previo a la deducción adicional del art. 10.7 LRTI (RLRTI 28.6.g); procedimiento no publicado.", f"Aplica_DedAd = {{Aplica_DedAd}}; sin ella TIR {pct(mo(T_DEDAD, 'TIR'))} vs {pct('X_TIR')} (tornado 15).", "#Aplica_DedAd"),
    ("D.E. 32 · DT 14.ª", "Obligación de autogenerar de los clientes AV1/AV2 en 18 meses desde el 18-jun-2025 → 18-dic-2026.", "GPM es AV1: el proyecto se acredita como «en curso» en los reportes mensuales (02, 11).", f"#'{S2}'!B5"),
    ("Tm · FGD", "Tm = mayor cargo horario que valora el remanente (27.3); FGD = factor de gestión de demanda del cargo por potencia.", "Remoto (2a): la demanda de GPM no cambia → el FGD no aplica; sin excedentes mensuales.", f"#'{S2}'!B5"),
    ("Pendientes P-xx del Atlas", "Zonas grises legales numeradas por el Atlas Regulatorio v2.0 (P-01…P-14); no son entradas del modelo.", "Se listan en 02 (zonas grises) y 12 §A; las tres que mueven la tesis: P-01, P-06, P-08.", f"#'{S12}'!B5"),
    ("Ley 2026 · litigio", "Ley de Sectores Estratégicos (02-mar-2026): vigente-no-operativa; 14 demandas, 1 admitida.", "El encaje SALELGI–Exergy no depende de ella (005/24 + LOCE 2024).", f"#'{S2}'!B5"),
]
GRUPOS = [("A · Casos, estados y control", G_CASOS), ("B · Energía y tarifa", G_ENERGIA), ("C · Costos y fiscal", G_COSTOS), ("D · Flujo, deuda e indicadores", G_FLUJO), ("E · Marco legal y permisos (v3.1)", G_LEGAL)]

FAQ = [
    ("¿Por qué bajó el Base respecto a la v2.0?",
     f"Porque la ronda 2 modela lo que antes quedaba fuera del motor: precios del CAPEX escalados hasta la compra, disponibilidad, reemplazo de inversores y la duración real de la construcción. El puente de 10 §A.3 lo muestra escalón a escalón: TIR {pct(mo(BR0, 'TIR'), 2)} (definición v2.0) → {pct(mo(BR5, 'TIR'), 2)} (Base actual); accionista {pct(mo(BR0, 'TIR_eq'), 2)} → {pct(mo(BR5, 'TIR_eq'), 2)}. Con los 9 parámetros nuevos en neutro el libro reproduce la v2.0 celda a celda ({{Estado_Neutro}})."),
    (f"¿Por qué la TIR del accionista ({pct('X_TIReq')}) supera la del proyecto ({pct('X_TIR')}) si el DSCR mínimo es {num('DSCR_Min', '0.00')}x?",
     f"Porque la deuda cuesta {pct('Tasa_Deuda')}, menos que la TIR del proyecto (apalancamiento positivo). El DSCR < 1 es un problema de liquidez, no de rentabilidad: en t = {{Anio_DSCR_Min}} el CFADS no cubre la cuota y el accionista pone la diferencia; un banco no financia {pct('Pct_Apalancamiento', 0)} a {{Plazo_Deuda}} años — 10 §H da la deuda máxima ({pct('Deuda_Max_Plazo2', 0)} a {{INDEX(Sens_Plazos,2)}} años)."),
    ("¿Qué es el Custom, cómo lo comparo con Conservador · Base · Favorable y cómo vuelvo al Base?",
     f"El Custom es el caso de trabajo; los otros tres son referencias fijas calculadas siempre en el Motor con las ocho palancas del bloque B y el mismo diseño. Se comparan en la portada (tira C · B · F, gráfico, página 3), 10 §A y 05. Hoy {{Estado_Custom}}; en 01 las celdas del Custom distintas del Base están en arcilla: en el bloque B copie la columna Base, en la capa de diseño vuelva al valor entregado (comentario de la celda)."),
    ("¿Qué pasa si SALELGI no tiene utilidad gravable suficiente?",
     f"Las pérdidas incrementales de los primeros años (depreciación + deducción adicional) dejan de generar ahorro fiscal inmediato: con Utilidad_Gravable_SALELGI = 0 sólo se recuperan por arrastre (art. 11 LRTI, ≤ 25 %/año) y la TIR del accionista cae {num('ABS(' + mo(T_UG, 'TIR_eq') + '-X_TIReq)*100', '0.0')} pp (tornado «sin absorción fiscal»). Es el dato P3, por confirmar con la contabilidad de SALELGI."),
    (f"¿Por qué el LCOE ({num('LCOE', '0.0')} $/MWh) se compara con {num('Tarifa_MWh', '0.0')} $/MWh y no con la tarifa del pliego ({num('Tarifa_A*1000', '0')})?",
     "Porque no toda la inyección cae en el bloque A: la tarifa evitable pondera los cargos A/B y C por la inyección horaria. El LCOE excluye impuestos: la TIR del proyecto no es simplemente «tarifa − LCOE». El ahorro tampoco incluye demanda, comercialización ni alumbrado (art. 27.2, SGDA remoto)."),
    ("¿Qué pasa si SALELGI no obtiene la certificación ambiental para la deducción adicional?",
     f"La deducción adicional del 100 % (art. 10.7 LRTI, topada al 5 % de los ingresos) exige una certificación de la Autoridad Ambiental Competente antes de la primera declaración que la use (RLRTI 28.6.g); el procedimiento no está publicado (Atlas P-01). Sin ella, el escudo de {usd('MIN(CAPEX_Depreciable*Pct_Elegible_DedAd/Vida_Fiscal_Equipos,Tope_DedAd_Pct*Ingresos_SALELGI)*Tasa_IR')} USD/año desaparece y la TIR del proyecto pasa de {pct('X_TIR')} a {pct(mo(T_DEDAD, 'TIR'))} (tornado 15, 10 §B). Aplica_DedAd en 01 conmuta el libro entero; hoy {{Aplica_DedAd}}."),
    ("¿Quién debería pagar el reemplazo de inversores?",
     f"Es una cláusula del contrato de O&M, no un supuesto técnico: si paga SALELGI es capex depreciable en t = {{Reemplazo_Anio}} ({usd('Reemplazo_USD')} USD); si paga Exergy sale de la reserva incluida en el fee de O&M y el VAN de Exergy baja ≈ {usd(_REP_DELTA)} USD. 10 §G.2 muestra las dos caras; hoy paga {{Reemplazo_Pagador}}."),
]


def _row_text(ws, r, c, text, size=SZ_TABLE, color=CARBON, bold=False, c2=None, valign="top", border=True, wrap=True):
    cell = ws.cell(row=r, column=c, value=fx(text))
    cell.font = Font(name=FONT, size=size, color=color, bold=bold)
    cell.alignment = Alignment(wrap_text=wrap, vertical=valign)
    if border:
        cell.border = B_BOTTOM
    if c2 and c2 > c:
        ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c2)
    return cell


def build_guia(wb):
    ws = wb.create_sheet(SG)
    widths(ws, {"A": 2, "B": W_B, "C": W_C, "D": W_D, "E": W_E, "F": W_F})
    _NUM = {6: "seis", 7: "siete", 8: "ocho", 9: "nueve"}
    _n_faq, _n_glos = len(FAQ), sum(len(items) for _, items in GRUPOS)
    sheet_header(ws, "Guía de lectura", f"El libro en cinco minutos, convenciones de color, {_NUM.get(_n_faq, str(_n_faq))} preguntas frecuentes y un glosario de {_n_glos} términos con su cifra viva (fórmulas que cambian con 01_Supuestos); cada término enlaza (→) a su celda.", "0b", last_col=6, total=NSHEETS, guide=False)
    r = 5
    groups = []          # (fila inicial, nº de filas que deben quedar juntas) para la paginación
    forced = []          # filas que abren página
    # ---- 1 · el libro en cinco minutos
    section(ws, r, 2, 6, "1 · El libro en cinco minutos", guide="qué calcula, cómo se lee, dónde se edita, dónde se decide y cómo se verifica", guide_col=4)
    r += 1
    for titulo, texto, sheet in PASOS:
        _row_text(ws, r, 2, titulo, size=SZ_BODY, bold=True)
        _row_text(ws, r, 3, texto, size=SZ_TABLE, c2=5)
        link_cell(ws, r, 6, "→", f"#'{sheet}'!A1", size=SZ_BODY, align="center", valign="top")
        ws.cell(row=r, column=6).border = B_BOTTOM
        fit_row(ws, r, [(plain(texto), W_C + W_D + W_E - 2, 9)], min_h=20, pad=7)
        r += 1
    ws.row_dimensions[r].height = 12
    r += 1
    # ---- 2 · convenciones (dos columnas: elemento + significado | elemento + significado)
    section(ws, r, 2, 6, "2 · Convenciones", guide="el color sólo aparece con significado; todo lo demás es escala de grises", guide_col=4)
    r += 1
    pairs = [CONVENCIONES[i:i + 2] for i in range(0, len(CONVENCIONES), 2)]
    for pair in pairs:
        specs = []
        for j, (elem, signif, colr, bold) in enumerate(pair):
            ce, cs = (2, 3) if j == 0 else (4, 5)
            c = ws.cell(row=r, column=ce, value=elem)
            c.font = Font(name=FONT, size=SZ_TABLE, color=colr, bold=bold)
            c.alignment = Alignment(vertical="top", wrap_text=True)
            c.border = B_BOTTOM
            _row_text(ws, r, cs, signif, size=SZ_TABLE, c2=(6 if cs == 5 else None))
            specs += [(elem, (W_B if ce == 2 else W_D) - 1, 9), (signif, (W_C if cs == 3 else W_E + W_F) - 1, 9)]
        fit_row(ws, r, specs, min_h=16, pad=5)
        r += 1
    ws.row_dimensions[r].height = 12
    r += 1
    # ---- 3 · preguntas frecuentes (abren la página 2; se leen de corrido)
    forced.append(r)
    section(ws, r, 2, 6, "3 · Preguntas frecuentes", guide=f"{len(FAQ)} preguntas · cada respuesta señala la hoja donde se ve el dato", guide_col=4)
    r += 1
    for q, a in FAQ:
        groups.append((r, 2))
        _row_text(ws, r, 2, q, size=SZ_BODY, bold=True, c2=6, border=False, valign="bottom")
        fit_row(ws, r, [(plain(q), W_B + W_C + W_D + W_E + W_F - 2, 10)], min_h=20, pad=7)
        r += 1
        _row_text(ws, r, 2, a, size=SZ_TABLE, c2=6, color=CARBON)
        fit_row(ws, r, [(plain(a), W_B + W_C + W_D + W_E + W_F - 2, 9)], min_h=18, pad=6)
        r += 1
    ws.row_dimensions[r].height = 12
    r += 1
    # ---- 4 · glosario (tres columnas: término · qué es y dónde vive · cómo leerlo con la cifra viva · →)
    groups.append((r, 5))
    section(ws, r, 2, 6, "4 · Glosario", guide=f"{sum(len(i) for _, i in GRUPOS)} términos en {len(GRUPOS)} grupos · cada fila enlaza (→) a la celda donde se calcula", guide_col=4)
    r += 1
    for gname, items in GRUPOS:
        ws.row_dimensions[r].height = 8
        r += 1
        groups.append((r, 2 + len(items) if len(items) <= 10 else 4))
        c = ws.cell(row=r, column=2, value=gname); c.font = Font(name=FONT, size=SZ_BODY, bold=True, color=CARBON); c.alignment = Alignment(vertical="bottom")
        ws.row_dimensions[r].height = 20
        r += 1
        hdr(ws, r, 2, 6, ["Término", "Qué es y dónde vive", None, "Cómo leerlo (cifra viva)", "→"], height=16, align="left")
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=4)
        r += 1
        for term, que, leer, target in items:
            _row_text(ws, r, 2, term, size=SZ_TABLE, bold=True)
            _row_text(ws, r, 3, que, size=SZ_TABLE, c2=4)
            _row_text(ws, r, 5, leer, size=SZ_TABLE, color=CARBON)
            link_cell(ws, r, 6, "→", target, size=SZ_BODY, align="center", valign="top")
            ws.cell(row=r, column=6).border = B_BOTTOM
            fit_row(ws, r, [(plain(term), W_B - 1, 9), (plain(que), W_C + W_D - 1, 9), (plain(leer), W_E - 1, 9)], min_h=16, pad=5)
            r += 1
    r += 1
    note(ws, r, 2, '="Guía elaborada con el libro "&Version&" ("&TEXT(Fecha_Analisis,"dd-mmm-yyyy")&"). Documento de trabajo interno de Exergy EXG S.A.S.; no constituye oferta ni opinión legal."', c2=6)
    last = r
    # paginación: escala fija 87 % (145 caracteres × 6,05 × 0,87 = 763 pt < 772 pt útiles, factor Excel/Mac) para que Excel respete los saltos manuales;
    # los saltos evitan grupos huérfanos (pregunta sin respuesta, grupo del glosario sin sus primeras filas)
    def h(rr):
        v = ws.row_dimensions[rr].height
        return v if v is not None else 15
    PAGE = (8.27 - 0.5 - 0.6) * 72 / 0.87 - sum(h(x) for x in (1, 2, 3)) - 6
    keep = {a: k for a, k in groups}
    used = 0.0
    breaks = []
    for rr in range(4, last + 1):
        if rr in forced and used > 0:
            breaks.append(rr); used = 0.0
        if rr in keep:
            need = sum(h(x) for x in range(rr, rr + keep[rr]))
            if used + need > PAGE and used > 0:
                breaks.append(rr); used = 0.0
        if used + h(rr) > PAGE and used > 0:
            breaks.append(rr); used = 0.0
        used += h(rr)
    for b in breaks:
        ws.row_breaks.append(Break(id=b - 1))
    ws.sheet_properties.tabColor = CARBON
    setup_print(ws, landscape=True, title_rows="1:3", scale=87)
    return ws
