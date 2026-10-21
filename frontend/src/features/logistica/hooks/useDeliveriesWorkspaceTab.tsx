import * as transporte from "../api/DeliveriesWorkspaceTab";
import { requestAllPages } from "../../../api/pagination";
import { FormEvent, useEffect, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { DeliveryItem } from "../types/DeliveriesWorkspaceTab";
import { ProofOfDeliveryData } from "../types/DeliveriesWorkspaceTab";

export function useDeliveriesWorkspaceTab(_props: {
  canWrite: boolean;
}) {
  const [deliveries, setDeliveries] = useState<DeliveryItem[]>([]);

  const [delayedCount, setDelayedCount] = useState(0);

  const [delayedOnly, setDelayedOnly] = useState(false);

  const [statusFilter, setStatusFilter] = useState("");

  const [carrierFilter, setCarrierFilter] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [revision, setRevision] = useState(0);

  const [activeDelivery, setActiveDelivery] = useState<DeliveryItem | null>(null);

  const [activePod, setActivePod] = useState<ProofOfDeliveryData | null>(null);

  const [modalType, setModalType] = useState<string | null>(null);

  const [eligibleSales, setEligibleSales] = useState<{ sale_id: string; number: string; total_amount: string; currency: string; warehouse_id?: string | null }[]>([]);

  const [warehouses, setWarehouses] = useState<{ warehouse_id: string; name: string; code: string }[]>([]);

  const [deliveryCurrency, setDeliveryCurrency] = useState("");

  const [carrierMode, setCarrierMode] = useState("Transporte Propio");

  const toast = useToast();

  async function openCreateDelivery() {
    try {
      const [salesResult, warehouseRows, company] = await Promise.all([
        transporte.solicitarOpenCreateDelivery(),
        transporte.solicitarOpenCreateDelivery2(),
        transporte.solicitarOpenCreateDelivery3()
      ]);
      setEligibleSales(salesResult.items || []);
      setWarehouses(warehouseRows);
      setDeliveryCurrency(company.base_currency);
      setModalType("create_delivery");
    } catch (requestError: unknown) {
      toast.error("No se pudo preparar la entrega", requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "Verifica ventas confirmadas y almacenes activos.");
    }
  }

  useEffect(() => {
    setLoading(true);
    setError("");
    const params = new URLSearchParams();
    params.set("limit", "100");
    if (delayedOnly) params.set("delayed_only", "true");
    if (statusFilter) params.set("status", statusFilter);
    if (carrierFilter) params.set("carrier", carrierFilter);

    requestAllPages<{ items: DeliveryItem[]; delayed_count: number }>(`/api/v1/deliveries?${params.toString()}`)
      .then(res => {
        setDeliveries(res.items || []);
        setDelayedCount(res.delayed_count || 0);
      })
      .catch(err => setError(String(err?.detail || "Error al cargar entregas logísticas")))
      .finally(() => setLoading(false));
  }, [delayedOnly, statusFilter, carrierFilter, revision]);

  async function handleCreateDelivery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      await transporte.solicitarHandleCreateDelivery({ data });
      toast.success("Despacho preparado", "Entrega registrada con snapshot inmutable de dirección.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al registrar entrega";
      toast.error("Error", msg);
    }
  }

  async function handleDispatch(deliveryId: string) {
    try {
      await transporte.solicitarHandleDispatch({ deliveryId });
      toast.success("Despacho efectuado", "Salida física de inventario confirmada en almacén.");
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al despachar entrega";
      toast.error("Error", msg);
    }
  }

  async function handleAddTrackingEvent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeDelivery) return;
    const data = new FormData(event.currentTarget);
    try {
      await transporte.solicitarHandleAddTrackingEvent({ activeDelivery, data });
      toast.success("Evento registrado", "Hito de seguimiento añadido con deduplicación y anti-regresión.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al registrar evento";
      toast.error("Error", msg);
    }
  }

  async function handleRecordPod(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeDelivery) return;
    const data = new FormData(event.currentTarget);
    try {
      await transporte.solicitarHandleRecordPod({ activeDelivery, data });
      toast.success("Entrega finalizada", "Prueba de entrega (POD) registrada de forma confidencial.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al registrar POD";
      toast.error("Error", msg);
    }
  }

  async function handleViewPod(deliveryId: string) {
    try {
      const res = await transporte.solicitarHandleViewPod({ deliveryId });
      setActivePod(res);
      setModalType("view_pod");
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al consultar prueba de entrega";
      toast.error("Error", msg);
    }
  }

  async function handleRecordIncident(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeDelivery) return;
    const data = new FormData(event.currentTarget);
    try {
      await transporte.solicitarHandleRecordIncident({ activeDelivery, data });
      toast.warning("Incidencia reportada", "Registrada sin reponer inventario en falso.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al registrar incidencia";
      toast.error("Error", msg);
    }
  }

  async function handleCancel(deliveryId: string) {
    try {
      await transporte.solicitarHandleCancel({ deliveryId });
      toast.success("Despacho cancelado", "Reserva liberada para el almacén.");
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al cancelar";
      toast.error("Error", msg);
    }
  }

  async function handleIntercept(deliveryId: string) {
    try {
      await transporte.solicitarHandleIntercept({ deliveryId });
      toast.warning("Intercepción solicitada", "Notificación transmitida al transportista para retorno seguro.");
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al solicitar intercepción";
      toast.error("Error", msg);
    }
  }
  return { deliveries, delayedCount, delayedOnly, setDelayedOnly, statusFilter, setStatusFilter, carrierFilter, setCarrierFilter, loading, error, setRevision, activeDelivery, setActiveDelivery, activePod, modalType, setModalType, eligibleSales, warehouses, deliveryCurrency, carrierMode, setCarrierMode, openCreateDelivery, handleCreateDelivery, handleDispatch, handleAddTrackingEvent, handleRecordPod, handleViewPod, handleRecordIncident, handleCancel, handleIntercept };
}
