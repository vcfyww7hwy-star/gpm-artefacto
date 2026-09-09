# 23 · Prompt de continuación — Artefacto interactivo v2: mejora integral (operación, UX, UI, análisis, verificación, gobierno)

**Proyecto:** Modelo FV 5,0 MWp Montecristi → Gran Piazza Machala (SALELGI S.A. · gerencia Exergy)
**Fecha:** 09-sep-2026 · **Autor:** Claude (Anthropic) para Exergy EXG S.A.S., a petición de Jorge A. Baquerizo («haz un listado claro de mejoras… quiero proceder en un nuevo chat… mejóra la estrategia de cómo atacar el listado»)
**Uso:** este documento ES el primer mensaje del nuevo chat (pegarlo íntegro o adjuntarlo), en el mismo proyecto de Cowork y con la carpeta `Exergy` de OneDrive conectada. Guardarlo además en `…/Modelo GPM 5MWp/Documentación/` (el chat que lo redactó perdió el enlace con el Mac antes de poder copiarlo).
**Antecedentes:** docs 17 (plan v1.0), 18 (conciliación legal), 19 (changelog v3.1), 20 (F1–F4), 21 (F5), 22 (cruce aleatorio, R3-5, r3-pre); memoria del proyecto `exergy-gpm-artefacto.md`.

---

## 0. Instrucción para el nuevo chat

Eres el mismo asistente que construyó el artefacto interactivo «Modelo FV Montecristi → GPM» (ediciones interna y externa) a partir del libro Excel v3.1. El objetivo de este chat es **mejorarlo integralmente** — operación, UX, UI, profundidad analítica, verificación de que todo funciona perfecto, gobierno y mantenimiento — con contexto limpio. Orden obligatorio: **(1)** ejecutar la Fase 0 del §5 (restaurar el entorno y verificar la línea base; nada se propone sobre un entorno no verificado); **(2)** presentar a Jorge, en una sola respuesta estructurada, el estado verificado, el backlog del §3 con tu diagnóstico actualizado y la estructura de trabajo del §5 con las decisiones del §4 pendientes; **(3)** esperar su aprobación (gate) antes de ejecutar cualquier cambio. Las reglas del §2 rigen íntegras.

## 1. Estado de partida (verificado 08/09-sep-2026)

| Elemento | Estado |
|---|---|
| **Artefacto INTERNO** «Modelo FV Montecristi → GPM» | https://claude.ai/code/artifact/6fb96cf4-613a-4649-ad0c-96704dc4d271 · favicon ☀️ · capacidades `{db: {}, downloads: true}` (por `db` es interno a la organización) · versión publicada «F5 r1 · escenarios y exportar» · fragmento 1.104 KB (SHA 9c7418a0…) · 15 vistas (Resumen, Sensibilidad, Supuestos, Energía, CAPEX, OPEX, Fiscal, Flujo, Legal, Trámites, Riesgos, Fuentes, Controles, Guía, Exergy) · Mandos (88 entradas + bloque B) · Escenarios en `db` (colección `escenarios`, compartida) · presets del memo de 03 · Comparar (≤ 3) · CSV por tabla · JSON de entradas · impresión por vista · ⌘K · enlaces `#v= #c= #s= #f=` · claro/oscuro · es-EC · IBM Plex |
| **Artefacto EXTERNO** «Proyecto FV Montecristi → GPM» | https://claude.ai/code/artifact/dd6ec83a-940b-4a4c-ac9b-5f9e2bd2cda7 · favicon 🔆 · `{downloads: true}` (compartible fuera) · «F5 r1 · edición externa» · 1.065 KB (SHA 8b8e4f76…) · sin vista Exergy, sin hoja 09, sin bloque H de 01, sin grupo E de controles (73/72 ●), sin nombres/valores internos ni textos que los citen (71 eliminaciones listadas por `make-externo.py`; `check-exclusion.mjs` en cada build) · resultados de SALELGI idénticos a la interna |
| **Libro Excel** | Raíz `Modelo_FV_5MWp_GPM_v3.0.xlsx` y `…Resumen_Directorio_v3.0.xlsx` **intactos** (Jorge los abrió/guardó el 08-sep 22:25 UTC; no tocar). Borrador **v3.1 r2** en `_borrador_v3.1/` (modelo + Resumen) pendiente de **G-L2** (su revisión hoja por hoja). **r3-pre** construido en el contenedor con el generador HEAD (R3-1…R3-5): 0 diferencias de valor frente a r2 (317 nombres, 86.085 celdas del Motor), 25 textos cambiados; **no entregado** (se regenerará con los puntos de G-L2) |
| **Verificación vigente** | Motor JS ≡ LibreOffice: línea base 91.546 celdas / 0 fuera; cruce aleatorio 61 muestras / 5.584.306 celdas / 1 divergencia explicada y resuelta con **R3-5** (guardia TIR accionista ≤ −100 % → «n/a») · `live.test` PASS (106 nombres, 94 textos idénticos, capex 57 + 111, opex 111) · `check:exclusion` OK · `tsc` limpio · **NO verificado:** `db`/`downloads` en el visor real de claude.ai (nunca probado desde el contenedor); comportamiento de Excel/Mac ante `IRR` con 1 + r < 0 (doc 22 §5) |
| **Fuentes (OneDrive `_borrador_v3.1/Fuentes técnicas v3.1/`)** | `artefacto_F5_r2_fuentes.tar.gz` (96df467c…; app + engine con la guardia + `data` r2 + `data_r3pre`; sin `node_modules`) · `build30_r3pre_generador_2026-09-08.tar.gz` (66e10314…; generador HEAD + r3pre.xlsx + log) · `cruce_aleatorio_motor_2026-09-08.tar.gz` (244a3627…) · `artefacto_F5_r1_fuentes.tar.gz` (ba3a5be3…; **contiene los fragmentos publicados** en `app/out/`) · `artefacto_F4_r1_fuentes.tar.gz` · `build30_extractores_F1.tar.gz` · `scripts_v3.1.tar.gz` · `referencias_regresion_v3.1.zip` |
| **Documentación** | `…/Modelo GPM 5MWp/Documentación/` docs 01–22 (17 plan · 18 legal · 19 changelog v3.1 · 20 F1–F4 · 21 F5 · 22 cruce/R3-5/r3-pre); doc 07 «Nota de traspaso» se actualiza sólo al sustituir el raíz |
| **Gates abiertos (de Jorge)** | **G-L2** r2 hoja por hoja → r3 → sustitución del raíz con aprobación explícita (v3.0 → `superadas/`) · **G2/G5** revisión de las 15 vistas y de F5, primera prueba real de `db`/`downloads`, alcance y destinatarios de la edición externa · **F6** cierre (carpeta `Artefacto interactivo/`, guía de uso y actualización, doc 07, memoria; borrar `_borrador_v3.1/` sólo con aprobación) |
| **Decisiones a ratificar** | D-F4-1 (es-EC en todo el artefacto) · D-F5-1…5 (doc 21 §3) · R3-5, D-X-1, D-X-2 (doc 22 §3) |
| **Observaciones abiertas del modelo** | Fee_OM 16 = Costo_OM_Exergy 16 → margen O&M de Exergy 0 · 04!D74/D75 y palancas de 09 no son entradas de 01 (9 valores «LIBRO» congelados en el artefacto) · memo de 03 «en la página siguiente» · control F10 «▲ Custom ≠ Base en 4 entradas» (deliberado en v3.1) |
| **Entorno** | El contenedor es efímero: **nada de lo construido sobrevive fuera de los tarballs de OneDrive**. Restaurar según §6 antes de trabajar |

