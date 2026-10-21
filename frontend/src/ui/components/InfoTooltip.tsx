import { Info } from "lucide-react";
import { useId, useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";

export interface InfoTooltipProps {
  title: string;
  description: string;
  className?: string;
  align?: "left" | "center" | "right";
  interactive?: boolean;
}

export function InfoTooltip({
  title,
  description,
  className = "",
  align = "center",
  interactive = false,
}: InfoTooltipProps) {
  const reactId = useId();
  const tooltipId = `info-tooltip-${reactId.replace(/:/g, "")}`;
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState<{
    top: number;
    left: number;
    placement: "top" | "bottom";
  } | null>(null);
  const iconRef = useRef<HTMLSpanElement>(null);
  const pinned = useRef(false);
  const popupRef = useRef<HTMLSpanElement>(null);
  const suppressFocusOpen = useRef(false);

  const updatePosition = useCallback(() => {
    if (!iconRef.current || typeof window === "undefined") return;
    const rect = iconRef.current.getBoundingClientRect();
    const tooltipWidth = 288;
    const padding = 16;
    const placement: "top" | "bottom" = rect.top >= 120 ? "top" : "bottom";
    const iconCenterX = rect.left + rect.width / 2;

    let targetLeft = iconCenterX - tooltipWidth / 2;
    if (align === "left") {
      targetLeft = rect.left;
    } else if (align === "right") {
      targetLeft = rect.right - tooltipWidth;
    }

    const maxLeft = Math.max(padding, window.innerWidth - tooltipWidth - padding);
    const clampedLeft = Math.max(padding, Math.min(maxLeft, targetLeft));
    const top = placement === "top" ? rect.top - 8 : rect.bottom + 8;

    setPosition({
      top,
      left: clampedLeft,
      placement,
    });
  }, [align]);

  const handleOpen = () => {
    if (suppressFocusOpen.current) return;
    updatePosition();
    setVisible(true);
  };

  const handleClose = () => {
    if (!pinned.current) setVisible(false);
  };
  const togglePinned = () => { pinned.current = !pinned.current; updatePosition(); setVisible(pinned.current); };
  useEffect(() => {
    if (!interactive || !visible) return;
    const dismiss = (event: PointerEvent) => { if (!iconRef.current?.contains(event.target as Node) && !popupRef.current?.contains(event.target as Node)) { pinned.current = false; setVisible(false); } };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [interactive, visible]);

  useEffect(() => {
    if (!visible) return;
    updatePosition();
    const handleScrollOrResize = () => {
      updatePosition();
    };
    window.addEventListener("scroll", handleScrollOrResize, true);
    window.addEventListener("resize", handleScrollOrResize);
    return () => {
      window.removeEventListener("scroll", handleScrollOrResize, true);
      window.removeEventListener("resize", handleScrollOrResize);
    };
  }, [visible, updatePosition]);

  const portalContent = visible && position && typeof document !== "undefined"
    ? createPortal(
      <span
        ref={popupRef}
        tabIndex={interactive ? 0 : undefined}
        aria-label={interactive ? `Ayuda: ${title}` : undefined}
        onKeyDown={event => {
          if (interactive && event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            pinned.current = false;
            setVisible(false);
            suppressFocusOpen.current = true;
            iconRef.current?.focus({ preventScroll: true });
            suppressFocusOpen.current = false;
          }
        }}
        onBlur={event => {
          if (!popupRef.current?.contains(event.relatedTarget as Node) && !iconRef.current?.contains(event.relatedTarget as Node)) { pinned.current = false; setVisible(false); }
        }}
        style={{
          position: "fixed",
          top: `${position.top}px`,
          left: `${position.left}px`,
          width: "288px",
          maxWidth: "calc(100vw - 32px)",
          transform: position.placement === "top" ? "translateY(-100%)" : "translateY(0)",
          zIndex: 99999,
          maxHeight: position.placement === "top" ? `${Math.max(80, position.top - 12)}px` : `calc(100vh - ${position.top + 12}px)`,
          overflowY: "auto",
          pointerEvents: interactive ? "auto" : undefined,
        }}
        className="pointer-events-none rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-left text-xs leading-relaxed text-slate-600 shadow-2xl dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300 animate-in fade-in zoom-in-95 duration-150"
      >
        <strong className="mb-0.5 block font-semibold text-slate-900 dark:text-white">
          {title}
        </strong>
        {description}
      </span>,
      iconRef.current?.closest("dialog") || document.body
    )
    : null;

  return (
    <span
      className={`relative inline-flex shrink-0 align-middle ${className}`}
      onMouseEnter={handleOpen}
      onMouseLeave={handleClose}
      onFocus={handleOpen}
      onBlur={event => { if (!popupRef.current?.contains(event.relatedTarget as Node) && !iconRef.current?.contains(event.relatedTarget as Node)) { pinned.current = false; setVisible(false); } }}
      onKeyDown={(event) => {
        if (event.key === "Escape" && visible) { event.preventDefault(); event.stopPropagation(); pinned.current = false; setVisible(false); }
        if (interactive && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); event.stopPropagation(); const opening = !pinned.current; togglePinned(); if (opening) requestAnimationFrame(() => popupRef.current?.focus({ preventScroll: true })); }
      }}
    >
      <span
        ref={iconRef}
        tabIndex={0}
        role={interactive ? "button" : "img"}
        aria-expanded={interactive ? visible : undefined}
        onClick={interactive ? event => { event.stopPropagation(); togglePinned(); } : undefined}
        aria-label={`Información sobre ${title}`}
        aria-describedby={tooltipId}
        className="inline-flex h-5 w-5 cursor-help items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-teal-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-teal-300 dark:focus-visible:ring-offset-slate-900"
      >
        <Info aria-hidden="true" size={14} strokeWidth={2} />
      </span>
      <span
        id={tooltipId}
        role="tooltip"
        aria-hidden="true"
        className="sr-only"
      >
        <strong className="font-semibold">{title}</strong> {description}
      </span>
      {portalContent}
    </span>
  );
}
