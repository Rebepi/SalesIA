import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";
import { MotionMode } from "./tokens";

export interface MotionDurations {
  micro: number;
  standard: number;
  modal: number;
  toast: number;
}

export const MOTION_DURATIONS: MotionDurations = {
  micro: 100,
  standard: 180,
  modal: 220,
  toast: 300
};

export const ICON_GESTURE_DURATIONS: Record<string, number> = {
  squarePen: 240,
  plus: 180,
  check: 200,
  x: 140,
  copy: 220,
  download: 220,
  upload: 220,
  search: 180,
  settings: 220,
  bell: 260,
  eye: 180,
  eyeOff: 180,
  refreshCw: 240,
  archive: 240,
  undo: 200,
  redo: 200,
  arrowRight: 140,
  arrowLeft: 140,
  chevronDown: 160,
  chevronUp: 160,
  chevronRight: 140,
  chevronLeft: 140,
  circleHelp: 200,
  circleCheck: 240,
  clock: 240,
  calendarDays: 180,
  users: 200,
  userPlus: 180,
  cart: 200,
  box: 220,
  boxes: 240,
  creditCard: 220,
  wallet: 220,
  chartLine: 260,
  chartColumnIncreasing: 260,
  chartPie: 220,
  fileText: 220,
  logout: 180,
  lock: 200,
  shieldCheck: 220,
  moon: 200,
  sun: 200,
  menu: 160,
  externalLink: 180,
  send: 180,
  attachFile: 180,
  link: 180,
  gripVertical: 160,
  expand: 180,
  minimize: 180,
  truck: 220,
  badgePercent: 200,
  trash2: 240,
  trash: 220,
  fallback: 180
};

export const MOTION_EASINGS = {
  standard: "cubic-bezier(0.4, 0, 0.2, 1)",
  enter: "cubic-bezier(0.16, 1, 0.3, 1)",
  exit: "cubic-bezier(0.4, 0, 1, 1)",
  spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
  linear: "linear"
};

export const MOTION_STORAGE_KEY = "salesia_motion_preference";

export function isSystemReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

let memoryMotionPreference: MotionMode = "normal";

export function getStoredMotionPreference(): MotionMode {
  if (typeof window !== "undefined" && window.localStorage) {
    const stored = window.localStorage.getItem(MOTION_STORAGE_KEY);
    return stored === "reduced" ? "reduced" : "normal";
  }
  return memoryMotionPreference;
}

export function setStoredMotionPreference(mode: MotionMode): void {
  memoryMotionPreference = mode;
  if (typeof window !== "undefined" && window.localStorage) {
    window.localStorage.setItem(MOTION_STORAGE_KEY, mode);
  }
  if (typeof window !== "undefined" && typeof window.dispatchEvent === "function") {
    window.dispatchEvent(new CustomEvent("salesia-motion-preference-changed", { detail: mode }));
  }
}

export function resolveEffectiveMotion(userPreference?: MotionMode): boolean {
  const effectiveUserPref = userPreference ?? getStoredMotionPreference();
  if (effectiveUserPref === "reduced") {
    return true;
  }
  return isSystemReducedMotion();
}

export function subscribeToMotionPreference(callback: (isReduced: boolean) => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }
  const handleCustomEvent = (event: Event) => {
    const customEvent = event as CustomEvent<MotionMode>;
    const isReduced = resolveEffectiveMotion(customEvent.detail);
    callback(isReduced);
  };
  const mediaQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  const handleMediaChange = () => {
    callback(resolveEffectiveMotion());
  };
  window.addEventListener("salesia-motion-preference-changed", handleCustomEvent);
  if (mediaQuery && mediaQuery.addEventListener) {
    mediaQuery.addEventListener("change", handleMediaChange);
  } else if (mediaQuery && (mediaQuery as any).addListener) {
    (mediaQuery as any).addListener(handleMediaChange);
  }
  return () => {
    window.removeEventListener("salesia-motion-preference-changed", handleCustomEvent);
    if (mediaQuery && mediaQuery.removeEventListener) {
      mediaQuery.removeEventListener("change", handleMediaChange);
    } else if (mediaQuery && (mediaQuery as any).removeListener) {
      (mediaQuery as any).removeListener(handleMediaChange);
    }
  };
}

export function getMotionDurationMs(
  type: keyof MotionDurations,
  isReduced: boolean
): number {
  if (isReduced) {
    return 0;
  }
  return MOTION_DURATIONS[type];
}

export function getIconGestureDurationMs(
  iconKey: string,
  isReduced: boolean
): number {
  if (isReduced) {
    return 0;
  }
  return ICON_GESTURE_DURATIONS[iconKey] ?? 180;
}

export function getTransitionCss(
  type: keyof MotionDurations = "standard",
  properties: string = "all",
  isReduced: boolean = false
): string {
  if (isReduced) {
    return `${properties} 0ms linear`;
  }
  const duration = MOTION_DURATIONS[type];
  return `${properties} ${duration}ms ${MOTION_EASINGS.standard}`;
}

export type IconInteractionState =
  | "rest"
  | "hover"
  | "focus"
  | "pressed"
  | "disabled"
  | "loading"
  | "success"
  | "error";

export interface IconStateContextValue {
  state: IconInteractionState;
  isReducedMotion: boolean;
}