## 2. Reglas vigentes (no negociables)

1. Español formal, salidas estructuradas y accionables; cada afirmación cuantitativa con fuente y fecha; incertidumbre declarada con nivel de confianza; datos en conflicto se muestran ambos.
2. **Cero contenido inventado**: los textos del artefacto salen del libro (constantes del generador + celdas calculadas) y se evalúan en vivo; nunca se parafrasean. Los textos propios de la interfaz (botones, ayudas, tour) se marcan como tales y no se confunden con contenido del modelo.
3. **Coherencia entre superficies como requisito estructural**: artefacto ≡ libro (valores, textos, casos). Todo cálculo que no exista en el libro debe (a) etiquetarse visiblemente como «cálculo del artefacto con la lógica del Motor (sin celda en el libro)» y (b) proponerse para el libro v4.0 — o no hacerse (decisión D-V2-2, §4).
4. Gates de aprobación: Jorge decide; Claude entrega análisis verificable, opciones con trade-offs y supuestos. Dentro de un plan aprobado rige «sigue a tu criterio»; fuera de él, no.
5. Mac de Jorge: avisar antes de abrir Excel; nunca capturas de su pantalla (las capturas se hacen en el contenedor con Playwright); nunca sobrescribir un archivo que tenga abierto; copias borrador con nombre único; los entregables se sustituyen sólo con aprobación explícita y lo sustituido va a `superadas/` (Claude no borra).
6. No tocar el libro raíz ni el Resumen v3.0 hasta G-L2. La edición externa excluye **físicamente** los internos de Exergy (no basta ocultarlos). `db` sólo en la edición interna.
7. Revisión de Jorge por lotes de puntos numerados; Claude responde punto por punto con la evidencia.
8. Cada bloque de trabajo termina con: verificación reproducible, documento numerado en `Documentación/`, fuentes en OneDrive (tarball o repositorio) y memoria actualizada. Nada queda sólo en el contenedor.

## 3. Backlog de mejoras — análisis por ejes

Leyenda: **Esf.** S ≤ ½ sesión · M 1–2 sesiones · L > 2 sesiones. **≡** = riesgo para la coherencia con el libro (∅ ninguno · ⚠ requiere etiqueta/decisión D-V2-2). Confianza en el diagnóstico: alta salvo nota.

### A · Verificación y robustez («que todo funcione perfecto»)

