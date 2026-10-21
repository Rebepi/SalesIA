import { selectorSeed } from "../../../api/selectorSeed";
import { FormEvent, useEffect, useState } from "react";
import { apiClient } from "../../../api/client";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { ModalSurface } from "../../../ui/components/ModalSurface";

export function InsightActionsDialog({ ids, onClose, onSaved }: { ids: string[]; onClose: () => void; onSaved: () => void }) {
  const [action, setAction] = useState("task");
  const [members, setMembers] = useState<Array<{ id: string; name: string; email: string }>>([]);
  const [assignee, setAssignee] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { selectorSeed<{ id: string; name: string; email: string }>("people", { active_only: "true" }).then(result => setMembers(result)).catch(() => setError("No se pudieron cargar los responsables. Puedes usar las otras acciones o volver a abrir el formulario.")); }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      await apiClient.request("/api/v1/insights/bulk-actions", { method: "POST", body: JSON.stringify({ ids, action, assignee_id: action === "task" ? assignee : undefined, due_date: action === "task" ? new Date(String(data.get("date"))).toISOString() : undefined, snoozed_until: action === "snooze" ? new Date(String(data.get("date"))).toISOString() : undefined, priority: String(data.get("priority") || "normal"), notes: String(data.get("notes") || "") }) });
      onSaved();
    } catch (failure: unknown) { setError(String((failure as { detail?: string }).detail || "No se pudo completar la acción. Revisa los datos y vuelve a intentar.")); }
    finally { setBusy(false); }
  }
  return <ModalSurface labelledBy="insight-actions-title" onClose={onClose} blocked={busy}><form onSubmit={submit} className="app-modal-panel w-[min(90vw,540px)] space-y-4 rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"><h3 id="insight-actions-title" className="font-bold">Gestionar {ids.length} alertas seleccionadas</h3><label className="block text-xs font-semibold">Acción<CustomSelect value={action} onChange={event => setAction(event.target.value)} className="mt-1 w-full rounded-xl border p-2.5"><option value="task">Crear tareas y asignar</option><option value="read">Marcar leídas</option><option value="snooze">Posponer</option><option value="dismiss">Descartar</option><option value="resolve">Cerrar como resueltas</option></CustomSelect></label>{action === "task" && <><label className="block text-xs font-semibold">Responsable<CustomSelect remote={{ resource: "people", active_only: true }} searchable value={assignee} onChange={event => setAssignee(event.target.value)} required className="mt-1 w-full rounded-xl border p-2.5"><option value="">Seleccionar responsable</option>{members.map(member => <option key={member.id} value={member.id}>{member.name} · {member.email}</option>)}</CustomSelect></label><label className="block text-xs font-semibold">Prioridad<CustomSelect name="priority" defaultValue="normal" className="mt-1 w-full rounded-xl border p-2.5"><option value="low">Baja</option><option value="normal">Normal</option><option value="high">Alta</option><option value="urgent">Urgente</option></CustomSelect></label></>}{["task", "snooze"].includes(action) && <label className="block text-xs font-semibold">{action === "task" ? "Fecha de vencimiento" : "Volver a mostrar a partir de"}<input name="date" type="datetime-local" required className="mt-1 w-full rounded-xl border p-2.5 dark:bg-slate-950" /></label>}<label className="block text-xs font-semibold">Motivo o instrucciones<textarea name="notes" maxLength={2000} required={["dismiss", "resolve"].includes(action)} className="mt-1 w-full rounded-xl border p-2.5 dark:bg-slate-950" /></label>{error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-xs text-red-800">{error}</p>}<p className="text-xs text-slate-500">Las tareas conservan el enlace al registro afectado. Una alerta con una tarea activa reutiliza esa tarea para evitar duplicados.</p><footer className="flex justify-end gap-2"><button type="button" onClick={onClose} disabled={busy} className="rounded-xl border px-4 py-2 text-xs">Cancelar</button><button type="submit" disabled={busy || action === "task" && !assignee} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy ? "Aplicando…" : "Aplicar acción"}</button></footer></form></ModalSurface>;
}