export const IconStateContext = createContext<IconStateContextValue>({
  state: "rest",
  isReducedMotion: false
});

export function useIconState(): IconStateContextValue {
  return useContext(IconStateContext);
}

export interface MotionContextValue {
  motionMode: MotionMode;
  isReducedMotion: boolean;
  setMotionMode: (mode: MotionMode) => void;
  getDuration: (standardDurationMs: number) => number;
}

export const MotionContext = createContext<MotionContextValue>({
  motionMode: "normal",
  isReducedMotion: false,
  setMotionMode: () => {},
  getDuration: (standardDurationMs: number) => standardDurationMs
});

export function useMotion(): MotionContextValue {
  return useContext(MotionContext);
}

export interface MotionProviderProps {
  children: React.ReactNode;
  initialMode?: MotionMode;
}

export const MotionProvider: React.FC<MotionProviderProps> = ({
  children,
  initialMode
}) => {
  const [motionMode, setMotionModeState] = useState<MotionMode>(() => {
    return initialMode ?? getStoredMotionPreference();
  });
  const [isReducedMotion, setIsReducedMotion] = useState<boolean>(() => {
    return resolveEffectiveMotion(initialMode ?? getStoredMotionPreference());
  });

  const setMotionMode = useCallback((mode: MotionMode) => {
    setMotionModeState(mode);
    setStoredMotionPreference(mode);
    setIsReducedMotion(resolveEffectiveMotion(mode));
  }, []);

  useEffect(() => {
    const unsubscribe = subscribeToMotionPreference((reduced) => {
      setIsReducedMotion(reduced);
    });
    return () => {
      unsubscribe();
    };
  }, []);

  const getDuration = useCallback((standardDurationMs: number) => {
    return isReducedMotion ? 0 : standardDurationMs;
  }, [isReducedMotion]);

  const value: MotionContextValue = {
    motionMode,
    isReducedMotion,
    setMotionMode,
    getDuration
  };

  return React.createElement(MotionContext.Provider, { value }, children);
};

export interface MotionTriggerContainerProps {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  isLoading?: boolean;
  role?: string;
  tabIndex?: number;
  onActivate?: () => void;
  onHoverFeedback?: () => void;
  ariaLabel?: string;
}

export const MotionTriggerContainer: React.FC<MotionTriggerContainerProps> = ({
  children,
  className = "",
  disabled = false,
  isLoading = false,
  role,
  tabIndex = 0,
  onActivate,
  onHoverFeedback,
  ariaLabel
}) => {
  const motionCtx = useMotion();
  const [localState, setLocalState] = useState<IconInteractionState>("rest");
  const timerRef = useRef<number | null>(null);

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
    if (disabled) {
      setLocalState("disabled");
      clearTimer();
    } else if (isLoading) {
      setLocalState("loading");
      clearTimer();
    } else if (localState === "disabled" || localState === "loading") {
      setLocalState("rest");
    }
  }, [disabled, isLoading, localState, clearTimer]);

  const handlePointerEnter = () => {
    if (disabled || isLoading) return;
    clearTimer();
    setLocalState("hover");
    if (onHoverFeedback) {
      onHoverFeedback();
    }
  };

  const handlePointerLeave = () => {
    if (disabled || isLoading) return;
    clearTimer();
    setLocalState("rest");
  };

  const handleFocus = () => {
    if (disabled || isLoading) return;
    clearTimer();
    setLocalState("focus");
  };

  const handleBlur = () => {
    if (disabled || isLoading) return;
    clearTimer();
    setLocalState("rest");
  };

  const handlePointerDown = () => {
    if (disabled || isLoading) return;
    setLocalState("pressed");
  };

  const handlePointerUp = () => {
    if (disabled || isLoading) return;
    setLocalState("hover");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (disabled || isLoading) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setLocalState("pressed");
      if (onActivate) {
        onActivate();
      }
      timerRef.current = window.setTimeout(() => {
        setLocalState("focus");
      }, 150);
    }
  };

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (disabled || isLoading) {
      e.preventDefault();
      return;
    }
    if (onActivate) {
      onActivate();
    }
  };

  const effectiveState: IconInteractionState = disabled
    ? "disabled"
    : isLoading
    ? "loading"
    : localState;

  return React.createElement(
    "div",
    {
      role,
      tabIndex: disabled ? -1 : tabIndex,
      "aria-label": ariaLabel,
      "aria-disabled": disabled,
      "aria-busy": isLoading,
      onPointerEnter: handlePointerEnter,
      onPointerLeave: handlePointerLeave,
      onFocus: handleFocus,
      onBlur: handleBlur,
      onPointerDown: handlePointerDown,
      onPointerUp: handlePointerUp,
      onKeyDown: handleKeyDown,
      onClick: handleClick,
      className: `select-none inline-flex items-center justify-center ${className}`
    },
    React.createElement(
      IconStateContext.Provider,
      { value: { state: effectiveState, isReducedMotion: motionCtx.isReducedMotion } },
      children
    )
  );
};

export function createFiniteAnimationTimer(
  onComplete: () => void,
  durationMs: number
): { cancel: () => void } {
  const timer = setTimeout(() => {
    onComplete();
  }, durationMs);
  return {
    cancel: () => {
      clearTimeout(timer);
    }
  };
}
