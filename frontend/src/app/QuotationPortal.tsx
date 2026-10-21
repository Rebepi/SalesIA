import { FormEvent, useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { useConfirm } from "../ui/components/ConfirmDialog";

interface Proposal {
  company_name: string;
  quotation_number: string;
  version: number;
  currency: string;
  total_amount: string;
  subtotal_amount: string;
  tax_amount: string;
  status: string;
  valid_until?: string;
  payment_terms_days: number;
  delivery_terms?: string;
  notes?: string;
  special_conditions?: string;
  lines: Array<{ product_id: string; sku?: string; name?: string; product_name?: string; quantity: string; total_amount?: string; line_total?: string }>;
}

export function QuotationPortal({ quotationId }: { quotationId: string }) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [token] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get("quotation-token") || "");
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const endpoint = `${apiClient.getBaseUrl()}/api/v1/quotation-portal/${encodeURIComponent(quotationId)}`;

  async function request(path: string, options: RequestInit = {}) {
    const response = await fetch(`${endpoint}${path}`, { ...options, headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, cache: "no-store", referrerPolicy: "no-referrer" });
    if (!response.ok) { const problem = await response.json().catch(() => ({})); throw new Error(problem.detail || "No se pudo abrir la propuesta. Solicita un enlace vigente a tu vendedor."); }
    return response;
  }

  async function load() {
    setLoading(true);
    setError("");
    try { setProposal(await (await request("")).json()); }
    catch (failure) { setError((failure as Error).message); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  async function accept(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    if (!await confirm({ title: "¿Aceptar cotización?", text: "Confirmarás la aceptación de esta versión de la cotización y sus términos comerciales.", confirmLabel: "Aceptar" })) return;
    setBusy(true);
    setError("");
    try { await request("/accept", { method: "POST", body: JSON.stringify({ accepted_by: String(data.get("accepted_by") || ""), conditions_accepted: data.get("conditions_accepted") === "on" }) }); await load(); }
    catch (failure) { setError((failure as Error).message); }
    finally { setBusy(false); }
  }
  async function download() {
    setBusy(true);
    try { const response = await request("/pdf"); const url = URL.createObjectURL(await response.blob()); const anchor = document.createElement("a"); anchor.href = url; anchor.download = `${proposal?.quotation_number || "cotizacion"}.pdf`; anchor.click(); URL.revokeObjectURL(url); }
    catch (failure) { setError((failure as Error).message); }
    finally { setBusy(false); }
  }
  const money = (value: string) => new Intl.NumberFormat("es-PE", { style: "currency", currency: proposal?.currency || "PEN" }).format(Number(value));
  const expired = proposal?.valid_until ? new Date(proposal.valid_until).getTime() < Date.now() : false;

  return <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900"><article className="mx-auto max-w-3xl space-y-6 rounded-3xl border bg-white p-5 shadow-sm sm:p-10">{loading && <p role="status">Cargando propuesta…</p>}{error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}<button type="button" onClick={load} className="ml-3 underline">Reintentar</button></div>}{proposal && <><header className="border-b pb-5"><p className="text-sm font-semibold text-teal-700">{proposal.company_name}</p><h1 className="mt-2 text-2xl font-bold">Cotización {proposal.quotation_number}</h1><p className="text-sm text-slate-500">Versión {proposal.version} · {proposal.valid_until ? `Válida hasta ${new Date(proposal.valid_until).toLocaleDateString("es-PE", { timeZone: "America/Lima" })}` : "Consulta la vigencia con tu vendedor"}</p></header><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="py-2">Producto</th><th className="py-2 text-right">Cantidad</th></tr></thead><tbody>{proposal.lines.map((line, index) => <tr key={`${line.product_id}-${index}`} className="border-t"><td className="py-3">{line.name || line.product_name || line.sku || "Artículo cotizado"}<span className="block text-xs text-slate-500">{line.sku}</span></td><td className="py-3 text-right">{line.quantity}</td></tr>)}</tbody></table></div><dl className="ml-auto grid max-w-xs grid-cols-2 gap-2 text-sm"><dt>Subtotal</dt><dd className="text-right">{money(proposal.subtotal_amount)}</dd><dt>Impuestos</dt><dd className="text-right">{money(proposal.tax_amount)}</dd><dt className="font-bold">Total</dt><dd className="text-right text-xl font-bold">{money(proposal.total_amount)}</dd></dl><section className="space-y-2 rounded-xl bg-slate-50 p-4 text-sm"><h2 className="font-bold">Términos comerciales</h2><p>Pago: {proposal.payment_terms_days ? `${proposal.payment_terms_days} días de crédito` : "Al contado"}</p>{proposal.delivery_terms && <p>Entrega: {proposal.delivery_terms}</p>}{proposal.notes && <p>Notas: {proposal.notes}</p>}{proposal.special_conditions && <p>Condiciones especiales: {proposal.special_conditions}</p>}</section><button type="button" onClick={download} disabled={busy} className="rounded-xl border px-4 py-2 text-sm font-semibold">Descargar PDF</button>{["accepted", "converted"].includes(proposal.status) ? <p role="status" className="rounded-xl bg-emerald-50 p-4 text-sm font-semibold text-emerald-800">Esta cotización ya fue aceptada. Tu vendedor continuará con el pedido.</p> : expired ? <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900">Esta propuesta ha vencido. Solicita una versión actualizada a tu vendedor.</p> : <form onSubmit={accept} className="space-y-3 border-t pt-5"><h2 className="font-bold">Aceptar propuesta</h2><label className="block text-sm">Nombre de quien acepta<input name="accepted_by" minLength={2} maxLength={200} required className="mt-1 w-full rounded-xl border p-3" autoComplete="name" /></label><label className="flex items-start gap-2 text-sm"><input type="checkbox" name="conditions_accepted" required className="mt-1" />He revisado los productos, importes y términos comerciales de esta versión.</label><button type="submit" disabled={busy} className="rounded-xl bg-teal-700 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">{busy ? "Registrando…" : "Aceptar cotización"}</button></form>}</>}</article>{ConfirmDialogNode}</main>;
}
