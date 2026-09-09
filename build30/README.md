# Generadores v3.0 · Modelo FV 5 MWp Montecristi → GPM y Resumen Directorio (ronda 2 de motor)

Requisitos: Python 3.11, openpyxl 3.1.5, LibreOffice 24.x headless (`recalc.py` de la skill xlsx o `soffice --headless --convert-to xlsx`), pdfplumber (para `check_render.py`), poppler (`pdftoppm`, `pdfinfo`) sólo para mirar renders.
Rutas esperadas (ajustar al principio de `pipeline.sh` / `pipeline_res.sh`): generadores en `/root/gpm13/build30/`, salidas en `/root/gpm13/out30/`, referencias en `/root/gpm13/verif/` (`gen_v20_calc.xlsx` = modelo v2.0 recalculado, para R1).

## Modos del generador (variable de entorno `ESC_DEF`)
- `v30` (defecto) — definición v3.0 del bloque B (política B del doc 13: Base realista moderado) y los 9 parámetros nuevos en sus valores entregados.
- `v20` — definición v2.0 del bloque B **y los 9 parámetros nuevos en neutro** (disponibilidad 1, escalación 0, peaje kW 0, reemplazo No, utilidad gravable vacía, 12 meses, tasa accionista = tasa proyecto, desmantelamiento 0, degradación 0) → el libro reproduce la v2.0 celda a celda (prueba de invariancia R1 frente a `gen_v20_calc.xlsx`).
- `v13` — histórico (definición v1.3).

## Archivos
- `xl_helpers.py` — sistema visual (paleta, componentes, chips, tarjetas, plantillas de gráficos incl. `chart_cascade`, `setup_print`, `split_long_literals` para literales > 255 caracteres).
- `build_core.py` — constantes (INPUTS con las 9 entradas nuevas, ESCENARIOS = bloque B de 8 filas, RUBROS, vectores canónicos, layouts `ENERGIA/CAPEX/OPEX/FISCAL/FLUJO/EXERGY`), hojas 04–09 y el **Motor** (`build_motor`: 110 casos; `PARAM_ROWS` 5–33, `SCAL_ROWS` 34–55 con fEsc/Krep/Decom, `OUT_ROWS` 56–71, 28 bloques anuales desde la fila 74 incl. Krep/PoolU/PoolL).
- `build_content.py` — índices de casos (`CASE_X/C/B/F`, tornado `T_*` incl. `T_DISP/T_ESCK/T_PKW/T_UG/T_REP`, puente `BR0–BR5`, `N_CASES` 110), `build_cases`, `TORNADO` (14 barras) y ranking, 02, 03, 11, 12 (§A generado desde INPUTS/ESCENARIOS, §B, §C, §D, §E), 13 (77 controles: A–G, **H · Ronda 2** H1–H13, **I · Libro** I1–I3; H1/H4/H5 comparan año a año, sin `TRANSPOSE`).
- `build_supuestos30.py` — 01 (panel de mandos, bloques A–J, bloque B de 8 filas, referencias ocultas, `Estado_Custom`, `Estado_Entregado`, `N_Neutro`/`Estado_Neutro`).
- `build_sens30.py` — 10 (§A los cuatro casos, **§A.3 puente + cascada**, §A.2 P50/P90, §B tornado ordenado, §C–§H incl. §G.2 reemplazo).
- `build_portada30.py` — 00 (tarjetas + tira C·B·F, tornado top-9 desde el ranking, siete conclusiones incl. el puente, p. 3 los cuatro casos).
- `build_guia.py` — 00b (el libro en cinco minutos, convenciones a dos columnas, FAQ 6, glosario de 31 términos a una línea; 4 páginas).
- `build_main.py SALIDA.xlsx` — orquestador del modelo. `build_resumen30.py SALIDA.xlsx [--ref MODELO_calc.xlsx]` — Resumen Directorio (mismo `build_motor`; hoja oculta `Inputs` con los escalares que Supuestos no muestra y `Inputs_Mark`; `Ref_*` y `Meses_Construccion` del modelo recalculado; puente en Resultados).
- `check_estilo.py` (0 hallazgos), `check_print.py` (paginación Excel/Mac: 6,05 pt/carácter, filas −1 pt, áreas de impresión en dos rangos), `check_errors.py` (lista blanca `00_Portada!D103:AD104`), `check_render.py RENDER.pdf [--budget …] [--strict]` (V10: páginas por hoja vs presupuesto doc 13 §9, cortes = x0 < ancho < x1, texto fuera de la caja informativo, páginas vacías).
- `regress30.py REF NEW [--tol] [--same] [--allow n1,n2] [--gone …] [--rows-gone …]` — regresión por **etiqueta de fila** del Motor y nombre de caso (sobrevive a inserciones de filas); `--same` para modelo vs Resumen.
- `shadow30.py LIBRO_calc.xlsx salida.csv [--blocks] [--tol] [--quiet]` — sombra Python independiente (lee los 9 parámetros nuevos por etiqueta y los drivers por nombre `Drv_*`; 110 casos, 28 bloques).
- `r2_report.py REF_v20_calc NEW_v30_calc SALIDA.txt` — informe de deltas R2 mapeado a los M del doc 13 (KPI antes/después, puente por escalón, nombres por familia, Motor por bloque).
- `try_inputs.py RAW SALIDA_calc Nombre=valor|Hoja!Celda=valor … [--shadow] [--quiet]` — prueba de uso en LibreOffice (valores por nombre o por celda; KPI de los cuatro casos, controles no ●, sombra).
- `inject_values.py` (valores calculados como caché), `pipeline.sh [NOMBRE]` (build → estilo → paginación → recalc → errores → regress30 → sombra → inject), `pipeline_res.sh [NOMBRE]` (Resumen; `MODEL=` el modelo recalculado).
- `regress20.py`, `shadow20.py` — herramientas de la v2.0 (referencia).

