# 27 · Changelog v2 — ola 0 cerrada y ola 1 · r2 en candidatos

**Proyecto:** Modelo FV 5,0 MWp Montecristi → Gran Piazza Machala (SALELGI S.A. · gerencia Exergy)
**Fecha:** 09-sep-2026 · **Autor:** Claude (Anthropic) para Exergy EXG S.A.S. · **Régimen:** G-A dado; «promover. sigue con todo… continúa bajo tu criterio» (Jorge, 09-sep) — promoción a las URL oficiales sigue siendo su palabra por ola (D-V2-4).
**Antecedentes:** docs 23 (plan v2), 24 (F0), 25 (diagnóstico), 26 (visión y olas).

## 1. Estado

| Bloque | Estado |
|---|---|
| Hotfix F1-01/F1-04 (candidatos r1) | **Promovido** a las dos URL oficiales el 09-sep («F5 r2 · hotfix F1-01 (promovido 09-sep)»; fragmentos `1917f7fe…` / `8ccecf03…`) |
| Ola 0 | Cerrada salvo H1 (G-L2, Jorge), GitHub (Jorge crea el repo) y A1 (requiere sesión en el panel del navegador) |
| Ola 1 · r2 | **Construida, verificada y publicada en los candidatos** 🧪 (interno, con reglas `db`) y 🔬 (externo) · pendiente «promover» |

## 2. Ola 0 — resultados

| ID | Resultado |
|---|---|
| **A2** | **Cerrada con hallazgo.** Excel/Mac 16.110 sobre la serie s19/M41: **−5,4876 %** con cualquier semilla; LibreOffice −303,36 % (espuria); motor anterior «n/a». Segunda tanda (A2b) con 4 series × 3 semillas (12 valores leídos de Excel por AppleScript): Excel devuelve la raíz real cuando es **única** en el dominio (PISO −7,2805 %, M41, M51 −6,4815 %) y **#NUM!** cuando hay varias raíces y Newton no converge (Conservador de s19: −30,5 % y −19,3 %; desde −0,5 devuelve −30,5 %). Libros temporales: `_borrador_v3.1/pruebas/IRR_prueba_Excel_2026-09-09{,b}.xlsx`. Ningún libro de Jorge tocado. |
| **D-V2-9** (nueva, a ratificar) | **Motor ≡ Excel:** Newton desde la semilla (LibreOffice) si converge en dominio; si converge fuera del dominio o no converge, raíz **única** en (−99 %, +1.000 %) por bisección; varias raíces → «n/a». `irr_excel.test.ts`: **12/12** frente a Excel + invariante VAN(TIR) ≈ 0 en las 333 TIR finitas de la línea base. `verify.ts` 91.546/0 sin cambios; las divergencias «oráculo LibreOffice n/a o espuria vs motor/Excel finito» se aceptan como **explicadas** (s19: 4). Consecuencia para el libro: la fórmula `IF(IRR(EQ;0,02)<=-1;"n/a";IRR(EQ;0,02))` (R3-5) en **Excel** ya da la raíz real; sólo LibreOffice necesita la guardia → R3-5 se mantiene como red de seguridad. |
| **A6** | Mac de Jorge: `AppleLocale = en_EC` (idiomas en-EC, es-EC; macOS 26.5.2). Excel muestra `$4,120,481`, `10.64%` (render r2 comprobado); el artefacto muestra es-EC `4.120.481`, `10,64 %`; los textos literales del libro usan la convención española («0,2 %/año», «9,33 %»). **Recomendación:** mantener D-F4-1 (es-EC) y declararlo en «Acerca de» (hecho). |
| A1 | No ejecutada: el panel del navegador de la app no tiene sesión en claude.ai (Claude no introduce credenciales). Se ejecuta en cuanto Jorge inicie sesión ahí. |
| G7 | `ops/BOOTSTRAP.md` definitivo en el repo (restauración < 15 min, release, publicación, cadena r3). |
| G1 | Repo git con 7 commits; bundle en OneDrive. Token GitHub de la sesión = proxy ligado a repos configurados (no crea repos); sin conector GitHub. **Jorge:** crear repo privado vacío y pasar la URL. |

## 3. Ola 1 · r2 — cambios (todos en los candidatos)

