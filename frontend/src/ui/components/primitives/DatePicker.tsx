import React, { useId } from "react";

export interface DatePickerProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  minDate?: string;
  maxDate?: string;
  id?: string;
}

export const DatePicker: React.FC<DatePickerProps> = ({
  label,
  value,
  onChange,
  minDate,
  maxDate,
  id
}) => {
  const generatedId = useId();
  const dateId = id || `date-${generatedId.replace(/:/g, "")}`;
  return (
    <div className="flex flex-col gap-1 w-full text-left">
      {label && (
        <label htmlFor={dateId} className="text-xs font-semibold text-slate-300">
          {label}
        </label>
      )}
      <input
        id={dateId}
        type="date"
        value={value}
        min={minDate}
        max={maxDate}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2 px-3 text-sm text-slate-100 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
      />
    </div>
  );
};
