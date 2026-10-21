import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { useState } from "react";
import type { useSalesTeamTab } from "../../hooks/useSalesTeamTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { DollarSign, Target, MoreHorizontal, User, Briefcase } from "lucide-react";
import { btnSecondary } from "../../support/SalesTeamTab";

export function Panel2({ serverPagination, period, filteredReps, loading, setRepModal, setTargetModal, openPortfolio, openCommissions }: { serverPagination?: ReturnType<typeof useSalesTeamTab>["serverPagination"]; period: ReturnType<typeof useSalesTeamTab>["period"]; filteredReps: ReturnType<typeof useSalesTeamTab>["filteredReps"]; loading: ReturnType<typeof useSalesTeamTab>["loading"]; setRepModal: ReturnType<typeof useSalesTeamTab>["setRepModal"]; setTargetModal: ReturnType<typeof useSalesTeamTab>["setTargetModal"]; openPortfolio: ReturnType<typeof useSalesTeamTab>["openPortfolio"]; openCommissions: ReturnType<typeof useSalesTeamTab>["openCommissions"] }) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  void btnSecondary;
  return (<div className="pagination-shell">
    <div className="pagination-shell">
      <PaginatedTable serverPagination={serverPagination} className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
          <tr>
            <th className="px-5 py-3.5">Vendedor</th>
            <th className="px-5 py-3.5">Equipo / Sede</th>
            <th className="px-5 py-3.5 text-right">Ventas ({period})</th>
            <th className="px-5 py-3.5 text-right">Ticket prom.</th>
            <th className="px-5 py-3.5 text-right">Devoluciones</th>
            <th className="px-5 py-3.5 text-right">Meta mensual</th>
            <th className="px-5 py-3.5 text-center">Cumplimiento</th>
            <th className="px-5 py-3.5 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {filteredReps.length === 0 ? (
            <tr>
              <td colSpan={8} className="p-8 text-center text-sm text-slate-500">
                {loading ? "Cargando representantes…" : "No se encontraron vendedores para el criterio seleccionado."}
              </td>
            </tr>
          ) : (
            filteredReps.map(rep => {
              const attainmentNum = rep.quota_attainment_pct ? Number(rep.quota_attainment_pct) : null;
              return (
                <tr key={rep.rep_id} className="transition hover:bg-slate-50/70">
                  <td className="px-5 py-4">
                    <div className="font-semibold text-slate-900">{rep.full_name}</div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span className="font-mono">{rep.code}</span>
                      {!rep.is_active && <span className="rounded bg-rose-50 px-1.5 py-0.5 text-[10px] font-medium text-rose-700">Inactivo</span>}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-600">
                    <div>{rep.team || "Sin equipo"}</div>
                    <div className="text-slate-400">{rep.territory}</div>
                  </td>
                  <td className="px-5 py-4 text-right font-medium tabular-nums text-slate-900">
                    ${Number(rep.total_sales || rep.current_sales || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    <div className="text-[11px] text-slate-400">{rep.sales_count} oper. / {rep.active_days} d. activos</div>
                  </td>
                  <td className="px-5 py-4 text-right tabular-nums text-slate-600">
                    ${Number(rep.average_ticket || rep.ticket_average || 0).toFixed(2)}
                  </td>
                  <td className="px-5 py-4 text-right tabular-nums text-rose-600">
                    {Number(rep.returns_amount) > 0 ? `-$${Number(rep.returns_amount).toFixed(2)}` : "—"}
                  </td>
                  <td className="px-5 py-4 text-right tabular-nums text-slate-700">
                    {rep.target_quota ? `$${Number(rep.target_quota).toFixed(2)}` : <span className="text-xs text-slate-400">Sin meta</span>}
                  </td>
                  <td className="px-5 py-4 text-center">
                    {attainmentNum !== null ? (
                      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${attainmentNum >= 100 ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" : attainmentNum >= 80 ? "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300" : "bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300"}`}>
                        {attainmentNum.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="inline-block rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] text-slate-500">
                        No configurada
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <IconAction label="Liquidación y comisiones" className="!border-teal-200 !bg-teal-50 !text-teal-700 enabled:hover:!bg-teal-100 dark:!border-teal-700/60 dark:!bg-teal-500/15 dark:!text-teal-300 dark:enabled:hover:!bg-teal-500/25" onClick={() => openCommissions(rep)}><DollarSign aria-hidden="true" /></IconAction>
                      <div className="relative">
                        <IconAction label="Más opciones" className="!border-slate-200 !bg-slate-50 !text-slate-700 enabled:hover:!bg-slate-100 dark:!border-slate-700/60 dark:!bg-slate-500/15 dark:!text-slate-300 dark:enabled:hover:!bg-slate-500/25" aria-expanded={openMenuId === rep.rep_id} aria-haspopup="true" onClick={() => setOpenMenuId(openMenuId === rep.rep_id ? null : rep.rep_id)}><MoreHorizontal aria-hidden="true" /></IconAction>
                        {openMenuId === rep.rep_id && (
                          <div
                            onMouseLeave={() => setOpenMenuId(null)}
                            className="absolute right-0 top-8 z-40 w-44 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-slate-800 dark:bg-slate-900 text-left"
                          >
                            <button
                              type="button"
                              onClick={() => {
                                setRepModal(rep);
                                setOpenMenuId(null);
                              }}
                              className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                            >
                              <User className="h-3.5 w-3.5" />
                              <span>Ficha</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setTargetModal(rep);
                                setOpenMenuId(null);
                              }}
                              className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                            >
                              <Target className="h-3.5 w-3.5" />
                              <span>Metas</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                openPortfolio(rep);
                                setOpenMenuId(null);
                              }}
                              className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                            >
                              <Briefcase className="h-3.5 w-3.5" />
                              <span>Cartera</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </div>);
}
