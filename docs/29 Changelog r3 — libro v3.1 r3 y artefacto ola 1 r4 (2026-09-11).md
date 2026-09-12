# 29 · Changelog r3 — libro Excel v3.1 r3 y artefacto ola 1 · r4 (≡ libro r3)

**Proyecto:** Modelo FV 5,0 MWp Montecristi → Gran Piazza Machala (SALELGI S.A. · gerencia Exergy)
**Fecha:** 11-sep-2026 (cierre 12-sep 00:00 UTC) · **Autor:** Claude (Anthropic) para Exergy EXG S.A.S.
**Régimen:** G-L2 aprobado (Jorge, 11-sep: «aprobado G-L2 (doc 28) · Ratificar D-V2-9 listo · Procede con todo y tus recomendaciones»). Quedan **dos palabras** suyas: la **sustitución** del raíz v3.0 por r3 y **«promover»** el artefacto r4.
**Antecedentes:** doc 28 (pre-revisión r2 y cola r3), doc 27 (ola 1 r2), doc 26 (plan), doc 23 (mandato v2).

## 1. Qué cambió en el libro (r2 → r3)

| ID | Cambio | Hojas | Evidencia |
|---|---|---|---|
| R3-1…R3-5 | Ya en r3-pre (doc 28 §4): guardia `IF(IRR(EQ;0,02)<=-1;"n/a";…)`, notas, glosario «n/a» | Motor, 08, 00b | r3-pre vs r2: 0 diferencias numéricas (08-sep) |
| **R3-6** (G-L2 10-1) | La barra 3 del tornado **«Escalación tarifa»** pasa de `escT = Sens_EscTarifa` (con el Custom en +2 % medía **0**) a **`escT = Custom + Sens_EscTarifa`**, con `Sens_EscTarifa` = **0,01 (+1 pp/año)** y rótulo «Escalación tarifa +1 pp/año». Nota (3) reescrita: «Escalación del Custom 2 % → 3 %/año: cada punto adicional … añade ≈ +0,9 pp de TIR». Nota de 01 «Sensibilidad: tornado 10 §B (+1 pp sobre el Custom; r3)» | 10, Motor, 01, 00_Portada (ranking) | Regresión r3 vs r2: **279 celdas distintas, las 279 en el caso «Esc. tarifa»** (regress30 con desglose por caso); 317 nombres: 0 distintos (Sens_EscTarifa 0,02 → 0,01 permitido) |
| **R3-7** (D-V2-9) | 00b, «TIR y VAN del accionista»: «Excel y el artefacto muestran la TIR real del accionista; si el flujo no tiene TIR única en dominio (o no hay deuda), «n/a»» | 00b | Texto en el PDF, pág. 7 |
| **R3-8** (hallazgo nuevo) | El **Resumen Directorio** decía «Resumen Directorio **v3.0 · 04-sep-2026**» en la cabecera (U1) y en el pie — literal heredado que r2 arrastraba. Ahora sigue a `VERSION` y `FECHA_ANALISIS` del modelo: «Resumen Directorio v3.1 · 08-sep-2026» | Resumen (todas) | U1 leído en Excel/Mac |
| **R3-9** (hallazgo nuevo) | Portada: el título del tornado decía «las 9 variables de mayor amplitud (**14** en 10 §B)» con 15 barras desde v3.1; ahora se genera del nº real de barras | 00_Portada | PDF pág. 1: «(15 en 10 §B)» |

**Consecuencia visible de R3-6:** la barra entra con **+0,90 pp** (8.ª de 15 por amplitud) y **desplaza a «Con Contrato de Inversión» (0,61 pp) del top 9 de la portada Excel**; en el artefacto la portada muestra las 5 mayores (sin cambio) y el tornado completo la incluye. Sensibilidad de la TIR del proyecto a la escalación real de la tarifa: **≈ +0,90 pp de TIR por cada +1 pp/año** (Custom 10,64 % → 11,54 %).

Puntos de G-L2 sin observación de Jorge → **se mantienen** (recomendación del doc 28): `Aplica_DedAd = Sí`; costos RC-04 5.000 · RC-08a 3.000 · RC-08b 2.000 · RC-08c 5.000 · RC-15 5.000; memo estático; **F10 en ▲** (Custom ≠ Base en 4 entradas, estado esperado → 78/79 ●); 09 O&M margen sin cambio (H2). Fecha de corte del análisis: **08-sep-2026** (sin cambios en el marco legal/fiscal; sólo cambia la revisión r3).

