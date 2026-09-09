# 25 · Diagnóstico con evidencia y backlog v2 consolidado — artefacto interactivo (F1)

**Proyecto:** Modelo FV 5,0 MWp Montecristi → Gran Piazza Machala (SALELGI S.A. · gerencia Exergy)
**Fecha:** 09-sep-2026 · **Autor:** Claude (Anthropic) para Exergy EXG S.A.S., a petición de Jorge A. Baquerizo
**Antecedentes:** doc 23 (prompt v2, backlog §3 desde el código), doc 24 (F0, línea base verificada). G-A dado por Jorge el 09-sep con las decisiones D-V2-1…8 (doc 26).
**Método:** auditoría del artefacto **vivo** en el contenedor con Playwright (Chromium 1194, 1280 × 800, sin GPU): 15 vistas × 4 casos × 2 temas en la edición interna (120 combinaciones) y 14 × 4 × 2 en la externa (112); sondas de DOM (desborde, textos recortados, tamaño de fuente, contraste WCAG calculado sobre colores efectivos, nombres accesibles, SVG), medición de rendimiento (mando → KPI, carga, ⌘K), lectura de código para lo no observable. Scripts en el repo `ops/audit/` (`audit.mjs`, `audit2.mjs`, `probe_garbage.mjs`, `probe_ovf.mjs`) y capturas en `Fuentes técnicas v3.1/F1_auditoria_2026-09-09.tar.gz`. **No probado aún** (requiere el Mac o el navegador de Jorge, ambos sin enlace al cierre de F1): A1 `db`/`downloads` en el visor real, A2 `IRR` en Excel/Mac, configuración regional.

## 1. Resultado en una línea

El artefacto es estable (0 errores de consola en 232 combinaciones, recálculo mando → KPI de 17–30 ms) pero la auditoría visual encontró **un defecto de contenido en producción** en las dos ediciones publicadas (F1-01, ya corregido en los candidatos r1) y **tres problemas sistémicos de legibilidad** (contraste del gris terciario, fuentes de 8,5–10 px, vistas de > 5.000 px sin navegación interna) que el diagnóstico desde el código del doc 23 no había detectado.

## 2. Hallazgos con evidencia (F1-xx)

Severidad: **P0** defecto visible en producción · **P1** afecta la lectura o la confianza · **P2** mejora. Confianza alta salvo nota.

