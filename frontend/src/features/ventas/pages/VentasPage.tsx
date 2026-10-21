import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { CheckSquare, ChevronLeft, ChevronRight } from "lucide-react";
import { VentasKPIBar } from "../components/VentasKPIBar";
import { VentasToolbar } from "../components/VentasToolbar";
import { VentasTable } from "../components/VentasTable";
import { VentasBulkActionBar } from "../components/VentasBulkActionBar";
import { VentasPostPaymentModal } from "../components/VentasPostPaymentModal";
import { VentasAnulacionModal } from "../components/VentasAnulacionModal";
import { VentasReprogramarModal } from "../components/VentasReprogramarModal";
import { VentasComunicacionModal } from "../components/VentasComunicacionModal";
import { VentasDevolucionModal } from "../components/VentasDevolucionModal";
import { VentasNotaDebitoModal } from "../components/VentasNotaDebitoModal";
import { VentasGuiaRemisionModal } from "../components/VentasGuiaRemisionModal";
import { SaleRecord, SaleKPIs, VentasFilterState, SavedView } from "../types/ventas";
import { exportToCSV, exportToExcel, exportToPDF, exportSaleVoucherPDF } from "../utils/formateadores";
import { filtrosEjecutivos } from "../utils/filtrosEjecutivos";
import { apiClient } from "../../../api/client";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { setDefaultPageSize as persistDefaultPageSize } from "../../../ui/preferences";

const DEFAULT_FILTER: VentasFilterState = {
  only_zero_cost: false,
  only_unassigned: false,
  only_with_lines: false,
  category: "",
  date_basis: "created",
  dashboard_period: "",
  dashboard_as_of: "",
  search: "",
  date_shortcut: "all",
  date_from: "",
  date_to: "",
  customer_id: "",
  sales_rep_id: "",
  branch_id: "",
  warehouse_id: "",
  document_type: "",
  currency: "",
  document_status: "",
  payment_status: "",
  delivery_status: "",
  sunat_status: "",
  return_status: "",
  payment_method: "",
  min_amount: "",
  max_amount: "",
  only_with_balance: false,
  only_overdue: false,
  only_with_returns: false,
  origin: "",
};

const DEFAULT_COLUMNS = [
  { key: "created_at", label: "Fecha / Hora", visible: true },
  { key: "voucher_type", label: "Tipo", visible: false },
  { key: "document", label: "Documento", visible: true },
  { key: "customer", label: "Cliente", visible: true },
  { key: "sales_rep", label: "Vendedor", visible: false },
  { key: "branch", label: "Sede", visible: false },
  { key: "total", label: "Total", visible: true },
  { key: "paid", label: "Cobrado", visible: false },
  { key: "balance", label: "Saldo", visible: true },
  { key: "due_date", label: "Vencimiento", visible: false },
  { key: "statuses", label: "Estados", visible: true },
];

const EMPTY_KPIS: SaleKPIs = {
  today_count: 0,
  today_amount: 0,
  month_count: 0,
  month_amount: 0,
  receivable_count: 0,
  receivable_amount: 0,
  overdue_count: 0,
  overdue_amount: 0,
  pending_delivery_count: 0,
  sunat_rejected_count: 0,
  old_drafts_count: 0,
};

const LOCAL_VIEWS_KEY = "salesia_ventas_saved_views";
const LOCAL_KPI_CFG_KEY = "salesia_ventas_kpi_cfg";

function loadSavedViews(): SavedView[] {
  try {
    return JSON.parse(localStorage.getItem(LOCAL_VIEWS_KEY) || "[]");
  } catch {
    return [];
  }
}

function persistViews(views: SavedView[]) {
  try {
    localStorage.setItem(LOCAL_VIEWS_KEY, JSON.stringify(views));
  } catch {}
}

function loadKpiCfg(): { visible: boolean; clickable: boolean } {
  try {
    return JSON.parse(localStorage.getItem(LOCAL_KPI_CFG_KEY) || JSON.stringify({ visible: false, clickable: true }));
  } catch {
    return { visible: false, clickable: true };
  }
}

function persistKpiCfg(cfg: { visible: boolean; clickable: boolean }) {
  try {
    localStorage.setItem(LOCAL_KPI_CFG_KEY, JSON.stringify(cfg));
  } catch {}
}

