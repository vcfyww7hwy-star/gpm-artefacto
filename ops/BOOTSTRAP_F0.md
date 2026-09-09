# BOOTSTRAP_F0 — restauración del entorno del artefacto interactivo (verificado 09-sep-2026)

Precursor de `BOOTSTRAP.md` (G7). Comandos que funcionaron, en orden. `SP` = scratchpad del chat; `UP` = carpeta de staging.

1. Traer desde OneDrive (`device_stage_files`) `…/Modelo GPM 5MWp/_borrador_v3.1/Fuentes técnicas v3.1/`:
   `artefacto_F5_r2_fuentes.tar.gz` (96df467c…) · `build30_r3pre_generador_2026-09-08.tar.gz` (66e10314…) ·
   `referencias_regresion_v3.1.zip` (93175e94…) · `scripts_v3.1.tar.gz` (a5515234…) · `artefacto_F5_r1_fuentes.tar.gz` (ba3a5be3…; fragmentos publicados en `app/out/`) ·
   `cruce_aleatorio_motor_2026-09-08.tar.gz` (244a3627…). Comprobar `sha256sum` a ambos lados.
2. Descomprimir:
   `mkdir -p $SP/artefacto $SP/v31 && tar xzf artefacto_F5_r2_fuentes.tar.gz -C $SP/artefacto` (→ app, engine, data, data_r3pre)
   `tar xzf build30_r3pre_generador_2026-09-08.tar.gz -C $SP/v31` (→ build30, out30 con r3pre) · `mkdir $SP/v31/refs && unzip referencias_regresion_v3.1.zip -d $SP/v31/refs`
   `ln -sfn $SP/v31 /root/gpm13`
3. Dependencias: `cd engine && npm install` (7 paquetes, 1 s) · `cd app && pnpm install --frozen-lockfile` (9 s; pnpm 10.28 ya en /opt/node22/bin). Node 22.22.2. Python 3.11 + openpyxl 3.1.5 ya presentes. LibreOffice `/usr/bin/soffice`; `recalc.py` en `/mnt/skills/public/xlsx/scripts/`; `bundle-artifact.sh` en `/mnt/skills/examples/web-artifacts-builder/scripts/`. Playwright global en `/home/claude/.npm-global/lib/node_modules/playwright` (navegadores en `/opt/pw-browsers`).
4. Línea base: `cd engine && npx tsx test/verify.ts` (91.546/0) · `cd app && npx tsx test/live.test.ts` (PASS) · `DATA_DIR=../data_r3pre npx tsx test/live.test.ts` (PASS) · `npx tsx test/format.test.ts` (73/73) · `npx tsc -b` · `npm run build:editions` (interno 1.136.664 B af0275d5… · externo 1.096.431 B 47b07cf4…; determinista) · `node scripts/smoke.mjs interno|externo` (aserciones h1 obsoletas desde F4, ver doc 24 §2.4).
5. Cruce aleatorio: `ENGINE_DIR=$SP/artefacto/engine python3 build30/crosscheck_engine.py $SP/v31/refs/Modelo_FV_5MWp_GPM_v3.1_calc.xlsx $SP/xcheck N SEMILLA` (≈ 19 s/muestra). El `_raw` de r2 no está en los tarballs; el `_calc` de refs sirve de plantilla.
6. Artefactos: `Artifact action:"read"` de https://claude.ai/code/artifact/6fb96cf4-613a-4649-ad0c-96704dc4d271 (interno) y …/dd6ec83a-940b-4a4c-ac9b-5f9e2bd2cda7 (externo) antes de republicar. Republicar con `url`, `label`, sin cambiar favicon ni `capabilities`.
7. No sobrevivieron: `shots/host.mjs`, `shots/f5.mjs`; `out30/*_raw|_calc` de r2 (sí en refs).