| ID | Sev. | Dónde | Hallazgo (evidencia) | Causa | Corrección | Estado |
|---|---|---|---|---|---|---|
| **F1-01** | **P0** | Resumen · «Los cinco candados del régimen», candados 4 y 5 · **interno y externo publicados (F5 r1)** | El criterio se muestra como AST + fórmula crudos: «fbin&bin&bin&strCapacidad del alimentador 13,8 kV para callTEXTnamePotencia_ACstr#,##0str … ="Capacidad del alimentador…"&TEXT(Potencia_AC,"#,##0")…» (8 coincidencias por edición; captura `resumen-custom-light.png`). Provoca además F1-04. | `Resumen.tsx:193` renderiza `{c.criterio}` en crudo; para 4 y 5 `criterio` es una fórmula `['f', ast, texto]` (los otros tres son cadenas). Legal sí evalúa (`<Live text={concatFormula(c.criterio)}/>`). `live.test` no cubre `candados[*].criterio`. | `{m.live(c.criterio)}` + `min-w-0 break-words`. Verificado: «Capacidad del alimentador 13,8 kV para 3.788 kWac (aprobable: 3.800 kW, por confirmar)» y «Peaje de red desde 28-feb-2029 — valor no publicado…». Añadir a A3 una aserción de DOM «ningún token de AST ni fórmula cruda fuera de la columna Fórmula de Controles» y a `live.test` la evaluación de todos los `['f',…]` de `book.json`. | **Corregido en candidatos r1** (interno 🧪, externo 🔬). Pendiente: promover (Jorge) |
| **F1-02** | P1 | Todas las vistas, ambos temas | El gris terciario `--ink-3` (#8B94A3 claro / #6F7987 oscuro) no cumple AA: **2,81:1** sobre `--bg` #F4F5F7, 3,06:1 sobre blanco, 2,95:1 sobre `--surface-2`; oscuro 4,26:1 sobre #0F1216, 3,96:1 sobre #161A20 (mínimo 4,5:1 para texto normal). 154 usos (`text-ink-3`): rótulos de KPI (10,5 px), subtítulos, pies, chips «interno»/«Ctrl K», glosas. Muestreo topado en 40 elementos por vista → el recuento real es mayor. | Token elegido por jerarquía visual sin validar contraste. | Recalibrar `--ink-3` a ≥ 4,5:1 sobre `--bg` y `--surface` en ambos temas (p. ej. ≈ #667080 claro, ≈ #8C97A8 oscuro; validar con `validate_palette`) o reservar el gris actual a elementos ≥ 18,66 px. Revisar `--info` (◇ #6F7987: 4,04:1 a 9 px). | Ola 1 (F3/C5) |
| **F1-03** | P1 | Controles (90 elementos < 10 px), Supuestos (34), Trámites (25), Legal (23), Fuentes (23), Riesgos (19), Guía (13), CAPEX (11), Resumen (10) | Texto de **8,5 px** (1 clase) y **9 px** (3 clases: `Live`, `SelfCheckChip`, `Status`, `Resumen`) y 45 usos de 10–10,5 px. Legible en pantalla retina, no en proyector ni al imprimir. | Densidad buscada en F3/F4. | Mínimo 11 px para texto informativo; 10,5 px sólo en rótulos en mayúsculas con `tracking`; la columna «Fórmula del libro» de Controles a 11 px mono con `overflow-x` propio. | Ola 1 (C1) |
| **F1-04** | P1 | Resumen (todas las combinaciones) | `main` desbordaba **93 px** en horizontal a 1.280 px (226 px con Mandos abiertos): la cadena sin espacios de F1-01 no partía. | Ídem F1-01 + celda sin `min-w-0`. | Corregido con F1-01 (`scrollLeft` 0 tras el fix). Añadir al E2E «`main.scrollWidth ≤ clientWidth` en todas las vistas». | **Corregido en candidatos r1** |
| **F1-05** | P2 | CAPEX (ambos temas, ambas ediciones) | 2 textos recortados con `truncate` a 1.280 px: «Gerencia del proyecto — Exergy (7 % del valor del…», «TOTAL CAPEX INDUSTRIAL SALELGI (sin IVA, sin terre…». | Columna de partida con ancho fijo. | Partir en dos líneas (`line-clamp-2`) o `title` con el texto completo; no ocultar información del libro. | Ola 1 (C1) |
| **F1-06** | P1 | 13 de 15 vistas | Alto de página **> 5.000 px** a 1.280 px (Supuestos, Energía, CAPEX, OPEX, Fiscal, Flujo, Exergy, Legal, Trámites, Riesgos, Fuentes, Controles, Guía; Resumen 1.793, Sensibilidad 1.809). Sin índice de secciones ni «volver arriba»; ⌘K sólo lleva a filas concretas. | Vistas reproducen hojas completas. | Sub-navegación pegajosa por sección (títulos de `Section` ya existen), «volver arriba», y en Guía «cómo leer esta vista». Relacionado con B1/B2. | Ola 2 (B1) |
| **F1-07** | P2 | Gráficos | `RiskMatrix` sin hover (confirmado: 0 `setHover`); ningún gráfico con `<title>` SVG ni foco de teclado (0 `tabIndex/onKeyDown`); `Tornado` es el único con `<title>`. Todos tienen `role="img"` + `aria-label` (svgNoRole = 0) ✔. | Cada gráfico implementa su propio hover. | `ChartFrame` común (C2): tooltip unificado, «ver tabla», exportar, `<title>`/`<desc>`, foco. | Ola 2 (C2) |
| **F1-08** | P2 | Aplicación | Sin `ErrorBoundary` (0 coincidencias): un error de render tumba toda la aplicación (ocurrió en F4). | — | `ViewErrorBoundary` por vista + «copiar diagnóstico» (A7). | Ola 1 (A7) |
| **F1-09** | P2 | Accesibilidad | Sin `prefers-reduced-motion` (0 reglas); `focus-visible` sólo en 7 componentes ui; sliders **sí** tienen nombre accesible (12 `input[type=range]` dentro de `<label>`; 31 controles de Mandos, 0 sin nombre) → corrige F2 del doc 23. | — | F4 (reduced-motion) y F1 (auditoría de teclado) en Ola 1. | Ola 1 |
| **F1-10** | P2 | Tablas | 7 tablas más anchas que su contenedor (Energía 2, CAPEX 1, Fiscal 1, Flujo 2, Trámites 1) con `overflow-x-auto` propio ✔, sin indicador visual de que hay más columnas. | — | Sombra de borde o «⇢ N columnas más» en `DataTable`. | Ola 1 (C1) |
| **F1-11** | P2 | `check-exclusion.mjs` | Informa tamaño en caracteres/1024 (`html.length`) y `to-fragment.mjs` en bytes (1.098,4 «KB» vs 1.136.664 B). | Unidad distinta. | Unificar en bytes (R-F0-5). | Ola 1 (G2) |
| **F1-12** | P2 | `smoke.mjs` | 3–4 aserciones obsoletas (h1 = título de hoja desde F4; título interno codificado para el host externo). | Prueba de F3 no actualizada. | Actualizar y ampliar a suite E2E (A3). | Ola 1 (A3) |

**Medidas de rendimiento (E1, contenedor sin GPU):** mando → KPI **17–30 ms** (10 muestras sobre `Ratio_DCAC`, mediana ≈ 22 ms; objetivo < 50 ms cumplido) · carga de vista 259–300 ms en caliente, ≈ 1 s en frío · ⌘K abre en 27 ms con 285 ítems en 11 grupos · heap JS 14 MB. Confianza alta para escritorio; sin dato en móvil (fuera de alcance, D-V2-3).

## 3. Correcciones al diagnóstico del doc 23 (§3) tras la evidencia

| ID doc 23 | Decía | Evidencia | Ajuste |
|---|---|---|---|
| A3 | «ninguna prueba con aserciones» | `smoke.mjs` tiene 20 aserciones (3–4 obsoletas); no cubre KPI ≡ motor, CSV, escenarios, 15 vistas | «Actualizar y ampliar», esfuerzo M → S–M |
| A6 | «falta probar negativos, −0, miles, %…» | `format.test.ts` 73/73 ya los cubre | Reducir a «equivalencia es-EC ↔ Excel/Mac regional» (S) |
| C7 | «gráficos SVG de ancho fijo» | Todos usan `useMeasure` → responsivos al contenedor | Retirar del razonamiento; C7 fuera de v2 por D-V2-3 |
| F2 | «etiquetas en sliders» | 12 ranges dentro de `<label>`; 0 controles sin nombre en Mandos | Cerrado; queda `<title>`/foco en gráficos (F1-07) |
| E1 | «no medido; confianza media» | 17–30 ms por mando | Cumplido en escritorio; medir sólo tras cambios grandes |
| E3 | «redes corporativas pueden bloquear fonts» | Confirmado en el contenedor (`ERR_TUNNEL_CONNECTION_FAILED`, respaldo del sistema sin errores) | Decisión pendiente C4/E3 (embeber subconjunto ≈ 150–250 KB o aceptar) |
| A7, F4 | supuestos | Confirmados (0 ErrorBoundary, 0 reduced-motion) | — |
| Nuevo | — | F1-01…F1-06, F1-10 | Añadidos al backlog |

## 4. Backlog v2 consolidado (con las decisiones de G-A)

Olas según doc 26. **Fuera de v2 por decisión de Jorge:** C7 (D-V2-3 no), B9 y G6 (D-V2-6 no), B10 y D5 (v3), H5 (v3). Esf.: S ≤ ½ sesión · M 1–2 · L > 2.

| Ola | ID | Mejora | Esf. | Criterio de aceptación | Depende de |
|---|---|---|---|---|---|
| 0 | F1-01/F1-04 | Hotfix candados Resumen | S | 0 tokens de AST en DOM; `main.scrollWidth ≤ clientWidth` | — (hecho en candidatos r1) |
| 0 | A1 | Prueba real `db`/`downloads` en el visor | S | Protocolo de 12 pasos ejecutado en el candidato interno; resultados en doc | navegador/Mac de Jorge |
| 0 | A2 | `IRR` en Excel/Mac con 1 + r < 0 | S | Valor de `=TIR(serie;0,02)` registrado y comparado con LibreOffice/motor | Excel/Mac (con aviso) |
| 0 | G7 | `BOOTSTRAP.md` definitivo (desde `BOOTSTRAP_F0.md`) | S | Restauración desde cero en < 15 min siguiendo el documento | — |
| 0 | G1 | Repo git: bundle en OneDrive hoy; GitHub privado cuando Jorge cree el repo | S | `git clone` del bundle reproduce la línea base; CI verde tras GitHub | Jorge (repo) |
| 0 | H1 | G-L2 → r3 → sustitución → re-extraer → republicar | M | Tres motores idénticos; `live.test` PASS con r3; candidatos con r3 | **Jorge (G-L2)** |
| 1 | A3 | Suite E2E (smoke actualizado + 15 vistas × 4 casos × 2 temas × 2 ediciones, KPI ≡ motor, CSV ≡ tabla, hash ida y vuelta, presets ≡ memo, sin AST en DOM, sin desborde) | M | 100 % verde en cada build; corre en `release.sh` | — |
| 1 | A4 | Invariantes del motor + 79 controles de 13 recalculados con el motor | M | 1.000 muestras aleatorias sin violación; controles del artefacto ≡ libro en la línea base | — |
| 1 | A5 | Cruce aleatorio institucionalizado (`ENGINE_DIR`, 24 muestras, semilla por versión) | S | Informe por release | — |
| 1 | A6 | Equivalencia es-EC ↔ Excel/Mac | S | Tabla de formatos verificada con la configuración regional real | lectura del Mac |
| 1 | A7/F1-08 | `ViewErrorBoundary` + copiar diagnóstico | S | Error inyectado en una vista no afecta a las demás | — |
| 1 | A8 | Rangos y validaciones de mandos desde el libro/documentados | S–M | Tabla única de rangos compartida por Mandos y cruce | decisión de rangos (Claude propone) |
| 1 | A9/G4 | Chip ≡ → panel «Acerca de» (versión del libro, SHA, fecha, oráculo, edición, entradas modificadas, changelog) | S | Panel visible en ambas ediciones | — |
| 1 | A10 | Impresión por vista verificada (Chromium `page.pdf()`) | S | PDF por vista sin cortes de tabla | — |
| 1 | A11 | Humo tras publicar (abrir URL del candidato) | S | Título, edición, chip ≡, 0 errores | — |
| 1 | G2 | `release.sh` cadena completa + changelog automático de textos/valores | M | Un comando produce candidatos + informe | A3 |
| 1 | G3 | Candidatos (hecho: 🧪 interno, 🔬 externo) + regla de promoción | S | Promoción = mismo fragmento (sólo cambia `<title>`) | — |
| 1 | G5 | `rules` en `db`: `admin` escribe, `interact` lee; borrado lógico | S–M | Un usuario `interact` no puede eliminar escenarios | A1 |
| 1 | G9 | `publicados/` con SHA de cada fragmento | S | Carpeta en OneDrive/repo | — |
| 1 | C1/F1-02/03/05/10 | Auditoría visual corregida: contraste AA, mínimos tipográficos, recortes, indicador de scroll en tablas | M | Validador de paleta 0 fallos; 0 textos < 10 px; 0 `truncate` sobre contenido del libro | — |
| 1 | C4/E3 | Tipografía: decisión fuentes (embeber subconjunto vs respaldo) + `size-adjust` | S | Sin FOUT perceptible; funciona sin red | decisión (Claude propone) |
| 1 | C5 | QA tema oscuro con validador | S–M | AA en ambos temas | C1 |
| 1 | C6 | Iconografía y microcopy | S | Un set; verbos consistentes | — |
| 1 | F1–F4 | Teclado, aria en gráficos, contraste, reduced-motion | S–M | Auditoría axe/Playwright sin errores serios | C1 |
| 1 | E2 | Matriz navegadores (Chromium/WebKit en contenedor; Safari/Chrome/Edge/app Claude a mano) | S | Tabla con resultado por navegador | 10 min de Jorge (opcional) |
| 1 | B6/B7/B8 | Copiar enlace; ⌘K ampliado (fuentes, CAPEX, OPEX, salidas Motor); explicaciones «n/a»/«LIBRO»/«▲» | S | Presentes y probados en E2E | — |
| 2 | B1/F1-06 | Recorrido inicial + sub-navegación por sección + «cómo leer esta vista» | M | Cada vista > 2.000 px tiene índice pegajoso; tour de 5 pasos | — |
| 2 | B2 | Modo presentación | M | Orden fijo, teclado, tipografía mayor | C1 |
| 2 | B3 | Informe PDF completo | M–L | Paquete con portada, índice, pie con versión | A10 |
| 2 | B4 | Mandos: deshacer/rehacer, reset por bloque, «qué cambié», campo numérico | M | E2E | — |
| 2 | B5 | Escenarios: importar JSON, duplicar, etiquetas, autor, filtro | M | E2E + prueba real | A1, G5 |
| 2 | D3 | Comparador con gráficos y deltas | M | 2–3 escenarios superpuestos | B5 |
| 2 | D6 | Riesgos → impacto (presets donde el libro define el parámetro) | S–M | Cada preset ≡ caso del libro o etiquetado | — |
| 2 | D7 | Trazabilidad: copiar referencia, enlace a Fuentes, dependencias de un nivel | M | Popover en todos los `Trace` | — |
| 2 | D8 | Lectura ejecutiva viva: pruebas en 4 casos y extremos | S | Casos en E2E | A3 |
| 2 | D9 | Indicadores adicionales calculables (propuesta → Jorge) | S | Lista aprobada | — |
| 2 | C2/F1-07 | `ChartFrame`: tooltip unificado (incl. RiskMatrix), ver tabla, exportar, `<title>`, foco | M | Todos los gráficos con la misma capa | C1 |
| 2 | C3 | KPI: sparkline C·B·F, delta vs libro, glifo | S–M | E2E | — |
| 2 | H3 | Tracker «por confirmar» en `db` (metadatos) | M | Colección `confirmaciones` con reglas | A1, G5 |
| 2 | G8 | Bitácora de decisiones (D-*, R3-*, D-V2-*) en Guía | S | Visible en interno | — |
| 3 | D1, D2, D4 | Goal seek, tornado dinámico, puente ΔTIR — **etiquetados** «cálculo del artefacto con la lógica del Motor (sin celda en el libro)» y propuestos para Excel v4.0 (D-V2-2) | M–L | Etiqueta visible; documento de propuesta v4.0 | H4 |
| 3 | C8 | `tokens.json` para Excel v4.0 | S | Consumido por el generador | H4 |
| 3 | H2 | Observaciones abiertas del modelo (margen O&M 0, 04!D74/D75, memo 03, F10) | S–M | Decisiones de Jorge | Jorge |

## 5. Lo que sigue necesitando a Jorge (sin cambios respecto al mensaje del 09-sep)

1. **G-L2** (r2 hoja por hoja) — ruta crítica de H1; Claude entregará una pre-revisión para reducirla a ~30 min.
2. **GitHub** — crear el repositorio privado y dar acceso; mientras, `gpm-artefacto_2026-09-09.bundle` en OneDrive.
3. **Un clic** de aprobación de sitio si la app lo pide al ejecutar A1 en su navegador.
4. **«Promover»** — candidatos r1 (hotfix F1-01) → URL oficiales.
