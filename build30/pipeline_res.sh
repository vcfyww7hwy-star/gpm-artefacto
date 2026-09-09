#!/bin/bash
# pipeline_res.sh NOMBRE — build Resumen v3.0 (motor unificado) → check_estilo → check_print → recalc (0 errores) → regress30 --same vs el
# modelo completo v3.0 recalculado (Motor idéntico por etiqueta) → inject_values
set -e -o pipefail
NAME=${1:-Modelo_FV_5MWp_Resumen_Directorio_v3.0}
OUT=/root/gpm13/out30
MODEL=${MODEL:-/root/gpm13/out30/Modelo_FV_5MWp_GPM_v3.0_calc.xlsx}
mkdir -p $OUT
cd /root/gpm13/build30
python3 build_resumen30.py $OUT/${NAME}_raw.xlsx --ref $MODEL | tail -1
python3 check_estilo.py $OUT/${NAME}_raw.xlsx --max 5 | tail -n +2 | head -12
python3 check_print.py $OUT/${NAME}_raw.xlsx | tail -1
cp $OUT/${NAME}_raw.xlsx $OUT/${NAME}_calc.xlsx
python3 /mnt/skills/public/xlsx/scripts/recalc.py $OUT/${NAME}_calc.xlsx 300 | grep -E '"status"|total_errors|total_formulas' | tr -d ' ,"' | paste -sd' '
python3 check_errors.py $OUT/${NAME}_calc.xlsx | tail -1
python3 regress30.py $MODEL $OUT/${NAME}_calc.xlsx --tol 1e-6 --quiet --same | grep -E "nombres comparados|Motor:|✔|✖|    -"
python3 inject_values.py $OUT/${NAME}_raw.xlsx $OUT/${NAME}_calc.xlsx $OUT/${NAME}.xlsx
ls -la $OUT/${NAME}.xlsx | awk '{print $5, $9}'
