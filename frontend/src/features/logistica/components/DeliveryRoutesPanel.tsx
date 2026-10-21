import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Vehicle = { id: string; code: string; name: string; max_weight_kg: string; max_volume_m3: string; is_active: boolean; version: number };
type Delivery = { id: string; warehouse_id: string; recipient_name: string; address: string; status: string; assigned: boolean };
type Stop = { appointment?: { starts_at: string; ends_at: string; requirements: string } | null; delivery_id: string; weight_kg: string; volume_m3: string; notes: string; recipient_name?: string; address?: string; current_status?: string; products?: { product_id: string; name: string; sku: string; quantity: string }[] };
type Route = { id: string; code: string; service_date: string; zone: string; vehicle: Vehicle; responsible_id: string; responsible_name: string; warehouse_id: string; status: string; version: number; stops: Stop[]; total_weight_kg: string; total_volume_m3: string; weight_available_kg: string; volume_available_m3: string; notes: string; history: { action: string; reason: string; actor: string; at: string; version: number }[] };
type Options = { warehouses: { warehouse_id: string; name: string }[]; vehicles: Vehicle[]; responsible: { id: string; name: string }[]; deliveries: Delivery[]; business_date: string };
const states: Record<string, string> = { draft: "Borrador", planned: "Planificado", in_progress: "En recorrido", completed: "Completado", cancelled: "Cancelado", ready: "Listo para despacho", dispatched: "Despachado", in_transit: "En tránsito", out_for_delivery: "En reparto", incident: "Con incidencia", failed_attempt: "Intento fallido", delivered: "Entregado", returned: "Retornado", partially_delivered: "Entrega parcial", pending_redelivery: "Reentrega pendiente", partially_rejected: "Rechazo parcial", rejected: "Rechazado" };
const actionNames: Record<string, string> = { plan: "Confirmar planificación", start: "Iniciar recorrido", complete: "Completar recorrido", cancel: "Cancelar recorrido", reopen: "Reabrir recorrido" };
const input = "rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
function problem(cause: unknown) { const detail = (cause as { detail?: unknown }).detail; return typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "No se pudo completar la operación."; }

