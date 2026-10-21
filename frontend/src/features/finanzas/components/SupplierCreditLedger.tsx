import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useState } from "react";
import { apiClient } from "../../../api/client";

type Summary = { supplier_id: string; supplier_name: string; currency: string; balance: string };
type Ledger = { supplier_name: string; currency: string; available: string; lots: { movement_id: string; reference: string; kind: string; amount: string; remaining: string; date: string; claim_code: string | null; source_document_id: string | null }[]; movements: { id: string; kind: string; date: string; amount: string; reference: string; notes: string; allocations: { movement_id: string; reference: string; amount: string; claim_code: string | null }[] }[] };
const names: Record<string, string> = { advance: "Anticipo", credit: "Crédito", refund: "Reintegro recibido", application: "Aplicación a obligación", reversal: "Reversión de aplicación" };

export function SupplierCreditLedger({ revision }: { revision: number }) {
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [selected, setSelected] = useState("");
  const [ledger, setLedger] = useState<Ledger | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    void apiClient.request<Summary[]>("/api/v1/supplier-balances", { signal: controller.signal }).then(setSummaries).catch(() => { if (!controller.signal.aborted) setError("No se pudieron cargar los saldos por proveedor."); });
    return () => controller.abort();
  }, [revision]);
  useEffect(() => {
    setLedger(null);
    setError("");
    if (!selected) return;
    const controller = new AbortController();
    void apiClient.request<Ledger>(`/api/v1/supplier-balances/${selected}`, { signal: controller.signal }).then(setLedger).catch(cause => { if (!controller.signal.aborted) setError(typeof (cause as { detail?: unknown })?.detail === "string" ? String((cause as { detail: string }).detail) : "No se pudo reconstruir el historial del saldo."); });
    return () => controller.abort();
  }, [selected, revision]);
  return <section className="space-y-3 rounded-xl border bg-white p-4"><h2 className="font-semibold">Origen y aplicación de saldos a favor</h2><label className="flex flex-col gap-1 text-sm">Proveedor y moneda<CustomSelect searchable className="rounded-lg border p-2" value={selected} onChange={event => setSelected(event.target.value)}><option value="">Consultar un saldo</option>{summaries.map(item => <option key={`${item.supplier_id}/${item.currency}`} value={`${item.supplier_id}/${item.currency}`}>{item.supplier_name} · {item.currency} · Disponible {item.balance}</option>)}</CustomSelect></label>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{ledger && <><p className="text-sm">{ledger.supplier_name} · Saldo disponible: {ledger.currency} {ledger.available}</p><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Fecha", "Origen", "Referencia", "Importe", "Disponible", "Vinculación"].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{ledger.lots.map(item => <tr key={item.movement_id} className="border-t"><td className="p-2">{item.date}</td><td className="p-2">{names[item.kind]}</td><td className="p-2">{item.reference}</td><td className="p-2">{item.amount}</td><td className="p-2">{item.remaining}</td><td className="p-2">{item.claim_code || (item.source_document_id ? `Compra ${item.source_document_id.substring(0, 8).toUpperCase()}` : "Sin compra específica")}{item.kind === "advance" && item.source_document_id && <p className="text-xs text-slate-500">Aplicable a la compra vinculada</p>}</td></tr>)}</tbody></table></div><details><summary className="cursor-pointer text-sm font-medium">Movimientos y créditos utilizados</summary><ul className="mt-2 space-y-3 text-sm">{ledger.movements.map(item => <li key={item.id} className="rounded-lg border p-3">{item.date} · {names[item.kind]} · {item.reference} · {ledger.currency} {item.amount}<p className="text-slate-500">{item.notes}</p>{item.allocations.map(allocation => <p key={allocation.movement_id} className="text-xs">Origen {allocation.reference}{allocation.claim_code ? ` · ${allocation.claim_code}` : ""} · {allocation.amount}</p>)}</li>)}</ul></details></>}</section>;
}
