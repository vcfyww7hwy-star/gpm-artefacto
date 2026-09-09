# 24 · Estado verificado — Fase 0 del artefacto interactivo v2 (restauración y línea base)

**Proyecto:** Modelo FV 5,0 MWp Montecristi → Gran Piazza Machala (SALELGI S.A. · gerencia Exergy)
**Fecha:** 09-sep-2026, 17:49–18:05 UTC · **Autor:** Claude (Anthropic) para Exergy EXG S.A.S., a petición de Jorge A. Baquerizo
**Alcance:** Fase 0 del doc 23 §5–§6 (restaurar el entorno desde OneDrive y verificar la línea base). No se ejecutó ningún cambio sobre el artefacto ni sobre los libros. Un solo cambio de restauración en un script auxiliar (R-F0-1, §4).
**Numeración:** el doc 23 asignaba el 24 al «Diagnóstico y backlog v2» (F1); esta nota ocupa el 24 y desplaza F1 → 25, F2 → 26 (a ratificar).

## 1. Resultado en una línea

Entorno restaurado íntegramente desde los tarballs de OneDrive (SHA idénticos a los del doc 23 §1); línea base reproducida y **determinista**; los dos artefactos publicados contienen byte a byte los fragmentos F5 r1; cruce aleatorio 6/6 PASS con LibreOffice en este contenedor. Hallazgos nuevos: el raíz v3.0 cambió el 08-sep 23:54 UTC (§3), el smoke test tiene 3–4 aserciones obsoletas (§2.4), y tres piezas del entorno anterior no sobrevivieron o traían rutas absolutas (§4).

## 2. Verificación (todo reproducible en el contenedor)

| Paso (§6 doc 23) | Resultado | Esperado (doc 23) | Tiempo |
|---|---|---|---|
| Tarballs en OneDrive `_borrador_v3.1/Fuentes técnicas v3.1/` | 8 archivos; SHA **iguales** en Mac y contenedor: F5_r2 `96df467c…` · generador r3-pre `66e10314…` · cruce `244a3627…` · F5_r1 `ba3a5be3…` · refs `93175e94…` · scripts `a5515234…` · F4_r1 `84f254fa…` · extractores F1 `f5fb8dbb…` | Los cuatro primeros coinciden con el doc 23 §1; la memoria del proyecto tenía SHA anteriores para F5_r2 (`71371c9c…`) y generador (`1dfe3fc3…`) → corregida | — |
| Toolchain | Node 22.22.2 · pnpm 10.28.0 (`--frozen-lockfile`, 26 paquetes de nivel superior) · Python 3.11.15 + openpyxl 3.1.5 · LibreOffice `/usr/bin/soffice` + `recalc.py` · `bundle-artifact.sh` · Playwright 1.56 + chromium-1194 | Igual | 11 s |
| `engine: npx tsx test/verify.ts` | **PASS 91.546 celdas / 0 fuera** (abs 1e-6 · rel 1e-9 · params 1e-12) · `tsc` limpio | 91.546 / 0 | 1,0 s |
| `app: live.test` (data r2) | **PASS** — 106 nombres vivos iguales · 9 congelados «LIBRO» · 94 textos idénticos · 38 plantillas · capex 57 + 111/111 · opex 111/111 · 06_OPEX 6/6 | PASS | 0,8 s |
| `app: DATA_DIR=../data_r3pre live.test` | **PASS** | PASS | 0,8 s |
| `app: test/format.test.ts` | **73/73** (ya existe y cubre redondeo, negativos, miles, %, años, «x») → A6 del doc 23 estaba parcialmente desactualizado | no citado | 0,3 s |
| `app: tsc -b` | limpio | limpio | 9 s |
| `app: npm run build:editions` + `check:exclusion` | OK · interno **1.136.664 B** (SHA `af0275d5…`) · externo **1.096.431 B** (`47b07cf4…`) · CSP OK · marcador interno ×1 / ×0 · cadenas internas: ninguna · aviso previsto «link Google Fonts inyectado» | ≈ 1.098 / 1.059 «KB» (medidos en caracteres/1024 por `check-exclusion`; en bytes son 1.110 / 1.071 KiB) | 23 s |
| Determinismo del build | Segundo `build:interno` → **idéntico byte a byte** | no verificado antes | 12 s |
| Artefactos publicados (`Artifact read`) | INTERNO `6fb96cf4…` (☀️, privado, 1.131.143 B con esqueleto) y EXTERNO `dd6ec83a…` (🔆, privado, 1.090.955 B): ambos **contienen íntegros** los fragmentos F5 r1 del tarball (`9c7418a0…` / `8b8e4f76…`) → registrados en esta conversación para republicar | F5 r1 | — |
| Build actual vs publicado | Distintos (esperado): el build local es r2 + guardia R3-5 + `labels_f`; **no publicado** (D-X-2) | igual | — |
| `smoke.mjs` (Playwright, 20 comprobaciones × 2 ediciones) | 17/20 interno · 16/20 externo · **0 errores de consola/página** · fallos = aserciones obsoletas (§2.4) | no citado | 6 s/ed. |
| Cruce aleatorio `crosscheck_engine.py` (6 muestras, semilla 20260909, plantilla `refs/…v3.1_calc.xlsx` = r2) | **6/6 PASS** · 91.546 celdas/muestra · 0 fuera · 19–20 s/muestra | opcional | 115 s |