## 2. Verificación (tres motores + render)

| Prueba | Resultado |
|---|---|
| `pipeline.sh …_v3.1_r3` | 0 hallazgos de estilo · paginación OK · 52 errores = 52 `NA()` intencionales · **78/79 ●** (▲ F10 deliberado) · sombra30: 4.218 KPI y 81.867 celdas anuales, 0 difieren |
| Regresión r3 vs r2 (LibreOffice) | Nombres 317: 0 distintos (1 permitido) · Motor: 279 distintas, **1 caso** («Esc. tarifa») |
| `pipeline_res.sh` (Resumen r3) | 0 errores · **246 nombres ≡ modelo · 111/111 casos · 86.085 celdas del Motor idénticas** |
| Motor TS (`verify.ts`) vs oráculo r3 | **91.546 celdas / 0 fuera de tolerancia** (abs 1e-6, rel 1e-9, parámetros 1e-12) |
| TIR ≡ Excel (`irr_excel.test.ts`) | 13/13 |
| Cruce aleatorio motor ↔ LibreOffice (`crosscheck_engine.py`, 8 muestras, semilla 20260911, **Sens_EscTarifa y Escalacion_Tarifa aleatorios**) | **8/8 PASS**, 91.546 celdas cada una, 201 s |
| **Excel/Mac 16.110** (tercer motor, copias `_prueba`, AppleScript `value of range`) | Libro: **1.776/1.776 salidas** (16 × 111) ≡ LibreOffice, peor Δrel 3,6e-11 (12 cifras); **3.330/3.330 parámetros** idénticos; `Esc. tarifa` escT = 0,03; controles **78/79 ●**. Resumen: 1.776/1.776 |
| Render Excel/Mac (`check_render.py`) | Libro **66 págs.** (presupuesto 67), 0 cortes, 0 vacías (68 palabras «fuera de la caja» en págs. 47 y 51 = auxiliares U:W de 10, informativo, igual que r2) · Resumen **12 págs.**, 0 cortes |

Excel se abrió en su Mac con aviso previo (22:09 UTC), sólo sobre copias `_prueba` con nombre único, sin ningún libro suyo abierto (0 libros al empezar); las copias se cerraron sin guardar y su SHA-256 no cambió. Incidencia menor: `export_pdf` sobre un PDF ya existente tardó > 60 s (el aviso de la herramienta expiró) pero completó; los PDF del Resumen se exportaron con AppleScript propio (`save … as PDF file format`) porque la herramienta devolvió «Parameter error (-50)» dos veces seguidas en ese libro.

## 3. Artefacto — ola 1 · r4 (≡ libro r3), en candidatos 🧪/🔬

| ID | Cambio |
|---|---|
| Datos | Extracción r3 (`artefacto/data`): `book.json`, `motor.json`, `names.json`, `sheets.json`, `meta.json` (SHA del cálculo LibreOffice `6d80e87c4312efed…`, el que muestra «Acerca de»). Todos los textos nuevos (rótulos del tornado, nota (3), frase D-V2-9) vienen **del libro**, en vivo. |
| Motor | `caseDefinitions.ts`: «Esc. tarifa» = `B.escT + Sens_EscTarifa` (espejo engine ↔ app idéntico) |
| **G-nuevo** `make-oracle.py` | `inputs_v31.json` y `oracle_v31.json` se generaban con un script ad hoc no conservado (hallazgo al re-extraer). Ahora `npm run make:oracle` los regenera desde `data/`; la regla se **validó reproduciendo byte a byte el oráculo de r2**; incorporado como paso 1b de `release.sh` |
| F1-13 | El tornado mide el rótulo más largo y ensancha la columna (antes «Escalación CAPEX +2 pp/año» se recortaba por la izquierda) |
| Acerca de | `v2 · ola 1 · r4 (11-sep-2026) · libro v3.1 r3`, entrada de changelog |
| Release | `release.sh "v2 ola 1 r4 libro v3.1 r3"`: verify 91.546/0 · irr 13/13 · live PASS · format 73/73 · tsc · build + check:exclusion · smoke 22/22 × 2 · `publicados/2026-09-11_v2_ola_1_r4_libro_v3.1_r3/` |

Fragmentos definitivos: interno `635a90db…` (1.150.924 B) · externo `cd8fa243…` (1.110.723 B). Candidatos = mismos fragmentos con `<title>` «Candidato · …» (etiqueta «Candidato · ola 1 r4 · libro v3.1 r3 (final)», Version 6 en ambos). Las URL oficiales siguen en **ola 1 · r3 ≡ libro r2** hasta su «promover».

