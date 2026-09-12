#!/usr/bin/env python3
"""make-oracle.py — regenera, a partir de la extracción del libro (artefacto/data/), los dos JSON del modelo que no salen de extract_book.py:

  src/model/inputs_v31.json   entradas del libro (copia de engine/data/inputs_v31.json, que escribe engine/test/verify.ts)
  src/model/oracle_v31.json   oráculo del auto-chequeo «Motor ≡ Excel»: las 16 salidas de los 111 casos tal como las recalculó
                              LibreOffice (data/motor.json) + versión, fecha de análisis y SHA-256 del libro (data/meta.json)

Uso (desde artefacto/app/): python3 scripts/make-oracle.py        (DATA_DIR opcional; por defecto ../data)
Cadena r3 (ops/BOOTSTRAP.md §6): extract_model → extract_book → cp book.json → verify.ts (escribe inputs) → make-oracle → make:externo → release.sh
Antes de r3 este archivo se generaba con un script ad hoc no conservado (hallazgo 11-sep-2026); la regla de conversión se comprobó
contra el oracle_v31.json de r2: 111 casos × 16 salidas idénticos.
"""
import json, os, shutil, sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.abspath(os.environ.get("DATA_DIR", os.path.join(APP, "..", "data")))
ENGINE = os.path.abspath(os.environ.get("ENGINE_DIR", os.path.join(APP, "..", "engine")))
MODEL = os.path.join(APP, "src", "model")

motor = json.load(open(os.path.join(DATA, "motor.json"), encoding="utf-8"))
meta = json.load(open(os.path.join(DATA, "meta.json"), encoding="utf-8"))
labels = motor["labels"]["outputs"]
oracle = {
    "version": meta["version"],
    "fecha_analisis": meta["fecha_analisis"],
    "calc_sha256": meta["calc"]["sha256"],
    "raw_sha256": meta["raw"]["sha256"],
    "outputLabels": labels,
    "cases": [{"name": c["name"], "outputs": [c["outputs"][lab] for lab in labels]} for c in motor["cases"]],
}
json.dump(oracle, open(os.path.join(MODEL, "oracle_v31.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

src_inputs = os.path.join(ENGINE, "data", "inputs_v31.json")
if not os.path.exists(src_inputs):
    sys.exit(f"falta {src_inputs}: ejecute antes `npx tsx test/verify.ts` en engine/ (sin DATA_DIR) para que escriba las entradas del libro")
shutil.copyfile(src_inputs, os.path.join(MODEL, "inputs_v31.json"))
inputs = json.load(open(src_inputs, encoding="utf-8"))
print(f"oracle_v31.json: {len(oracle['cases'])} casos × {len(labels)} salidas · libro {oracle['version']} · calc {oracle['calc_sha256'][:16]}…")
print(f"inputs_v31.json: {len(inputs)} entradas (Sens_EscTarifa = {inputs.get('Sens_EscTarifa')})")
