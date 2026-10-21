import type { useCashRegisterWorkspaceTab } from "../../hooks/useCashRegisterWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { Lock, Unlock } from "lucide-react";
import { CashRegisterWorkspaceTabProps } from "../../types/CashRegisterWorkspaceTab";
import { formatMoney } from "../../support/CashRegisterWorkspaceTab";

export function SeccionMovimientosDeLaSesion({ section = "sessions", activeSession, canWrite, setModalType, currency }: { section?: "sessions" | "movements" | "counts"; activeSession: NonNullable<ReturnType<typeof useCashRegisterWorkspaceTab>["activeSession"]>; setModalType: ReturnType<typeof useCashRegisterWorkspaceTab>["setModalType"]; currency: ReturnType<typeof useCashRegisterWorkspaceTab>["currency"] } & { canWrite: NonNullable<CashRegisterWorkspaceTabProps["canWrite"]> }) {
  return (<div className="space-y-6">
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${activeSession.status === "open"
              ? "bg-teal-100 text-teal-800"
              : "bg-slate-100 text-slate-700"
              }`}
            data-testid="cash-session-status"
          >
            {activeSession.status === "open" ? (
              <>
                <Unlock className="h-3.5 w-3.5 text-teal-600" />
                Turno Abierto
              </>
            ) : (
              <>
                <Lock className="h-3.5 w-3.5 text-slate-500" />
                Turno Cerrado
              </>
            )}
          </span>
          <span className="font-mono text-xs font-semibold text-slate-800">
            Terminal: {activeSession.terminal_code}
          </span>
        </div>

        {activeSession.status === "open" && canWrite && (
          <div className="flex flex-wrap gap-2">
            {section !== "counts" && <button
              onClick={() => setModalType("new_movement")}
              className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
              disabled={!activeSession.can_count && !activeSession.can_approve}
              data-testid="add-movement-btn"
            >
              Movimiento de Caja
            </button>}
            {section !== "movements" && <button
              onClick={() => setModalType("blind_count")}
              className="rounded-xl border border-teal-200 bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-800 hover:bg-teal-100 transition"
              disabled={!activeSession.can_count}
              data-testid="blind-count-btn"
            >
              Arqueo Ciego
            </button>}
            {section !== "movements" && activeSession.can_approve && activeSession.control.is_current && activeSession.control.approval_status === "pending" && (
              <button
                onClick={() => setModalType("approve_diff")}
                className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-800 hover:bg-amber-100 transition"
                data-testid="approve-diff-btn"
              >
                Autorizar Diferencia
              </button>
            )}
            {section !== "movements" && <button
              onClick={() => setModalType("close_session")}
              className="rounded-xl bg-slate-900 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition"
              disabled={(!activeSession.can_count && !activeSession.can_approve) || !activeSession.control.is_current || !["approved", "not_required"].includes(activeSession.control.approval_status || "")}
              data-testid="close-session-btn"
            >
              Cerrar Caja
            </button>}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Saldo de Apertura</p>
          <p className="mt-1 text-lg font-bold text-slate-900 tabular-nums">
            {formatMoney(activeSession.initial_cash, currency)}
          </p>
        </div>
        <div>
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Saldo Esperado (Teórico)</p>
          <p className="mt-1 text-lg font-bold text-teal-700 tabular-nums" data-testid="expected-cash-val">
            {formatMoney(activeSession.expected_cash, currency)}
          </p>
        </div>
        <div>
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Conteo Ciego Real</p>
          <p className="mt-1 text-lg font-bold text-slate-800 tabular-nums">
            {formatMoney(activeSession.actual_cash, currency)}
          </p>
        </div>
        <div>
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Diferencia de Caja</p>
          <p
            className={`mt-1 text-lg font-bold tabular-nums ${activeSession.difference_cash === null || Number(activeSession.difference_cash) === 0
              ? "text-slate-600"
              : Number(activeSession.difference_cash) > 0
                ? "text-blue-700"
                : "text-rose-700"
              }`}
            data-testid="difference-cash-val"
          >
            {formatMoney(activeSession.difference_cash ?? 0, currency)}
          </p>
        </div>
      </div>

      {section !== "movements" && <div className="rounded-xl border border-slate-200 p-3 text-xs space-y-2">
        <p>Arqueo: {activeSession.control.version ? `Versión ${activeSession.control.version} · ${activeSession.control.is_current ? "vigente" : "requiere nuevo conteo por movimientos posteriores"}` : "Pendiente de conteo"}</p>
        <p>Revisión: {({ pending: "Pendiente de autorización", approved: "Diferencia aprobada", rejected: "Rechazado, repita el conteo", not_required: "Conteo conforme" } as Record<string, string>)[activeSession.control.approval_status || ""] || "Sin arqueo"}</p>
        {Object.entries(activeSession.control.denominations || {}).map(([value, quantity]) => <span key={value} className="inline-block mr-3">{value} {currency}: {quantity} unidades</span>)}
        {Object.entries(activeSession.control.non_cash_totals || {}).map(([medium, amount]) => <p key={medium}>{medium}: {amount} (referencia sin aumentar efectivo)</p>)}
        {activeSession.control.approval_history?.map((decision, index) => <p key={index}>{decision.reviewed_at.slice(0, 19).replace("T", " ")} · {decision.approved ? "Aprobado" : "Rechazado"}: {decision.notes}</p>)}
        {Boolean(activeSession.control.history?.length) && <details><summary>Conteos anteriores</summary>{activeSession.control.history?.map(count => <p key={count.version}>Versión {count.version}: {count.counted_cash} {currency} · {count.counted_at.slice(0, 19).replace("T", " ")} · {count.approval_status}</p>)}</details>}
      </div>
      }
      {activeSession.notes && (
        <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600 border border-slate-100">
          <span className="font-semibold text-slate-700">Notas / Justificación:</span> {activeSession.notes}
        </div>
      )}
    </div>

    {section === "movements" && <div className="pagination-group">
      <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 mb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
          Movimientos de la Sesión
        </h3>
      </div>
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Fecha y Hora</th>
              <th className="px-4 py-3">Tipo</th>
              <th className="px-4 py-3">Motivo / Concepto</th>
              <th className="px-4 py-3 text-right">Importe</th>
              <th className="px-4 py-3 text-right">Saldo Posterior</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {activeSession.movements.map(m => (
              <tr key={m.movement_id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-mono text-[11px] text-slate-600">
                  {m.timestamp.slice(0, 19).replace("T", " ")}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block rounded-md px-2 py-0.5 text-[10px] font-bold ${m.movement_type === "DEPOSIT"
                      ? "bg-teal-100 text-teal-800"
                      : "bg-rose-100 text-rose-800"
                      }`}
                  >
                    {m.movement_type === "DEPOSIT" ? "INGRESO" : "EGRESO"}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-800 font-medium">{m.reason}</td>
                <td className={`px-4 py-3 text-right tabular-nums font-semibold ${m.movement_type === "DEPOSIT" ? "text-teal-700" : "text-rose-700"}`}>
                  {m.movement_type === "DEPOSIT" ? `+${formatMoney(m.amount, currency)}` : `-${formatMoney(m.amount, currency)}`}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {formatMoney(m.balance_after, currency)}
                </td>
              </tr>
            ))}
            {activeSession.movements.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-400">
                  Sin movimientos registrados en este turno de caja.
                </td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </div>}
  </div>);
}
