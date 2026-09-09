# 26 · Visión, olas y plan de ejecución v2 — artefacto interactivo (F2–F4)

**Proyecto:** Modelo FV 5,0 MWp Montecristi → Gran Piazza Machala (SALELGI S.A. · gerencia Exergy)
**Fecha:** 09-sep-2026 · **Autor:** Claude (Anthropic) para Exergy EXG S.A.S. · **Gate G-A:** dado por Jorge el 09-sep-2026 (decisiones §2) con la instrucción de avanzar con las recomendaciones de Claude y pedir su intervención sólo donde sea imprescindible.
**Antecedentes:** doc 23 (§4 olas y decisiones, §5 estructura), doc 24 (F0), doc 25 (diagnóstico con evidencia y backlog consolidado).

## 1. Visión v2

**Para quién.** Jorge (operación diaria, negociación), el directorio del grupo (lectura ejecutiva y decisión), SALELGI (edición externa, sin internos de Exergy) y, cuando llegue, el banco (misma edición externa; sin perfil propio en v2 por D-V2-6).

**Qué cambia en v2.** El artefacto pasa de «réplica interactiva verificada del libro» a **herramienta de trabajo fiable y mantenible**: (a) nada se rompe sin que una máquina lo detecte (E2E, invariantes, cruce, humo tras publicar); (b) toda publicación pasa por un **candidato** y se promueve con una palabra; (c) legible por cualquiera en proyector o impreso (contraste AA, mínimos tipográficos, navegación interna); (d) escenarios como herramienta entre socios con reglas de escritura; (e) analítica nueva sólo etiquetada y comprometida para Excel v4.0.

**Qué no cambia.** El libro es la fuente: textos y valores salen del libro y se evalúan en vivo; cero paráfrasis; la edición externa excluye físicamente lo interno; el raíz v3.0 no se toca hasta G-L2; Excel en el Mac sólo con aviso; capturas sólo en el contenedor.

**Fuera de v2.** Móvil/tablet (D-V2-3), pantalla de confidencialidad y perfiles de la edición externa (D-V2-6), inglés (B10), Monte Carlo (D5), datos externos vivos (H5) → v3 / Excel v4.0.

## 2. Decisiones (estado tras G-A, 09-sep-2026)

| ID | Decisión de Jorge | Consecuencia operativa |
|---|---|---|
| D-V2-1 | Repositorio git privado — **sí** | Repo iniciado en el contenedor (3 commits); `gpm-artefacto_2026-09-09.bundle` en OneDrive; GitHub cuando Jorge cree el repo (no bloquea) |
| D-V2-2 | Cálculos sin celda — **sí, con etiqueta y compromiso v4.0** | D1/D2/D4 en ola 3 con la etiqueta «cálculo del artefacto con la lógica del Motor (sin celda en el libro)» y propuesta escrita para Excel v4.0 |
| D-V2-3 | Móvil/tablet — **no** | C7 fuera de v2; pruebas sólo ≥ 1.024 px |
| D-V2-4 | Candidato — **sí** | Publicados: interno 🧪 «Candidato · Modelo FV Montecristi → GPM», externo 🔬 «Candidato · Proyecto FV Montecristi → GPM» (versión «F1 · hotfix F1-01 candidato r1»). Promoción = republicar el mismo fragmento (sólo difiere el `<title>`) en la URL oficial con `label` |
| D-V2-5 | Escritura en `db` — **sólo `admin`; lectura para el resto; borrado lógico** | G5 en ola 1 (`rules` del contrato de capacidades) |
| D-V2-6 | Edición externa — **no** (se queda como está) | B9 y G6 fuera de v2 |
| D-V2-7 | Secuencia — **artefacto v2 primero, Excel v4.0 después** | H4 y C8 en ola 3 |
| D-V2-8 | Custom canónico — **`V31` del generador; las ediciones del raíz son exploración y se descartan** | r3 se genera desde el generador; el raíz se sustituye tras G-L2 (v3.0 → `superadas/`) |

Ratificadas implícitamente al aprobar el avance: D-F4-1 (es-EC), D-F5-1…5, R3-5, D-X-1, D-X-2 (docs 21–22). Si alguna debe reabrirse, Jorge lo indica.

## 3. Olas y criterios de aceptación (F3)

| Ola | Objetivo | Contenido (IDs doc 25 §4) | Criterios de aceptación medibles | Gate |
|---|---|---|---|---|
| **0 · Prerrequisitos** | Entorno reproducible, producción sin defectos visibles, capacidades probadas de verdad | F1-01/04 (hecho) · A1 · A2 · G7 · G1 (bundle hoy; GitHub después) · H1 (G-L2 → r3) | Candidatos r1 promovidos · A1: 12/12 pasos OK en el visor real · A2: valor de Excel/Mac registrado · `BOOTSTRAP.md` probado · r3 ≡ tres motores | **G-Ola 0** = «promover» + G-L2 |
| **1 · Sólido** | Cero regresiones detectables por máquina; legibilidad AA; release reproducible | A3–A11 · G2 · G3 · G4 · G5 · G9 · C1 (F1-02/03/05/10) · C4/E3 · C5 · C6 · F1–F4 · E2 · B6–B8 | E2E 100 % verde (15 × 4 × 2 × 2) · validador de paleta 0 fallos en ambos temas · 0 textos < 10 px · 0 `truncate` sobre contenido del libro · `release.sh` produce candidatos + informe en un comando · `rules` de `db` probadas · humo tras publicar OK | **G-Ola 1** = «promover» |
| **2 · Útil** | Herramienta de trabajo para directorio y socios | B1 (F1-06) · B2 · B3 · B4 · B5 · D3 · D6 · D7 · D8 · D9 · C2 (F1-07) · C3 · H3 · G8 | Cada vista > 2.000 px con índice pegajoso · modo presentación operable con teclado · informe PDF completo sin cortes · escenarios importar/duplicar/etiquetar probados en el visor real · `ChartFrame` en 7 gráficos · tracker «por confirmar» con reglas | **G-Ola 2** = «promover» |
| **3 · Analítica nueva** | Preguntas de negociación respondidas en el artefacto, con etiqueta | D1 · D2 · D4 · C8 · H2 · (propuesta Excel v4.0) | Etiqueta visible en cada cálculo sin celda · resultados coherentes con el motor (bisección converge a la tolerancia del cruce) · `tokens.json` consumible · doc de propuesta v4.0 | **G-Ola 3** + decisión H2 |

