import { CustomSelect } from "../../../ui/components/CustomSelect";
import { Settings2, Plus, Trash2, Save } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";

type Policy = { business_date?: string; version: number; tiers: { minimum_attainment: string; rate: string }[]; base: "sales" | "margin"; include_tax: boolean; earned_on: "sale" | "collection" | "delivery" | "full_payment"; product_ids: string[]; category_ids: string[]; valid_from: string; valid_until: string | null };
type Product = Record<string, unknown> & { id: string; name: string; sku: string };
type Category = { id: string; name: string };
const field = "team-input w-full";
const button = "team-button";
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : "No se pudo consultar o guardar la política de comisiones."; }
function percentage(rate: string) { const [whole, fraction = ""] = rate.split("."); const value = BigInt(whole || "0") * 1000000n + BigInt(fraction.padEnd(6, "0").slice(0, 6)); return `${value / 10000n}.${String(value % 10000n).padStart(4, "0")}`; }
function rate(percent: string) { const [whole, fraction = ""] = percent.split("."); const value = BigInt(whole || "0") * 10000n + BigInt(fraction.padEnd(4, "0").slice(0, 4)); return `${value / 1000000n}.${String(value % 1000000n).padStart(6, "0")}`; }

export function CommissionPolicyPanel() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [tiers, setTiers] = useState<{ minimum: string; percentage: string }[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Record<string, string>>({});
  const [history, setHistory] = useState<{ policy: Policy; actor: string; reason: string; at: string }[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  function adopt(value: Policy) { setPolicy({ ...value, valid_from: value.business_date && value.valid_from < value.business_date ? value.business_date : value.valid_from }); setTiers(value.tiers.map(tier => ({ minimum: tier.minimum_attainment, percentage: percentage(tier.rate) }))); }
  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([apiClient.request<Policy>("/api/v1/sales/commission-policy", { signal: controller.signal }), apiClient.request<Category[] | { items: Category[] }>("/api/v1/categories", { signal: controller.signal }).catch(() => [] as Category[])]).then(([value, result]) => { if (!controller.signal.aborted) { adopt(value); setCategories(Array.isArray(result) ? result : result.items); void Promise.all(value.product_ids.map(id => apiClient.request<Product>(`/api/v1/products/${id}`, { signal: controller.signal }).then(row => [id, `${row.sku} · ${row.name}`] as const))).then(labels => { if (!controller.signal.aborted) setProducts(Object.fromEntries(labels)); }).catch(() => undefined); } }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, []);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!policy || lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const values = Object.fromEntries(new FormData(event.currentTarget));
    let signature = "";
    try {
      const body = JSON.stringify({ expected_version: policy.version, policy: { ...policy, tiers: tiers.map(tier => ({ minimum_attainment: tier.minimum, rate: rate(tier.percentage) })) }, reason: values.reason });
      signature = body;
      const key = keys.current.get(signature) || crypto.randomUUID();
      keys.current.set(signature, key);
      const result = await apiClient.request<Policy>("/api/v1/sales/commission-policy", { method: "PUT", headers: { "Idempotency-Key": key }, body });
      adopt(result);
      keys.current.delete(signature);
      setNotice("Nueva versión guardada. Las ventas confirmadas conservan la política y participación que tenían al vender.");
    } catch (cause) { setError(problem(cause)); }
    finally { lock.current = false; setBusy(false); }
  }
  async function loadHistory() { try { setHistory(await apiClient.request("/api/v1/sales/commission-policy/history")); } catch (cause) { setError(problem(cause)); } }
  return <section className="team-panel"><h2 className="team-panel-title"><Settings2 size={20} aria-hidden="true" />Reglas, devengo y vigencia de comisiones</h2><div className="mt-4 space-y-3">{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}{policy && <form className="space-y-4" onSubmit={save}><p className="team-note">Versión {policy.version}. La tasa se obtiene del cumplimiento del período de venta y queda fijada en el primer reconocimiento de esa venta; los cobros y devoluciones posteriores ajustan el importe sin cambiar esa tasa.</p><div className="grid gap-3 md:grid-cols-3"><label className="grid gap-1 text-sm">Base<CustomSelect searchable={false} className={field} value={policy.base} disabled={busy} onChange={event => setPolicy({ ...policy, base: event.target.value as Policy["base"], include_tax: event.target.value === "margin" ? false : policy.include_tax })}><option value="sales">Importe de venta</option><option value="margin">Margen por línea</option></CustomSelect></label><label className="grid gap-1 text-sm">Cuándo se gana<CustomSelect searchable={false} className={field} value={policy.earned_on} disabled={busy} onChange={event => setPolicy({ ...policy, earned_on: event.target.value as Policy["earned_on"] })}><option value="sale">Confirmación de venta</option><option value="collection">Proporción efectivamente cobrada</option><option value="delivery">Unidades entregadas</option><option value="full_payment">Cobro completo</option></CustomSelect></label><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={policy.include_tax} disabled={busy || policy.base === "margin"} onChange={event => setPolicy({ ...policy, include_tax: event.target.checked })} />Incluir impuestos en base de venta</label><label className="grid gap-1 text-sm">Vigente desde<input className={field} type="date" required value={policy.valid_from} disabled={busy} onChange={event => setPolicy({ ...policy, valid_from: event.target.value })} /></label><label className="grid gap-1 text-sm">Vigente hasta (opcional)<input className={field} type="date" min={policy.valid_from} value={policy.valid_until || ""} disabled={busy} onChange={event => setPolicy({ ...policy, valid_until: event.target.value || null })} /></label></div><p className="text-xs text-slate-500">El margen usa el precio neto y costo histórico de cada línea; los márgenes negativos generan base cero. La moneda se liquida por separado y las cuotas deben estar expresadas en esa misma moneda.</p>
      <fieldset className="team-fieldset space-y-3" disabled={busy}><legend className="px-1 text-sm font-semibold">Escalas por cumplimiento</legend>{tiers.map((tier, index) => <div className="team-tier-row" key={index}><label className="grid gap-1 text-sm">Cumplimiento mínimo %<input className={field} type="number" min="0" step="0.000001" required value={tier.minimum} onChange={event => setTiers(previous => previous.map((row, position) => position === index ? { ...row, minimum: event.target.value } : row))} /></label><label className="grid gap-1 text-sm">Comisión %<input className={field} type="number" min="0" max="100" step="0.0001" required value={tier.percentage} onChange={event => setTiers(previous => previous.map((row, position) => position === index ? { ...row, percentage: event.target.value } : row))} /></label><button type="button" className={`${button} team-danger`} disabled={tiers.length <= 1} onClick={() => setTiers(previous => previous.filter((_, position) => position !== index))}><Trash2 size={15} aria-hidden="true" />Quitar tramo</button></div>)}<button type="button" className={button} disabled={tiers.length >= 100} onClick={() => setTiers(previous => [...previous, { minimum: "0", percentage: "0" }])}><Plus size={16} aria-hidden="true" />Agregar tramo</button></fieldset>
      <fieldset className="team-fieldset space-y-3" disabled={busy}><legend className="px-1 text-sm font-semibold">Productos y categorías incluidos</legend><p className="text-xs text-slate-500">Sin selección se incluyen todas las líneas. Con selección se incluyen los productos elegidos y los que pertenecen directamente a las categorías elegidas. El alcance se conserva al confirmar cada venta.</p><RemoteEntitySelect<Product> value="" onChange={(_, option) => { if (option && !policy.product_ids.includes(option.value)) { setPolicy({ ...policy, product_ids: [...policy.product_ids, option.value] }); setProducts(previous => ({ ...previous, [option.value]: `${option.data.sku} · ${option.data.name}` })); } }} endpoint="/api/v1/products" entityType="product" mapOption={row => ({ value: row.id, label: `${row.sku} · ${row.name}`, data: row })} label="Agregar producto" disabled={busy} /><div className="flex flex-wrap gap-2">{policy.product_ids.map(id => <button type="button" className={button} key={id} disabled={busy} onClick={() => setPolicy({ ...policy, product_ids: policy.product_ids.filter(value => value !== id) })}>{products[id] || `Producto ${id.slice(0, 8)}`} · Quitar</button>)}</div><CustomSelect remote={{ resource: "categories" }} searchable={true} aria-label="Agregar categoría" className={field} value="" disabled={busy} onChange={event => { if (event.target.value && !policy.category_ids.includes(event.target.value)) setPolicy({ ...policy, category_ids: [...policy.category_ids, event.target.value] }); }}><option value="">Agregar categoría</option>{categories.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</CustomSelect><div className="flex flex-wrap gap-2">{policy.category_ids.map(id => <button type="button" className={button} key={id} disabled={busy} onClick={() => setPolicy({ ...policy, category_ids: policy.category_ids.filter(value => value !== id) })}>{categories.find(row => row.id === id)?.name || id.slice(0, 8)} · Quitar</button>)}</div></fieldset>
      <label className="grid gap-1 text-sm">Motivo de nueva versión<textarea className={field} name="reason" required minLength={5} maxLength={2000} disabled={busy} /></label><div className="team-actions"><button className={`${button} team-primary`} disabled={busy}><Save size={16} aria-hidden="true" />Guardar nueva política</button><button type="button" className={button} disabled={busy} onClick={() => void loadHistory()}>Historial de políticas</button></div></form>}{history.map(row => <details key={row.policy.version} className="rounded-lg border p-3 text-sm"><summary>Versión {row.policy.version} · {row.actor} · {row.at.slice(0, 19).replace("T", " ")}</summary><p>{row.reason}</p><p>Desde {row.policy.valid_from} hasta {row.policy.valid_until || "sin límite"} · {row.policy.base} · {row.policy.earned_on}</p>{row.policy.tiers.map(tier => <p key={tier.minimum_attainment}>Desde {tier.minimum_attainment} % de cumplimiento: comisión {percentage(tier.rate)} %</p>)}</details>)}</div></section>;
}
