# 28 · Pre-revisión del borrador r2 (Excel v3.1) para G-L2 — guía de 30 minutos

**Proyecto:** Modelo FV 5,0 MWp Montecristi → Gran Piazza Machala (SALELGI S.A. · gerencia Exergy)
**Fecha:** 11-sep-2026 · **Autor:** Claude (Anthropic) para Exergy EXG S.A.S., a petición de Jorge A. Baquerizo («what is G-L2… proceed with that»)
**Antecedentes:** doc 18 (conciliación legal, decisiones D-L1…D-L9 aprobadas), doc 19 (changelog v3.1 r2), doc 22 (R3-1…R3-5), doc 27 (D-V2-9).

## 1. Qué es G-L2 y por qué es la ruta crítica

**G-L2** es su aprobación del **borrador r2 del libro Excel v3.1** (`_borrador_v3.1/Modelo_FV_5MWp_GPM_v3.1_r2.xlsx` y su Resumen Directorio) tras revisarlo hoja por hoja. Es la única compuerta que sigue abierta desde el 08-sep y bloquea la cadena: **G-L2 → r3** (generador HEAD con R3-1…R3-5 + sus puntos) → tres motores + render Excel → **sustitución del raíz** `Modelo_FV_5MWp_GPM_v3.0.xlsx` y del Resumen (v3.0 → `superadas/`, con su aprobación explícita) → re-extracción → **el artefacto pasa a leer r3**. Mientras no ocurra, el libro «oficial» de la carpeta sigue siendo la v3.0 (con sus exploraciones del 08-sep) y el artefacto muestra la v3.1 r2: dos superficies con Custom distinto (D-V2-8 ya lo resolvió: el canónico es el `V31`; falta materializarlo).

**Qué le pido:** no una auditoría (ya está hecha: tres motores, 91.546 celdas, render sin cortes), sino su **juicio sobre lo que sólo usted puede decidir**: redacción legal, estimaciones de costo, definiciones del Custom y de los casos, y cualquier cosa que no le convenza. Responda con puntos numerados («03-2: …») o con «G-L2 aprobado» si no hay puntos.

## 2. Cómo revisar en 30 minutos

1. Abra el **PDF del render** `_borrador_v3.1/render_excel/Modelo_FV_5MWp_GPM_v3.1_r2 (render Excel, libro completo).pdf` (66 páginas): es exactamente lo que imprime su Excel. Páginas por hoja: 00 1–3 · 00b 4–8 · **01 9–12** · **02 13–18** · **03 19–21** · 04 22–26 · 05 27–29 · 06 30–32 · 07 33–36 · 08 37–40 · 09 41–45 · 10 46–54 · **11 55–56** · **12 57–60** · 13 61–64 · Motor 65–66.
2. Dedique el tiempo a las hojas en **negrita** (donde está el 95 % del cambio: 01, 02, 03, 11, 12); las demás sólo cambian en lo que indica la tabla §3.
3. Abra el `.xlsx` r2 sólo si quiere mover un mando (los cuatro casos, `Aplica_DedAd`) o ver una fórmula. No hace falta guardar nada: r3 se regenera desde el generador.
4. Lo que **ya está verificado** y no necesita su tiempo: identidad numérica con la v3.0 (110 casos, 0 diferencias), Custom = sus diez valores del 04-sep, 78/79 controles ● (el ▲ es deliberado), render sin cortes, Resumen ≡ modelo.

## 3. Lista de comprobación por hoja

Origen de los conteos: comparación r2 vs v3.0 entregado (`ops/gl2/diff_r2_vs_v30.json`, textos por conjunto) y doc 19. «Usted» = lo que sólo usted puede juzgar.

