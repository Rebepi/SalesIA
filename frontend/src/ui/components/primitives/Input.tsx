import React, { useRef, useId } from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  showCount?: boolean;
  prefixText?: string;
  suffixText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  id,
  className = "",
  required,
  showCount = false,
  prefixText,
  suffixText,
  value,
  maxLength,
  onChange,
  onPaste,
  ...props
}) => {
  const generatedId = useId();
  const inputId = id || `input-${generatedId.replace(/:/g, "")}`;
  const isComposingRef = useRef(false);

  const currentLength = typeof value === "string" ? value.length : 0;

  return (
    <div className="flex flex-col gap-1 w-full text-left">
      <div className="flex items-center justify-between">
        {label && (
          <label htmlFor={inputId} className="text-xs font-semibold text-slate-300">
            {label}
            {required ? (
              <span className="text-rose-400 ml-1" title="Requerido">*</span>
            ) : (
              <span className="text-slate-500 font-normal ml-1">(Opcional)</span>
            )}
          </label>
        )}
        {showCount && maxLength && (
          <span className="text-xs text-slate-400 tabular-nums">
            {`${currentLength} / ${maxLength}`}
          </span>
        )}
      </div>
      <div className="relative flex items-center">
        {leftIcon && (
          <div className="absolute left-3 text-slate-400 pointer-events-none">{leftIcon}</div>
        )}
        {prefixText && (
          <span className="absolute left-3 text-xs font-semibold text-slate-400 pointer-events-none select-none">
            {prefixText}
          </span>
        )}
        <input
          id={inputId}
          required={required}
          value={value}
          maxLength={maxLength}
          aria-invalid={!!error}
          aria-describedby={
            error ? `${inputId}-error` : helperText ? `${inputId}-help` : undefined
          }
          onCompositionStart={() => {
            isComposingRef.current = true;
          }}
          onCompositionEnd={(e) => {
            isComposingRef.current = false;
            if (onChange) {
              onChange(e as unknown as React.ChangeEvent<HTMLInputElement>);
            }
          }}
          onChange={(e) => {
            if (onChange) {
              onChange(e);
            }
          }}
          onPaste={(e) => {
            if (onPaste) {
              onPaste(e);
            }
          }}
          className={`w-full bg-slate-900 border rounded-xl py-2 px-3 text-sm text-slate-100 placeholder-slate-500 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${leftIcon ? "pl-9" : prefixText ? "pl-12" : ""
            } ${rightIcon ? "pr-9" : suffixText ? "pr-12" : ""} ${error
              ? "border-rose-500/80 focus-visible:ring-rose-500"
              : "border-slate-700 hover:border-slate-600"
            } ${className}`}
          {...props}
        />
        {suffixText && (
          <span className="absolute right-3 text-xs font-semibold text-slate-400 pointer-events-none select-none">
            {suffixText}
          </span>
        )}
        {rightIcon && <div className="absolute right-3 text-slate-400">{rightIcon}</div>}
      </div>
      {error && (
        <span id={`${inputId}-error`} role="alert" className="text-xs text-rose-400 font-medium">
          {error}
        </span>
      )}
      {!error && helperText && (
        <span id={`${inputId}-help`} className="text-xs text-slate-400">
          {helperText}
        </span>
      )}
    </div>
  );
};
