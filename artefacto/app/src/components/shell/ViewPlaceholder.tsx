import { groupOf, viewMeta, type ViewId } from "@/lib/views";

interface Props {
  view: ViewId;
}

/** Cabecera + hueco por vista. Las vistas reales sustituirán este componente. */
export function ViewPlaceholder({ view }: Props) {
  const meta = viewMeta(view);
  const group = groupOf(view);
  return (
    <article aria-labelledby={`view-${view}-title`} className="flex flex-col gap-5">
      <header className="flex flex-col gap-1">
        <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-ink-3">{group.label}</p>
        <h1 id={`view-${view}-title`} className="font-serif text-[22px] font-medium leading-tight tracking-[-0.01em] text-ink">
          {meta.label}
        </h1>
      </header>
      <section
        aria-label="Contenido pendiente"
        className="flex min-h-64 items-center rounded-2 border border-dashed border-hairline bg-surface px-6 text-[13px] text-ink-3"
      >
        <p>
          Vista <span className="font-mono text-ink-2">#v={view}</span> · contenido pendiente.
        </p>
      </section>
    </article>
  );
}
