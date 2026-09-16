# 30 · Pendientes y hoja de ruta tras la entrega v3.1 / artefacto ola 1 · r4

**Proyecto:** Modelo FV 5,0 MWp Montecristi → Gran Piazza Machala (SALELGI S.A. · gerencia Exergy)
**Fecha:** 16-sep-2026 · **Autor:** Claude (Anthropic) para Exergy EXG S.A.S. · **Pregunta de Jorge:** «¿queda algo por hacer? deja un listado claro»
**Fuentes:** doc 25 §4 (backlog con IDs y esfuerzo S/M/L), doc 26 §3 (olas y criterios de aceptación), doc 27 §4, doc 29 §6, doc 07 (12-sep) §6, memoria del proyecto. Estado leído de los archivos el 16-sep-2026.

## 0. Qué está cerrado (nada en vuelo)

Libro **v3.1** y Resumen en el raíz (SHA `3d85da4d…` / `35ea3d1f…`), renders y fuentes en su sitio, v3.0 en `superadas/` y `referencia_v3.0/`; artefacto **ola 1 · r4 ≡ libro v3.1** en las dos URL oficiales; repo GitHub `cbcdb0a`; docs 07 (12-sep), 29; memoria del proyecto al día. No hay ningún trabajo a medias en el contenedor: todo lo reutilizable está en el repo, los bundles y `Fuentes técnicas`. Si este chat desaparece, el arranque es el §7 del doc 07.

## 1. Depende de Jorge (lo único que yo no puedo hacer)

| # | Qué | Por qué usted | Esfuerzo |
|---|---|---|---|
| J1 | Enviar a la papelera el escenario **«Prueba de reglas (temporal)»** en el artefacto interno oficial (Escenarios → papelera); opcional: confirmar que ve «Prueba A1» en el candidato 🧪 | La herramienta de publicación no puede modificar documentos existentes del `db` (exige una versión que no expone) | 1 min |
| J2 | **Lote de puntos** sobre el artefacto oficial r4 cuando lo use (numerados, por vista), y opcionalmente 10 min de **E2** a mano: abrir el interno en Safari, en la app Claude del Mac y en el móvil (sólo mirar; D-V2-3 deja el móvil fuera del alcance) | Las herramientas del contenedor no llegan al iframe del visor real | 10–20 min |
| J3 | **`downloads` en el visor real**: pulsar «Exportar CSV/JSON» e «Imprimir» en el oficial y decirme si descarga/abre | Misma razón que J2 | 2 min |
| J4 | **Datos por confirmar** que cambian el Custom (no la herramienta): certificación ambiental previa para la deducción adicional (RLRTI 28.6.g); garantía de disponibilidad del O&M (97/98 %); escalación de precios del CAPEX; cotización del reemplazo de inversores (0,06 $/Wac); utilidad gravable de SALELGI; componente por potencia del peaje (art. 5.17); capacidad del alimentador (3.800 kW) / factibilidad CNEL Manabí; D.E. 32; consultas SRI #17/#18 y CEPAI #19; term sheet de la deuda | Son datos de terceros | — |
| J5 | **H2 — observaciones abiertas del modelo** (doc 28): margen O&M de Exergy en 0, 04!D74/D75, memo estático de 03, F10 en ▲ | Decisiones de contenido, no de forma | 15 min |
| J6 | Decisión **C4/E3 — fuentes**: (a) embeber un subconjunto de IBM Plex (≈ 150–250 KB más por fragmento; funciona sin red) o (b) mantener Google Fonts con respaldo del sistema (hoy). Mi recomendación: **(a) sólo si el artefacto va a abrirse en redes que bloquean `fonts.googleapis.com`**; si no, (b) | Trade-off tamaño ↔ independencia de red | 1 palabra |
| J7 | **Limpieza** (Claude no borra): cuando quiera, eliminar `_borrador_v3.1/superadas/{r1,r2,raiz_v3.0}`, `_borrador_v3.1/pruebas/` y los tarballs antiguos de `Fuentes técnicas v3.1/` (F0/F1, bundles del 09 y 11-sep). Todo lo vigente está en el raíz, en `referencia_v3.0/` y en GitHub | Regla del proyecto | 5 min |
| J8 | Opcional: añadir el repo `gpm-artefacto` a las fuentes de la sesión de Claude para que el push no pase por su Mac | Hoy el push funciona vía `gh` en su Mac; sólo comodidad | 2 min |

