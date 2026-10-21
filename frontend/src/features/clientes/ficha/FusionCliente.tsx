import { CustomSelect } from "../../../ui/components/CustomSelect";
import type { useFichaCliente } from "../hooks/useFichaCliente";
import type { FichaClienteProps, Row } from "../types/clientes";
import { btnPrimary, inputStyle } from "./estilos";
export function FusionCliente({ model, customerId, allCustomers }: FichaClienteProps & { model: ReturnType<typeof useFichaCliente> }) {
  const { mergeTargetId, setMergeTargetId, mergePreview, setMergePreview, handlePreviewMerge, handleExecuteMerge } = model;
  return (<div className="space-y-6">
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900 leading-relaxed">
      <p className="font-semibold">Asistente de fusión segura de clientes</p>
      <p className="mt-1">
        Esta operación integrará las cotizaciones, ventas, pedidos, contactos y saldos pendientes del cliente duplicado dentro de este cliente maestro.
        El cliente duplicado quedará archivado y sus snapshots históricos se mantendrán inalterables.
      </p>
    </div>

    <div className="space-y-3">
      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700" htmlFor="duplicate-select">
        Seleccionar cliente a absorber (duplicado)
      </label>
      <CustomSelect remote={{ resource: "customers", exclude_id: customerId, active_only: true }}
        id="duplicate-select"
        value={mergeTargetId}
        onChange={e => { setMergeTargetId(e.target.value); setMergePreview(null); }}
        className={inputStyle}
      >
        <option value="">-- Seleccionar cliente duplicado --</option>
        {allCustomers.filter(c => c.id !== customerId && c.is_active !== false).map(c => (
          <option key={String(c.id)} value={String(c.id)}>
            {String(c.legal_name)} ({String(c.code)} - {String(c.doc_number)})
          </option>
        ))}
      </CustomSelect>
      <button type="button" disabled={!mergeTargetId} onClick={() => void handlePreviewMerge()} className={btnPrimary}>
        Previsualizar impacto de la fusión
      </button>
    </div>

    {mergePreview && (
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3 text-xs">
        <h4 className="font-semibold text-slate-800">Impacto detectado para la fusión:</h4>
        <ul className="grid grid-cols-2 gap-2 text-slate-600">
          <li>Ventas a transferir: <strong>{String((mergePreview.impact as unknown as Row)?.sales_count ?? 0)}</strong></li>
          <li>Cotizaciones: <strong>{String((mergePreview.impact as unknown as Row)?.quotations_count ?? 0)}</strong></li>
          <li>Pedidos: <strong>{String((mergePreview.impact as unknown as Row)?.orders_count ?? 0)}</strong></li>
          <li>Contactos: <strong>{String((mergePreview.impact as unknown as Row)?.contacts_count ?? 0)}</strong></li>
          <li>Saldo a integrar: <strong>{String((mergePreview.impact as unknown as Row)?.balance_transfer ?? "0.00")}</strong></li>
        </ul>
        <div className="pt-2">
          <button type="button" onClick={() => void handleExecuteMerge()} className="rounded-lg bg-red-700 px-4 py-2 font-semibold text-white transition hover:bg-red-800">
            Confirmar y ejecutar fusión irreversible
          </button>
        </div>
      </div>
    )}
  </div>);
}
