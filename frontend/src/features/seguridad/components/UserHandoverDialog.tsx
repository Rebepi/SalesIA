import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";
import type { MemberItem } from "../types/UsersAndRolesWorkspaceTab";

type Group = { key: string; label: string; count: number; required_permissions: string[]; requires_sales_rep: boolean; samples: { id: string; name: string }[] };
type Review = { user_id: string; name: string; email: string; is_active: boolean; preview_hash: string; can_suspend: boolean; groups: Group[]; blockers: { code: string; label: string; count: number; guidance: string; samples: string[] }[]; effects: string[] };
type Candidate = Record<string, unknown> & { id: string; name: string; email: string; role: string };
const button = "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm disabled:opacity-50";
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : detail && typeof detail === "object" && "message" in detail ? String(detail.message) : "No se pudo consultar o completar el traspaso del usuario."; }

export function UserHandoverDialog({ member, onClose, onChanged }: { member: MemberItem; onClose: () => void; onChanged: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [review, setReview] = useState<Review | null>(null);
  const [recipients, setRecipients] = useState<Record<string, string>>({});
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [revision, setRevision] = useState(0);
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  useEffect(() => { dialog.current?.showModal(); return () => dialog.current?.close(); }, []);
  useEffect(() => {
    const controller = new AbortController();
    setReview(null); setRecipients({});
    void apiClient.request<Review>(`/api/v1/memberships/${member.id}/handover`, { signal: controller.signal }).then(row => { if (!controller.signal.aborted) setReview(row); }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [member.id, revision]);
  const pending = review?.groups.filter(group => group.count > 0) || [];
  const canSuspend = Boolean(review?.is_active && !review.blockers.length && pending.every(group => recipients[group.key]));
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!review || lock.current) return;
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    const action = submitter?.value === "suspend" ? "suspend" : "transfer";
    const transfers = Object.fromEntries(Object.entries(recipients).filter(([key, value]) => value && pending.some(group => group.key === key)));
    const body = JSON.stringify({ preview_hash: review.preview_hash, transfers, reason });
    const signature = `${member.id}:${action}:${body}`; const key = keys.current.get(signature) || crypto.randomUUID(); keys.current.set(signature, key);
    lock.current = true; setBusy(true); setError(""); setNotice("");
    try {
      const result = await apiClient.request<{ is_active: boolean; transferred: Record<string, number>; review: Review }>(`/api/v1/memberships/${member.id}/handover/${action}`, { method: "POST", headers: { "Idempotency-Key": key }, body });
      setReview(result.review); setRecipients({}); setReason(""); onChanged();
      if (!result.is_active) { onClose(); return; }
      setNotice(`Se traspasaron ${Object.values(result.transferred).reduce((sum, count) => sum + count, 0)} responsabilidades. Revise los pendientes restantes antes de suspender al usuario.`);
    } catch (cause) { setError(problem(cause)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <dialog ref={dialog} onCancel={event => { event.preventDefault(); if (!busy) onClose(); }} className="max-h-[90vh] w-[min(1000px,96vw)] overflow-y-auto rounded-xl bg-white p-5 text-slate-800 shadow-xl backdrop:bg-slate-900/50"><div className="mb-4 flex items-start justify-between gap-3"><div><h2 className="font-semibold">Revisión de baja y traspaso de responsabilidades</h2><p className="text-sm text-slate-500">{member.name} · {member.email}</p></div><button type="button" className={button} disabled={busy} onClick={onClose}>Cerrar</button></div>{error && <p role="alert" className="mb-3 text-sm text-red-700">{error}</p>}{notice && <p role="status" className="mb-3 text-sm text-teal-800">{notice}</p>}{!review && !error && <p role="status" className="text-sm">Consultando cartera, tareas, documentos y responsabilidades…</p>}{review && <form className="space-y-4" onSubmit={submit}><p className="text-sm">Elija el destinatario de cada responsabilidad. Puede traspasar una parte, resolver los bloqueos desde sus módulos y volver a revisar. La baja se comprueba otra vez al guardar.</p>{review.blockers.length > 0 && <section className="space-y-2 rounded-lg border border-amber-300 bg-amber-50 p-3"><h3 className="font-semibold">Obligaciones que deben resolverse antes de la baja</h3>{review.blockers.map(blocker => <details className="rounded border border-amber-200 p-2 text-sm" key={blocker.code}><summary>{blocker.label}: {blocker.count}</summary><p className="my-2">{blocker.guidance}</p>{blocker.samples.map(id => <p className="break-all text-xs" key={id}>{id}</p>)}</details>)}</section>}<div className="space-y-3">{review.groups.map(group => <article className="space-y-3 rounded-lg border p-3" key={group.key}><div className="flex items-center justify-between gap-2"><h3 className="text-sm font-semibold">{group.label}</h3><span className="text-sm">{group.count} pendientes</span></div>{group.count > 0 && <><RemoteEntitySelect<Candidate> key={`${member.id}:${group.key}:${revision}`} value={recipients[group.key] || ""} onChange={value => setRecipients(previous => ({ ...previous, [group.key]: value }))} endpoint={`/api/v1/memberships/${member.id}/handover/options`} queryParams={{ group: group.key }} entityType="sales_rep" label="Persona que recibirá esta responsabilidad" disabled={busy} mapOption={item => ({ value: item.id, label: item.name, description: `${item.email} · ${item.role}`, data: item })} /><p className="text-xs text-slate-500">{group.requires_sales_rep && "Debe tener representación comercial activa. "}{group.required_permissions.length > 0 ? `Permisos necesarios: ${group.required_permissions.join(", ")}.` : "Debe ser una persona activa de la empresa."}</p><details className="text-xs"><summary className="cursor-pointer">Ver ejemplos de los registros por traspasar</summary>{group.samples.map(row => <p className="mt-1 break-all" key={row.id}>{row.name} · {row.id}</p>)}{group.count > group.samples.length && <p>Se muestran {group.samples.length} ejemplos de {group.count}. El traspaso incluye todos los registros de esta responsabilidad.</p>}</details></>}</article>)}</div><ul className="list-inside list-disc space-y-1 text-sm">{review.effects.map(effect => <li key={effect}>{effect}</li>)}</ul><label className="grid gap-1 text-sm">Motivo y condiciones del traspaso o baja<textarea className="rounded-lg border border-slate-300 p-2" required minLength={5} maxLength={2000} disabled={busy} value={reason} onChange={event => setReason(event.target.value)} /></label><div className="flex flex-wrap gap-3"><button className={button} name="action" value="transfer" disabled={busy || !Object.values(recipients).some(Boolean)}>Traspasar las responsabilidades seleccionadas</button><button className={button} name="action" value="suspend" disabled={busy || !canSuspend}>{pending.length ? "Traspasar todos los pendientes y suspender" : "Suspender usuario sin pendientes"}</button><button type="button" className={button} disabled={busy} onClick={() => { setError(""); setRevision(value => value + 1); }}>Actualizar revisión</button></div></form>}</dialog>;
}
