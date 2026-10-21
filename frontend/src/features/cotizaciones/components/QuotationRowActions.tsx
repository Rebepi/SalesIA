import { Tooltip } from "../../../ui/components/primitives/Tooltip";
import { useEffect, useId, useLayoutEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import { ArrowRight, CheckCircle2, Download, Eye, GitBranch, History, Mail, MoreHorizontal } from "lucide-react";
import "./quotation-actions.css";

type Props = {
  number: string;
  status: string;
  version: number;
  canWrite: boolean;
  busy: boolean;
  onAccept: () => void;
  onVersion: () => void;
  onConvert: () => void;
  onReview: () => void;
  onPreview: () => void;
  onDownload: () => void;
  onSend: () => void;
};

export function QuotationRowActions({ number, status, version, canWrite, busy, onAccept, onVersion, onConvert, onReview, onPreview, onDownload, onSend }: Props) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<CSSProperties>({ visibility: "hidden" });
  const trigger = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const id = useId();
  const canRevise = canWrite && ["pending", "negotiating"].includes(status);
  const items = [
    { label: "Vista previa", Icon: Eye, run: onPreview, tone: "preview", disabled: false },
    { label: "Descargar PDF", Icon: Download, run: onDownload, tone: "download", disabled: false },
    ...(canWrite ? [{ label: "Enviar cotización", Icon: Mail, run: onSend, tone: "send", disabled: false }] : []),
    ...(canRevise ? [{ label: `Nueva versión · v${version + 1}`, Icon: GitBranch, run: onVersion, tone: "version", disabled: busy }] : []),
  ];
  function close(restoreFocus = false) {
    setOpen(false);
    if (restoreFocus) trigger.current?.focus();
  }
  useLayoutEffect(() => {
    if (!open || !trigger.current || !menu.current) return;
    const rect = trigger.current.getBoundingClientRect();
    const height = menu.current.offsetHeight;
    const width = 224;
    const top = rect.bottom + height + 12 > window.innerHeight ? Math.max(8, rect.top - height - 6) : rect.bottom + 6;
    setPosition({ top, left: Math.max(8, Math.min(rect.right - width, window.innerWidth - width - 8)), visibility: "visible" });
  }, [open]);
  useLayoutEffect(() => {
    if (open && position.visibility === "visible") menu.current?.querySelector<HTMLButtonElement>("button:not(:disabled)")?.focus();
  }, [open, position.visibility]);
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => { if (!menu.current?.contains(event.target as Node) && !trigger.current?.contains(event.target as Node)) close(); };
    const reposition = (event: Event) => { if (!menu.current?.contains(event.target as Node)) close(); };
    document.addEventListener("pointerdown", outside);
    window.addEventListener("scroll", reposition, true);
    window.addEventListener("resize", reposition);
    return () => { document.removeEventListener("pointerdown", outside); window.removeEventListener("scroll", reposition, true); window.removeEventListener("resize", reposition); };
  }, [open]);
  function menuKeys(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close(true); }
    if (event.key === "Tab") { event.preventDefault(); close(true); }
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const buttons = Array.from(menu.current?.querySelectorAll<HTMLButtonElement>("button:not(:disabled)") || []);
      const current = buttons.indexOf(document.activeElement as HTMLButtonElement);
      const next = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : (current + (event.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length;
      buttons[next]?.focus();
    }
  }
  return <div className="quotation-row-actions" role="group" aria-label={`Acciones de ${number}`}>
    {canRevise && <Tooltip text="Aceptar cotización" portal><button type="button" className="quotation-icon-action quotation-icon-accept" aria-label="Aceptar cotización" disabled={busy} onClick={onAccept}><CheckCircle2 size={17} aria-hidden="true" /></button></Tooltip>}
    {canWrite && status === "accepted" && <Tooltip text="Convertir a pedido" portal><button type="button" className="quotation-icon-action quotation-icon-convert" aria-label="Convertir a pedido" disabled={busy} onClick={onConvert}><ArrowRight size={17} aria-hidden="true" /></button></Tooltip>}
    <Tooltip text="Versiones y negociación" portal><button type="button" className="quotation-icon-action quotation-icon-history" aria-label="Versiones y negociación" onClick={onReview}><History size={17} aria-hidden="true" /></button></Tooltip>
    <Tooltip text="Más acciones" portal><button type="button" ref={trigger} className="quotation-icon-action quotation-icon-more" aria-label="Más acciones" aria-haspopup="menu" aria-expanded={open} aria-controls={open ? id : undefined} onClick={() => setOpen(value => !value)} onKeyDown={event => { if (event.key === "ArrowDown" || event.key === "ArrowUp") { event.preventDefault(); setOpen(true); } }}><MoreHorizontal size={18} aria-hidden="true" /></button></Tooltip>
    {open && createPortal(<div id={id} ref={menu} role="menu" aria-label={`Más acciones de ${number}`} className="quotation-action-menu" style={position} onKeyDown={menuKeys} onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) close(); }}>
      {items.map(item => <button type="button" role="menuitem" className={`quotation-menu-${item.tone}`} key={item.label} disabled={item.disabled} onClick={() => { close(true); item.run(); }}><span className="quotation-menu-icon" aria-hidden="true"><item.Icon size={16} /></span><span>{item.label}</span></button>)}
    </div>, document.body)}
  </div>;
}
