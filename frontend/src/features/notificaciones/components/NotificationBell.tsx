import { useEffect, useRef, useState } from "react";
import { Bell, X } from "lucide-react";
import { NotificationsWorkspaceTab } from "./NotificationsWorkspaceTab";

export function NotificationBell({ onNavigate }: { onNavigate: (view: string) => void }) {
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    closeButton.current?.focus();
    const outside = (event: PointerEvent) => {
      const target = event.target as Element;
      if (!root.current?.contains(target) && !target.closest(".custom-select-menu, .salesia-toasts")) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);

  const close = () => { setOpen(false); trigger.current?.focus(); };

  return <div ref={root} className="relative" onKeyDown={event => {
    if (event.key === "Escape" && open) { event.preventDefault(); event.stopPropagation(); close(); }
  }} onBlur={event => { if (event.relatedTarget && !event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}>
    <button ref={trigger} type="button" onClick={() => setOpen(value => !value)} aria-label={unread ? `Notificaciones, ${unread} sin leer` : "Notificaciones"} aria-expanded={open} aria-haspopup="dialog" aria-controls="navbar-notification-panel" title="Notificaciones" className="relative flex h-9 w-9 items-center justify-center rounded-xl border transition-colors hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-400" style={{ color: "var(--sb-text)", borderColor: "var(--sb-border)", background: open ? "var(--sb-hover)" : undefined }}>
      <Bell size={18} aria-hidden="true" />
      {unread > 0 && <span className="absolute -right-1 -top-1 flex min-w-4 h-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[9px] font-bold text-white ring-2" style={{ boxShadow: "0 0 0 2px var(--sb-bg)" }} aria-hidden="true">{unread > 99 ? "99+" : unread}</span>}
    </button>
    <div id="navbar-notification-panel" hidden={!open} role="dialog" aria-labelledby="notification-inbox-title" className="notification-popover fixed right-3 top-16 z-50 w-[min(440px,calc(100vw-24px))] overflow-hidden rounded-2xl border shadow-2xl sm:right-5" style={{ background: "var(--choice-bg)", borderColor: "var(--choice-border)", color: "var(--choice-text)" }}>
      <button ref={closeButton} type="button" onClick={close} aria-label="Cerrar notificaciones" className="absolute right-3 top-3 z-10 rounded-lg p-1.5 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-500"><X size={17} /></button>
      <div className="max-h-[calc(100dvh-88px)] overflow-y-auto overscroll-contain p-4">
        <NotificationsWorkspaceTab compact refreshKey={open} onUnreadCountChange={setUnread} onNavigate={view => { close(); onNavigate(view); }} />
      </div>
    </div>
  </div>;
}