## 2. Pendiente mío — cierre de la **ola 1 «Sólido»** (doc 26 §3; se ejecuta bajo «sigue a tu criterio», termina con doc 31 y su «promover»)

| ID | Qué falta exactamente | Criterio de aceptación | Esfuerzo | Necesita |
|---|---|---|---|---|
| A3 (ampliación) | E2E completo: 15 vistas × 4 casos × 2 temas × 2 ediciones; KPI ≡ motor en cada vista; CSV ≡ tabla; hash ida y vuelta; presets ≡ memo. Hoy: `smoke.mjs` 22 comprobaciones por edición | 100 % verde en `release.sh` | M | — |
| A4 | Invariantes del motor (VAN(TIR)≈0 ya está; faltan: Σ bloques ≡ escalares, DSCR con deuda 0 → «n/a», payback monotónico, etc.) + los **79 controles de 13_Controles recalculados por el motor** y comparados con el libro | 1.000 muestras aleatorias sin violación; controles ≡ libro en la línea base | M | — |
| A5 | Cruce aleatorio en `release.sh` (hoy corre a demanda: 8/8 el 11-sep) | Informe por release (24 muestras, semilla por versión) | S | ~10 min por release |
| A8 | Tabla única de rangos/validaciones de los mandos, tomada del libro o documentada, compartida por Mandos y cruce | Un solo archivo de rangos; Mandos no permite valores fuera de rango | S–M | propuesta mía → usted valida |
| A10 | Impresión por vista verificada con Chromium `page.pdf()` | PDF por vista sin cortes de tabla | S | — |
| A11 | Humo tras publicar: abrir la URL pública del candidato y comprobar título, edición, chip ≡, 0 errores | Automático tras cada publicación | S | acceso al visor desde el contenedor (comprobar) |
| C4/E3 | Ejecutar la decisión J6 (+ `size-adjust` para evitar el salto de fuente) | Sin FOUT perceptible | S | J6 |
| C5 | QA del tema oscuro con el validador de paleta y capturas | AA en ambos temas (hoy 0 fallos en 120 combinaciones, sin capturas del oscuro archivadas) | S | — |
| C6 | Iconografía y microcopy: un solo set de iconos, verbos consistentes en botones y menús | Revisión de las 15 vistas | S | — |
| F1/F2 | Teclado y accesibilidad: foco visible y navegación por teclado en los gráficos, `<title>` SVG en todos (hoy sólo el tornado), auditoría axe | Auditoría sin errores serios | S–M | — |
| F1-11 | `check-exclusion.mjs` en bytes (hoy caracteres/1024) | Unidad única | S | — |
| E2 | Matriz de navegadores: Chromium y WebKit en el contenedor (Playwright); Safari/Chrome/Edge/app Claude a mano (J2) | Tabla con resultado por navegador | S | J2 |
| B7 | ⌘K ampliado: fuentes, rubros CAPEX, líneas OPEX, salidas del Motor | Presentes y probados en E2E | S | — |
| B8 | Explicaciones al pasar el cursor por «n/a», «LIBRO», «▲» | Presentes y probados en E2E | S | — |
| G1 (resto) | `Documentación/01–22` al repo (lotes ≤ 8 archivos por el enlace del Mac); opcional CI en GitHub (tsc + verify; el generador necesita LibreOffice, mejor fuera de CI) | Docs en `docs/`; CI verde | S | enlace del Mac |
| Cierre | Doc 31 «Changelog ola 1 · cierre», candidatos, bundle, memoria → **su «promover»** | G-Ola 1 | S | Jorge |

Estimación total del §2: **≈ 2–3 bloques de trabajo** como el del 11/12-sep (confianza media: A3 y A4 son los que más pueden crecer).

## 3. Después — **ola 2 «Útil»** (herramienta de trabajo para directorio y socios; gate G-Ola 2 = «promover»)

