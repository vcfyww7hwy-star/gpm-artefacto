# -*- coding: utf-8 -*-
"""01_Supuestos v3.0: panel de mandos (sólo lectura) + bloques A–I con guía.
Columnas: Parámetro · Custom · Conservador · Base · Favorable · Unidad · Sensibilizado en (enlace) · Fuente / nota corta;
columnas ocultas: J referencia «Base» del Custom (valor entregado; en el bloque B = la columna Base), K/L/M definición entregada
de Conservador/Base/Favorable (sólo bloque B), N nombre técnico, O marcador (1 entrada · 2 por confirmar).
Capas (doc 11 §1.4): A diseño compartido por los cuatro casos (una sola columna de valor) · B supuestos de escenario (cuatro
columnas) · C–I estructurales (una sola columna). Custom nace igual al Base; Estado_Custom y Estado_Entregado vigilan las dos capas."""
from openpyxl.styles import Font, Alignment, Border
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.worksheet.hyperlink import Hyperlink
from xl_helpers import *
from build_core import (S1, S5, S8, S9, S10, S12, NSHEETS, INPUTS, INFO_INPUTS, SELECTORS, YESNO, VERSION, ESCENARIOS, CASE_KEYS, FLUJO, EXERGY)
import build_content as BC

# ------------------------------------------------------------------ bloques v2.0 (orden y guía)
ESC_NAMES = [e[0] for e in ESCENARIOS]
BLOQUES = [
    ("A · Mandos y marco general", "los maestros del diseño (compartidos por los cuatro casos) y el marco temporal",
     ["Potencia_DC", "Ratio_DCAC", "Comprador_Terreno", "Usar_Deuda", "Tasa_Descuento", "Tasa_Descuento_Equity", "Tasa_Desc_Alt1", "Tasa_Desc_Alt2", "Horizonte", "Fecha_COD", "Meses_Construccion", "Fecha_Analisis", "Version"]),
    ("B · Supuestos de escenario", "lo único que distingue a los cuatro casos; el Custom gobierna 04–09 y la portada, los otros tres se calculan siempre en el Motor",
     ESC_NAMES),
    ("C · Energía, red y tarifa", "qué produce la planta, cuánto cabe en la red y a qué precio lo evita GPM · un solo valor, compartido por los cuatro casos",
     ["Potencia_AC", "Potencia_Ref", "Ratio_Ref", "Yield_Ref", "Densidad_MWp_ha", "Hectareas", "Ha_Disponibles", "Capacidad_Alimentador_kW", "Tope_SGDA_kW",
      "Degradacion_Adicional", "Frac_A", "Frac_B", "Frac_C", "Tarifa_A", "Tarifa_C", "Cargo_Demanda", "Cargo_Comercializacion", "SAPG_mes", "Crecimiento_Consumo", "Fecha_Peaje", "Peaje_kW_mes"]),
    ("D · CAPEX y terreno", "costo real bottom-up (05), nacionalización e IVA; el terreno, según quién lo compre · compartido por los cuatro casos",
     ["Fase_m1", "Fecha_Precios", "Contingencia_Pct", "Contingencia_Frac_IVA", "Fee_Gerencia_Pct", "Asignacion_Compartida",
      "Exponente_Escala", "Contrato_Inversion", "IVA_Recuperable", "Tasa_IVA", "FODINFA_Pct", "ISD_Pct",
      "Reemplazo_Anio", "Reemplazo_USD_Wac", "Reemplazo_Pagador", "Desmantelamiento_Pct",
      "Precio_Terreno_ha", "Costos_Transaccion_Terreno_Pct", "Predial_Terreno", "Residual_Terreno_Pct", "Apreciacion_Terreno"]),
    ("E · OPEX de SALELGI", "costo anual del dueño; todas las líneas escalan con Escalacion_OPEX · compartido por los cuatro casos",
     ["Fee_OM_kWp", "Seguro_kWp", "Renta_Terreno_ha", "Tributos_Locales", "Escalacion_OPEX"]),
    ("F · Deuda", "SALELGI como deudor corporativo; el flujo con y sin deuda se calcula siempre · compartido por los cuatro casos",
     ["Pct_Apalancamiento", "Tasa_Deuda", "Plazo_Deuda", "Gracia_Deuda", "IDC_Frac_Tramo0", "DSCR_Objetivo", "Deuda_Financia_Terreno"]),
    ("G · Fiscal", "tasas legales de SALELGI; rara vez se tocan · compartido por los cuatro casos",
     ["Tasa_IR", "Tasa_Participacion", "Incluir_Participacion", "Escudo_Negativo", "Utilidad_Gravable_SALELGI", "Vida_Fiscal_Equipos", "Vida_Fiscal_Civil", "Aplica_DedAd", "Pct_Elegible_DedAd",
      "Ingresos_SALELGI", "Tope_DedAd_Pct", "Meses_Recup_IVA"]),
    ("H · Negocio Exergy", "costos propios de gerencia y O&M y tasa de impuestos de Exergy · compartido por los cuatro casos",
     ["Costo_Gerencia_Pct", "Costo_OM_Exergy_kWp", "Tasa_Efectiva_Exergy"]),
    ("I · Umbrales y tolerancias", "parámetros de los controles y del cronograma (avanzado)",
     ["Umbral_Riesgo_Alto", "Umbral_Riesgo_Medio", "Tol_Costo_Tramites", "Tol_Dias_COD"]),
]