| ID | Mejora | Valor para el lector/operación | Cómo | Esf. | Depende de | ≡ / nota |
|---|---|---|---|---|---|---|
| A1 | **Prueba real de `db` y `downloads` en el visor de claude.ai** | Es la única parte del artefacto nunca ejecutada de verdad: guardar/cargar/actualizar/eliminar escenarios, tiempo real entre dos ventanas, enlace `#s=`, CSV/JSON, impresión. | Protocolo escrito de 12 pasos con resultado esperado; Jorge lo ejecuta en su cuenta (10 min) o comparte pantalla de resultados; registro en doc. | S | Jorge | ∅ |
| A2 | **Cerrar la duda Excel/`IRR`** (doc 22 §5) | Fija si Excel/Mac se comporta como LibreOffice ante 1 + r < 0; con R3-5 las tres superficies coinciden igual, pero conviene saberlo. | `=TIR(serie;0,02)` con los 27 valores del doc 22 en un libro nuevo (1 min), o Claude vía conector de Excel en libro temporal con autorización previa. | S | Jorge | ∅ |
| A3 | **Suite E2E automatizada** (Playwright en el contenedor sobre el fragmento) | Hoy hay scripts de captura (`shots/host.mjs`, `f5.mjs`) pero **ninguna prueba con aserciones**: una regresión visual o funcional sólo se detecta a ojo. | 15 vistas × 4 casos × claro/oscuro × 2 ediciones sin errores de consola; mandos → KPI ≡ motor; ⌘K → foco; CSV ≡ tabla; hash de ida y vuelta; presets ≡ memo; diálogo Comparar; `#v=exergy` cae en Resumen en externo. Corre en cada build. | M | §6 restaurado | ∅ |
| A4 | **Invariantes del motor en JS** (sin LibreOffice) | Verificación en segundos con miles de muestras: VAN(TIR) ≈ 0; Σ amortización = deuda; DSCR = CFADS/servicio; payback coherente con el acumulado; identidades fiscales; y **recalcular los 79 controles de 13 con el motor** y compararlos con los del libro (hoy los controles se muestran congelados). | Pruebas basadas en propiedades (`fast-check` o generador propio) + `controles.ts` que reimplemente las fórmulas de 13 sobre el motor. | M | — | ∅ (extiende ≡ a los controles) |
| A5 | Cruce aleatorio como parte de cada release | Ya existe (`crosscheck_engine.py`, 61 muestras); falta institucionalizarlo. | 24 muestras (≈ 7 min) en `release.sh` (G2) con semilla fija por versión + informe. | S | LibreOffice en contenedor | ∅ |
| A6 | **Formato es-EC**: pruebas de `fmt*` y equivalencia con TEXT() | `live.test` demuestra identidad de los 94 textos en en-US; el artefacto muestra es-EC. Falta probar negativos, −0, miles, %, años, «x», y documentar la equivalencia con lo que Excel/Mac muestra en la configuración regional de Jorge. | Juego de casos límite en `format.test.ts`; tabla de equivalencia formato Excel ↔ `fmt*`; verificar la configuración regional real de su Mac (pregunta a Jorge). | S–M | — | ∅ |
| A7 | **ErrorBoundary por vista** + pantalla de error útil | Hoy un error en una vista tumba toda la aplicación (ocurrió en F4 con Legal). Con límites por vista el resto sigue operativo y el usuario puede copiar un diagnóstico (vista, caso, entradas JSON, error) para enviarlo. | Componente `ViewErrorBoundary`; botón «copiar diagnóstico». | S | — | ∅ |
| A8 | **Validación de entradas** alineada con el libro | Los rangos de los mandos están fijados en el código (p. ej. ratio 1,10–1,50, deuda 0–100 %, tasa 5–12 %) y no provienen del libro; faltan bloqueos ante combinaciones imposibles (plazo ≤ gracia, potencia 0, fechas invertidas). | Extraer rangos/validaciones de 01 al `book.json` (o definirlos con Jorge y documentarlos en 01 en v4.0); mensajes de rango; misma tabla de rangos para el cruce aleatorio. | S–M | decisión de rangos | ∅ |
| A9 | Chip «Motor ≡ Excel» y panel **«Acerca de»** | Que el lector sepa siempre qué versión del libro está viendo (v3.1 r?, SHA del cálculo, fecha de extracción, oráculo 1776/1776 o 1443/1443, edición) y si se ha alejado del libro (entradas modificadas). | Panel desde el chip; datos ya existen en `book.meta`. | S | — | ∅ |
| A10 | Impresión por vista en Chrome/Safari → PDF | Verificar paginación, tablas anchas, colores de estado en impresión, encabezado con versión/fecha. | Pruebas manuales + Playwright `page.pdf()`. | S | — | ∅ |
| A11 | Prueba de humo de publicación | Tras cada publicación, abrir la URL en el contenedor (Playwright) y comprobar título, edición, chip ≡ y ausencia de errores — evita publicar un fragmento roto. | Paso final de `release.sh`. | S | G2 | ∅ |

### B · UX y operación diaria

| ID | Mejora | Valor | Cómo | Esf. | Depende de | ≡ / nota |
|---|---|---|---|---|---|---|
| B1 | **Recorrido inicial** (60 s) y «cómo leer esta vista» | Directorio y SALELGI abren el artefacto sin conocer el libro: dónde están los mandos, qué es el caso Custom vs C·B·F, qué significa el chip ≡, cómo guardar un escenario. | 5 pasos con resaltado; se muestra una vez (localStorage); textos de interfaz, marcados como tales. | S–M | — | ∅ (texto de UI) |
| B2 | **Modo presentación / directorio** | Reunión de directorio: tipografía mayor, mandos ocultos, orden de lectura fijo (Resumen → Flujo → Sensibilidad → Legal → Trámites → Riesgos → Controles), flechas del teclado, indicador de página. | Estado `presentacion` en el shell; estilos `data-mode`. | M | C1 | ∅ |
| B3 | **Informe PDF completo** | Hoy se imprime vista a vista. Un «paquete de directorio» con portada, índice, vistas seleccionadas, pie con versión/fecha/edición reemplaza al PDF del libro para muchos usos. | Ruta de impresión que renderiza las vistas elegidas en secuencia con `@page`; Playwright `page.pdf()` para validar. | M–L | A10, C1 | ∅ |
| B4 | **Mandos**: deshacer/rehacer, reset por bloque, panel «qué cambié vs libro», campo numérico junto al slider, pegar valores | Hoy se ajusta con sliders y hay `reset` global; explorar escenarios exige precisión y memoria de lo cambiado. | Historial en el store (pila de entradas); `describePatch` ya existe para el diff. | M | — | ∅ |
| B5 | **Escenarios**: importar `.json` (hoy sólo exportar), duplicar, etiquetas, autor (campo de texto: no hay capacidad `user`), orden/filtro, comparar con gráficos y exportar la comparación | Convierte los escenarios en herramienta de trabajo entre socios; el JSON importable permite mover escenarios entre ediciones/versiones y respaldarlos. | Extender `ScenariosPanel`/`CompareDialog`; validar el JSON contra la versión del libro (`base`). | M | A1 | ∅ |
| B6 | «Copiar enlace» a vista + caso + escenario + foco | Compartir exactamente lo que se está viendo (ya existe el hash; falta el botón y la confirmación). | Botón en TopBar; `navigator.clipboard`. | S | — | ∅ |
| B7 | ⌘K ampliado | Incluir las 26 fuentes, rubros de CAPEX, líneas de OPEX, salidas del Motor por nombre Excel; historial de búsquedas. | Índice en `CommandMenu`. | S | — | ∅ |
| B8 | Explicaciones uniformes de «n/a», «no cruza», «LIBRO», «▲ por confirmar» | Que ningún valor no numérico quede sin razón visible (tooltip con el texto del glosario: p. ej. R3-5). | Componente `Why` con textos del `book.guia`. | S | r3 | ∅ |
| B9 | **Edición externa**: pantalla de entrada (confidencialidad, fecha de corte, contacto), y alcance por destinatario | Decisión pendiente de G5: qué ve el banco vs SALELGI; si conviene una tercera edición «banco» centrada en deuda/DSCR. | Decisión D-V2-6 + `make-externo.py` parametrizado por perfil. | S + decisión | G5 | ∅ |
| B10 | Idioma inglés (banca/proveedores extranjeros) | Trade-off duro: los textos vienen del libro en español; traducir en el artefacto rompe la regla de cero paráfrasis salvo que el libro sea bilingüe. **Recomendación: no en v2**; registrar como idea v3 ligada a Excel v4.0 bilingüe. | — | L | H4 | ⚠ |

