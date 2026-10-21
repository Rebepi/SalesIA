import { useEffect } from "react";
import { CashForecastPanel } from "./CashForecastPanel";
import { PettyCashPanel } from "./PettyCashPanel";
import { CashCustodyPanel } from "./CashCustodyPanel";
import { SeccionMovimientosDeLaSesion } from "../sections/CashRegisterWorkspaceTab/SeccionMovimientosDeLaSesion";
export type { CashMovement } from "../types/CashRegisterWorkspaceTab";
export type { CashSession } from "../types/CashRegisterWorkspaceTab";
export type { CashRegisterWorkspaceTabProps } from "../types/CashRegisterWorkspaceTab";
import { useCashRegisterWorkspaceTab } from "../hooks/useCashRegisterWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { RefreshCw, Unlock, X } from "lucide-react";
import { CashDenominationCounter } from "./CashDenominationCounter";
import { CashRegisterWorkspaceTabProps } from "../types/CashRegisterWorkspaceTab";
import { formatMoney } from "../support/CashRegisterWorkspaceTab";

export function CashRegisterWorkspaceTab({ canWrite = true, currentBranchId = "", section = "sessions" }: CashRegisterWorkspaceTabProps) {
  const { sessions, selectedSessionId, setSelectedSessionId, revision, openingCurrency, sessionsCount, activeSession, loading, error, setRevision, branches, currency, modalType, setModalType, handleOpenSession, handleNewMovement, handleBlindCount, handleApproveDifference, handleCloseSession } = useCashRegisterWorkspaceTab({ canWrite, currentBranchId, section });
  const sessionSection = ["sessions", "movements", "counts"].includes(section);
  useEffect(() => { setModalType(null); }, [section, setModalType]);
  return (
    <div id="scr-020-cash-register-tab" className="space-y-6">
      {sessionSection && <NavbarSectionHeader view={section === "sessions" ? "cash" : `cash_${section}`} className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Control de Caja y Arqueo Ciego</h1>
          <p className="mt-1 text-xs text-slate-500">
            Apertura de turno, movimientos de ingresos/egresos, arqueo de valores y cierre con justificación de diferencias.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setRevision(r => r + 1)}
            disabled={loading}
            aria-label="Actualizar caja"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Actualizar
          </button>
          {canWrite && section === "sessions" && (
            <button
              onClick={() => setModalType("open_session")}
              className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3.5 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition"
              data-testid="open-session-btn"
            >
              <Unlock className="h-3.5 w-3.5" />
              Abrir Turno de Caja
            </button>
          )}
        </div>
      </NavbarSectionHeader>}

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700">
          <p>{error}</p>
        </div>
      ) : null}

      {sessionSection && sessionsCount > 1 ? (
        <label className="block text-xs text-slate-600">Sesión de caja ({sessionsCount})
          <CustomSelect searchable value={activeSession?.id || selectedSessionId} onChange={event => { setSelectedSessionId(event.target.value); setModalType(null); }} className="mt-2 w-full rounded-xl border border-slate-200 p-2">
            {sessions.map(session => <option key={session.id} value={session.id}>{session.terminal_code} · {session.currency} · {session.status === "open" ? "Abierta" : "Cerrada"} · {session.opened_at.slice(0, 10)}</option>)}
          </CustomSelect>
        </label>
      ) : null}

      {sessionSection && (activeSession ? (
        <SeccionMovimientosDeLaSesion section={section === "movements" ? "movements" : section === "counts" ? "counts" : "sessions"} activeSession={activeSession} canWrite={canWrite} setModalType={setModalType} currency={currency} />
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-300 p-12 text-center">
          <p className="text-sm text-slate-500">No hay turnos de caja registrados actualmente.</p>
          {canWrite && (
            <button
              onClick={() => setModalType("open_session")}
              className="mt-4 rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition"
            >
              Abrir Turno Ahora
            </button>
          )}
        </div>
      ))}

      {section === "custody" && <CashCustodyPanel canWrite={canWrite} revision={revision} onChanged={() => setRevision(value => value + 1)} />}
      {section === "petty" && <PettyCashPanel canWrite={canWrite} revision={revision} onChanged={() => setRevision(value => value + 1)} />}
      {section === "forecast" && <CashForecastPanel canWrite={canWrite} revision={revision} />}

      {modalType === "open_session" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Apertura de Turno de Caja</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleOpenSession} className="mt-4 space-y-4">
              <label className="block text-xs font-semibold text-slate-700">
                Código de Terminal / TPV
                <input name="terminal_code" defaultValue="TPV-01" required className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Sede / Sucursal
                <CustomSelect remote={{ resource: "branches" }} name="branch_id" defaultValue={currentBranchId || (branches.length === 1 ? branches[0].branch_id : "")} searchable required className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs"><option value="">Seleccionar sede</option>{branches.map(branch => <option key={branch.branch_id} value={branch.branch_id}>{branch.name} ({branch.code})</option>)}</CustomSelect>
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Moneda de la caja
                <input name="currency" defaultValue={openingCurrency} pattern="[A-Z]{3}" maxLength={3} required className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs" />
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Fondo Fijo de Apertura (en la moneda elegida)
                <input name="opening_balance" type="number" step="0.01" min="0" defaultValue="100.00" required className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition">Confirmar Apertura</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalType === "new_movement" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Registrar Movimiento de Efectivo</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleNewMovement} className="mt-4 space-y-4">
              <label className="block text-xs font-semibold text-slate-700">
                Tipo de Operación
                <CustomSelect name="movement_type" className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs">
                  <option value="DEPOSIT">Depósito / Ingreso extraordinario</option>
                  <option value="WITHDRAWAL">Retiro / Egreso de caja menor</option>
                </CustomSelect>
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Monto ({currency})
                <input name="amount" type="number" step="0.01" min="0.01" required className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Motivo / Justificación
                <input name="reason" placeholder="Pago de flete menor, cambio de sencillo, etc." required className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition">Registrar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalType === "blind_count" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Arqueo Ciego de Turno</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleBlindCount} className="mt-4 space-y-4">
              <p className="text-xs text-slate-500">
                Ingrese el total físico de efectivo contado en gaveta sin consultar saldos teóricos previos.
              </p>
              <CashDenominationCounter key={`${activeSession?.id}-${currency}`} currency={currency} />
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition">Enviar Conteo Ciego</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalType === "approve_diff" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Autorizar Diferencia de Caja</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleApproveDifference} className="mt-4 space-y-4">
              <label className="block text-xs font-semibold">Decisión
                <select name="decision" className="ml-3 rounded-xl border p-2"><option value="approve">Aprobar diferencia</option><option value="reject">Rechazar y solicitar nuevo conteo</option></select>
              </label>
              <p className="text-xs text-slate-500">
                Diferencia actual: {formatMoney(activeSession?.difference_cash || 0, currency)}. Ingrese el sustento gerencial.
              </p>
              <label className="block text-xs font-semibold text-slate-700">
                Justificación de la Discrepancia
                <textarea name="notes" rows={3} minLength={5} required placeholder="Motivo documentado del faltante o sobrante" className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" className="rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-700 transition">Guardar revisión</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalType === "close_session" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Cierre Definitivo de Caja</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleCloseSession} className="mt-4 space-y-4">
              <label className="block text-xs font-semibold text-slate-700">
                Saldo Final Contado ({currency})
                <input name="counted_balance" type="number" step="0.01" min="0" required readOnly value={activeSession?.control.counted_cash || ""} className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Observaciones de Cierre
                <textarea name="notes" rows={2} placeholder="Comentarios de entrega a tesorería o siguiente turno" className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition">Confirmar Cierre de Turno</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