# nota corta visible (≤ 60 caracteres); la nota completa de INPUTS va al comentario de la celda
SHORT = {
    "Version": "Se muestra en cabeceras y pies",
    "Fecha_Analisis": "Corte 08-sep-2026 · Atlas Regulatorio v2.0 (08-sep-2026)",
    "Tasa_Descuento_Equity": "12 % · sólo el VAN del accionista",
    "Meses_Construccion": "toma Mes_COD_Cron de 03 · IDC × meses/12",
    "Fecha_Precios": "precios del deck v4 (22-jul-2026)",
    "Reemplazo_Anio": "vida útil inversores 10–15 a · rango 5–24",
    "Reemplazo_USD_Wac": "≈ 6 % del CAPEX · cotización pendiente",
    "Reemplazo_Pagador": "SALELGI · alt. Exergy (fee) · No",
    "Desmantelamiento_Pct": "0 % en Base · 2 % en tornado",
    "Degradacion_Adicional": "v3.1: 1 %/año (Jorge 04-sep) · canónico ≈ 0,55 %",
    "Peaje_kW_mes": "art. 5.17 005/24 · no publicado · 0,5 / 1,0 en tornado",
    "Utilidad_Gravable_SALELGI": "vacío = ilimitada · dato P3 pendiente",
    "Disponibilidad": "97 / 97 / 98 / 99 % · garantía O&M pendiente",
    "Escalacion_CAPEX": "0 / 5 / 3 / 0 %/año desde jul-2026",
    "Fecha_COD": "P10: ruta crítica 18–32 m desde sep-2026",
    "Horizonte": "Decisión previa; vectores a 30 años (máx. 25)",
    "Tasa_Descuento": "Decisión previa; VAN alternos en 08",
    "Tasa_Desc_Alt1": "Sólo VAN alterno (08)",
    "Tasa_Desc_Alt2": "Sólo VAN alterno (08)",
    "Potencia_DC": "Mando maestro 1 · lista 5–8 MWp (mín. 5.000)",
    "Ratio_DCAC": "Mando maestro 2 · diseño 5.000 kWp / 3.788 kWac",
    "Potencia_AC": "Cálculo · candado art. 7.a",
    "Potencia_Ref": "Base del estudio CAPEX y del yield (no editar)",
    "Ratio_Ref": "Curva de recorte relativa a este ratio",
    "Yield_Ref": "pvlib jul-2026 · TMY Solargis adaptado",
    "Densidad_MWp_ha": "Decisión Jorge (01-sep-2026)",
    "Hectareas": "Cálculo · candado predio",
    "Ha_Disponibles": "Predio Montecristi (dos proyectos)",
    "Capacidad_Alimentador_kW": "Factibilidad CNEL pendiente (art. 7.a)",
    "Tope_SGDA_kW": "Sin tope en la 005/24 codificada (vacío)",
    "Exponente_Escala": "Decisión D3: 0 = lineal (ácido)",
    "Frac_A": "TMY P50 adaptado (GHI horario)",
    "Frac_B": "TMY · cargo = bloque A",
    "Frac_C": "TMY · cargo nocturno",
    "Tarifa_A": "Pliego 2026 (Res. 029/25) · 19 planillas",
    "Tarifa_C": "Pliego 2026 · cargo nocturno",
    "Cargo_Demanda": "No evitable (art. 27.2) · informativo",
    "Cargo_Comercializacion": "No evitable · informativo",
    "SAPG_mes": "Constante en las 19 planillas",
    "Crecimiento_Consumo": "Ácido: 0 % · mueve el tope del art. 9",
    "Fecha_Peaje": "DT Cuarta 005/24 · 28-feb-2029 (D.E. 176: 23-feb)",
    "Escenario_Energia": "P50 mediana pvlib · P90 −10,7 % (04)",
    "Factor_CAPEX": "1,15 = rango alto del estudio CAPEX/OPEX",
    "CAPEX_Fijo_Wp": "0,75 = deck v4 (22-jul-2026) · vacío = bottom-up",
    "Factor_OPEX": "1,15 = rango alto del estudio CAPEX/OPEX",
    "Peaje_SGDA": "No publicado (DT Cuarta 005/24) · 0 / 1,5 / 0,5 / 0 ¢",
    "Escalacion_Tarifa": "Custom +2 % (Jorge) · C/B plana · F +2 %",
    "Fase_m1": "P10: 30 % desarrollo/procura · 70 % obra",
    "Contingencia_Pct": "Estudio CAPEX: 5–8 %",
    "Contingencia_Frac_IVA": "Mezcla de bienes y servicios gravados",
    "Fee_Gerencia_Pct": "Decisión Jorge: 7 % del subtotal EPC",
    "Asignacion_Compartida": "P5: 100 % (alternativa 50 % con 2ª planta)",
    "Contrato_Inversion": "P11: No · si Sí, arancel e ISD = 0 (los 4 casos)",
    "IVA_Recuperable": "P3: crédito por arriendos gravados (art. 66)",
    "Tasa_IVA": "LRTI art. 65 · 15 % · sin cambio 2026",
    "FODINFA_Pct": "COPCI art. 110",
    "ISD_Pct": "SRI 2026 · sin crédito tributario",
    "Fee_OM_kWp": "v3.1: 16 $/kWp (Jorge 04-sep) · deck 20",
    "Seguro_kWp": "Estudio CAPEX/OPEX: 2,5–5 $/kWp",
    "Renta_Terreno_ha": "Decisión Jorge · 10 % bruto sobre 50 k$/ha",
    "Tributos_Locales": "Estimación · 1,5 ‰ activos + patente + predial",
    "Escalacion_OPEX": "v3.1: 2 %/año (Jorge 04-sep) · estudio 1–2 %",
    "Comprador_Terreno": "v3.1: SALELGI compra (Jorge 04-sep) · alt. Exergy",
    "Precio_Terreno_ha": "Decisión Jorge (01-sep-2026)",
    "Costos_Transaccion_Terreno_Pct": "Alcabala 1 % + notaría/registro ≈ 0,5 %",
    "Predial_Terreno": "Estimación S4 (< 2.000 $/año)",
    "Residual_Terreno_Pct": "Base: conserva su valor nominal",
    "Apreciacion_Terreno": "Ácido: 0 %",
    "Tasa_IR": "LRTI art. 37",
    "Tasa_Participacion": "Código del Trabajo art. 97",
    "Incluir_Participacion": "Toggle · comparación con libros previos",
    "Escudo_Negativo": "P3: SALELGI con utilidad gravable",
    "Vida_Fiscal_Equipos": "RALRTI (10 % anual)",
    "Vida_Fiscal_Civil": "RALRTI (5 % anual)",
    "Aplica_DedAd": "Certificación ambiental previa (RLRTI 28.6.g) · P-01",
    "Pct_Elegible_DedAd": "Estimación: 60–70 % del CAPEX industrial",
    "Ingresos_SALELGI": "P3: rango 8–12 M · confirmar contabilidad",
    "Tope_DedAd_Pct": "LRTI art. 10.7",
    "Meses_Recup_IVA": "Informativo · no alimenta cálculos",
    "Usar_Deuda": "Sólo elige qué destaca la portada",
    "Pct_Apalancamiento": "v3.1: 100 % (Jorge 04-sep) · máx. sostenible 10 §H",
    "Deuda_Financia_Terreno": "Decisión D2: terreno con capital",
    "Tasa_Deuda": "v3.1: 7,5 % (Jorge) · BCE corp. 6,79 % (ago-2026)",
    "Plazo_Deuda": "P4: 8 años incl. gracia · 10 mejora el DSCR",
    "Gracia_Deuda": "P4: 12 meses sólo intereses",
    "IDC_Frac_Tramo0": "Decisión G2-1: medio año promedio",
    "DSCR_Objetivo": "Regla bancaria típica",
    "Costo_Gerencia_Pct": "Estimación · margen neto ≈ 4,5 pts",
    "Costo_OM_Exergy_kWp": "Estudio CAPEX/OPEX mín. 16 $/kWp",
    "Tasa_Efectiva_Exergy": "15 % + 25 % × 85 %",
    "Umbral_Riesgo_Alto": "11_Riesgos",
    "Umbral_Riesgo_Medio": "11_Riesgos",
    "Tol_Costo_Tramites": "03_Tramites",
    "Tol_Dias_COD": "03_Tramites y 13_Controles",
}

