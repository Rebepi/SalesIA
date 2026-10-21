import React, { useState, useEffect, useRef, useCallback } from "react";
import { IconInteractionState, useIconState, resolveEffectiveMotion, getIconGestureDurationMs } from "../../motion";

export interface IconProps {
  size?: number;
  className?: string;
  color?: string;
  state?: IconInteractionState;
  reducedMotion?: boolean;
  role?: string;
  "aria-hidden"?: boolean | "true" | "false";
  "aria-label"?: string;
  tabIndex?: number;
  onClick?: React.MouseEventHandler<SVGSVGElement | HTMLSpanElement>;
  onMouseEnter?: React.MouseEventHandler<SVGSVGElement | HTMLSpanElement>;
  onMouseLeave?: React.MouseEventHandler<SVGSVGElement | HTMLSpanElement>;
  onFocus?: React.FocusEventHandler<SVGSVGElement | HTMLSpanElement>;
  onBlur?: React.FocusEventHandler<SVGSVGElement | HTMLSpanElement>;
  onTouchStart?: React.TouchEventHandler<SVGSVGElement | HTMLSpanElement>;
  onTouchEnd?: React.TouchEventHandler<SVGSVGElement | HTMLSpanElement>;
}

export interface IconGestureProps extends IconProps {
  iconId: string;
  renderPaths: (effectiveState: IconInteractionState, isReduced: boolean) => React.ReactNode;
}

export const AnimatedIconBase: React.FC<IconGestureProps> = ({
  iconId,
  size = 20,
  className = "",
  color = "currentColor",
  state: explicitState,
  reducedMotion: explicitReduced,
  role,
  "aria-hidden": ariaHidden,
  "aria-label": ariaLabel,
  tabIndex,
  onClick,
  onMouseEnter,
  onMouseLeave,
  onFocus,
  onBlur,
  onTouchStart,
  onTouchEnd,
  renderPaths
}) => {
  const contextState = useIconState();
  const [internalState, setInternalState] = useState<IconInteractionState>("rest");
  const timerRef = useRef<number | null>(null);

  const isReduced = explicitReduced ?? (contextState.isReducedMotion || resolveEffectiveMotion());
  const effectiveState: IconInteractionState = explicitState ?? (contextState.state !== "rest" ? contextState.state : internalState);

  const durationMs = getIconGestureDurationMs(iconId, isReduced);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null && typeof window !== "undefined") {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      clearTimer();
    };
  }, [clearTimer]);

  useEffect(() => {
    if (isReduced && internalState !== "rest" && internalState !== "disabled" && internalState !== "loading") {
      clearTimer();
      setInternalState("rest");
    }
  }, [isReduced, internalState, clearTimer]);

  const handlePointerEnter = (e: React.MouseEvent<HTMLSpanElement>) => {
    if (effectiveState === "disabled" || effectiveState === "loading") return;
    clearTimer();
    setInternalState("hover");
    if (!isReduced && durationMs > 0 && typeof window !== "undefined") {
      timerRef.current = window.setTimeout(() => {
        setInternalState("rest");
      }, durationMs);
    }
    if (onMouseEnter) onMouseEnter(e);
  };

  const handlePointerLeave = (e: React.MouseEvent<HTMLSpanElement>) => {
    if (effectiveState === "disabled" || effectiveState === "loading") return;
    clearTimer();
    setInternalState("rest");
    if (onMouseLeave) onMouseLeave(e);
  };

  const handleFocus = (e: React.FocusEvent<HTMLSpanElement>) => {
    if (effectiveState === "disabled" || effectiveState === "loading") return;
    clearTimer();
    setInternalState("focus");
    if (!isReduced && durationMs > 0 && typeof window !== "undefined") {
      timerRef.current = window.setTimeout(() => {
        setInternalState("rest");
      }, durationMs);
    }
    if (onFocus) onFocus(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLSpanElement>) => {
    if (effectiveState === "disabled" || effectiveState === "loading") return;
    clearTimer();
    setInternalState("rest");
    if (onBlur) onBlur(e);
  };

  const handleTouchStart = (e: React.TouchEvent<HTMLSpanElement>) => {
    if (effectiveState === "disabled" || effectiveState === "loading") return;
    clearTimer();
    setInternalState("pressed");
    if (onTouchStart) onTouchStart(e);
  };

  const handleTouchEnd = (e: React.TouchEvent<HTMLSpanElement>) => {
    if (effectiveState === "disabled" || effectiveState === "loading") return;
    clearTimer();
    if (!isReduced && typeof window !== "undefined") {
      timerRef.current = window.setTimeout(() => {
        setInternalState("rest");
      }, 150);
    } else {
      setInternalState("rest");
    }
    if (onTouchEnd) onTouchEnd(e);
  };

  const stateClasses = effectiveState === "disabled" ? "opacity-40 cursor-not-allowed" : "";

  return (
    <span
      role={role}
      aria-hidden={ariaHidden ?? (ariaLabel ? undefined : true)}
      aria-label={ariaLabel}
      tabIndex={tabIndex}
      onClick={onClick}
      onMouseEnter={handlePointerEnter}
      onMouseLeave={handlePointerLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      style={{
        width: size,
        height: size,
        minWidth: size,
        minHeight: size,
        maxWidth: size,
        maxHeight: size
      }}
      className={`inline-flex items-center justify-center flex-shrink-0 select-none overflow-visible ${stateClasses} ${className}`}
      data-icon-id={iconId}
      data-interaction-state={effectiveState}
      data-reduced-motion={isReduced ? "true" : "false"}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{
          width: size,
          height: size,
          overflow: "visible"
        }}
        className="pointer-events-none"
      >
        {renderPaths(effectiveState, isReduced)}
      </svg>
    </span>
  );
};
