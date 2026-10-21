import { useState } from "react";
import { CustomerDetailEditor } from "./CustomerDetailEditor";
import { Mail, Phone, Plus, Trash2 } from "lucide-react";
import type { useFichaCliente } from "../hooks/useFichaCliente";
import type { FichaClienteProps } from "../types/clientes";
import { btnPrimary, btnSecondary, inputStyle } from "./estilos";
export function ContactosCliente({ model, canWrite, customerId }: FichaClienteProps & { model: ReturnType<typeof useFichaCliente> }) {
  const { contacts, handleAddContact, handleDeleteContact } = model;
  const [editing, setEditing] = useState<Record<string, unknown> | null>(null);
  return (<div className="space-y-6">
    {editing && <CustomerDetailEditor customerId={customerId} kind="contact" row={editing} close={() => setEditing(null)} onSaved={() => { void model.loadData(); }} />}
    <div className="space-y-3">
      {contacts.map(c => (
        <div key={String(c.id)} className="flex items-center justify-between rounded-xl border border-slate-200 p-3.5">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-900">{String(c.name)}</span>
              {c.is_active === false && <span className="text-xs text-slate-400">Archivado</span>}
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{String(c.role)}</span>
              {c.is_primary && <span className="rounded bg-teal-100 px-2 py-0.5 text-xs font-medium text-teal-800">Principal</span>}
            </div>
            <div className="flex flex-wrap gap-4 text-xs text-slate-500">
              {c.email && <span className="flex items-center gap-1"><Mail className="h-3 w-3" />{String(c.email)}</span>}
              {c.phone && <span className="flex items-center gap-1"><Phone className="h-3 w-3" />{String(c.phone)}</span>}
            </div>
          </div>
          {canWrite && (
            <div className="flex gap-2"><button type="button" className={btnSecondary} onClick={() => setEditing(c)}>Editar</button>
            <button type="button" onClick={() => void handleDeleteContact(String(c.id))} className={btnSecondary} aria-label="Eliminar contacto">
              <Trash2 className="h-3.5 w-3.5 text-red-600" />
            </button></div>
          )}
        </div>
      ))}
      {contacts.length === 0 && <p className="text-center text-xs text-slate-400">No hay contactos registrados.</p>}
    </div>

    {canWrite && (
      <form onSubmit={handleAddContact} className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-3">
        <h3 className="font-semibold text-slate-800 text-xs uppercase tracking-wider">Añadir nuevo contacto</h3>
        <div className="grid gap-2 sm:grid-cols-2">
          <input name="name" required placeholder="Nombre completo" className={inputStyle} />
          <input name="role" required defaultValue="Compras" placeholder="Cargo / Rol" className={inputStyle} />
          <input name="email" type="email" placeholder="Correo" className={inputStyle} />
          <input name="phone" placeholder="Teléfono" className={inputStyle} />
        </div>
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input type="checkbox" name="is_primary" className="rounded text-teal-700" />
          Marcar como contacto principal
        </label>
        <button type="submit" className={btnPrimary}><Plus className="h-4 w-4" />Guardar contacto</button>
      </form>
    )}
  </div>);
}