# etiqueta corta (≤ 46 caracteres) cuando la de INPUTS es larga; la etiqueta original se conserva al inicio del comentario
LABEL = {
    "Ratio_DCAC": "Ratio DC/AC (módulos / inversores)", "Potencia_Ref": "Potencia de referencia (estudio CAPEX y yield)",
    "Yield_Ref": "Yield específico P50 año 1 a la referencia", "Capacidad_Alimentador_kW": "Capacidad aprobable de inyección (13,8 kV)",
    "Tope_SGDA_kW": "Tope regulatorio de potencia SGDA (vacío = ninguno)", "Exponente_Escala": "Exponente de economías de escala ε",
    "Frac_A": "Fracción de la inyección en bloque A (08–18 h)", "Frac_B": "Fracción en bloque B (18–22 h)", "Frac_C": "Fracción en bloque C (22–08 h)",
    "Tarifa_A": "Cargo de energía 08–22 h (bloques A y B)", "Tarifa_C": "Cargo de energía 22–08 h (bloque C)",
    "Cargo_Demanda": "Cargo por demanda (no evitable, informativo)",
    "Contingencia_Frac_IVA": "Fracción de la contingencia gravada con IVA",
    "Asignacion_Compartida": "Rubros compartibles del sitio cargados a GPM", "IVA_Recuperable": "IVA del CAPEX recuperable como crédito",
    "Seguro_kWp": "Seguros all-risk + RC (paga SALELGI)", "Renta_Terreno_ha": "Arriendo del terreno a Exergy (si es la dueña)",
    "Tributos_Locales": "Tributos locales y administración", "Escalacion_OPEX": "Escalación anual del OPEX",
    "Costos_Transaccion_Terreno_Pct": "Costos de transacción de la compra", "Predial_Terreno": "Predial y gastos anuales del terreno",
    "Residual_Terreno_Pct": "Valor residual del terreno (% del precio)", "Apreciacion_Terreno": "Apreciación anual del terreno",
    "Tasa_Participacion": "Participación laboral sobre la utilidad", "Incluir_Participacion": "Incluir participación laboral (SALELGI)",
    "Escudo_Negativo": "Escudo fiscal de las pérdidas incrementales", "Pct_Elegible_DedAd": "% del CAPEX elegible para deducción adicional",
    "Aplica_DedAd": "Deducción adicional aplicable (certificación)",
    "Ingresos_SALELGI": "Ingresos anuales de SALELGI (tope del 5 %)", "Tope_DedAd_Pct": "Tope de la deducción adicional (% ingresos)",
    "Meses_Recup_IVA": "Meses para absorber el crédito de IVA (memo)", "Usar_Deuda": "Destacar el caso con deuda en la portada",
    "Deuda_Financia_Terreno": "El banco financia el terreno (si compra SALELGI)", "IDC_Frac_Tramo0": "IDC: fracción de año del tramo del año 0",
    "Costo_Gerencia_Pct": "Costo interno de Exergy por gerenciar", "Costo_OM_Exergy_kWp": "Costo propio de Exergy por operar el SGDA",
    "Tasa_Efectiva_Exergy": "Tasa efectiva de impuestos de Exergy", "Umbral_Riesgo_Alto": "Score desde el que un riesgo es alto",
    "Umbral_Riesgo_Medio": "Score desde el que un riesgo es medio", "Tol_Costo_Tramites": "Tolerancia del cronograma vs rubro 9",
    "Tol_Dias_COD": "Tolerancia entre COD del cronograma y Fecha_COD", "Fecha_COD": "Fecha objetivo de inicio de operación (COD)",
    "Crecimiento_Consumo": "Crecimiento anual de la demanda del medidor", "Fee_Gerencia_Pct": "Fee de gerencia del proyecto (Exergy)",
    "Fase_m1": "Fracción del CAPEX desembolsada en el año −1",
    "Escenario_Energia": "Energía del caso (P50 / P90)", "Factor_CAPEX": "Factor sobre el CAPEX bottom-up (05)",
    "CAPEX_Fijo_Wp": "CAPEX unitario fijo (vacío = bottom-up × factor)", "Factor_OPEX": "Factor sobre el OPEX de SALELGI (06)",
    "Peaje_SGDA": "Peaje de red SGDA desde Fecha_Peaje", "Escalacion_Tarifa": "Escalación anual de la tarifa evitable",
    "Tasa_Descuento_Equity": "Tasa de descuento del accionista (VAN equity)", "Meses_Construccion": "Meses de construcción (IDC) — de 03",
    "Fecha_Precios": "Fecha de los precios del CAPEX (05)", "Reemplazo_Anio": "Reemplazo de inversores: año (t)", "Reemplazo_USD_Wac": "Reemplazo de inversores: costo",
    "Reemplazo_Pagador": "Reemplazo de inversores: quién paga", "Desmantelamiento_Pct": "Desmantelamiento en t = H (% del CAPEX)",
    "Degradacion_Adicional": "Degradación adicional sobre el yield canónico", "Peaje_kW_mes": "Peaje SGDA por potencia (desde Fecha_Peaje)",
    "Utilidad_Gravable_SALELGI": "Utilidad gravable disponible (vacío = ilimitada)",
    "Disponibilidad": "Disponibilidad de la planta", "Escalacion_CAPEX": "Escalación del CAPEX hasta la compra",
}