### C · UI y sistema visual

| ID | Mejora | Valor | Cómo | Esf. | Depende de | ≡ / nota |
|---|---|---|---|---|---|---|
| C1 | **Auditoría visual vista por vista** con lista de comprobación | Jerarquía, densidad, alineación, `tabular-nums`, leyendas y etiquetas directas, contraste AA validado (claro y oscuro), estados de foco, textos truncados, estados vacíos. Captura Playwright de cada vista en 4 casos × 2 temas; hallazgos numerados. | Checklist + capturas en el contenedor (nunca del Mac); informe con antes/después propuesto. | M | §6 | ∅ |
| C2 | **Gráficos**: comportamiento unificado | Tooltip/crosshair en todos (RiskMatrix hoy sin hover; StackedBars parcial), «ver tabla» por gráfico, exportar PNG/SVG, ejes con unidad, etiquetas directas selectivas, versión imprimible sin hover. | Capa común `ChartFrame` (título, leyenda, tabla, exportar) + validador de paleta (`dataviz`) en ambos temas. | M | C1 | ∅ |
| C3 | KPI: micro-sparkline C·B·F, delta vs libro cuando hay cambios, glifo de estado coherente con 13 | Lectura ejecutiva más rápida; el lector ve de un vistazo si sus mandos mejoran o empeoran cada indicador respecto del libro. | Extender `KpiTile`. | S–M | — | ∅ |
| C4 | Tipografía y carga de fuentes | IBM Plex desde Google Fonts: parpadeo (FOUT) y dependencia de red; `size-adjust` en la pila de respaldo, `text-wrap: balance`, escala tipográfica documentada. Alternativa: subconjunto embebido (peso vs tamaño 16 MB máx.). | Ajustes CSS; decisión E3. | S | E3 | ∅ |
| C5 | QA completo del tema oscuro | Todas las vistas y gráficos con colores validados sobre `#0F1216/#161A20`; estados ● ▲ ■ legibles. | Capturas + validador. | S–M | C1 | ∅ |
| C6 | Iconografía y microcopy | Un solo set (lucide), verbos claros («Guardar» → «Guardado»), errores accionables con código de capacidad. | Revisión de textos de UI. | S | — | ∅ |
| C7 | **Layout responsivo (tablet/móvil)** | Responsividad parcial: 63 clases responsivas de Tailwind en toda la app y ninguna regla `@media` de ancho propia; el shell (mandos laterales, tablas anchas, gráficos SVG de ancho fijo) no fue diseñado para < 1024 px → en iPhone/iPad el artefacto muy probablemente no está resuelto (confianza media-alta; confirmar en F1 con capturas a 390/768 px). Uso real: abrir en reunión desde el teléfono. Mandos como hoja inferior, tablas → scroll propio o tarjetas, gráficos que se reescalan, ⌘K como botón. | Rediseño de shell para < 1024 px; pruebas en 390/768/1024 px. | L | decisión D-V2-3 | ∅ |
| C8 | Tokens exportables para Excel v4.0 | El artefacto define el sistema visual del libro v4.0 (doc 16/17): exportar tokens (colores, tipos, espaciados, formatos) como JSON consumible por el generador. | `tokens.json` + documento de sistema. | S | H4 | ∅ |

### D · Análisis de datos (profundidad analítica)

