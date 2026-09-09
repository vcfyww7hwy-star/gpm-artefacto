# Modelo FV 5,0 MWp Montecristi → GPM — generador Excel (build30) + artefacto interactivo

Repositorio privado de Exergy EXG S.A.S. (decisión D-V2-1, 09-sep-2026). Contiene el código; **los libros Excel con datos y los renders quedan en OneDrive** (`…/Modelo GPM 5MWp/`).

- `build30/` — generador del libro v3.1 (openpyxl), extractores (`extract_model.py`, `extract_book.py`), cruce aleatorio (`crosscheck_engine.py`, `ENGINE_DIR`), pipeline.
- `artefacto/engine/` — motor TypeScript ≡ LibreOffice (`npx tsx test/verify.ts`).
- `artefacto/app/` — aplicación React del artefacto (ediciones interna/externa; `pnpm install --frozen-lockfile`; `npm run build:editions`).
- `artefacto/data/`, `artefacto/data_r3pre/` — extracciones del libro (r2 y r3-pre).
- `docs/` — copia de `Documentación/` (la fuente canónica sigue en OneDrive).
- `ops/` — restauración del entorno (`BOOTSTRAP_F0.md`) y utilidades.