### 2.4 Smoke test: fallos explicados (no son regresiones)

| Comprobación | Espera | Encuentra | Causa |
|---|---|---|---|
| «vista inicial desde hash (#v=flujo)» | `h1 = "Flujo"` | `"Flujo de caja de SALELGI"` | Desde F4 el `h1` es el título de la hoja del libro; la prueba data de F3 |
| «paleta ⌘K navega a Riesgos» | `h1 = "Riesgos"` | `"Matriz de riesgos"` (⌘K sí navega: primer resultado `Riesgos #v=riesgos`) | Ídem |
| «host: vista renderizada» | `h1 = "Guía"` | `"Guía de lectura"` | Ídem |
| «host: título» (sólo externo) | título interno | `"Proyecto FV Montecristi → GPM"` (correcto) | Título interno codificado en la prueba |

Único error de red en el host: `fonts.googleapis.com` → `ERR_TUNNEL_CONNECTION_FAILED` (el contenedor no tiene salida; la interfaz cae a la pila de respaldo) — confirma E3 del doc 23.

## 3. Hallazgo: el raíz `Modelo_FV_5MWp_GPM_v3.0.xlsx` cambió (sólo lectura, sin abrir Excel)

| Dato | Valor |
|---|---|
| mtime / SHA actual | **08-sep-2026 23:54:13 UTC** · `2f36c34c…` (la memoria registraba `ff4443b9…` del 04/05-sep; el doc 23 cita un guardado a las 22:25 UTC) |
| Resumen v3.0 | intacto: `f321243e…` (04-sep 16:18 UTC) |
| Estructura | 16 hojas, 314 nombres, fórmulas por hoja idénticas al entregado salvo 01 (51 → 50: `Meses_Construccion` pasó de `=Mes_COD_Cron` a 21); filas insertadas 00 (+7) y 01 (+3) → 110 nombres desplazados (C23 → C26…), como en el 05-sep |
| Entradas del Custom ≠ entregado (10) | `Meses_Construccion` 21 · `Peaje_SGDA` 0 · `Disponibilidad` 0,97 · `Escalacion_CAPEX` 0 · `Degradacion_Adicional` 0,01 · `Fee_OM_kWp` 16 · `Escalacion_OPEX` 0,02 · `Pct_Apalancamiento` 1,00 · `Tasa_Deuda` 0,075 · **`Deuda_Financia_Terreno` «Sí»** (nueva) |
| Frente a la lista del 05-sep (ff4443b9) | Ya **no** difieren `Comprador_Terreno` (= Exergy) ni `Escalacion_Tarifa` (= 0); aparece `Deuda_Financia_Terreno = Sí`. Confianza **media**: no conservo la copia ff4443b9 para un diff directo; la comparación es contra el entregado `8814ce43…` |
| Valores en caché del raíz (Custom) | Estado_Custom «▲ Custom ≠ Base en 9 entrada(s)» · 76/77 ● · TIR 9,05 % · VAN −256.037 · TIR acc. 17,73 % · VAN acc. 250.451 · DSCR mín 0,639 · LCOE 108,0 · PB 7,5 · B_TIR 8,12 % |
| Implicación | El generador v3.1 (`V31`) tomó «los 10 valores de Jorge» del 05-sep; el Custom que Jorge tiene hoy en el raíz **ya no es ese** (3 diferencias). La coherencia artefacto ≡ libro se define frente a r2/r3, no frente al raíz explorado → decisión en G-L2 (§5, D-V2-8) |

## 4. Restauración: qué no sobrevivió y qué se corrigió

| ID | Hallazgo | Acción en F0 | Pendiente |
|---|---|---|---|
| R-F0-1 | `build30/crosscheck_engine.py:23` tenía la ruta absoluta del motor del contenedor anterior (`…/25ffeae2…/scratchpad/artefacto/engine`) → el cruce no arrancaba | Sustituida por `ENGINE_DIR` (variable de entorno) con respaldo relativo `../../artefacto/engine`; original conservado como `.orig`; diff en el tarball F0 | Llevar al generador HEAD (G2/G7) |
| R-F0-2 | `scratchpad/shots/host.mjs` y `f5.mjs` (capturas F4/F5) **no están en ningún tarball**; sólo sobreviven sus PNG y `fragment-host.html` en `artefacto_F5_r1_fuentes.tar.gz` | Ninguna (no se reconstruyen sin aprobación) | Reescribir dentro de A3/C1 (F1) |
| R-F0-3 | `smoke.mjs` depende de `/home/claude/.npm-global/lib/node_modules/playwright` (existe aquí) o `PLAYWRIGHT_MODULE` | Ninguna | Documentar en `BOOTSTRAP.md` (G7) |
| R-F0-4 | `out30/` del generador sólo trae `…_v3.1_r3pre.xlsx` + log; el `_raw`/`_calc` de r2 no están en los tarballs (sí el `_calc` en `referencias_regresion_v3.1.zip`, usado como plantilla del cruce) | Ninguna | Incluir `_raw` r2 en el próximo tarball o regenerarlo con `pipeline.sh` (H1) |
| R-F0-5 | `check-exclusion.mjs` informa tamaño en caracteres/1024 (`html.length`) y `to-fragment.mjs` en bytes → cifras distintas para el mismo archivo | Ninguna | Unificar en bytes (A9/G2) |

## 5. Estado de gates y decisiones tras F0

- **Abiertos (sin cambio):** G-L2 (r2 hoja por hoja → r3 → sustitución) · G2/G5 (15 vistas, F5, primera prueba real de `db`/`downloads`, alcance externo) · F6.
- **Nuevo, para G-L2 — D-V2-8:** ¿qué Custom es el canónico para r3: el `V31` del generador (lista del 05-sep) o el raíz actual (§3: Comprador_Terreno = Exergy, Escalacion_Tarifa = 0, Deuda_Financia_Terreno = Sí)? Mientras no se decida, el artefacto (r2) y el raíz explorado muestran Customs distintos.
- **Regla vigente:** el raíz v3.0 y el Resumen no se tocan; en F0 sólo se leyeron con openpyxl (copias en el contenedor).
- **Siguiente paso:** G-A (aprobación de visión, olas y decisiones D-V2-1…8) → F1 «Diagnóstico con evidencia» (doc 25).

## 6. Fuentes de esta fase (OneDrive `_borrador_v3.1/Fuentes técnicas v3.1/`)

`F0_restauracion_2026-09-09.tar.gz`: `BOOTSTRAP_F0.md` (comandos que funcionaron, en orden), `crosscheck_engine.py` parcheado + `.orig` + diff, `xcheck_f0/` (resumen.json y 6 muestras sin libros), `smoke_F0/` (salida y capturas de ambas ediciones), `probe.mjs`, `compara_raiz.py` + salida, `out_build_F0/` (fragmentos del build actual r2 + guardia + labels_f, `af0275d5…` / `47b07cf4…`, **no publicados**). Memoria del proyecto actualizada (`exergy-gpm-artefacto.md`).