| ID | Mejora | Valor | Cómo | Esf. | Depende de | ≡ / nota |
|---|---|---|---|---|---|---|
| D1 | **Buscador de objetivos** (goal seek) | Preguntas de negociación que hoy exigen mover sliders a ciegas: tarifa mínima, CAPEX máximo, fee O&M máximo o apalancamiento máximo para una TIR/DSCR objetivo. | Bisección sobre el motor (rápida: 111 casos por evaluación no hacen falta; sólo el Custom); panel «Objetivo». | M | D-V2-2 | ⚠ el número no existe en el libro → etiqueta + propuesta v4.0 (10 §H ya hace «deuda máxima») |
| D2 | **Sensibilidad dinámica** | Tornado recalculado para el Custom actual con ± % elegibles; matriz bidimensional con ejes a elección (hoy sólo CAPEX × tarifa del Motor). | Casos ad hoc calculados por el motor (misma lógica de `caseDefinitions`). | M | D-V2-2 | ⚠ |
| D3 | **Comparador con gráficos** | FCF, equity, DSCR y acumulados superpuestos para 2–3 escenarios; tabla de deltas; exportación. | Extender `CompareDialog` con `Series`. | M | B5 | ∅ |
| D4 | **Puente entre dos escenarios** (descomposición del ΔTIR entrada por entrada) | Explica *por qué* cambia la TIR entre el libro y un escenario (o entre dos escenarios), como el puente v2.0→v3.0 de 10 §A.3 pero generalizado. | Descomposición secuencial (one-at-a-time) con el motor; cascada. | M–L | D-V2-2 | ⚠ |
| D5 | Simulación probabilística (Monte Carlo) de TIR/DSCR | Muy valorada por directorios; pero **no está en el libro** y exigiría hoja MC en Excel v4.0 para mantener ≡. **Recomendación: v3, no v2.** | Distribuciones sobre 5–8 drivers; 2.000 corridas en Web Worker. | L | H4 | ⚠⚠ |
| D6 | **Riesgos → impacto** | Cada riesgo parametrizable de 11 con «ver impacto» (preset): retraso red +12 (existe), licencia +3 (existe), tarifa, peaje, disponibilidad, reemplazo, aranceles. | Mapa riesgo → parche de entradas; sólo donde el libro ya define el parámetro. | S–M | — | ∅ |
| D7 | **Trazabilidad** «por qué este número» | `Trace` ya muestra el nombre Excel; añadir «copiar referencia», enlace a la fila de Fuentes y árbol de dependencias de un nivel (usando el resolutor `names.ts`). | Popover de trazabilidad. | M | — | ∅ |
| D8 | Lectura ejecutiva viva: pruebas | Las frases de Resumen cambian con los mandos; probar que cada frase sigue siendo coherente en los 4 casos y en escenarios extremos (p. ej. TIR «n/a»). | Casos en A3. | S | A3 | ∅ |
| D9 | Indicadores adicionales ya calculables desde el Motor (sin cálculo nuevo) | P. ej. LCOE vs tarifa por año, año de recuperación del equity, cobertura de la demanda, VAN por MWp. Revisar con Jorge cuáles aportan al lector antes de añadir. | Lista candidata → decisión. | S | — | ∅ si son celdas/salidas del libro; ⚠ si no |

### E · Rendimiento y compatibilidad

| ID | Mejora | Valor | Cómo | Esf. | Depende de | ≡ / nota |
|---|---|---|---|---|---|---|
| E1 | **Medir y garantizar el rendimiento** | Cada mando recalcula 111 casos y todas las vistas; no está medido (confianza media de que sea fluido en Mac, baja en móvil). Objetivo: < 50 ms por cambio; si no, `debounce` en sliders, memoización por caso y motor en Web Worker. | Marcas `performance.measure`; informe por vista. | S–M | — | ∅ |
| E2 | Matriz de navegadores/dispositivos | Safari macOS/iOS, Chrome, Edge, app móvil de Claude; impresión en cada uno. | Lista + pruebas manuales (Jorge, 10 min) + Playwright (Chromium/WebKit) en el contenedor. | S | — | ∅ |
| E3 | Dependencia de red (Google Fonts) | Redes corporativas pueden bloquear fonts.googleapis → la interfaz cae al respaldo del sistema. Opciones: aceptar (pila de respaldo cuidada), o embeber subconjunto WOFF2 (≈ 150–250 KB). | Decisión + prueba sin red. | S–M | C4 | ∅ |
| E4 | Presupuesto de tamaño y CSP | Mantener < 1,5 MB por edición; revisar dependencias del bundle; sin hosts externos salvo fuentes. | Informe en `to-fragment.mjs` (existe) + umbral en CI. | S | G1 | ∅ |

### F · Accesibilidad