interface VentasPageProps {
  canWrite?: boolean;
  canReadCosts?: boolean;
  canCancel?: boolean;
  onOpenNewSale?: (saleId?: string) => void;
  onOpenDetail?: (sale: SaleRecord) => void;
  branches?: Array<{ branch_id?: string; id?: string; name: string }>;
  salesReps?: Array<{ id: string; full_name: string }>;
  warehouses?: Array<{ warehouse_id?: string; id?: string; name: string }>;
  currency?: string;
  revision?: number;
}

export function VentasPage({
  canWrite = true,
  canReadCosts = false,
  canCancel = true,
  onOpenNewSale,
  onOpenDetail,
  branches = [],
  salesReps = [],
  warehouses = [],
  currency = "USD",
  revision: parentRevision = 0,
}: VentasPageProps) {
  const [rows, setRows] = useState<SaleRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [matchingLines, setMatchingLines] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(() => {
    const pref = Number(typeof window !== "undefined" ? window.localStorage.getItem("salesia_default_page_size") : null);
    return [10, 25, 50, 100].includes(pref) ? pref : 50;
  });
  const [filter, setFilter] = useState<VentasFilterState>(() => filtrosEjecutivos(DEFAULT_FILTER, window.location.search));
  const [sortField, setSortField] = useState("created_at");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [kpis, setKpis] = useState<SaleKPIs>(EMPTY_KPIS);
  const [kpiBarVisible, setKpiBarVisible] = useState(() => loadKpiCfg().visible);
  const [kpiClickable, setKpiClickable] = useState(() => loadKpiCfg().clickable);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectionMode, setSelectionMode] = useState(false);
  const [columnsConfig, setColumnsConfig] = useState(DEFAULT_COLUMNS);
  const [savedViews, setSavedViews] = useState<SavedView[]>(loadSavedViews);
  const [selectedViewId, setSelectedViewId] = useState("");
  const [revision, setRevision] = useState(0);
  const effectiveRevision = revision + parentRevision;

  const [paymentTarget, setPaymentTarget] = useState<SaleRecord | null>(null);
  const [anulacionTarget, setAnulacionTarget] = useState<SaleRecord | null>(null);
  const [reprogramarTarget, setReprogramarTarget] = useState<SaleRecord | null>(null);
  const [comunicacionTarget, setComunicacionTarget] = useState<SaleRecord | null>(null);
  const [devolucionTarget, setDevolucionTarget] = useState<SaleRecord | null>(null);
  const [debitNoteTarget, setDebitNoteTarget] = useState<SaleRecord | null>(null);
  const [guideTarget, setGuideTarget] = useState<SaleRecord | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const buildQueryParams = useCallback(
    (f: VentasFilterState, p: number, ps: number): string => {
      const params = new URLSearchParams();
      params.set("page", String(p));
      params.set("page_size", String(ps));
      if (f.search) params.set("q", f.search);
      if (f.customer_id) params.set("customer_id", f.customer_id);
      if (f.sales_rep_id) params.set("sales_rep_id", f.sales_rep_id);
      if (f.branch_id) params.set("branch_id", f.branch_id);
      if (f.warehouse_id) params.set("warehouse_id", f.warehouse_id);
      if (f.currency) params.set("currency", f.currency);
      if (f.document_status) {
        const s = f.document_status.trim();
        const map: Record<string, string> = {
          Borrador: "draft",
          Confirmada: "confirmed",
          Anulada: "cancelled",
        };
        params.set("status", map[s] || s.toLowerCase());
        params.set("document_status", f.document_status);
      }
      if (f.date_shortcut && f.date_shortcut !== "all") {
        params.set("date_shortcut", f.date_shortcut);
      }
      if (f.date_from) params.set("date_from", f.date_from);
      if (f.date_to) params.set("date_to", f.date_to);
      if (f.document_type) params.set("document_type", f.document_type);
      if (f.payment_status) params.set("payment_status", f.payment_status);
      if (f.delivery_status) params.set("delivery_status", f.delivery_status);
      if (f.sunat_status) params.set("sunat_status", f.sunat_status);
      if (f.return_status) params.set("return_status", f.return_status);
      if (f.min_amount) params.set("min_amount", f.min_amount);
      if (f.max_amount) params.set("max_amount", f.max_amount);
      if (f.only_with_balance) params.set("only_with_balance", "true");
      if (f.only_overdue) params.set("only_overdue", "true");
      if (f.only_with_returns) params.set("only_with_returns", "true");
      if (f.origin) params.set("origin", f.origin);
      if (f.only_zero_cost) params.set("only_zero_cost", "true");
      if (f.only_unassigned) params.set("only_unassigned", "true");
      if (f.only_with_lines) params.set("only_with_lines", "true");
      if (f.category) params.set("category", f.category);
      if (f.date_basis) params.set("date_basis", f.date_basis);
      if (f.dashboard_period) params.set("dashboard_period", f.dashboard_period);
      if (f.dashboard_as_of) params.set("dashboard_as_of", f.dashboard_as_of);
      return params.toString();
    },
    []
  );

  useEffect(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError("");
    setMatchingLines(null);

    const qs = buildQueryParams(filter, page, pageSize);

    apiClient
      .request<{ items: SaleRecord[]; total?: number; total_count?: number; matching_lines_count?: number | null } | SaleRecord[]>(`/api/v1/sales?${qs}`, { signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted) {
          if (Array.isArray(res)) {
            setRows(res);
            setTotal(res.length);
          } else {
            const data = res as { items?: SaleRecord[]; total?: number; total_count?: number; matching_lines_count?: number | null };
            setMatchingLines(data.matching_lines_count ?? null);
            const fetched = data.items || [];
            const count = Number(data.total ?? data.total_count ?? fetched.length);
            setRows(fetched);
            setTotal(count);
          }
        }
      })
      .catch((failure) => {
        if (!controller.signal.aborted) {
          setError(String(failure?.detail || failure?.message || "No se pudieron cargar las ventas."));
          setRows([]);
          setTotal(0);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [filter, page, pageSize, effectiveRevision, buildQueryParams]);

  useEffect(() => {
    apiClient
      .request<SaleKPIs>("/api/v1/sales/kpis")
      .then((res) => setKpis(res || EMPTY_KPIS))
      .catch(() => setKpis(EMPTY_KPIS));
  }, [effectiveRevision]);

  const filteredRows = useMemo(() => {
    const list = rows.filter((r) => {
      if (filter.document_status) {
        const s = filter.document_status.trim();
        const sLower = s.toLowerCase();
        const rDoc = (r.document_status || "").toLowerCase();
        const rRaw = (r.status || "").toLowerCase();
        const isDraft = (sLower === "borrador" || sLower === "draft") && (rDoc === "borrador" || rRaw === "draft");
        const isConf = (sLower === "confirmada" || sLower === "confirmed") && (rDoc === "confirmada" || rRaw === "confirmed" || rRaw === "paid");
        const isCanc = (sLower === "anulada" || sLower === "cancelled") && (rDoc === "anulada" || rRaw === "cancelled");
        if (!isDraft && !isConf && !isCanc && rDoc !== sLower) return false;
      }

      if (filter.search) {
        const q = filter.search.toLowerCase().trim();
        const doc = (r.number || "").toLowerCase();
        const cust = (r.customer_name || "").toLowerCase();
        const custDoc = (r.customer_document || "").toLowerCase();
        const tot = String(r.total_amount || "");
        if (!doc.includes(q) && !cust.includes(q) && !custDoc.includes(q) && !tot.includes(q)) {
          return false;
        }
      }

      if (filter.document_type) {
        const dt = filter.document_type.toUpperCase();
        if (dt === "INVOICE" && !r.series?.startsWith("F") && r.document_type !== "INVOICE") return false;
        if (dt === "RECEIPT" && !r.series?.startsWith("B") && r.document_type !== "RECEIPT") return false;
        if (dt === "SALE_NOTE" && !r.series?.startsWith("NV") && !r.series?.startsWith("N") && r.document_type !== "SALE_NOTE") return false;
      }

      if (filter.payment_status) {
        const ps = filter.payment_status.toLowerCase();
        const rPs = (r.payment_status || "").toLowerCase();
        if (rPs !== ps) return false;
      }

      if (filter.delivery_status) {
        const ds = filter.delivery_status.toLowerCase();
        const rDs = (r.delivery_status || "").toLowerCase();
        if (rDs !== ds) return false;
      }

      if (filter.sunat_status) {
        const ss = filter.sunat_status.toLowerCase();
        const rSs = (r.sunat_status || "").toLowerCase();
        if (rSs !== ss) return false;
      }

      if (filter.return_status) {
        const rs = filter.return_status.toLowerCase();
        const rRs = (r.return_status || "").toLowerCase();
        if (rRs !== rs) return false;
      }

      if (filter.only_with_balance) {
        const bal = Number(r.balance_amount ?? (Number(r.total_amount) - Number(r.paid_amount)));
        if (bal <= 0) return false;
      }

      if (filter.only_overdue) {
        const bal = Number(r.balance_amount ?? (Number(r.total_amount) - Number(r.paid_amount)));
        if (bal <= 0) return false;
      }

      if (filter.only_with_returns) {
        if (!r.return_status || r.return_status === "Sin devolución") return false;
      }

      if (filter.min_amount) {
        const min = Number(filter.min_amount);
        if (!isNaN(min) && Number(r.total_amount) < min) return false;
      }

      if (filter.max_amount) {
        const max = Number(filter.max_amount);
        if (!isNaN(max) && Number(r.total_amount) > max) return false;
      }

      if (filter.branch_id) {
        if (r.branch_id && r.branch_id !== filter.branch_id) return false;
      }

      if (filter.sales_rep_id) {
        if (r.sales_rep_id && r.sales_rep_id !== filter.sales_rep_id) return false;
      }

      if (filter.warehouse_id) {
        if (r.warehouse_id && r.warehouse_id !== filter.warehouse_id) return false;
      }

      if (filter.currency) {
        if (r.currency && r.currency.toUpperCase() !== filter.currency.toUpperCase()) return false;
      }

      if (filter.origin) {
        if (r.origin && r.origin !== filter.origin) return false;
      }

      if (filter.date_basis !== "confirmed" && filter.date_shortcut && filter.date_shortcut !== "all" && r.created_at) {
        const rDate = new Date(r.created_at);
        const now = new Date();
        if (filter.date_shortcut === "today") {
          const isToday = rDate.toISOString().substring(0, 10) === now.toISOString().substring(0, 10);
          if (!isToday) return false;
        } else if (filter.date_shortcut === "yesterday") {
          const yest = new Date(now.getTime() - 86400000);
          const isYest = rDate.toISOString().substring(0, 10) === yest.toISOString().substring(0, 10);
          if (!isYest) return false;
        } else if (filter.date_shortcut === "this_month") {
          const isThisMonth = rDate.getFullYear() === now.getFullYear() && rDate.getMonth() === now.getMonth();
          if (!isThisMonth) return false;
        } else if (filter.date_shortcut === "last_30_days") {
          const diffDays = (now.getTime() - rDate.getTime()) / (1000 * 3600 * 24);
          if (diffDays > 30 || diffDays < 0) return false;
        }
      }

      if (filter.date_basis !== "confirmed") {
        if (filter.date_from && r.created_at && r.created_at.substring(0, 10) < filter.date_from) return false;
        if (filter.date_to && r.created_at && r.created_at.substring(0, 10) > filter.date_to) return false;
      }

      return true;
    });

    return list.slice().sort((a: SaleRecord, b: SaleRecord) => {
      let valA: any = "";
      let valB: any = "";

      if (sortField === "created_at") {
        valA = a.created_at ? new Date(a.created_at).getTime() : 0;
        valB = b.created_at ? new Date(b.created_at).getTime() : 0;
      } else if (sortField === "number") {
        valA = a.number || "";
        valB = b.number || "";
      } else if (sortField === "customer_name") {
        valA = (a.customer_name || "").toLowerCase();
        valB = (b.customer_name || "").toLowerCase();
      } else if (sortField === "total_amount") {
        valA = Number(a.total_amount || 0);
        valB = Number(b.total_amount || 0);
      } else if (sortField === "paid_amount") {
        valA = Number(a.paid_amount || 0);
        valB = Number(b.paid_amount || 0);
      } else if (sortField === "balance") {
        valA = Number(a.balance_amount ?? Math.max(0, Number(a.total_amount || 0) - Number(a.paid_amount || 0)));
        valB = Number(b.balance_amount ?? Math.max(0, Number(b.total_amount || 0) - Number(b.paid_amount || 0)));
      } else if (sortField === "due_date") {
        valA = a.due_date ? new Date(a.due_date).getTime() : 0;
        valB = b.due_date ? new Date(b.due_date).getTime() : 0;
      } else if (sortField === "voucher_type") {
        valA = (a.voucher_type || a.document_type || "").toLowerCase();
        valB = (b.voucher_type || b.document_type || "").toLowerCase();
      } else if (sortField === "sales_rep_name") {
        valA = (a.sales_rep_name || "").toLowerCase();
        valB = (b.sales_rep_name || "").toLowerCase();
      } else if (sortField === "branch_name") {
        valA = (a.branch_name || "").toLowerCase();
        valB = (b.branch_name || "").toLowerCase();
      } else {
        valA = (a as any)[sortField] ?? "";
        valB = (b as any)[sortField] ?? "";
      }

      if (valA < valB) return sortDirection === "asc" ? -1 : 1;
      if (valA > valB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [rows, filter, sortField, sortDirection]);

  const filterTotalsSummary = useMemo(() => {
    const pageTotal = filteredRows.reduce((s, r) => s + Number(r.total_amount || 0), 0);
    const pagePaid = filteredRows.reduce((s, r) => s + Number(r.paid_amount || 0), 0);
    const pageBalance = filteredRows.reduce((s, r) => s + Number(r.balance_amount ?? (Number(r.total_amount) - Number(r.paid_amount))), 0);
    return {
      page_total: pageTotal,
      page_paid: pagePaid,
      page_balance: pageBalance,
      filter_total: pageTotal,
      filter_paid: pagePaid,
      filter_balance: pageBalance,
      filter_count: filteredRows.length,
    };
  }, [filteredRows]);

  function handleFilterChange(patch: Partial<VentasFilterState>) {
    const changesDates = "date_from" in patch || "date_to" in patch || "date_shortcut" in patch || "date_basis" in patch;
    setFilter((prev) => ({ ...prev, ...(changesDates ? { dashboard_period: "", dashboard_as_of: "" } : {}), ...patch }));
    setPage(1);
    setSelectedIds([]);
  }

  function handleResetFilters() {
    setFilter(DEFAULT_FILTER);
    setPage(1);
    setSelectedIds([]);
    setSelectedViewId("");
  }

  function handleSort(field: string) {
    if (field === sortField) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  }

  function handleSelectRow(id: string) {
    setSelectedIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  }

  function handleSelectAll() {
    if (selectedIds.length === filteredRows.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredRows.map((r) => r.id));
    }
  }

  function handleToggleColumn(key: string) {
    setColumnsConfig((prev) => prev.map((c) => c.key === key ? { ...c, visible: !c.visible } : c));
  }

  function handleResetColumns() {
    setColumnsConfig(DEFAULT_COLUMNS.map((c) => ({ ...c })));
  }

  function handleSelectSavedView(view: SavedView) {
    setSelectedViewId(view.id);
    setFilter({ ...DEFAULT_FILTER, ...view.filters });
    if (view.columns) {
      setColumnsConfig((prev) => prev.map((c) => ({ ...c, visible: (view.columns || []).includes(c.key) })));
    }
    setPage(1);
    setSelectedIds([]);
  }

  function handleSaveCurrentView(name: string) {
    const newView: SavedView = {
      id: `view_${Date.now()}`,
      name,
      filters: { ...filter },
      columns: columnsConfig.filter((c) => c.visible).map((c) => c.key),
    };
    const next = [...savedViews, newView];
    setSavedViews(next);
    persistViews(next);
    setSelectedViewId(newView.id);
  }

  const selectedRows = useMemo(() => filteredRows.filter((r) => selectedIds.includes(r.id)), [filteredRows, selectedIds]);

  async function handleConfirmSale(saleId: string) {
    try {
      await apiClient.request(`/api/v1/sales/${saleId}/confirm`, { method: "POST", body: JSON.stringify({ is_credit_sale: false }) });
      setRevision((v) => v + 1);
    } catch {
  
    }
  }

  function handleOpenDetail(sale: SaleRecord) {
    if (onOpenDetail) {
      onOpenDetail(sale);
    }
  }

  function handleDownloadXml(sale: SaleRecord) {
    const docNumber = sale.number || sale.id?.substring(0, 8);
    const xmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <ID>${docNumber}</ID>
  <IssueDate>${sale.created_at ? sale.created_at.substring(0, 10) : new Date().toISOString().substring(0, 10)}</IssueDate>
  <CustomerName>${sale.customer_name || "CLIENTE GENERAL"}</CustomerName>
  <PayableAmount currencyID="${sale.currency || "USD"}">${Number(sale.total_amount || 0).toFixed(2)}</PayableAmount>
</Invoice>`;
    const blob = new Blob([xmlContent], { type: "application/xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${docNumber}.xml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function handleDownloadPdf(sale: SaleRecord) {
    exportSaleVoucherPDF(sale);
  }

  return (
    <section className="flex flex-col flex-1 min-h-0 h-full w-full max-w-none gap-2.5 sm:gap-3 overflow-hidden" id="ventas-page-root">
      {kpiBarVisible && (
        <div className="shrink-0 w-full">
          <VentasKPIBar
            kpis={kpis}
            activeFilter={filter}
            onSelectKpi={handleFilterChange}
            currency={currency}
            clickable={kpiClickable}
          />
        </div>
      )}

      {(filter.dashboard_period || filter.only_zero_cost || filter.only_unassigned || filter.only_with_lines || filter.category) && <div className="shrink-0 w-full flex flex-wrap items-center gap-2 rounded-xl border border-teal-200 bg-teal-50 px-4 py-2 text-xs text-teal-800 dark:border-teal-900 dark:bg-teal-950/30 dark:text-teal-300">{filter.dashboard_period && <span>Desde Inicio ejecutivo · {filter.dashboard_period === "all" ? "Todo el historial" : filter.dashboard_period === "12m" ? "Últimos 12 meses" : `Últimos ${filter.dashboard_period.replace("d", "")} días`} · {filter.currency} · {filter.branch_id ? branches.find(branch => (branch.branch_id || branch.id) === filter.branch_id)?.name || filter.branch_id : "Todas las sedes"}</span>}{filter.only_zero_cost && <button type="button" onClick={() => handleFilterChange({ only_zero_cost: false })}>Con líneas de costo cero ×</button>}{filter.only_unassigned && <button type="button" onClick={() => handleFilterChange({ only_unassigned: false })}>Sin vendedor asignado ×</button>}{filter.only_with_lines && <button type="button" onClick={() => handleFilterChange({ only_with_lines: false })}>Con detalle de productos ×</button>}{filter.category && <button type="button" onClick={() => handleFilterChange({ category: "" })}>Categoría: {filter.category} ×</button>}{!loading && filter.only_zero_cost && matchingLines !== null && <strong>{matchingLines} {matchingLines === 1 ? "línea" : "líneas"} en {total} {total === 1 ? "venta" : "ventas"}</strong>}<button type="button" className="ml-auto font-semibold underline" onClick={() => window.dispatchEvent(new CustomEvent("salesia:navigate", { detail: { view: "dashboard" } }))}>Volver al dashboard</button></div>}
      {error && <p role="alert" className="shrink-0 text-sm text-rose-600 dark:text-rose-400">{error}</p>}
      <div className="shrink-0 w-full">
        <VentasToolbar
          canReadCosts={canReadCosts}
          filter={filter}
          onFilterChange={handleFilterChange}
          onResetFilters={handleResetFilters}
          onRefresh={() => setRevision((v) => v + 1)}
          loading={loading}
          canWrite={canWrite}
          onOpenNewSale={onOpenNewSale || (() => { })}
          onExportCSV={() => exportToCSV(selectedIds.length > 0 ? selectedRows : filteredRows)}
          onExportExcel={() => exportToExcel(selectedIds.length > 0 ? selectedRows : filteredRows)}
          onExportPDF={() => exportToPDF(selectedIds.length > 0 ? selectedRows : filteredRows)}
          savedViews={savedViews}
          selectedViewId={selectedViewId}
          onSelectSavedView={handleSelectSavedView}
          onSaveCurrentView={handleSaveCurrentView}
          columnsConfig={columnsConfig}
          onToggleColumn={handleToggleColumn}
          onResetColumns={handleResetColumns}
          branches={branches}
          salesReps={salesReps}
          warehouses={warehouses}
          totalsSummary={filterTotalsSummary}
          currency={currency}
          kpiBarVisible={kpiBarVisible}
          onToggleKpiBar={(visible) => {
            setKpiBarVisible(visible);
            persistKpiCfg({ visible, clickable: kpiClickable });
          }}
          kpiClickable={kpiClickable}
          onToggleKpiClickable={(clickable) => {
            setKpiClickable(clickable);
            persistKpiCfg({ visible: kpiBarVisible, clickable });
          }}
        />
      </div>

      <VentasTable
        rows={filteredRows}
        loading={loading}
        selectionMode={selectionMode}
        selectedIds={selectedIds}
        onSelectRow={handleSelectRow}
        onSelectAll={handleSelectAll}
        canWrite={canWrite}
        canCancel={canCancel}
        onOpenDetail={handleOpenDetail}
        onConfirmSale={(sale) => handleConfirmSale(sale.sale_id || sale.id)}
        onOpenPayment={(sale) => setPaymentTarget(sale)}
        onRepeatSale={(sale) => {
          const sid = sale.sale_id || sale.id;
          if (onOpenNewSale) {
            sessionStorage.setItem("salesia_repeat_sale_id", sid);
            onOpenNewSale(sid);
          }
        }}
        onDuplicateDraft={(sale) => {
          const sid = sale.sale_id || sale.id;
          if (onOpenNewSale) {
            sessionStorage.setItem("salesia_repeat_sale_id", sid);
            onOpenNewSale(sid);
          }
        }}
        onDeleteDraft={async (sale) => {
          try {
            await apiClient.request(`/api/v1/sales/${sale.sale_id || sale.id}`, { method: "DELETE" });
            setRevision((v) => v + 1);
          } catch {
        
          }
        }}
        onConvertToQuotation={async (sale) => {
          try {
            await apiClient.request(`/api/v1/sales/${sale.sale_id || sale.id}/convert-to-quotation`, { method: "POST" });
            setRevision((v) => v + 1);
          } catch {
        
          }
        }}
        onOpenReturn={(sale) => setDevolucionTarget(sale)}
        onCancelSale={(sale) => setAnulacionTarget(sale)}
        onRescheduleDueDate={(sale) => setReprogramarTarget(sale)}
        onPrintSale={(sale) => exportSaleVoucherPDF(sale)}
        onSendSale={(sale) => setComunicacionTarget(sale)}
        onRetrySunat={async (sale) => {
          try {
            await apiClient.request(`/api/v1/sales/${sale.sale_id || sale.id}/retry-sunat`, { method: "POST" });
            setRevision((v) => v + 1);
          } catch {
        
          }
        }}
        onViewCancellationReason={(_sale) => {}}
        onViewSunatError={(_sale) => {}}
        onCreateDebitNote={(sale) => setDebitNoteTarget(sale)}
        onGenerateGuide={(sale) => setGuideTarget(sale)}
        onDownloadXml={(sale) => handleDownloadXml(sale)}
        onDownloadPdf={(sale) => handleDownloadPdf(sale)}
        columnsConfig={columnsConfig}
        sortField={sortField}
        sortDirection={sortDirection}
        onSort={handleSort}
      />

      {selectionMode && (
        <div className="shrink-0">
          <VentasBulkActionBar
            selectedCount={selectedIds.length}
            onClearSelection={() => { setSelectedIds([]); setSelectionMode(false); }}
            onBatchPrint={() => window.print()}
            onBatchResend={() => {
              if (selectedRows.length > 0) setComunicacionTarget(selectedRows[0]);
            }}
            onExportSelected={() => exportToCSV(selectedRows)}
            onAssignSeller={() => { }}
            onRetrySunat={async () => {
              for (const sale of selectedRows) {
                try {
                  await apiClient.request(`/api/v1/sales/${sale.sale_id || sale.id}/retry-sunat`, { method: "POST" });
                } catch {
              
                }
              }
              setRevision((v) => v + 1);
            }}
          />
        </div>
      )}

      <div className="shrink-0 flex flex-wrap items-center justify-between gap-3 rounded-xl sm:rounded-2xl border border-slate-200 bg-white px-4 sm:px-5 py-2 sm:py-2.5 shadow-sm dark:border-slate-800 dark:bg-slate-900 w-full">
        <div className="flex items-center gap-3">
          <button
            type="button"
            title={selectionMode ? "Desactivar selección múltiple" : "Activar selección múltiple"}
            onClick={() => {
              setSelectionMode((v) => !v);
              if (selectionMode) setSelectedIds([]);
            }}
            className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold transition ${
              selectionMode
                ? "border-teal-500 bg-teal-50 text-teal-700 dark:border-teal-400 dark:bg-teal-950/40 dark:text-teal-300"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            }`}
          >
            <CheckSquare className="h-3.5 w-3.5" />
            <span>{selectionMode ? `Seleccionando (${selectedIds.length})` : "Selección múltiple"}</span>
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 dark:text-slate-400">Filas por página</span>
            <CustomSelect
              aria-label="Filas por página"
              value={pageSize}
              disabled={loading}
              className="sales-pagination-select"
              onChange={(e) => {
                const nextSize = Number(e.target.value);
                setPageSize(nextSize);
                persistDefaultPageSize(nextSize);
                setPage(1);
              }}
            >
              {[10, 25, 50, 100].map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </CustomSelect>
          </div>

          <span className="text-xs text-slate-500 dark:text-slate-400">
            Página <strong className="text-slate-900 dark:text-slate-100">{page}</strong> ·{" "}
            <strong className="text-slate-900 dark:text-slate-100">
              {filteredRows.length === 0 ? 0 : `${(page - 1) * pageSize + 1} - ${(page - 1) * pageSize + filteredRows.length}`}
            </strong>{" "}
            de <strong className="text-slate-900 dark:text-slate-100">{total}</strong> registros
          </span>

          <div className="flex items-center gap-1">
            <button
              type="button"
              disabled={page <= 1 || loading}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="inline-flex items-center gap-1 rounded-xl border border-slate-200 px-2.5 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Anterior
            </button>
            <button
              type="button"
              disabled={page >= Math.max(1, Math.ceil(total / pageSize)) || rows.length < pageSize || loading}
              onClick={() => setPage((p) => p + 1)}
              className="inline-flex items-center gap-1 rounded-xl border border-slate-200 px-2.5 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Siguiente
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>

      {paymentTarget && (
        <VentasPostPaymentModal
          isOpen={true}
          sale={paymentTarget}
          onClose={() => setPaymentTarget(null)}
          onPaymentSuccess={() => { setPaymentTarget(null); setRevision((v) => v + 1); }}
          toast={{ success: () => {}, error: () => {} }}
        />
      )}

      {anulacionTarget && (
        <VentasAnulacionModal
          isOpen={true}
          sale={anulacionTarget}
          onClose={() => setAnulacionTarget(null)}
          onConfirmAnulacion={async (saleId, reason, paymentDisposition) => {
            try {
              await apiClient.request(`/api/v1/sales/${saleId}/cancel`, {
                method: "POST",
                body: JSON.stringify({ reason, payment_disposition: paymentDisposition }),
              });
              setAnulacionTarget(null);
              setRevision((v) => v + 1);
            } catch {
          
            }
          }}
          toast={{ error: () => {} }}
        />
      )}

      {reprogramarTarget && (
        <VentasReprogramarModal
          isOpen={true}
          sale={reprogramarTarget}
          onClose={() => setReprogramarTarget(null)}
          onConfirmReschedule={async (saleId, newDate, reason) => {
            try {
              await apiClient.request(`/api/v1/sales/${saleId}/reschedule`, {
                method: "POST",
                body: JSON.stringify({ new_due_date: newDate, reason }),
              });
              setReprogramarTarget(null);
              setRevision((v) => v + 1);
            } catch {
          
            }
          }}
          toast={{ error: () => {} }}
        />
      )}

      {comunicacionTarget && (
        <VentasComunicacionModal
          isOpen={true}
          sale={comunicacionTarget}
          onClose={() => setComunicacionTarget(null)}
          toast={{
            success: () => { setComunicacionTarget(null); setRevision((v) => v + 1); },
            error: () => {},
          }}
        />
      )}

      {devolucionTarget && (
        <VentasDevolucionModal
          isOpen={true}
          sale={devolucionTarget}
          onClose={() => setDevolucionTarget(null)}
          onSuccess={() => { setRevision((v) => v + 1); }}
          onOpenSale={async (id) => { const record = await apiClient.request<SaleRecord>(`/api/v1/sales/${id}`); setDevolucionTarget(null); handleOpenDetail(record); }}
        />
      )}

      {debitNoteTarget && (
        <VentasNotaDebitoModal
          isOpen={true}
          sale={debitNoteTarget}
          onClose={() => setDebitNoteTarget(null)}
          onSuccess={() => { setDebitNoteTarget(null); setRevision((v) => v + 1); }}
        />
      )}

      {guideTarget && (
        <VentasGuiaRemisionModal
          isOpen={true}
          sale={guideTarget}
          onClose={() => setGuideTarget(null)}
          onSuccess={() => { setGuideTarget(null); setRevision((v) => v + 1); }}
        />
      )}
    </section>
  );
}
