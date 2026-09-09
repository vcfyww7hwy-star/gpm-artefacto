import { Check, Download, GitCompareArrows, Save, Trash2, Upload } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { outcomeText, saveText, stamp } from "@/lib/export";
import { fmtDate, fmtPct, fmtUSDCompact, fmtX } from "@/lib/format";
import { useDb, errorCode, type Db } from "@/lib/capabilities";
import { cn } from "@/lib/utils";
import { computeAll } from "@/engine";
import { BASELINE_EXTRAS, BASELINE_INPUTS, useModel } from "@/model/store";
import { describePatch, diffExtras, diffInputs, kpiOf, newScenarioId, presetScenarios, SCENARIOS_COLLECTION, type Scenario } from "@/model/scenarios";

interface Props {
  onCompare: (scenarios: Scenario[]) => void;
}

type DbState = "pending" | "ready" | "absent";

/**
 * Escenarios: presets del memo de 03 (sesión) y escenarios guardados en la base del artefacto (`db`: compartidos por la
 * organización, en tiempo real). Cada escenario es un parche sobre el libro v3.1; «cargar» lo aplica a los Mandos,
 * «guardar como» crea uno con las entradas actuales, «actualizar» sobrescribe el activo, «comparar» abre la tabla lado a lado.
 */
