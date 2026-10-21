import React, { useState, useEffect } from "react";

export interface SwitchProps {
  checked: boolean;
  onChange?: (checked: boolean) => void;
  onAsyncChange?: (checked: boolean) => Promise<void>;
  label?: string;
  disabled?: boolean;
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onChange,
  onAsyncChange,
  label,
  disabled = false
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
    <label className="flex items-center gap-3 cursor-pointer select-none">
      <div
        role="switch"
        tabIndex={disabled || isPending ? -1 : 0}
        aria-checked={localChecked}
        aria-busy={isPending}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={`w-11 h-6 rounded-full transition-colors relative focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${localChecked ? "bg-blue-600" : "bg-slate-700"
          } ${disabled || isPending ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <div
          className={`w-4 h-4 rounded-full bg-white transition-transform absolute top-1 ${localChecked ? "left-6" : "left-1"
            } ${isPending ? "animate-pulse" : ""}`}
        />
      </div>
      {label && <span className="text-sm font-medium text-slate-200">{label}</span>}
      {isPending && <span className="text-xs text-amber-400">Guardando...</span>}
    </label>
  );
};
