import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

const input = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";

export function CustomerDetailEditor({ customerId, kind, row, close, onSaved }: { customerId: string; kind: "contact" | "address"; row: Record<string, unknown>; close: () => void; onSaved: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const lock = useRef(false);
  const pending = useRef(new Map<string, string>());
  useEffect(() => { const previous = document.activeElement as HTMLElement | null; dialog.current?.showModal(); return () => previous?.focus(); }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const body = { ...Object.fromEntries(data), version: Number(row.version || 1), is_primary: data.get("is_primary") === "on", is_active: data.get("is_active") === "on", valid_from: data.get("valid_from") || null, valid_until: data.get("valid_until") || null, ...(kind === "contact" ? { can_purchase: data.get("can_purchase") === "on", can_receive: data.get("can_receive") === "on", preferences: row.preferences || {}, email: data.get("email") || null, phone: data.get("phone") || null } : {}) };
    const signature = JSON.stringify(body);
    const key = pending.current.get(signature) || crypto.randomUUID();
    pending.current.set(signature, key);
    try {
      await apiClient.request(`/api/v1/customers/${customerId}/${kind === "contact" ? "contacts" : "addresses"}/${row.id}`, { method: "PUT", body: signature, headers: { "Idempotency-Key": key } });
      pending.current.delete(signature);
      onSaved();
      close();
    } catch (failure) { const detail = (failure as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo guardar el registro."); }
    finally { lock.current = false; setBusy(false); }
  }
  function textField(name: string, label: string, required = false, type = "text") { return <label className="block text-sm" key={name}>{label}<input className={input} name={name} type={type} required={required} defaultValue={String(row[name] ?? "")} /></label>; }
  return <dialog ref={dialog} onCancel={event => { event.preventDefault(); if (!busy) close(); }} className="max-h-[90vh] w-[min(95vw,650px)] rounded-2xl bg-white p-5 text-slate-900 shadow-xl backdrop:bg-slate-950/60"><div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">Editar {kind === "contact" ? "contacto" : "dirección"}</h2><button className={button} disabled={busy} onClick={close}>Cerrar</button></div>{error && <p role="alert" className="mb-3 text-sm text-red-700">{error}</p>}<form onSubmit={submit} className="space-y-4"><div className="grid gap-3 sm:grid-cols-2">{kind === "contact" ? <>{textField("name", "Nombre", true)}{textField("role", "Cargo", true)}{textField("email", "Correo", false, "email")}{textField("phone", "Teléfono")}<label className="block text-sm">Finalidad<select className={input} name="purpose" defaultValue={String(row.purpose || "general")}><option value="general">General</option><option value="purchasing">Compras</option><option value="billing">Facturación</option><option value="delivery">Recepción de entregas</option></select></label></> : <><label className="block text-sm">Tipo<select className={input} name="address_type" defaultValue={String(row.address_type || "comercial")}><option value="comercial">Comercial</option><option value="fiscal">Fiscal</option><option value="entrega">Entrega</option></select></label>{textField("street", "Calle y número", true)}{textField("city", "Ciudad", true)}{textField("state", "Región")}{textField("country", "País", true)}{textField("postal_code", "Código postal")}</>}{textField("valid_from", "Vigente desde", false, "date")}{textField("valid_until", "Vigente hasta", false, "date")}</div><label className="flex items-center gap-2 text-sm"><input name="is_primary" type="checkbox" defaultChecked={Boolean(row.is_primary)} />Principal de esta finalidad</label><label className="flex items-center gap-2 text-sm"><input name="is_active" type="checkbox" defaultChecked={row.is_active !== false} />Registro activo</label>{kind === "contact" && <><label className="flex items-center gap-2 text-sm"><input type="checkbox" name="can_purchase" defaultChecked={row.can_purchase !== false} />Autorizado para comprar</label><label className="flex items-center gap-2 text-sm"><input type="checkbox" name="can_receive" defaultChecked={Boolean(row.can_receive)} />Autorizado para recibir mercadería</label></>}<button className={button} disabled={busy}>Guardar cambios</button></form></dialog>;
}