| ID | Cambio | Verificación |
|---|---|---|
| F1-02 | `--ink-3` #8B94A3 → **#676E7A** (4,71:1 sobre `--bg`, 5,14:1 sobre blanco); oscuro #6F7987 → **#88919D** (5,89 / 5,07:1); `--info` → #666F7C; sobre celdas resaltadas el gris terciario pasa al secundario | Auditoría: textos < 4,5:1 de **40+/vista → 0** en ambos temas (120 combinaciones) |
| F1-03 | Chip «LIBRO» 8,5 → 10 px; glifos de estado 9 → 10 px | 0 elementos < 10 px (antes 90 en Controles) |
| F1-05 | CAPEX: nombres de rubro en 2 líneas, total sin recorte | 0 textos recortados |
| F1-10 | `DataTable`: sombras de desplazamiento (CSS, sin JS) en tablas más anchas que su contenedor | Captura `r2-energia-tabla-scroll.png` |
| F4 | `prefers-reduced-motion: reduce` desactiva animaciones y transiciones | CSS |
| A7 / F1-08 | `ViewErrorBoundary` por vista: el resto de la aplicación sigue operativo; botón «Copiar diagnóstico» (edición, libro, SHA, vista, caso, error, entradas JSON); «Reintentar» | tsc; render normal sin cambios |
| A9 / G4 | El chip «Motor ≡ Excel» abre **«Acerca de esta versión»**: edición, versión del artefacto, libro y fecha de análisis, extracción, SHA del cálculo, oráculo, convención numérica, regla de la TIR, **entradas ≠ libro** con «volver al libro», historial de versiones (changelog embebido) | Captura `r2-acerca-de.png` |
| G5 / D-V2-5 | Candidato interno publicado con `db.rules = [{path: "", read: "interact", write: "admin"}]`; **borrado lógico** (`eliminado: fecha`) con **papelera** y «restaurar»; mensajes claros cuando un lector sin permiso intenta escribir | Pendiente de A1 en el visor real |
| B6 | Botón «Copiar enlace» en la barra (vista + caso + escenario + foco viajan en el hash) | — |
| A3 / F1-12 | `smoke.mjs`: aserciones corregidas + barrido de las 15 vistas (sin AST, sin desborde) — **22/22** en ambas ediciones; control negativo detecta F5 r1 | Corre en `release.sh` |
| G2 | `scripts/release.sh "<etiqueta>"`: verify → irr → live → format → tsc → build:editions → smoke → SHA → `publicados/` → candidatos; **50 s** | Ejecutado para r2 |
| G9 | `publicados/2026-09-09_v2____ola_1____r2/` con fragmentos, informes y `SHA256SUMS.txt` | En el repo |

**Fragmentos r2:** interno `d869d5cb…` (1.147.033 B) · externo `da5c580a…` (1.106.832 B). Candidatos = mismos fragmentos con `<title>` «Candidato · …». Contrato de los candidatos 0.2.44 (oficiales 0.2.42; la promoción conserva el pin del oficial).

## 4. Pendiente de la ola 1 (r3 de la ola)

A4 (invariantes ampliadas + 79 controles de 13 recalculados con el motor) · A5 (cruce de 24 muestras en `release.sh`, opcional por tiempo) · A8 (tabla única de rangos) · A10 (PDF por vista) · A11 (humo tras publicar) · C4/E3 (decisión de fuentes) · C5 (QA oscuro con capturas) · C6 · F1/F2 (teclado, `<title>` en gráficos) · E2 · B7 · B8 · F1-11.

## 5. Decisiones para ratificar (Jorge, una palabra cada una)

- **«promover» r2** → las dos URL oficiales reciben la ola 1 · r2 (incluye las reglas `db` en la interna).
- **D-V2-9** (TIR ≡ Excel) — recomendación: ratificar; ya está probada contra 12 valores de su Excel.
- **A6 / D-F4-1** — recomendación: mantener es-EC.

## 6. Fuentes

Repo: commits `c3f410d` (F1-01), `fdd6e4b` (smoke), `5212ec8` (D-V2-9), `6f1d828` (ola 1 r2); bundle `gpm-artefacto_2026-09-09.bundle` (OneDrive, `Fuentes técnicas v3.1/`). Capturas r2 en `F1_auditoria_2026-09-09_capturas_claro.tar.gz` (ya en OneDrive) y `ola1_r2_capturas` (repo `publicados/`). Memoria del proyecto actualizada.
