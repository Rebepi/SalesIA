import { apiClient } from "./client";

type Collection = { items: unknown[]; total_count?: number; count?: number; next_cursor?: string | null };

export async function requestAllPages<T>(path: string, mode: "offset" | "page" | "cursor" = "offset", signal?: AbortSignal): Promise<T> {
  const [pathname, query = ""] = path.split("?");
  const params = new URLSearchParams(query);
  const size = 100;
  params.set(mode === "page" ? "page_size" : "limit", String(size));
  const items: unknown[] = [];
  const seen = new Set<string>();
  let first: Collection | unknown[] | undefined;
  let page = 1;
  let cursor: string | null = null;
  while (true) {
    if (signal?.aborted) throw new DOMException("Solicitud cancelada", "AbortError");
    if (mode === "page") params.set("page", String(page));
    if (mode === "offset") params.set("offset", String(items.length));
    if (mode === "cursor") { params.delete("cursor"); if (cursor) params.set("cursor", cursor); }
    const result = await apiClient.request<Collection | unknown[]>(`${pathname}?${params}`, { signal });
    if (!first) first = result;
    const batch = Array.isArray(result) ? result : result.items;
    if (!Array.isArray(batch)) throw new Error("La respuesta no contiene una colección válida.");
    const signature = JSON.stringify(batch);
    if (batch.length && seen.has(signature)) throw new Error("El servidor repitió una página. Actualiza el listado para volver a intentarlo.");
    if (batch.length) seen.add(signature);
    items.push(...batch);
    if (mode === "cursor") {
      const next = Array.isArray(result) ? null : result.next_cursor;
      if (!next) break;
      if (next === cursor) throw new Error("El servidor no avanzó el cursor de la colección.");
      cursor = next;
    } else {
      const total = Array.isArray(result) ? undefined : result.total_count;
      if (!batch.length || batch.length < size || (typeof total === "number" && items.length >= total)) break;
      page += 1;
    }
  }
  return (Array.isArray(first) ? items : { ...first, items, count: items.length, total_count: items.length, next_cursor: null }) as T;
}