## Reproducir la entrega v3.0
```
cd /root/gpm13/build30
./pipeline.sh Modelo_FV_5MWp_GPM_v3.0                       # → out30/Modelo_FV_5MWp_GPM_v3.0.xlsx (+ _raw, _calc, sombra); regress30 vs gen_v20_calc = informe R2 (deltas intencionales)
./pipeline_res.sh Modelo_FV_5MWp_Resumen_Directorio_v3.0    # → out30/…Resumen_Directorio_v3.0.xlsx; regress30 --same vs el modelo (0 diferencias)
ESC_DEF=v20 ./pipeline.sh Modelo_FV_5MWp_GPM_v30_neutro     # invariancia R1: 0 diferencias frente a gen_v20_calc.xlsx (68.469 celdas del Motor por etiqueta, 288 nombres)
python3 r2_report.py /root/gpm13/verif/gen_v20_calc.xlsx out30/Modelo_FV_5MWp_GPM_v3.0_calc.xlsx out30/R2_informe_deltas.txt
python3 check_render.py "RENDER (render Excel).pdf"          # tras cada render en Excel/Mac
```
Protocolo de cambios de motor (doc 09 / 11 / 13): implementar en 04–09 + Motor + `shadow30` a la vez, control nuevo en 13, fuente en 12, término en 00b, entrada en 01 con «· por confirmar» si aplica; **primero en neutro** (R1 = 0), después re-basing; `r2_report` como informe de deltas; tres motores (LibreOffice, sombra, Excel real por el conector sobre una copia `…_prueba.xlsx`); render en Excel/Mac + `check_render`; documentación.

Lecciones de esta ronda: `TRANSPOSE` dentro de `SUMPRODUCT` devuelve `#VALUE!` en Excel/Mac sin fórmula matricial (LibreOffice lo acepta) → comparar año a año; los saltos de fila manuales son globales y partían las páginas de años (segundo rango del área de impresión) → el salto va antes de la fila de años; Excel/Mac emite fuera de la caja de página las celdas auxiliares de gráficos ajenas al área de impresión (no se imprimen).
