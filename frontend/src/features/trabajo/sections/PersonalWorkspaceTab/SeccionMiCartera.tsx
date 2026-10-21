import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { AlertCircle, ExternalLink, Lock, Users } from "lucide-react";
import { PersonalWorkspaceTabProps } from "../../types/PersonalWorkspaceTab";
import { formatMoney } from "../../support/PersonalWorkspaceTab";

export function SeccionMiCartera({ customersSectionRef, customers, isSupervisorOrAdmin, setCustomersScope, customersScope, onNavigate, canReadCustomers, customersError, loadCustomers, currentUserId, customersLoading, onOpenCustomer, setSelectedCustomerModal, baseCurrency }: { customersSectionRef: ReturnType<typeof usePersonalWorkspaceTab>["customersSectionRef"]; customers: ReturnType<typeof usePersonalWorkspaceTab>["customers"]; isSupervisorOrAdmin: ReturnType<typeof usePersonalWorkspaceTab>["isSupervisorOrAdmin"]; setCustomersScope: ReturnType<typeof usePersonalWorkspaceTab>["setCustomersScope"]; customersScope: ReturnType<typeof usePersonalWorkspaceTab>["customersScope"]; canReadCustomers: ReturnType<typeof usePersonalWorkspaceTab>["canReadCustomers"]; customersError: ReturnType<typeof usePersonalWorkspaceTab>["customersError"]; loadCustomers: ReturnType<typeof usePersonalWorkspaceTab>["loadCustomers"]; currentUserId: ReturnType<typeof usePersonalWorkspaceTab>["currentUserId"]; customersLoading: ReturnType<typeof usePersonalWorkspaceTab>["customersLoading"]; setSelectedCustomerModal: ReturnType<typeof usePersonalWorkspaceTab>["setSelectedCustomerModal"] } & { onNavigate: PersonalWorkspaceTabProps["onNavigate"]; onOpenCustomer: PersonalWorkspaceTabProps["onOpenCustomer"]; baseCurrency: NonNullable<PersonalWorkspaceTabProps["baseCurrency"]> }) {
  return (<section
    ref={customersSectionRef}
    id="section-customers"
    className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm space-y-4 flex flex-col justify-between"
  >
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          <h3 className="font-bold text-slate-900 dark:text-slate-100">Mi Cartera</h3>
          <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-semibold tabular-nums text-slate-600 dark:text-slate-400">
            {customers.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isSupervisorOrAdmin && (
            <div className="flex items-center gap-1 rounded-xl bg-slate-100 dark:bg-slate-800 p-1 text-xs">
              <button
                type="button"
                onClick={() => setCustomersScope("mine")}
                className={`rounded-lg px-2 py-0.5 font-semibold transition ${customersScope === "mine" ? "bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-sm" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                  }`}
              >
                Míos
              </button>
              <button
                type="button"
                onClick={() => setCustomersScope("all")}
                className={`rounded-lg px-2 py-0.5 font-semibold transition ${customersScope === "all" ? "bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-sm" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                  }`}
              >
                Todos
              </button>
            </div>
          )}
          {onNavigate && (
            <button
              type="button"
              onClick={() => onNavigate("customers")}
              className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 dark:text-teal-400 hover:text-teal-900 dark:hover:text-teal-300"
            >
              Ver todos <ExternalLink className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {!canReadCustomers ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Lock className="h-8 w-8 text-slate-400 mb-2" />
          <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Módulo de cartera restringido</p>
          <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
            No cuentas con el permiso <code className="font-mono">customers:read</code> para ver clientes.
          </p>
        </div>
      ) : customersError ? (
        <div className="flex items-center justify-between rounded-xl bg-rose-50 dark:bg-rose-950/40 p-3 text-xs text-rose-800 dark:text-rose-300">
          <span className="flex items-center gap-2 font-medium">
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" /> {customersError}
          </span>
          <button
            type="button"
            onClick={() => loadCustomers(currentUserId, customersScope)}
            className="font-bold underline hover:text-rose-900 dark:hover:text-rose-100"
          >
            Reintentar
          </button>
        </div>
      ) : customersLoading ? (
        <div className="space-y-2 py-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-14 w-full animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
          ))}
        </div>
      ) : customers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Users className="h-8 w-8 text-slate-300 dark:text-slate-700 stroke-1 mb-2" />
          <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Sin clientes asignados</p>
          <p className="text-[11px] text-slate-400 mt-1">
            {customersScope === "mine" ? "No tienes cuentas de clientes asociadas a tu perfil." : "No se encontraron clientes registrados en la empresa."}
          </p>
        </div>
      ) : (
        <ul className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
          {customers.map(c => {
            const isRestrictedBalance = c.current_balance === null || c.current_balance === undefined;

            return (
              <li
                key={c.id}
                onClick={() => {
                  if (onOpenCustomer) onOpenCustomer(c.id);
                  else setSelectedCustomerModal(c);
                }}
                className="cursor-pointer rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3.5 shadow-sm transition hover:border-teal-400 dark:hover:border-teal-600 hover:shadow-md flex items-center justify-between"
              >
                <div className="min-w-0 pr-3">
                  <p className="font-bold text-xs text-slate-900 dark:text-slate-100 truncate">{c.legal_name}</p>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">{c.doc_number || c.code}</p>
                </div>

                <div className="text-right shrink-0">
                  {isRestrictedBalance ? (
                    <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-500 dark:text-slate-400">
                      <Lock className="h-3 w-3 text-slate-400" /> Saldo restringido
                    </span>
                  ) : (
                    <div>
                      <span className="block text-[10px] text-slate-400">Saldo pendiente</span>
                      <span className="text-xs font-bold tabular-nums text-slate-800 dark:text-slate-200">
                        {formatMoney(c.current_balance, baseCurrency)}
                      </span>
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>

    <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
      Clientes asignados a tu cartera comercial para seguimiento continuo de crédito y ventas.
    </p>
  </section>);
}
