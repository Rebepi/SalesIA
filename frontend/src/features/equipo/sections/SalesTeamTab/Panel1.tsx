import type { useSalesTeamTab } from "../../hooks/useSalesTeamTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Plus, RefreshCw, Search } from "lucide-react";
import { btnPrimary } from "../../support/SalesTeamTab";
import { btnSecondary } from "../../support/SalesTeamTab";

export function Panel1({ period, setPeriod, setScopeFilter, scopeFilter, teams, selectedTeam, setSelectedTeam, searchTerm, setSearchTerm, loadData, loading, setRepModal }: { period: ReturnType<typeof useSalesTeamTab>["period"]; setPeriod: ReturnType<typeof useSalesTeamTab>["setPeriod"]; setScopeFilter: ReturnType<typeof useSalesTeamTab>["setScopeFilter"]; scopeFilter: ReturnType<typeof useSalesTeamTab>["scopeFilter"]; teams: ReturnType<typeof useSalesTeamTab>["teams"]; selectedTeam: ReturnType<typeof useSalesTeamTab>["selectedTeam"]; setSelectedTeam: ReturnType<typeof useSalesTeamTab>["setSelectedTeam"]; searchTerm: ReturnType<typeof useSalesTeamTab>["searchTerm"]; setSearchTerm: ReturnType<typeof useSalesTeamTab>["setSearchTerm"]; loadData: ReturnType<typeof useSalesTeamTab>["loadData"]; loading: ReturnType<typeof useSalesTeamTab>["loading"]; setRepModal: ReturnType<typeof useSalesTeamTab>["setRepModal"] }) {
  return (<div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="flex flex-wrap items-center gap-3">
      <label className="flex items-center gap-2 text-xs font-medium text-slate-500">
        <span>Periodo:</span>
        <input
          type="month"
          value={period}
          onChange={e => setPeriod(e.target.value)}
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs text-slate-800 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100"
        />
      </label>
      <div className="flex items-center rounded-xl border border-slate-200 bg-slate-50 p-1 text-xs">
        <button
          type="button"
          onClick={() => setScopeFilter("team")}
          className={`rounded-lg px-3 py-1 font-medium transition ${scopeFilter === "team" ? "bg-white text-teal-700 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
        >
          Equipo comercial
        </button>
        <button
          type="button"
          onClick={() => setScopeFilter("personal")}
          className={`rounded-lg px-3 py-1 font-medium transition ${scopeFilter === "personal" ? "bg-white text-teal-700 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
        >
          Visibilidad personal
        </button>
      </div>
      {teams.length > 0 && (
        <label className="flex items-center gap-2 text-xs font-medium text-slate-500">
          <span>Equipo:</span>
          <CustomSelect remote={{ resource: "teams" }} searchable
            value={selectedTeam}
            onChange={e => setSelectedTeam(e.target.value)}
            className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs text-slate-800 outline-none focus:border-teal-600"
          >
            <option value="">Todos los equipos</option>
            {teams.map(t => <option key={t} value={t}>{t}</option>)}
          </CustomSelect>
        </label>
      )}
    </div>
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <input
          type="text"
          placeholder="Buscar vendedor…"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="rounded-lg border border-slate-300 py-1.5 pl-9 pr-3 text-xs outline-none focus:ring-2 focus:ring-teal-100"
        />
      </div>
      <button type="button" onClick={loadData} disabled={loading} className={btnSecondary} aria-label="Actualizar">
        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
      </button>
      <button type="button" onClick={() => setRepModal("new")} className={btnPrimary}>
        <Plus className="h-4 w-4" /> Nuevo vendedor
      </button>
    </div>
  </div>);
}
