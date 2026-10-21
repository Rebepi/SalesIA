import { apiClient } from "../../../api/client";
import * as transporte from "../api/InventoryWorkspaceTab";
import { requestAllPages } from "../../../api/pagination";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { InventoryOperation } from "../components/InventoryOperationDialog";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { Submodule } from "../types/InventoryWorkspaceTab";
import { Warehouse } from "../types/InventoryWorkspaceTab";
import { Product } from "../types/InventoryWorkspaceTab";
import { StockItem } from "../types/InventoryWorkspaceTab";
import { KardexItem } from "../types/InventoryWorkspaceTab";
import { TransferItem } from "../types/InventoryWorkspaceTab";
import { CountItem } from "../types/InventoryWorkspaceTab";
import { LotItem } from "../types/InventoryWorkspaceTab";
import { SerialItem } from "../types/InventoryWorkspaceTab";
import { LocationItem } from "../types/InventoryWorkspaceTab";
import { RuleItem } from "../types/InventoryWorkspaceTab";
import { AlertItem } from "../types/InventoryWorkspaceTab";
import { QuarantineItem } from "../types/InventoryWorkspaceTab";

export function useInventoryWorkspaceTab({ initialSubmodule = "stock", initialTransfers = [], initialCounts = [] }: {
  canWrite: boolean;
  initialSubmodule?: Submodule;
  initialTransfers?: TransferItem[];
  initialCounts?: CountItem[];
}) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [submodule, setSubmodule] = useState<Submodule>(initialSubmodule);

  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);

  const [products, setProducts] = useState<Product[]>([]);

  const [selectedWarehouseId, setSelectedWarehouseId] = useState<string>("");

  const [search, setSearch] = useState("");

  const [revision, setRevision] = useState(0);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const toast = useToast();

  const navRef = useRef<HTMLElement | null>(null);

  const [canScrollLeft, setCanScrollLeft] = useState(false);

  const [canScrollRight, setCanScrollRight] = useState(false);

  const updateScrollIndicators = useCallback(() => {
    const el = navRef.current;
    if (!el) return;
    const { scrollLeft, scrollWidth, clientWidth } = el;
    const maxScroll = scrollWidth - clientWidth;
    setCanScrollLeft(scrollLeft > 2);
    setCanScrollRight(maxScroll > 2 && scrollLeft < maxScroll - 2);
  }, []);

  useEffect(() => {
    const el = navRef.current;
    if (!el) return;

    updateScrollIndicators();

    const handleWheel = (e: WheelEvent) => {
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        return;
      }
      e.preventDefault();
      el.scrollLeft += e.deltaY;
      updateScrollIndicators();
    };

    el.addEventListener("wheel", handleWheel, { passive: false });
    el.addEventListener("scroll", updateScrollIndicators, { passive: true });
    window.addEventListener("resize", updateScrollIndicators);

    return () => {
      el.removeEventListener("wheel", handleWheel);
      el.removeEventListener("scroll", updateScrollIndicators);
      window.removeEventListener("resize", updateScrollIndicators);
    };
  }, [updateScrollIndicators]);

  useEffect(() => {
    updateScrollIndicators();
    const container = navRef.current;
    if (!container) return;
    const activeBtn = container.querySelector<HTMLButtonElement>('[aria-current="page"]');
    if (activeBtn) {
      activeBtn.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
    }
  }, [submodule, updateScrollIndicators]);

  const [stockItems, setStockItems] = useState<StockItem[]>([]);

  const [kardexItems, setKardexItems] = useState<KardexItem[]>([]);

  const [transfers, setTransfers] = useState<TransferItem[]>(initialTransfers);

  const [counts, setCounts] = useState<CountItem[]>(initialCounts);

  const [lots, setLots] = useState<LotItem[]>([]);

  const [serials, setSerials] = useState<SerialItem[]>([]);

  const [locations, setLocations] = useState<LocationItem[]>([]);

  const [rules, setRules] = useState<RuleItem[]>([]);

  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  const [quarantineItems, setQuarantineItems] = useState<QuarantineItem[]>([]);

  const [trace, setTrace] = useState<{ kind: "lot" | "serial"; id: string }>();

  const [operation, setOperation] = useState<InventoryOperation | null>(null);

  const [countProductIds, setCountProductIds] = useState<string[]>([]);

  const [activeCount, setActiveCount] = useState<CountItem | null>(null);

  const [transferContext, setTransferContext] = useState({ sourceId: "", productId: "" });

  const [productFilter, setProductFilter] = useState("");

  const [modalType, setModalType] = useState<string | null>(null);

  const [activeTransfer, setActiveTransfer] = useState<TransferItem | null>(null);

  useEffect(() => {
    transporte.solicitarDatos()
      .then(list => {
        const active = list.filter(w => w.is_active);
        setWarehouses(active);
        if (active.length > 0 && !selectedWarehouseId) {
          setSelectedWarehouseId(active[0].warehouse_id);
        }
      })
      .catch((requestError) => setError(String(requestError?.detail || "No se pudieron cargar los almacenes.")));
    apiClient.request<{ items: Product[] }>("/api/v1/products?limit=20")
      .then(res => setProducts(res.items || []))
      .catch((requestError) => setError(String(requestError?.detail || "No se pudieron cargar los productos.")));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError("");
    const whParam = selectedWarehouseId ? `&warehouse_id=${selectedWarehouseId}` : "";
    if (submodule === "stock") {
      requestAllPages<{ items: StockItem[] }>(`/api/v1/inventory?limit=100${whParam}`)
        .then(res => setStockItems(res.items || []))
        .catch(err => setError(String(err?.detail || "Error al cargar existencias")))
        .finally(() => setLoading(false));
    } else if (submodule === "kardex") {
      requestAllPages<{ items: KardexItem[] }>(`/api/v1/inventory/movements?limit=100${whParam}${productFilter ? `&product_id=${productFilter}` : ""}`)
        .then(res => setKardexItems(res.items || []))
        .catch(err => setError(String(err?.detail || "Error al consultar kardex")))
        .finally(() => setLoading(false));
    } else if (submodule === "transfers") {
      transporte.solicitarDatos2()
        .then(res => setTransfers(res.items || []))
        .catch(err => setError(String(err?.detail || "Error al consultar transferencias")))
        .finally(() => setLoading(false));
    } else if (submodule === "counts") {
      transporte.solicitarDatos3({ whParam })
        .then(res => setCounts(res.items || []))
        .catch(err => setError(String(err?.detail || "Error al consultar conteos")))
        .finally(() => setLoading(false));
    } else if (submodule === "lots_serials") {
      Promise.all([
        transporte.solicitarDatos4(),
        transporte.solicitarDatos5()
      ])
        .then(([lotsRes, serialsRes]) => {
          setLots(lotsRes.items || []);
          setSerials(serialsRes.items || []);
        })
        .catch(err => setError(String(err?.detail || "Error al cargar lotes y series")))
        .finally(() => setLoading(false));
    } else if (submodule === "locations_rules") {
      Promise.all([
        transporte.solicitarDatos6({ whParam }),
        transporte.solicitarDatos7()
      ])
        .then(([locRes, ruleRes]) => {
          setLocations(locRes.items || []);
          setRules(ruleRes.items || []);
        })
        .catch(err => setError(String(err?.detail || "Error al cargar ubicaciones y reglas")))
        .finally(() => setLoading(false));
    } else if (submodule === "alerts_reconcile") {
      Promise.all([
        transporte.solicitarDatos8(),
        transporte.solicitarDatos9()
      ])
        .then(([alertRes, quarRes]) => {
          setAlerts(alertRes.items || []);
          setQuarantineItems(quarRes.items || []);
        })
        .catch(err => setError(String(err?.detail || "Error al cargar alertas y cuarentena")))
        .finally(() => setLoading(false));
    }
  }, [submodule, selectedWarehouseId, revision, productFilter]);

  async function handleDispatchTransfer(transferId: string) {
    try {
      await transporte.solicitarHandleDispatchTransfer({ transferId });
      toast.success("Despacho confirmado", "El stock pasó a estado de tránsito.");
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al despachar";
      toast.error("Error", msg);
    }
  }

  async function handleCreateCount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const whId = String(data.get("warehouse_id"));
    const notes = String(data.get("notes") || "");
    try {
      await transporte.solicitarHandleCreateCount({ whId, notes, countProductIds });
      toast.success("Sesión de conteo creada", "El conteo ciego está habilitado para registro de cantidades.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al crear conteo";
      toast.error("Error", msg);
    }
  }

  async function handleApproveCount(countId: string) {
    if (!await confirm({ title: "¿Aprobar conteo físico?", text: "Se ajustarán las existencias según las diferencias revisadas y se registrará cada cambio en Kardex. Para corregirlo será necesario otro ajuste.", confirmLabel: "Aprobar" })) return;
    try {
      await transporte.solicitarHandleApproveCount({ countId });
      toast.success("Conteo aprobado", "Diferencias aplicadas a kardex exactamente una vez.");
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al aprobar conteo";
      toast.error("Error de aprobación", msg);
    }
  }

  async function handleRecalculateAlerts() {
    try {
      const res = await transporte.solicitarHandleRecalculateAlerts();
      toast.success("Alertas recalculadas", `${res.active_alerts_count} alertas activas detectadas.`);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al recalcular alertas";
      toast.error("Error", msg);
    }
  }

  async function handleRunReconcile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const whId = String(data.get("warehouse_id"));
    const prodId = String(data.get("product_id"));
    try {
      const res = await transporte.solicitarHandleRunReconcile({ whId, prodId });
      if (res.status === "MATCH") {
        toast.success("Auditoría conforme", `Saldo stock (${res.cached_stock_balance}) concilia con libro mayor (${res.ledger_balance}).`);
      } else {
        toast.warning("Discrepancia detectada", `Diferencia de ${res.discrepancy_delta} unidades entre kardex y saldo.`);
      }
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error en reconciliación";
      toast.error("Error", msg);
    }
  }

  async function handleClassifyQuarantine(id: string, action: "RESTOCK" | "SCRAP") {
    try {
      await transporte.solicitarHandleClassifyQuarantine({ id, action });
      toast.success("Clasificación guardada", action === "RESTOCK" ? "Unidades reintegradas a disponible." : "Unidades desechadas.");
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al clasificar";
      toast.error("Error", msg);
    }
  }

  const [referencedProductNames, setReferencedProductNames] = useState<Record<string, string>>({});
  useEffect(() => {
    const ids = Array.from(new Set([...lots, ...serials, ...rules, ...quarantineItems].map(item => item.product_id).filter(Boolean)));
    if (!ids.length) return;
    const controller = new AbortController();
    void (async () => {
      const labels: Record<string, string> = {};
      for (let index = 0; index < ids.length; index += 50) {
        const params = new URLSearchParams({ ids: ids.slice(index, index + 50).join(","), limit: "50" });
        const result = await apiClient.request<{ items: { value: string; label: string }[] }>(`/api/v1/selector-options/products?${params}`, { signal: controller.signal });
        if (controller.signal.aborted) return;
        for (const item of result.items) labels[item.value] = item.label;
      }
      if (!controller.signal.aborted) setReferencedProductNames(previous => ({ ...previous, ...labels }));
    })().catch(() => undefined);
    return () => controller.abort();
  }, [lots, serials, rules, quarantineItems]);

  const productName = (id: string) => { const item = products.find(product => product.id === id); const stock = stockItems.find(row => row.product_id === id); return item ? `${item.sku} · ${item.name}` : referencedProductNames[id] || (stock ? `${stock.sku} · ${stock.product_name}` : `Producto ${id.slice(0, 8)}`); };

  const warehouseName = (id: string) => warehouses.find(item => item.warehouse_id === id)?.name || "Almacén no disponible";

  async function blockLot(id: string) {
    if (!await confirm({ title: "¿Bloquear lote?", text: "El lote quedará bloqueado para su venta. Revisa las reservas y operaciones pendientes.", danger: true, confirmLabel: "Bloquear" })) return;
    try {
      await transporte.solicitarBlockLot({ id });
      setRevision(value => value + 1);
      toast.success("Lote bloqueado", "El lote quedó retenido para revisión.");
    } catch { toast.error("No se pudo bloquear", "Actualiza el inventario e intenta nuevamente."); }
  }

  async function deactivateRule(id: string) {
    if (!await confirm({ title: "¿Desactivar regla?", text: "La regla dejará de generar sugerencias de reposición. Podrás reactivarla guardando su configuración.", danger: true, confirmLabel: "Desactivar" })) return;
    try {
      await transporte.solicitarDeactivateRule({ id });
      setRevision(value => value + 1);
    } catch { toast.error("No se pudo desactivar", "Actualiza las reglas e intenta nuevamente."); }
  }

  const filteredStock = stockItems.filter(item =>
    !search || item.product_name.toLowerCase().includes(search.toLowerCase()) || item.sku.toLowerCase().includes(search.toLowerCase())
  );

  const totalAvailable = stockItems.reduce((acc, item) => acc + Number(item.available_quantity || 0), 0);

  const totalInTransit = stockItems.reduce((acc, item) => acc + Number(item.transit_quantity || 0), 0);

  const totalQuarantine = stockItems.reduce((acc, item) => acc + Number(item.quarantine_quantity || 0), 0);

  const totalReserved = stockItems.reduce((acc, item) => acc + Number(item.reserved_quantity || 0), 0);
  return { ConfirmDialogNode, submodule, setSubmodule, warehouses, products, selectedWarehouseId, setSelectedWarehouseId, search, setSearch, setRevision, loading, error, navRef, canScrollLeft, canScrollRight, kardexItems, transfers, counts, lots, serials, locations, rules, alerts, quarantineItems, trace, setTrace, operation, setOperation, countProductIds, setCountProductIds, activeCount, setActiveCount, transferContext, setTransferContext, setProductFilter, modalType, setModalType, activeTransfer, setActiveTransfer, handleDispatchTransfer, handleCreateCount, handleApproveCount, handleRecalculateAlerts, handleRunReconcile, handleClassifyQuarantine, productName, warehouseName, blockLot, deactivateRule, filteredStock, totalAvailable, totalInTransit, totalQuarantine, totalReserved };
}
