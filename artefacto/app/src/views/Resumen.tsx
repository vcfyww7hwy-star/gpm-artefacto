import { useMemo, type ReactNode } from "react";

import { KpiTile, type StripValue } from "@/components/KpiTile";
import { CintaAnual } from "@/components/charts/CintaAnual";
import { Tornado, type TornadoRow } from "@/components/charts/Tornado";
import { T_AXIS } from "@/engine";
import { fmtDate, fmtNum, fmtPct, fmtUSD, fmtUSDCompact, fmtX, fmtYears } from "@/lib/format";
import { CASES, type CaseId, type ViewId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { CASE_X, T_DEDAD, tornadoDefs } from "@/model/cases";
import { statusOf } from "@/model/book";
import { ORACLE, useModel } from "@/model/store";

interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

function Section({ title, guide, children, className }: { title: string; guide?: string; children: ReactNode; className?: string }) {
  return (
    <section className={cn("flex flex-col gap-3", className)}>
      <header className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
        <h2 className="text-[13.5px] font-semibold text-ink">{title}</h2>
        {guide && <p className="text-[12px] text-ink-3">{guide}</p>}
      </header>
      {children}
    </section>
  );
}

const GLYPH: Record<"ok" | "warn" | "risk" | "info", { g: string; cls: string }> = {
  ok: { g: "●", cls: "text-ok" },
  warn: { g: "▲", cls: "text-warn-text" },
  risk: { g: "■", cls: "text-risk" },
  info: { g: "◇", cls: "text-info" },
};

function Status({ kind, children, mono, className }: { kind: keyof typeof GLYPH; children: ReactNode; mono?: boolean; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[12px] text-ink-2", mono && "font-mono", className)}>
      <span aria-hidden className={cn("text-[10px] leading-none", GLYPH[kind].cls)}>{GLYPH[kind].g}</span>
      {children}
    </span>
  );
}

export function Resumen({ caseId, onNavigate }: Props) {
  const m = useModel();
  const ci = m.idx(caseId);
  const meta = CASES.find((c) => c.id === caseId)!;
  const i = m.inputs, d = m.derived;
  const tasa = i.Tasa_Descuento;
  const tir = m.num(ci, "TIR"), van = m.num(ci, "VAN"), tirEq = m.num(ci, "TIR_eq"), dscr = m.num(ci, "DSCR_min"), lcoe = m.num(ci, "LCOE"), pb = m.out(ci, "PB");
  const tarifaMWh = d.Tarifa_Evitable * 1000;
  const others = CASES.filter((c) => c.id !== caseId);
  const strip = (key: "TIR" | "VAN" | "TIR_eq" | "LCOE", fmt: (v: number | null) => string, below?: (v: number | null) => boolean): StripValue[] =>
    others.map((c) => {
      const v = m.num(m.idx(c.id), key);
      return { caseId: c.id, text: fmt(v), below: below ? below(v) : false };
    });
  const blocks = m.cases[ci].result.blocks;
  const dscrBlock = blocks.DSCR;
  const anioDscrMin = useMemo(() => {
    let best: number | null = null, bt = 0;
    dscrBlock.forEach((v, k) => { if (typeof v === "number" && (best === null || v < best)) { best = v; bt = T_AXIS[k]; } });
    return best === null ? null : bt;
  }, [dscrBlock]);
  const cobertura = m.num(ci, "Cob");
  const tirX = m.num(CASE_X, "TIR");
  const TORNADO = useMemo(() => tornadoDefs(m.book), [m.book]);
  const tornadoRows: TornadoRow[] = useMemo(
    () => TORNADO.map((t) => ({ id: t.id, label: m.live(m.book.sens.tornado_short[t.k]), lo: m.num(t.lo, "TIR"), hi: t.hi === null ? null : m.num(t.hi, "TIR"), note: m.live(m.book.sens.tornado[t.k].note), loName: m.cases[t.lo].name, hiName: t.hi === null ? null : m.cases[t.hi].name })),
    [m, TORNADO],
  );
  const top5 = useMemo(() => {
    const ref = tirX ?? 0;
    return [...tornadoRows]
      .map((r) => ({ r, amp: Math.max(r.lo ?? ref, r.hi ?? ref, ref) - Math.min(r.lo ?? ref, r.hi ?? ref, ref) }))
      .sort((a, b) => b.amp - a.amp)
      .slice(0, 5)
      .map((x) => x.r);
  }, [tornadoRows, tirX]);
  const codYear = Number(i.Fecha_COD.slice(0, 4));
  const sinDed = m.num(T_DEDAD, "TIR");
  const dedAnual = m.cases[CASE_X].result.scalars["Deducción adicional/año"];
  const capex = m.cases[ci].result.scalars["CAPEX industrial sin IVA"];
  const nCtrl = m.book.frozen.N_Controles as number, nOk = m.book.frozen.N_Controles_OK as number, nConf = m.book.frozen.N_Por_Confirmar as number;
  const estadoCustom = String(m.nameValue("Estado_Custom") ?? "");

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-7">
      {/* cabecera de la vista */}
      <header className="flex flex-col gap-2">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h1 className="text-[20px] font-semibold tracking-[-0.01em] text-ink">Proyecto FV Montecristi → GPM</h1>
          <p className="text-[12px] text-ink-3">
            {fmtNum(i.Potencia_DC / 1000, 1)} MWp · SALELGI S.A. · libro {ORACLE.version} · corte {fmtDate(ORACLE.fecha_analisis)} · USD nominal
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <Status kind={m.selfCheck.status === "ok" ? "ok" : m.selfCheck.status === "warn" ? "warn" : "risk"} mono>
            Motor ≡ Excel {m.selfCheck.compared - m.selfCheck.failed}/{m.selfCheck.compared} salidas · {ORACLE.cases.length} casos
          </Status>
          <Status kind={nOk === nCtrl ? "ok" : "warn"}>Controles del libro {nOk}/{nCtrl}</Status>
          <Status kind="warn">{nConf} supuestos por confirmar</Status>
          <Status kind={statusOf(estadoCustom)}>{estadoCustom.replace(/^[●▲■◇]\s*/, "")}</Status>
          {m.dirty > 0 && (
            <Status kind="info">
              sandbox: {m.dirty} entrada{m.dirty > 1 ? "s" : ""} distinta{m.dirty > 1 ? "s" : ""} del libro ·{" "}
              <button className="underline decoration-dotted underline-offset-2 hover:text-ink" onClick={m.reset}>volver al libro</button>
            </Status>
          )}
        </div>
      </header>

      {/* indicadores del caso seleccionado */}
      <Section title={`Los indicadores que deciden · caso ${meta.label}`} guide="cifra grande = caso seleccionado; debajo, los otros tres casos con su trazo">
        <div className="grid grid-cols-2 gap-x-8 gap-y-5 lg:grid-cols-4">
          <KpiTile
            label="TIR del proyecto (sin deuda)"
            excelName="TIR_Proyecto"
            value={tir === null ? "n/a" : fmtPct(tir, 2)}
            state={tir === null ? "neutral" : tir >= tasa ? "ok" : "risk"}
            compare={<>frente a la tasa exigida {fmtPct(tasa, 0)} {tir !== null && <span className={tir >= tasa ? "text-ok" : "text-risk"}>({(tir - tasa) * 100 >= 0 ? "+" : "−"}{fmtNum(Math.abs(tir - tasa) * 100, 2)} pp)</span>}</>}
            strip={strip("TIR", (v) => (v === null ? "n/a" : fmtPct(v, 2)), (v) => v !== null && v < tasa)}
          />
          <KpiTile
            label={`VAN @ ${fmtPct(tasa, 0)} (al COD)`}
            excelName="VAN_Proyecto"
            value={fmtUSDCompact(van, 1)}
            state={van === null ? "neutral" : van >= 0 ? "ok" : "risk"}
            compare={<>payback {typeof pb === "number" ? fmtYears(pb, 1) : String(pb)} desde el COD · CAPEX {fmtUSDCompact(capex, 2)} sin IVA</>}
            strip={strip("VAN", (v) => fmtUSDCompact(v, 1), (v) => v !== null && v < 0)}
          />
          <KpiTile
            label="TIR del accionista (con deuda)"
            excelName="TIR_Equity"
            value={tirEq === null ? "n/a" : fmtPct(tirEq, 2)}
            state="neutral"
            compare={
              <>
                deuda {fmtPct(i.Pct_Apalancamiento, 0)} al {fmtPct(i.Tasa_Deuda, 1)} · {i.Plazo_Deuda} años · DSCR mín{" "}
                <span className={dscr !== null && dscr < i.DSCR_Objetivo ? "text-risk" : "text-ink"}>{dscr === null ? "n/a" : fmtX(dscr, 2)}</span>
                {anioDscrMin !== null && <> en t = {anioDscrMin}</>} (objetivo {fmtX(i.DSCR_Objetivo, 2)})
              </>
            }
            strip={strip("TIR_eq", (v) => (v === null ? "n/a" : fmtPct(v, 2)))}
          />
          <KpiTile
            label="LCOE frente a la red"
            excelName="LCOE"
            value={lcoe === null ? "n/a" : `${fmtNum(lcoe, 1)} $/MWh`}
            state={lcoe === null ? "neutral" : lcoe <= tarifaMWh ? "ok" : "risk"}
            compare={<>tarifa evitable {fmtNum(tarifaMWh, 1)} $/MWh → ahorro {lcoe === null ? "—" : fmtPct(1 - lcoe / tarifaMWh, 0)} por kWh · sin impuestos</>}
            strip={strip("LCOE", (v) => (v === null ? "n/a" : `${fmtNum(v, 1)}`), (v) => v !== null && v > tarifaMWh)}
          />
        </div>
      </Section>

      {/* cinta anual */}
      <Section title="Cinta anual · flujo libre sin deuda y acumulado" guide="27 años en una tira: barras = flujo del año (construcción en gris oscuro), línea = acumulado, punto = payback · pase el cursor por un año">
        <CintaAnual
          t={T_AXIS}
          fcf={blocks.FCF_u}
          cum={blocks.Cum_u}
          lineColor={`var(${meta.colorVar})`}
          lineDash={`var(${meta.dashVar})`}
          codYear={codYear}
          payback={typeof pb === "number" ? pb : null}
        />
      </Section>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
        {/* qué mueve la tesis */}
        <Section title="Qué mueve la tesis" guide="las cinco palancas de mayor amplitud sobre el Custom (Δ TIR del proyecto, pp)">
          <Tornado rows={top5} ref={tirX ?? 0} />
          <button
            className="self-start text-[12px] text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid"
            onClick={() => onNavigate("sensibilidad")}
          >
            Ver el tornado completo, las matrices y la deuda →
          </button>
        </Section>

        {/* candados */}
        <Section title="Los cinco candados del régimen" guide="estado en vivo (02_Legal · Atlas Regulatorio v2.0, 08-sep-2026)">
          <ul className="flex flex-col divide-y divide-hairline text-[12.5px]">
            {m.book.legal.candados.map((c) => {
              const estado = m.live(c.estado);
              return (
                <li key={m.live(c.label)} className="grid grid-cols-[176px_minmax(0,1fr)] items-start gap-x-2 py-1.5">
                  <Status kind={statusOf(estado)} className="items-start leading-snug [&>span:first-child]:mt-1.5">{m.live(c.label)}</Status>
                  <span className="min-w-0 break-words text-ink-2"><span className="text-ink">{estado.replace(/^[●▲■◇]\s*/, "")}</span> · {m.live(c.criterio)}</span>
                </li>
              );
            })}
          </ul>
        </Section>
      </div>

      {/* lectura ejecutiva */}
      <Section title="Lectura ejecutiva" guide="conclusiones con cifras vivas; el detalle está en Legal, Flujo, Exergy y Sensibilidad">
        <dl className="grid gap-x-8 gap-y-4 font-serif text-[14px] leading-[1.45] text-ink md:grid-cols-2">
          <div>
            <dt className="mb-0.5 font-sans text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">Viabilidad</dt>
            <dd>El proyecto es legalmente viable y encaja en el régimen SGDA remoto; el encaje no depende de la Ley 2026 (en litigio). {fmtNum(i.Potencia_DC / 1000, 1)} MWp cubren el {cobertura === null ? "—" : fmtPct(cobertura, 0)} del consumo sin excedentes mensuales. El riesgo binario es la capacidad del alimentador.</dd>
          </div>
          <div>
            <dt className="mb-0.5 font-sans text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">Economía</dt>
            <dd>
              {tir === null ? "La TIR del caso no es calculable." : tir >= tasa ? `La rentabilidad del ${meta.label} supera la tasa exigida` : `La rentabilidad del ${meta.label} queda bajo la tasa exigida`}: TIR {tir === null ? "n/a" : fmtPct(tir, 1)} frente al {fmtPct(tasa, 0)} (VAN {fmtUSD(van)}). LCOE {lcoe === null ? "—" : fmtNum(lcoe, 0)} frente a {fmtNum(tarifaMWh, 0)} $/MWh de la red. Deciden la tarifa y el CAPEX.
            </dd>
          </div>
          <div>
            <dt className="mb-0.5 font-sans text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">Deuda</dt>
            <dd>La deuda lleva la TIR del accionista a {tirEq === null ? "n/a" : fmtPct(tirEq, 1)}, pero el DSCR mínimo cae a {dscr === null ? "n/a" : fmtX(dscr, 2)}{anioDscrMin !== null ? ` en t = ${anioDscrMin}` : ""}: con {fmtPct(i.Pct_Apalancamiento, 0)} al {fmtPct(i.Tasa_Deuda, 1)} a {i.Plazo_Deuda} años el banco no financia; la deuda máxima para {fmtX(i.DSCR_Objetivo, 2)} está en Sensibilidad §H.</dd>
          </div>
          <div>
            <dt className="mb-0.5 font-sans text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">Fiscal y regulación</dt>
            <dd>A favor: deducción adicional de {fmtUSD(dedAnual)}/año (topada al 5 % de los ingresos, condicionada a certificación ambiental previa: sin ella la TIR sería {sinDed === null ? "n/a" : fmtPct(sinDed, 1)}) e IVA recuperable. En contra: participación + IR, arancel + ISD y el peaje SGDA desde {fmtDate(i.Fecha_Peaje).slice(3)}. GPM es cliente AV1: el D.E. 32 le exige acreditar generación propia (18-dic-2026).</dd>
          </div>
        </dl>
      </Section>
    </div>
  );
}
