import { CustomSelect } from "../CustomSelect";
import React, { useId } from "react";
import type { SelectOption } from "./SelectOption";

export interface SelectProps {
  label?: string;
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  error?: string;
  placeholder?: string;
  className?: string;
  id?: string;
  required?: boolean;
}

export const Select: React.FC<SelectProps> = ({
  label,
  options,
  value,
  onChange,
  error,
  placeholder = "Seleccionar opción...",
  className = "",
  id,
  required
}) => {
  const generatedId = useId();
  const selectId = id || `select-${generatedId.replace(/:/g, "")}`;
  return (
    <div className={`flex flex-col gap-1 w-full text-left ${className}`}>
      {label && (
        <label htmlFor={selectId} className="custom-select-label text-xs font-semibold">
          {label}
        </label>
      )}
      <CustomSelect
        id={selectId}
        value={value}
        required={required}
        aria-invalid={!!error}
        aria-describedby={error ? `${selectId}-error` : undefined}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full bg-slate-900 border rounded-xl py-2 px-3 text-sm text-slate-100 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 border-slate-700 hover:border-slate-600 ${error ? "border-rose-500" : ""
          }`}
      >
        <option value="" disabled className="bg-slate-900 text-slate-500">
          {placeholder}
        </option>
        {options.map((opt) => (
          <option
            key={opt.value}
            value={opt.value}
            disabled={opt.disabled}
            className="bg-slate-900 text-slate-100"
          >
            {opt.label}
          </option>
        ))}
      </CustomSelect>
      {error && (
        <span id={`${selectId}-error`} role="alert" className="text-xs text-rose-400">
          {error}
        </span>
      )}
    </div>
  );
};
