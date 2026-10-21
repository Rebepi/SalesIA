import type { useSalesTeamTab } from "../../hooks/useSalesTeamTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X } from "lucide-react";
import { inputStyle } from "../../support/SalesTeamTab";
import { btnPrimary } from "../../support/SalesTeamTab";
import { btnSecondary } from "../../support/SalesTeamTab";

export function SeccionReasignarCartera({ portfolioModal, setPortfolioModal, executeReassign, reps, busy }: { portfolioModal: NonNullable<ReturnType<typeof useSalesTeamTab>["portfolioModal"]>; setPortfolioModal: ReturnType<typeof useSalesTeamTab>["setPortfolioModal"]; executeReassign: ReturnType<typeof useSalesTeamTab>["executeReassign"]; reps: ReturnType<typeof useSalesTeamTab>["reps"]; busy: ReturnType<typeof useSalesTeamTab>["busy"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
    <div className="app-modal-panel w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <h3 className="text-lg font-semibold text-slate-900">
          Reasignar cartera: {portfolioModal.rep.full_name}
        </h3>
        <button type="button" onClick={() => setPortfolioModal(null)} className={btnSecondary}><X className="h-4 w-4" /></button>
      </div>
      <div className="mt-4 space-y-3 rounded-xl bg-slate-50 p-4 text-xs text-slate-700">
        <p className="font-semibold text-slate-900">Registros abiertos detectados:</p>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-lg bg-white p-2 shadow-sm">
            <div className="text-lg font-bold text-teal-700">{String(portfolioModal.preview?.customers_count ?? 0)}</div>
            <div className="text-slate-500">Clientes</div>
          </div>
          <div className="rounded-lg bg-white p-2 shadow-sm">
            <div className="text-lg font-bold text-teal-700">{String(portfolioModal.preview?.opportunities_count ?? 0)}</div>
            <div className="text-slate-500">Oportunidades</div>
          </div>
          <div className="rounded-lg bg-white p-2 shadow-sm">
            <div className="text-lg font-bold text-teal-700">{String(portfolioModal.preview?.activities_count ?? 0)}</div>
            <div className="text-slate-500">Actividades</div>
          </div>
        </div>
      </div>
      <form onSubmit={executeReassign} className="mt-4 space-y-4">
        <label className="text-xs font-medium text-slate-700">
          Vendedor de destino:
          <CustomSelect remote={{ resource: "sales_reps", exclude_id: portfolioModal.rep.rep_id, active_only: true }} name="target_rep_id" required className={inputStyle}>
            <option value="">Seleccione vendedor activo</option>
            {reps.filter(r => r.rep_id !== portfolioModal.rep.rep_id && r.is_active).map(r => (
              <option key={r.rep_id} value={r.rep_id}>{r.full_name} ({r.code})</option>
            ))}
          </CustomSelect>
        </label>
        <label className="text-xs font-medium text-slate-700">
          Motivo del traspaso:
          <input name="reason" defaultValue="Reestructuración territorial planificada" required className={inputStyle} />
        </label>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={() => setPortfolioModal(null)} className={btnSecondary}>Cancelar</button>
          <button type="submit" disabled={busy} className={btnPrimary}>{busy ? "Traspasando…" : "Confirmar reasignación"}</button>
        </div>
      </form>
    </div>
  </div>);
}
