import { useMemo, type ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { KpiTile, type StripValue } from "@/components/KpiTile";
import { Trace } from "@/components/Live";
import { Status } from "@/components/Status";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { SCALAR_LABELS } from "@/engine";
import { fmtMonthYear, fmtNum, fmtPct, fmtUSD, fmtUSDCompact, fmtX } from "@/lib/format";
import { CASES, type CaseId, type ViewId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { capexTable, escalas, type RubroRow } from "@/model/capex";
import { CASE_B, CASE_C, CASE_F, CASE_X } from "@/model/cases";
import { useModel } from "@/model/store";

/**
 * CAPEX (hoja 05_CAPEX): tabla de rubros del caso seleccionado con `capexTable` (misma aritmética que la hoja, verificada),
 * composición por rubro, comparativo de los cuatro casos (filas 32–36), factores del caso (27–30), reemplazo y
 * desmantelamiento (38–41), drivers de escala (43–54) y las notas (1)…(12) del libro. Los textos con cifras de la hoja
 * (C18, C21, D27, E29, I33:I36, E40:J41, D54, F54) se reproducen con los valores vivos del caso.
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

const hdr = (s: string): ReactNode => s.split("\n").map((l, k) => (k === 0 ? l : <span key={k}><br />{l}</span>));
const CASE_ORDER = [CASE_X, CASE_C, CASE_B, CASE_F] as const;

/** Fila de la tabla de rubros (7–24): rubro del caso o agregado de la hoja. */
interface FilaCapex {
  key: string;
  n?: number;
  nombre: ReactNode;
  r?: RubroRow;
  cap?: number;
  iva?: number;
  ivaPct?: number;
  usdWp?: number;
  nota?: number;
  /** total (negrita), agregado normal o informativo (atenuado) */
  kind: "rubro" | "total" | "agregado" | "info";
  /** texto libre en la columna capitalizable (fila 24: %) */
  capText?: string;
  /** texto en la columna «IVA %» (fila 23: «FODINFA →») y su valor en «IVA [USD]» */
  ivaLabel?: string;
}

export function Capex({ caseId }: Props) {
  const m = useModel();
  const ci = m.idx(caseId);
  const c = m.cases[ci];
  const meta = CASES.find((x) => x.id === caseId)!;
  const i = m.inputs, d = m.derived, p = c.params;
  const s = c.result.scalars;
  const K = s[SCALAR_LABELS.K], IVA = s[SCALAR_LABELS.IVA], fKeff = s[SCALAR_LABELS.fKeff], fEsc = s[SCALAR_LABELS.fEsc];
  const AC = s[SCALAR_LABELS.AC], ha = s[SCALAR_LABELS.ha], Krep = s[SCALAR_LABELS.Krep], Decom = s[SCALAR_LABELS.Decom];
  const tbl = useMemo(() => capexTable(i, d, p), [i, d, p]);
  const P1000 = p.P * 1000;
  const kbase = fKeff * fEsc > 0 ? K / (fKeff * fEsc) : 0;                       // 05!D28 (bottom-up a factor 1 con potencia y contrato del caso)
  const { escWp, escWac } = escalas(i, p);                                      // 01!C147:C148 con la potencia del caso
  const labels = m.book.capex.labels;
  const L: Record<string, string> = m.book.sheets["05_CAPEX"]?.labels ?? {};
  const H = m.book.capex.headers;
  const others = CASES.filter((x) => x.id !== caseId);
  const strip = (f: (k: number) => number, fmt: (v: number) => string): StripValue[] => others.map((x) => ({ caseId: x.id, text: fmt(f(m.idx(x.id))) }));
  const kOf = (k: number) => m.cases[k].result.scalars[SCALAR_LABELS.K];
  const ivaOf = (k: number) => m.cases[k].result.scalars[SCALAR_LABELS.IVA];

  // ---- textos de la hoja con cifras vivas ---------------------------------------------------------------------------------------
  const contrato = p.cont === 1;
  /** D27 (minúscula) e I33:I36 (mayúscula): «fijo X $/Wp» o «bottom-up × f», más la escalación si la hay. */
  const definicionBase = (k: number, cap: boolean): string => {
    const kfix = i.Esc_CAPEX_Fijo_Wp[k], fK = i.Esc_Factor_CAPEX[k] ?? 1;
    const fijo = typeof kfix === "number" && kfix > 0;
    return fijo ? `${cap ? "Fijo" : "fijo"} ${fmtNum(kfix, 3)} $/Wp` : `${cap ? "Bottom-up" : "bottom-up"} × ${fmtNum(fK, 2)}`;
  };
  const escTxt = (k: number): string => { const dK = i.Esc_Escalacion_CAPEX[k] ?? 0; return dK > 0 ? ` · precios +${fmtPct(dK, 1)}/año` : ""; };
  const sufijo: Record<number, string> = {
    [CASE_X]: " · caso de trabajo: gobierna 04–09 y la portada",
    [CASE_C]: " · rango alto del estudio CAPEX/OPEX (jul-2026)",
    [CASE_B]: ` · costo real para el grupo con gerencia Exergy al ${fmtPct(i.Fee_Gerencia_Pct, 0)}`,
    [CASE_F]: ` · precio «llave en mano todo incluido» del deck v4 (22-jul-2026) para cliente externo; exige ${fmtPct(kOf(CASE_B) > 0 ? kOf(CASE_F) / kOf(CASE_B) - 1 : 0, 0, "always")} vs costo real → verificar con 3 cotizaciones EPC`,
  };
  const definicionCaso = (k: number) => `${definicionBase(k, true)}${escTxt(k)}${sufijo[k] ?? ""}`;   // I33:I36
  const e29 = `Precios de ${fmtMonthYear(i.Fecha_Precios)} escalados al ${fmtPct(p.dK, 1)}/año: tramo −1 (${fmtPct(i.Fase_m1, 0)}) a ${fmtNum(Math.max(0, d.Anios_Precios - 1), 1)} años · tramo 0 a ${fmtNum(d.Anios_Precios, 1)} años (COD ${fmtMonthYear(i.Fecha_COD)}). Bloque B: C ${fmtPct(i.Esc_Escalacion_CAPEX[1] ?? 0, 0)} · B ${fmtPct(i.Esc_Escalacion_CAPEX[2] ?? 0, 0)} · F ${fmtPct(i.Esc_Escalacion_CAPEX[3] ?? 0, 0)}`;
  const c18 = `Gerencia del proyecto — Exergy (${fmtPct(i.Fee_Gerencia_Pct, 0)} del valor del proyecto)`;
  const c21 = `Terreno comprado por SALELGI (${fmtNum(ha, 1)} ha × ${fmtNum(i.Precio_Terreno_ha, 0)} $/ha + ${fmtPct(i.Costos_Transaccion_Terreno_Pct, 1)} transacción) — sólo si Comprador_Terreno = SALELGI`;
  const c24 = `% del CAPEX industrial en obra civil (vida fiscal ${i.Vida_Fiscal_Civil} años)`;
  const j40 = i.Reemplazo_Pagador === "SALELGI"
    ? `Capex de SALELGI en t = ${i.Reemplazo_Anio}, depreciado en ${Math.min(i.Vida_Fiscal_Equipos, i.Horizonte - i.Reemplazo_Anio)} años (07, 08)`
    : i.Reemplazo_Pagador === "Exergy"
      ? `Gasto de Exergy en t = ${i.Reemplazo_Anio} con cargo a la reserva del fee de O&M (09); sin efecto en SALELGI`
      : "Sin reemplazo (neutro ≡ v2.0): la reserva de inversores se supone dentro del fee de O&M";
  const f54 = `Escala_Wp = ${fmtNum(escWp, 3)} · Escala_Wac = ${fmtNum(escWac, 3)} (potencia ${fmtNum(p.P, 0)} kWp / ${fmtNum(AC, 0)} kWac; ε = ${fmtNum(i.Exponente_Escala, 2)}). Pesos estimados; validez 3–8 MWp.`;
  const driversOk = i.rubros.every((rb) => Math.abs(rb.drvWp + rb.drvWac + rb.drvFijo - 1) <= 0.0005);
  const d54 = driversOk ? "● drivers OK" : "■ drivers ≠ 100 %";

  // ---- filas de la tabla de rubros (7–24) -------------------------------------------------------------------------------------------
  const filas: FilaCapex[] = useMemo(() => {
    const out: FilaCapex[] = tbl.rubros.map((r) => ({ key: `r${r.n}`, n: r.n, nombre: r.nombre, r, cap: r.capitalizable, iva: r.iva, ivaPct: r.ivaPct, usdWp: r.usdWp, nota: r.n, kind: "rubro" }));
    out.push({ key: "f16", n: 10, nombre: labels["16"], cap: tbl.contingencia.capitalizable, iva: tbl.contingencia.iva, usdWp: tbl.contingencia.usdWp, nota: 10, kind: "agregado" });
    out.push({ key: "f17", nombre: labels["17"], cap: tbl.subtotal.capitalizable, iva: tbl.subtotal.iva, usdWp: tbl.subtotal.usdWp, kind: "total" });
    out.push({ key: "f18", n: 11, nombre: c18, cap: tbl.gerencia.capitalizable, iva: tbl.gerencia.iva, ivaPct: i.iva_fee, usdWp: tbl.gerencia.usdWp, nota: 11, kind: "agregado" });
    out.push({ key: "f19", nombre: labels["19"], cap: tbl.total.capitalizable, iva: tbl.total.iva, usdWp: tbl.total.usdWp, kind: "total" });
    out.push({ key: "f20", nombre: labels["20"], cap: tbl.total_con_iva, usdWp: tbl.total_con_iva / P1000, kind: "agregado" });
    out.push({ key: "f21", n: 12, nombre: c21, cap: tbl.terreno, usdWp: tbl.terreno / P1000, nota: 12, kind: "agregado" });
    out.push({ key: "f22", nombre: labels["22"], cap: tbl.total_con_terreno, usdWp: tbl.total_con_terreno / P1000, kind: "total" });
    out.push({ key: "f23", nombre: labels["23"], cap: tbl.aranceles_isd, ivaLabel: "FODINFA →", iva: tbl.fodinfa, kind: "info" });
    out.push({ key: "f24", nombre: c24, capText: fmtPct(tbl.pct_civil, 1), kind: "info" });
    return out;
  }, [tbl, labels, c18, c21, c24, i.iva_fee, P1000]);

  const usd = (v: number | undefined) => (v === undefined ? "" : fmtNum(v, 0));
  const pct = (v: number | undefined, dec = 0) => (v === undefined ? "" : fmtPct(v, dec));
  const rubroCols: Column<FilaCapex>[] = [
    { key: "n", label: H.B, align: "right", mono: true, muted: true, render: (f) => (f.n === undefined ? "" : String(f.n)) },
    { key: "nombre", label: H.C, render: (f) => f.nombre },
    { key: "D", label: hdr(H.D), align: "right", render: (f) => usd(f.r?.base) },
    { key: "E", label: H.E, align: "right", muted: true, render: (f) => pct(f.r?.pctComp) },
    { key: "F", label: hdr(H.F), align: "right", render: (f) => usd(f.r?.costo) },
    { key: "G", label: H.G, align: "right", muted: true, render: (f) => pct(f.r?.pctExt) },
    { key: "H", label: hdr(H.H), align: "right", render: (f) => usd(f.r?.exterior) },
    { key: "I", label: hdr(H.I), align: "right", muted: true, render: (f) => pct(f.r?.arancelPct) },
    { key: "J", label: hdr(H.J), align: "right", render: (f) => usd(f.r?.arancel) },
    { key: "K", label: hdr(H.K), align: "right", render: (f) => usd(f.r?.fodinfa) },
    { key: "L", label: hdr(H.L), align: "right", render: (f) => usd(f.r?.isd) },
    { key: "M", label: hdr(H.M), align: "right", render: (f) => (f.r ? (contrato ? <span className="text-ink-3">{usd(f.r.arancelIsd)}</span> : usd(f.r.arancelIsd)) : "") },
    { key: "N", label: hdr(H.N), align: "right", render: (f) => f.capText ?? usd(f.cap) },
    { key: "O", label: hdr(H.O), align: "right", muted: true, render: (f) => f.ivaLabel ?? pct(f.ivaPct) },
    { key: "P", label: hdr(H.P), align: "right", render: (f) => usd(f.iva) },
    { key: "Q", label: H.Q, align: "right", render: (f) => (f.usdWp === undefined ? "" : fmtNum(f.usdWp, 3)) },
    { key: "R", label: H.R, align: "center", muted: true, render: (f) => (f.nota === undefined ? "" : <span title={m.book.capex.notas[f.nota - 1]} className="cursor-help underline decoration-dotted underline-offset-2">({f.nota})</span>) },
  ];

  // ---- composición por rubro: las tres mayores del Custom en --cat-1..3 (orden fijo), el resto en gris ------------------------------
  const custom = useMemo(() => capexTable(i, d, m.cases[CASE_X].params), [i, d, m.cases]);
  const top3 = useMemo(() => [...custom.rubros].sort((a, b) => b.capitalizable - a.capitalizable).slice(0, 3).map((r) => r.n), [custom]);
  const colorDe = (n: number) => { const k = top3.indexOf(n); return k >= 0 ? `var(--cat-${k + 1})` : "var(--c-base)"; };
  const compos = [
    ...tbl.rubros.map((r) => ({ n: r.n, nombre: r.nombre, v: r.capitalizable, color: colorDe(r.n) })),
    { n: 10, nombre: labels["16"], v: tbl.contingencia.capitalizable, color: "var(--c-base)" },
    { n: 11, nombre: c18, v: tbl.gerencia.capitalizable, color: "var(--c-base)" },
  ];
  const maxV = Math.max(1, ...compos.map((x) => x.v));

  // ---- comparativo de los cuatro casos (32–36) ---------------------------------------------------------------------------------------
  interface CasoRow { k: number; id: CaseId }
  const casosRows: CasoRow[] = CASE_ORDER.map((k) => ({ k, id: CASES.find((x) => m.idx(x.id) === k)!.id }));
  const casoCols: Column<CasoRow>[] = [
    { key: "caso", label: "Caso", render: (r) => <Swatch id={r.id} /> },
    { key: "K", label: hdr("Total sin IVA\n[USD]"), align: "right", render: (r) => fmtNum(kOf(r.k), 0) },
    { key: "wp", label: "$/Wp", align: "right", render: (r) => fmtNum(kOf(r.k) / (m.cases[r.k].params.P * 1000), 3) },
    { key: "iva", label: hdr("IVA\n[USD]"), align: "right", render: (r) => fmtNum(ivaOf(r.k), 0) },
    { key: "con", label: hdr("Total con IVA\n[USD]"), align: "right", render: (r) => fmtNum(kOf(r.k) + ivaOf(r.k), 0) },
    { key: "fk", label: hdr("Factor CAPEX\nefectivo"), align: "right", muted: true, render: (r) => fmtX(m.cases[r.k].result.scalars[SCALAR_LABELS.fKeff], 3) },
    { key: "fe", label: hdr("Factor de\nescalación"), align: "right", muted: true, render: (r) => fmtX(m.cases[r.k].result.scalars[SCALAR_LABELS.fEsc], 3) },
    { key: "def", label: "Definición del CAPEX en el caso", render: (r) => <span className="text-ink-2">{definicionCaso(r.k)}</span> },
  ];

  // ---- drivers (44–54) ------------------------------------------------------------------------------------------------------------------
  const drvCols: Column<RubroRow>[] = [
    { key: "n", label: "#", align: "right", mono: true, muted: true, render: (r) => String(r.n) },
    { key: "nombre", label: "Rubro", render: (r) => r.nombre },
    { key: "wp", label: "% Wp", align: "right", render: (r) => fmtPct(r.drvWp, 0) },
    { key: "wac", label: "% Wac", align: "right", render: (r) => fmtPct(r.drvWac, 0) },
    { key: "fijo", label: "% fijo", align: "right", render: (r) => fmtPct(r.drvFijo, 0) },
    { key: "sum", label: "Σ", align: "right", muted: true, render: (r) => fmtPct(r.drvWp + r.drvWac + r.drvFijo, 0) },
    { key: "ctl", label: "Control", align: "center", render: (r) => (Math.abs(r.drvWp + r.drvWac + r.drvFijo - 1) <= 0.0005 ? <Status kind="ok">ok</Status> : <Status kind="risk">≠ 100 %</Status>) },
  ];

  // ---- reemplazo y desmantelamiento (39–41) -----------------------------------------------------------------------------------------------
  interface PartidaRow { key: string; partida: string; t: number; base: string; usd: number; pagador: string; nota: string; trace: string }
  const partidas: PartidaRow[] = [
    { key: "rep", partida: "Reemplazo de inversores", t: i.Reemplazo_Anio, base: `${fmtNum(i.Reemplazo_USD_Wac, 2)} $/Wac × ${fmtNum(AC, 0)} kWac`, usd: Krep, pagador: i.Reemplazo_Pagador, nota: j40, trace: "Reemplazo_USD · 05!H40" },
    { key: "dec", partida: "Desmantelamiento al final del horizonte", t: i.Horizonte, base: `${fmtPct(p.dec, 1)} del CAPEX industrial`, usd: Decom, pagador: "SALELGI", nota: "Gasto deducible de SALELGI en t = Horizonte (desmontaje y disposición, neto de chatarra); 0 en el Base, 2 % en el tornado", trace: "Desmantelamiento_USD · 05!H41" },
  ];
  const partidaCols: Column<PartidaRow>[] = [
    { key: "p", label: "Partida", render: (r) => <>{r.partida}<br /><Trace name={r.trace} /></> },
    { key: "t", label: "Año (t)", align: "right", mono: true, render: (r) => String(r.t) },
    { key: "b", label: "Base", render: (r) => r.base },
    { key: "u", label: "USD", align: "right", render: (r) => fmtUSD(r.usd) },
    { key: "pg", label: "Pagador", render: (r) => r.pagador },
    { key: "n", label: "Nota", render: (r) => <span className="text-ink-2">{r.nota}</span> },
  ];

  /** Notas (1)…(12) de la hoja; las cuatro notas generales (filas 85–88) se muestran junto a su sección. */
  const notas = m.book.capex.notas.filter((t) => /^\(\d+\)/.test(t));
  const notaTitulo = (t: string) => { const k = t.indexOf(". "); return k > 0 && k < 60 ? t.slice(0, k) : t.slice(0, 48); };

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="CAPEX" sheet="05_CAPEX">
        <Chip title="05_CAPEX!D27">{definicionBase(ci, false)}{escTxt(ci)}</Chip>
        <Chip title="05_CAPEX!D30">Factor del caso × {fmtNum(tbl.factor_caso, 4)}</Chip>
        <Chip>Contrato de Inversión: {contrato ? "Sí" : "No"}</Chip>
        <Chip>IVA recuperable: {p.iva === 1 ? "Sí" : "No"}</Chip>
        <Chip title="01_Supuestos!C147:C148">Escala_Wp {fmtNum(escWp, 3)} · Escala_Wac {fmtNum(escWac, 3)}</Chip>
        <Chip>{fmtNum(p.P, 0)} kWp · {fmtNum(AC, 0)} kWac</Chip>
      </ViewHeader>

      {/* ---------------------------------------------------------------- cifras clave (19–24) */}
      <Section title={`CAPEX del caso ${meta.label}`} guide="cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo · USD nominales sin IVA salvo indicación">
        <div className="grid grid-cols-2 gap-x-6 gap-y-5 md:grid-cols-3 lg:grid-cols-6">
          <KpiTile
            label="Total CAPEX industrial SALELGI (sin IVA, sin terreno)"
            excelName="CAPEX_Total · 05!N19"
            value={fmtUSDCompact(K, 2)}
            compare={<>{fmtNum(K / P1000, 3)} $/Wp · subtotal EPC {fmtUSDCompact(tbl.subtotal.capitalizable, 2)} + gerencia {fmtPct(i.Fee_Gerencia_Pct, 0)}</>}
            strip={strip(kOf, (v) => fmtUSDCompact(v, 2))}
          />
          <KpiTile
            label="IVA del CAPEX"
            excelName="IVA_Total · 05!P19"
            value={fmtUSDCompact(IVA, 2)}
            compare={<>total industrial con IVA {fmtUSDCompact(tbl.total_con_iva, 2)} · {p.iva === 1 ? "recuperable (capital de trabajo)" : "no recuperable: se capitaliza"}</>}
            strip={strip(ivaOf, (v) => fmtUSDCompact(v, 2))}
          />
          <KpiTile
            label="Terreno comprado por SALELGI"
            excelName="Terreno_SALELGI · 05!N21"
            value={fmtUSDCompact(tbl.terreno, 2)}
            compare={<>comprador: {i.Comprador_Terreno} · total con terreno {fmtUSDCompact(tbl.total_con_terreno, 2)}</>}
          />
          <KpiTile
            label="Aranceles + ISD dentro del total"
            excelName="Aranceles_ISD · 05!N23"
            value={fmtUSDCompact(tbl.aranceles_isd, 2)}
            compare={<>FODINFA aparte {fmtUSD(tbl.fodinfa)}{contrato ? " · con Contrato de Inversión los aranceles e ISD son 0" : ""}</>}
          />
          <KpiTile label={c24} excelName="Pct_CAPEX_Civil · 05!N24" value={fmtPct(tbl.pct_civil, 1)} compare={<>obra civil {fmtUSDCompact(tbl.rubros[5]?.capitalizable ?? 0, 2)}</>} />
          <KpiTile
            label="Bottom-up a factor 1 (potencia y contrato de 01)"
            excelName="05!D28"
            value={fmtUSDCompact(kbase, 2)}
            compare={<>× factor CAPEX efectivo {fmtNum(fKeff, 3)} × escalación {fmtNum(fEsc, 4)} = factor del caso {fmtNum(tbl.factor_caso, 4)}</>}
          />
        </div>
      </Section>

      {/* ---------------------------------------------------------------- tabla de rubros (6–24) */}
      <Section
        title="Rubros del CAPEX"
        guide="columnas de la hoja; costo del caso = costo base × factor del caso × (drivers × escalas); «(n)» abre la nota del rubro al pasar el cursor"
        aside={<Trace name="CAPEX_Total · IVA_Total" cell="05_CAPEX!B6:R24" />}
      >
        <DataTable columns={rubroCols} rows={filas} rowKey={(f) => f.key} size="sm" emphasize={(f) => f.kind === "total"} muted={(f) => f.kind === "info"} />
        <Note>{L["87"]}</Note>
      </Section>

      {/* ---------------------------------------------------------------- composición + factores del caso */}
      <div className="grid gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(300px,2fr)]">
        <Section title="Composición del CAPEX industrial por rubro" guide="capitalizable sin IVA del caso; en color las tres partidas mayores, el resto en gris" aside={<Trace cell="05_CAPEX!N7:N18" />}>
          <ul className="flex flex-col divide-y divide-hairline text-[12px]">
            {compos.map((x) => (
              <li key={x.n} className="grid grid-cols-[22px_minmax(0,200px)_minmax(0,1fr)_92px_56px_64px] items-center gap-x-3 py-1.5" style={{ fontVariantNumeric: "tabular-nums" }}>
                <span className="font-mono text-[11px] text-ink-3">{x.n}</span>
                <span className="truncate text-ink" title={x.nombre}>{x.nombre}</span>
                <span className="h-3 w-full overflow-hidden rounded-[2px] bg-surface-2">
                  <span className="block h-full rounded-[2px]" style={{ width: `${Math.max(0, (x.v / maxV) * 100)}%`, background: x.color, opacity: 0.85 }} />
                </span>
                <span className="text-right text-ink">{fmtUSD(x.v)}</span>
                <span className="text-right text-ink-3">{fmtPct(K > 0 ? x.v / K : 0, 1)}</span>
                <span className="text-right text-ink-3">{fmtNum(x.v / P1000, 3)} $/Wp</span>
              </li>
            ))}
            <li className="grid grid-cols-[22px_minmax(0,200px)_minmax(0,1fr)_92px_56px_64px] items-center gap-x-3 border-t border-ink-3/40 py-1.5 font-semibold text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
              <span />
              <span className="col-span-2 truncate">{labels["19"]}</span>
              <span className="text-right">{fmtUSD(K)}</span>
              <span className="text-right">{fmtPct(1, 0)}</span>
              <span className="text-right">{fmtNum(K / P1000, 3)} $/Wp</span>
            </li>
          </ul>
        </Section>

        <Section title={`Factores del caso ${meta.label}`} guide="filas 27–30 de la hoja con los parámetros del caso">
          <dl className="flex flex-col divide-y divide-hairline text-[12.5px]">
            <Fila label={`Definición del CAPEX ${meta.label}`} value={`${definicionBase(ci, false)}${escTxt(ci)}`} trace={<Trace cell="05_CAPEX!D27" />} />
            <Fila label={labels["28"] ?? "Bottom-up a factor 1 (potencia y contrato de 01)"} value={fmtUSD(kbase)} trace={<Trace cell="05_CAPEX!D28" />} />
            <Fila label="Escalación de precios hasta la compra" value={fmtX(fEsc, 4)} trace={<Trace name="Factor_Escalacion" cell="05_CAPEX!D29" />} />
            <Fila label="Factor CAPEX efectivo" value={fmtX(fKeff, 4)} trace={<Trace name="Factor CAPEX efectivo" cell="Motor_Sens fila 53" />} />
            <Fila label="Factor del caso (× cada rubro), incl. escalación" value={fmtX(tbl.factor_caso, 4)} trace={<Trace name="Factor_Caso" cell="05_CAPEX!D30" />} />
          </dl>
          <Note>{e29}</Note>
          <Note className="text-ink-3">{L["88"]}</Note>
        </Section>
      </div>

      {/* ---------------------------------------------------------------- comparativo (26–36) */}
      <Section title={L["26"] ?? "Caso Custom y comparativo de los cuatro casos (sin IVA, incl. gerencia, sin terreno)"} guide="orden fijo Custom · Conservador · Base · Favorable; la fila resaltada es el caso seleccionado" aside={<Trace cell="05_CAPEX!C32:I36 · Motor_Sens filas 38–39" />}>
        <DataTable columns={casoCols} rows={casosRows} rowKey={(r) => r.id} size="sm" selected={(r) => r.id === caseId} />
        <Note className="text-ink-3">{L["86"]}</Note>
      </Section>

      {/* ---------------------------------------------------------------- reemplazo y desmantelamiento (38–41) */}
      <Section title={L["38"] ?? "Reemplazo de inversores y desmantelamiento"} guide="capa de diseño compartida por los cuatro casos; el pagador lo fija el contrato de O&M">
        <DataTable columns={partidaCols} rows={partidas} rowKey={(r) => r.key} size="sm" />
      </Section>

      {/* ---------------------------------------------------------------- drivers (43–54) */}
      <Section
        title={L["43"] ?? "Drivers de escala de cada rubro (· por confirmar)"}
        guide="qué parte de cada rubro sigue a la potencia DC (Wp), a la AC (Wac) o es fija; costo = base × [%Wp × Escala_Wp + %Wac × Escala_Wac + %fijo]"
        aside={<Trace name="Drv_Wp · Drv_Wac · Drv_Fijo" cell="05_CAPEX!D45:F53" />}
      >
        <DataTable columns={drvCols} rows={tbl.rubros} rowKey={(r) => String(r.n)} size="sm" />
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px]">
          <Status kind={driversOk ? "ok" : "risk"}>{d54.replace(/^[●▲■◇]\s*/, "")} <Trace name="Check_Drivers" cell="05_CAPEX!D54" /></Status>
          <span className="text-ink-2">{f54}</span>
        </div>
        <Note>{L["85"]}</Note>
      </Section>

      {/* ---------------------------------------------------------------- notas (72–84) */}
      <Section title={L["72"] ?? "Notas — alcance y fuente de cada rubro"} guide={`${notas.length} notas del libro · clic para desplegar`}>
        <div className="flex flex-col divide-y divide-hairline border-y border-hairline">
          {notas.map((t, k) => (
            <details key={k} className="group py-2">
              <summary className="flex cursor-pointer list-none items-start gap-2 text-[13px] font-medium text-ink hover:text-accent [&::-webkit-details-marker]:hidden">
                <span aria-hidden className="mt-[3px] w-3 shrink-0 text-[10px] text-ink-3 transition-transform group-open:rotate-90">▶</span>
                {notaTitulo(t)}
              </summary>
              <p className="mt-1.5 max-w-[92ch] pl-5 font-serif text-[13.5px] leading-[1.5] text-ink-2">{t}</p>
            </details>
          ))}
        </div>
      </Section>
    </div>
  );
}

// ------------------------------------------------------------------------------------------------ piezas locales
function Fila({ label, value, trace }: { label: ReactNode; value: ReactNode; trace?: ReactNode }) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-3 py-1.5">
      <dt className="text-ink-2">{label}</dt>
      <dd className="flex flex-col items-end text-right text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
        <span>{value}</span>
        {trace}
      </dd>
    </div>
  );
}

/** Muestra del caso: trazo (color + patrón) y nombre. */
function Swatch({ id, className }: { id: CaseId; className?: string }) {
  const meta = CASES.find((x) => x.id === id)!;
  return (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      <svg width="16" height="6" viewBox="0 0 16 6" aria-hidden>
        <line x1="0" y1="3" x2="16" y2="3" strokeWidth="2" style={{ stroke: `var(${meta.colorVar})`, strokeDasharray: `var(${meta.dashVar})` }} />
      </svg>
      <span className={cn(id === "custom" ? "text-accent" : "text-ink")}>{meta.label}</span>
    </span>
  );
}
