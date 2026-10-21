import { ChevronDown, LoaderCircle, Plus, Search, X } from "lucide-react";
import { useEffect, useId, useRef, useState, KeyboardEvent } from "react";
import { apiClient } from "../../api/client";
import { ENTITY_CHANGED_EVENT, EntityChangedDetail, EntityType } from "../entityEvents";

export interface RemoteEntityOption<T = Record<string, unknown>> {
  value: string;
  label: string;
  description?: string;
  data: T;
}

interface RemoteEntitySelectProps<T> {
  value: string;
  onChange: (value: string, option?: RemoteEntityOption<T>) => void;
  endpoint: string;
  mapOption: (item: T) => RemoteEntityOption<T>;
  entityType: EntityType;
  label?: string;
  placeholder?: string;
  emptyText?: string;
  initialOption?: RemoteEntityOption<T>;
  onCreate?: () => void;
  createLabel?: string;
  disabled?: boolean;
  required?: boolean;
  name?: string;
  queryParams?: Record<string, string | undefined>;
  pageSize?: number;
  className?: string;
}

function unpackItems<T>(result: T[] | { items?: T[]; total_count?: number; count?: number }) {
  if (Array.isArray(result)) return { items: result, total: result.length };
  const items = result.items || [];
  return { items, total: result.total_count ?? result.count ?? items.length };
}

