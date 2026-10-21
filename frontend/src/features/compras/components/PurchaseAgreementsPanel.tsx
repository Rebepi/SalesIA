import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";

interface Supplier extends Record<string, unknown> { id: string; legal_name: string; tax_id: string }
interface Product extends Record<string, unknown> { id: string; name: string; sku: string; unit_cost: string }
interface Agreement { id: string; version: number; status: string; supplier_name: string; can_release: boolean; committed_amount: string; available_amount: string | null; details: { reference: string; currency: string; valid_from: string; valid_until: string }; lines: { product_id: string; name: string; sku: string; quantity: string; available_quantity: string; committed_quantity: string; received_quantity: string }[]; orders: { id: string; status: string; delivery_date: string | null }[] }

export function PurchaseAgreementsPanel({ canWrite, warehouses, onChanged }: { canWrite: boolean; warehouses: { warehouse_id: string; name: string }[]; onChanged: () => void }) {
  const [items, setItems] = useState<Agreement[]>([]);
  const [open, setOpen] = useState(false);
  const [supplier, setSupplier] = useState<Supplier>();
  const [product, setProduct] = useState<Product>();
  const [lines, setLines] = useState<{ product: Product; quantity: string; unit_cost: string; tax_rate: string }[]>([]);
  const [releaseQuantities, setReleaseQuantities] = useState<Record<string, string>>({});
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const input = "mt-1 w-full rounded-lg border bg-white p-2 text-sm";
  const button = "rounded-lg border px-3 py-2 text-sm disabled:opacity-50";

  async function load() { const result = await apiClient.request<{ items: Agreement[] }>("/api/v1/purchase-agreements"); setItems(result.items); }
  useEffect(() => { void load().catch(() => setError("No se pudieron cargar los acuerdos de compra.")); }, []);

  async function write(path: string, payload: unknown) {
    if (sending.current) return;
    sending.current = true;
    setBusy(true);
    setError("");
    const body = JSON.stringify(payload);
    const signature = `${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try {
      await apiClient.request(path, { method: "POST", headers: { "Idempotency-Key": key }, body });
      keys.current.delete(signature);
      setNotice("Operación registrada. Las liberaciones generan órdenes pendientes de aprobación y consumen el saldo del acuerdo.");
      setReleaseQuantities({});
      setOpen(false);
      await load();
      onChanged();
    } catch (cause) { const detail = (cause as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo guardar el acuerdo."); }
    finally { sending.current = false; setBusy(false); }
  }

  function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supplier || !lines.length) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    void write("/api/v1/purchase-agreements", { ...values, supplier_id: supplier.id, payment_terms_days: Number(values.payment_terms_days), amount_limit: values.amount_limit || null, items: lines.map(line => ({ product_id: line.product.id, quantity: line.quantity, unit_cost: line.unit_cost, tax_rate: line.tax_rate, discount_percentage: "0" })) });
  }

  function release(event: FormEvent<HTMLFormElement>, agreement: Agreement) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const selected = agreement.lines.filter(line => Number(releaseQuantities[`${agreement.id}:${line.product_id}`] || 0) > 0);
    if (!selected.length) { setError("Selecciona al menos una cantidad para liberar."); return; }
    void write(`/api/v1/purchase-agreements/${agreement.id}/release`, { ...values, version: agreement.version, items: selected.map(line => ({ product_id: line.product_id, quantity: releaseQuantities[`${agreement.id}:${line.product_id}`] })) });
  }

  return <section className="mt-6 space-y-4 rounded-2xl border bg-white p-5 text-slate-900"><div className="flex justify-between gap-3"><div><h2 className="font-semibold">Acuerdos abiertos de compra</h2><p className="text-sm text-slate-500">Precios negociados, límites por producto, importe máximo y entregas parciales dentro de la vigencia.</p></div>{canWrite && <button type="button" className={button} onClick={() => setOpen(!open)}>{open ? "Cerrar alta" : "Nuevo acuerdo"}</button>}</div>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}{open && <form onSubmit={create} className="space-y-3"><fieldset disabled={busy} className="space-y-3"><RemoteEntitySelect<Supplier> endpoint="/api/v1/suppliers" entityType="supplier" value={supplier?.id || ""} onChange={(_, option) => setSupplier(option?.data)} mapOption={item => ({ value: item.id, label: item.legal_name, description: item.tax_id, data: item })} label="Proveedor" /><div className="grid gap-3 sm:grid-cols-4"><label className="text-sm">Referencia<input className={input} name="reference" required minLength={2} maxLength={128} /></label><label className="text-sm">Almacén<CustomSelect remote={{ resource: "warehouses" }} className={input} name="warehouse_id" required><option value="">Seleccionar</option>{warehouses.map(item => <option key={item.warehouse_id} value={item.warehouse_id}>{item.name}</option>)}</CustomSelect></label><label className="text-sm">Moneda<input className={input} name="currency" required pattern="[A-Z]{3}" maxLength={3} defaultValue="PEN" /></label><label className="text-sm">Importe máximo opcional<input className={input} name="amount_limit" type="number" min="0.000001" step="0.000001" /></label><label className="text-sm">Vigente desde<input className={input} name="valid_from" type="date" required /></label><label className="text-sm">Vigente hasta<input className={input} name="valid_until" type="date" required /></label><label className="text-sm">Pago en días<input className={input} name="payment_terms_days" type="number" min="0" max="365" defaultValue="30" required /></label><label className="text-sm">Notas<input className={input} name="notes" maxLength={4000} /></label></div><div className="flex items-end gap-2"><div className="flex-1"><RemoteEntitySelect<Product> endpoint="/api/v1/products" entityType="product" value={product?.id || ""} onChange={(_, option) => setProduct(option?.data)} mapOption={item => ({ value: item.id, label: item.name, description: item.sku, data: item })} label="Producto del acuerdo" /></div><button type="button" className={button} disabled={!product || lines.some(line => line.product.id === product.id)} onClick={() => { if (product) setLines(previous => [...previous, { product, quantity: "1", unit_cost: product.unit_cost || "0", tax_rate: "0" }]); }}>Agregar</button></div>{lines.map((line, index) => <div key={line.product.id} className="flex flex-wrap items-end gap-3 rounded-lg border p-3"><strong className="mr-auto text-sm">{line.product.sku} · {line.product.name}</strong>{([['quantity', 'Cantidad máxima'], ['unit_cost', 'Costo negociado'], ['tax_rate', 'Impuesto (0–1)']] as const).map(([field, label]) => <label className="w-32 text-xs" key={field}>{label}<input className={input} type="number" min={field === "quantity" ? "0.000001" : "0"} max={field === "tax_rate" ? "1" : undefined} required step="0.000001" value={line[field]} onChange={event => setLines(previous => previous.map((row, position) => position === index ? { ...row, [field]: event.target.value } : row))} /></label>)}<button type="button" className={button} onClick={() => setLines(previous => previous.filter((_, position) => position !== index))}>Quitar</button></div>)}<button className={button} disabled={busy || !supplier || !lines.length} type="submit">Guardar acuerdo en borrador</button></fieldset></form>}{items.map(agreement => <details key={agreement.id} className="space-y-3 rounded-xl border p-4"><summary className="cursor-pointer text-sm"><strong>{agreement.details.reference} · {agreement.supplier_name}</strong> · {agreement.status} · {agreement.details.currency} comprometido {agreement.committed_amount} · Disponible {agreement.available_amount ?? "según cantidades"}</summary><p className="mt-3 text-xs text-slate-500">Vigencia {agreement.details.valid_from} a {agreement.details.valid_until} · v{agreement.version}</p>{canWrite && <><label className="block text-sm">Motivo de aprobación o cierre<input className={input} minLength={5} maxLength={2000} value={reasons[agreement.id] || ""} onChange={event => setReasons(previous => ({ ...previous, [agreement.id]: event.target.value }))} /></label><div className="flex gap-2">{["draft", "active"].includes(agreement.status) && <button type="button" disabled={busy || (reasons[agreement.id] || "").trim().length < 5} className={button} onClick={() => void write(`/api/v1/purchase-agreements/${agreement.id}/${agreement.status === "draft" ? "approve" : "close"}`, { version: agreement.version, reason: reasons[agreement.id] })}>{agreement.status === "draft" ? "Aprobar acuerdo" : "Cerrar acuerdo"}</button>}</div></>}<form className="space-y-3" onSubmit={event => release(event, agreement)}><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">Producto</th><th className="p-2">Límite</th><th className="p-2">Comprometido</th><th className="p-2">Recibido</th><th className="p-2">Disponible</th><th className="p-2">Liberar</th></tr></thead><tbody>{agreement.lines.map(line => <tr key={line.product_id} className="border-t"><td className="p-2">{line.sku} · {line.name}</td><td className="p-2">{line.quantity}</td><td className="p-2">{line.committed_quantity}</td><td className="p-2">{line.received_quantity}</td><td className="p-2">{line.available_quantity}</td><td className="p-2"><input className={`${input} w-28`} aria-label={`Liberar ${line.sku}`} type="number" min="0" step="0.000001" max={line.available_quantity} disabled={!canWrite || !agreement.can_release || busy} value={releaseQuantities[`${agreement.id}:${line.product_id}`] || "0"} onChange={event => setReleaseQuantities(previous => ({ ...previous, [`${agreement.id}:${line.product_id}`]: event.target.value }))} /></td></tr>)}</tbody></table></div>{canWrite && agreement.can_release && <div className="flex flex-wrap items-end gap-3"><label className="text-sm">Entrega de esta liberación<input className={input} name="delivery_date" type="date" required min={agreement.details.valid_from} max={agreement.details.valid_until} /></label><label className="text-sm">Notas<input className={input} name="notes" maxLength={2000} /></label><button className={button} disabled={busy} type="submit">Generar orden parcial</button></div>}</form><ul className="text-xs text-slate-500">{agreement.orders.map(order => <li key={order.id}>Orden {order.id.slice(0, 8).toUpperCase()} · {order.status} · {order.delivery_date || "Sin fecha"}</li>)}</ul></details>)}</section>;
}
