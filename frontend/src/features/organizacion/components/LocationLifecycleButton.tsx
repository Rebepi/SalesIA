import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Preview = { id: string; name: string; code: string; is_active: boolean; can_retire: boolean; can_reactivate: boolean; preview_hash: string; checks: { code: string; label: string; count: number; blocking: boolean; guidance: string }[]; effects: string[]; warehouses_to_retire: { id: string; code: string; name: string }[] };
const button = "rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs disabled:opacity-50";
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : typeof detail === "object" && detail && "message" in detail ? String(detail.message) : "No se pudo completar la revisión. Actualice los pendientes antes de reintentar."; }

export function LocationLifecycleButton({ kind, identifier, isActive, onChanged }: { kind: "branch" | "warehouse"; identifier: string; isActive: boolean; onChanged: () => void | Promise<void> }) {
  const [open, setOpen] = useState(false);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { if (open) dialog.current?.showModal(); else dialog.current?.close(); }, [open]);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setPreview(null); setError("");
    void apiClient.request<Preview>(`/api/v1/organization/locations/${kind}/${identifier}/retirement`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) setPreview(result); }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [open, kind, identifier, revision]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!preview || lock.current) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const action = preview.is_active ? "retirement" : "reactivation";
    const body = JSON.stringify({ preview_hash: preview.preview_hash, reason: values.reason });
    const signature = `${action}:${identifier}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID(); keys.current.set(signature, key);
    lock.current = true; setBusy(true); setError("");
    try { await apiClient.request(`/api/v1/organization/locations/${kind}/${identifier}/${action}`, { method: "POST", headers: { "Idempotency-Key": key }, body }); setOpen(false); await onChanged(); }
    catch (cause) { setError(problem(cause)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <><button type="button" className={button} onClick={() => setOpen(true)}>{isActive ? "Revisar retiro" : "Reactivar"}</button><dialog ref={dialog} onCancel={event => { event.preventDefault(); if (!busy) setOpen(false); }} className="max-h-[90vh] w-[min(900px,95vw)] overflow-auto rounded-xl p-5 text-slate-800 shadow-xl backdrop:bg-slate-900/40"><div className="mb-4 flex justify-between gap-3"><h3 className="font-semibold">{isActive ? "Retiro asistido" : "Reactivación"} de {kind === "branch" ? "sede" : "almacén"}</h3><button type="button" className={button} disabled={busy} onClick={() => setOpen(false)}>Cerrar</button></div>{error && <p role="alert" className="mb-3 text-sm text-red-700">{error}</p>}{!preview && !error && <p role="status">Consultando existencias y documentos pendientes…</p>}{preview && <form className="space-y-4" onSubmit={submit}><strong>{preview.code} · {preview.name}</strong>{preview.is_active ? <><p className="text-sm">Resuelva cada pendiente desde su módulo. El retiro vuelve a comprobar esta información al guardar.</p><div className="space-y-2">{preview.checks.map(check => <article key={check.code} className={`rounded border p-3 text-sm ${check.blocking ? "border-amber-300 bg-amber-50" : "border-slate-200"}`}><strong>{check.label}: {check.count}</strong>{check.blocking && <p>{check.guidance}</p>}</article>)}</div><ul className="list-inside list-disc text-sm">{preview.effects.map(effect => <li key={effect}>{effect}</li>)}</ul>{preview.warehouses_to_retire.length > 0 && <p className="text-sm">Almacenes que se desactivarán: {preview.warehouses_to_retire.map(item => `${item.code} (${item.name})`).join(", ")}.</p>}</> : <p className="text-sm">{preview.can_reactivate ? "Se habilitará esta ubicación para nuevas operaciones. Los almacenes, fondos y franjas desactivados se habilitan por separado." : "Reactive primero la sede a la que pertenece este almacén."}</p>}<label className="grid gap-1 text-sm">Motivo<textarea name="reason" minLength={5} maxLength={2000} required disabled={busy} className="rounded-lg border p-2" /></label><div className="flex flex-wrap gap-3"><button className={button} disabled={busy || (preview.is_active ? !preview.can_retire : !preview.can_reactivate)}>{preview.is_active ? "Desactivar ubicación sin pendientes" : "Reactivar ubicación"}</button><button type="button" className={button} disabled={busy} onClick={() => setRevision(value => value + 1)}>Actualizar revisión</button></div></form>}</dialog></>;
}
