import React, { useState } from "react";
import { CurrencyDollarIcon } from "../../icons/index";
import { Input } from "./Input";

export interface MoneyInputProps {
  label?: string;
  value: string;
  onChange: (normalizedValue: string, displayValue?: string) => void;
  currency?: string;
  error?: string;
  min?: number;
  placeholder?: string;
  id?: string;
  locale?: "es-PE" | "es-ES" | "en-US";
  roundingPolicy?: "half-even" | "floor" | "ceil" | "round";
}

export const MoneyInput: React.FC<MoneyInputProps> = ({
  label,
  value,
  onChange,
  currency = "USD",
  error,
  min = 0,
  placeholder = "0.00",
  id,
  locale = "es-PE",
  roundingPolicy = "half-even"
}) => {
  const [internalError, setInternalError] = useState<string | null>(null);

  const isEsLocale = locale === "es-PE" || locale === "es-ES";

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    setInternalError(null);

    if (raw.trim() === "") {
      onChange("", "");
      return;
    }

    if (isEsLocale) {
      if (/,\d{3}\./.test(raw) || (/^\d+\.\d{2}$/.test(raw) && !raw.includes(","))) {
        setInternalError("Formato no válido para " + locale + ". Use coma para decimales (ej. 1.234,56)");
        return;
      }
      const clean = raw.replace(/[^\d.,]/g, "");
      const withoutThousands = clean.replace(/\./g, "");
      const normalized = withoutThousands.replace(",", ".");
      const parts = normalized.split(".");
      if (parts.length > 2) return;
      if (parts[1] && parts[1].length > 4) return;
      onChange(normalized, raw);
    } else {
      if (/\.\d{3},/.test(raw) || (/^\d+,\d{2}$/.test(raw) && !raw.includes("."))) {
        setInternalError("Formato no válido para " + locale + ". Use punto para decimales (ej. 1,234.56)");
        return;
      }
      const clean = raw.replace(/[^\d.,]/g, "");
      const withoutThousands = clean.replace(/,/g, "");
      const normalized = withoutThousands;
      const parts = normalized.split(".");
      if (parts.length > 2) return;
      if (parts[1] && parts[1].length > 4) return;
      onChange(normalized, raw);
    }
  };

  const displayError = error || internalError || undefined;

  return (
    <div className="w-full">
      <Input
        id={id}
        label={label}
        value={value}
        min={min}
        onChange={handleChange}
        error={displayError}
        placeholder={placeholder}
        className="text-right font-mono"
        leftIcon={<CurrencyDollarIcon size={16} />}
        rightIcon={
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400">
            <span>{currency}</span>
            <span className="text-[10px] text-slate-500">({roundingPolicy})</span>
          </div>
        }
      />
    </div>
  );
};
