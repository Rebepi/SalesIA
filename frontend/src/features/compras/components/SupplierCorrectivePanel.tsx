import { useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

export interface CorrectiveTask { id: string; title: string; status: string; due_date: string | null; version: number; resolution_notes: string | null; can_edit: boolean }

export function SupplierCorrectivePanel({ supplierId, tasks, canWrite, onChanged }: { supplierId: string; tasks: CorrectiveTask[]; canWrite: boolean; onChanged: () => void }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const input = "mt-1 w-full rounded-lg border p-2 text-sm";
  async function write(path: string, payload: unknown, method: string) {
    if (sending.current) return;
    sending.current = true;
    setBusy(true);
    setError("");
    const body = JSON.stringify(payload);
    const key = keys.current.get(`${path}:${body}`) || crypto.randomUUID();
    keys.current.set(`${path}:${body}`, key);
    try { await apiClient.request(path, { method, body, headers: { "Idempotency-Key": key } }); keys.current.delete(`${path}:${body}`); onChanged(); }
    catch (cause) { const detail = (cause as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : "No se pudo registrar el compromiso correctivo."); }
    finally { sending.current = false; setBusy(false); }
  }
  function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = Object.fromEntries(new FormData(event.currentTarget));
    void write(`/api/v1/suppliers/${supplierId}/corrective-tasks`, { ...fields, due_date: new Date(String(fields.due_date)).toISOString() }, "POST");
  }
  return <section className="mt-4 space-y-3 border-t pt-4"><h4 className="font-semibold">Compromisos correctivos y verificación</h4>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{tasks.map(task => <article key={task.id} className="space-y-2 rounded-lg border p-3 text-sm"><strong>{task.title}</strong><p>{task.status} · {task.due_date ? new Date(task.due_date).toLocaleString("es-PE") : "Sin plazo"}</p>{task.resolution_notes && <p>{task.resolution_notes}</p>}{canWrite && task.can_edit && !["completed", "cancelled"].includes(task.status) && <><label className="block text-xs">Resultado verificado<input className={input} value={notes[task.id] || ""} minLength={5} maxLength={2000} onChange={event => setNotes(previous => ({ ...previous, [task.id]: event.target.value }))} /></label><button type="button" disabled={busy || (notes[task.id] || "").trim().length < 5} className="rounded-lg border px-3 py-2 text-xs disabled:opacity-50" onClick={() => void write(`/api/v1/collaboration/tasks/${task.id}`, { version: task.version, status: "completed", resolution_notes: notes[task.id] }, "PATCH")}>Registrar revisión y completar</button></>}</article>)}{canWrite && <form onSubmit={create} className="space-y-2"><label className="block text-xs">Compromiso<input className={input} name="title" required minLength={5} maxLength={255} /></label><label className="block text-xs">Acción acordada y evidencia esperada<textarea className={input} name="description" required minLength={5} maxLength={2000} /></label><label className="block text-xs">Revisar antes de<input className={input} name="due_date" type="datetime-local" required /></label><button disabled={busy} className="rounded-lg border px-3 py-2 text-xs" type="submit">Crear seguimiento a mi cargo</button></form>}</section>;
}
