import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Task = { id: string; title: string; description: string | null; status: string; assignee_id: string | null; creator_id: string; due_date: string | null; priority: string; parent_id: string | null; version: number; checklist: { title: string; done: boolean }[]; dependencies: string[]; resolution_notes?: string | null };
type Series = { id: string; title: string; is_active: boolean; next_due_at: string | null; schedule: { frequency: string; interval: number; timezone: string } };
const states: Record<string, string> = { pending: "Pendiente", in_progress: "En curso", completed: "Completada", cancelled: "Cancelada" };
const input = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
const button = "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 disabled:opacity-50";

function localDateTime(value: string | null) {
  if (!value) return "";
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Lima", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(value));
  const part = (type: string) => parts.find(item => item.type === type)?.value || "";
  return `${part("year")}-${part("month")}-${part("day")}T${part("hour")}:${part("minute")}`;
}

export function TaskPlanningBoard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [series, setSeries] = useState<Series[]>([]);
  const [members, setMembers] = useState<{ id: string; name: string }[]>([]);
  const [userId, setUserId] = useState("");
  const [canManage, setCanManage] = useState(false);
  const [person, setPerson] = useState("");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<Task | null>(null);
  const [open, setOpen] = useState(false);
  const [recurring, setRecurring] = useState(false);
  const [checklist, setChecklist] = useState<{ title: string; done: boolean }[]>([]);
  const [dependencies, setDependencies] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);
  const lock = useRef(false);
  const pendingKeys = useRef(new Map<string, string>());
  function problem(failure: unknown) { const detail = (failure as { detail?: unknown }).detail; return typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo completar la operación."; }
  async function load() {
    setLoading(true);
    setError("");
    try {
      const [result, seriesResult, memberResult, profile] = await Promise.all([apiClient.request<{ items: Task[] }>("/api/v1/collaboration/tasks"), apiClient.request<Series[]>("/api/v1/collaboration/task-series"), apiClient.request<{ items: { id: string; name: string }[] }>("/api/v1/collaboration/members"), apiClient.getMe()]);
      setTasks(result.items);
      setSeries(seriesResult);
      setMembers(memberResult.items);
      setUserId(profile.user_id);
      setCanManage(Boolean(profile.permissions?.includes("operations:manage") || profile.permissions?.includes("approvals:manage") || ["company_admin", "manager", "platform_admin"].includes(profile.role)));
    } catch (failure) { setError(problem(failure)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  useEffect(() => { if (open) dialog.current?.showModal(); else dialog.current?.close(); }, [open]);
  function edit(task: Task | null) { setEditing(task); setRecurring(false); setChecklist(task?.checklist || []); setDependencies(task?.dependencies || []); setOpen(true); setError(""); }
  async function write(path: string, body: unknown, method = "POST") {
    if (lock.current) return false;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const signature = JSON.stringify({ path, body, method });
    const key = pendingKeys.current.get(signature) || crypto.randomUUID();
    pendingKeys.current.set(signature, key);
    try { await apiClient.request(path, { method, body: JSON.stringify(body), headers: { "Idempotency-Key": key } }); pendingKeys.current.delete(signature); await load(); setNotice("Cambios registrados."); return true; }
    catch (failure) { setError(problem(failure)); return false; }
    finally { lock.current = false; setBusy(false); }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    const body = { title: values.title, description: values.description || null, assignee_id: values.assignee_id || null, due_date: values.due_date ? new Date(`${values.due_date}:00-05:00`).toISOString() : null, priority: values.priority, parent_id: values.parent_id || null, checklist, dependencies };
    let success: boolean;
    if (editing) success = await write(`/api/v1/collaboration/tasks/${editing.id}`, { ...body, version: editing.version, status: values.status, resolution_notes: values.resolution_notes || null }, "PATCH");
    else if (recurring) success = await write("/api/v1/collaboration/task-series", { task: body, frequency: values.frequency, interval: Number(values.interval || 1), timezone: "America/Lima", until: values.until || null, skip_dates: (values.skip_dates || "").split(",").map(value => value.trim()).filter(Boolean) });
    else success = await write("/api/v1/collaboration/tasks", body);
    if (success) setOpen(false);
  }
  const visible = tasks.filter(task => (!person || task.assignee_id === person) && `${task.title} ${task.description || ""}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
  return <section className="mt-6 space-y-5 rounded-2xl border border-slate-200 bg-white p-5 text-slate-900"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold">Planificación, subtareas y actividades periódicas</h2><p className="mt-1 text-sm text-slate-500">Las listas de comprobación y dependencias se validan antes de completar una actividad.</p></div><div className="flex gap-2"><button type="button" className={button} disabled={loading || busy} onClick={() => void load()}>Actualizar</button><button type="button" className={button} disabled={busy} onClick={() => edit(null)}>Nueva tarea</button></div></div>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-700">{notice}</p>}<div className="grid gap-3 sm:grid-cols-2"><label className="text-sm">Buscar<input className={input} value={query} onChange={event => setQuery(event.target.value)} /></label><label className="text-sm">Responsable<CustomSelect remote={{ resource: "people" }} className={input} value={person} onChange={event => setPerson(event.target.value)}><option value="">Todos los disponibles</option>{members.map(member => <option key={member.id} value={member.id}>{member.name}</option>)}</CustomSelect></label></div>{loading && <p role="status" className="text-sm">Cargando planificación…</p>}<div className="grid items-start gap-3 lg:grid-cols-4">{Object.entries(states).map(([state, label]) => <section key={state} className="space-y-3 rounded-xl bg-slate-50 p-3"><h3 className="text-sm font-semibold">{label} · {visible.filter(task => task.status === state).length}</h3>{visible.filter(task => task.status === state).map(task => <button key={task.id} type="button" className="w-full rounded-xl border bg-white p-3 text-left text-sm hover:border-teal-600" onClick={() => edit(task)}><strong>{task.title}</strong><p className="mt-2 text-xs text-slate-500">{members.find(member => member.id === task.assignee_id)?.name || "Sin asignar"}</p>{task.due_date && <p className={`mt-1 text-xs ${new Date(task.due_date).getTime() < Date.now() && !["completed", "cancelled"].includes(task.status) ? "text-red-700" : "text-slate-500"}`}>{new Date(task.due_date).toLocaleString("es-PE", { timeZone: "America/Lima" })}</p>}{task.parent_id && <p className="mt-1 text-xs text-slate-500">Subtarea de {tasks.find(parent => parent.id === task.parent_id)?.title || "otra actividad"}</p>}{task.checklist?.length > 0 && <p className="mt-1 text-xs">{task.checklist.filter(item => item.done).length}/{task.checklist.length} comprobaciones</p>}{task.dependencies?.length > 0 && <p className="mt-1 text-xs">{task.dependencies.length} dependencias</p>}</button>)}</section>)}</div><details className="rounded-xl border p-4"><summary className="cursor-pointer font-medium">Series periódicas · {series.length}</summary><div className="mt-3 space-y-3">{series.map(item => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3 text-sm"><div><strong>{item.title}</strong><p className="mt-1 text-xs text-slate-500">{({ daily: "Días", weekly: "Semanas", monthly: "Meses" } as Record<string, string>)[item.schedule.frequency]}: cada {item.schedule.interval} · {item.is_active ? "Activa" : "Pausada o finalizada"}</p><p className="text-xs">{item.next_due_at ? `Próxima: ${new Date(item.next_due_at).toLocaleString("es-PE", { timeZone: "America/Lima" })}` : "Sin más ocurrencias"}</p></div>{item.next_due_at && <button type="button" className={button} disabled={busy} onClick={() => void write(`/api/v1/collaboration/task-series/${item.id}/${item.is_active ? "pause" : "resume"}`, {})}>{item.is_active ? "Pausar" : "Reanudar"}</button>}</div>)}</div></details>
    <dialog ref={dialog} onCancel={event => { event.preventDefault(); if (!busy) setOpen(false); }} className="max-h-[90vh] w-[min(95vw,800px)] rounded-2xl bg-white p-5 text-slate-900 shadow-xl backdrop:bg-slate-950/60"><div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">{editing ? "Detalle de tarea" : "Nueva actividad"}</h2><button type="button" className={button} disabled={busy} onClick={() => setOpen(false)}>Cerrar</button></div>{error && <p role="alert" className="mb-3 text-sm text-red-700">{error}</p>}{open && <form key={editing?.id || "new"} onSubmit={submit} className="space-y-4"><fieldset disabled={busy || Boolean(editing && !canManage && editing.creator_id !== userId && editing.assignee_id !== userId)} className="space-y-4"><label className="block text-sm">Título<input className={input} name="title" required maxLength={255} defaultValue={editing?.title} /></label><label className="block text-sm">Descripción<textarea className={input} name="description" maxLength={2000} defaultValue={editing?.description || ""} /></label><div className="grid gap-3 sm:grid-cols-2"><label className="text-sm">Responsable<CustomSelect remote={{ resource: "people" }} className={input} name="assignee_id" defaultValue={editing?.assignee_id || userId}><option value="">Sin asignar</option>{members.map(member => <option key={member.id} value={member.id}>{member.name}</option>)}</CustomSelect></label><label className="text-sm">Vencimiento, hora de Lima<input className={input} name="due_date" type="datetime-local" required={recurring} defaultValue={localDateTime(editing?.due_date || null)} /></label><label className="text-sm">Prioridad<select className={input} name="priority" defaultValue={editing?.priority || "normal"}><option value="low">Baja</option><option value="normal">Normal</option><option value="high">Alta</option><option value="urgent">Urgente</option></select></label>{editing ? <label className="text-sm">Estado<select className={input} name="status" defaultValue={editing.status}>{Object.entries(states).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label> : <label className="text-sm">Subtarea de<select className={input} name="parent_id"><option value="">Actividad independiente</option>{tasks.filter(task => !["completed", "cancelled"].includes(task.status)).map(task => <option key={task.id} value={task.id}>{task.title}</option>)}</select></label>}</div><label className="block text-sm">Debe completarse después de<select className={`${input} min-h-24`} multiple value={dependencies} onChange={event => setDependencies(Array.from(event.target.selectedOptions).map(option => option.value))}>{tasks.filter(task => task.id !== editing?.id).map(task => <option key={task.id} value={task.id}>{task.title} · {states[task.status]}</option>)}</select></label><fieldset className="space-y-2 rounded-xl border p-3"><legend className="px-2 text-sm">Lista de comprobación</legend>{checklist.map((item, index) => <div key={index} className="flex items-center gap-2"><input type="checkbox" aria-label={`Completar comprobación ${index + 1}`} checked={item.done} onChange={event => setChecklist(rows => rows.map((row, position) => position === index ? { ...row, done: event.target.checked } : row))} /><input className={input} required maxLength={255} aria-label={`Título comprobación ${index + 1}`} value={item.title} onChange={event => setChecklist(rows => rows.map((row, position) => position === index ? { ...row, title: event.target.value } : row))} /><button type="button" className={button} onClick={() => setChecklist(rows => rows.filter((_, position) => position !== index))}>Quitar</button></div>)}<button type="button" className={button} disabled={checklist.length >= 100} onClick={() => setChecklist(rows => [...rows, { title: "", done: false }])}>Agregar comprobación</button></fieldset>{editing && <label className="block text-sm">Resultado o motivo de reapertura<textarea className={input} name="resolution_notes" defaultValue={editing.resolution_notes || ""} /></label>}{!editing && <><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={recurring} onChange={event => setRecurring(event.target.checked)} />Crear una serie periódica</label>{recurring && <div className="grid gap-3 rounded-xl border p-4 sm:grid-cols-2"><label className="text-sm">Frecuencia<select className={input} name="frequency"><option value="daily">Diaria</option><option value="weekly">Semanal</option><option value="monthly">Mensual</option></select></label><label className="text-sm">Cada cuántos períodos<input className={input} name="interval" type="number" min="1" max="365" defaultValue="1" required /></label><label className="text-sm">Termina el<input className={input} name="until" type="date" /></label><label className="text-sm">Fechas que se omiten<textarea className={input} name="skip_dates" placeholder="2026-12-25, 2027-01-01" /></label><p className="text-xs text-slate-500 sm:col-span-2">El proceso interno de trabajos genera las ocurrencias y conserva cada actividad por separado.</p></div>}</>}<button className={button} disabled={busy}>Guardar actividad</button></fieldset></form>}</dialog>
  </section>;
}
