import { useState } from "react";
import { CustomerDetailEditor } from "./CustomerDetailEditor";
import { Plus, Trash2 } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import type { useFichaCliente } from "../hooks/useFichaCliente";
import type { FichaClienteProps } from "../types/clientes";
import { btnPrimary, btnSecondary, inputStyle } from "./estilos";
export function DireccionesCliente({ model, canWrite, customerId }: FichaClienteProps & { model: ReturnType<typeof useFichaCliente> }) {
  const { addresses, handleAddAddress, handleDeleteAddress } = model;
  const [editing, setEditing] = useState<Record<string, unknown> | null>(null);
  return (<div className="space-y-6">
    {editing && <CustomerDetailEditor customerId={customerId} kind="address" row={editing} close={() => setEditing(null)} onSaved={() => { void model.loadData(); }} />}
    <div className="space-y-3">
      {addresses.map(a => (
        <div key={String(a.id)} className="flex items-center justify-between rounded-xl border border-slate-200 p-3.5">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-900 capitalize">{String(a.address_type)}</span>
              {a.is_active === false && <span className="text-xs text-slate-400">Archivado</span>}
              {a.is_primary && <span className="rounded bg-teal-100 px-2 py-0.5 text-xs font-medium text-teal-800">Principal</span>}
            </div>
            <p className="text-xs text-slate-600 mt-1">{String(a.street)}, {String(a.city)} ({String(a.country)})</p>
          </div>
          {canWrite && (
            <div className="flex gap-2"><button type="button" className={btnSecondary} onClick={() => setEditing(a)}>Editar</button>
            <button type="button" onClick={() => void handleDeleteAddress(String(a.id))} className={btnSecondary} aria-label="Eliminar dirección">
              <Trash2 className="h-3.5 w-3.5 text-red-600" />
            </button></div>
          )}
        </div>
      ))}
      {addresses.length === 0 && <p className="text-center text-xs text-slate-400">No hay direcciones registradas.</p>}
    </div>

    {canWrite && (
      <form onSubmit={handleAddAddress} className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-3">
        <h3 className="font-semibold text-slate-800 text-xs uppercase tracking-wider">Añadir nueva dirección</h3>
        <div className="grid gap-2 sm:grid-cols-3">
          <CustomSelect name="address_type" className={inputStyle}>
            <option value="comercial">Comercial</option>
            <option value="fiscal">Fiscal</option>
            <option value="entrega">Entrega</option>
          </CustomSelect>
          <input name="street" required placeholder="Dirección / Calle / Nro" className={`${inputStyle} sm:col-span-2`} />
          <input name="city" required defaultValue="Lima" placeholder="Ciudad" className={inputStyle} />
          <input name="country" required defaultValue="PE" placeholder="País" className={inputStyle} />
          <input name="postal_code" placeholder="Código postal" className={inputStyle} />
        </div>
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input type="checkbox" name="is_primary" className="rounded text-teal-700" />
          Marcar como dirección principal de este tipo
        </label>
        <button type="submit" className={btnPrimary}><Plus className="h-4 w-4" />Guardar dirección</button>
      </form>
    )}
  </div>);
}
