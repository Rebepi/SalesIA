import { AnchoredListbox } from "../AnchoredListbox";
import React, { useState, useRef, useEffect, useId } from "react";
import { CheckCircleIcon, ChevronDownIcon, RefreshSyncIcon } from "../../icons/index";

export interface ComboboxOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface ComboboxProps {
  label?: string;
  options?: ComboboxOption[];
  value: string;
  onChange: (value: string, option?: ComboboxOption) => void;
  onSearch?: (query: string, signal?: AbortSignal) => Promise<ComboboxOption[]>;
  placeholder?: string;
  error?: string;
  id?: string;
  debounceMs?: number;
}

export const Combobox: React.FC<ComboboxProps> = ({
  label,
  options = [],
  value,
  onChange,
  onSearch,
  placeholder = "Buscar o seleccionar...",
  error,
  id,
  debounceMs = 200
}) => {
  const generatedId = useId();
  const comboboxId = id || `combobox-${generatedId.replace(/:/g, "")}`;
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredOptions, setFilteredOptions] = useState<ComboboxOption[]>(options);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const searchSequenceRef = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    if (!onSearch) {
      if (!searchTerm) {
        setFilteredOptions(options);
      } else {
        const lower = searchTerm.toLowerCase();
        setFilteredOptions(options.filter((opt) => opt.label.toLowerCase().includes(lower)));
      }
      return;
    }

    const currentSeq = ++searchSequenceRef.current;
    setIsLoading(true);
    const timer = setTimeout(() => {
      onSearch(searchTerm)
        .then((results) => {
          if (currentSeq === searchSequenceRef.current) {
            setFilteredOptions(results);
            setIsLoading(false);
          }
        })
        .catch(() => {
          if (currentSeq === searchSequenceRef.current) {
            setIsLoading(false);
          }
        });
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [searchTerm, options, onSearch, debounceMs]);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node) && !menuRef.current?.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIsOpen(true);
      setHighlightedIndex((prev) => {
        const next = filteredOptions.findIndex((option, index) => index > prev && !option.disabled);
        return next >= 0 ? next : filteredOptions.findIndex(option => !option.disabled);
      });
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setIsOpen(true);
      setHighlightedIndex((prev) => {
        const enabled = filteredOptions.map((option, index) => option.disabled ? -1 : index).filter(index => index >= 0);
        return [...enabled].reverse().find(index => index < prev) ?? enabled[enabled.length - 1] ?? -1;
      });
    } else if (e.key === "Enter") {
      if (isOpen && highlightedIndex >= 0 && filteredOptions[highlightedIndex] && !filteredOptions[highlightedIndex].disabled) {
        e.preventDefault();
        const selected = filteredOptions[highlightedIndex];
        onChange(selected.value, selected);
        setIsOpen(false);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const selectedOption =
    options.find((opt) => opt.value === value) ||
    filteredOptions.find((opt) => opt.value === value);

  return (
    <div ref={containerRef} className="flex flex-col gap-1 w-full text-left relative">
      {label && (
        <label htmlFor={`${comboboxId}-input`} className="custom-select-label text-xs font-semibold">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          id={`${comboboxId}-input`}
          ref={inputRef}
          role="combobox"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          aria-controls={`${comboboxId}-listbox`}
          aria-activedescendant={isOpen && highlightedIndex >= 0 ? `${comboboxId}-option-${highlightedIndex}` : undefined}
          onBlur={(event) => { if (!containerRef.current?.contains(event.relatedTarget)) setIsOpen(false); }}
          aria-invalid={!!error}
          value={isOpen ? searchTerm : selectedOption ? selectedOption.label : searchTerm}
          placeholder={placeholder}
          onFocus={() => setIsOpen(true)}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setHighlightedIndex(-1);
            setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          className={`w-full bg-slate-900 border rounded-xl py-2 pl-3 pr-10 text-sm text-slate-100 placeholder-slate-500 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 ${error ? "border-rose-500" : "border-slate-700 hover:border-slate-600"
            }`}
        />
        {isLoading ? (
          <span className="absolute right-3 top-2.5 text-teal-400 animate-spin">
            <RefreshSyncIcon size={16} />
          </span>
        ) : (
          <button
            type="button"
            tabIndex={-1}
            onClick={() => setIsOpen(!isOpen)}
            className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200 transition-transform focus:outline-none"
            aria-label="Mostrar opciones"
            onMouseDown={event => event.preventDefault()}
          >
            <ChevronDownIcon size={16} className={`transition-transform duration-200 ${isOpen ? "rotate-180 text-teal-400" : ""}`} />
          </button>
        )}
      </div>
      {isOpen && (
        <AnchoredListbox
          anchorRef={inputRef}
          menuRef={menuRef}
          activeIndex={highlightedIndex}
          id={`${comboboxId}-listbox`}
          aria-label={label || "Opciones"}
        >
          {filteredOptions.length === 0 ? (
            <li className="p-3 text-xs text-slate-500 text-center">
              {isLoading ? "Buscando resultados..." : "No se encontraron coincidencias"}
            </li>
          ) : (
            filteredOptions.map((opt, idx) => {
              const isSelected = opt.value === value;
              const isHighlighted = idx === highlightedIndex;
              return (
                <li
                  key={opt.value}
                  id={`${comboboxId}-option-${idx}`}
                  aria-disabled={opt.disabled}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    if (opt.disabled) return;
                    onChange(opt.value, opt);
                    setIsOpen(false);
                  }}
                  data-active={isHighlighted}
                  className="custom-select-option"
                >
                  <span>{opt.label}</span>
                  {isSelected && <CheckCircleIcon size={14} />}
                </li>
              );
            })
          )}
        </AnchoredListbox>
      )}
      {error && <span role="alert" className="text-xs text-rose-400">{error}</span>}
    </div>
  );
};