export function ScenariosPanel({ onCompare }: Props) {
  const m = useModel();
  const [db, setDb] = useState<Db | null>(null);
  const [dbState, setDbState] = useState<DbState>("pending");
  const [saved, setSaved] = useState<Scenario[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [exportMsg, setExportMsg] = useState<string | null>(null);

  const presets = useMemo(() => presetScenarios(BASELINE_INPUTS), []);

  const exportJson = async () => {
    const body = { artefacto: "Modelo FV Montecristi → GPM", libro: m.book.meta.version, corte: m.book.meta.fecha_analisis, exportado: new Date().toISOString(),
      escenario: m.scenario?.nombre ?? null, entradas: m.inputs, extras: m.extras, kpi_custom: kpiOf(m.cases) };
    const o = await saveText(`entradas-${stamp()}.json`, JSON.stringify(body, null, 1));
    setExportMsg(outcomeText(o, "JSON"));
    window.setTimeout(() => setExportMsg(null), 4000);
  };

  useEffect(() => {
    let unsub: (() => void) | null = null;
    let alive = true;
    useDb().then((d) => {
      if (!alive) return;
      if (!d) { setDbState("absent"); return; }
      setDb(d);
      setDbState("ready");
      unsub = d.collection(SCENARIOS_COLLECTION).orderBy("actualizado", "desc").limit(200).onSnapshot(
        (snap) => setSaved(snap.docs.filter((x) => x.exists).map((x) => ({ id: x.id, ...(x.data() as Omit<Scenario, "id">) }))),
        (e) => setError(`Escenarios guardados no disponibles (${e.code}).`),
      );
    });
    return () => { alive = false; unsub?.(); };
  }, []);

  const current = useCallback((): Pick<Scenario, "patch" | "extras" | "kpi"> => ({
    patch: diffInputs(m.inputs, BASELINE_INPUTS),
    extras: diffExtras(m.extras, BASELINE_EXTRAS),
    kpi: kpiOf(m.cases),
  }), [m.inputs, m.extras, m.cases]);

  const saveAs = async () => {
    if (!db || !name.trim()) return;
    setBusy(true); setError(null);
    const id = newScenarioId();
    const now = new Date().toISOString();
    const body: Omit<Scenario, "id"> = { nombre: name.trim(), nota: note.trim(), base: m.book.meta.version, creado: now, actualizado: now, ...current() };
    try {
      await db.doc(`${SCENARIOS_COLLECTION}/${id}`).set(body as unknown as Record<string, unknown>);
      m.markScenario({ id, nombre: body.nombre });
      setName(""); setNote("");
    } catch (e) {
      setError(errorCode(e) === "quota_exceeded" ? "La base del artefacto está llena: elimine escenarios antiguos." : `No se pudo guardar (${errorCode(e)}).`);
    } finally { setBusy(false); }
  };

  const updateActive = async () => {
    if (!db || !m.scenario || m.scenario.id.startsWith("preset-")) return;
    setBusy(true); setError(null);
    try {
      await db.doc(`${SCENARIOS_COLLECTION}/${m.scenario.id}`).update({ ...current(), actualizado: new Date().toISOString() } as unknown as Record<string, unknown>);
    } catch (e) { setError(`No se pudo actualizar (${errorCode(e)}).`); } finally { setBusy(false); }
  };

  const remove = async (id: string) => {
    if (!db) return;
    setBusy(true); setError(null);
    try {
      await db.doc(`${SCENARIOS_COLLECTION}/${id}`).delete();
      if (m.scenario?.id === id) m.markScenario(null);
      setSelected((s) => s.filter((x) => x !== id));
    } catch (e) { setError(`No se pudo eliminar (${errorCode(e)}).`); } finally { setBusy(false); setConfirmDelete(null); }
  };

  const toggleSelect = (id: string) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : s.length >= 3 ? s : [...s, id]));
  const all = [...presets, ...saved];
  const activeIsSaved = m.scenario && !m.scenario.id.startsWith("preset-") && saved.some((s) => s.id === m.scenario!.id);
  const activeSaved = activeIsSaved ? saved.find((s) => s.id === m.scenario!.id) : null;
  const activeStale = activeSaved ? JSON.stringify({ p: activeSaved.patch, e: activeSaved.extras }) !== JSON.stringify({ p: current().patch, e: current().extras }) : false;

  return (
    <div className="flex flex-col gap-5">
      <p className="text-[11.5px] text-ink-3">
        Un escenario guarda sólo las entradas distintas del libro v{m.book.meta.version.replace(/^v/, "")} y se aplica sobre él al cargarlo. {dbState === "ready" ? "Los guardados son compartidos por la organización y se actualizan en tiempo real." : dbState === "absent" ? "Los escenarios guardados no están disponibles en esta vista (fuera del visor de claude.ai o edición externa); los presets sí." : "Conectando con la base del artefacto…"}
      </p>

      {m.scenario && (
        <div className="rounded-1 border border-hairline bg-surface-2 px-2.5 py-2 text-[12px]">
          <div className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">Escenario activo</div>
          <div className="font-medium text-ink">{m.scenario.nombre}</div>
          {activeStale && <div className="mt-0.5 text-[11.5px] text-warn-text">▲ entradas modificadas desde la última versión guardada</div>}
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {activeIsSaved && <Button variant="outline" size="xs" onClick={updateActive} disabled={busy || !activeStale}><Save aria-hidden /> actualizar</Button>}
            <Button variant="ghost" size="xs" onClick={m.reset}>volver al libro</Button>
          </div>
        </div>
      )}

      <section className="flex flex-col gap-2">
        <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] text-ink-3">Presets del libro (memo de 03_Tramites)</h3>
        <ul className="flex flex-col gap-1.5">
          {presets.map((p) => <Row key={p.id} s={p} active={m.scenario?.id === p.id} selected={selected.includes(p.id)} onLoad={() => m.loadScenario(p)} onSelect={() => toggleSelect(p.id)} />)}
        </ul>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] text-ink-3">Guardados{dbState === "ready" ? ` (${saved.length})` : ""}</h3>
        {dbState === "ready" && saved.length === 0 && <p className="text-[12px] text-ink-3">Aún no hay escenarios guardados.</p>}
        {dbState === "absent" && <p className="text-[12px] text-ink-3">—</p>}
        <ul className="flex flex-col gap-1.5">
          {saved.map((s) => (
            <Row
              key={s.id}
              s={s}
              active={m.scenario?.id === s.id}
              selected={selected.includes(s.id)}
              onLoad={() => m.loadScenario(s)}
              onSelect={() => toggleSelect(s.id)}
              onDelete={confirmDelete === s.id ? () => remove(s.id) : () => setConfirmDelete(s.id)}
              confirming={confirmDelete === s.id}
              onCancelDelete={() => setConfirmDelete(null)}
            />
          ))}
        </ul>
      </section>

      {dbState === "ready" && (
        <section className="flex flex-col gap-2 border-t border-hairline pt-3">
          <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] text-ink-3">Guardar las entradas actuales como…</h3>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Nombre del escenario"
            className="h-8 rounded-1 border border-hairline bg-surface px-2 text-[12.5px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
            maxLength={80}
          />
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Nota (opcional): qué prueba este escenario"
            className="h-8 rounded-1 border border-hairline bg-surface px-2 text-[12px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
            maxLength={240}
          />
          <div className="flex items-center justify-between gap-2">
            <span className="text-[11px] text-ink-3">{m.dirty === 0 ? "sin cambios frente al libro (se guardaría el libro tal cual)" : `${m.dirty} entrada${m.dirty > 1 ? "s" : ""} distinta${m.dirty > 1 ? "s" : ""} del libro`}</span>
            <Button variant="outline" size="xs" onClick={saveAs} disabled={busy || !name.trim()}><Save aria-hidden /> guardar</Button>
          </div>
        </section>
      )}

      <section className="flex items-center justify-between gap-2 border-t border-hairline pt-3">
        <span className="text-[11.5px] text-ink-3">{selected.length === 0 ? "Marque hasta 3 escenarios para compararlos con las entradas actuales." : `${selected.length} seleccionado${selected.length > 1 ? "s" : ""}`}</span>
        <Button variant="outline" size="xs" onClick={() => onCompare(all.filter((x) => selected.includes(x.id)))} disabled={selected.length === 0}><GitCompareArrows aria-hidden /> comparar</Button>
      </section>

      <section className="flex items-center justify-between gap-2 border-t border-hairline pt-3">
        <span className="text-[11.5px] text-ink-3">{exportMsg ?? "Las 88 entradas + extras actuales, con nombres Excel, para archivar o reimportar."}</span>
        <Button variant="outline" size="xs" onClick={exportJson}><Download aria-hidden /> entradas .json</Button>
      </section>

      {error && <p className="text-[12px] text-risk">{error}</p>}
    </div>
  );
}

