import React, { useState } from "react";
import { RefreshSyncIcon } from "../../icons/index";
import { IconStateContext, IconInteractionState, useMotion } from "../../motion";
import { Tooltip } from "./Tooltip";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "destructive";
  size?: "sm" | "md" | "lg";
  rounded?: boolean;
  ariaLabel: string;
  tooltip?: string;
  isLoading?: boolean;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  variant = "ghost",
  size = "md",
  rounded = false,
  ariaLabel,
  tooltip,
  isLoading = false,
  className = "",
  disabled,
  onPointerEnter,
  onPointerLeave,
  onFocus,
  onBlur,
  onPointerDown,
  onPointerUp,
  onTouchStart,
  onTouchEnd,
  ...props
}) => {
  const motionCtx = useMotion();
  const [containerState, setContainerState] = useState<IconInteractionState>("rest");

  const effectiveState: IconInteractionState = disabled
    ? "disabled"
    : isLoading
      ? "loading"
      : containerState;

  const sizeStyles = {
    sm: "p-1.5 min-w-[36px] min-h-[36px] text-xs",
    md: "p-2 min-w-[40px] min-h-[40px] text-sm",
    lg: "p-2.5 min-w-[48px] min-h-[48px] text-base"
  };

  const effectiveVariant = variant === "destructive" ? "danger" : variant;

  const variantStyles = {
    primary: "bg-blue-600 text-white hover:bg-blue-500 shadow-md",
    secondary: "bg-slate-800 text-slate-100 hover:bg-slate-700 border border-slate-700",
    outline: "border border-slate-600 text-slate-200 hover:bg-slate-800",
    ghost: "text-slate-300 hover:bg-slate-800 hover:text-white",
    danger: "bg-rose-600 text-white hover:bg-rose-500 shadow-md shadow-rose-900/20"
  };

  const handlePointerEnter = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!disabled && !isLoading) setContainerState("hover");
    if (onPointerEnter) onPointerEnter(e);
  };
  const handlePointerLeave = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!disabled && !isLoading) setContainerState("rest");
    if (onPointerLeave) onPointerLeave(e);
  };
  const handleFocus = (e: React.FocusEvent<HTMLButtonElement>) => {
    if (!disabled && !isLoading) setContainerState("focus");
    if (onFocus) onFocus(e);
  };
  const handleBlur = (e: React.FocusEvent<HTMLButtonElement>) => {
    if (!disabled && !isLoading) setContainerState("rest");
    if (onBlur) onBlur(e);
  };
  const handlePointerDown = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!disabled && !isLoading) setContainerState("pressed");
    if (onPointerDown) onPointerDown(e);
  };
  const handlePointerUp = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!disabled && !isLoading) setContainerState("hover");
    if (onPointerUp) onPointerUp(e);
  };
  const handleTouchStart = (e: React.TouchEvent<HTMLButtonElement>) => {
    if (!disabled && !isLoading) setContainerState("pressed");
    if (onTouchStart) onTouchStart(e);
  };
  const handleTouchEnd = (e: React.TouchEvent<HTMLButtonElement>) => {
    if (!disabled && !isLoading) setContainerState("rest");
    if (onTouchEnd) onTouchEnd(e);
  };

  const buttonElement = (
    <button
      aria-label={ariaLabel}
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      onPointerEnter={handlePointerEnter}
      onPointerLeave={handlePointerLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      className={`group inline-flex items-center justify-center transition-all duration-200 active:scale-95 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none focus:outline-none disabled:opacity-50 disabled:pointer-events-none ${rounded ? "rounded-full" : "rounded-xl"
        } ${sizeStyles[size]} ${variantStyles[effectiveVariant]} ${className}`}
      {...props}
    >
      <IconStateContext.Provider value={{ state: effectiveState, isReducedMotion: motionCtx.isReducedMotion }}>
        <span className="pointer-events-none flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
          {isLoading ? (
            <span className="inline-flex w-4 h-4 items-center justify-center animate-spin">
              <RefreshSyncIcon size={16} />
            </span>
          ) : (
            icon
          )}
        </span>
      </IconStateContext.Provider>
    </button>
  );

  if (tooltip) {
    return <Tooltip text={tooltip}>{buttonElement}</Tooltip>;
  }

  return buttonElement;
};
