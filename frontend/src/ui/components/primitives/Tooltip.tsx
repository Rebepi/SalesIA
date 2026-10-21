import React, { useEffect, useLayoutEffect, useRef, useState, useId, type CSSProperties } from "react";
import { createPortal } from "react-dom";

const useClientLayoutEffect = typeof window === "undefined" ? useEffect : useLayoutEffect;

export const Tooltip: React.FC<{ text: string; children: React.ReactNode; portal?: boolean }> = ({ text, children, portal = false }) => {
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState<CSSProperties>({ visibility: "hidden" });
  const anchor = useRef<HTMLDivElement>(null);
  const bubble = useRef<HTMLDivElement>(null);
  const generatedId = useId();
  const tooltipId = `tooltip-${generatedId.replace(/:/g, "")}`;
  useClientLayoutEffect(() => {
    if (!visible || !portal || !anchor.current || !bubble.current) return;
    const rect = anchor.current.getBoundingClientRect();
    const bounds = bubble.current.getBoundingClientRect();
    const left = Math.max(8, Math.min(rect.left + rect.width / 2 - bounds.width / 2, window.innerWidth - bounds.width - 8));
    const top = rect.top - bounds.height - 8 >= 8 ? rect.top - bounds.height - 8 : rect.bottom + 8;
    setPosition({ position: "fixed", left, top, maxWidth: "calc(100vw - 16px)", zIndex: 120, visibility: "visible" });
  }, [visible, portal, text]);
  useEffect(() => {
    if (!visible || !portal) return;
    const hide = () => setVisible(false);
    window.addEventListener("scroll", hide, true);
    window.addEventListener("resize", hide);
    document.addEventListener("pointerdown", hide);
    return () => { window.removeEventListener("scroll", hide, true); window.removeEventListener("resize", hide); document.removeEventListener("pointerdown", hide); };
  }, [visible, portal]);
  const content = visible ? <div ref={bubble} id={tooltipId} role="tooltip" style={portal ? position : undefined} className={`${portal ? "" : "absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50"} px-3 py-2 text-xs font-medium text-slate-100 bg-slate-800 border border-slate-700 rounded-lg shadow-xl whitespace-normal w-max pointer-events-none`}>{text}</div> : null;
  const trigger = React.isValidElement<{ "aria-describedby"?: string }>(children) ? React.cloneElement(children, { "aria-describedby": visible ? [children.props["aria-describedby"], tooltipId].filter(Boolean).join(" ") : children.props["aria-describedby"] }) : children;
  return <div ref={anchor} className="relative inline-flex" onMouseEnter={() => setVisible(true)} onMouseLeave={() => setVisible(false)} onFocus={() => setVisible(true)} onBlur={() => setVisible(false)} onClick={() => setVisible(false)} onKeyDown={event => { if (event.key === "Escape") setVisible(false); }}>
    {trigger}
    {portal && content ? createPortal(content, document.body) : content}
  </div>;
};