| # | Hoja (págs.) | Qué cambió (r2 vs v3.0) | Ya verificado por Claude | **Usted** |
|---|---|---|---|---|
| 00-1 | 00_Portada (1–3) | Textos estáticos: 0 cambios; cambian los textos **vivos** (lectura ejecutiva «Viabilidad» y «Fiscal y regulación», tornado top-9 con la barra 15) | Fórmulas 418 = 418; render 3 págs. | ¿La lectura ejecutiva dice lo que usted diría al directorio? (2 párrafos, pág. 1) |
| 00b-1 | 00b_Guía (4–8) | +26 / −4 textos: grupo **E · Marco legal y permisos** (7 términos), FAQ sobre la certificación de la deducción, «15 palancas»; 5 páginas (antes 4) | Conteos de glosario/FAQ; en r3 pasan a dinámicos (R3-2) | Tono y precisión de los 7 términos nuevos (pág. 6–7) |
| 01-1 | 01_Supuestos (9–12) | +19 / −16 notas: fecha de corte 08-sep, Atlas v2.0, `Fecha_Peaje` (DT Cuarta; D.E. 176), `Tasa_IVA`, `Tributos_Locales`, `Tasa_Deuda` (BCE ago-2026 6,79 %), P-01/P-14; **nueva entrada §G `Aplica_DedAd` (Sí)**; `N_Por_Confirmar` 18 → 19 | Nombres 314 → 317 (+`Aplica_DedAd`, `Fin_RC09`, `Fin_RC10`); `Meses_Construccion = Mes_COD_Cron` = 21 | **Confirme los 10 valores del Custom** (D1 · 04-sep): SALELGI compra el terreno · peaje 0 · tarifa +2 %/año · disponibilidad 97 % · escalación CAPEX 0 · degradación adicional 1 %/año · fee O&M 16 $/kWp · OPEX +2 %/año · deuda 100 % al 7,5 %. Sus cambios del 08-sep en el raíz (Comprador = Exergy, tarifa 0 %, `Deuda_Financia_Terreno` = Sí) quedan **descartados** por D-V2-8 — dígalo si alguno debe entrar |
| 01-2 | 01_Supuestos | `Aplica_DedAd` = «Sí» por defecto («por confirmar») | Caso 111 cuantifica el «No»: TIR 9,42 % / accionista 13,78 % | ¿El defecto debe ser «Sí» (optimista, con certificación) o «No» (prudente)? Afecta al Custom del artefacto |
| 02-1 | 02_Legal (13–18) | +150 / −101 textos; fórmulas 8 → 21: matriz **25 filas** (20 revisadas, 5 nuevas: Ley 2026, Sentencia CC 112-21-IN/25, retenciones 2026, suelo rural LOTRTA, servidumbre y altura); 5 candados actualizados (4 y 5 en fórmula viva); arquitectura contractual con cifras vivas y **consulta DG 17.ª**; 15 zonas grises con P-xx | Textos vivos evaluados ≡ Excel (94 textos); F1-01 del artefacto ya corregido | Redacción de las 5 filas nuevas y del blindaje comercial (candado 3); ¿mantiene la consulta DG 17.ª como instrumento opcional? |
| 02-2 | 02_Legal | Zona gris #17 reescrita (P-01/P-14, TIR viva del caso 111); #15 vs 18-dic-2026 marcada resuelta | — | ¿Está de acuerdo en dar por resuelta la #15? |
| 03-1 | 03_Tramites (19–21) | +60 / −40 textos; fórmulas 502 → 564: 17 hitos (RC-00 pre-consulta, RC-03 ARCONEL-UTA, **RC-04 Registro Ambiental**, RC-08a/b/c, **RC-09 meses 7–8**, RC-10 mes 12, RC-15 servidumbre); `Mes_COD_Cron` dinámico = 21 (COD jul-2028); costo 252,5 k → **194,5 k** | Control **F12** (vigencia 6 meses de la factibilidad) ●; COD ● | **Estimaciones «por confirmar» que fijé para el Gantt:** RC-04 5.000 · RC-08a 3.000 · RC-08b 2.000 · RC-08c 5.000 · RC-15 5.000 (total 194,5 k ≪ rubro 9 = 250 k). ¿Las acepta como marcadores o prefiere otras cifras? |
| 03-2 | 03_Tramites | Memo estático (3.ª página): Licencia (+3 meses) y retraso por red (+12) con cifras de la sombra al 08-sep | En el artefacto son presets vivos (≡ memo: +12 → TIReq 16,45 %, DSCR 0,701) | ¿Conserva el memo estático en el libro o lo sustituye por una remisión al artefacto? (R3 opcional) |
| 04 | 04_Energia (22–26) | Sin cambios de texto ni fórmula | 548 = 548 | — |
| 05-1 | 05_CAPEX (27–29) | 5 notas de rubro reescritas (inversores: arancel 2026 P-03, IVA 0 % zona gris P-04; estructura y CT/MT: P-03; **rubro 9: Registro Ambiental, IVA 12 % ≈ 15 % × 80 % servicios**); sin cambio de valores | 385 = 385 fórmulas | ¿La nota del rubro 9 (Registro vs Licencia como contingencia) refleja su criterio? |
| 06 | 06_OPEX (30–32) | Sin cambios en r2; **r3-pre** cambia la nota 06!H7 (R3-3: «≈ 21,3 $/kWp-año») | — | — |
| 07-1 | 07_Fiscal (33–36) | `DedAd_Anual = IF(Aplica_DedAd="Sí",1,0) × MIN(…)`; chip «◇ n/a» cuando no aplica; caja RLRTI 28.6.g / P-01 | 821 = 821; H14 ● | ¿La explicación de la certificación ambiental previa es correcta para el directorio? |
| 08 | 08_Flujo (37–40) | Sin cambios en r2; en r3: nota 08!F7 y fórmula E7 con la guardia R3-5 | — | Ver §4 (D-V2-9) |
| 09 | 09_Exergy (41–45) | Sin cambios | 595 = 595 | Observación abierta H2: `Fee_OM` 16 = `Costo_OM_Exergy` 16 → **margen O&M de Exergy 0**. ¿Es intencional para v3.1 o lo corregimos en r3 (fee 16 con costo menor)? |
| 10-1 | 10_Sensibilidad (46–54) | Tornado **15 barras** (nueva «Sin deducción adicional», 1,22 pp, 5.ª por amplitud); fórmulas 928 → 943 | Ranking verificado | **Barra 3 degenerada:** «Escalación tarifa +2 %/año» tiene amplitud 0 porque su Custom ya lleva +2 %. ¿La redefinimos como «+1 pp sobre el Custom» en r3 (cambio de motor pequeño) o la dejamos y lo anotamos? |
| 11-1 | 11_Riesgos (55–56) | +37 / −23 textos; **15 riesgos** (11 revisados + 4 nuevos: cambio regulatorio general 3 × 2, vacío reglamentario/litigio Ley 2026 2 × 2, político-institucional 2 × 2, fiscal Exergy 2 × 2); red 3 × 3; fiscal reescrito con cifras vivas del caso 111 | Probabilidades e impactos según D-L8 | ¿Está de acuerdo con las puntuaciones de los 4 nuevos y con red 3 × 3? |
| 12-1 | 12_Fuentes (57–60) | +21 / −9: `Aplica_DedAd` en «por confirmar», aranceles 2026, lista de pendientes P-xx del Atlas, simplificaciones nuevas, fuentes (Atlas v2.0, Ley 2026, Sentencia CC, 005/25, MAATE-2025-0002-R, retenciones, SENAE/COMEX/ISD, BCE ago-2026), historial v3.1 | Conteo «por confirmar» = 19 | Vistazo a las fuentes nuevas (pág. 59–60); en r3 se quitan los valores v3.0 de los «por qué» (R3-4) |
| 13-1 | 13_Controles (61–64) | 79 controles: **F12** (vigencia factibilidad) y **H14** (deducción aplicable) nuevos; encabezado actualizado | 78/79 ●; el ▲ es **F10 «Custom ≠ Base en 4 entradas»** (bloque B de su Custom) | ¿Acepta que F10 quede en ▲ como estado esperado, o preferiría que F10 compare contra la definición del Custom (siempre ●)? |
| M-1 | Motor_Sens (65–66) | Fila 34 «Deducción adicional aplicable (1/0)»; caso **111** «Sin deducción adicional»; TIR del accionista con semilla 2 % | 91.546 celdas ≡ motor JS; sombra 0 dif.; Excel/Mac ≡ en 4 casos + 111 | — |
| R-1 | Resumen Directorio r2 (12 págs.) | Tornado 15 barras; hoja «Legal y riesgos» con 3.er hecho regulatorio (deducción condicionada), ruta crítica re-planificada, riesgo fiscal nuevo | 246 nombres ≡ modelo; 111/111 | Dos páginas de «Legal y riesgos»: ¿es el mensaje que quiere llevar al directorio? |

