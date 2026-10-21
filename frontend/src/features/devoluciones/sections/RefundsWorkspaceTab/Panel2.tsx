import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { Settings2, ArrowLeftRight } from "lucide-react";
import type { useRefundsWorkspaceTab } from "../../hooks/useRefundsWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { HelpCircle } from "lucide-react";
import { RefundsWorkspaceTabProps } from "../../types/RefundsWorkspaceTab";

export function Panel2({ onOpenSettlement, filteredRefunds, isUncertain, canWrite, setActiveRefund, setModalType, loading }: { onOpenSettlement?: (returnId: string) => void; filteredRefunds: ReturnType<typeof useRefundsWorkspaceTab>["filteredRefunds"]; isUncertain: ReturnType<typeof useRefundsWorkspaceTab>["isUncertain"]; setActiveRefund: ReturnType<typeof useRefundsWorkspaceTab>["setActiveRefund"]; setModalType: ReturnType<typeof useRefundsWorkspaceTab>["setModalType"]; loading: ReturnType<typeof useRefundsWorkspaceTab>["loading"] } & { canWrite: NonNullable<RefundsWorkspaceTabProps["canWrite"]> }) {
  return (<div className="pagination-shell">
    <div className="pagination-shell">
      <PaginatedTable className="w-full text-left text-xs table-fixed min-w-[1000px]">
        <colgroup><col style={{ width: "12%" }} /><col style={{ width: "12%" }} /><col style={{ width: "24%" }} /><col style={{ width: "13%" }} /><col style={{ width: "16%" }} /><col style={{ width: "13%" }} /><col style={{ width: "10%" }} /></colgroup>
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">ID Reembolso</th>
            <th className="px-4 py-3">Pago Origen</th>
            <th className="px-4 py-3">Motivo</th>
            <th className="px-4 py-3 text-right">Importe</th>
            <th className="px-4 py-3">Estado</th>
            <th className="px-4 py-3">Referencia Proveedor</th>
            <th className="px-4 py-3 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {filteredRefunds.map(r => (
            <tr key={r.id} className="hover:bg-slate-50/60">
              <td className="px-4 py-3 font-mono font-semibold text-slate-900">
                {r.id.slice(0, 8)}…
              </td>
              <td className="px-4 py-3 font-mono text-slate-600">
                {r.payment_id.slice(0, 8)}…
              </td>
              <td className="px-4 py-3 text-slate-700 max-w-xs truncate" title={r.reason}>
                {r.reason}
              </td>
              <td className="px-4 py-3 text-right tabular-nums font-bold text-slate-900">
                {r.currency} {Number(r.amount).toFixed(2)}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col items-start gap-1">
                  <span
                    className={`inline-block rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${r.status === "confirmado" || r.status === "confirmed"
                      ? "bg-teal-100 text-teal-800"
                      : r.status === "fallido" || r.status === "failed"
                        ? "bg-rose-100 text-rose-800"
                        : isUncertain(r.status)
                          ? "bg-amber-100 text-amber-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    data-testid={`refund-status-${r.id}`}
                  >
                    {r.status}
                  </span>
                  {isUncertain(r.status) && (
                    <span
                      className="inline-flex items-center gap-1 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-700 border border-amber-200"
                      data-testid="provider-uncertainty-badge"
                    >
                      <HelpCircle className="h-3 w-3" /> Incertidumbre de pasarela
                    </span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                {r.provider_reference || "—"}
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex justify-end gap-2">
                  {r.return_id && onOpenSettlement && <IconAction label="Ver liquidación vinculada" tone="primary" onClick={() => onOpenSettlement(r.return_id!)}><ArrowLeftRight aria-hidden="true" /></IconAction>}
                  {canWrite && <IconAction label="Gestionar reembolso" tone="primary" onClick={() => { setActiveRefund(r); setModalType("update_status"); }} data-testid={`manage-refund-${r.id}`}><Settings2 aria-hidden="true" /></IconAction>}
                </div>
              </td>
            </tr>
          ))}
          {filteredRefunds.length === 0 && !loading && (
            <tr>
              <td colSpan={7} className="p-8 text-center text-slate-400">
                No se encontraron reembolsos en el estado seleccionado.
              </td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </div>);
}
