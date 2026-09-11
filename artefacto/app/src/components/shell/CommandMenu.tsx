import { useEffect, useMemo, useState } from "react";
import { BookOpen, CornerDownLeft, Info, Printer, RotateCcw, ScrollText, ShieldAlert, SlidersHorizontal, Waypoints } from "lucide-react";
import { AboutPanel } from "@/components/shell/AboutPanel";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from "@/components/ui/command";
import { navigateWithFocus } from "@/lib/hash";
import { NAV_GROUPS, VIEWS, type ViewId } from "@/lib/views";
import { useModel } from "@/model/store";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavigate: (view: ViewId) => void;
}

const has = (id: ViewId) => VIEWS.some((v) => v.id === id);

/**
 * Paleta ⌘K: ir a una vista; buscar una entrada de 01_Supuestos por nombre Excel o etiqueta (abre Supuestos y resalta la
 * fila); término del glosario (Guía); norma (Legal, por tema); trámite (RC-xx); riesgo; control (A1…); acciones (imprimir,
 * volver al libro). Todo lo que se busca son textos del libro; nada se inventa aquí.
 */
export function CommandMenu({ open, onOpenChange, onNavigate }: Props) {
  const m = useModel();
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onOpenChange]);

  const go = (view: ViewId, focus?: string) => {
    if (focus) navigateWithFocus(view, focus);
    onNavigate(view);
    onOpenChange(false);
  };

  const inputs = useMemo(() => m.book.inputs.rows.filter((r) => r.name && r.label).map((r) => ({ name: r.name as string, label: r.label as string, calc: !!r.calc })), [m.book]);
  const escenarios = useMemo(() => m.book.inputs.escenarios.map((e) => ({ name: e.name, label: e.label })), [m.book]);
  const glosario = useMemo(() => m.book.guia.grupos.flatMap((g) => g.items.map((it) => ({ term: it.term, grupo: g.title }))), [m.book]);
  const normas = useMemo(() => m.book.legal.rows.map((r, k) => ({ k, tema: m.live(r.tema), norma: m.live(r.norma) })), [m.book, m]);
  const tramites = useMemo(() => m.book.tramites.rows.map((t) => ({ id: t.id, tramite: m.live(t.tramite) })), [m.book, m]);
  const riesgos = useMemo(() => m.book.riesgos.rows.map((r, k) => ({ id: String(k + 1), categoria: m.live(r.categoria), riesgo: m.live(r.riesgo) })), [m.book, m]);
  const controles = useMemo(() => m.book.controles.rows.map((c) => ({ id: c.id, desc: c.desc })), [m.book]);
  const [aboutOpen, setAboutOpen] = useState(false);   // A1 (F-A1-03): «Acerca de» accesible también cuando el chip está oculto (< md)

  return (
    <>
    <AboutPanel open={aboutOpen} onOpenChange={setAboutOpen} />
    <CommandDialog open={open} onOpenChange={onOpenChange} title="Buscar en el modelo">
      <CommandInput placeholder="Vista, entrada de 01 (nombre Excel o etiqueta), término, norma, trámite, riesgo, control…" />
      <CommandList className="max-h-[60vh]">
        <CommandEmpty>Sin resultados.</CommandEmpty>
        {NAV_GROUPS.map((group) => (
          <CommandGroup key={group.id} heading={group.label}>
            {group.views.map((v) => (
              <CommandItem key={v.id} value={`vista ${group.label} ${v.label}`} onSelect={() => go(v.id)}>
                <span>{v.label}</span>
                <CommandShortcut className="inline-flex items-center gap-1 font-mono text-[11px]">
                  #v={v.id}
                  <CornerDownLeft className="size-3" aria-hidden />
                </CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
        ))}
        <CommandGroup heading="Acciones">
          <CommandItem value="accion imprimir vista" onSelect={() => { onOpenChange(false); window.setTimeout(() => window.print(), 150); }}>
            <Printer className="size-3.5 text-ink-3" aria-hidden /> <span>Imprimir la vista actual</span>
          </CommandItem>
          <CommandItem value="accion acerca de esta version libro sha edicion" onSelect={() => { onOpenChange(false); window.setTimeout(() => setAboutOpen(true), 120); }}>
            <Info className="size-3.5 text-ink-3" aria-hidden /> <span>Acerca de esta versión (libro, SHA, edición, convención)</span>
          </CommandItem>
          <CommandItem value="accion volver al libro restaurar entradas" onSelect={() => { m.reset(); onOpenChange(false); }} disabled={m.dirty === 0}>
            <RotateCcw className="size-3.5 text-ink-3" aria-hidden /> <span>Volver al libro (restaurar las entradas v{m.book.meta.version.replace(/^v/, "")})</span>
          </CommandItem>
        </CommandGroup>
        {has("supuestos") && (
          <CommandGroup heading="Entradas de 01_Supuestos">
            {inputs.map((r) => (
              <CommandItem key={r.name} value={`entrada ${r.name} ${r.label}`} onSelect={() => go("supuestos", `id:sup-${r.name}`)}>
                <SlidersHorizontal className="size-3.5 text-ink-3" aria-hidden />
                <span className="truncate">{r.label}</span>
                <CommandShortcut className="font-mono text-[11px]">{r.name}{r.calc ? " · calc" : ""}</CommandShortcut>
              </CommandItem>
            ))}
            {escenarios.map((e) => (
              <CommandItem key={e.name} value={`entrada bloque B ${e.name} ${e.label}`} onSelect={() => go("supuestos", `row:${e.name}`)}>
                <SlidersHorizontal className="size-3.5 text-ink-3" aria-hidden />
                <span className="truncate">{e.label}</span>
                <CommandShortcut className="font-mono text-[11px]">{e.name} · bloque B</CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {has("guia") && (
          <CommandGroup heading="Glosario (Guía)">
            {glosario.map((t) => (
              <CommandItem key={`${t.grupo}-${t.term}`} value={`glosario ${t.term} ${t.grupo}`} onSelect={() => go("guia", `row:${t.term}`)}>
                <BookOpen className="size-3.5 text-ink-3" aria-hidden />
                <span className="truncate">{t.term}</span>
                <CommandShortcut className="text-[11px]">{t.grupo.split(" · ")[0]}</CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {has("legal") && (
          <CommandGroup heading="Normas (Legal)">
            {normas.map((n) => (
              <CommandItem key={n.k} value={`norma ${n.tema} ${n.norma}`} onSelect={() => go("legal", `row:${n.k}`)}>
                <ScrollText className="size-3.5 text-ink-3" aria-hidden />
                <span className="truncate">{n.tema}</span>
                <CommandShortcut className="max-w-[40%] truncate text-[11px]">{n.norma}</CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {has("tramites") && (
          <CommandGroup heading="Trámites">
            {tramites.map((t) => (
              <CommandItem key={t.id} value={`tramite ${t.id} ${t.tramite}`} onSelect={() => go("tramites", `row:${t.id}`)}>
                <Waypoints className="size-3.5 text-ink-3" aria-hidden />
                <span className="truncate">{t.tramite}</span>
                <CommandShortcut className="font-mono text-[11px]">{t.id}</CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {has("riesgos") && (
          <CommandGroup heading="Riesgos">
            {riesgos.map((r) => (
              <CommandItem key={r.id} value={`riesgo ${r.id} ${r.categoria} ${r.riesgo}`} onSelect={() => go("riesgos", `row:${r.id}`)}>
                <ShieldAlert className="size-3.5 text-ink-3" aria-hidden />
                <span className="truncate">{r.riesgo}</span>
                <CommandShortcut className="text-[11px]">{r.id} · {r.categoria}</CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {has("controles") && (
          <CommandGroup heading="Controles (13)">
            {controles.map((c) => (
              <CommandItem key={c.id} value={`control ${c.id} ${c.desc}`} onSelect={() => go("controles", `row:${c.id}`)}>
                <span className="font-mono text-[11px] text-ink-3">{c.id}</span>
                <span className="truncate">{c.desc}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </CommandDialog>
    </>
  );
}
