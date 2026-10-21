import type { useSalesTeamTab } from "../../hooks/useSalesTeamTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X } from "lucide-react";
import { inputStyle } from "../../support/SalesTeamTab";
import { btnPrimary } from "../../support/SalesTeamTab";
import { btnSecondary } from "../../support/SalesTeamTab";

export function Seccionundefined({ repModal, setRepModal, saveRep, branches, busy }: { repModal: NonNullable<ReturnType<typeof useSalesTeamTab>["repModal"]>; setRepModal: ReturnType<typeof useSalesTeamTab>["setRepModal"]; saveRep: ReturnType<typeof useSalesTeamTab>["saveRep"]; branches: ReturnType<typeof useSalesTeamTab>["branches"]; busy: ReturnType<typeof useSalesTeamTab>["busy"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
    <div className="app-modal-panel w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <h3 className="text-lg font-semibold text-slate-900">
          {repModal === "new" ? "Registrar nuevo vendedor" : `Ficha de ${repModal.full_name}`}
        </h3>
        <button type="button" onClick={() => setRepModal(null)} className={btnSecondary}><X className="h-4 w-4" /></button>
      </div>
      <form onSubmit={saveRep} className="mt-4 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <label className="text-xs font-medium text-slate-700">
            Código:
            <input name="code" defaultValue={repModal === "new" ? "" : repModal.code} required className={inputStyle} />
          </label>
          <label className="text-xs font-medium text-slate-700">
            Nombre completo:
            <input name="full_name" defaultValue={repModal === "new" ? "" : repModal.full_name} required className={inputStyle} />
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-xs font-medium text-slate-700">
            Equipo:
            <input name="team" defaultValue={repModal === "new" ? "" : repModal.team || ""} placeholder="ej. Norte" className={inputStyle} />
          </label>
          <label className="text-xs font-medium text-slate-700">
            Territorio:
            <input name="territory" defaultValue={repModal === "new" ? "Principal" : repModal.territory} required className={inputStyle} />
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-xs font-medium text-slate-700">
            Sucursal:
            <CustomSelect remote={{ resource: "branches" }} searchable name="branch_id" defaultValue={repModal === "new" ? "" : repModal.branch_id || ""} className={inputStyle}>
              <option value="">Seleccionar sede</option>
              {branches.map(b => <option key={String(b.branch_id || b.id)} value={String(b.branch_id || b.id)}>{String(b.name)}</option>)}
            </CustomSelect>
          </label>
          <label className="text-xs font-medium text-slate-700">
            Cuota mensual base ($):
            <input name="monthly_quota" type="number" step="any" defaultValue={repModal === "new" ? "0" : repModal.monthly_quota || "0"} className={inputStyle} />
          </label>
        </div>
        <label className="text-xs font-medium text-slate-700">
          Estado operativo:
          <CustomSelect name="is_active" defaultValue={repModal === "new" || repModal.is_active ? "true" : "false"} className={inputStyle}>
            <option value="true">Activo (habilitado para ventas)</option>
            <option value="false">Inactivo (preserva atribución histórica)</option>
          </CustomSelect>
        </label>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={() => setRepModal(null)} className={btnSecondary}>Cancelar</button>
          <button type="submit" disabled={busy} className={btnPrimary}>{busy ? "Guardando…" : "Guardar ficha"}</button>
        </div>
      </form>
    </div>
  </div>);
}
