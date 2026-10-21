import * as transporte from "../api/PurchasesWorkspaceTab";
import { requestAllPages } from "../../../api/pagination";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { FormEvent, useEffect, useRef, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { notifyEntityChanged } from "../../../ui/entityEvents";
import { PurchaseEditorSource } from "../components/PurchaseOrderEditor";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { Supplier } from "../types/PurchasesWorkspaceTab";
import { PurchaseOrder } from "../types/PurchasesWorkspaceTab";
import { PurchaseRequisition } from "../types/PurchasesWorkspaceTab";
import { ReplenishmentSuggestion } from "../types/PurchasesWorkspaceTab";
import { SupplierPerformance } from "../types/PurchasesWorkspaceTab";
import { ReceiptActionChoice } from "../types/PurchasesWorkspaceTab";
import { ProcessTimeline } from "../types/PurchasesWorkspaceTab";

export function usePurchasesWorkspaceTab({ initialSubtab = "orders", initialModalType = null, initialActiveOrder = null }: {
  canWrite: boolean;
  initialSubtab?: "suppliers" | "orders" | "requisitions" | "replenishment";
  initialModalType?: string | null;
  initialActiveOrder?: PurchaseOrder | null;
}) {
  const [subtab, setSubtab] = useState<"suppliers" | "orders" | "requisitions" | "replenishment">(initialSubtab);

  const [suppliers, setSuppliers] = useState<Supplier[]>([]);

  const [orders, setOrders] = useState<PurchaseOrder[]>([]);

  const [requisitions, setRequisitions] = useState<PurchaseRequisition[]>([]);

  const [suggestions, setSuggestions] = useState<ReplenishmentSuggestion[]>([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [revision, setRevision] = useState(0);

  const [activeOrder, setActiveOrder] = useState<PurchaseOrder | null>(initialActiveOrder);

  const [activePerformance, setActivePerformance] = useState<SupplierPerformance | null>(null);

  const [activeTimeline, setActiveTimeline] = useState<ProcessTimeline | null>(null);

  const [activeReceiptId, setActiveReceiptId] = useState<string | null>(null);

  const [receiptChoices, setReceiptChoices] = useState<ReceiptActionChoice[]>([]);

  const [receiptLoading, setReceiptLoading] = useState(false);

  const [receiptError, setReceiptError] = useState("");

  const [returnProductId, setReturnProductId] = useState("");

  const [receiptActionBusy, setReceiptActionBusy] = useState(false);

  const receiptActionKey = useRef(crypto.randomUUID());

  const selectedReceipt = receiptChoices.find(item => item.id === activeReceiptId);

  const returnLine = selectedReceipt?.returnable_lines.find(item => item.product_id === returnProductId);

  const [modalType, setModalType] = useState<string | null>(initialModalType);

  const [warehouses, setWarehouses] = useState<{ warehouse_id: string; name: string; code: string }[]>([]);

  const [companyCurrency, setCompanyCurrency] = useState("");

  const [defaultTaxRate, setDefaultTaxRate] = useState("0");

  const [editorSource, setEditorSource] = useState<PurchaseEditorSource>();

  const [editorMode, setEditorMode] = useState<"order" | "requisition">("order");

  const [selectedSuggestions, setSelectedSuggestions] = useState<string[]>([]);

  const [replenishmentWarehouse, setReplenishmentWarehouse] = useState("");

  const [returnToOrderAfterSupplier, setReturnToOrderAfterSupplier] = useState(false);

  const toast = useToast();

  const { confirm, ConfirmDialogNode } = useConfirm();

  useEffect(() => {
    if (modalType !== "create_order" && modalType !== "create_supplier" && subtab !== "replenishment") return;
    Promise.all([
      transporte.solicitarDatos(),
      transporte.solicitarDatos2(),
      transporte.solicitarDatos3()
    ]).then(([warehouseRows, company, settings]) => {
      setWarehouses(warehouseRows);
      setCompanyCurrency(company.base_currency);
      setDefaultTaxRate(String(settings.default_tax_rate || "0"));
    }).catch(() => setError("Configura una moneda y un almacén activo antes de crear la orden."));
  }, [modalType, subtab]);

  useEffect(() => {
    setLoading(true);
    setError("");
    if (subtab === "suppliers") {
      requestAllPages<{ items: Supplier[] }>("/api/v1/suppliers?limit=100")
        .then(res => setSuppliers(res.items || []))
        .catch(err => setError(String(err?.detail || "Error al cargar proveedores")))
        .finally(() => setLoading(false));
    } else if (subtab === "orders") {
      requestAllPages<{ items: PurchaseOrder[] }>("/api/v1/purchase-orders?limit=100")
        .then(res => setOrders(res.items || []))
        .catch(err => setError(String(err?.detail || "Error al cargar órdenes de compra")))
        .finally(() => setLoading(false));
    } else if (subtab === "requisitions") {
      transporte.solicitarDatos4()
        .then(res => setRequisitions(res.items || []))
        .catch(err => setError(String(err?.detail || "Error al cargar solicitudes de compra")))
        .finally(() => setLoading(false));
    } else if (subtab === "replenishment") {
      transporte.solicitarDatos5({ replenishmentWarehouse })
        .then(res => setSuggestions(res.suggestions || []))
        .catch(err => setError(String(err?.detail || "Error al cargar sugerencias de reposición")))
        .finally(() => setLoading(false));
    }
  }, [subtab, revision, replenishmentWarehouse]);

  async function handleCreateSupplier(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      const created = await transporte.solicitarHandleCreateSupplier({ data, companyCurrency });
      notifyEntityChanged("supplier", created);
      toast.success("Proveedor registrado", "Ficha de proveedor creada con éxito.");
      setModalType(returnToOrderAfterSupplier ? "create_order" : null);
      setReturnToOrderAfterSupplier(false);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al registrar proveedor";
      toast.error("Error", msg);
    }
  }

  function prepareSuggestions(mode: "order" | "requisition") {
    const rows = suggestions.filter(item => selectedSuggestions.includes(item.product_id));
    if (!replenishmentWarehouse || !rows.length) return;
    if (rows.some(item => Number(item.suggested_quantity) <= 0)) { toast.warning("Sin faltante", "Selecciona únicamente productos con una cantidad sugerida positiva."); return; }
    if (new Set(rows.map(item => item.currency || companyCurrency)).size > 1 || (mode === "order" && new Set(rows.map(item => item.suggested_supplier_id || "")).size > 1)) { toast.warning("Separa las compras", "Selecciona productos del mismo proveedor y moneda para preparar una orden."); return; }
    const supplierIds = [...new Set(rows.map(item => item.suggested_supplier_id).filter(Boolean))];
    setEditorMode(mode);
    setEditorSource({ warehouse_id: replenishmentWarehouse, currency: rows[0]?.currency || companyCurrency, supplier_id: supplierIds.length === 1 ? supplierIds[0] : undefined, lines: rows.map(item => ({ product_id: item.product_id, quantity: Number(item.suggested_quantity) > 0 ? item.suggested_quantity : "1", unit_cost: item.unit_cost || "0" })) });
    setModalType("create_order");
  }

  async function handleApproveOrder(orderId: string) {
    try {
      await transporte.solicitarHandleApproveOrder({ orderId });
      toast.success("Orden aprobada", "La orden está autorizada para su recepción en almacén.");
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al aprobar orden";
      toast.error("Error", msg);
    }
  }

  useEffect(() => {
    if (!["landed_cost", "purchase_return"].includes(modalType || "") || !activeOrder) return;
    const controller = new AbortController();
    setActiveReceiptId(null);
    setReturnProductId("");
    setReceiptChoices([]);
    setReceiptError("");
    setReceiptLoading(true);
    transporte.solicitarDatos6({ activeOrder, controller }).then(result => { if (!controller.signal.aborted) setReceiptChoices(result.receipts); }).catch(failure => { if (!controller.signal.aborted) setReceiptError(failure?.detail || "No se pudieron consultar las recepciones de esta orden."); }).finally(() => { if (!controller.signal.aborted) setReceiptLoading(false); });
    return () => controller.abort();
  }, [modalType, activeOrder?.id]);

  useEffect(() => { receiptActionKey.current = crypto.randomUUID(); }, [activeReceiptId, modalType]);

  function receiptSelector() {
    return <div className="space-y-2">{receiptLoading && <p role="status" className="text-xs">Consultando recepciones de la orden…</p>}{receiptError && <p role="alert" className="text-xs text-rose-800">{receiptError}</p>}<label className="block text-xs font-semibold">Recepción de origen<CustomSelect aria-label="Recepción de origen" required value={activeReceiptId || ""} disabled={receiptLoading || receiptActionBusy} onChange={event => { setActiveReceiptId(event.target.value || null); setReturnProductId(""); }} className="mt-1 w-full"><option value="">Seleccionar una recepción real</option>{receiptChoices.filter(item => item.returnable_lines.some(line => Number(line.returnable_quantity) > 0)).map(item => <option key={item.id} value={item.id}>{new Date(item.created_at).toLocaleString("es-PE", { timeZone: "America/Lima" })} · {item.returnable_lines.filter(line => Number(line.returnable_quantity) > 0).map(line => `${line.sku}: ${line.returnable_quantity}`).join(" · ")}</option>)}</CustomSelect></label>{!receiptLoading && !receiptChoices.some(item => item.returnable_lines.some(line => Number(line.returnable_quantity) > 0)) && <p className="text-xs text-slate-500">No hay recepciones aceptadas con saldo disponible. Revisa la recepción o resuelve su cuarentena.</p>}</div>;
  }

  async function handleLandedCost(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const targetReceiptId = selectedReceipt?.id;
    if (!targetReceiptId || receiptActionBusy) return;
    const data = new FormData(event.currentTarget);
    if (!await confirm({ title: "¿Aplicar costos a esta recepción?", text: `Se distribuirá el cargo de ${String(data.get("amount"))} ${activeOrder?.details?.currency || ""} entre los artículos aceptados de la recepción seleccionada y se actualizará su valorización.`, confirmLabel: "Aplicar costos" })) return;
    setReceiptActionBusy(true);
    try {
      await transporte.solicitarHandleLandedCost({ targetReceiptId, receiptActionKey, data });
      toast.success("Costos prorrateados", "Ajuste de costo de adquisición registrado en Kardex.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al aplicar costos de adquisición";
      toast.error("Error", msg);
    } finally { setReceiptActionBusy(false); }
  }

  async function handlePurchaseReturn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeOrder) return;
    const data = new FormData(event.currentTarget);
    const line = returnLine;
    if (!selectedReceipt || !line || receiptActionBusy) return;
    if (!await confirm({ title: "¿Devolver artículos al proveedor?", text: `Se descontarán ${String(data.get("quantity"))} unidades de ${line.sku} del almacén de la recepción. Se registrará el crédito esperado del proveedor.`, danger: true, confirmLabel: "Devolver artículos" })) return;
    setReceiptActionBusy(true);
    try {
      await transporte.solicitarHandlePurchaseReturn({ receiptActionKey, selectedReceipt, activeOrder, line, data });
      toast.success("Devolución confirmada", "Salida de stock registrada y crédito esperado generado.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al procesar devolución";
      toast.error("Error", msg);
    } finally { setReceiptActionBusy(false); }
  }

  async function handleThreeWayMatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeOrder) return;
    const data = new FormData(event.currentTarget);
    try {
      const res = await transporte.solicitarHandleThreeWayMatch({ activeOrder, data });
      if (res.requires_review) {
        toast.warning("Diferencia detectada", `Discrepancia de S/ ${res.discrepancy_amount}. Estado en revisión.`);
      } else {
        toast.success("Conciliación conforme", "Orden, recepción y factura coinciden al 100%.");
      }
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al procesar conciliación";
      toast.error("Error", msg);
    }
  }

  async function handleViewPerformance(supplierId: string) {
    try {
      const res = await transporte.solicitarHandleViewPerformance({ supplierId });
      setActivePerformance(res);
      setModalType("supplier_performance");
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al consultar desempeño";
      toast.error("Error", msg);
    }
  }

  async function handleViewTimeline(orderId: string) {
    try {
      const res = await transporte.solicitarHandleViewTimeline({ orderId });
      setActiveTimeline(res);
      setModalType("order_timeline");
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al consultar ciclo de compra";
      toast.error("Error", msg);
    }
  }

  const filteredSuppliers = suppliers.filter(s =>
    s.legal_name.toLowerCase().includes(search.toLowerCase()) ||
    s.tax_id.includes(search)
  );
  return { subtab, setSubtab, orders, requisitions, suggestions, loading, error, search, setSearch, setRevision, activeOrder, setActiveOrder, activePerformance, activeTimeline, setActiveReceiptId, returnProductId, setReturnProductId, receiptActionBusy, selectedReceipt, returnLine, modalType, setModalType, warehouses, companyCurrency, defaultTaxRate, editorSource, setEditorSource, editorMode, setEditorMode, selectedSuggestions, setSelectedSuggestions, replenishmentWarehouse, setReplenishmentWarehouse, returnToOrderAfterSupplier, setReturnToOrderAfterSupplier, toast, ConfirmDialogNode, handleCreateSupplier, prepareSuggestions, handleApproveOrder, receiptSelector, handleLandedCost, handlePurchaseReturn, handleThreeWayMatch, handleViewPerformance, handleViewTimeline, filteredSuppliers };
}
