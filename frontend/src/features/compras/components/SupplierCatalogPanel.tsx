import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";

interface Product extends Record<string, unknown> { id: string; sku: string; name: string }
interface Supplier extends Record<string, unknown> { id: string; legal_name: string; tax_id: string }
interface Condition {
  id: string; supplier_id: string; supplier_name: string; product_id: string; product_name: string; sku: string; supplier_sku: string; purchase_presentation: string;
  currency: string; unit_cost: string; minimum_quantity: string; order_multiple: string; lead_time_days: number; valid_from: string | null; valid_until: string | null; is_preferred: boolean; is_active: boolean; is_current: boolean; version: number; notes: string;
}

export function SupplierCatalogPanel({ canWrite }: { canWrite: boolean }) {
  const [items, setItems] = useState<Condition[]>([]);
  const [supplier, setSupplier] = useState<Supplier>();
  const [product, setProduct] = useState<Product>();
  const [editing, setEditing] = useState<Condition | null>(null);
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const sequence = useRef(0);
  const saving = useRef(false);
  const attempts = useRef(new Map<string, string>());
  const input = "mt-1 w-full rounded-lg border bg-white px-3 py-2 text-sm";
  const button = "rounded-lg border px-3 py-2 text-sm disabled:opacity-50";

  async function load() {
    const current = ++sequence.current;
    const result = await apiClient.request<{ items: Condition[]; total_count: number }>(`/api/v1/supplier-products?limit=25&offset=${page * 25}`);
    if (current !== sequence.current) return;
    setItems(result.items);
    setTotal(result.total_count);
  }

  useEffect(() => { void load().catch(() => setError("No se pudo cargar el catálogo del proveedor.")); return () => { sequence.current += 1; }; }, [page]);

  function edit(item: Condition | null) {
    setEditing(item);
    setSupplier(item ? { id: item.supplier_id, legal_name: item.supplier_name, tax_id: "" } : undefined);
    setProduct(item ? { id: item.product_id, name: item.product_name, sku: item.sku } : undefined);
    setError("");
    setOpen(true);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving.current || !supplier || !product) return;
    const values = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    const body = JSON.stringify({ ...values, supplier_id: supplier.id, product_id: product.id, lead_time_days: Number(values.lead_time_days), is_preferred: values.is_preferred === "on", is_active: values.is_active === "on", valid_from: values.valid_from || null, valid_until: values.valid_until || null, version: editing?.version || 0 });
    const key = attempts.current.get(body) || crypto.randomUUID();
    attempts.current.set(body, key);
    saving.current = true;
    setBusy(true);
    setError("");
    try {
      await apiClient.request("/api/v1/supplier-products", { method: "PUT", body, headers: { "Idempotency-Key": key } });
      attempts.current.delete(body);
      setOpen(false);
      setNotice("Condiciones guardadas. Se usarán para calcular las sugerencias de reposición.");
      await load();
    } catch (cause) { const detail = (cause as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : "No se pudieron guardar las condiciones."); }
    finally { setBusy(false); saving.current = false; }
  }

  return <section className="space-y-4 rounded-2xl border bg-white p-5 text-slate-900"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">Catálogo de productos por proveedor</h2><p className="text-sm text-slate-500">Condiciones por proveedor y producto. Costos, mínimos y múltiplos se expresan en la unidad base del producto; la presentación comercial queda como referencia.</p></div>{canWrite && <button type="button" className={button} onClick={() => edit(null)}>Agregar condiciones</button>}</div>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-700">{notice}</p>}<div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">Proveedor / producto</th><th className="p-2">Precio</th><th className="p-2">Compra mínima / múltiplo</th><th className="p-2">Plazo</th><th className="p-2">Estado</th><th className="p-2">Acción</th></tr></thead><tbody>{items.map(item => <tr key={item.id} className="border-t"><td className="p-2">{item.supplier_name}<strong className="block">{item.sku} · {item.product_name}</strong><span className="text-xs text-slate-500">Código proveedor: {item.supplier_sku || "Sin código"} · {item.purchase_presentation || "Sin presentación"}</span></td><td className="p-2">{item.currency} {item.unit_cost}</td><td className="p-2">{item.minimum_quantity} / {item.order_multiple}</td><td className="p-2">{item.lead_time_days} días</td><td className="p-2">{item.is_current ? "Vigente" : item.is_active ? "Fuera de vigencia" : "Archivado"}{item.is_preferred && " · Preferido"}</td><td className="p-2">{canWrite && <button type="button" className={button} onClick={() => edit(item)}>Editar</button>}</td></tr>)}</tbody></table></div>{!items.length && <p className="text-sm text-slate-500">No hay condiciones registradas.</p>}<div className="flex justify-between"><button type="button" className={button} disabled={page === 0} onClick={() => setPage(previous => previous - 1)}>Anterior</button><span>{total} condiciones</span><button type="button" className={button} disabled={(page + 1) * 25 >= total} onClick={() => setPage(previous => previous + 1)}>Siguiente</button></div>{open && <form key={editing?.id || "new"} onSubmit={event => void submit(event)} className="space-y-4 border-t pt-4"><fieldset disabled={busy} className="grid gap-4 md:grid-cols-3"><div className="md:col-span-2"><RemoteEntitySelect<Supplier> endpoint="/api/v1/suppliers" entityType="supplier" value={supplier?.id || ""} initialOption={supplier ? { value: supplier.id, label: supplier.legal_name, description: supplier.tax_id, data: supplier } : undefined} disabled={Boolean(editing)} onChange={(_, option) => setSupplier(option?.data)} mapOption={value => ({ value: value.id, label: value.legal_name, description: value.tax_id, data: value })} label="Proveedor" /></div><div><RemoteEntitySelect<Product> endpoint="/api/v1/products" entityType="product" value={product?.id || ""} initialOption={product ? { value: product.id, label: product.name, description: product.sku, data: product } : undefined} disabled={Boolean(editing)} onChange={(_, option) => setProduct(option?.data)} mapOption={value => ({ value: value.id, label: value.name, description: value.sku, data: value })} label="Producto" /></div><label className="text-sm">Presentación comercial del proveedor<input name="purchase_presentation" maxLength={128} defaultValue={editing?.purchase_presentation} placeholder="Ejemplo: caja de 12 unidades" className={input} /></label><label className="text-sm">Código del proveedor<input name="supplier_sku" maxLength={128} defaultValue={editing?.supplier_sku} className={input} /></label><label className="text-sm">Moneda<input name="currency" required readOnly={Boolean(editing)} pattern="[A-Z]{3}" maxLength={3} defaultValue={editing?.currency || "PEN"} className={input} /></label><label className="text-sm">Costo unitario<input name="unit_cost" required type="number" min="0" step="0.000001" defaultValue={editing?.unit_cost || "0"} className={input} /></label><label className="text-sm">Compra mínima<input name="minimum_quantity" required type="number" min="0.000001" step="0.000001" defaultValue={editing?.minimum_quantity || "1"} className={input} /></label><label className="text-sm">Múltiplo de compra<input name="order_multiple" required type="number" min="0.000001" step="0.000001" defaultValue={editing?.order_multiple || "1"} className={input} /></label><label className="text-sm">Plazo de entrega en días<input name="lead_time_days" required type="number" min="0" max="3650" defaultValue={editing?.lead_time_days ?? 7} className={input} /></label><label className="text-sm">Vigente desde<input name="valid_from" type="date" defaultValue={editing?.valid_from || ""} className={input} /></label><label className="text-sm">Vigente hasta<input name="valid_until" type="date" defaultValue={editing?.valid_until || ""} className={input} /></label><label className="text-sm">Notas<textarea name="notes" maxLength={4000} defaultValue={editing?.notes} className={input} /></label><label className="flex items-center gap-2 text-sm"><input name="is_preferred" type="checkbox" defaultChecked={editing?.is_preferred || false} />Preferido para este producto y moneda</label><label className="flex items-center gap-2 text-sm"><input name="is_active" type="checkbox" defaultChecked={editing?.is_active ?? true} />Activo</label></fieldset><div className="flex gap-2"><button type="submit" disabled={busy || !supplier || !product} className={button}>{busy ? "Guardando…" : "Guardar condiciones"}</button><button type="button" disabled={busy} onClick={() => setOpen(false)} className={button}>Cerrar edición</button></div></form>}</section>;
}
