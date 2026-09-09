# BOOTSTRAP — restaurar el entorno del artefacto interactivo desde cero (G7 · v1, 09-sep-2026)

Objetivo: en < 15 min, un contenedor nuevo vuelve a construir, verificar y publicar candidatos. Todo lo necesario está en este
repositorio (código) y en OneDrive (`…/Modelo GPM 5MWp/_borrador_v3.1/Fuentes técnicas v3.1/`: libros, extracciones, tarballs).

## 1. Código
- Con GitHub: `git clone <repo> gpm && cd gpm`.
- Sin GitHub (bundle en OneDrive): `git clone gpm-artefacto_<fecha>.bundle gpm && cd gpm` (`git bundle verify` antes).

## 2. Dependencias (contenedor de Cowork: Node 22, pnpm 10, Python 3.11 + openpyxl, LibreOffice, Playwright global)
```
cd artefacto/engine && npm install
cd ../app && pnpm install --frozen-lockfile
```
Rutas fijas que usan los scripts: `/mnt/skills/public/xlsx/scripts/recalc.py` (LibreOffice headless), `/mnt/skills/examples/web-artifacts-builder/scripts/bundle-artifact.sh`
(`npm run build:bundle`), Playwright en `/home/claude/.npm-global/lib/node_modules/playwright` (o `PLAYWRIGHT_MODULE`), navegadores en `/opt/pw-browsers`.

## 3. Línea base (≈ 1 min)
```
cd artefacto/engine && npx tsx test/verify.ts          # 91.546 celdas / 0 fuera
npx tsx test/irr_excel.test.ts                         # TIR ≡ Excel (D-V2-9) 13/13
cd ../app && npx tsx test/live.test.ts && npx tsx test/format.test.ts && npx tsc -b
```

## 4. Release completa (≈ 1 min) — G2
```
cd artefacto/app && bash scripts/release.sh "<etiqueta>"
```
→ verify · irr · live · format · tsc · build:editions (+check:exclusion) · smoke (22 × 2) · SHA · `publicados/<fecha>_<etiqueta>/` · `out/candidato/*.fragment.html`.

## 5. Publicar (herramienta Artifact de Cowork)
1. Candidatos: `out/candidato/interno.fragment.html` → 🧪 https://claude.ai/code/artifact/aaa702aa-cdd2-4da6-8496-5e584b9e6521 (capabilities `{db: {rules: [{path: "", read: "interact", write: "admin"}]}, downloads: true}`) ·
   `out/candidato/externo.fragment.html` → 🔬 https://claude.ai/code/artifact/6cae17ba-e4ca-44b1-bf4c-6a59a7b035a0 (`{downloads: true}`). Siempre con `label`.
2. Con la palabra «promover» de Jorge: `out/interno/fragment.html` → oficial ☀️ https://claude.ai/code/artifact/6fb96cf4-613a-4649-ad0c-96704dc4d271 y
   `out/externo/fragment.html` → oficial 🔆 https://claude.ai/code/artifact/dd6ec83a-940b-4a4c-ac9b-5f9e2bd2cda7 con `url` + `label` (antes hay que haber leído cada URL con `Artifact read` en la conversación).
3. Guardar el fragmento publicado en `publicados/` (G9) y anotar el SHA en el doc de la ola.

## 6. Actualizar el libro (cuando haya r3): cadena de extracción
```
REF=/root/gpm13/out30/…_calc.xlsx ./build30/pipeline.sh Modelo_FV_5MWp_GPM_v3.1_r3          # libro (generador)
python3 build30/extract_model.py RAW CALC artefacto/data && python3 build30/extract_book.py artefacto/data artefacto/data/book.json
cp artefacto/data/book.json artefacto/app/src/model/book_v31.json && cd artefacto/engine && npx tsx test/verify.ts && cd ../app && npm run make:externo && bash scripts/release.sh "r3"
```
Cruce aleatorio (LibreOffice, ~20 s/muestra): `ENGINE_DIR=$PWD/artefacto/engine python3 build30/crosscheck_engine.py <RAW o _calc> <out> 24 <semilla>`.

## 7. Reglas que no cambian
Nada se publica sin pasar por `release.sh`; el raíz v3.0 y el Resumen no se tocan hasta G-L2; Excel en el Mac sólo con aviso; capturas sólo en el contenedor;
cada bloque termina con doc numerado en `Documentación/`, fuentes en OneDrive (bundle/tarball) y memoria del proyecto actualizada.
