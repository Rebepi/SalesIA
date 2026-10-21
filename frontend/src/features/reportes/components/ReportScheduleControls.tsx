import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { ReportScheduleBuilder } from "./ReportScheduleBuilder";
import type { ReportScheduleConfig } from "./ReportScheduleBuilder";
import type { ReportScheduleItem } from "../types/ReportsWorkspaceTab";

const input = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
const button = "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 disabled:opacity-50";

export function ReportScheduleControls({ schedule, onSaved }: { schedule: ReportScheduleItem; onSaved: () => void }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [config, setConfig] = useState<ReportScheduleConfig>(() => schedule.schedule || { frequency: "daily", hour: 8, minute: 0, weekday: 1, day: 1, start_date: new Date().toISOString().slice(0, 10) });
  const dialog = useRef<HTMLDialogElement>(null);
  const lock = useRef(false);
  useEffect(() => { if (open) dialog.current?.showModal(); else dialog.current?.close(); }, [open]);
  async function save(body: unknown) {
    if (lock.current) return false;
    lock.current = true;
    setBusy(true);
    setError("");
    try { await apiClient.request(`/api/v1/report-schedules/${schedule.schedule_id}`, { method: "PATCH", body: JSON.stringify({ version: schedule.version || 1, ...(body as object) }) }); onSaved(); return true; }
    catch (failure) { const detail = (failure as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo cambiar la programación."); return false; }
    finally { lock.current = false; setBusy(false); }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const recipients = [...new Set(String(data.get("recipients") || "").split(/[;,\n]/).map(email => email.trim().toLowerCase()).filter(Boolean))];
    if (await save({ schedule: config, recipients, timezone: String(data.get("timezone")), format: String(data.get("format")) })) setOpen(false);
  }
  return <div className="mt-3 space-y-2">{error && <p role="alert" className="text-xs text-red-700">{error}</p>}<div className="flex flex-wrap gap-2"><button className={button} type="button" disabled={busy} onClick={() => void save({ is_active: !schedule.is_active })}>{schedule.is_active ? "Pausar" : "Reanudar"}</button><button className={button} type="button" disabled={busy} onClick={() => setOpen(true)}>Editar programación</button>{schedule.next_run_at && <p className="w-full text-xs text-slate-500">Próxima ejecución: {new Date(schedule.next_run_at).toLocaleString("es-PE", { timeZone: schedule.timezone })}</p>}</div><dialog ref={dialog} onCancel={event => { event.preventDefault(); if (!busy) setOpen(false); }} className="max-h-[90vh] w-[min(95vw,700px)] rounded-2xl bg-white p-5 text-slate-900 shadow-xl backdrop:bg-slate-950/60"><div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">Editar programación de reporte</h2><button type="button" className={button} disabled={busy} onClick={() => setOpen(false)}>Cerrar</button></div>{error && <p role="alert" className="mb-3 text-sm text-red-700">{error}</p>}{open && <form onSubmit={submit} className="space-y-4"><ReportScheduleBuilder value={config} onChange={setConfig} /><label className="block text-sm">Zona horaria<input className={input} name="timezone" required defaultValue={schedule.timezone} /></label><label className="block text-sm">Formato<select className={input} name="format" defaultValue={schedule.format}><option value="csv">CSV</option><option value="xlsx">Excel</option><option value="pdf">PDF</option><option value="json">JSON</option></select></label><label className="block text-sm">Correos de destinatarios internos<textarea className={input} name="recipients" defaultValue={schedule.recipient_emails.join(", ")} /><span className="mt-1 block text-xs text-slate-500">Deben pertenecer a miembros activos con acceso al reporte. Los archivos quedan en la bandeja del sistema. En blanco: responsable de la programación.</span></label><button className={button} disabled={busy}>Guardar programación</button></form>}</dialog></div>;
}
