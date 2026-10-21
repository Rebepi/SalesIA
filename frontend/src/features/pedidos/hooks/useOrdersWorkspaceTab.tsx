import * as transporte from "../api/OrdersWorkspaceTab";
import { requestAllPages } from "../../../api/pagination";
import { useState, useEffect } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { useConfirm, usePrompt } from "../../../ui/components/ConfirmDialog";
import { OrderItem } from "../types/OrdersWorkspaceTab";
import { CustomerChoice } from "../types/OrdersWorkspaceTab";
import { ProductChoice } from "../types/OrdersWorkspaceTab";
import { BranchChoice } from "../types/OrdersWorkspaceTab";
import { WarehouseChoice } from "../types/OrdersWorkspaceTab";
import { DraftLine } from "../types/OrdersWorkspaceTab";

export function useOrdersWorkspaceTab(_props: {
  canWrite?: boolean;
}) {
  const { confirm: _confirmOrders, ConfirmDialogNode } = useConfirm();

  const { prompt, PromptDialogNode } = usePrompt();

  const [orders, setOrders] = useState<OrderItem[]>([]);

  const [filterStatus, setFilterStatus] = useState<string>("");

  const [viewMode, setViewMode] = useState<"table" | "board">("table");

  const [selectedOrder, setSelectedOrder] = useState<OrderItem | null>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [busy, setBusy] = useState(false);

  const [fulfillModal, setFulfillModal] = useState<OrderItem | null>(null);

  const [fulfillSerials, setFulfillSerials] = useState<Record<string, string>>({});

  const [fulfillQuantities, setFulfillQuantities] = useState<Record<string, string>>({});

  const [editorOpen, setEditorOpen] = useState(false);

  const [editingOrder, setEditingOrder] = useState<OrderItem | null>(null);

  const [customer, setCustomer] = useState<CustomerChoice | null>(null);

  const [branches, setBranches] = useState<BranchChoice[]>([]);

  const [warehouses, setWarehouses] = useState<WarehouseChoice[]>([]);

  const [branchId, setBranchId] = useState("");

  const [warehouseId, setWarehouseId] = useState("");

  const [currency, setCurrency] = useState("USD");

  const [lines, setLines] = useState<DraftLine[]>([{ product_id: "", quantity: "1", discount_pct: "0" }]);

  const [customerDrawerOpen, setCustomerDrawerOpen] = useState(false);

  const [productLineIndex, setProductLineIndex] = useState<number | null>(null);

  const [scanOrder, setScanOrder] = useState<OrderItem | null>(null);

  const [scanCode, setScanCode] = useState("");

  const [shortageOrder, setShortageOrder] = useState<OrderItem | null>(null);

  const [shortages, setShortages] = useState<Array<{ product_id: string; sku: string; name: string; missing_quantity: string; alternatives: Array<{ warehouse_id: string; warehouse_name: string; available_quantity: string }> }>>([]);

  const [substitutes, setSubstitutes] = useState<Record<string, ProductChoice | undefined>>({});

  const toast = useToast();

  useEffect(() => {
    const openContextOrder = () => {
      const id = sessionStorage.getItem("salesia_context_order_id");
      if (!id) return;
      sessionStorage.removeItem("salesia_context_order_id");
      transporte.solicitarOpenContextOrder({ id }).then(setSelectedOrder).catch(() => toast.error("Pedido no disponible", "Actualiza la pantalla y verifica tus permisos."));
    };
    openContextOrder();
    window.addEventListener("salesia:open-order", openContextOrder);
    return () => window.removeEventListener("salesia:open-order", openContextOrder);
  }, []);

  useEffect(() => {
    loadOrders();
  }, [filterStatus]);

  useEffect(() => {
    Promise.all([
      transporte.solicitarDatos(),
      transporte.solicitarDatos2(),
      transporte.solicitarDatos3()
    ]).then(([branchRows, warehouseRows, company]) => {
      setBranches(branchRows);
      setWarehouses(Array.isArray(warehouseRows) ? warehouseRows : warehouseRows.items || []);
      setCurrency(company.base_currency || "USD");
    }).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (sessionStorage.getItem("salesia_open_order") !== "true") return;
    sessionStorage.removeItem("salesia_open_order");
    const customerId = sessionStorage.getItem("salesia_context_customer_id");
    if (customerId) transporte.solicitarDatos4({ customerId }).then(setCustomer).catch(() => undefined);
    const stockContext = sessionStorage.getItem("salesia_stock_order_context");
    if (stockContext) {
      sessionStorage.removeItem("salesia_stock_order_context");
      try {
        const context = JSON.parse(stockContext) as { product_id: string; warehouse_id: string };
        Promise.all([transporte.solicitarDatos5({ context }), transporte.solicitarDatos6()]).then(([product, warehouseRows]) => {
          const warehouse = warehouseRows.find(item => (item.warehouse_id || item.id) === context.warehouse_id);
          if (!warehouse) { toast.warning("Almacén no disponible", "Selecciona el almacén autorizado para reservar."); return; }
          setLines([{ product_id: product.id, product, quantity: "1", discount_pct: "0" }]);
          setBranchId(warehouse.branch_id || "");
          setWarehouseId(context.warehouse_id);
        }).catch(() => toast.error("No se pudo recuperar el artículo", "Selecciona nuevamente el producto y almacén del pedido."));
      } catch { toast.warning("Contexto no disponible", "Completa los datos del pedido para reservar existencias."); }
    }
    setEditorOpen(true);
  }, []);

  async function loadOrders() {
    setLoading(true);
    setError("");
    try {
      const url = filterStatus ? `/api/v1/orders?status_filter=${filterStatus}` : "/api/v1/orders";
      const res = await requestAllPages<OrderItem[]>(url);
      setOrders(Array.isArray(res) ? res : []);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar pedidos";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmAndReserve(order: OrderItem) {
    setBusy(true);
    try {
      await transporte.solicitarHandleConfirmAndReserve({ order });
      toast.success("Pedido confirmado", `Stock reservado en almacén para ${order.order_number}.`);
      await loadOrders();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al confirmar pedido";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  function openFulfillModal(order: OrderItem) {
    setFulfillModal(order);
    const initial: Record<string, string> = {};
    order.lines?.forEach((l, index) => {
      const remaining = Math.max(0, parseFloat(l.quantity) - parseFloat(l.fulfilled_quantity || "0") - parseFloat(l.cancelled_quantity || "0"));
      initial[String(index + 1)] = String(remaining);
    });
    setFulfillQuantities(initial);
    setFulfillSerials({});
  }

  async function handleFulfillSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!fulfillModal) return;
    setBusy(true);
    try {
      const items = Object.entries(fulfillQuantities)
        .filter(([, qty]) => parseFloat(qty) > 0)
        .map(([number, quantity]) => ({ product_id: fulfillModal.lines![Number(number) - 1].product_id, order_line_number: Number(number), quantity, serial_numbers: (fulfillSerials[number] || "").split(/[\s,;]+/).filter(Boolean) }));

      if (items.length === 0) {
        toast.warning("Sin cantidades", "Ingresa al menos una cantidad a despachar.");
        setBusy(false);
        return;
      }

      await transporte.solicitarHandleFulfillSubmit({ fulfillModal, items });
      toast.success("Despacho registrado", "Salida de inventario y cantidades servidas actualizadas.");
      setFulfillModal(null);
      await loadOrders();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error en despacho";
      toast.error("Error al despachar", msg);
    } finally {
      setBusy(false);
    }
  }

  async function createOrder(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!customer || !branchId || !warehouseId || lines.some(line => !line.product_id || Number(line.quantity) <= 0)) {
      toast.warning("Datos incompletos", "Selecciona cliente, sede, almacén y productos válidos.");
      return;
    }
    const data = new FormData(event.currentTarget);
    setBusy(true);
    try {
      const payload = { customer_id: customer.id, branch_id: branchId, warehouse_id: warehouseId, currency, payment_terms_days: Number(data.get("payment_terms_days") || 0), delivery_terms: String(data.get("delivery_terms") || "") || null, customer_po_number: String(data.get("customer_po_number") || "") || null, allow_backorder: data.get("allow_backorder") === "on", lines: lines.map(line => ({ product_id: line.product_id, quantity: line.quantity, discount_pct: line.discount_pct })) };
      await transporte.solicitarCreateOrder({ editingOrder, payload });
      setEditorOpen(false);
      setEditingOrder(null);
      setLines([{ product_id: "", quantity: "1", discount_pct: "0" }]);
      toast.success("Pedido creado", "El pedido quedó listo para aprobación y reserva.");
      await loadOrders();
    } catch (error: unknown) {
      const detail = error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudo crear el pedido.";
      toast.error("Error al crear", detail);
    } finally {
      setBusy(false);
    }
  }

  function editOrderLines(order: OrderItem) {
    setEditingOrder(order);
    setCustomer(order.customer_id ? { id: order.customer_id, legal_name: order.customer_name || "Cliente seleccionado" } : null);
    setBranchId(order.branch_id || "");
    setWarehouseId(order.warehouse_id || "");
    setCurrency(order.currency);
    setLines((order.lines || []).map(line => ({ product_id: line.product_id, product: { id: line.product_id, sku: line.sku, name: line.name || line.product_name || line.sku, unit_price: line.unit_price }, quantity: line.quantity, discount_pct: "0" })));
    setEditorOpen(true);
  }

  async function orderAction(order: OrderItem, action: "approve" | "release-reservation" | "renew-reservation" | "cancel" | "clone" | "picking") {
    setBusy(true);
    try {
      const id = order.id || order.order_id;
      const headers = action === "renew-reservation" || action === "picking" ? undefined : { "Idempotency-Key": crypto.randomUUID() };
      const cancelReason = action === "cancel" ? (await prompt({ title: "Motivo de cancelación", label: "Motivo", defaultValue: "Solicitud del cliente" }) ?? "Solicitud del cliente") : undefined;
      const body = action === "cancel" ? JSON.stringify({ reason: cancelReason }) : undefined;
      const result = await transporte.solicitarOrderAction({ id, action, headers, body });
      if (action === "picking") setScanOrder({ ...order, picking: result as unknown as OrderItem["picking"] });
      toast.success("Pedido actualizado", action === "clone" ? "Se creó un nuevo borrador con las mismas líneas." : "La acción se registró correctamente.");
      await loadOrders();
    } catch (error: unknown) {
      const detail = error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudo actualizar el pedido.";
      toast.error("Error", detail);
    } finally {
      setBusy(false);
    }
  }

  async function scanPicking(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!scanOrder?.picking?.lines?.length) return;
    const target = scanOrder.picking.lines.find(line => !line.verified && (line.sku === scanCode || !scanCode)) || scanOrder.picking.lines[0];
    setBusy(true);
    try {
      const picking = await transporte.solicitarScanPicking({ scanOrder, target, scanCode });
      setScanOrder({ ...scanOrder, picking });
      setScanCode("");
      toast.success("Artículo validado", target.name);
    } catch (error: unknown) {
      const detail = error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudo validar el artículo.";
      toast.error("Escaneo rechazado", detail);
    } finally {
      setBusy(false);
    }
  }

  async function completePicking() {
    if (!scanOrder) return;
    setBusy(true);
    try {
      await transporte.solicitarCompletePicking({ scanOrder });
      setScanOrder(null);
      toast.success("Entrega generada", "La preparación y la salida de inventario quedaron registradas.");
      await loadOrders();
    } catch (error: unknown) {
      const detail = error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudo completar la preparación.";
      toast.error("Error", detail);
    } finally {
      setBusy(false);
    }
  }

  async function openShortages(order: OrderItem) {
    try {
      const result = await transporte.solicitarOpenShortages({ order, shortages });
      setShortages(result.shortages);
      setShortageOrder(order);
    } catch (error: unknown) {
      const detail = error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudieron consultar los faltantes.";
      toast.error("Error", detail);
    }
  }

  async function resolveShortage(productId: string, action: string, warehouseIdValue?: string, substituteProductId?: string) {
    if (!shortageOrder) return;
    try {
      const estimated = action === "ESTIMATED_DATE" ? await prompt({ title: "Fecha estimada de reposición", label: "Fecha (AAAA-MM-DD)", defaultValue: new Date().toISOString().slice(0, 10) }) : undefined;
      await transporte.solicitarResolveShortage({ shortageOrder, productId, action, warehouseIdValue, substituteProductId, estimated });
      toast.success("Faltante gestionado", "La decisión quedó registrada en el historial.");
      setShortageOrder(null);
      await loadOrders();
    } catch (error: unknown) {
      const detail = error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudo gestionar el faltante.";
      toast.error("Error", detail);
    }
  }
  return { fulfillSerials, setFulfillSerials, ConfirmDialogNode, PromptDialogNode, orders, filterStatus, setFilterStatus, viewMode, setViewMode, selectedOrder, setSelectedOrder, loading, error, busy, fulfillModal, setFulfillModal, fulfillQuantities, setFulfillQuantities, editorOpen, setEditorOpen, editingOrder, setEditingOrder, customer, setCustomer, branches, warehouses, branchId, setBranchId, warehouseId, setWarehouseId, currency, lines, setLines, customerDrawerOpen, setCustomerDrawerOpen, productLineIndex, setProductLineIndex, scanOrder, setScanOrder, scanCode, setScanCode, shortageOrder, setShortageOrder, shortages, substitutes, setSubstitutes, loadOrders, handleConfirmAndReserve, openFulfillModal, handleFulfillSubmit, createOrder, editOrderLines, orderAction, scanPicking, completePicking, openShortages, resolveShortage };
}
