import type { useIntegrationsWorkspaceTab } from "../../hooks/useIntegrationsWorkspaceTab";
import { KeyRound, RefreshCw, X } from "lucide-react";
import { IntegrationsWorkspaceTabProps } from "../../types/IntegrationsWorkspaceTab";

export function Panel1({ connectors, testingId, handleToggleMode, canWrite, setEditingCredentialId, setCredential, setShowCreate, handleTestConnection, editingCredentialId, handleRotateCredential, credential, saving }: { connectors: ReturnType<typeof useIntegrationsWorkspaceTab>["connectors"]; testingId: ReturnType<typeof useIntegrationsWorkspaceTab>["testingId"]; handleToggleMode: ReturnType<typeof useIntegrationsWorkspaceTab>["handleToggleMode"]; setEditingCredentialId: ReturnType<typeof useIntegrationsWorkspaceTab>["setEditingCredentialId"]; setCredential: ReturnType<typeof useIntegrationsWorkspaceTab>["setCredential"]; setShowCreate: ReturnType<typeof useIntegrationsWorkspaceTab>["setShowCreate"]; handleTestConnection: ReturnType<typeof useIntegrationsWorkspaceTab>["handleTestConnection"]; editingCredentialId: ReturnType<typeof useIntegrationsWorkspaceTab>["editingCredentialId"]; handleRotateCredential: ReturnType<typeof useIntegrationsWorkspaceTab>["handleRotateCredential"]; credential: ReturnType<typeof useIntegrationsWorkspaceTab>["credential"]; saving: ReturnType<typeof useIntegrationsWorkspaceTab>["saving"] } & { canWrite: NonNullable<IntegrationsWorkspaceTabProps["canWrite"]> }) {
  return (<div className="grid gap-6 sm:grid-cols-2">
    {connectors.map((c) => {
      const isTesting = testingId === c.id;

      return (
        <div
          key={c.id}
          className={`rounded-2xl border bg-white p-5 shadow-sm transition ${c.status === "connected"
            ? "border-slate-200"
            : c.status === "error"
              ? "border-rose-200 bg-rose-50/10"
              : "border-slate-200 opacity-70"
            }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{c.category}</span>
              <h3 className="text-base font-bold text-slate-900">{c.provider_name}</h3>
            </div>

            <div className="flex items-center gap-1.5">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${c.status === "connected"
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                : c.status === "error"
                  ? "bg-rose-50 text-rose-700 border border-rose-200"
                  : "bg-slate-100 text-slate-600"
                }`}>
                {c.status === "connected" ? "Conectado" : c.status === "error" ? "Con Errores" : "No Configurado"}
              </span>
            </div>
          </div>

          {c.error_message && (
            <div role="alert" className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
              {c.error_message}
            </div>
          )}

          <div className="mt-4 space-y-3 rounded-xl border border-slate-100 bg-slate-50 p-3.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Modo de Operación:</span>
              <button
                onClick={() => handleToggleMode(c)}
                disabled={!canWrite}
                className={`rounded-lg px-2.5 py-1 font-bold text-[11px] transition disabled:cursor-not-allowed disabled:opacity-50 ${c.mode === "live"
                  ? "bg-emerald-700 text-white"
                  : "bg-amber-100 text-amber-900 border border-amber-300"
                  }`}
              >
                {c.mode === "live" ? "Producción (Live)" : "Prueba (Sandbox)"}
              </button>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-500">Credencial API:</span>
              <span className="font-mono">{c.masked_key}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-500">Última Verificación:</span>
              <span className="text-slate-700 font-medium">
                {c.last_sync ? new Date(c.last_sync).toLocaleString("es-PE") : "Nunca"}
              </span>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between pt-2 border-t border-slate-100">
            <span className="text-[11px] text-slate-400">
              {c.latency_ms ? `Tiempo de validación: ${c.latency_ms} ms` : "Sin verificación reciente"}
            </span>

            <div className="flex gap-2">{canWrite && <button type="button" onClick={() => { setEditingCredentialId(c.id); setCredential(""); setShowCreate(false); }} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"><KeyRound className="h-3.5 w-3.5" />Rotar</button>}<button onClick={() => handleTestConnection(c)} disabled={isTesting || !canWrite} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-teal-700 hover:bg-slate-50 disabled:opacity-50"><RefreshCw className={`h-3.5 w-3.5 ${isTesting ? "animate-spin" : ""}`} />Probar Conexión en Vivo</button></div>
          </div>
          {editingCredentialId === c.id && <form onSubmit={(event) => handleRotateCredential(event, c.id)} className="mt-4 flex gap-2 rounded-xl border border-slate-200 bg-white p-3"><input required type="password" minLength={8} maxLength={4096} value={credential} onChange={(event) => setCredential(event.target.value)} autoComplete="new-password" placeholder="Nueva credencial" className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-xs" /><button type="submit" disabled={saving} className="rounded-lg bg-teal-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50">Actualizar</button><button type="button" onClick={() => { setEditingCredentialId(null); setCredential(""); }} className="rounded-lg border border-slate-300 p-2 text-slate-500"><X className="h-4 w-4" /></button></form>}
        </div>
      );
    })}
  </div>);
}
