#!/bin/bash
# pipeline.sh NOMBRE_SALIDA — build v3.0 → check_estilo → check_print → recalc (LibreOffice) → check_errors → regress30 (por etiqueta) → sombra30 → inject_values
#   ESC_DEF=v20 (entorno): bloque B con la definición v2.0 y los parámetros de la ronda 2 en neutro → prueba R1 frente a gen_v20_calc (0 diferencias).
#   ESC_DEF=v30 (defecto): definición v3.0 (política del Base B) → R2 = informe de deltas frente a gen_v20_calc (o REF=… frente a otra referencia).
# Resultado: /root/gpm13/out30/NOMBRE_SALIDA.xlsx (con valores en caché) + NOMBRE_SALIDA_calc.xlsx (LibreOffice) + sombra_NOMBRE.csv
set -e -o pipefail
NAME=${1:-Modelo_FV_5MWp_GPM_v3.0}
OUT=/root/gpm13/out30
REF=${REF:-/root/gpm13/verif/gen_v20_calc.xlsx}
ALLOW=${ALLOW:-N_Controles,N_Controles_OK,N_Por_Confirmar_Esperado,N_Por_Confirmar}   # estructurales: pueden diferir frente a la v2.0
GONE=${GONE:-}
ROWS_GONE=${ROWS_GONE:-}
mkdir -p $OUT
cd /root/gpm13/build30
echo "· build (ESC_DEF=${ESC_DEF:-v30})"
python3 build_main.py $OUT/${NAME}_raw.xlsx | tail -1
python3 check_estilo.py $OUT/${NAME}_raw.xlsx --max 5 | tail -n +2 | head -20
python3 check_print.py $OUT/${NAME}_raw.xlsx | tail -1
cp $OUT/${NAME}_raw.xlsx $OUT/${NAME}_calc.xlsx
python3 /mnt/skills/public/xlsx/scripts/recalc.py $OUT/${NAME}_calc.xlsx 300 | grep -E '"status"|total_errors|total_formulas' | tr -d ' ,"' | paste -sd' '
# los únicos errores admitidos: NA() intencionales de los marcadores del año de cruce (portada, filas auxiliares)
python3 check_errors.py $OUT/${NAME}_calc.xlsx --allow "${ALLOW_ERR:-00_Portada!D103:AD104}" | tail -2
if [ -f "$REF" ]; then
  SAME=""; case "$(basename "$REF")" in *Resumen*|res_*) SAME="--same";; esac
  python3 regress30.py $REF $OUT/${NAME}_calc.xlsx --quiet $SAME ${ALLOW:+--allow $ALLOW} ${GONE:+--gone $GONE} ${ROWS_GONE:+--rows-gone "$ROWS_GONE"} | grep -E "nombres comparados|Motor:|permitido|✔|✖|    -" || true
fi
python3 shadow30.py $OUT/${NAME}_calc.xlsx $OUT/sombra_${NAME}.csv --blocks --quiet | tail -3
python3 inject_values.py $OUT/${NAME}_raw.xlsx $OUT/${NAME}_calc.xlsx $OUT/${NAME}.xlsx
ls -la $OUT/${NAME}.xlsx | awk '{print $5, $9}'