export function RemoteEntitySelect<T extends Record<string, unknown>>({
  value,
  onChange,
  endpoint,
  mapOption,
  entityType,
  label,
  placeholder = "Buscar…",
  emptyText = "No se encontraron resultados",
  initialOption,
  onCreate,
  createLabel = "Crear nuevo",
  disabled,
  required,
  name,
  queryParams = {},
  pageSize = 20,
  className = ""
}: RemoteEntitySelectProps<T>) {
  const boundedPageSize = Math.max(1, Math.min(50, pageSize));
  const id = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const creatingRef = useRef(false);
  const [active, setActive] = useState(-1);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [options, setOptions] = useState<RemoteEntityOption<T>[]>(initialOption ? [initialOption] : []);
  const [selected, setSelected] = useState<RemoteEntityOption<T> | undefined>(initialOption?.value === value ? initialOption : undefined);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!value) setSelected(undefined);
    else if (initialOption?.value === value) setSelected(initialOption);
    else setSelected(previous => previous?.value === value ? previous : undefined);
  }, [initialOption, value]);

  useEffect(() => {
    const outside = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, []);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<EntityChangedDetail<T>>).detail;
      if (detail?.type !== entityType) return;
      const option = mapOption(detail.entity);
      setOptions(previous => [option, ...previous.filter(item => item.value !== option.value)]);
      if (creatingRef.current || option.value === value) {
        creatingRef.current = false;
        setSelected(option);
        onChange(option.value, option);
      }
    };
    window.addEventListener(ENTITY_CHANGED_EVENT, handler);
    return () => window.removeEventListener(ENTITY_CHANGED_EVENT, handler);
  }, [entityType, mapOption, onChange, value]);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true);
    if (offset === 0) setOptions([]);
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const url = new URL(endpoint, window.location.origin);
        if (query.trim()) url.searchParams.set("search", query.trim());
        url.searchParams.set("limit", String(boundedPageSize));
        url.searchParams.set("offset", String(offset));
        Object.entries(queryParams).forEach(([key, item]) => { if (item) url.searchParams.set(key, item); });
        const result = await apiClient.request<T[] | { items?: T[]; total_count?: number; count?: number }>(`${url.pathname}${url.search}`, { signal: controller.signal });
        if (controller.signal.aborted) return;
        const unpacked = unpackItems(result);
        const mapped = unpacked.items.map(mapOption);
        setOptions(previous => {
          const base = offset === 0 ? [] : previous;
          const next = [...base];
          mapped.forEach(item => { if (!next.some(existing => existing.value === item.value)) next.push(item); });
          if (!query.trim() && selected && !next.some(item => item.value === selected.value)) next.unshift(selected);
          return next;
        });
        setTotal(unpacked.total);
      } catch (requestError: unknown) {
        if (!controller.signal.aborted && (requestError as { name?: string })?.name !== "AbortError") setError("No se pudieron cargar las opciones.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [open, query, offset, endpoint, boundedPageSize, JSON.stringify(queryParams)]);

  useEffect(() => {
    if (open && active >= 0) rootRef.current?.querySelector<HTMLElement>(`[data-option-index="${active}"]`)?.scrollIntoView?.({ block: "nearest" });
  }, [active, open]);

  function keyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === "Escape" && open) {
      event.preventDefault();
      event.stopPropagation();
      setOpen(false);
      triggerRef.current?.focus();
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      setActive(previous => options.length ? (previous + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length : -1);
    } else if (event.key === "Enter" && open && options[active]) {
      event.preventDefault();
      choose(options[active]);
    }
  }

  function choose(option: RemoteEntityOption<T>) {
    setSelected(option);
    onChange(option.value, option);
    setOpen(false);
    triggerRef.current?.focus();
  }

  function clear() {
    setSelected(undefined);
    onChange("");
    setQuery("");
  }

  return (
    <div ref={rootRef} className={`remote-entity-select relative ${className}`} onKeyDown={keyDown} onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setOpen(false); }}>
      {label && <label htmlFor={`${id}-trigger`} className="mb-1 block text-[11px] font-semibold text-slate-600">{label}</label>}
      {name && <input type="hidden" name={name} value={value} required={required} />}
      <button
        ref={triggerRef}
        id={`${id}-trigger`}
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-required={required}
        aria-label={label || placeholder}
        aria-controls={`${id}-options`}
        disabled={disabled}
        onClick={() => { setOpen(previous => !previous); setOffset(0); setActive(-1); creatingRef.current = false; }}
        className="custom-select-trigger flex min-h-10 w-full items-center justify-between gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-left text-xs text-slate-900 outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100 disabled:opacity-50"
      >
        <span className={selected ? "min-w-0 truncate" : "min-w-0 truncate text-slate-400"}>{selected?.label || placeholder}</span>
        <span className={`flex shrink-0 items-center gap-1 ${selected ? "ml-5" : ""}`}>
          <ChevronDown className="h-4 w-4" />
        </span>
      </button>
      {selected && <button type="button" disabled={disabled} aria-label={`Limpiar ${label || "selección"}`} onClick={clear} className="remote-entity-clear absolute right-9 bottom-2.5 rounded p-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-600"><X className="h-3.5 w-3.5" /></button>}
      {open && (
        <div className="remote-entity-panel absolute z-[80] mt-2 w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
          <div className="border-b border-slate-100 p-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input autoFocus role="combobox" aria-label={`Buscar ${label || "opciones"}`} aria-expanded={open} aria-controls={`${id}-options`} aria-autocomplete="list" aria-activedescendant={active >= 0 ? `${id}-option-${active}` : undefined} value={query} onChange={event => { setQuery(event.target.value.slice(0, 128)); setOffset(0); setActive(-1); }} placeholder={placeholder} className="w-full rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-xs outline-none focus:border-teal-600" />
            </div>
          </div>
          <div id={`${id}-options`} role="listbox" aria-label={label || "Opciones disponibles"} aria-busy={loading} className="max-h-64 overflow-y-auto p-1">
            {loading && offset === 0 && <div className="flex items-center justify-center gap-2 p-6 text-xs text-slate-500"><LoaderCircle className="h-4 w-4 animate-spin" />Buscando…</div>}
            {!loading && !error && options.length === 0 && <div className="p-6 text-center text-xs text-slate-500">{emptyText}</div>}
            {error && <div role="alert" className="p-4 text-xs text-rose-700">{error}</div>}
            {options.map((option, index) => (
              <button id={`${id}-option-${index}`} key={option.value} role="option" aria-selected={option.value === value} data-option-index={index} data-active={index === active} type="button" onClick={() => choose(option)} className="remote-entity-option w-full rounded-xl px-3 py-2 text-left transition">
                <span className="block text-xs font-semibold text-slate-900">{option.label}</span>
                {option.description && <span className="mt-0.5 block text-[10px] text-slate-500">{option.description}</span>}
              </button>
            ))}
            {options.length < total && <button type="button" disabled={loading} onClick={() => setOffset(previous => previous + boundedPageSize)} className="flex w-full items-center justify-center gap-2 rounded-xl p-2 text-xs font-semibold text-teal-700 hover:bg-teal-50 disabled:opacity-50">{loading && <LoaderCircle className="h-3.5 w-3.5 animate-spin" />}Cargar más</button>}
          </div>
          {onCreate && <div className="border-t border-slate-100 p-2"><button type="button" onClick={() => { triggerRef.current?.focus(); setOpen(false); creatingRef.current = true; onCreate(); }} className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-700 px-3 py-2 text-xs font-semibold text-white hover:bg-teal-800"><Plus className="h-4 w-4" />{createLabel}</button></div>}
        </div>
      )}
    </div>
  );
}