## 4. Entrega en OneDrive (`…/Modelo GPM 5MWp/`)

| Dónde | Qué |
|---|---|
| `_borrador_v3.1/` | `Modelo_FV_5MWp_GPM_v3.1_r3.xlsx` (SHA `3d85da4d3fa8e387…`) · `Modelo_FV_5MWp_Resumen_Directorio_v3.1_r3.xlsx` (SHA `35ea3d1f0ade187b…`) |
| `_borrador_v3.1/render_excel/` | `…_r3 (render Excel, libro completo).pdf` (66 págs., `f2d95627…`) · Resumen r3 (12 págs., `b4218aed…`) |
| `_borrador_v3.1/pruebas/` | copias `_r3_prueba` (SHA = entregables) · `excel_r3_motor_2026-09-11.txt` y `excel_r3_resumen_motor_2026-09-11.txt` (valores leídos de Excel/Mac) |
| `_borrador_v3.1/Fuentes técnicas v3.1/` | `scripts_v3.1_r3.tar.gz` (generador HEAD) · `referencias_regresion_v3.1_r3.zip` (raw/calc r3, Resumen calc, sombra, logs, cruce, evidencia Excel, SHA256SUMS) |
| `_borrador_v3.1/superadas/r2/` | libros r2, renders r2, copias `_prueba` r2, `scripts_v3.1.tar.gz` y `referencias_regresion_v3.1.zip` de r2 (nada borrado) |
| Raíz | **sin tocar**: `Modelo_FV_5MWp_GPM_v3.0.xlsx`, `…Resumen_Directorio_v3.0.xlsx`, `Renders PDF/`, `Fuentes técnicas/` |

Repo `gpm-artefacto`: commit `101716b` (main). Bundle del día en `Fuentes técnicas v3.1/` y push a GitHub desde su Mac (vía `gh`) al cierre del bloque.

## 5. Lo que necesito de usted (una palabra cada una)

1. **«sustituir»** → ejecuto la sustitución del raíz: `Modelo_FV_5MWp_GPM_v3.0.xlsx`, `…Resumen_Directorio_v3.0.xlsx`, `Renders PDF/*v3.0*` y `Fuentes técnicas/{scripts_v3.0.tar.gz, referencias_regresion_v3.0.zip}` → `_borrador_v3.0/superadas/` (o `superadas/v3.0/` bajo el raíz); r3 pasa al raíz como **`Modelo_FV_5MWp_GPM_v3.1.xlsx`** y **`…Resumen_Directorio_v3.1.xlsx`** (nombres sin sufijo de revisión, como la v3.0), renders a `Renders PDF/`, fuentes r3 a `Fuentes técnicas/`; reescribo `07 Nota de traspaso` para v3.1. Nada se borra. Antes de mover compruebo que ningún libro esté abierto en Excel.
2. **«promover»** → las dos URL oficiales reciben ola 1 · r4 (≡ libro r3), con `label` y conservando `db` en la interna.

Si prefiere revisar antes: el PDF del render r3 (66 págs.) es la lectura más rápida; los cambios están en las págs. 1 (portada: tornado), 7 (00b), 48–49 (tornado y nota (3)) y en la cabecera del Resumen.

## 6. Pendiente de la ola 1 (sin cambios respecto al doc 27 §4)

A4 · A5 (el cruce ya corre a demanda; falta integrarlo opcionalmente en `release.sh`) · A8 · A10 · A11 · C4/E3 · C5 · C6 · F1/F2 · E2 · B7 · B8 · F1-11 · `downloads` sin probar en el visor · `Documentación/01–22` al repo (lotes ≤ 8) · Jorge: enviar «Prueba de reglas (temporal)» a la papelera desde la UI oficial.

## 7. Fuentes

Contenedor: `/root/gpm13/out30/{Modelo_FV_5MWp_GPM_v3.1_r3*, Modelo_FV_5MWp_Resumen_Directorio_v3.1_r3*, r3_pipeline.log, r3_res_pipeline.log, cruce_r3/}`; `artefacto/publicados/2026-09-11_v2_ola_1_r4_libro_v3.1_r3/`; capturas `audit/out_r4/` (tornado, portada, Acerca de, ambas ediciones). Excel/Mac 16.110, macOS 26.5.2, AppleLocale en_EC. Todas las cifras de este documento se leyeron de los archivos indicados el 11/12-sep-2026.
