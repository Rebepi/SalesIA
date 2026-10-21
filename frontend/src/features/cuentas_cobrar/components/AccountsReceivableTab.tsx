import { Panel1 } from "../sections/AccountsReceivableTab/Panel1";
import { Panel2 } from "../sections/AccountsReceivableTab/Panel2";
import { SeccionReconciliacionDeSaldo } from "../sections/AccountsReceivableTab/SeccionReconciliacionDeSaldo";
export type { ReceivableItem } from "../types/AccountsReceivableTab";
export type { CreditNoteItem } from "../types/AccountsReceivableTab";
export type { AccountsReceivableResponse } from "../types/AccountsReceivableTab";
export type { AccountsReceivableTabProps } from "../types/AccountsReceivableTab";
import { useAccountsReceivableTab } from "../hooks/useAccountsReceivableTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import "./receivables.css";
import { useEffect, useId, useRef, useState } from "react";
import { IconAction } from "../../../ui/components/primitives/IconAction";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { ReceivableActionDialog } from "./ReceivableActionDialog";
import { AccountsReceivableTabProps } from "../types/AccountsReceivableTab";

export function AccountsReceivableTab({ canWrite = true }: AccountsReceivableTabProps) {
  const { metrics, setRevision, action, setAction,  loading, error, selectedBucket, setSelectedBucket, search, setSearch, activeItem, setActiveItem, creditNotes, loadingReconcile, reconcileNotes, setReconcileNotes, toast, openReconciliation, filteredItems } = useAccountsReceivableTab({ canWrite });
  const summaryId = useId();
  const [cardsVisible, setCardsVisible] = useState(() => {
    try { return window.localStorage.getItem("salesia_receivables_cards_visible") !== "false"; }
    catch { return true; }
  });
  const [viewOpen, setViewOpen] = useState(false);
  const viewRef = useRef<HTMLDivElement>(null);
  const viewTriggerRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!viewOpen) return;
    const outside = (event: PointerEvent) => { if (!viewRef.current?.contains(event.target as Node)) setViewOpen(false); };
    const escape = (event: KeyboardEvent) => { if (event.key === "Escape") { setViewOpen(false); viewTriggerRef.current?.focus(); } };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => { document.removeEventListener("pointerdown", outside); document.removeEventListener("keydown", escape); };
  }, [viewOpen]);
  return (
    <div id="scr-019-receivables-tab" className="space-y-6">
      <NavbarSectionHeader view="receivables" className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Cuentas por Cobrar y Antigüedad de Deuda</h1>
          <p className="mt-1 text-xs text-slate-500">
            Control cronológico de vencimientos, tramos de cobranza y reconciliación de saldos con cobros y notas de crédito.
          </p>
        </div>
        <div className="flex items-center gap-2">

        </div>
      </NavbarSectionHeader>

      <div className="receivables-view-toolbar">
        <div className="receivables-view-config" ref={viewRef}>
          <IconAction ref={viewTriggerRef} label={cardsVisible ? "Configurar vista · tarjetas activadas" : "Configurar vista · tarjetas desactivadas"} tone={cardsVisible ? "primary" : "neutral"} aria-expanded={viewOpen} aria-controls={`${summaryId}-view`} onClick={() => setViewOpen(value => !value)}><SlidersHorizontal size={17} /></IconAction>
          {viewOpen && <div id={`${summaryId}-view`} className="receivables-view-menu" role="group" aria-label="Configuración de vista">
            <div className="receivables-view-heading"><h2>Configuración de vista</h2><IconAction label="Cerrar configuración de vista" onClick={() => setViewOpen(false)}><X size={16} /></IconAction></div>
            <label className="receivables-view-option"><span><strong>Mostrar tarjetas de información (KPIs)</strong><span>Muestra el resumen de saldos, vencimientos y disputas.</span></span><input type="checkbox" role="switch" checked={cardsVisible} aria-controls={summaryId} onChange={event => {
              const visible = event.target.checked;
              setCardsVisible(visible);
              try { window.localStorage.setItem("salesia_receivables_cards_visible", String(visible)); } catch {}
            }} /></label>
          </div>}
        </div>
      </div>
      {cardsVisible && <Panel1 id={summaryId} metrics={metrics} />}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {["ALL", "not_due", "0-30", "31-60", "61-90", "90+"].map(b => (
            <button
              key={b}
              onClick={() => setSelectedBucket(b)}
              className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition ${selectedBucket === b
                ? "bg-slate-900 text-white shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
            >
              {b === "ALL" ? "Todos los tramos" : b === "not_due" ? "Por vencer" : `${b} días de mora`}
            </button>
          ))}
        </div>

        <div className="relative w-64">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por documento o cliente"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-300 py-1.5 pl-8 pr-3 text-xs outline-none focus:ring-2 focus:ring-teal-200"
          />
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-800">
          {error}
        </div>
      )}

      <Panel2 filteredItems={filteredItems} setAction={setAction} canWrite={canWrite} openReconciliation={openReconciliation} loading={loading} />

      {action && <ReceivableActionDialog saleId={action.saleId} mode={action.mode} canWrite={canWrite} onClose={() => { setAction(null); setRevision(value => value + 1); }} onSaved={() => { setAction(null); setRevision(value => value + 1); }} />}
      {activeItem && (
        <SeccionReconciliacionDeSaldo activeItem={activeItem} setActiveItem={setActiveItem} loadingReconcile={loadingReconcile} creditNotes={creditNotes} reconcileNotes={reconcileNotes} setReconcileNotes={setReconcileNotes} toast={toast} />
      )}
    </div>
  );
}
