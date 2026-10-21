import type { useFichaCliente } from "../hooks/useFichaCliente";
import type { FichaClienteProps } from "../types/clientes";
import { btnPrimary } from "./estilos";
export function CondicionesComercialesCliente({ model }: FichaClienteProps & { model: ReturnType<typeof useFichaCliente> }) {
  const { terms, creditTestAmount, setCreditTestAmount, creditTestResult, handleTestCredit } = model;
  return (<div className="space-y-6">
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-xl border border-slate-100 p-4">
        <span className="text-xs text-slate-400">Límite de crédito autorizado</span>
        <p className="text-xl font-bold text-slate-900">{String(terms?.credit_limit ?? "0.00")} {String(terms?.preferred_currency ?? "USD")}</p>
      </div>
      <div className="rounded-xl border border-slate-100 p-4">
        <span className="text-xs text-slate-400">Plazo de pago comercial</span>
        <p className="text-xl font-bold text-slate-900">{String(terms?.payment_terms_days ?? 30)} días</p>
      </div>
      <div className="rounded-xl border border-slate-100 p-4">
        <span className="text-xs text-slate-400">Estado de crédito</span>
        <p className="text-sm font-semibold">{terms?.is_credit_blocked ? "Bloqueado" : "Habilitado"}</p>
        {terms?.is_credit_blocked && <p className="text-xs text-red-600 mt-1">{String(terms?.credit_block_reason ?? "")}</p>}
      </div>
      <div className="rounded-xl border border-slate-100 p-4">
        <span className="text-xs text-slate-400">Lista de precios asociada</span>
        <p className="text-sm font-semibold">{String(terms?.price_list_id ?? "Predeterminada general")}</p>
      </div>
    </div>

    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">Comprobador dinámico de crédito</h3>
      <div className="flex items-center gap-3">
        <input
          type="number"
          value={creditTestAmount}
          onChange={e => setCreditTestAmount(e.target.value)}
          placeholder="Importe a evaluar"
          className="w-48 rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
        />
        <button type="button" onClick={() => void handleTestCredit()} className={btnPrimary}>Simular crédito</button>
      </div>
      {creditTestResult && (
        <div className={`rounded-lg p-3 text-xs ${creditTestResult.allowed ? "bg-teal-50 text-teal-800" : "bg-amber-50 text-amber-800"}`}>
          <p className="font-semibold">{creditTestResult.allowed ? "Aprobado" : "Requiere aprobación"}: {creditTestResult.reason}</p>
          <p className="mt-1 text-slate-600">Crédito disponible resultante: {creditTestResult.available_credit}</p>
        </div>
      )}
    </div>
  </div>);
}