**Definición de terminado (toda ola):** ≡ libro (verify 91.546/0, live.test PASS, cruce ≥ 24 muestras), E2E verde, candidatos publicados y revisados, promoción aprobada, doc NN en `Documentación/`, fuentes en OneDrive + repo (bundle o GitHub), memoria del proyecto actualizada.

## 4. Plan de acción — Ola 0 (F4)

| # | Tarea | Quién | Estado / dependencia |
|---|---|---|---|
| 0.1 | Hotfix F1-01/F1-04 en candidatos r1 | Claude | **Hecho** (09-sep) |
| 0.2 | Promover candidatos r1 → URL oficiales (`label` «F5 r2 · hotfix F1-01») | Jorge («promover») → Claude | Pendiente de su palabra |
| 0.3 | A1 · protocolo de 12 pasos en el candidato interno 🧪 (guardar/actualizar/eliminar/compartir escenario, segunda ventana, `#s=`, CSV, JSON, impresión); limpieza de escenarios de prueba | Claude en el navegador de Jorge (sin capturas) | Requiere enlace con el Mac o Chrome (sin enlace al cierre del 09-sep) |
| 0.4 | A2 · `=IRR(serie,0.02)` en libro temporal `_borrador_v3.1/pruebas/` con la serie del doc 22 §5; comparar con LibreOffice y motor | Claude vía conector Excel, **con aviso previo** | Requiere enlace con el Mac |
| 0.5 | Configuración regional del Mac (`AppleLocale`, separadores) para A6 | Claude vía osascript | Requiere enlace |
| 0.6 | `BOOTSTRAP.md` definitivo + `README` del repo | Claude | Ola 0, sin dependencias |
| 0.7 | Añadir `Documentación/01–24` al repo; bundle actualizado en OneDrive | Claude | Requiere enlace (staging en lotes de ≤ 8 archivos) |
| 0.8 | GitHub: `git push` del bundle al repo privado | Jorge crea el repo → Claude | No bloquea |
| 0.9 | Pre-revisión de r2 para G-L2 (lista de puntos por hoja, render Excel ya existente en `render_excel/`) | Claude | Ola 0; entrega a Jorge |
| 0.10 | G-L2 → r3 (generador HEAD + puntos) → tres motores + render → sustitución → re-extraer → candidatos con r3 → promover | Jorge (revisión y aprobación de sustitución) → Claude | Ruta crítica |

## 5. Plan de acción — Ola 1 (F4)

Secuencia propuesta (cada bloque termina con build de candidatos, E2E y punto de guardado):

| Bloque | Tareas | Entregable verificable |
|---|---|---|
| 1.A Pruebas | A3 (smoke → E2E con aserciones de DOM: sin AST, sin desborde, KPI ≡ motor, CSV ≡ tabla, hash, presets, Comparar, `#v=exergy` externo → Resumen) · A4 (invariantes + controles de 13 con el motor) · A5 (`ENGINE_DIR`, 24 muestras) · F1-11 | `npm run e2e` verde; `controles.ts`; informe de cruce |
| 1.B Robustez | A7 (`ViewErrorBoundary`) · A8 (rangos desde tabla única) · A9/G4 (panel «Acerca de») · A10 (PDF por vista) · A11 (humo tras publicar) | Panel visible; PDFs sin cortes |
| 1.C Legibilidad | C1 con F1-02 (`--ink-3`, `--info`), F1-03 (mínimos), F1-05 (recortes), F1-10 (indicador de scroll) · C5 (oscuro) · C6 · F3/F4 · C4/E3 (decisión fuentes) | Validador 0 fallos; capturas antes/después |
| 1.D Gobierno | G2 (`release.sh` + changelog de `book.json`) · G3 (regla de promoción) · G5 (`rules` `db`) · G9 (`publicados/`) · B6/B7/B8 | Un comando → candidatos + informe; reglas probadas |
| 1.E Cierre | E2 (matriz), doc 27 «Changelog v2 · ola 1», fuentes, memoria, promoción | G-Ola 1 |

**Qué necesita de Jorge en ola 1:** nada obligatorio; opcional 10 min para la matriz de navegadores (Safari/app Claude) y su lote de puntos numerados sobre los candidatos cuando quiera.

## 6. Principios de ejecución (vigentes)

Una ola a la vez; cambios pequeños con prueba; nunca romper ≡ libro; toda decisión con ID y estado; cada sesión termina con punto de guardado fuera del contenedor (bundle/tarball + doc); capturas en el contenedor; pruebas que exigen la cuenta de Jorge agrupadas en un bloque por ola; promoción a las URL oficiales sólo con su palabra.
