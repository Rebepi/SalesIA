import { useRef, useState } from "react";
import { apiClient } from "../../../api/client";
import type { SaleReturnRecord } from "../../ventas/components/VentasDevolucionModal";
import type { SaleDetailData } from "../../ventas/types/SaleDetailModal";
import { returnProblem } from "../api/returnFlow";
import { SaleReturnCompletion } from "./SaleReturnCompletion";

export function PendingSaleReturn({ record, sale, onAccepted, onCancelled, onChanged, onOpenSale, onBusyChange }: { record: SaleReturnRecord; sale: SaleDetailData; onAccepted: () => void; onCancelled: () => void; onChanged: () => void; onOpenSale?: (id: string) => void; onBusyChange: (value: boolean) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const [action, setAction] = useState("CREDIT_NOTE");
  const lock = useRef(false);
  const acceptKey = useRef(crypto.randomUUID());
  async function submit(cancel: boolean) {
    if (lock.current) return;
    if (cancel && reason.trim().length < 5) { setError("Escribe al menos cinco caracteres para justificar la cancelación."); return; }
    lock.current = true; setBusy(true); onBusyChange(true); setError("");
    try {
      await apiClient.request(`/api/v1/returns/${record.id}/${cancel ? "cancel" : "accept"}`, {
        method: "POST",
        headers: cancel ? undefined : { "Idempotency-Key": acceptKey.current },
        body: JSON.stringify(cancel ? { reason: reason.trim() } : { create_credit_note: true, credit_action: action, inspections: record.lines.map(line => ({ product_id: line.product_id, sale_line_id: line.sale_line_id, disposition: line.disposition })) })
      });
      if (cancel) onCancelled(); else onAccepted();
    } catch (cause) { setError(returnProblem(cause)); }
    finally { lock.current = false; setBusy(false); onBusyChange(false); }
  }
  if (record.status === "accepted") return <SaleReturnCompletion returnId={record.id} sale={sale} warehouseId={record.warehouse_id} onChanged={onChanged} onOpenSale={onOpenSale} onBusyChange={onBusyChange} />;
  return <section className="space-y-4">
    <h3 className="font-bold">Revisar solicitud {record.id.slice(0, 8)}</h3><p>{record.reason}</p>
    <p className="text-sm text-slate-500">La aceptación aplica la inspección guardada y los movimientos de inventario. Si se exige revisión independiente, debe aceptarla otra persona autorizada; el servidor verifica esta regla.</p>
    <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th>Producto</th><th>Cantidad</th><th>Destino</th></tr></thead><tbody>{record.lines.map((line, index) => <tr key={index}><td>{sale.lines?.find(item => item.product_id === line.product_id)?.product_name || line.product_id}</td><td>{line.quantity}</td><td>{{ RESTOCK: "Inventario vendible", QUARANTINE: "Cuarentena", DISPOSE: "Merma" }[line.disposition] || line.disposition}</td></tr>)}</tbody></table></div>
    {error && <p role="alert" className="text-red-600">{error}</p>}
    <fieldset disabled={busy} className="space-y-3">
      <label className="grid gap-2">Liquidación al aceptar<select value={action} onChange={event => { setAction(event.target.value); acceptKey.current = crypto.randomUUID(); }}><option value="CREDIT_NOTE">Ajustar deuda y conservar valor para cambio o reembolso</option><option value="STORE_CREDIT">Ajustar deuda y otorgar saldo a favor</option><option value="REFUND">Ajustar deuda y continuar con el desembolso</option></select></label>
      <button type="button" onClick={() => void submit(false)}>{busy ? "Procesando…" : "Aceptar devolución revisada"}</button>
      <label className="grid gap-2">Motivo para cancelar la solicitud<input value={reason} onChange={event => setReason(event.target.value)} maxLength={255} /></label><button type="button" onClick={() => void submit(true)}>Cancelar solicitud pendiente</button>
    </fieldset>
  </section>;
}
