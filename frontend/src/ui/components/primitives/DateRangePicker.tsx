import React, { useState, useId } from "react";
import { Button } from "./Button";

export interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onChange: (start: string, end: string) => void;
  label?: string;
  error?: string;
  minDate?: string;
  maxDate?: string;
  timezone?: string;
  id?: string;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  startDate,
  endDate,
  onChange,
  label,
  error,
  minDate,
  maxDate,
  timezone = "America/Lima (UTC-5)",
  id
}) => {
  const generatedId = useId();
  const rangeId = id || `daterange-${generatedId.replace(/:/g, "")}`;
  const [rangeError, setRangeError] = useState<string | null>(null);

  const handleStartChange = (val: string) => {
    setRangeError(null);
    if (endDate && val > endDate) {
      setRangeError("La fecha de inicio no puede ser posterior a la de fin");
    }
    onChange(val, endDate);
  };

  const handleEndChange = (val: string) => {
    setRangeError(null);
    if (startDate && startDate > val) {
      setRangeError("La fecha de inicio no puede ser posterior a la de fin");
    }
    onChange(startDate, val);
  };

  const setPreset = (preset: "today" | "week" | "month") => {
    const today = new Date().toISOString().split("T")[0];
    if (preset === "today") {
      onChange(today, today);
    } else if (preset === "week") {
      const past = new Date(Date.now() - 6 * 86400000).toISOString().split("T")[0];
      onChange(past, today);
    } else if (preset === "month") {
      const now = new Date();
      const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split("T")[0];
      onChange(firstDay, today);
    }
    setRangeError(null);
  };

  const clearRange = () => {
    onChange("", "");
    setRangeError(null);
  };

  const effectiveError = error || rangeError;

  const inclusiveDays =
    startDate && endDate && startDate <= endDate
      ? Math.round((new Date(endDate).getTime() - new Date(startDate).getTime()) / 86400000) + 1
      : null;

  return (
    <div className="flex flex-col gap-2 w-full text-left">
      {label && <label className="text-xs font-semibold text-slate-300">{label}</label>}
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <Button size="sm" variant="ghost" onClick={() => setPreset("today")}>
          Hoy
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setPreset("week")}>
          7 días
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setPreset("month")}>
          Este mes
        </Button>
        <Button size="sm" variant="ghost" onClick={clearRange}>
          Limpiar
        </Button>
        <span className="text-[11px] text-slate-500 ml-auto">Zona: {timezone}</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div>
          <label htmlFor={`${rangeId}-start`} className="text-[11px] text-slate-400">
            Desde
          </label>
          <input
            id={`${rangeId}-start`}
            type="date"
            value={startDate}
            min={minDate}
            max={maxDate}
            onChange={(e) => handleStartChange(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2 px-3 text-sm text-slate-100"
          />
        </div>
        <div>
          <label htmlFor={`${rangeId}-end`} className="text-[11px] text-slate-400">
            Hasta
          </label>
          <input
            id={`${rangeId}-end`}
            type="date"
            value={endDate}
            min={minDate}
            max={maxDate}
            onChange={(e) => handleEndChange(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2 px-3 text-sm text-slate-100"
          />
        </div>
      </div>
      {inclusiveDays !== null && (
        <span className="text-xs text-blue-400">
          {`Rango inclusivo: ${inclusiveDays} ${inclusiveDays === 1 ? "día" : "días"}`}
        </span>
      )}
      {effectiveError && (
        <span role="alert" className="text-xs text-rose-400 font-medium">
          {effectiveError}
        </span>
      )}
    </div>
  );
};
