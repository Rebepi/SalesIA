import { useEffect, useState } from "react";
import { apiClient } from "../../../api/client";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { ReturnWizardModal } from "../../devoluciones/components/ReturnWizardModal";
import { SaleReturnCompletion } from "../../devoluciones/components/SaleReturnCompletion";
import { PendingSaleReturn } from "../../devoluciones/components/PendingSaleReturn";
import type { SaleDetailData } from "../types/SaleDetailModal";
import type { SaleRecord } from "../types/ventas";
import "./ventas-return.css";
import { returnProblem } from "../../devoluciones/api/returnFlow";

export interface SaleReturnRecord {
  id: string;
  status: string;
  reason: string;
  warehouse_id: string;
  created_at: string;
  details?: { requested_by?: string };
  lines: { product_id: string; sale_line_id?: string; quantity: string; disposition: string }[];
}

interface Props {
  isOpen: boolean;
  sale: SaleRecord | null;
  onClose: () => void;
  onSuccess: (result?: { returnId: string; isExchange?: boolean }) => void;
  onOpenSale?: (id: string) => void;
}

export function VentasDevolucionModal({ isOpen, sale, onClose, onSuccess, onOpenSale }: Props) {
  const [detail, setDetail] = useState<SaleDetailData | null>(null);
  const [returns, setReturns] = useState<SaleReturnRecord[]>([]);
  const [warehouseId, setWarehouseId] = useState("");
  const [warehouses, setWarehouses] = useState<{ warehouse_id: string; name: string; branch_id: string }[]>([]);
  const [view, setView] = useState<"loading" | "choose" | "new" | "existing">("loading");
  const [selected, setSelected] = useState<SaleReturnRecord | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const identifier = sale?.sale_id || sale?.id;
  useEffect(() => {
    if (!isOpen || !identifier) return;
    const controller = new AbortController();
    setView("loading"); setError(""); setSelected(null); setDetail(null);
    void Promise.all([
      apiClient.request<SaleDetailData>(`/api/v1/sales/${identifier}`, { signal: controller.signal }),
      apiClient.request<SaleReturnRecord[]>(`/api/v1/returns?sale_id=${identifier}`, { signal: controller.signal })
    ]).then(async ([record, previous]) => {
      let choices: typeof warehouses = [];
      if (!record.warehouse_id) choices = await apiClient.request<typeof warehouses>("/api/v1/warehouses?is_active=true", { signal: controller.signal });
      if (controller.signal.aborted) return;
      setDetail(record); setReturns(previous); setWarehouseId(record.warehouse_id || ""); setWarehouses(choices.filter(item => item.branch_id === record.branch_id));
      setView(previous.some(item => ["requested", "accepted"].includes(item.status)) || !record.warehouse_id ? "choose" : "new");
    }).catch(cause => { if (!controller.signal.aborted) { setError(returnProblem(cause)); setView("choose"); } });
    return () => controller.abort();
  }, [isOpen, identifier, revision]);
  if (!isOpen || !sale) return null;
  if (view === "new" && detail) return <ReturnWizardModal isOpen saleId={String(identifier)} documentNumber={detail.number || sale.number || "Venta"} customerName={detail.customer_name || sale.customer_name} warehouseId={warehouseId} onClose={onClose} onSuccess={returnId => onSuccess({ returnId })} renderCompletion={(returnId, onBusyChange) => <SaleReturnCompletion onBusyChange={onBusyChange} returnId={returnId} sale={detail} warehouseId={warehouseId} onChanged={() => onSuccess({ returnId })} onOpenSale={onOpenSale} />} />;
  return <ModalSurface labelledBy="sales-return-title" onClose={onClose} blocked={busy} className="sales-return-dialog w-[min(94vw,1000px)]">
    <article className="sales-return-workspace max-h-[90dvh] overflow-y-auto rounded-2xl border bg-white p-6">
      <header className="mb-5 flex items-center justify-between gap-3"><div><h2 id="sales-return-title" className="text-lg font-bold">Devoluciones de {sale.number}</h2><p>{sale.customer_name}</p></div><button type="button" disabled={busy} onClick={onClose}>Cerrar</button></header>
      {error && <div role="alert" className="mb-4 text-red-600">{error}<button type="button" onClick={() => setRevision(value => value + 1)}>Reintentar carga</button></div>}
      {view === "loading" && <p role="status">Cargando venta y devoluciones anteriores…</p>}
      {view === "choose" && detail && <div className="space-y-5">
        {!detail.warehouse_id && <label className="grid gap-2">Almacén receptor<select value={warehouseId} onChange={event => setWarehouseId(event.target.value)}><option value="">Seleccionar almacén de esta sede</option>{warehouses.map(item => <option key={item.warehouse_id} value={item.warehouse_id}>{item.name}</option>)}</select></label>}
        <button type="button" disabled={!warehouseId} onClick={() => setView("new")}>Registrar nueva devolución</button>
        <p className="text-sm text-slate-500">Las solicitudes pendientes reservan sus cantidades. Otra persona autorizada puede revisarlas y aceptarlas cuando la separación de funciones lo exige. Las aceptadas conservan su liquidación para continuar después.</p>
        {returns.filter(item => ["requested", "accepted"].includes(item.status)).map(item => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4"><div><strong>{item.id.slice(0, 8)} · {item.status === "requested" ? "Pendiente de revisión" : "Aceptada"}</strong><p>{item.reason}</p><small>{item.created_at?.slice(0, 10)}</small></div><button type="button" onClick={() => { setSelected(item); setView("existing"); }}>Continuar devolución</button></div>)}
      </div>}
      {view === "existing" && selected && detail && <PendingSaleReturn onBusyChange={setBusy} record={selected} sale={detail} onAccepted={() => { setSelected(value => value ? { ...value, status: "accepted" } : value); onSuccess({ returnId: selected.id }); }} onCancelled={() => { onSuccess({ returnId: selected.id }); setRevision(value => value + 1); }} onChanged={() => onSuccess({ returnId: selected.id })} onOpenSale={onOpenSale} />}
    </article>
  </ModalSurface>;
}