# dónde se sensibiliza cada parámetro: (texto, clave de ancla en 10 o destino explícito)
SENS = {
    "Potencia_DC": ("10 §F.1 barrido 5–8 MWp · §F.3", "F1"), "Ratio_DCAC": ("10 §F.2 · §F.3", "F2"),
    "Comprador_Terreno": ("10 §G", "G"), "Usar_Deuda": ("— (sólo portada)", None),
    "Tasa_Descuento": ("08 VAN a tasas alternas", f"#'{S8}'!B{FLUJO['kpi_sec']}"), "Horizonte": ("— (máximo 25; control G5)", None), "Fecha_COD": ("03 cronograma (fecha implícita)", "#Check_Cron"),
    "Capacidad_Alimentador_kW": ("13 candado F4 · 10 §F.2", "F2"), "Ha_Disponibles": ("13 candado F5", "#Estado_Controles"),
    "Tarifa_A": ("10 §B tarifa ± · §C matriz", "B"), "Tarifa_C": ("10 §B tarifa ± · §C matriz", "B"),
    "Crecimiento_Consumo": ("10 §F.1 (tope art. 9)", "F1"),
    "Escenario_Energia": ("10 §A los cuatro casos · §A.2 P50 vs P90", "A"), "Factor_CAPEX": ("10 §A · §B CAPEX ± · §C matriz", "A"),
    "CAPEX_Fijo_Wp": ("10 §A (Favorable) · 05 comparativo", "A"), "Factor_OPEX": ("10 §A · §B OPEX ±", "A"),
    "Peaje_SGDA": ("10 §A · §B peaje · §E piso", "A"), "Escalacion_Tarifa": ("10 §A (Favorable) · §B escalación", "A"),
    "Contingencia_Pct": ("10 §B (dentro de CAPEX ±)", "B"), "Fee_Gerencia_Pct": ("09 sensibilidad 5 / 7 / 9 %", f"#'{S9}'!B{EXERGY['sens_sec']}"),
    "Exponente_Escala": ("10 §F (escala de los drivers)", "F1"), "Contrato_Inversion": ("10 §B alterno", "B"), "IVA_Recuperable": ("10 §B alterno · §E piso", "B"),
    "Fee_OM_kWp": ("09 sensibilidad 18 / 20 / 24 · 10 §B OPEX ±", f"#'{S9}'!B{EXERGY['sens_sec']}"), "Seguro_kWp": ("10 §B OPEX ±", "B"),
    "Renta_Terreno_ha": ("09 sensibilidad 3 / 5 / 7 k$ · 10 §G", f"#'{S9}'!B{EXERGY['sens_sec']}"), "Tributos_Locales": ("10 §B OPEX ±", "B"), "Escalacion_OPEX": ("10 §B OPEX ±", "B"),
    "Precio_Terreno_ha": ("10 §G precio × 0,6 / 1,0 / 1,4", "G"), "Costos_Transaccion_Terreno_Pct": ("10 §G", "G"), "Predial_Terreno": ("10 §G", "G"),
    "Residual_Terreno_Pct": ("10 §G", "G"), "Apreciacion_Terreno": ("10 §G", "G"),
    "Pct_Apalancamiento": ("10 §D · §H deuda máxima", "D"), "Tasa_Deuda": ("10 §D cinco tasas", "D"), "Plazo_Deuda": ("10 §D · §H (8 / 10 / 12)", "D"),
    "DSCR_Objetivo": ("10 §H umbral", "H"), "Deuda_Financia_Terreno": ("10 §G", "G"),
    "Incluir_Participacion": ("10 §B alterno", "B"), "Costo_Gerencia_Pct": ("09", f"#'{S9}'!B{EXERGY['kpi_sec']}"), "Costo_OM_Exergy_kWp": ("09", f"#'{S9}'!B{EXERGY['kpi_sec']}"),
    "Disponibilidad": ("10 §A · §A.3 puente · §B ±2 pp", "A"), "Escalacion_CAPEX": ("10 §A · §A.3 puente · §B +2 pp · 05", "A"),
    "Tasa_Descuento_Equity": ("10 §A.3 puente (VAN acc.)", "A3"), "Meses_Construccion": ("10 §A.3 puente · 03 cronograma", "A3"),
    "Fecha_Precios": ("05 Factor_Escalacion", f"#Factor_Escalacion"), "Reemplazo_Anio": ("05 · 10 §G reemplazo", "G"), "Reemplazo_USD_Wac": ("05 · 10 §B · §G", "G"),
    "Reemplazo_Pagador": ("10 §G quién paga · §B alterno", "G"), "Desmantelamiento_Pct": ("10 §B 2 %", "B"),
    "Degradacion_Adicional": ("10 §B +0,2 %/año", "B"), "Peaje_kW_mes": ("10 §B 0,5 $/kW-mes", "B"), "Utilidad_Gravable_SALELGI": ("10 §B sin absorción", "B"),
    "Aplica_DedAd": ("10 §B sin deducción adicional", "B"),
}

