import "./receivable-action-menu.css";
import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { CreditCard as ActionCreditCard } from "lucide-react";
import { useState } from "react";
import type { useAccountsReceivableTab } from "../../hooks/useAccountsReceivableTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { RotateCcw, MoreHorizontal, FileText, Activity } from "lucide-react";
import { AccountsReceivableTabProps } from "../../types/AccountsReceivableTab";

export function Panel2({ filteredItems, setAction, canWrite, openReconciliation, loading }: { filteredItems: ReturnType<typeof useAccountsReceivableTab>["filteredItems"]; setAction: ReturnType<typeof useAccountsReceivableTab>["setAction"]; openReconciliation: ReturnType<typeof useAccountsReceivableTab>["openReconciliation"]; loading: ReturnType<typeof useAccountsReceivableTab>["loading"] } & { canWrite: NonNullable<AccountsReceivableTabProps["canWrite"]> }) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  return (<div className="pagination-shell">
    <div className="pagination-shell">
      <PaginatedTable className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Comprobante</th>
            <th className="px-4 py-3">Emisión</th>
            <th className="px-4 py-3">Vencimiento</th>
            <th className="px-4 py-3 text-right">Total Facturado</th>
            <th className="px-4 py-3 text-right">Cobrado</th>
            <th className="px-4 py-3 text-right">Saldo Pendiente</th>
            <th className="px-4 py-3 text-center">Antigüedad</th>
            <th className="px-4 py-3 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {filteredItems.map(item => {
            const menuOpen = openMenuId === item.sale_id;
            return (
              <tr key={item.sale_id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-semibold text-slate-900">
                  <span className="font-mono">{item.series_number}{item.has_installments && <span className="block text-[10px] font-normal text-slate-500">Con cronograma de cuotas</span>}{item.schedule_needs_review && <span className="block text-[10px] font-normal text-amber-800">Cronograma pendiente de revisión</span>}</span><span className="block text-xs font-normal text-slate-500">{item.customer_name || "Cliente registrado"}</span>
                </td>
                <td className="px-4 py-3 text-slate-500">{item.created_at.slice(0, 10)}</td>
                <td className="px-4 py-3 font-medium text-slate-700">{item.due_date.slice(0, 10)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-600">{new Intl.NumberFormat("es-PE", { style: "currency", currency: item.currency || "PEN" }).format(Number(item.total_amount))}</td>
                <td className="px-4 py-3 text-right tabular-nums text-teal-700">{new Intl.NumberFormat("es-PE", { style: "currency", currency: item.currency || "PEN" }).format(Number(item.paid_amount))}</td>
                <td className="px-4 py-3 text-right tabular-nums font-bold text-slate-900">{new Intl.NumberFormat("es-PE", { style: "currency", currency: item.currency || "PEN" }).format(Number(item.balance_due))}{item.selected_bucket_balance !== null && Number(item.selected_bucket_balance) !== Number(item.balance_due) && <span className="mt-1 block text-[10px] font-normal text-slate-500">En este tramo: {item.currency} {Number(item.selected_bucket_balance).toFixed(2)}</span>}</td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-bold ${item.aging_bucket === "0-30"
                      ? "bg-teal-100 text-teal-800"
                      : item.aging_bucket === "31-60"
                        ? "bg-amber-100 text-amber-800"
                        : item.aging_bucket === "61-90"
                          ? "bg-orange-100 text-orange-800"
                          : "bg-rose-100 text-rose-800"
                      }`}
                  >
                    {item.aging_bucket === "not_due" ? "Por vencer" : `${item.aging_bucket} días de mora`}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    {canWrite && (
                      <IconAction label="Cobrar" tone="primary" onClick={() => setAction({ saleId: item.sale_id, mode: "payment" })}><ActionCreditCard aria-hidden="true" /></IconAction>
                    )}
                    <div className="relative">
                      <IconAction label="Más opciones" tone="neutral" onClick={() => setOpenMenuId(menuOpen ? null : item.sale_id)}><MoreHorizontal className="h-4 w-4" /></IconAction>
                      {menuOpen && (
                        <div
                          onMouseLeave={() => setOpenMenuId(null)}
                          className="receivable-action-menu absolute right-0 top-8 z-40 w-48 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-slate-800 dark:bg-slate-900 text-left"
                        >
                          <button
                            type="button"
                            onClick={() => { setAction({ saleId: item.sale_id, mode: "context" }); setOpenMenuId(null); }}
                            className="receivable-menu-detail flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs"
                          >
                            <span className="receivable-menu-icon" aria-hidden="true"><FileText className="h-3.5 w-3.5" /></span>
                            <span>Detalle</span>
                          </button>
                          {canWrite && (
                            <button
                              type="button"
                              onClick={() => { setAction({ saleId: item.sale_id, mode: "activity" }); setOpenMenuId(null); }}
                              className="receivable-menu-collection flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs"
                            >
                              <span className="receivable-menu-icon" aria-hidden="true"><Activity className="h-3.5 w-3.5" /></span>
                              <span>Gestionar cobranza</span>
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => { openReconciliation(item); setOpenMenuId(null); }}
                            data-testid={`reconcile-btn-${item.sale_id}`}
                            className="receivable-menu-reconcile flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs"
                          >
                            <span className="receivable-menu-icon" aria-hidden="true"><RotateCcw className="h-3.5 w-3.5" /></span>
                            <span>Reconciliar</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </td>
              </tr>
            );
          })}
          {filteredItems.length === 0 && !loading && (
            <tr>
              <td colSpan={8} className="p-8 text-center text-slate-400">
                No hay saldos pendientes en el tramo de vencimiento seleccionado.
              </td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </div>);
}
