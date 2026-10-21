import React, { useEffect, useId, useRef, useState } from "react";
import { useServerOptions, type ServerSelectSource } from "./useServerOptions";
import { AnchoredListbox } from "./AnchoredListbox";
import { Check, ChevronDown } from "lucide-react";

export function CustomSelect({ children, className = "", id, onChange, searchable, remote, value, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { searchable?: boolean; remote?: ServerSelectSource }) {
  const sanitizedValue = value === null ? "" : value;
  const generatedId = useId();
  const controlId = id || `choice-${generatedId}`;
  const nativeRef = useRef<HTMLSelectElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const rootRef = useRef<HTMLSpanElement>(null);
  const searchRef = useRef({ text: "", time: 0 });
  const [inferredLabel, setInferredLabel] = useState("");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [invalid, setInvalid] = useState(false);
  const [active, setActive] = useState(-1);
  const [selected, setSelected] = useState(() => String(props.defaultValue || ""));
  const [options, setOptions] = useState<{ value: string; label: string; disabled: boolean }[]>([]);

  const remoteValue = String(sanitizedValue ?? selected);
  const remoteValues = props.multiple ? remoteValue.split(",").filter(Boolean) : remoteValue ? [remoteValue] : [];
  const server = useServerOptions(remote, open, query, remoteValue);
  const original = React.Children.toArray(children) as React.ReactElement<{ value?: string; children?: React.ReactNode }>[];
  const staticChildren = (Array.isArray(children) ? children : [children]).filter(child => React.isValidElement(child) && child.type === "option") as React.ReactElement<{ value?: string; children?: React.ReactNode }>[];
  const fixed = staticChildren.filter(child => ["", "all", "unassigned", "none"].includes(String(child.props.value ?? "")) && (!remoteValue || String(child.props.value ?? "") !== remoteValue) && !server.rows.some(row => row.value === String(child.props.value)));
  const remoteChildren = remote ? <>{fixed}{server.rows.map(row => <option key={row.value} value={row.value}>{row.label}</option>)}{remoteValues.filter(id => !server.rows.some(row => row.value === id)).map(id => <option key={id} value={id}>{server.selections.find(row => row.value === id)?.label || original.find(child => React.isValidElement(child) && String(child.props.value) === id)?.props.children || id}</option>)}</> : children;

  useEffect(() => {
    const select = nativeRef.current;
    if (!select) return;
    const next = Array.from(select.options, option => ({ value: option.value, label: option.label, disabled: option.disabled || (option.parentElement instanceof HTMLOptGroupElement && option.parentElement.disabled) }));
    setOptions(previous => JSON.stringify(previous) === JSON.stringify(next) ? previous : next);
    setSelected(select.multiple ? Array.from(select.selectedOptions, option => option.value).join(",") : select.value);
    const label = select.labels?.[0];
    if (label) {
      const copy = label.cloneNode(true) as HTMLElement;
      copy.querySelectorAll(".custom-select-root, select, button, input, textarea, svg").forEach(element => element.remove());
      setInferredLabel(copy.textContent?.replace(/\s+/g, " ").trim() || "");
    }
  });

  useEffect(() => {
    const form = nativeRef.current?.form;
    const reset = () => { setOpen(false); setInvalid(false); requestAnimationFrame(() => setSelected(nativeRef.current?.value || "")); };
    form?.addEventListener("reset", reset);
    return () => form?.removeEventListener("reset", reset);
  }, []);

  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node) && !menuRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);

  const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
  const visibleOptions = options.map((option, index) => ({ ...option, index })).filter(option => remote ? (!query || server.rows.some(row => row.value === option.value)) : normalize(option.label).includes(normalize(query)));
  const canSearch = Boolean(remote) || (searchable ?? options.length > 5);
  useEffect(() => {
    if (remote && open && active < 0) setActive(visibleOptions.find(option => !option.disabled)?.index ?? -1);
  }, [remote, open, options, query, active]);
  const choose = (index: number) => {
    const option = options[index];
    const select = nativeRef.current;
    if (!select || !option || option.disabled) return;
    const previousValue = select.value;
    const nativeSelectValueSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value")?.set;
    if (remote && props.multiple) {
      const values = remoteValues.includes(option.value) ? remoteValues.filter(id => id !== option.value) : [...remoteValues, option.value];
      for (const item of Array.from(select.options)) item.selected = values.includes(item.value);
    } else if (nativeSelectValueSetter) {
      nativeSelectValueSetter.call(select, option.value);
    } else {
      select.value = option.value;
    }
    if (props.multiple || previousValue !== option.value) select.dispatchEvent(new Event("change", { bubbles: true }));
    setSelected(select.multiple ? Array.from(select.selectedOptions, option => option.value).join(",") : select.value);
    setInvalid(!select.validity.valid);
    if (!props.multiple) setOpen(false);
    buttonRef.current?.focus();
  };

  const show = () => {
    setQuery("");
    setActive(options.findIndex(option => option.value === selected && !option.disabled));
    setOpen(true);
  };

  const keyDown = (event: React.KeyboardEvent<HTMLElement>) => {
    if (event.key === "Escape") {
      if (open) { event.preventDefault(); event.stopPropagation(); setOpen(false); buttonRef.current?.focus(); }
      return;
    }
    if (event.key === "Tab") { setOpen(false); return; }
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      setOpen(true);
      const enabled = visibleOptions.filter(option => !option.disabled).map(option => option.index);
      const current = enabled.indexOf(open ? active : options.findIndex(option => option.value === selected));
      const next = event.key === "Home" ? 0 : event.key === "End" ? enabled.length - 1 : event.key === "ArrowDown" ? (current + 1) % enabled.length : (current - 1 + enabled.length) % enabled.length;
      setActive(enabled[next] ?? -1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (open) choose(active); else show();
    } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      const now = Date.now();
      searchRef.current = { text: (now - searchRef.current.time < 700 ? searchRef.current.text : "") + event.key.toLocaleLowerCase(), time: now };
      const match = options.findIndex(option => !option.disabled && option.label.toLocaleLowerCase().startsWith(searchRef.current.text));
      if (match >= 0) { setOpen(true); setActive(match); }
    }
  };

  return (
    <span ref={rootRef} className="custom-select-root">
      <select {...props} defaultValue={remote ? undefined : props.defaultValue} value={remote ? props.multiple ? remoteValues : remoteValue : sanitizedValue} ref={nativeRef} id={`${controlId}-native`} className="custom-select-native" tabIndex={-1} aria-hidden="true" onChange={onChange || (() => {})} onInvalid={event => { event.preventDefault(); buttonRef.current?.focus(); setInvalid(true); }} onFocus={() => buttonRef.current?.focus()}>{remoteChildren}</select>
      <button ref={buttonRef} type="button" id={controlId} value={selected} role="combobox" disabled={props.disabled} autoFocus={props.autoFocus} className={`custom-select-trigger ${className}`} style={props.style} aria-label={props["aria-label"] || inferredLabel || undefined} aria-labelledby={props["aria-labelledby"]} aria-describedby={props["aria-describedby"]} aria-invalid={props["aria-invalid"] || invalid} aria-required={props.required} aria-expanded={open} aria-haspopup="listbox" aria-controls={`${controlId}-listbox`} aria-activedescendant={open && active >= 0 ? `${controlId}-option-${active}` : undefined} onClick={() => open ? setOpen(false) : show()} onKeyDown={keyDown} onBlur={event => { if (!menuRef.current?.contains(event.relatedTarget as Node)) setOpen(false); }}>
        <span className="custom-select-value">{remote && props.multiple ? remoteValues.length ? `${remoteValues.length} seleccionados` : "Seleccionar opciones…" : options.find(option => option.value === selected)?.label || "Seleccionar opción…"}</span>
        <ChevronDown className="custom-select-chevron" size={16} aria-hidden="true" />
      </button>
      {open && !props.disabled && <AnchoredListbox anchorRef={buttonRef} menuRef={menuRef} activeIndex={visibleOptions.findIndex(option => option.index === active)} id={`${controlId}-listbox`} aria-label={props["aria-label"] || "Opciones"}>
        {canSearch && <li role="presentation" className="custom-select-search"><input aria-label="Buscar opciones" placeholder="Buscar…" value={query} onChange={event => { setQuery(event.target.value.slice(0, 128)); const match = options.findIndex(option => !option.disabled && normalize(option.label).includes(normalize(event.target.value))); setActive(match); }} onKeyDown={event => { if (["ArrowDown", "ArrowUp", "Enter", "Escape", "Tab"].includes(event.key)) keyDown(event); }} onBlur={event => { if (!menuRef.current?.contains(event.relatedTarget as Node) && event.relatedTarget !== buttonRef.current) setOpen(false); }} /></li>}
        {remote && server.loading && <li role="presentation" className="custom-select-empty">Buscando…</li>}{remote && server.error && <li role="presentation" className="custom-select-empty">{server.error}</li>}{visibleOptions.length === 0 && !server.loading && !server.error && <li className="custom-select-empty">No hay opciones coincidentes</li>}
        {visibleOptions.map(({ index, ...option }) => <li key={`${option.value}-${index}`} id={`${controlId}-option-${index}`} role="option" aria-selected={props.multiple ? remoteValues.includes(option.value) : option.value === selected} aria-disabled={option.disabled} data-active={active === index} className="custom-select-option" onPointerMove={() => !option.disabled && setActive(index)} onClick={event => { event.preventDefault(); choose(index); }}><span>{option.label}</span>{option.value === selected && <Check size={16} aria-hidden="true" />}</li>)}
        {remote && server.hasMore && <li role="presentation"><button type="button" disabled={server.loading} className="w-full p-3 text-sm font-semibold text-teal-600" onClick={server.loadMore}>Cargar más</button></li>}
      </AnchoredListbox>}
    </span>
  );
}