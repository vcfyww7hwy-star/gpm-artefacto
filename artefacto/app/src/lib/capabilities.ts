/**
 * Acceso a las capacidades del visor de Artifacts (`window.claude.use(name)`), diseñado para la ausencia:
 * fuera del visor (vista previa, archivo local, edición externa sin `db`) todo resuelve `null` y la interfaz oculta
 * o degrada la función. `use()` está memoizado por el propio visor; aquí sólo se añade el tipo y el guardián.
 *
 * Tipos mínimos de los espacios de nombres usados (contrato 0.2.42): db (documentos JSON en tiempo real) y downloads
 * (guardar un archivo generado con confirmación del visor).
 */
export interface DbError { code: string; message: string }
export interface DocSnapshot { id: string; exists: boolean; data(): Record<string, unknown> | undefined; metadata: { fromCache: boolean; hasPendingWrites: boolean } }
export interface QuerySnapshot { docs: DocSnapshot[]; size: number; empty: boolean }
export interface DocRef {
  id: string;
  path: string;
  get(): Promise<DocSnapshot>;
  set(data: Record<string, unknown>): Promise<void>;
  update(data: Record<string, unknown>): Promise<void>;
  delete(): Promise<void>;
  onSnapshot(next: (s: DocSnapshot) => void, error?: (e: DbError) => void): () => void;
}
export interface Query {
  where(field: string, op: string, value: unknown): Query;
  orderBy(field: string, dir?: "asc" | "desc"): Query;
  limit(n: number): Query;
  get(): Promise<QuerySnapshot>;
  onSnapshot(next: (s: QuerySnapshot) => void, error?: (e: DbError) => void): () => void;
}
export interface CollectionRef extends Query { path: string; doc(id?: string): DocRef; add(data: Record<string, unknown>): Promise<DocRef> }
export interface Db { doc(path: string): DocRef; collection(path: string): CollectionRef }

export interface Downloads {
  save(req: { filename: string; data: string | Blob | ArrayBuffer | ArrayBufferView }): Promise<{ status: "saved" | "delivered" }>;
}

interface ClaudeUse {
  use(name: string): Promise<unknown>;
}

function claude(): ClaudeUse | null {
  const w = window as unknown as { claude?: ClaudeUse };
  return w.claude && typeof w.claude.use === "function" ? w.claude : null;
}

/** Espacio de nombres `db` o null (no servido, no concedido o fuera del visor). */
export async function useDb(): Promise<Db | null> {
  const c = claude();
  if (!c) return null;
  try {
    return ((await c.use("db")) as Db | null) ?? null;
  } catch {
    return null;
  }
}

/** Espacio de nombres `downloads` o null. */
export async function useDownloads(): Promise<Downloads | null> {
  const c = claude();
  if (!c) return null;
  try {
    return ((await c.use("downloads")) as Downloads | null) ?? null;
  } catch {
    return null;
  }
}

/** Código de error estable de una promesa rechazada por una capacidad («declined», «unavailable», …). */
export function errorCode(e: unknown): string {
  if (e && typeof e === "object" && "code" in e && typeof (e as { code: unknown }).code === "string") return (e as { code: string }).code;
  return "unavailable";
}