# columnas: B Parámetro · C Custom · D Conservador · E Base · F Favorable · G Unidad · H Sensibilizado en · I Fuente · J–O ocultas
W = {"A": 2, "B": 46, "C": 12, "D": 12, "E": 12, "F": 12, "G": 11, "H": 26, "I": 44, "J": 5, "K": 5, "L": 5, "M": 5, "N": 5, "O": 4}
LAST = 9                 # última columna visible (I)
COL_CASE = {"X": 3, "C": 4, "B": 5, "F": 6}
COL_REF = {"X": 10, "C": 11, "B": 12, "F": 13}   # J = referencia Base del Custom · K/L/M = definición entregada de C/B/F
COL_NAME, COL_MARK = 14, 15                      # N · O
PANEL = [
    # (etiqueta, fórmula del valor (texto), fórmula del contexto, nombre de la entrada a editar, color de la etiqueta)
    ("Potencia DC", '=TEXT(Potencia_DC,"#,##0")&" kWp"', '="ratio "&TEXT(Ratio_DCAC,"0.00")&" → "&TEXT(Potencia_AC,"#,##0")&" kWac · "&TEXT(Hectareas,"0.0")&" ha · lista 5–8 MWp"', "Potencia_DC", None),
    ("Ratio DC/AC", '=TEXT(Ratio_DCAC,"0.00")', '="recorte "&TEXT(Loss_Act,"0.00%")&" · alimentador "&TEXT(Capacidad_Alimentador_kW,"#,##0")&" kW (por confirmar)"', "Ratio_DCAC", None),
    ("Caso Custom", '=IF(N_Custom_vs_Base=0,"= Base","≠ Base · "&N_Custom_vs_Base)',
     '=Escenario_Energia&" · CAPEX "&IF(N(CAPEX_Fijo_Wp)>0,"fijo "&TEXT(CAPEX_Fijo_Wp,"0.00")&" $/Wp","× "&TEXT(Factor_CAPEX,"0.00"))&IF(Escalacion_CAPEX>0," +"&TEXT(Escalacion_CAPEX,"0%")&"/año","")&" · OPEX × "&TEXT(Factor_OPEX,"0.00")&" · peaje "&TEXT(Peaje_SGDA*100,"0.0")&" ¢ · tarifa "&IF(Escalacion_Tarifa=0,"plana","+"&TEXT(Escalacion_Tarifa,"0.0%")&"/año")&" · disp. "&TEXT(Disponibilidad,"0%")', "Escenario_Energia", X_COL),
    ("Compra el terreno", "=Comprador_Terreno", '=IF(Comprador_Terreno="Exergy","arrienda a SALELGI a "&TEXT(Renta_Terreno_ha,"#,##0")&" $/ha-año","SALELGI compra: sin arriendo, paga predial")', "Comprador_Terreno", None),
    ("Deuda", '=TEXT(Pct_Apalancamiento,"0%")&" · "&TEXT(Tasa_Deuda,"0.0%")&" · "&Plazo_Deuda&" años"', '="gracia "&Gracia_Deuda&" a · DSCR objetivo "&TEXT(DSCR_Objetivo,"0.00")&"x · portada: "&IF(Usar_Deuda="Sí","con deuda","sin deuda")', "Pct_Apalancamiento", None),
    ("Tarifa evitable", '=TEXT(Tarifa_Evitable,"0.0000")&" $/kWh"', '="Custom: escalación "&TEXT(Eff_EscT,"0.0%")&"/año · peaje "&TEXT(Eff_Peaje*100,"0.0")&" ¢ desde "&TEXT(Fecha_Peaje,"yyyy")', "Tarifa_A", None),
    ("CAPEX Custom", '=TEXT(CAPEX_Total/(Potencia_DC*1000),"0.000")&" $/Wp"', '=TEXT(CAPEX_Total,"#,##0")&" USD sin IVA · "&IF(N(CAPEX_Fijo_Wp)>0,"fijo","bottom-up × "&TEXT(Factor_CAPEX,"0.00"))&" · C × "&TEXT(INDEX(Esc_Factor_CAPEX,2),"0.00")&" · F fijo "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4),"0.00")', "Factor_CAPEX", X_COL),
    ("Tasa de descuento", '=TEXT(Tasa_Descuento,"0.0%")', '="nominal USD · alternas "&TEXT(Tasa_Desc_Alt1,"0%")&" / "&TEXT(Tasa_Desc_Alt2,"0%")&" · horizonte "&Horizonte&" años"', "Tasa_Descuento", None),
]
CARD_COLS = [(2, 2), (3, 5), (6, 7), (8, 9)]   # B · C:E · F:G · H:I


