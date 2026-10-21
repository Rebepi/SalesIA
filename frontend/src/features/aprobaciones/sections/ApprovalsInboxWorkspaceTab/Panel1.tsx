import type { useApprovalsInboxWorkspaceTab } from "../../hooks/useApprovalsInboxWorkspaceTab";
import { ApprovalsInboxWorkspaceTabProps } from "../../types/ApprovalsInboxWorkspaceTab";

export function Panel1({ approvals, canWrite, saving, setRejectionModalItem, handleApprove }: { approvals: ReturnType<typeof useApprovalsInboxWorkspaceTab>["approvals"]; saving: ReturnType<typeof useApprovalsInboxWorkspaceTab>["saving"]; setRejectionModalItem: ReturnType<typeof useApprovalsInboxWorkspaceTab>["setRejectionModalItem"]; handleApprove: ReturnType<typeof useApprovalsInboxWorkspaceTab>["handleApprove"] } & { canWrite: NonNullable<ApprovalsInboxWorkspaceTabProps["canWrite"]> }) {
  return (<div className="space-y-4">
    {approvals.map((item) => (
      <div
        key={item.id}
        className={`rounded-2xl border p-5 transition ${item.status === "approved"
          ? "border-emerald-200 bg-emerald-50/20"
          : item.status === "rejected"
            ? "border-slate-200 bg-slate-50 opacity-60"
            : "border-slate-200 bg-white shadow-sm"
          }`}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-teal-700">{item.code}</span>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${item.risk_level === "HIGH"
                ? "bg-rose-100 text-rose-800"
                : "bg-amber-100 text-amber-800"
                }`}>
                Riesgo: {item.risk_level}
              </span>
              <span className="text-xs text-slate-400">
                Versión doc: v{item.document_version}
              </span>
            </div>
            <h3 className="mt-1 text-base font-bold text-slate-900">{item.operation_type}</h3>
            <p className="mt-1 text-xs text-slate-500">Etapa {(item.stage_index || 0) + 1} de {item.stage_count || 1}: {item.stage_name || "Revisión"}{item.due_at ? ` · plazo ${new Date(item.due_at).toLocaleString("es-PE", { timeZone: "America/Lima" })}` : ""}</p>
            {item.document_changed && <p className="mt-1 text-xs text-rose-700">El contenido del documento cambió y requiere una nueva revisión.</p>}
            <p className="mt-0.5 text-xs text-slate-600 font-medium">{item.impact_summary}</p>
          </div>

          <div>
            <span className={`rounded-full px-3 py-1 text-xs font-bold ${item.status === "approved"
              ? "bg-emerald-100 text-emerald-800"
              : item.status === "rejected"
                ? "bg-rose-100 text-rose-800"
                : "bg-teal-50 text-teal-800 border border-teal-200"
              }`}>
              {item.status === "approved" ? "Aprobada" : item.status === "rejected" ? "Rechazada" : item.status === "stale" ? "Revisión vencida por cambios" : "Pendiente de Resolución"}
            </span>
          </div>
        </div>

        <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3.5 text-xs">
          <span className="font-semibold text-slate-700">Evidencia y Justificación:</span>
          <p className="mt-1 text-slate-600 leading-relaxed">{item.evidence}</p>
          <div className="mt-2 flex items-center gap-4 text-[11px] text-slate-400">
            <span>Solicitante: <strong className="text-slate-600">{item.requester_name}</strong> ({item.requester_email})</span>
            <span>Fecha: {new Date(item.created_at).toLocaleString("es-PE")}</span>
          </div>
        </div>

        {item.status === "pending" && canWrite && (
          <div className="mt-4 flex items-center justify-end gap-2 border-t border-slate-100 pt-3">
            <button
              disabled={saving}
              onClick={() => setRejectionModalItem(item)}
              className="rounded-xl border border-slate-200 bg-white px-4 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-50"
            >
              Rechazar con Motivo
            </button>
            <button
              disabled={saving}
              onClick={() => handleApprove(item)}
              className="rounded-xl bg-teal-700 px-5 py-1.5 text-xs font-semibold text-white hover:bg-teal-800 shadow-sm"
            >
              Aprobar Solicitud
            </button>
          </div>
        )}
      </div>
    ))}
  </div>);
}
