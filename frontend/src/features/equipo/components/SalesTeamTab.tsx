import "./team-submodules.css";
import { Panel1 } from "../sections/SalesTeamTab/Panel1";
import { CommissionCenter } from "./CommissionCenter";
import { Panel2 } from "../sections/SalesTeamTab/Panel2";
import { Seccionundefined } from "../sections/SalesTeamTab/Seccionundefined";
import { SeccionReasignarCartera } from "../sections/SalesTeamTab/SeccionReasignarCartera";
import { SeccionLiquidacion } from "../sections/SalesTeamTab/SeccionLiquidacion";
import { useSalesTeamTab } from "../hooks/useSalesTeamTab";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { RefreshCw, X } from "lucide-react";
import { inputStyle } from "../support/SalesTeamTab";
import { btnPrimary } from "../support/SalesTeamTab";
import { btnSecondary } from "../support/SalesTeamTab";

export type TeamSection = "team" | "targets" | "rules" | "assignments" | "settlements";

export function SalesTeamTab({ section = "team" }: { section?: TeamSection }) {
  const { serverPagination, reps, branches, loading, error, period, setPeriod, scopeFilter, setScopeFilter, selectedTeam, setSelectedTeam, searchTerm, setSearchTerm, repModal, setRepModal, targetModal, setTargetModal, portfolioModal, setPortfolioModal, commissionModal, setCommissionModal, busy, loadData, saveRep, saveTarget, openPortfolio, executeReassign, openCommissions, teams, filteredReps } = useSalesTeamTab({ filterByTeam: section === "team" });
  return (
    <div id="scr-013-sales-team" className={section === "team" ? "space-y-6" : "team-submodules space-y-5"}>
      {section === "team" ? <Panel1 period={period} setPeriod={setPeriod} setScopeFilter={setScopeFilter} scopeFilter={scopeFilter} teams={teams} selectedTeam={selectedTeam} setSelectedTeam={setSelectedTeam} searchTerm={searchTerm} setSearchTerm={setSearchTerm} loadData={loadData} loading={loading} setRepModal={setRepModal} /> : <div className="team-toolbar">
        <div className="flex flex-wrap items-center gap-3">{(section === "targets" || section === "settlements") && <label className="flex items-center gap-3 text-sm text-slate-500">Período<input type="month" required value={period} onChange={event => { if (event.target.value) setPeriod(event.target.value); }} className="team-input" /></label>}<span className="text-sm text-slate-500">{section === "targets" ? "Metas por vendedor, equipo y empresa" : section === "rules" ? "Configuración de comisiones" : section === "assignments" ? "Participación comercial" : "Liquidaciones por moneda"}</span></div>
        <button type="button" className="team-button" disabled={loading} onClick={loadData}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />Actualizar vendedores</button>
      </div>}

      {error && <div className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</div>}

      {section !== "team" && <CommissionCenter reps={reps} period={period} section={section} />}

      {section === "team" && <Panel2 serverPagination={serverPagination} period={period} filteredReps={filteredReps} loading={loading} setRepModal={setRepModal} setTargetModal={setTargetModal} openPortfolio={openPortfolio} openCommissions={openCommissions} />}

      {repModal && (
        <Seccionundefined repModal={repModal} setRepModal={setRepModal} saveRep={saveRep} branches={branches} busy={busy} />
      )}

      {targetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="text-lg font-semibold text-slate-900">
                Asignar meta: {targetModal.full_name}
              </h3>
              <button type="button" onClick={() => setTargetModal(null)} className={btnSecondary}><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={saveTarget} className="mt-4 space-y-4">
              <label className="text-xs font-medium text-slate-700">
                Periodo (YYYY-MM):
                <input name="period" defaultValue={period} required className={inputStyle} />
              </label>
              <label className="text-xs font-medium text-slate-700">
                Tipo de meta:
                <CustomSelect name="target_type" defaultValue="amount" className={inputStyle}>
                  <option value="amount">Monto de ventas facturadas</option>
                  <option value="margin">Margen sin impuestos</option>
                  <option value="units">Unidades vendidas</option>
                  <option value="clients">Clientes atendidos</option>
                </CustomSelect>
              </label>
              <label className="text-xs font-medium text-slate-700">Moneda de la cuota<input name="currency" required pattern="[A-Z]{3}" maxLength={3} defaultValue="USD" className={inputStyle} /></label>
              <label className="text-xs font-medium text-slate-700">
                Valor objetivo:
                <input name="target_value" type="number" step="any" defaultValue="5000" required className={inputStyle} />
              </label>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setTargetModal(null)} className={btnSecondary}>Cancelar</button>
                <button type="submit" disabled={busy} className={btnPrimary}>{busy ? "Guardando…" : "Asignar meta"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {portfolioModal && (
        <SeccionReasignarCartera portfolioModal={portfolioModal} setPortfolioModal={setPortfolioModal} executeReassign={executeReassign} reps={reps} busy={busy} />
      )}

      {commissionModal && commissionModal.settlement && (
        <SeccionLiquidacion settlement={commissionModal.settlement} setCommissionModal={setCommissionModal} />
      )}
    </div>
  );
}
