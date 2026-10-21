import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState } from "react";
import { Bookmark, Save, Star } from "lucide-react";
import { apiClient } from "../../../api/client";

type Favorite = { type: string; id: string; title: string };
type Filter = { id: string; name: string; resource_type: string; query: string; field_key: string; field_value: string; is_shared: boolean; can_edit: boolean; version: number };
type Selection = { kind: string; query: string; fieldFilter: string; fieldFilterValue: string };

export function RecordNavigation({ active, selection, onOpen, onFilter, canShare, storageScope }: { active: Favorite | null; selection: Selection; onOpen: (type: string, id: string) => void; onFilter: (value: Selection) => void; canShare: boolean; storageScope: string }) {
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [filters, setFilters] = useState<Filter[]>([]);
  const [name, setName] = useState("");
  const [shared, setShared] = useState(false);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const generation = useRef(0);

  async function load() {
    const requestedGeneration = generation.current;
    const [savedFavorites, savedFilters] = await Promise.all([apiClient.request<Favorite[]>("/api/v1/business/favorites"), apiClient.request<Filter[]>("/api/v1/business/record-views")]);
    if (requestedGeneration !== generation.current) return;
    setFavorites(savedFavorites);
    setFilters(savedFilters);
  }

  useEffect(() => {
    generation.current += 1;
    setFavorites([]);
    setFilters([]);
    setSelected("");
    setName("");
    void load().catch(() => setError("No se pudieron cargar los accesos guardados."));
    return () => { generation.current += 1; };
  }, [storageScope]);

  async function mutate(path: string, method: "PUT" | "DELETE", body?: unknown) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await apiClient.request(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
      await load();
    } catch (cause) {
      const detail = (cause as { detail?: unknown }).detail;
      setError(typeof detail === "string" ? detail : "No se pudo guardar el acceso.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  const isFavorite = Boolean(active && favorites.some(item => item.type === active.type && item.id === active.id));
  const currentFilter = filters.find(item => item.id === selected);
  const input = "records-input";

  return <section className="records-panel records-navigation space-y-4"><div className="flex flex-wrap items-center gap-3"><div className="records-section-title mr-auto"><Bookmark size={18} aria-hidden="true" /><h2>Mis accesos y filtros</h2></div>{active && <button type="button" className="records-button" disabled={busy} onClick={() => void mutate(`/api/v1/business/favorites/${active.type}/${active.id}`, "PUT", { active: !isFavorite })}><Star size={16} aria-hidden="true" fill={isFavorite ? "currentColor" : "none"} />{isFavorite ? "Quitar de favoritos" : "Guardar registro como favorito"}</button>}</div>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}<div className="records-favorites">{favorites.map(item => <button type="button" key={`${item.type}:${item.id}`} className="records-favorite" onClick={() => onOpen(item.type, item.id)}><Star size={14} aria-hidden="true" /><span>{item.title}</span></button>)}{favorites.length === 0 && <p className="records-muted flex items-center gap-2 text-sm"><Star size={16} aria-hidden="true" />Aún no tienes registros favoritos.</p>}</div><div className="records-saved-filters"><label className="records-saved-select text-sm">Búsquedas guardadas<CustomSelect searchable={true} aria-label="Filtro guardado" value={selected} onChange={event => {
    const filter = filters.find(item => item.id === event.target.value);
    setSelected(event.target.value);
    setName(filter?.name || "");
    setShared(filter?.is_shared || false);
    if (filter) onFilter({ kind: filter.resource_type, query: filter.query, fieldFilter: filter.field_key, fieldFilterValue: filter.field_value });
  }} className={input}><option value="">Nuevo filtro</option>{filters.map(filter => <option value={filter.id} key={filter.id}>{filter.name}{filter.is_shared ? " · Compartido" : ""}</option>)}</CustomSelect></label><label className="records-saved-name text-sm">Nombre de la búsqueda<input aria-label="Nombre del filtro" maxLength={128} placeholder="Nombre para esta búsqueda" value={name} onChange={event => setName(event.target.value)} className={input} /></label>{canShare && <label className="records-share flex items-center gap-2 text-sm"><input type="checkbox" checked={shared} onChange={event => setShared(event.target.checked)} />Compartir</label>}<button type="button" disabled={busy || name.trim().length < 2 || !selection.kind} className="records-button records-button-primary" onClick={() => {
    const ownMatch = filters.find(filter => filter.can_edit && filter.name === name.trim());
    void mutate("/api/v1/business/record-views", "PUT", { name: name.trim(), resource_type: selection.kind, query: selection.query, field_key: selection.fieldFilter, field_value: selection.fieldFilterValue, is_shared: shared, version: ownMatch?.version || 0 });
  }}><Save size={16} aria-hidden="true" />Guardar búsqueda</button>{currentFilter?.can_edit && <button type="button" className="records-button" disabled={busy} onClick={() => { void mutate(`/api/v1/business/record-views/${currentFilter.id}`, "DELETE"); setSelected(""); setName(""); }}>Eliminar filtro</button>}</div></section>;
}
