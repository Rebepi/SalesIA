import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { AlertCircle, ChevronLeft, ChevronRight, Lock, Target, Users } from "lucide-react";
import { PersonalWorkspaceTabProps } from "../../types/PersonalWorkspaceTab";
import { formatMoney } from "../../support/PersonalWorkspaceTab";
import { formatPeriodLabel } from "../../support/PersonalWorkspaceTab";

export function SeccionMetaPersonal({ quotaSectionRef, shiftPeriod, resetCurrentPeriod, selectedPeriod, canReadSales, salesError, loadSalesQuota, currentUserId, branchId, salesLoading, salesProgress, baseCurrency, progressBadge, attainmentNum, progressColor }: { quotaSectionRef: ReturnType<typeof usePersonalWorkspaceTab>["quotaSectionRef"]; shiftPeriod: ReturnType<typeof usePersonalWorkspaceTab>["shiftPeriod"]; resetCurrentPeriod: ReturnType<typeof usePersonalWorkspaceTab>["resetCurrentPeriod"]; selectedPeriod: ReturnType<typeof usePersonalWorkspaceTab>["selectedPeriod"]; canReadSales: ReturnType<typeof usePersonalWorkspaceTab>["canReadSales"]; salesError: ReturnType<typeof usePersonalWorkspaceTab>["salesError"]; loadSalesQuota: ReturnType<typeof usePersonalWorkspaceTab>["loadSalesQuota"]; currentUserId: ReturnType<typeof usePersonalWorkspaceTab>["currentUserId"]; salesLoading: ReturnType<typeof usePersonalWorkspaceTab>["salesLoading"]; salesProgress: ReturnType<typeof usePersonalWorkspaceTab>["salesProgress"]; progressBadge: ReturnType<typeof usePersonalWorkspaceTab>["progressBadge"]; attainmentNum: ReturnType<typeof usePersonalWorkspaceTab>["attainmentNum"]; progressColor: ReturnType<typeof usePersonalWorkspaceTab>["progressColor"] } & { branchId: PersonalWorkspaceTabProps["branchId"]; baseCurrency: NonNullable<PersonalWorkspaceTabProps["baseCurrency"]> }) {
  return (<section
    ref={quotaSectionRef}
    id="section-quota"
    className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm space-y-4 flex flex-col justify-between"
  >
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          <h3 className="font-bold text-slate-900 dark:text-slate-100">Meta Personal</h3>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => shiftPeriod(-1)}
            title="Mes anterior"
            className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={resetCurrentPeriod}
            title="Ir al mes actual"
            className="rounded-lg px-2 py-1 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            {formatPeriodLabel(selectedPeriod)}
          </button>
          <button
            type="button"
            onClick={() => shiftPeriod(1)}
            title="Mes siguiente"
            className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {!canReadSales ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Lock className="h-8 w-8 text-slate-400 mb-2" />
          <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Módulo de ventas restringido</p>
          <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
            Tu perfil de usuario no cuenta con permisos de lectura comercial (<code className="font-mono">sales:read</code>).
          </p>
        </div>
      ) : salesError ? (
        <div className="flex items-center justify-between rounded-xl bg-rose-50 dark:bg-rose-950/40 p-3 text-xs text-rose-800 dark:text-rose-300">
          <span className="flex items-center gap-2 font-medium">
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" /> {salesError}
          </span>
          <button
            type="button"
            onClick={() => loadSalesQuota(currentUserId, selectedPeriod, branchId)}
            className="font-bold underline hover:text-rose-900 dark:hover:text-rose-100"
          >
            Reintentar
          </button>
        </div>
      ) : salesLoading ? (
        <div className="space-y-3 py-6">
          <div className="h-8 w-2/3 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
          <div className="h-3 w-full animate-pulse rounded-full bg-slate-100 dark:bg-slate-800" />
          <div className="h-16 w-full animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
        </div>
      ) : !salesProgress?.isRepresentative ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Users className="h-8 w-8 text-slate-300 dark:text-slate-700 stroke-1 mb-2" />
          <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Usuario no registrado como representante de ventas</p>
          <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
            Para tener una cuota personal asignada, tu cuenta debe estar vinculada a un perfil de representante comercial en la sede.
          </p>
        </div>
      ) : !salesProgress?.hasQuota ? (
        <div className="flex flex-col items-center justify-center py-8 text-center space-y-2">
          <Target className="h-8 w-8 text-amber-500 mb-1" />
          <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">Sin cuota configurada para este período</p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 max-w-xs">
            Ventas netas registradas en {formatPeriodLabel(selectedPeriod)}:
          </p>
          <p className="text-xl font-bold tabular-nums text-slate-900 dark:text-slate-100">
            {formatMoney(salesProgress.netSales, baseCurrency)}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Ventas Netas del Mes
              </span>
              <p className="text-3xl font-extrabold tabular-nums tracking-tight text-slate-900 dark:text-slate-100">
                {formatMoney(salesProgress.netSales, baseCurrency)}
              </p>
            </div>
            <div className="text-right">
              <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold ${progressBadge}`}>
                {attainmentNum !== null ? `${attainmentNum}% alcanzado` : "0%"}
              </span>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Meta: {formatMoney(salesProgress.quota, baseCurrency)}
              </p>
            </div>
          </div>

          <div className="space-y-1">
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
                style={{ width: `${Math.min(100, Math.max(0, attainmentNum || 0))}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 p-3 text-center">
            <div>
              <span className="block text-[10px] font-semibold text-slate-500 dark:text-slate-400">Ventas Brutas</span>
              <span className="text-xs font-bold tabular-nums text-slate-800 dark:text-slate-200">
                {formatMoney(salesProgress.grossSales, baseCurrency)}
              </span>
            </div>
            <div>
              <span className="block text-[10px] font-semibold text-slate-500 dark:text-slate-400">Devoluciones</span>
              <span className="text-xs font-bold tabular-nums text-rose-600 dark:text-rose-400">
                {formatMoney(salesProgress.refunds, baseCurrency)}
              </span>
            </div>
            <div>
              <span className="block text-[10px] font-semibold text-slate-500 dark:text-slate-400">
                {salesProgress.gap >= 0 ? "Superávit" : "Brecha"}
              </span>
              <span className={`text-xs font-bold tabular-nums ${salesProgress.gap >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"}`}>
                {formatMoney(Math.abs(salesProgress.gap), baseCurrency)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>

    <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
      Cálculo correspondiente a las ventas confirmadas en la sucursal activa según zona horaria local.
    </p>
  </section>);
}
