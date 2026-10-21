import React, { useState, useRef } from "react";
import { RefreshSyncIcon } from "../../icons/index";
import { IconStateContext, IconInteractionState, useMotion } from "../../motion";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "destructive" | "icon";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  debounceMs?: number;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  leftIcon,
  rightIcon,
  className = "",
  disabled,
  onClick,
  debounceMs = 350,
  ...props
}) => {
  const lastClickTimeRef = useRef<number>(0);

  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed select-none min-w-[36px]";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs gap-1.5 min-h-[32px]",
    md: "px-4 py-2 text-sm gap-2 min-h-[40px]",
    lg: "px-5 py-2.5 text-base gap-2.5 min-h-[48px]"
  };

  const effectiveVariant = variant === "destructive" ? "danger" : variant;

  const variantStyles = {
    primary:
      "bg-blue-600 text-white hover:bg-blue-500 active:bg-blue-700 shadow-md shadow-blue-900/20",
    secondary:
      "bg-slate-800 text-slate-100 hover:bg-slate-700 active:bg-slate-900 border border-slate-700/60",
    outline:
      "border border-slate-600/80 text-slate-200 hover:bg-slate-800/60 active:bg-slate-800",
    ghost:
      "text-slate-300 hover:bg-slate-800/60 hover:text-white active:bg-slate-800",
    danger:
      "bg-rose-600 text-white hover:bg-rose-500 active:bg-rose-700 shadow-md shadow-rose-900/20",
    icon:
      "p-2 text-slate-300 hover:text-white hover:bg-slate-800/60"
  };

  const motionCtx = useMotion();
  const [btnState, setBtnState] = useState<IconInteractionState>("rest");

  const effectiveState: IconInteractionState = disabled
    ? "disabled"
    : isLoading
      ? "loading"
      : btnState;

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || isLoading) {
      e.preventDefault();
      return;
    }
    const now = Date.now();
    if (now - lastClickTimeRef.current < debounceMs) {
      e.preventDefault();
      return;
    }
    lastClickTimeRef.current = now;
    if (onClick) {
      onClick(e);
    }
  };

  return (
    <button
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      onClick={handleClick}
      onPointerEnter={() => { if (!disabled && !isLoading) setBtnState("hover"); }}
      onPointerLeave={() => { if (!disabled && !isLoading) setBtnState("rest"); }}
      onFocus={() => { if (!disabled && !isLoading) setBtnState("focus"); }}
      onBlur={() => { if (!disabled && !isLoading) setBtnState("rest"); }}
      onPointerDown={() => { if (!disabled && !isLoading) setBtnState("pressed"); }}
      onPointerUp={() => { if (!disabled && !isLoading) setBtnState("hover"); }}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[effectiveVariant]} ${className}`}
      {...props}
    >
      <IconStateContext.Provider value={{ state: effectiveState, isReducedMotion: motionCtx.isReducedMotion }}>
        {isLoading ? (
          <span className="inline-flex w-4 h-4 items-center justify-center animate-spin">
            <RefreshSyncIcon size={16} />
          </span>
        ) : (
          leftIcon
        )}
        <span className={isLoading ? "sr-only" : ""}>{children}</span>
        {isLoading && <span aria-hidden="true" className="opacity-75">{children}</span>}
        {!isLoading && rightIcon}
      </IconStateContext.Provider>
    </button>
  );
};
