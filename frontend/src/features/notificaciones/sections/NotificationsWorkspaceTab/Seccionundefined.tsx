import type { useNotificationsWorkspaceTab } from "../../hooks/useNotificationsWorkspaceTab";
import { Check, ExternalLink } from "lucide-react";

export function Seccionundefined({ filtered, handleOpenResource, handleToggleRead, loading }: { filtered: ReturnType<typeof useNotificationsWorkspaceTab>["filtered"]; handleOpenResource: ReturnType<typeof useNotificationsWorkspaceTab>["handleOpenResource"]; handleToggleRead: ReturnType<typeof useNotificationsWorkspaceTab>["handleToggleRead"]; loading: ReturnType<typeof useNotificationsWorkspaceTab>["loading"] }) {
  return (<div className="space-y-3">
    {filtered.length > 0 ? (
      filtered.map((item) => (
        <article
          key={item.id}
          className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border p-4 transition ${item.read
            ? "border-slate-200 bg-white opacity-85"
            : "border-teal-200 bg-teal-50/20 shadow-sm"
            }`}
        >
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded-md px-2 py-0.5 text-[10px] font-bold ${item.priority === "CRITICAL"
                ? "bg-rose-100 text-rose-800"
                : item.priority === "HIGH"
                  ? "bg-amber-100 text-amber-800"
                  : "bg-slate-100 text-slate-700"
                }`}>
                {item.priority}
              </span>
              <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
                {item.category}
              </span>
              <span className="text-[11px] text-slate-400">
                {new Date(item.created_at).toLocaleDateString("es-PE")} {new Date(item.created_at).toLocaleTimeString("es-PE")}
              </span>
            </div>
            <h3 className={`text-sm ${item.read ? "font-semibold text-slate-800" : "font-bold text-slate-900"}`}>
              {item.title}
            </h3>
            <p className="text-xs text-slate-600">{item.message}</p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {item.resource_type && (
              <button
                onClick={() => handleOpenResource(item)}
                className="inline-flex items-center gap-1 rounded-xl bg-white border border-slate-200 px-3 py-1.5 text-xs font-semibold text-teal-700 hover:bg-slate-50"
              >
                <span>Abrir recurso</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </button>
            )}
            <button
              onClick={() => handleToggleRead(item)}
              aria-label={item.read ? "Marcar como no leída" : "Marcar como leída"}
              title={item.read ? "Marcar como no leída" : "Marcar como leída"}
              className="rounded-xl border border-slate-200 bg-white p-2 text-slate-500 hover:bg-slate-50"
            >
              <Check className={`h-4 w-4 ${item.read ? "text-slate-400" : "text-teal-700 font-bold"}`} />
            </button>
          </div>
        </article>
      ))
    ) : (
      <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
        {loading ? "Estamos cargando tus avisos…" : "No hay notificaciones en la vista seleccionada."}
      </div>
    )}
  </div>);
}
