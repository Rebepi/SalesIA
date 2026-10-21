import React, { useEffect, useLayoutEffect, useState } from "react";
import { createPortal } from "react-dom";

const useClientLayoutEffect = typeof window === "undefined" ? useEffect : useLayoutEffect;

interface AnchoredListboxProps extends React.HTMLAttributes<HTMLUListElement> {
  anchorRef: React.RefObject<HTMLElement>;
  menuRef: React.RefObject<HTMLUListElement>;
  activeIndex: number;
}

export function AnchoredListbox({ anchorRef, menuRef, activeIndex, children, className = "", ...props }: AnchoredListboxProps) {
  const [position, setPosition] = useState<React.CSSProperties>({ visibility: "hidden" });

  useClientLayoutEffect(() => {
    let frame = 0;
    let previous = "";
    const update = () => {
      const anchor = anchorRef.current;
      const menu = menuRef.current;
      if (anchor && menu) {
        const rect = anchor.getBoundingClientRect();
        const viewport = window.visualViewport;
        const width = viewport?.width ?? window.innerWidth;
        const height = viewport?.height ?? window.innerHeight;
        const left = viewport?.offsetLeft ?? 0;
        const top = viewport?.offsetTop ?? 0;
        const menuWidth = Math.min(Math.max(rect.width, 180), width - 16);
        const below = Math.max(0, top + height - rect.bottom - 14);
        const above = Math.max(0, rect.top - top - 14);
        const upwards = below < Math.min(280, menu.scrollHeight) && above > below;
        const next: React.CSSProperties = {
          left: Math.max(left + 8, Math.min(rect.left, left + width - menuWidth - 8)),
          width: menuWidth,
          maxHeight: Math.min(280, upwards ? above : below),
          visibility: rect.bottom < top || rect.top > top + height ? "hidden" : "visible",
          ...(upwards ? { bottom: window.innerHeight - rect.top + 6 } : { top: rect.bottom + 6 })
        };
        const signature = JSON.stringify(next);
        if (signature !== previous) {
          previous = signature;
          setPosition(next);
        }
      }
      frame = requestAnimationFrame(update);
    };
    update();
    return () => cancelAnimationFrame(frame);
  }, [anchorRef, menuRef]);

  useClientLayoutEffect(() => {
    const menu = menuRef.current;
    const option = menu?.querySelectorAll<HTMLElement>('[role="option"]')[activeIndex];
    if (!menu || !option) return;
    const bounds = menu.getBoundingClientRect();
    const item = option.getBoundingClientRect();
    if (item.top < bounds.top + 6) menu.scrollTop -= bounds.top + 6 - item.top;
    else if (item.bottom > bounds.bottom - 6) menu.scrollTop += item.bottom - bounds.bottom + 6;
  }, [activeIndex, menuRef, position.maxHeight]);

  if (typeof document === "undefined") return null;
  const host = anchorRef.current?.closest("dialog[open]") ?? document.body;

  return createPortal(
    <ul {...props} ref={menuRef} role="listbox" className={`custom-select-menu ${className}`} style={position} onMouseDown={event => { if (!(event.target instanceof HTMLInputElement)) event.preventDefault(); }}>
      {children}
    </ul>,
    host
  );
}