## 4. Lo que r3 cambiará además de sus puntos (ya en el generador HEAD; 0 diferencias de valor frente a r2)

| ID | Cambio | Hoja |
|---|---|---|
| R3-1 | «110 casos» → `N_CASES` (111) en 8 textos | 00b, 10, 12, 13 |
| R3-2 | 00b!B2 con conteos dinámicos (7 FAQ / 38 términos) | 00b |
| R3-3 | Nota 06!H7 «≈ 21,3 $/kWp-año» | 06 |
| R3-4 | `CONFIRM_WHY` sin los valores v3.0 (9 textos) | 12 |
| R3-5 | Guardia de la TIR del accionista: `IF(IRR(EQ;0,02)<=-1;"n/a";IRR(EQ;0,02))` en Motor y 08!E7 + nota 08!F7 + glosario «n/a» | Motor, 08, 00b |
| **D-V2-9** (11-sep) | La prueba A2 demostró que **Excel** ya devuelve la raíz real en los casos donde LibreOffice da la espuria (−303 %) → en Excel la guardia R3-5 nunca actúa; se conserva como red de seguridad para LibreOffice (oráculo). El motor JS replica a Excel (12/12). **Recomendación:** mantener R3-5 tal cual; añadir en 00b una frase: «Excel y el artefacto muestran la TIR real del accionista; si el flujo no tiene TIR única en dominio, «n/a»» | 00b |
| Propuesta | Si aprueba 10-1 «+1 pp», entra en r3 como R3-6 | 10, Motor |

## 5. Después de G-L2 (lo hago yo; usted sólo aprueba la sustitución)

1. Aplicar sus puntos + R3-1…R3-6 en el generador → `pipeline.sh …_v3.1_r3` (regresión por etiqueta vs r2, `--tol 1e-6`) y `pipeline_res.sh`.
2. Tres motores (LibreOffice · sombra · **Excel/Mac** en copias `_prueba`, con aviso) + render Excel (`check_render`: 0 cortes).
3. Le presento el resumen de r3 (una página) → **usted aprueba la sustitución** → v3.0 → `superadas/`; r3 pasa a ser el raíz y el Resumen; `Fuentes técnicas/` v3.1; doc 07 actualizado.
4. Re-extracción → `verify` 91.546/0 → `release.sh "r3"` → candidatos → «promover» → **artefacto ≡ libro r3**.

## 6. Plantilla de respuesta

`G-L2 aprobado` — o — puntos numerados con el código de la tabla: `01-1 OK` · `01-2 No (prudente)` · `03-1 RC-04 → 8.000` · `10-1 +1 pp` · `13-1 F10 → comparar contra la definición` · `09 fee 16 / costo 12`… Cada punto lo respondo con la evidencia en el doc de r3.
