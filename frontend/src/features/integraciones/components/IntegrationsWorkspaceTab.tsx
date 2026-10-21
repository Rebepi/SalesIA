import { Panel1 } from "../sections/IntegrationsWorkspaceTab/Panel1";
export type { IntegrationConnector } from "../types/IntegrationsWorkspaceTab";
export type { IntegrationsWorkspaceTabProps } from "../types/IntegrationsWorkspaceTab";
import { useIntegrationsWorkspaceTab } from "../hooks/useIntegrationsWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { Plus, X } from "lucide-react";
import { IntegrationsWorkspaceTabProps } from "../types/IntegrationsWorkspaceTab";

export function IntegrationsWorkspaceTab({ canWrite = true }: IntegrationsWorkspaceTabProps) {
  const { connectors, loading, loadError, testingId, showCreate, setShowCreate, provider, setProvider, category, setCategory, mode, setMode, credential, setCredential, editingCredentialId, setEditingCredentialId, saving, handleCreate, handleRotateCredential, handleToggleMode, handleTestConnection } = useIntegrationsWorkspaceTab({ canWrite });
  return (
    <div id="scr-047-integrations-workspace" data-testid="scr-047-integrations-workspace" className="space-y-6">
      <NavbarSectionHeader view="integrations" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">CONEXIONES</span>
            <h1 className="text-xl font-bold text-slate-900">Integraciones y Conectores Externos</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Tarjetas por proveedor, credenciales cifradas y enmascaradas, modo de prueba y validación local de configuración.
          </p>
        </div>
        {canWrite && <button type="button" onClick={() => { setShowCreate(true); setEditingCredentialId(null); setCredential(""); }} className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-teal-800"><Plus className="h-4 w-4" />Configurar conector</button>}
      </NavbarSectionHeader>

      {showCreate && <form onSubmit={handleCreate} className="rounded-2xl border border-teal-200 bg-teal-50/40 p-5 shadow-sm"><div className="flex items-center justify-between"><div><h2 className="font-bold text-slate-900">Nueva integración</h2><p className="text-xs text-slate-500">La credencial se cifra antes de persistirse y no vuelve a mostrarse.</p></div><button type="button" onClick={() => setShowCreate(false)} className="rounded-lg p-2 text-slate-500 hover:bg-white"><X className="h-4 w-4" /></button></div><div className="mt-4 grid gap-3 md:grid-cols-4"><input required minLength={2} maxLength={64} value={provider} onChange={(event) => setProvider(event.target.value)} placeholder="Proveedor" className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" /><input required minLength={2} maxLength={64} value={category} onChange={(event) => setCategory(event.target.value)} placeholder="Categoría" className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" /><CustomSelect value={mode} onChange={(event) => setMode(event.target.value as "test" | "live")} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"><option value="test">Prueba</option><option value="live">Producción</option></CustomSelect><input required type="password" minLength={8} maxLength={4096} value={credential} onChange={(event) => setCredential(event.target.value)} autoComplete="new-password" placeholder="Credencial o token" className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" /></div><div className="mt-4 flex justify-end"><button type="submit" disabled={saving} className="rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Guardando…" : "Guardar integración"}</button></div></form>}

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">Cargando integraciones configuradas...</div>}
      {loadError && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{loadError}</div>}
      {!loading && !loadError && connectors.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">No hay conectores configurados para esta empresa.</div>}

      <Panel1 connectors={connectors} testingId={testingId} handleToggleMode={handleToggleMode} canWrite={canWrite} setEditingCredentialId={setEditingCredentialId} setCredential={setCredential} setShowCreate={setShowCreate} handleTestConnection={handleTestConnection} editingCredentialId={editingCredentialId} handleRotateCredential={handleRotateCredential} credential={credential} saving={saving} />
    </div>
  );
}
