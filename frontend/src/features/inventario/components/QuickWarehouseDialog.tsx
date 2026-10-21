import { FormEvent, useState } from "react";
import { LoaderCircle, Warehouse, X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { notifyEntityChanged } from "../../../ui/entityEvents";
import { useUnsavedChanges } from "../../../ui/drafts";
import { useToast } from "../../../ui/toast/ToastContext";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { useConfirm } from "../../../ui/components/ConfirmDialog";

interface BranchChoice {
  branch_id: string;
  name: string;
  code?: string;
}

export interface WarehouseChoice extends Record<string, unknown> {
  warehouse_id: string;
  branch_id: string;
  name: string;
  code: string;
  is_active?: boolean;
}

export function QuickWarehouseDialog({ isOpen, branches, onClose, onCreated }: { isOpen: boolean; branches: BranchChoice[]; onClose: () => void; onCreated: (warehouse: WarehouseChoice) => void }) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  useUnsavedChanges(isOpen && dirty);
  if (!isOpen) return null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    try {
      const warehouse = await apiClient.request<WarehouseChoice>("/api/v1/warehouses", { method: "POST", body: JSON.stringify({ branch_id: String(data.get("branch_id")), code: String(data.get("code")).trim(), name: String(data.get("name")).trim() }) });
      notifyEntityChanged("warehouse", warehouse);
      setDirty(false);
      onCreated(warehouse);
      toast.success("Almacén creado", "El nuevo almacén ya está disponible en el flujo actual.");
    } catch (requestError: unknown) {
      toast.error("No se pudo crear el almacén", requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "Revisa los datos ingresados.");
    } finally { setBusy(false); }
  }

  async function close() {
    if (busy) return;
    if (dirty && !await confirm({ title: "¿Cerrar sin guardar?", text: "Hay datos del almacén sin guardar.", confirmLabel: "Cerrar", cancelLabel: "Quedarme" })) return;
    onClose();
  }

  return <ModalSurface labelledBy="quick-warehouse-title" blocked={busy} onClose={() => void close()}><div className="app-modal-panel w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl"><div className="flex items-center justify-between"><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-teal-50 text-teal-700"><Warehouse className="h-5 w-5" /></span><div><h3 id="quick-warehouse-title" className="font-bold">Crear almacén</h3><p className="text-xs text-slate-500">Se seleccionará al guardar</p></div></div><button type="button" onClick={close} disabled={busy} aria-label="Cerrar creación de almacén"><X className="h-5 w-5" /></button></div><form onSubmit={submit} onChange={() => setDirty(true)} className="mt-5 space-y-3"><label className="block text-xs font-semibold text-slate-700">Sede<CustomSelect remote={{ resource: "branches" }} name="branch_id" required searchable className="mt-1 w-full rounded-xl border border-slate-300 p-2.5"><option value="">Seleccionar sede</option>{branches.map(branch => <option key={branch.branch_id} value={branch.branch_id}>{branch.name}{branch.code ? ` (${branch.code})` : ""}</option>)}</CustomSelect></label><label className="block text-xs font-semibold text-slate-700">Código<input name="code" required maxLength={32} placeholder="ALM-02" className="mt-1 w-full rounded-xl border border-slate-300 p-2.5" /></label><label className="block text-xs font-semibold text-slate-700">Nombre<input name="name" required maxLength={128} placeholder="Almacén secundario" className="mt-1 w-full rounded-xl border border-slate-300 p-2.5" /></label><div className="flex justify-end gap-2 pt-3"><button type="button" onClick={close} className="rounded-xl border px-4 py-2 text-xs font-semibold">Cancelar</button><button type="submit" disabled={busy || branches.length === 0} className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy && <LoaderCircle className="h-4 w-4 animate-spin" />}Crear almacén</button></div></form></div>{ConfirmDialogNode}</ModalSurface>;
}
