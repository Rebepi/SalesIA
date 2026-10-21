import { ModalSurface } from "../../../ui/components/ModalSurface";
import { FormEvent, useState } from "react";
import { X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useConfirm } from "../../../ui/components/ConfirmDialog";

interface Product { id: string; name: string; sku: string }
interface Warehouse { warehouse_id: string; name: string; code: string }
export interface InventoryOperation {
  kind: "adjustment" | "lot" | "serial" | "location" | "rule";
  product_id?: string;
  warehouse_id?: string;
  id?: string;
  values?: Record<string, string | boolean>;
}

const titles = { adjustment: "Ajustar existencias", lot: "Registrar lote", serial: "Registrar serie", location: "Gestionar ubicación", rule: "Configurar reposición" };
const inputClass = "mt-1 w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs dark:border-slate-700 dark:bg-slate-950";

export function InventoryOperationDialog({ operation, products, warehouses, onClose, onSaved }: { operation: InventoryOperation; products: Product[]; warehouses: Warehouse[]; onClose: () => void; onSaved: () => void }) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const toast = useToast();
  const values = operation.values || {};
  const kind = operation.kind;
  const numeric = (name: string, label: string, fallback = "0", min = "0") => <label className="block text-xs font-semibold">{label}<input name={name} type="number" step="0.000001" min={min} required defaultValue={String(values[name] ?? fallback)} className={inputClass} /></label>;
  const text = (name: string, label: string, required = false, fallback = "") => <label className="block text-xs font-semibold">{label}<input name={name} required={required} defaultValue={String(values[name] ?? fallback)} className={inputClass} /></label>;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const data: Record<string, unknown> = Object.fromEntries(form.entries());
    let endpoint: string;
    if (kind === "adjustment") {
      endpoint = "/api/v1/inventory/adjustments";
      if (!Number(data.quantity_delta)) { setError("Ingresa una diferencia distinta de cero."); return; }
      if (!await confirm({ title: "¿Ajustar inventario?", text: `Se ajustará el inventario en ${data.quantity_delta} unidades y se registrará el motivo en Kardex. Para corregirlo será necesario otro ajuste.`, confirmLabel: "Ajustar" })) return;
    } else if (kind === "rule") endpoint = "/api/v1/inventory/rules";
    else if (kind === "location") {
      endpoint = `/api/v1/inventory/locations${operation.id ? `/${operation.id}` : ""}`;
      if (operation.id) {
        data.is_active = form.get("is_active") === "on";
        delete data.warehouse_id;
        if (!data.is_active && !await confirm({ title: "¿Desactivar ubicación?", text: "La ubicación dejará de estar disponible para nuevas operaciones. El sistema verificará las existencias antes de desactivarla.", danger: true, confirmLabel: "Desactivar" })) return;
      }
    } else endpoint = `/api/v1/inventory/${kind === "lot" ? "lots" : "serials"}`;
    for (const key of ["expiration_date", "manufacture_date", "notes"]) if (data[key] === "") data[key] = null;
    setError("");
    setBusy(true);
    try {
      await apiClient.request(endpoint, { method: kind === "location" && operation.id ? "PUT" : "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(data) });
      toast.success("Cambios guardados", "La operación quedó registrada.");
      onSaved();
    } catch (failure: unknown) {
      setError(String((failure as { detail?: string }).detail || "No se pudo guardar. Revisa los campos y vuelve a intentar."));
    } finally { setBusy(false); }
  }

  return (
    <>
      <ModalSurface labelledBy="inventory-operation-title" onClose={onClose} blocked={busy}><section className="app-modal-panel max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"><header className="mb-5 flex items-center justify-between"><h3 id="inventory-operation-title" className="font-bold">{titles[kind]}</h3><button type="button" aria-label="Cerrar operación" disabled={busy} onClick={onClose}><X className="h-5 w-5" /></button></header><form onSubmit={submit} className="space-y-4">
        {kind !== "location" && <label className="block text-xs font-semibold">Producto<CustomSelect remote={{ resource: "products" }} name="product_id" searchable required defaultValue={operation.product_id || ""} disabled={Boolean(operation.product_id)} className={inputClass}><option value="">Seleccionar producto</option>{products.map(product => <option key={product.id} value={product.id}>{product.sku} · {product.name}</option>)}</CustomSelect>{operation.product_id && <input name="product_id" type="hidden" value={operation.product_id} />}</label>}
        {kind !== "lot" && <label className="block text-xs font-semibold">Almacén<CustomSelect remote={{ resource: "warehouses" }} name="warehouse_id" searchable required defaultValue={operation.warehouse_id || ""} disabled={Boolean(operation.id || operation.warehouse_id)} className={inputClass}><option value="">Seleccionar almacén</option>{warehouses.map(warehouse => <option key={warehouse.warehouse_id} value={warehouse.warehouse_id}>{warehouse.code} · {warehouse.name}</option>)}</CustomSelect>{operation.warehouse_id && <input name="warehouse_id" type="hidden" value={operation.warehouse_id} />}</label>}
        {kind === "adjustment" && <>{numeric("quantity_delta", "Diferencia de unidades (positiva o negativa)", "0", "-999999999")}{numeric("unit_cost", "Costo unitario de entrada")}{text("reason", "Motivo del ajuste", true)}<p className="text-xs text-slate-500">Las salidas utilizan el costo promedio vigente. El ajuste respeta las reservas existentes.</p></>}
        {kind === "lot" && <>{text("lot_code", "Código de lote", true)}<label className="block text-xs font-semibold">Fabricación<input name="manufacture_date" type="date" className={inputClass} /></label><label className="block text-xs font-semibold">Vencimiento<input name="expiration_date" type="date" className={inputClass} /></label>{text("notes", "Observaciones")}</>}
        {kind === "serial" && text("serial_number", "Número de serie", true)}
        {kind === "location" && <>{text("code", "Código de ubicación", true)}<div className="grid grid-cols-2 gap-3">{text("aisle", "Pasillo", true, "A")}{text("rack", "Estante", true, "1")}{text("shelf", "Nivel", true, "1")}{text("bin", "Casillero", true, "1")}</div>{numeric("capacity_units", "Capacidad en unidades", "1000", "0.000001")}{operation.id && <label className="flex gap-2 text-xs"><input name="is_active" type="checkbox" defaultChecked={values.is_active !== false} />Ubicación activa</label>}</>}
        {kind === "rule" && <div className="grid grid-cols-2 gap-3">{numeric("min_quantity", "Existencia mínima")}{numeric("max_quantity", "Existencia máxima (0: sin límite)")}{numeric("reorder_point", "Punto de reposición")}{numeric("reorder_quantity", "Cantidad a reponer")}</div>}
        {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-xs text-red-800">{error}</p>}<footer className="flex justify-end gap-2 border-t pt-4"><button type="button" disabled={busy} onClick={onClose} className="rounded-xl border px-4 py-2 text-xs">Cancelar</button><button type="submit" disabled={busy} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy ? "Guardando…" : "Guardar"}</button></footer>
      </form></section></ModalSurface>
      {ConfirmDialogNode}
    </>
  );
}
