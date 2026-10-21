import { selectorSeed } from "../../../api/selectorSeed";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useOperatingProfile } from "../../organizacion/components/OperatingProfileContext";
import { FormEvent, useEffect, useRef, useState } from "react";
import { ChevronLeft, LoaderCircle, PackagePlus, Plus, X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { notifyEntityChanged } from "../../../ui/entityEvents";
import { useUnsavedChanges } from "../../../ui/drafts";
import { useToast } from "../../../ui/toast/ToastContext";
import { useConfirm } from "../../../ui/components/ConfirmDialog";

interface QuickProductDialogProps {
  isOpen: boolean;
  currency: string;
  defaultTaxRate: string;
  onClose: () => void;
  onCreated: (product: Record<string, unknown>) => void;
}

interface Category { id: string; code: string; name: string; is_active: boolean }
interface Unit { id: string; code: string; name: string }
interface Supplier { id: string; supplier_id?: string; legal_name: string }
interface Warehouse { id: string; warehouse_id?: string; name: string; code?: string }

export function QuickProductDialog({ isOpen, currency, defaultTaxRate, onClose, onCreated }: QuickProductDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [categoryId, setCategoryId] = useState("");
  const [unitCode, setUnitCode] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [auxiliary, setAuxiliary] = useState<"category" | "unit" | null>(null);
  const [auxCode, setAuxCode] = useState("");
  const [auxName, setAuxName] = useState("");
  const toast = useToast();
  const { enabled } = useOperatingProfile();
  useUnsavedChanges(isOpen && dirty);

  useEffect(() => {
    if (isOpen) dialogRef.current?.showModal(); else dialogRef.current?.close();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    Promise.all([
      selectorSeed<Category>("categories", { active_only: "true" }),
      selectorSeed<Unit>("units", { active_only: "true" }),
      selectorSeed<Supplier>("suppliers"),
      selectorSeed<Warehouse>("warehouses")
    ]).then(([categoryRows, unitRows, supplierRows, warehouseRows]) => {
      setCategories(categoryRows.filter(item => item.is_active !== false));
      setUnits(unitRows);
      setSuppliers(supplierRows);
      setWarehouses(warehouseRows);
      setCategoryId(current => current || categoryRows.find(item => item.is_active !== false)?.id || "");
      setUnitCode(current => current || unitRows[0]?.code || "");
    }).catch(error => toast.error("No se pudieron cargar los catálogos", error instanceof Error ? error.message : "Reintenta la operación.")).finally(() => setLoading(false));
  }, [isOpen]);

  async function close() {
    if (dirty && !await confirm({ title: "¿Cerrar sin guardar?", text: "Hay datos del producto sin guardar.", confirmLabel: "Cerrar", cancelLabel: "Quedarme" })) return;
    setAuxiliary(null);
    onClose();
  }

  async function createAuxiliary(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      if (auxiliary === "category") {
        const row = await apiClient.request<Category>("/api/v1/categories", { method: "POST", body: JSON.stringify({ code: auxCode.trim() || undefined, name: auxName.trim(), parent_id: null, sort_order: categories.length }) });
        setCategories(previous => [...previous, row]);
        setCategoryId(row.id);
      } else {
        const row = await apiClient.request<Unit>("/api/v1/units", { method: "POST", body: JSON.stringify({ code: auxCode.trim().toUpperCase(), name: auxName.trim(), allow_fractions: false, precision_digits: 0 }) });
        setUnits(previous => [...previous, row]);
        setUnitCode(row.code);
      }
      setAuxCode("");
      setAuxName("");
      setAuxiliary(null);
      toast.success("Catálogo actualizado", "El nuevo valor quedó seleccionado.");
    } catch (error: unknown) {
      const detail = error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudo crear el valor.";
      toast.error("Error", detail);
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const initialStock = String(data.get("initial_stock_quantity") || "0");
    const reorderPoint = String(data.get("reorder_point") || "0");
    const reorderQuantity = String(data.get("reorder_quantity") || "0");
    if ((Number(initialStock) > 0 || Number(reorderPoint) > 0 || Number(reorderQuantity) > 0) && !warehouseId) {
      toast.error("Almacén requerido", "Selecciona el almacén del stock inicial o la regla de reposición.");
      return;
    }
    setBusy(true);
    try {
      const product = await apiClient.request<Record<string, unknown>>("/api/v1/products", {
        method: "POST",
        body: JSON.stringify({
          sku: String(data.get("sku") || "").trim(), name: String(data.get("name") || "").trim(), category_id: categoryId,
          unit_of_measure: unitCode, unit_price: String(data.get("unit_price") || "0"), unit_cost: String(data.get("unit_cost") || "0"),
          tax_rate: String(data.get("tax_rate") || defaultTaxRate), description: String(data.get("description") || "").trim() || null,
          product_type: enabled("inventory") ? "product" : "service", track_inventory: data.get("track_inventory") === "on",
          barcode: String(data.get("barcode") || "").trim() || null, supplier_id: String(data.get("supplier_id") || "") || null,
          brand: String(data.get("brand") || "").trim() || null, image_url: String(data.get("image_url") || "").trim() || null,
          length_cm: String(data.get("length_cm") || "") || null, width_cm: String(data.get("width_cm") || "") || null,
          height_cm: String(data.get("height_cm") || "") || null, weight_kg: String(data.get("weight_kg") || "") || null,
          tracking_mode: String(data.get("tracking_mode") || "NONE"), initial_stock_quantity: initialStock,
          warehouse_id: warehouseId || null, reorder_point: reorderPoint, reorder_quantity: reorderQuantity,
          warranty_period_months: Number(data.get("warranty_period_months") || 0), warranty_policy: String(data.get("warranty_policy") || "").trim() || null,
          price_includes_tax: data.get("price_includes_tax") === "on"
        })
      });
      setDirty(false);
      notifyEntityChanged("product", product);
      onCreated(product);
      toast.success("Producto creado", `${String(product.name || data.get("name"))} ya está disponible.`);
      onClose();
    } catch (error: unknown) {
      const detail = error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudo crear el producto.";
      toast.error("Error al crear producto", detail);
    } finally {
      setBusy(false);
    }
  }

  if (!isOpen) return null;
  const inputClass = "mt-1 w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100";

  return (
    <dialog ref={dialogRef} onCancel={event => { event.preventDefault(); close(); }} className="app-modal-panel w-[min(96vw,960px)] rounded-3xl border-0 bg-white p-0 shadow-2xl backdrop:bg-slate-950/70 dark:bg-slate-900">
      <header className="flex items-center justify-between border-b border-slate-100 p-5 dark:border-slate-800">
        <div className="flex items-center gap-3"><PackagePlus className="h-5 w-5 text-teal-600" /><div><h2 className="text-lg font-bold text-slate-900 dark:text-white">Crear producto</h2><p className="text-xs text-slate-500">Ficha comercial, logística, fiscal e inventario inicial.</p></div></div>
        <button type="button" onClick={close} aria-label="Cerrar creación de producto" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"><X className="h-5 w-5" /></button>
      </header>
      {loading ? <div className="grid h-72 place-items-center"><LoaderCircle className="h-7 w-7 animate-spin text-teal-600" /></div> : auxiliary ? (
        <form onSubmit={createAuxiliary} className="space-y-4 p-6">
          <button type="button" onClick={() => setAuxiliary(null)} className="inline-flex items-center gap-1 text-xs font-semibold text-teal-600"><ChevronLeft className="h-4 w-4" />Volver al producto</button>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Nueva {auxiliary === "category" ? "categoría" : "unidad"}</h3>
          <div className="grid gap-4 sm:grid-cols-2"><label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Código<input required={auxiliary === "unit"} value={auxCode} onChange={event => setAuxCode(event.target.value)} className={inputClass} /></label><label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Nombre<input required value={auxName} onChange={event => setAuxName(event.target.value)} className={inputClass} /></label></div>
          <div className="flex justify-end"><button type="submit" disabled={busy} className="rounded-xl bg-teal-700 px-5 py-2.5 text-xs font-semibold text-white disabled:opacity-50">Crear y seleccionar</button></div>
        </form>
      ) : (
        <form onSubmit={submit} onChange={() => setDirty(true)} className="max-h-[78vh] space-y-5 overflow-y-auto p-5">
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">SKU<input name="sku" required autoFocus className={inputClass} /></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 sm:col-span-2">Nombre<input name="name" required className={inputClass} /></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Código de barras<input name="barcode" className={inputClass} /></label>
            <div className="text-xs font-semibold text-slate-700 dark:text-slate-300"><span className="flex items-center justify-between">Categoría<button type="button" onClick={() => setAuxiliary("category")} className="inline-flex items-center gap-1 text-teal-600"><Plus className="h-3 w-3" />Crear</button></span><CustomSelect remote={{ resource: "categories" }} required value={categoryId} onChange={event => setCategoryId(event.target.value)} className={inputClass}><option value="">Seleccionar</option>{categories.map(item => <option key={item.id} value={item.id}>{item.name} ({item.code})</option>)}</CustomSelect></div>
            <div className="text-xs font-semibold text-slate-700 dark:text-slate-300"><span className="flex items-center justify-between">Unidad<button type="button" onClick={() => setAuxiliary("unit")} className="inline-flex items-center gap-1 text-teal-600"><Plus className="h-3 w-3" />Crear</button></span><CustomSelect remote={{ resource: "units" }} required value={unitCode} onChange={event => setUnitCode(event.target.value)} className={inputClass}><option value="">Seleccionar</option>{units.map(item => <option key={item.id} value={item.code}>{item.name} ({item.code})</option>)}</CustomSelect></div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Proveedor<CustomSelect remote={{ resource: "suppliers" }} name="supplier_id" className={inputClass}><option value="">Sin proveedor principal</option>{suppliers.map(item => <option key={item.id || item.supplier_id} value={item.id || item.supplier_id}>{item.legal_name}</option>)}</CustomSelect></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Marca<input name="brand" className={inputClass} /></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Precio ({currency})<input name="unit_price" required type="number" min="0" step="0.000001" className={inputClass} /></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Costo ({currency})<input name="unit_cost" type="number" min="0" step="0.000001" defaultValue="0" className={inputClass} /></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Impuesto<input name="tax_rate" type="number" min="0" step="0.0001" defaultValue={defaultTaxRate} className={inputClass} /></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Control<select name="tracking_mode" className={inputClass}><option value="NONE">Sin lote o serie</option><option value="LOT">Por lote</option><option value="SERIAL">Por serie</option></select></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 lg:col-span-2">Imagen URL<input name="image_url" type="url" className={inputClass} /></label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 lg:col-span-2">Descripción<input name="description" className={inputClass} /></label>
          </section>
          <section className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700"><h3 className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Dimensiones y garantía</h3><div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6"><label className="text-xs text-slate-600 dark:text-slate-300">Largo cm<input name="length_cm" type="number" min="0" step="0.001" className={inputClass} /></label><label className="text-xs text-slate-600 dark:text-slate-300">Ancho cm<input name="width_cm" type="number" min="0" step="0.001" className={inputClass} /></label><label className="text-xs text-slate-600 dark:text-slate-300">Alto cm<input name="height_cm" type="number" min="0" step="0.001" className={inputClass} /></label><label className="text-xs text-slate-600 dark:text-slate-300">Peso kg<input name="weight_kg" type="number" min="0" step="0.001" className={inputClass} /></label><label className="text-xs text-slate-600 dark:text-slate-300">Garantía meses<input name="warranty_period_months" type="number" min="0" defaultValue="0" className={inputClass} /></label><label className="text-xs text-slate-600 dark:text-slate-300">Política<input name="warranty_policy" className={inputClass} /></label></div></section>
          {enabled("inventory") && <section className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700"><h3 className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Inventario y reposición</h3><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><label className="text-xs text-slate-600 dark:text-slate-300">Almacén<CustomSelect remote={{ resource: "warehouses" }} value={warehouseId} onChange={event => setWarehouseId(event.target.value)} className={inputClass}><option value="">Seleccionar si corresponde</option>{warehouses.map(item => <option key={item.id || item.warehouse_id} value={item.id || item.warehouse_id}>{item.name}{item.code ? ` (${item.code})` : ""}</option>)}</CustomSelect></label><label className="text-xs text-slate-600 dark:text-slate-300">Stock inicial<input name="initial_stock_quantity" type="number" min="0" step="0.000001" defaultValue="0" className={inputClass} /></label><label className="text-xs text-slate-600 dark:text-slate-300">Punto de reposición<input name="reorder_point" type="number" min="0" step="0.000001" defaultValue="0" className={inputClass} /></label><label className="text-xs text-slate-600 dark:text-slate-300">Cantidad a reponer<input name="reorder_quantity" type="number" min="0" step="0.000001" defaultValue="0" className={inputClass} /></label></div><div className="mt-3 flex flex-wrap gap-5 text-xs text-slate-600 dark:text-slate-300"><label className="flex items-center gap-2"><input name="track_inventory" type="checkbox" defaultChecked />Controlar existencias</label><label className="flex items-center gap-2"><input name="price_includes_tax" type="checkbox" />Precio incluye impuesto</label></div></section>}
          <div className="flex justify-end gap-2 border-t border-slate-100 pt-4 dark:border-slate-800"><button type="button" onClick={close} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200">Cancelar</button><button type="submit" disabled={busy || !categoryId || !unitCode} className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy && <LoaderCircle className="h-4 w-4 animate-spin" />}Crear y seleccionar</button></div>
        </form>
      )}
      {ConfirmDialogNode}
    </dialog>
  );
}