export function DeliveryRoutesPanel({ canWrite, onChanged }: { canWrite: boolean; onChanged: () => void }) {
  const [options, setOptions] = useState<Options>({ warehouses: [], vehicles: [], responsible: [], deliveries: [], business_date: "" });
  const [routes, setRoutes] = useState<Route[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [filter, setFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [selected, setSelected] = useState<Route | null>(null);
  const [editing, setEditing] = useState<Route | "new" | null>(null);
  const [vehicleEdit, setVehicleEdit] = useState<Vehicle | "new" | null>(null);
  const [stops, setStops] = useState<Stop[]>([]);
  const [warehouse, setWarehouse] = useState("");
  const [vehicleId, setVehicleId] = useState("");
  const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const requestRevision = useRef(0);
  const warehouses = options.warehouses;
  const vehicle = options.vehicles.find(item => item.id === vehicleId);
  const weight = stops.reduce((sum, item) => sum + Number(item.weight_kg || 0), 0);
  const volume = stops.reduce((sum, item) => sum + Number(item.volume_m3 || 0), 0);
  const overloaded = Boolean(vehicle && (weight > Number(vehicle.max_weight_kg) || volume > Number(vehicle.max_volume_m3)));

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([apiClient.request<Options>("/api/v1/delivery-route-options", { signal: controller.signal }), apiClient.request<{ items: Route[]; total_count: number }>(`/api/v1/delivery-routes?limit=10&offset=${page * 10}${filter ? `&status=${filter}` : ""}${dateFilter ? `&service_date=${dateFilter}` : ""}`, { signal: controller.signal })]).then(([available, result]) => { if (controller.signal.aborted) return; setOptions(available); setRoutes(result.items); setTotal(result.total_count); }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [page, filter, dateFilter, revision]);
  useEffect(() => () => { requestRevision.current += 1; }, []);

  async function open(id: string) {
    const current = ++requestRevision.current;
    try { const result = await apiClient.request<Route>(`/api/v1/delivery-routes/${id}`); if (current === requestRevision.current) setSelected(result); }
    catch (cause) { if (current === requestRevision.current) setError(problem(cause)); }
  }

  function edit(route: Route | "new") {
    setEditing(route);
    setStops(route === "new" ? [] : route.stops.map(item => ({ ...item })));
    setWarehouse(route === "new" ? warehouses[0]?.warehouse_id || "" : route.warehouse_id);
    setVehicleId(route === "new" ? options.vehicles.find(item => item.is_active)?.id || "" : route.vehicle.id);
    setError("");
  }

  async function mutate(path: string, values: Record<string, unknown>, method = "POST") {
    if (sending.current) return;
    sending.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const body = JSON.stringify(values);
    const signature = `${method}:${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try {
      const result = await apiClient.request<Route | Vehicle>(`/api/v1${path}`, { method, headers: { "Idempotency-Key": key }, body });
      requestRevision.current += 1;
      if ("stops" in result) setSelected(result);
      setEditing(null);
      setVehicleEdit(null);
      setRevision(value => value + 1);
      setNotice("Operación logística registrada.");
      onChanged();
    } catch (cause) { setError(problem(cause)); if (selected) await open(selected.id); }
    finally { sending.current = false; setBusy(false); }
  }

  function saveRoute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    void mutate(`/delivery-routes${editing === "new" ? "" : `/${editing.id}`}`, { ...values, warehouse_id: warehouse, vehicle_id: vehicleId, version: editing === "new" ? 0 : editing.version, stops: stops.map(item => ({ delivery_id: item.delivery_id, weight_kg: item.weight_kg, volume_m3: item.volume_m3, notes: item.notes })) }, editing === "new" ? "POST" : "PUT");
  }

  function move(index: number, direction: number) {
    setStops(previous => { const result = [...previous]; const target = index + direction; if (target < 0 || target >= result.length) return previous; [result[index], result[target]] = [result[target], result[index]]; return result; });
  }

  const editValue = editing && editing !== "new" ? editing : null;
  const vehicleValue = vehicleEdit && vehicleEdit !== "new" ? vehicleEdit : null;
  return <section className="space-y-4 rounded-xl border bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold">Recorridos, vehículos y capacidad</h2><p className="text-sm text-slate-500">Ordena las paradas y registra el peso y volumen reales de cada envío.</p></div><div className="flex gap-2"><button className={button} disabled={busy} onClick={() => { setRevision(value => value + 1); if (selected) void open(selected.id); }}>Actualizar</button>{canWrite && <><button className={button} disabled={busy} onClick={() => edit("new")}>Nuevo recorrido</button><button className={button} disabled={busy} onClick={() => setVehicleEdit("new")}>Nuevo vehículo</button></>}</div></div>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}
    <details><summary className="cursor-pointer text-sm font-medium">Vehículos y capacidad registrada</summary><ul className="mt-2 space-y-2 text-sm">{options.vehicles.map(item => <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3"><span>{item.code} · {item.name} · {item.max_weight_kg} kg · {item.max_volume_m3} m³ · {item.is_active ? "Disponible" : "Inactivo"}</span>{canWrite && <button className={button} disabled={busy} onClick={() => setVehicleEdit(item)}>Editar vehículo</button>}</li>)}</ul></details>
    {vehicleEdit && <form key={vehicleValue?.id || "new-vehicle"} onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void mutate(`/delivery-vehicles${vehicleValue ? `/${vehicleValue.id}` : ""}`, { ...values, is_active: values.is_active === "on", version: vehicleValue?.version || 0 }, vehicleValue ? "PUT" : "POST"); }} className="grid gap-3 rounded-xl border p-4"><h3 className="font-medium">{vehicleValue ? "Editar vehículo" : "Registrar vehículo"}</h3><label className="grid gap-1 text-sm">Código<input className={input} name="code" required pattern="[A-Za-z0-9_-]+" maxLength={64} defaultValue={vehicleValue?.code} /></label><label className="grid gap-1 text-sm">Nombre o identificación<input className={input} name="name" required minLength={2} maxLength={255} defaultValue={vehicleValue?.name} /></label><label className="grid gap-1 text-sm">Carga máxima en kg<input className={input} name="max_weight_kg" type="number" required min="0.000001" step="0.000001" defaultValue={vehicleValue?.max_weight_kg} /></label><label className="grid gap-1 text-sm">Volumen máximo en m³<input className={input} name="max_volume_m3" type="number" required min="0.000001" step="0.000001" defaultValue={vehicleValue?.max_volume_m3} /></label><label className="flex gap-2 text-sm"><input type="checkbox" name="is_active" defaultChecked={vehicleValue?.is_active ?? true} />Vehículo disponible para planificar</label><textarea className={input} name="reason" required minLength={5} maxLength={2000} placeholder="Motivo del registro o cambio" aria-label="Motivo del cambio de vehículo" /><div className="flex gap-2"><button className={button} disabled={busy}>Guardar vehículo</button><button type="button" className={button} disabled={busy} onClick={() => setVehicleEdit(null)}>Cerrar</button></div></form>}
    {editing && <form key={editValue?.id || "new-route"} className="space-y-3 rounded-xl border p-4" onSubmit={saveRoute}><h3 className="font-medium">{editValue ? `Editar ${editValue.code}` : "Nuevo recorrido"}</h3><div className="grid gap-3 md:grid-cols-2"><label className="grid gap-1 text-sm">Fecha de servicio<input className={input} name="service_date" type="date" required min={options.business_date} defaultValue={editValue?.service_date || options.business_date} /></label><label className="grid gap-1 text-sm">Zona<input className={input} name="zone" required minLength={2} maxLength={128} defaultValue={editValue?.zone} /></label><label className="grid gap-1 text-sm">Almacén<CustomSelect remote={{ resource: "warehouses" }} className={input} value={warehouse} required onChange={event => { setWarehouse(event.target.value); setStops([]); }}>{warehouses.map(item => <option key={item.warehouse_id} value={item.warehouse_id}>{item.name}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Vehículo<select className={input} value={vehicleId} required onChange={event => setVehicleId(event.target.value)}><option value="">Seleccionar</option>{options.vehicles.filter(item => item.is_active).map(item => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label><label className="grid gap-1 text-sm">Responsable<CustomSelect remote={{ resource: "people" }} className={input} name="responsible_id" required defaultValue={editValue?.responsible_id || ""}><option value="">Seleccionar</option>{options.responsible.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</CustomSelect></label></div>
      <label className="grid gap-1 text-sm">Agregar entrega<select className={input} value="" disabled={busy} onChange={event => { const item = options.deliveries.find(value => value.id === event.target.value); if (item) setStops(previous => [...previous, { delivery_id: item.id, recipient_name: item.recipient_name, address: item.address, weight_kg: "", volume_m3: "", notes: "" }]); }}><option value="">Seleccionar entrega del almacén</option>{options.deliveries.filter(item => item.warehouse_id === warehouse && !stops.some(stop => stop.delivery_id === item.id) && (!item.assigned || editValue?.stops.some(stop => stop.delivery_id === item.id))).map(item => <option key={item.id} value={item.id}>{item.id.substring(0, 8).toUpperCase()} · {item.recipient_name} · {item.address}</option>)}</select></label>
      <ol className="space-y-3">{stops.map((item, index) => <li key={item.delivery_id} className="space-y-2 rounded-lg border p-3"><div className="flex flex-wrap items-center justify-between gap-2 text-sm"><strong>Parada {index + 1} · {item.recipient_name} · {item.address}</strong><div className="flex gap-2"><button className={button} type="button" disabled={busy || index === 0} onClick={() => move(index, -1)}>Subir</button><button className={button} type="button" disabled={busy || index === stops.length - 1} onClick={() => move(index, 1)}>Bajar</button><button className={button} type="button" disabled={busy} onClick={() => setStops(previous => previous.filter(stop => stop.delivery_id !== item.delivery_id))}>Quitar</button></div></div><div className="grid gap-2 md:grid-cols-3"><label className="grid gap-1 text-sm">Peso kg<input className={input} type="number" required min="0.000001" step="0.000001" value={item.weight_kg} onChange={event => setStops(previous => previous.map((stop, position) => position === index ? { ...stop, weight_kg: event.target.value } : stop))} /></label><label className="grid gap-1 text-sm">Volumen m³<input className={input} type="number" required min="0.000001" step="0.000001" value={item.volume_m3} onChange={event => setStops(previous => previous.map((stop, position) => position === index ? { ...stop, volume_m3: event.target.value } : stop))} /></label><label className="grid gap-1 text-sm">Instrucciones<input className={input} maxLength={1000} value={item.notes} onChange={event => setStops(previous => previous.map((stop, position) => position === index ? { ...stop, notes: event.target.value } : stop))} /></label></div></li>)}</ol>
      <p className={`rounded-lg p-3 text-sm ${overloaded ? "bg-red-50 text-red-800" : "bg-slate-50"}`}>Carga: {weight.toFixed(6)} / {vehicle?.max_weight_kg || "—"} kg · Volumen: {volume.toFixed(6)} / {vehicle?.max_volume_m3 || "—"} m³{overloaded && " · Capacidad superada"}</p><label className="grid gap-1 text-sm">Notas<textarea className={input} name="notes" maxLength={4000} defaultValue={editValue?.notes} /></label><label className="grid gap-1 text-sm">Motivo de creación o cambio<textarea className={input} name="reason" required minLength={5} maxLength={2000} /></label><p className="text-sm text-slate-500">Si cambian las entregas después de planificar, guarda otra vez el manifiesto y confirma la planificación. Despacha cada entrega antes de iniciar el recorrido.</p><div className="flex gap-2"><button className={button} disabled={busy || overloaded || !stops.length}>Guardar borrador y manifiesto</button><button type="button" className={button} disabled={busy} onClick={() => setEditing(null)}>Cerrar editor</button></div>
    </form>}
    <div className="flex flex-wrap gap-3"><label className="grid gap-1 text-sm">Estado<select className={input} value={filter} onChange={event => { setFilter(event.target.value); setPage(0); }}><option value="">Todos</option>{["draft", "planned", "in_progress", "completed", "cancelled"].map(value => <option key={value} value={value}>{states[value]}</option>)}</select></label><label className="grid gap-1 text-sm">Fecha<input className={input} type="date" value={dateFilter} onChange={event => { setDateFilter(event.target.value); setPage(0); }} /></label></div>
    <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Recorrido", "Fecha y zona", "Vehículo y responsable", "Carga", "Estado", "Detalle"].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{routes.map(item => <tr key={item.id} className="border-t"><td className="p-2">{item.code}</td><td className="p-2">{item.service_date} · {item.zone}</td><td className="p-2">{item.vehicle.code} · {item.responsible_name}</td><td className="p-2">{item.total_weight_kg} kg · {item.total_volume_m3} m³ · {item.stops.length} paradas</td><td className="p-2">{states[item.status]}</td><td className="p-2"><button className={button} disabled={busy} onClick={() => void open(item.id)}>Abrir manifiesto</button></td></tr>)}</tbody></table>{!routes.length && <p className="p-3 text-sm text-slate-500">No hay recorridos para estos filtros.</p>}</div><div className="flex items-center gap-3 text-sm"><button className={button} disabled={busy || page === 0} onClick={() => setPage(value => value - 1)}>Anterior</button><span>{total} recorridos · Página {page + 1}</span><button className={button} disabled={busy || (page + 1) * 10 >= total} onClick={() => setPage(value => value + 1)}>Siguiente</button></div>
    {selected && <div className="space-y-3 rounded-xl border p-4"><div className="flex flex-wrap justify-between gap-2"><h3 className="font-semibold">{selected.code} · {states[selected.status]}</h3><div className="flex gap-2">{canWrite && ["draft", "planned"].includes(selected.status) && <button className={button} disabled={busy} onClick={() => edit(selected)}>Editar manifiesto</button>}<button className={button} disabled={busy} onClick={() => { requestRevision.current += 1; setSelected(null); }}>Cerrar detalle</button></div></div><p className="text-sm">{selected.service_date} · {selected.zone} · {selected.vehicle.code} · {selected.responsible_name}</p><p className="text-sm">Carga: {selected.total_weight_kg} kg · Volumen: {selected.total_volume_m3} m³ · Capacidad restante: {selected.weight_available_kg} kg y {selected.volume_available_m3} m³</p><p className="text-sm">{selected.notes}</p><ol className="space-y-3">{selected.stops.map((item, index) => <li key={item.delivery_id} className="rounded-lg border p-3 text-sm"><strong>Parada {index + 1} · {item.recipient_name} · {states[item.current_status || ""] || item.current_status}</strong><p>{item.address} · {item.weight_kg} kg · {item.volume_m3} m³</p><p>{item.notes}</p>{item.appointment && <p>Horario pactado: {new Date(item.appointment.starts_at).toLocaleString("es-PE")} – {new Date(item.appointment.ends_at).toLocaleString("es-PE")} · {item.appointment.requirements}</p>}<ul className="mt-2 text-xs">{item.products?.map(product => <li key={product.product_id}>{product.sku} · {product.name} · {product.quantity}</li>)}</ul></li>)}</ol>
      {canWrite && selected.status !== "completed" && <form className="flex flex-wrap gap-2" key={`${selected.id}:${selected.version}`} onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void mutate(`/delivery-routes/${selected.id}/actions`, { ...values, version: selected.version }); }}><select className={input} name="action" aria-label="Acción del recorrido">{(selected.status === "draft" ? ["plan", "cancel"] : selected.status === "planned" ? ["start", "cancel"] : selected.status === "in_progress" ? ["complete", "cancel"] : ["reopen"]).map(value => <option key={value} value={value}>{actionNames[value]}</option>)}</select><input className={`${input} grow`} name="reason" required minLength={5} maxLength={2000} placeholder="Motivo de la acción" aria-label="Motivo de la acción" /><button className={button} disabled={busy}>Aplicar</button></form>}
      <details><summary className="cursor-pointer text-sm font-medium">Historial y versiones</summary><ul className="mt-2 space-y-2 text-sm">{selected.history.map((item, index) => <li key={`${item.at}:${index}`}>Versión {item.version} · {item.action} · {item.actor} · {new Date(item.at).toLocaleString("es-PE")}<p>{item.reason}</p></li>)}</ul></details>
    </div>}
  </section>;
}