| ID | Qué | Esfuerzo |
|---|---|---|
| B1 / F1-06 | Recorrido inicial (tour de 5 pasos), índice pegajoso por sección en las 13 vistas > 2.000 px, «cómo leer esta vista» | M |
| B2 | Modo presentación (orden fijo, teclado, tipografía mayor) | M |
| B3 | Informe PDF completo (portada, índice, pie con versión) — depende de A10 | M–L |
| B4 | Mandos: deshacer/rehacer, reset por bloque, «qué cambié», campo numérico junto al slider | M |
| B5 | Escenarios: importar JSON, duplicar, etiquetas, autor, filtro — probado en el visor real (necesita J1/J3) | M |
| D3 | Comparador de 2–3 escenarios con gráficos y deltas | M |
| D6 | Riesgos → impacto: presets donde el libro define el parámetro (cada preset ≡ caso del libro o etiquetado) | S–M |
| D7 | Trazabilidad: copiar referencia de celda, enlace a Fuentes, dependencias de un nivel en cada `Trace` | M |
| D8 | Lectura ejecutiva viva probada en los 4 casos y en extremos | S |
| D9 | Indicadores adicionales calculables — **lista para que usted apruebe** | S |
| C2 / F1-07 | `ChartFrame` común: tooltip unificado (incl. RiskMatrix), «ver tabla», exportar, `<title>`, foco | M |
| C3 | KPI con sparkline C·B·F, delta vs libro, glifo | S–M |
| H3 | Tracker «por confirmar» en `db` (colección `confirmaciones` con reglas) — el sitio natural para J4 | M |
| G8 | Bitácora de decisiones (D-*, R3-*, D-V2-*) visible en la Guía interna | S |

## 4. Después — **ola 3 «Analítica nueva»** (gate G-Ola 3 + decisión H2)

| ID | Qué | Nota |
|---|---|---|
| D1 · D2 · D4 | Goal seek (tarifa/CAPEX para TIR objetivo), tornado dinámico sobre cualquier escenario, puente ΔTIR entre dos escenarios — **etiquetados** «cálculo del artefacto con la lógica del Motor (sin celda en el libro)» (D-V2-2) | M–L |
| C8 | `tokens.json` del sistema visual consumible por el generador Excel | S |
| H2 | Sus decisiones sobre las observaciones abiertas (J5) | — |
| Propuesta Excel v4.0 | Documento con lo que el Excel debe adoptar del artefacto (D-V2-7) | S |

## 5. Excel — siguientes rondas (no arrancan hasta que usted lo pida)

| Qué | Cuándo | Cómo |
|---|---|---|
| **v3.2 (re-basing por datos)** | Cuando llegue cualquier dato de J4 o una decisión de J5 | Cadena rN del `ops/BOOTSTRAP.md` §6 (generador → tres motores → render → candidatos → «promover» → sustitución con su palabra); `Fecha_Analisis` se actualiza en esa ronda |
| **v4.0 rediseño visual** (doc 16) | Después de la ola 1 (idealmente tras la 2) del artefacto — D-V2-7 | El artefacto define el sistema visual (`tokens.json`, C8) y el Excel lo adopta; mandato y gates G1–G6 en el doc 16 |
| Ideas de motor no implementadas | Sólo si usted las prioriza | Pool de pérdidas con añadas (caducidad 5 años), art. 9 mensual/24 meses, deuda *sculpted*, eje mensual de construcción, horizonte 30 años |

## 6. Orden que recomiendo

1. **Usted, 5 min:** J1 (papelera), J3 (`downloads`), J6 (una palabra sobre fuentes). J2 cuando use el artefacto con calma.
2. **Yo, siguiente bloque:** cierre de la ola 1 en el orden A11 → A3 → A4 → A5 → A8 → F1/F2 → C5/C6 → B7/B8 → F1-11 → E2 → docs 01–22 al repo → doc 31 → candidatos → su «promover».
3. **Ola 2** empezando por lo que más valor da al directorio: B1 (navegación en vistas largas), C2 (gráficos con tabla y exportación), B5/D3 (escenarios y comparador), B3 (informe PDF).
4. **Ola 3 + propuesta v4.0**, y la ronda Excel v3.2 en cuanto haya datos de J4.

Nada del §2–§5 toca el libro vigente ni las URL oficiales sin pasar por candidatos y su «promover».