| ID | Mejora | Valor | Cómo | Esf. |
|---|---|---|---|---|
| F1 | Teclado completo (mandos, tablas, diálogos, ⌘K), orden lógico, foco visible | Uso sin ratón; requisito de calidad. | Auditoría con Playwright + corrección. | M |
| F2 | Lectores de pantalla: `aria` en gráficos, tabla alternativa por gráfico (C2), etiquetas en sliders | Hoy 23 `aria-label` y 5 gráficos con rol; incompleto. | Revisión por componente. | S–M |
| F3 | Contraste AA en ambos temas | Validador de paleta sobre los tokens reales; corregir ▲ (#996311/#E0A63A) si falla sobre superficies. | Script `validate_palette.js`. | S |
| F4 | `prefers-reduced-motion` y sin dependencia del color | Verificado: ninguna regla `prefers-reduced-motion` ni clase `motion-reduce` en la app (las animaciones son pocas: `focus-flash`, transiciones); estados siempre con glifo (● ▲ ■ ◇) además de color — comprobar en gráficos. | CSS + revisión. | S |

### G · Gobierno, versiones, mantenimiento y seguridad

| ID | Mejora | Valor | Cómo | Esf. | Depende de | Nota |
|---|---|---|---|---|---|---|
| G1 | **Repositorio git privado** (GitHub) con `build30/`, `artefacto/`, docs de método y CI | El contenedor es efímero y los tarballs en OneDrive son frágiles (sin historial, sin diff, riesgo de sobrescritura). Un repo da historial, revisión de cambios y CI (verify + live.test + exclusion + E2E en cada commit). Trade-off: requiere cuenta/organización GitHub y decidir qué NO va al repo (libros con datos: quedan en OneDrive). | Decisión D-V2-1; `git init` desde los tarballs; GitHub Actions con LibreOffice para el cruce. | M | Jorge | Recomendado |
| G2 | **`release.sh`** (cadena completa) | r3 → `extract_model` → `extract_book` → `verify` → `live.test` → `build:editions` → E2E → SHA → publicar candidato → promover; changelog automático de textos (diff de `book.json`, como en doc 22 §4) y de valores. Elimina errores humanos en cada republicación. | Script + plantilla de doc de release. | M | A3 | — |
| G3 | **Artefacto «candidato»** (tercera URL privada) | Revisar cada versión antes de tocar las URL oficiales; promover = republicar el mismo fragmento en la oficial. Etiquetar cada publicación (`label`). | Publicar `out/interno/fragment.html` como artefacto nuevo «Candidato»; regla de promoción. | S | — | — |
| G4 | Panel «Acerca de / versión» (A9) + historial de versiones | Trazabilidad para el lector y para soporte. | Datos de `book.meta` + changelog embebido. | S | A9 | — |
| G5 | **Reglas de escritura en `db`** | Hoy cualquier persona de la organización con el enlace puede eliminar o sobrescribir escenarios. Opciones: `rules` por nivel de compartición (`interact` lee, `admin` escribe), confirmaciones dobles, papelera (borrado lógico), copia de seguridad JSON periódica. | Declarar `rules` en `capabilities` (contrato 0.2.42) + borrado lógico. | S–M | A1 | — |
| G6 | Registro de destinatarios y aviso de confidencialidad (externo) | Saber quién recibió qué versión; revisión humana antes de compartir además del `check:exclusion`. | Tabla en la guía + pantalla de entrada (B9). | S | G5 gate | — |
| G7 | **Guía de uso y de actualización + `BOOTSTRAP.md`** | Cierre F6 del doc 21 y, sobre todo, cómo restaurar el entorno desde cero (§6) — sin esto cada chat nuevo pierde una hora. | Documento en `Artefacto interactivo/` y en el repo. | S–M | F6 | — |
| G8 | Bitácora de decisiones (D-*, R3-*, D-V2-*) con estado | Gobierno del proyecto: qué está ratificado y qué pendiente; visible en la edición interna (vista Guía) o en la guía. | Sección en `book.guia` o documento. | S | — | — |
| G9 | Copias de seguridad de las publicaciones | Guardar cada fragmento publicado con su SHA (hoy sólo F5 r1 en tarball y `out_published_F5r1/` del contenedor). | Carpeta `publicados/` en repo/OneDrive. | S | — | — |

### H · Contenido y modelo (co-evolución con el libro)

| ID | Mejora | Valor | Cómo | Esf. | Depende de | ≡ / nota |
|---|---|---|---|---|---|---|
| H1 | **Cerrar G-L2 → r3 → sustitución → re-extraer → republicar** | Prerrequisito de casi todo: el artefacto debe seguir al libro vigente. | Puntos de G-L2 + R3-1…R3-5 → `pipeline.sh` → tres motores + render Excel (protocolo del doc 20) → sustitución con aprobación → G2 cadena. | M | Jorge | ∅ |
| H2 | Observaciones abiertas del modelo (§1) | Decidir: margen O&M de Exergy 0 (¿fee o costo?); convertir 04!D74/D75 y palancas de 09 en entradas de 01 (elimina los 9 «LIBRO» congelados); memo de 03; F10 ▲. | Decisiones de Jorge → generador (v3.2 o v4.0). | S–M | Jorge | ∅ |
| H3 | **Tracker de «por confirmar»** (19 marcadas) | Operación real del proyecto: estado, responsable, fecha y nota por cada dato por confirmar y por cada duda legal (15); vive en `db` como **metadatos** (el contenido sigue siendo del libro). | Colección `confirmaciones`; vista en Supuestos/Legal (interno). | M | A1, G5 | ∅ (metadatos) |
| H4 | **Excel v4.0** (doc 16) | Definir cuándo el rediseño del libro toma el sistema visual del artefacto (C8) y qué analítica nueva (D1/D2/D4/D5) entra al libro para conservar ≡. Proyecto aparte con su propio plan. | Decisión de secuencia: v2 del artefacto primero, v4.0 después (recomendado). | L | — | — |
| H5 | Datos externos vivos (tarifas/pliego ARCONEL, tipo de cambio) | Idea v3: el libro es la fuente; traer datos vivos rompe ≡ y añade dependencia de red. **No en v2.** | — | — | — | ⚠⚠ |

## 4. Priorización propuesta (olas) y decisiones que debe tomar Jorge

**Criterios:** primero lo que reduce riesgo y protege lo construido (verificación, gobierno), luego lo que aumenta el valor de uso diario sin tocar la coherencia con el libro, y al final la analítica nueva que exige decisión de fondo.

| Ola | Contenido | Resultado esperado |
|---|---|---|
| **0 · Prerrequisitos** | §6 (restaurar y verificar) · A1 · A2 · **H1** (G-L2 → r3 → sustitución → republicar) · G7 (`BOOTSTRAP.md`) · decisión D-V2-1 (repo) | Entorno reproducible; artefacto alineado con el libro vigente; capacidades probadas de verdad |
| **1 · Sólido** | A3 · A4 · A5 · A6 · A7 · A8 · A9 · A10 · A11 · G2 · G3 · G4 · G5 · G9 · C1 · C4 · C5 · C6 · F1–F4 · E1 · E2 · B6 · B7 · B8 | Cero regresiones detectables por máquina; auditoría visual con hallazgos corregidos; release reproducible con candidato |
| **2 · Útil** | B1 · B2 · B3 · B4 · B5 · D3 · D6 · D7 · D8 · D9 · C2 · C3 · H3 · B9 · G6 · G8 | Herramienta de trabajo para directorio/socios: presentación, informe PDF, escenarios completos, riesgos → impacto, trazabilidad |
| **3 · Analítica nueva** | D1 · D2 · D4 · (D5 → v3) · C7 · C8 · E3 · H4 · (B10 → v3) | Sólo tras D-V2-2/D-V2-3; co-evolución con Excel v4.0 |

| Decisión | Pregunta | Recomendación de Claude (con trade-off) |
|---|---|---|
| **D-V2-1** | ¿Repositorio git privado para generador + artefacto? | Sí (GitHub privado de Exergy): historial, CI, restauración en 5 min. Coste: crear la organización/cuenta; los libros con datos siguen en OneDrive. |
| **D-V2-2** | ¿Se admiten cálculos que no existen en el libro (goal seek, tornado dinámico, puente, Monte Carlo)? | Sí, con dos condiciones: etiqueta visible «cálculo del artefacto con la lógica del Motor (sin celda en el libro)» y compromiso de llevarlos a Excel v4.0. Alternativa estricta: nada que no tenga celda (pierde D1/D2/D4). |
| **D-V2-3** | ¿Móvil/tablet dentro del alcance v2? | Sí para tablet (≥ 768 px) y lectura en móvil (sin edición de mandos); edición completa en móvil sólo si se usará de verdad (esfuerzo L). |
| **D-V2-4** | ¿Artefacto «candidato» separado para revisión antes de tocar las URL oficiales? | Sí; coste nulo, evita publicar roto. |
| **D-V2-5** | ¿Quién puede escribir escenarios en `db`? | Sólo editores (`admin`), lectura para el resto; borrado lógico. |
| **D-V2-6** | Alcance de la edición externa: ¿una sola (SALELGI/banco) o perfiles? | Una sola en v2 con pantalla de confidencialidad; perfil «banco» sólo si el banco pide DSCR-centric. |
| **D-V2-7** | ¿Secuencia con Excel v4.0? | Artefacto v2 (olas 0–2) primero; v4.0 del libro después, tomando C8. |

## 5. Estructura de trabajo propuesta

Su esquema (1 pulir la idea → 2 plan objetivo → 3 plan de acción → 4 revisión final y aprobación → 5 puesta en marcha) es correcto como **columna vertebral por ola**; propongo tres mejoras: una **Fase 0 de restauración y línea base** antes de opinar (sin ella no hay base verificable), una **Fase 1 de diagnóstico con evidencia** (auditoría del artefacto vivo + sus puntos de G2 → un solo backlog), y ejecutar **por olas cortas con ciclo cerrado** (construir → verificar → candidato → revisión → promover → documentar) en lugar de una única puesta en marcha grande — porque el contenedor es efímero y porque cada ola debe dejar el artefacto publicable.

| Fase | Contenido | Entregable | Gate |
|---|---|---|---|
| **F0 · Restauración y línea base** | §6: restaurar desde OneDrive, `npm install`, verify + live.test + build:editions + check:exclusion, leer los dos artefactos publicados (registro para republicar), comparar SHA con lo publicado. | Nota «Estado verificado» (1 página) | — (obligatoria) |
| **F1 · Diagnóstico con evidencia** | Auditoría del artefacto vivo (C1 capturas en contenedor, A3 exploratorio, E1 medición) + puntos de Jorge de G2/G5 + observaciones del libro → **backlog v2 consolidado** (este §3 actualizado, con hallazgos reales, IDs y estimaciones). | Doc 24 «Diagnóstico y backlog v2» | — |
| **F2 · Pulir la idea (su paso 1)** | Visión v2 (para quién, qué cambia, qué no), criterios de priorización, olas, decisiones D-V2-1…7. | Doc 25 «Visión y olas v2» | **G-A** (aprobación de visión, olas y decisiones) |
| **F3 · Plan objetivo (su paso 2)** — por ola | Objetivos, **criterios de aceptación medibles** (p. ej. «E2E 100 % verde en 15 × 4 × 2 × 2», «recalculo < 50 ms», «AA en ambos temas»), método de verificación, definición de terminado (≡ libro, pruebas, doc, fuentes). | Sección por ola | — |
| **F4 · Plan de acción (su paso 3)** — por ola | Tareas, secuencia, dependencias, riesgos, qué necesita de Jorge (decisiones, pruebas en su cuenta, ~30–45 min por ola), estimación. | Plan de la ola | **G-B** (su paso 4: revisión final y aprobación de la ola) |
| **F5 · Ejecución por olas (su paso 5)** | Ciclo por ola: construir → verificar (tests + cruce) → publicar **candidato** → revisión de Jorge por puntos numerados → corregir → **promover** a las URL oficiales → doc NN + fuentes + memoria. Dentro del plan aprobado rige «sigue a tu criterio». | Artefactos republicados + doc de ola | **G-Ola n** (aceptación) |
| **F6 · Cierre** | F6 del doc 21 (carpeta `Artefacto interactivo/`, guía, doc 07, memoria), retrospectiva, backlog remanente → v3. | Doc de cierre | **G-Cierre** |

**Principios de ejecución:** una ola a la vez; cambios pequeños y verificables; nunca romper ≡ libro (todo cálculo nuevo etiquetado o llevado a v4.0); toda decisión con ID y estado; cada sesión termina con punto de guardado fuera del contenedor (repo/tarball + doc); las capturas se hacen en el contenedor; las pruebas que exigen la cuenta de Jorge se agrupan en un solo bloque por ola para no fragmentar su tiempo.

## 6. Guion de arranque del nuevo chat (Fase 0)

1. **Leer** la memoria del proyecto (`exergy-gpm-artefacto.md`) y los docs 20–22 de `Documentación/`; guardar este doc 23 en `Documentación/` si no está.
2. **Restaurar** el entorno: con la carpeta `Exergy` conectada, traer al contenedor desde `…/Modelo GPM 5MWp/_borrador_v3.1/Fuentes técnicas v3.1/`: `artefacto_F5_r2_fuentes.tar.gz`, `build30_r3pre_generador_2026-09-08.tar.gz`, `referencias_regresion_v3.1.zip`, `scripts_v3.1.tar.gz` (y `artefacto_F5_r1_fuentes.tar.gz` por los fragmentos publicados). Descomprimir en `scratchpad/artefacto/` (app, engine, data, data_r3pre) y `scratchpad/v31/` (build30, out30, refs, verif); crear el enlace `/root/gpm13 → scratchpad/v31`. `npm install` en `app/` y `engine/`; Python 3.11 con `openpyxl`; LibreOffice (`/mnt/skills/public/xlsx/scripts/recalc.py`) y el empaquetador (`/mnt/skills/examples/web-artifacts-builder/scripts/bundle-artifact.sh`, ruta usada por `npm run build:bundle`).
3. **Verificar** la línea base: `cd engine && npx tsx test/verify.ts` (91.546 celdas, 0 fuera) · `cd app && npx tsx test/live.test.ts` (PASS) · `DATA_DIR=../data_r3pre npx tsx test/live.test.ts` (PASS) · `npm run build:editions` (interno/externo + `check:exclusion` OK; ≈ 1.098 / 1.059 KB) · opcional `python3 build30/crosscheck_engine.py out30/Modelo_FV_5MWp_GPM_v3.1_raw.xlsx xcheck 6` (6 muestras ≈ 2 min).
4. **Registrar los artefactos publicados** para poder republicarlos desde este chat: `Artifact action: "read"` con cada URL del §1 (la herramienta rechaza publicar sobre un artefacto que la conversación no ha leído). Republicar siempre con `url` de la oficial (o del candidato), `label` de versión y **sin** cambiar favicon ni `capabilities` salvo decisión.
5. **Reportar** «Estado verificado» y presentar §3–§5 con las decisiones D-V2-1…7. No ejecutar nada más hasta G-A.
6. Recordar: G-L2/G2/G5 siguen abiertos; el raíz v3.0 no se toca; Excel en el Mac sólo con aviso previo; capturas sólo en el contenedor.

## 7. Anexo · rutas, comandos y referencias

- OneDrive (conector Exergy): `Exergy/Energía Fotovoltaica/Proyectos/Manta/Análisis Financiero/Modelo GPM 5MWp/` → `Documentación/`, `_borrador_v3.1/` (r2, `Fuentes técnicas v3.1/`, `pruebas/`, `render_excel/`, `superadas/`), `Fuentes técnicas/`, `Renders PDF/`. En `device_bash`: `$HOME/mnt/Exergy/Energía Fotovoltaica/…`.
- Contenedor (tras §6): `/root/gpm13 → scratchpad/v31/` (`build30/` generador v3.1 HEAD con `extract_model.py`, `extract_book.py`, `xlformula.py`, `crosscheck_engine.py`, `pipeline.sh`, `regress30.py`, `shadow30.py`, `check_render.py`; `out30/` r2 y r3-pre); `scratchpad/artefacto/{app,engine,data,data_r3pre}`; `scratchpad/shots/` (host.mjs, f5.mjs).
- Pipeline del libro: `REF=/root/gpm13/out30/Modelo_FV_5MWp_GPM_v3.1_calc.xlsx ./pipeline.sh Modelo_FV_5MWp_GPM_v3.1_r3` (regresión por etiqueta vs r2; `--tol 1e-6`); Resumen: `MODEL=…_calc.xlsx ./pipeline_res.sh Modelo_FV_5MWp_Resumen_Directorio_v3.1_r3`; tres motores + render Excel: protocolo del doc 20 / memoria («Cómo se hizo el render/tercer motor»).
- Cadena del artefacto: `extract_model.py RAW CALC data` → `extract_book.py data data/book.json` → `cp data/book.json app/src/model/book_v31.json` → `engine: npx tsx test/verify.ts` (escribe `inputs_v31.json`/oráculo) → `app: npm run make:externo && npx tsx test/live.test.ts && npm run build:editions` → publicar `out/interno/fragment.html` (URL interna) y `out/externo/fragment.html` (URL externa).
- Motor: `engine/src/engine.ts` (`irr` ≡ LibreOffice ScIrr + `IRR_GUARD_BELOW_MINUS1`), `caseDefinitions.ts` (111 casos), `inputs.ts`; copia idéntica en `app/src/engine/`.
- Textos vivos: `app/src/model/formula.ts` (evaluador), `names.ts` (resolutor), `book.ts` (tipos; `sheets[*].labels_f` = columna F estática, usada por Flujo).
- Sistema visual (doc 17): acento `#2A5BD7`/`#6D96F0`; ● `#2E7D57`/`#5DBB8A`; ▲ `#996311`·`#B7791F`/`#E0A63A`; ■ `#B23A32`/`#E5665D`; ◇ `#6F7987`/`#8F99A8`; C·B·F `#2B2F36/#6B7280/#A9AEB6`; categórica `#2A5BD7 #D9722C #159C6E` (oscuro `#4A8CEC #D65E2B #1FA476`); fondos `#F4F5F7/#FFFFFF/#FAFBFC` y `#0F1216/#161A20/#1C2129`; IBM Plex; es-EC.
- Fuentes legales: Project claude.ai «Marco Legal FV Ecuador — Exergy» (Atlas Regulatorio v2, Informe F3 v1.1, Auditoría F1–F2); doc 18 = conciliación.