def build_supuestos(wb):
    ws = wb.create_sheet(S1)
    widths(ws, W)
    sheet_header(ws, "1 · Supuestos", "Única hoja de entradas. Edite sólo la tinta («· por confirmar» = sin fuente firme). El bloque B define los cuatro casos; el resto es diseño compartido. El Custom gobierna 04–09 y la portada.", 1, last_col=LAST, total=NSHEETS)
    by_name = {nm: (lab, val, u, fmt, conf, nt) for sec, nm, lab, val, u, fmt, conf, nt in INPUTS if nm}
    esc_by = {e[0]: e for e in ESCENARIOS}
    # ---- leyenda
    r = 5
    lg = ws.cell(row=r, column=2, value="Convenciones:")
    lg.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO, bold=True)
    parts = [("tinta = editable", TINTA, False), ("carbón = calculado", CARBON, False), ("· por confirmar", ARCILLA, False),
             ("Custom", X_COL, True), ("Conservador", C_COL, True), ("Base", B_COL, True), ("Favorable", F_COL, True), ("arcilla = distinto del Base / de la definición entregada", ARCILLA, False)]
    rt = CellRichText()
    for i, (txt, colr, b) in enumerate(parts):
        if i:
            rt.append(TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=GRAFITO), "   ·   "))
        rt.append(TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=colr, b=b), txt))
    c = ws.cell(row=r, column=3, value=rt)
    c.alignment = Alignment(vertical="center")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=LAST)
    ws.row_dimensions[r].height = 16
    # ---- panel de mandos (2 filas × 4 tarjetas, 4 filas cada una) + fila de estado
    r = 7
    section(ws, r, 2, LAST, "Panel de mandos", guide="los ocho maestros del modelo (sólo lectura; se editan en la tabla — enlace «editar ↓»)")
    r += 1
    panel_top = r
    r += 2 * 4
    status_row = r
    r += 4
    # ---- tabla
    hdr(ws, r, 2, LAST, ["Parámetro", "", "", "", "", "Unidad", "Sensibilizado en", "Fuente · nota"], height=20)
    for key, cc in COL_CASE.items():
        caso_hdr(ws, r, cc, key, size=SZ_TABLE)
    for cc, txt in ((COL_REF["X"], "ref. Base"), (COL_REF["C"], "ref. C"), (COL_REF["B"], "ref. B"), (COL_REF["F"], "ref. F"), (COL_NAME, "Nombre"), (COL_MARK, "m")):
        ws.cell(row=r, column=cc, value=txt).font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO)
    hdr_row = r
    r += 1
    dvs = {k: DataValidation(type="list", formula1=v, allow_blank=False) for k, v in SELECTORS.items()}
    dv_yes = DataValidation(type="list", formula1='"Sí,No"', allow_blank=False)
    for dv in list(dvs.values()) + [dv_yes]:
        ws.add_data_validation(dv)
    row_of = {}
    first_row = r
    used = set()
    group_rows = []
    b_rows = []

    def write_meta(r, nm, unit_txt, nt, cell_for_comment):
        short = SHORT.get(nm, "")
        comment(cell_for_comment, nt)
        unit(ws, r, 7, unit_txt)
        s_txt, s_target = SENS.get(nm, ("—", None))
        sc = ws.cell(row=r, column=8, value=s_txt)
        sc.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO)
        sc.alignment = Alignment(vertical="center", wrap_text=True)
        sc.border = B_BOTTOM
        if s_target:
            loc = s_target[1:] if s_target.startswith("#") else (f"'{S10}'!{BC.SENS_ANCHORS[s_target]}" if s_target in BC.SENS_ANCHORS else None)
            if loc:
                sc.hyperlink = Hyperlink(ref=sc.coordinate, location=loc, display=str(sc.value))
        nc = ws.cell(row=r, column=9, value=short)
        nc.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO); nc.alignment = Alignment(vertical="center", wrap_text=True); nc.border = B_BOTTOM
        hn = ws.cell(row=r, column=COL_NAME, value=nm)
        hn.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO)

    def write_label(r, lab, confirm):
        if confirm:
            rt = CellRichText([TextBlock(InlineFont(rFont=FONT, sz=SZ_BODY, color=CARBON), lab), TextBlock(InlineFont(rFont=FONT, sz=SZ_TABLE, color=ARCILLA), " · por confirmar")])
            c = ws.cell(row=r, column=2, value=rt)
            c.alignment = Alignment(vertical="center", wrap_text=True)
            c.border = B_BOTTOM
        else:
            label(ws, r, 2, lab, wrap=True, size=SZ_BODY)

    for bname, guide, names_ in BLOQUES:
        ws.row_dimensions[r].height = 8   # aire entre bloques
        r += 1
        if bname.startswith("B ·"):
            # banda del bloque B: sin guía en C:F (llevan el nombre de cada caso en su color); la guía va en G:I
            section(ws, r, 2, LAST, bname)
            for key, cc in COL_CASE.items():
                t = ws.cell(row=r, column=cc, value=CASO_NOMBRE[key]); t.font = Font(name=FONT, size=SZ_TABLE, bold=True, color=CASO_COL[key]); t.alignment = Alignment(horizontal="right", vertical="center")
            ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=LAST)
            g = ws.cell(row=r, column=7, value=guide); g.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO); g.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
            ws.row_dimensions[r].height = 30
        else:
            section(ws, r, 2, LAST, bname, guide=guide, guide_col=3)
        r += 1
        for nm in names_:
            if nm in esc_by:
                # ---------------- bloque B: cuatro columnas
                nm_, rng_nm, lab0, unit_txt, fmt, vals, confirm, nt = esc_by[nm]
                lab = LABEL.get(nm, lab0)
                if lab != lab0:
                    nt = f"{lab0}. {nt}"
                used.add(nm)
                write_label(r, lab, confirm)
                cells = {}
                for key in CASE_KEYS:
                    v = vals[key]
                    cc = COL_CASE[key]
                    if key == "X":
                        cell = inp(ws, r, cc, v, fmt=fmt, confirm=confirm)
                    else:
                        cell = ws.cell(row=r, column=cc, value=v)
                        cell.font = Font(name=FONT, size=SZ_BODY, color=GRAFITO); cell.border = B_BOTTOM; cell.alignment = Alignment(horizontal="right", vertical="center")
                        if fmt:
                            cell.number_format = fmt
                    cells[key] = cell
                    if nm in dvs:
                        dvs[nm].add(cell)
                    # referencias ocultas: J = columna Base (viva) para el Custom; K/L/M = definición entregada de C/B/F
                    rc = COL_REF[key]
                    if key == "X":
                        ref = ws.cell(row=r, column=rc, value=f'=IF(ISBLANK(E{r}),"",E{r})')   # vacío en el Base → "" (comparable con el vacío del Custom; 0 ≠ vacío)
                    else:
                        ref = ws.cell(row=r, column=rc, value=v)
                    ref.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO)
                    if fmt:
                        ref.number_format = fmt
                m = ws.cell(row=r, column=COL_MARK, value=(2 if confirm else 1)); m.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO)
                if nm in SELECTORS:
                    nt = f"Opciones: {unit_txt}. {nt}"
                    unit_txt = "lista ▾"
                write_meta(r, nm, unit_txt, nt, cells["X"])
                name(wb, nm, S1, f"$C${r}")
                name(wb, rng_nm, S1, f"$C${r}:$F${r}")
                row_of[nm] = r
                b_rows.append(r)
                ws.row_dimensions[r].height = 20
                r += 1
                continue
            # ---------------- capa de diseño / estructural: una sola columna de valor (Custom); D/E/F vacías
            lab0, val, unit_txt, fmt, confirm, nt = by_name[nm]
            lab = LABEL.get(nm, lab0)
            if lab != lab0:
                nt = f"{lab0}. {nt}"
            used.add(nm)
            is_calc = isinstance(val, str) and val.startswith("=")
            is_info = nm in INFO_INPUTS
            write_label(r, lab, confirm)
            if is_calc:
                cell = calc(ws, r, 3, val, fmt=fmt, color=CARBON)
            elif is_info:
                cell = ws.cell(row=r, column=3, value=val)
                cell.font = Font(name=FONT, color=GRAFITO, size=SZ_BODY); cell.border = B_BOTTOM; cell.alignment = Alignment(horizontal="right")
                if fmt:
                    cell.number_format = fmt
            else:
                cell = inp(ws, r, 3, val, fmt=fmt, confirm=confirm)
                ref = ws.cell(row=r, column=COL_REF["X"], value=val)   # J: valor entregado (= Base por definición)
                ref.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO)
                if fmt:
                    ref.number_format = fmt
                m = ws.cell(row=r, column=COL_MARK, value=(2 if confirm else 1))
                m.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO)
            for cc in (4, 5, 6):
                ws.cell(row=r, column=cc).border = B_BOTTOM
            if nm in SELECTORS or nm in YESNO:
                nt = f"Opciones: {unit_txt}. {nt}" if unit_txt else nt
                unit_txt = "lista ▾"
            write_meta(r, nm, unit_txt, nt, cell)
            name(wb, nm, S1, f"$C${r}")
            row_of[nm] = r
            if nm in YESNO:
                dv_yes.add(cell)
            if nm in dvs:
                dvs[nm].add(cell)
            ws.row_dimensions[r].height = 20   # filas uniformes: etiquetas ≤ 46 caracteres, notas ≤ 60
            if bname.startswith("I ·"):
                group_rows.append(r)
            r += 1
    missing = set(by_name) - used
    assert not missing, f"entradas sin bloque: {missing}"
    assert set(ESC_NAMES) <= used
    last_row = r - 1
    b0, b1 = min(b_rows), max(b_rows)
    # avisos: Custom ≠ Base (arcilla en C) · C/B/F ≠ definición entregada (arcilla en D/E/F)
    ws.conditional_formatting.add(f"C{first_row}:C{last_row}", FormulaRule(formula=[f'AND($O{first_row}>0,(C{first_row}&"")<>($J{first_row}&""))'], font=Font(color=ARCILLA, bold=True)))
    for key in ("C", "B", "F"):
        cc = col(COL_CASE[key]); rc = col(COL_REF[key])
        ws.conditional_formatting.add(f"{cc}{b0}:{cc}{b1}", FormulaRule(formula=[f'({cc}{b0}&"")<>(${rc}{b0}&"")'], font=Font(color=ARCILLA, bold=True)))
    # bloque I agrupado (avanzado): plegado por defecto
    if group_rows:
        ws.row_dimensions.group(group_rows[0], group_rows[-1], outline_level=1, hidden=True)
    # ---- J · calculados de apoyo
    r += 1
    ws.row_dimensions[r].height = 8
    r += 1
    section(ws, r, 2, LAST, "J · Calculados de apoyo", guide="no editar: estado del libro, tasas efectivas y factores derivados", guide_col=3)
    r += 1
    n_conf = sum(1 for sec, nm, lab, val, u, fmt, conf, nt in INPUTS if nm and conf) + sum(1 for e in ESCENARIOS if e[6]) + 1   # + drivers de 05
    calcs = [
        ("Entradas del Custom distintas del Base", f'=SUMPRODUCT(($O${first_row}:$O${last_row}>0)*(($C${first_row}:$C${last_row}&"")<>($J${first_row}:$J${last_row}&"")))', "0", "n.º", "N_Custom_vs_Base", "0 = el Custom coincide con el Base (bloque B y capa de diseño); las distintas se marcan en arcilla. Comparación como texto: vacío ≠ 0 (p. ej. Utilidad_Gravable_SALELGI)"),
        ("Estado del Custom", '=IF(N_Custom_vs_Base=0,"● Custom = Base","▲ Custom ≠ Base en "&N_Custom_vs_Base&" entrada(s)")', None, "", "Estado_Custom", "Se muestra en la portada, 10 §A y 13_Controles"),
        ("Supuestos de C/B/F distintos de la definición entregada", f'=SUMPRODUCT(($O${b0}:$O${b1}>0)*((($D${b0}:$D${b1}&"")<>($K${b0}:$K${b1}&""))+(($E${b0}:$E${b1}&"")<>($L${b0}:$L${b1}&""))+(($F${b0}:$F${b1}&"")<>($M${b0}:$M${b1}&""))))', "0", "n.º", "N_Fuera_Entregado", "0 = los tres escenarios fijos siguen la definición entregada (control G4); comparación como texto (vacío ≠ 0)"),
        ("Estado de los escenarios fijos", '=IF(N_Fuera_Entregado=0,"● C · B · F según la definición entregada","▲ "&N_Fuera_Entregado&" supuesto(s) de C/B/F fuera de la definición "&Version)', None, "", "Estado_Entregado", "Se muestra en la portada, 10 §A y 13_Controles"),
        ("Supuestos por confirmar", f"=COUNTIF($O${first_row}:$O${last_row},2)+(COUNTA(Drv_Wp)>0)", "0", "n.º", "N_Por_Confirmar", "Marcados aquí + los drivers de escala de 05 (un ítem); lista en 12 §A"),
        ("Supuestos por confirmar al entregar (constante del generador)", n_conf, "0", "n.º", "N_Por_Confirmar_Esperado", "Referencia del control I2 de 13: si difiere, la lista de 12 §A está desactualizada"),
        ("Tasa efectiva marginal de SALELGI", '=IF(Incluir_Participacion="Sí",Tasa_Participacion,0)+Tasa_IR*(1-IF(Incluir_Participacion="Sí",Tasa_Participacion,0))', FMT_PCT2, "%", "Tasa_Efectiva", "15 % + 25 % × 85 % = 36,25 % con participación"),
        ("Escenario de energía efectivo (1 = P50 · 2 = P90)", '=IF(Escenario_Energia="P50",1,2)', "0", "", "Eff_Scen", "Custom · gobierna 04_Energia"),
        ("Factor OPEX efectivo", "=Factor_OPEX", "0.000", "×", "Eff_fO", "Custom · se aplica en 07 sobre el OPEX de 06"),
        ("Peaje SGDA efectivo", "=Peaje_SGDA", FMT_KWH, "$/kWh", "Eff_Peaje", "Custom"),
        ("Escalación de tarifa efectiva", "=Escalacion_Tarifa", FMT_PCT, "%/año", "Eff_EscT", "Custom"),
        ("Escala de los componentes por Wp", "=(Potencia_DC/Potencia_Ref)^(1-Exponente_Escala)", "0.0000", "×", "Escala_Wp", "(Potencia_DC / Potencia_Ref)^(1−ε) · costos ligados a la potencia DC"),
        ("Escala de los componentes por Wac", "=(Potencia_AC/(Potencia_Ref/Ratio_Ref))^(1-Exponente_Escala)", "0.0000", "×", "Escala_Wac", "(Potencia_AC / AC_ref)^(1−ε) · costos ligados a la potencia AC"),
        ("Fecha estimada de fin de operación", "=EDATE(Fecha_COD,12*Horizonte)", FMT_DATE, "fecha", "Fin_Operacion", "COD + horizonte"),
        ("Años entre los precios del CAPEX y el COD", "=(Fecha_COD-Fecha_Precios)/365.25", "0.00", "años", "Anios_Precios", "Base de la escalación del CAPEX (05 Factor_Escalacion): tramo −1 a (años − 1), tramo 0 a (años)"),
        ("Parámetros de la ronda 2 fuera de su valor neutro (0 = libro ≡ v2.0)", '=(Disponibilidad<>1)+(Escalacion_CAPEX<>0)+(Reemplazo_Pagador<>"No")+(Meses_Construccion<>12)+(ABS(Tasa_Descuento_Equity-Tasa_Descuento)>0.000001)+(Desmantelamiento_Pct<>0)+(Degradacion_Adicional<>0)+(Peaje_kW_mes<>0)+ISNUMBER(Utilidad_Gravable_SALELGI)', "0", "n.º", "N_Neutro", "Los 9 parámetros nuevos (disponibilidad, escalación CAPEX, reemplazo, meses, tasa accionista, desmantelamiento, degradación, peaje kW, utilidad gravable) tienen un valor neutro que reproduce la v2.0"),
        ("Estado de la ronda 2 (alcance del motor)", '=IF(N_Neutro=0,"● Ronda 2 en neutro: el libro reproduce la v2.0","◇ Ronda 2: "&N_Neutro&" de 9 parámetros fuera de neutro (puente en 10 §A.3)")', None, "", "Estado_Neutro", "Se muestra en el panel de mandos, 10 §A.3 y 13 (I3)"),
        ("Fracción del año 0 con IDC (memo)", "=IDC_Frac_Tramo0", "0.00", "años", None, "Memo de IDC_Frac_Tramo0"),
    ]
    for lab, f, fmt, u, nm, nt in calcs:
        label(ws, r, 2, lab)
        if fmt is None:
            chip(ws, r, 3, f, kind=("custom" if nm == "Estado_Custom" else ("info" if nm == "Estado_Neutro" else "ok")), c2=6)
        else:
            calc(ws, r, 3, f, fmt=fmt, bold=(nm in ("Tasa_Efectiva", "N_Custom_vs_Base", "N_Fuera_Entregado", "N_Por_Confirmar")))
            for cc in (4, 5, 6):
                ws.cell(row=r, column=cc).border = B_BOTTOM
        unit(ws, r, 7, u)
        ws.cell(row=r, column=8).border = B_BOTTOM
        nc = ws.cell(row=r, column=9, value=nt); nc.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO); nc.border = B_BOTTOM; nc.alignment = Alignment(vertical="center", wrap_text=True)
        hn = ws.cell(row=r, column=COL_NAME, value=nm or ""); hn.font = Font(name=FONT, size=SZ_NOTE, color=GRAFITO)
        if nm:
            name(wb, nm, S1, f"$C${r}")
        ws.row_dimensions[r].height = 20
        r += 1
    # ---- panel de mandos: rellenar
    for k, (lab, vf, cf, nm, lab_color) in enumerate(PANEL):
        rr = panel_top + (k // 4) * 4
        c1, c2 = CARD_COLS[k % 4]
        for i in range(4):
            for cc in range(c1, c2 + 1):
                ws.cell(row=rr + i, column=cc).fill = fill(LINO)
            if c2 > c1:
                ws.merge_cells(start_row=rr + i, start_column=c1, end_row=rr + i, end_column=c2)
        for cc in range(c1, c2 + 1):
            ws.cell(row=rr, column=cc).border = Border(top=(rule_caso["X"] if lab_color else rule_soft))
        a = ws.cell(row=rr, column=c1, value=lab.upper()); a.font = Font(name=FONT, size=SZ_TABLE, color=(lab_color or GRAFITO), bold=bool(lab_color)); a.alignment = Alignment(vertical="bottom", indent=1)
        v = ws.cell(row=rr + 1, column=c1, value=vf); v.font = Font(name=FONT_LIGHT, size=16, color=CARBON); v.alignment = Alignment(vertical="center", indent=1)
        x = ws.cell(row=rr + 2, column=c1, value=cf); x.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO); x.alignment = Alignment(vertical="top", wrap_text=True, indent=1)
        e = link_cell(ws, rr + 3, c1, "editar ↓", f"#'{S1}'!C{row_of[nm]}", size=SZ_NOTE, align="left", valign="top")
        e.alignment = Alignment(horizontal="left", vertical="top", indent=1)
        ws.row_dimensions[rr].height = 16; ws.row_dimensions[rr + 1].height = 24; ws.row_dimensions[rr + 2].height = 28; ws.row_dimensions[rr + 3].height = 14
    # fila de estado bajo el panel
    lab = ws.cell(row=status_row, column=2, value="Estado del libro"); lab.font = Font(name=FONT, size=SZ_TABLE, color=GRAFITO, bold=True); lab.alignment = Alignment(vertical="center", indent=1)
    chip(ws, status_row, 3, "=Estado_Custom", kind="custom", c2=5)
    chip(ws, status_row, 6, "=Estado_Entregado", kind="ok", c2=LAST)
    chip(ws, status_row + 1, 3, '="▲ "&N_Por_Confirmar&" supuestos por confirmar (lista en 12 §A)"', kind="warn", c2=5)
    chip(ws, status_row + 1, 6, "=Estado_Controles", kind="ok", c2=LAST)
    chip(ws, status_row + 2, 3, "=Estado_Neutro", kind="info", c2=LAST)
    ws.row_dimensions[status_row].height = 16
    ws.row_dimensions[status_row + 1].height = 16
    ws.row_dimensions[status_row + 2].height = 16
    ws.row_dimensions[status_row + 3].height = 6
    # columnas técnicas ocultas
    for cc in range(COL_REF["X"], COL_MARK + 1):
        ws.column_dimensions[col(cc)].hidden = True
    setup_print(ws, landscape=True, title_rows=f"{hdr_row}:{hdr_row}")
    return ws