function Row({ s, active, selected, onLoad, onSelect, onDelete, confirming, onCancelDelete }: { s: Scenario; active: boolean; selected: boolean; onLoad: () => void; onSelect: () => void; onDelete?: () => void; confirming?: boolean; onCancelDelete?: () => void }) {
  const kpi = useMemo(() => (s.preset ? kpiOf(computeAll({ ...BASELINE_INPUTS, ...s.patch }).cases) : s.kpi), [s]);
  const diffs = describePatch(s.patch ?? {}, s.extras ?? {});
  return (
    <li className={cn("rounded-1 border border-hairline px-2.5 py-2 text-[12px]", active && "border-accent bg-accent-soft/40")}>
      <div className="flex items-start gap-2">
        <button
          type="button"
          role="checkbox"
          aria-checked={selected}
          onClick={onSelect}
          title="Seleccionar para comparar"
          className={cn("mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-[3px] border border-hairline", selected && "border-accent bg-accent text-on-accent")}
        >
          {selected && <Check className="size-3" aria-hidden />}
        </button>
        <div className="min-w-0 flex-1">
          <div className="font-medium leading-snug text-ink">{s.nombre}</div>
          {s.nota && <div className="mt-0.5 text-[11.5px] leading-snug text-ink-2">{s.nota}</div>}
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-ink-2" style={{ fontVariantNumeric: "tabular-nums" }}>
            <span title="TIR del proyecto (Custom)">TIR {fmtPct(kpi.TIR, 2)}</span>
            <span title="VAN @ tasa exigida (Custom)">VAN {fmtUSDCompact(kpi.VAN, 1)}</span>
            <span title="TIR del accionista (Custom)">accionista {fmtPct(kpi.TIR_eq, 1)}</span>
            <span title="DSCR mínimo (Custom)">DSCR {fmtX(kpi.DSCR_min, 2)}</span>
          </div>
          <div className="mt-1 text-[10.5px] text-ink-3" title={diffs.join("\n")}>
            {diffs.length} entrada{diffs.length !== 1 ? "s" : ""} distinta{diffs.length !== 1 ? "s" : ""} del libro{s.actualizado ? ` · ${fmtDate(s.actualizado)}` : ""}{s.base && s.base !== "v3.1" ? ` · definido sobre ${s.base}` : ""}
          </div>
        </div>
      </div>
      <div className="mt-1.5 flex flex-wrap items-center gap-1">
        <Button variant="outline" size="xs" onClick={onLoad} disabled={active}><Upload aria-hidden /> {active ? "cargado" : "cargar"}</Button>
        {onDelete && !confirming && <Button variant="ghost" size="xs" onClick={onDelete} className="text-ink-3"><Trash2 aria-hidden /> eliminar</Button>}
        {onDelete && confirming && (
          <>
            <span className="text-[11px] text-risk">¿Eliminar para toda la organización?</span>
            <Button variant="ghost" size="xs" onClick={onDelete} className="text-risk">sí, eliminar</Button>
            <Button variant="ghost" size="xs" onClick={onCancelDelete}>no</Button>
          </>
        )}
      </div>
    </li>
  );
}
