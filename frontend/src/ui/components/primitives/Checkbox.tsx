import React, { useState, useEffect } from "react";
import { CheckCircleIcon } from "../../icons/index";

export interface CheckboxProps {
  checked: boolean;
  onChange?: (checked: boolean) => void;
  onAsyncChange?: (checked: boolean) => Promise<void>;
  label?: string;
  disabled?: boolean;
  isTableRowSelection?: boolean;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  checked,
  onChange,
  onAsyncChange,
  label,
  disabled = false,
  isTableRowSelection = false
}) => {
  const [isPending, setIsPending] = useState(false);
  const [localChecked, setLocalChecked] = useState(checked);

  useEffect(() => {
    setLocalChecked(checked);
  }, [checked]);

  const handleToggle = () => {
    if (disabled || isPending) return;
    const next = !localChecked;
    if (onAsyncChange) {
      setIsPending(true);
      setLocalChecked(next);
      onAsyncChange(next)
        .then(() => setIsPending(false))
        .catch(() => {
          setLocalChecked(!next);
          setIsPending(false);
        });
    } else if (onChange) {
      onChange(next);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled || isPending) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleToggle();
    }
  };

  return (
    <label className="flex items-center gap-2.5 cursor-pointer select-none">
      <div
        role="checkbox"
        tabIndex={disabled || isPending ? -1 : 0}
        aria-checked={localChecked}
        aria-busy={isPending}
        aria-label={isTableRowSelection ? (label || "Seleccionar fila") : undefined}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={`w-5 h-5 rounded-md border flex items-center justify-center transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${localChecked
          ? "bg-blue-600 border-blue-500 text-white"
          : "border-slate-600 bg-slate-900"
          } ${disabled || isPending ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        {localChecked && <CheckCircleIcon size={14} />}
      </div>
      {label && <span className="text-sm text-slate-200">{label}</span>}
      {isPending && <span className="text-xs text-amber-400">Actualizando...</span>}
    </label>
  );
};
