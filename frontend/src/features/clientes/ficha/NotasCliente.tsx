import { Plus } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import type { useFichaCliente } from "../hooks/useFichaCliente";
import type { FichaClienteProps } from "../types/clientes";
import { btnPrimary, inputStyle } from "./estilos";
export function NotasCliente({ model, canWrite }: FichaClienteProps & { model: ReturnType<typeof useFichaCliente> }) {
  const { notes, handleAddNote } = model;
  return (<div className="space-y-6">
    <div className="space-y-3">
      {notes.map(n => (
        <div key={String(n.id)} className="rounded-xl border border-slate-200 p-4 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className={`rounded px-2 py-0.5 font-medium uppercase ${n.category === "interno" ? "bg-purple-100 text-purple-800" : n.category === "personal" ? "bg-amber-100 text-amber-800" : "bg-teal-100 text-teal-800"}`}>
              {String(n.category)}
            </span>
            <span className="text-slate-400">{String(n.author_email)} · {String(n.created_at).slice(0, 10)}</span>
          </div>
          <p className="text-xs text-slate-800 whitespace-pre-wrap">{String(n.content)}</p>
        </div>
      ))}
      {notes.length === 0 && <p className="text-center text-xs text-slate-400">No hay notas registradas.</p>}
    </div>

    {canWrite && (
      <form onSubmit={handleAddNote} className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">Agregar nota</h3>
        <CustomSelect name="category" className={inputStyle}>
          <option value="comercial">Comercial (visible al equipo)</option>
          <option value="personal">Dato personal sensible</option>
          <option value="interno">Comentario interno confidencial</option>
        </CustomSelect>
        <textarea name="content" required rows={3} placeholder="Escribe el contenido..." className={inputStyle} />
        <button type="submit" className={btnPrimary}><Plus className="h-4 w-4" />Registrar nota</button>
      </form>
    )}
  </div>);
}
