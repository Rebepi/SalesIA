import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { ModalSurface } from "../../../ui/components/ModalSurface";

interface Document { id: string; file_name: string }
interface Qualification { id: string; legal_name: string; status: string; version: number; valid_until: string | null; can_create_commitments: boolean; documents: Document[]; available_documents: Document[]; history: { action: string; status: string; actor: string; at: string; reason: string }[]; existing_orders: { id: string; status: string }[] }

export function SupplierQualificationDialog({ supplierId, canWrite, onClose, onChanged }: { supplierId: string; canWrite: boolean; onClose: () => void; onChanged: () => void }) {
  const [data, setData] = useState<Qualification | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const input = "mt-1 w-full rounded-lg border bg-white p-2 text-sm";
  const button = "rounded-lg border px-3 py-2 text-sm disabled:opacity-50";

  async function load() { const result = await apiClient.request<Qualification>(`/api/v1/suppliers/${supplierId}/qualification`); setData(result); setSelected(result.documents.map(item => item.id)); }
  useEffect(() => { void load().catch(() => setError("No se pudo consultar la homologación del proveedor.")); }, [supplierId]);

  function problem(cause: unknown) { const detail = (cause as { detail?: unknown }).detail; return typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "No se pudo completar la operación."; }

  async function upload(files: FileList | null) {
    if (!files || sending.current) return;
    sending.current = true;
    setBusy(true);
    setError("");
    const added: string[] = [];
    try {
      for (const file of Array.from(files)) {
        if (!["application/pdf", "image/png", "image/jpeg"].includes(file.type)) throw new Error("Selecciona documentos PDF o imágenes PNG/JPG.");
        const intent = await apiClient.request<{ attachment_id: string; upload_url: string; upload_token: string }>("/api/v1/attachments/upload-intents", { method: "POST", body: JSON.stringify({ file_name: file.name, mime_type: file.type, file_size_bytes: file.size, related_entity_type: "supplier", related_entity_id: supplierId }) });
        await apiClient.request(intent.upload_url, { method: "PUT", headers: { "Content-Type": file.type, "X-Upload-Token": intent.upload_token }, body: await file.arrayBuffer() });
        await apiClient.request(`/api/v1/attachments/${intent.attachment_id}/complete`, { method: "POST", body: "{}" });
        added.push(intent.attachment_id);
      }
      await load();
      setSelected(previous => [...new Set([...previous, ...added])]);
    } catch (cause) { setError(problem(cause)); }
    finally { sending.current = false; setBusy(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!data || sending.current) return;
    const fields = Object.fromEntries(new FormData(event.currentTarget));
    const body = JSON.stringify({ ...fields, version: data.version, valid_until: fields.valid_until || null, attachment_ids: selected });
    const key = keys.current.get(body) || crypto.randomUUID();
    keys.current.set(body, key);
    sending.current = true;
    setBusy(true);
    setError("");
    try {
      await apiClient.request(`/api/v1/suppliers/${supplierId}/qualification`, { method: "POST", headers: { "Idempotency-Key": key }, body });
      keys.current.delete(body);
      await load();
      setNotice("Evaluación registrada con responsable, motivo y documentos.");
      onChanged();
    } catch (cause) { setError(problem(cause)); }
    finally { sending.current = false; setBusy(false); }
  }

  return <ModalSurface labelledBy="supplier-qualification-title" blocked={busy} onClose={onClose}><section className="app-modal-panel max-h-[90vh] w-full max-w-3xl space-y-4 overflow-y-auto rounded-2xl bg-white p-5 text-slate-900"><header className="flex justify-between gap-3"><h2 id="supplier-qualification-title" className="text-lg font-semibold">Evaluación y homologación de proveedor</h2><button className={button} disabled={busy} type="button" onClick={onClose}>Cerrar</button></header>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}{data && <><h3 className="font-semibold">{data.legal_name}</h3><p className="text-sm">{data.status} · v{data.version} · Vigencia: {data.valid_until || "Histórica sin vencimiento registrado"}</p><p className="rounded-lg bg-slate-50 p-3 text-sm">{data.can_create_commitments ? "El proveedor admite nuevos compromisos." : "El proveedor requiere evaluación vigente para nuevas compras. Las órdenes ya comprometidas pueden continuar su recepción."}</p>{canWrite && <><label className="block text-sm">Documentos internos<input className={input} type="file" accept="application/pdf,image/png,image/jpeg" multiple disabled={busy} onChange={event => void upload(event.target.files)} /></label><form className="space-y-3" key={data.version} onSubmit={event => void submit(event)}><fieldset disabled={busy} className="space-y-3"><div className="grid gap-3 sm:grid-cols-2"><label className="text-sm">Acción<select name="action" className={input}><option value="evaluate">Registrar evaluación pendiente</option><option value="approve">Aprobar homologación</option><option value="suspend">Suspender nuevos compromisos</option><option value="reject">Rechazar homologación</option></select></label><label className="text-sm">Vigencia de la aprobación<input className={input} name="valid_until" type="date" defaultValue={data.valid_until || ""} /></label></div><label className="block text-sm">Evaluación y motivo<textarea className={input} name="reason" required minLength={5} maxLength={4000} /></label><fieldset className="space-y-2 rounded-lg border p-3"><legend className="px-2 text-sm">Evidencia de esta decisión</legend>{data.available_documents.map(item => <label key={item.id} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={selected.includes(item.id)} onChange={event => setSelected(previous => event.target.checked ? [...previous, item.id] : previous.filter(id => id !== item.id))} />{item.file_name}</label>)}{data.available_documents.length === 0 && <p className="text-sm text-slate-500">Sin documentos verificados vinculados.</p>}</fieldset><button type="submit" className={button} disabled={busy}>Registrar decisión</button></fieldset></form></>}<details className="rounded-lg border p-3"><summary className="cursor-pointer text-sm font-semibold">Órdenes existentes ({data.existing_orders.length})</summary><ul className="mt-2 text-sm">{data.existing_orders.map(order => <li key={order.id}>{order.id.slice(0, 8).toUpperCase()} · {order.status}</li>)}</ul></details><section className="space-y-2"><h3 className="font-semibold">Historial de evaluación</h3>{data.history.map((item, index) => <article className="rounded-lg border p-3 text-sm" key={index}><strong>{item.action} · {item.status}</strong><p>{item.reason}</p><p className="mt-1 text-xs text-slate-500">{item.actor} · {new Date(item.at).toLocaleString("es-PE")}</p></article>)}</section></>}</section></ModalSurface>;
}
