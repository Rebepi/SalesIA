import { LocationLifecycleButton } from "../../components/LocationLifecycleButton";
import type { useCompanySettingsWorkspaceTab } from "../../hooks/useCompanySettingsWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Check, Loader2, Plus, Store, Warehouse as WarehouseIcon, X } from "lucide-react";
import { CompanySettingsWorkspaceTabProps } from "../../types/CompanySettingsWorkspaceTab";
import { TIMEZONE_OPTIONS } from "../../support/CompanySettingsWorkspaceTab";

export function SeccionSedes({ setShowNewBranchModal, canWrite, setShowNewWarehouseModal, branches, showNewBranchModal, handleCreateBranch, newBranchCode, setNewBranchCode, inputClass, newBranchName, setNewBranchName, newBranchTimezone, setNewBranchTimezone, savingBranch, showNewWarehouseModal, handleCreateWarehouse, newWarehouseBranchId, setNewWarehouseBranchId, newWarehouseCode, setNewWarehouseCode, newWarehouseName, setNewWarehouseName, savingWarehouse, warehousesByBranch, reloadLocations }: { setShowNewBranchModal: ReturnType<typeof useCompanySettingsWorkspaceTab>["setShowNewBranchModal"]; setShowNewWarehouseModal: ReturnType<typeof useCompanySettingsWorkspaceTab>["setShowNewWarehouseModal"]; branches: ReturnType<typeof useCompanySettingsWorkspaceTab>["branches"]; showNewBranchModal: ReturnType<typeof useCompanySettingsWorkspaceTab>["showNewBranchModal"]; handleCreateBranch: ReturnType<typeof useCompanySettingsWorkspaceTab>["handleCreateBranch"]; newBranchCode: ReturnType<typeof useCompanySettingsWorkspaceTab>["newBranchCode"]; setNewBranchCode: ReturnType<typeof useCompanySettingsWorkspaceTab>["setNewBranchCode"]; inputClass: ReturnType<typeof useCompanySettingsWorkspaceTab>["inputClass"]; newBranchName: ReturnType<typeof useCompanySettingsWorkspaceTab>["newBranchName"]; setNewBranchName: ReturnType<typeof useCompanySettingsWorkspaceTab>["setNewBranchName"]; newBranchTimezone: ReturnType<typeof useCompanySettingsWorkspaceTab>["newBranchTimezone"]; setNewBranchTimezone: ReturnType<typeof useCompanySettingsWorkspaceTab>["setNewBranchTimezone"]; savingBranch: ReturnType<typeof useCompanySettingsWorkspaceTab>["savingBranch"]; showNewWarehouseModal: ReturnType<typeof useCompanySettingsWorkspaceTab>["showNewWarehouseModal"]; handleCreateWarehouse: ReturnType<typeof useCompanySettingsWorkspaceTab>["handleCreateWarehouse"]; newWarehouseBranchId: ReturnType<typeof useCompanySettingsWorkspaceTab>["newWarehouseBranchId"]; setNewWarehouseBranchId: ReturnType<typeof useCompanySettingsWorkspaceTab>["setNewWarehouseBranchId"]; newWarehouseCode: ReturnType<typeof useCompanySettingsWorkspaceTab>["newWarehouseCode"]; setNewWarehouseCode: ReturnType<typeof useCompanySettingsWorkspaceTab>["setNewWarehouseCode"]; newWarehouseName: ReturnType<typeof useCompanySettingsWorkspaceTab>["newWarehouseName"]; setNewWarehouseName: ReturnType<typeof useCompanySettingsWorkspaceTab>["setNewWarehouseName"]; savingWarehouse: ReturnType<typeof useCompanySettingsWorkspaceTab>["savingWarehouse"]; warehousesByBranch: ReturnType<typeof useCompanySettingsWorkspaceTab>["warehousesByBranch"]; reloadLocations: ReturnType<typeof useCompanySettingsWorkspaceTab>["reloadLocations"] } & { canWrite: NonNullable<CompanySettingsWorkspaceTabProps["canWrite"]> }) {
  return (<div className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <h2 className="font-bold text-slate-900">Estructura Organizacional: Sedes y Almacenes</h2>
        <p className="text-xs text-slate-500">Crea sucursales físicas y vincula sus respectivos almacenes de stock.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setShowNewBranchModal(true)}
          disabled={!canWrite}
          className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3.5 py-2 text-xs font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
        >
          <Plus className="h-4 w-4" />
          Nueva Sucursal
        </button>
        <button
          type="button"
          onClick={() => setShowNewWarehouseModal(true)}
          disabled={!canWrite || branches.length === 0}
          className="inline-flex items-center gap-1.5 rounded-xl border border-teal-700 bg-teal-50 px-3.5 py-2 text-xs font-semibold text-teal-800 hover:bg-teal-100 disabled:opacity-50"
        >
          <Plus className="h-4 w-4" />
          Nuevo Almacén
        </button>
      </div>
    </div>

    {showNewBranchModal && (
      <form onSubmit={handleCreateBranch} className="rounded-2xl border-2 border-teal-300 bg-teal-50/30 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Store className="h-4 w-4 text-teal-700" />
            Registrar Nueva Sucursal
          </h3>
          <button type="button" onClick={() => setShowNewBranchModal(false)} className="text-slate-400 hover:text-slate-600">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-xs font-semibold text-slate-700">
            Código de Sede
            <input
              required
              maxLength={32}
              value={newBranchCode}
              onChange={e => setNewBranchCode(e.target.value)}
              placeholder="SUC-02"
              className={inputClass}
            />
          </label>
          <label className="text-xs font-semibold text-slate-700">
            Nombre de la Sede
            <input
              required
              maxLength={255}
              value={newBranchName}
              onChange={e => setNewBranchName(e.target.value)}
              placeholder="Sede Arequipa Centro"
              className={inputClass}
            />
          </label>
          <label className="text-xs font-semibold text-slate-700">
            Zona Horaria
            <CustomSelect
              value={newBranchTimezone}
              onChange={e => setNewBranchTimezone(e.target.value)}
              className={inputClass}
            >
              {TIMEZONE_OPTIONS.map(tz => (
                <option key={tz.value} value={tz.value}>{tz.label}</option>
              ))}
            </CustomSelect>
          </label>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={() => setShowNewBranchModal(false)}
            className="rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={savingBranch}
            className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
          >
            {savingBranch ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
            Guardar Sucursal
          </button>
        </div>
      </form>
    )}

    {showNewWarehouseModal && (
      <form onSubmit={handleCreateWarehouse} className="rounded-2xl border-2 border-teal-300 bg-teal-50/30 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <WarehouseIcon className="h-4 w-4 text-teal-700" />
            Registrar Nuevo Almacén
          </h3>
          <button type="button" onClick={() => setShowNewWarehouseModal(false)} className="text-slate-400 hover:text-slate-600">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-xs font-semibold text-slate-700">
            Sucursal Perteneciente
            <CustomSelect remote={{ resource: "branches" }}
              required
              value={newWarehouseBranchId}
              onChange={e => setNewWarehouseBranchId(e.target.value)}
              className={inputClass}
            >
              {branches.map(b => (
                <option key={b.branch_id} value={b.branch_id}>
                  {b.name} ({b.code})
                </option>
              ))}
            </CustomSelect>
          </label>
          <label className="text-xs font-semibold text-slate-700">
            Código de Almacén
            <input
              required
              maxLength={32}
              value={newWarehouseCode}
              onChange={e => setNewWarehouseCode(e.target.value)}
              placeholder="ALM-02"
              className={inputClass}
            />
          </label>
          <label className="text-xs font-semibold text-slate-700">
            Nombre del Almacén
            <input
              required
              maxLength={255}
              value={newWarehouseName}
              onChange={e => setNewWarehouseName(e.target.value)}
              placeholder="Almacén de Tránsito"
              className={inputClass}
            />
          </label>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={() => setShowNewWarehouseModal(false)}
            className="rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={savingWarehouse}
            className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
          >
            {savingWarehouse ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
            Guardar Almacén
          </button>
        </div>
      </form>
    )}

    <div className="grid gap-4">
      {branches.map(branch => {
        const bWarehouses = warehousesByBranch.get(branch.branch_id) || [];
        return (
          <article key={branch.branch_id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-3">
                <Store className="h-5 w-5 text-teal-700" />
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-slate-900">{branch.name}</h3>
                    <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs font-bold text-slate-700">
                      {branch.code}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">Zona horaria: {branch.timezone}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${branch.is_active ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-slate-100 text-slate-600 border border-slate-200"
                  }`}>
                  {branch.is_active ? "Activa" : "Inactiva"}
                </span>
                {canWrite && (
                  <LocationLifecycleButton kind="branch" identifier={branch.branch_id} isActive={branch.is_active} onChanged={reloadLocations} />
                )}
              </div>
            </div>

            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                <WarehouseIcon className="h-3.5 w-3.5 text-slate-400" />
                Almacenes asociados ({bWarehouses.length})
              </h4>
              {bWarehouses.length > 0 ? (
                <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                  {bWarehouses.map(wh => (
                    <div key={wh.warehouse_id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                      <div>
                        <p className="font-semibold text-slate-800">{wh.name}</p>
                        <p className="font-mono text-[11px] text-slate-500">Código: {wh.code}</p>
                      </div>
                      <div className="flex items-center gap-2"><span className={`h-2 w-2 rounded-full ${wh.is_active ? "bg-emerald-500" : "bg-slate-400"}`} title={wh.is_active ? "Activo" : "Inactivo"} />{canWrite && <LocationLifecycleButton kind="warehouse" identifier={wh.warehouse_id} isActive={wh.is_active} onChanged={reloadLocations} />}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No hay almacenes registrados en esta sucursal.</p>
              )}
            </div>
          </article>
        );
      })}

      {branches.length === 0 && (
        <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 bg-white">
          No hay sucursales registradas. Haz clic en "Nueva Sucursal" para comenzar.
        </div>
      )}
    </div>
  </div>);
}
