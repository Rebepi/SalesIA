import { useEffect, useState, useRef, useMemo, useCallback } from "react";
import { apiClient } from "../../../api/client";
import { getAccessibleTables, UI_PREFERENCES_EVENT } from "../../../ui/preferences";
import { DashboardSummary } from "../types/DashboardAnalyticsTab";
import { SalesAnalytics } from "../types/DashboardAnalyticsTab";
import { ProductsAnalytics } from "../types/DashboardAnalyticsTab";
import { CustomersAnalytics } from "../types/DashboardAnalyticsTab";
import { SellersAnalytics } from "../types/DashboardAnalyticsTab";
import { CategoryItem } from "../types/DashboardAnalyticsTab";
import { BranchItem } from "../types/DashboardAnalyticsTab";
import { PANELS_STORAGE_KEY } from "../support/DashboardAnalyticsTab";
import { FILTERS_STORAGE_KEY } from "../support/DashboardAnalyticsTab";

export type DashboardBranchContext = { operationalBranchId: string; allBranches: boolean; onSelectBranch: (id: string) => void };

export function useDashboardAnalyticsTab(branchContext?: DashboardBranchContext) {
  const initialPanels = useMemo(() => {
    try {
      const stored = localStorage.getItem(PANELS_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch { }
    return {
      summary: true,
      trend: true,
      products: true,
      sellers: true,
      customers: true,
      inventory: true,
      stats: false
    };
  }, []);

  const initialFilters = useMemo(() => {
    try {
      const stored = localStorage.getItem(FILTERS_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch { }
    return {
      period: "30d",
      currency: "",
      category: "",
      granularity: "day"
    };
  }, []);

  const [period, setPeriod] = useState<string>(initialFilters.period || "30d");

  const [fallbackBranchId, setFallbackBranchId] = useState("");
  const branchId = branchContext ? branchContext.allBranches ? "" : branchContext.operationalBranchId : fallbackBranchId;
  const setBranchId = (id: string) => { if (branchContext) branchContext.onSelectBranch(id); else setFallbackBranchId(id); };

  const [currency, setCurrency] = useState<string>(initialFilters.currency || "");

  const [category, setCategory] = useState<string>(initialFilters.category || "");

  const [granularity, setGranularity] = useState<string>(initialFilters.granularity || "day");

  const [revision, setRevision] = useState(0);

  const [branches, setBranches] = useState<BranchItem[]>([]);

  const [categories, setCategories] = useState<CategoryItem[]>([]);

  const [categorySearch, setCategorySearch] = useState("");

  const [categoryDropdownOpen, setCategoryDropdownOpen] = useState(false);

  const categoryContainerRef = useRef<HTMLDivElement>(null);

  const [summaryData, setSummaryData] = useState<DashboardSummary | null>(null);

  const [summaryLoading, setSummaryLoading] = useState(true);

  const [summaryError, setSummaryError] = useState("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  const [salesData, setSalesData] = useState<SalesAnalytics | null>(null);

  const [salesLoading, setSalesLoading] = useState(true);

  const [salesError, setSalesError] = useState("");

  const [productsData, setProductsData] = useState<ProductsAnalytics | null>(null);

  const [productsLoading, setProductsLoading] = useState(true);

  const [productsError, setProductsError] = useState("");

  const [customersData, setCustomersData] = useState<CustomersAnalytics | null>(null);

  const [customersLoading, setCustomersLoading] = useState(true);

  const [customersError, setCustomersError] = useState("");

  const [sellersData, setSellersData] = useState<SellersAnalytics | null>(null);

  const [sellersLoading, setSellersLoading] = useState(true);

  const [sellersError, setSellersError] = useState("");

  const [showZeroSellers, setShowZeroSellers] = useState(false);

  const [drillDown, setDrillDown] = useState<{
    title: string;
    subtitle: string;
    rows: { label: string; value: string; note?: string }[];
  } | null>(null);

  const [visiblePanels, setVisiblePanels] = useState(initialPanels);

  const [showConfig, setShowConfig] = useState(false);

  const [showFilters, setShowFilters] = useState(false);

  const filterButtonRef = useRef<HTMLButtonElement>(null);

  const [showAccessibleTables, setShowAccessibleTables] = useState(getAccessibleTables);

  useEffect(() => {
    const syncPreferences = () => setShowAccessibleTables(getAccessibleTables());
    window.addEventListener(UI_PREFERENCES_EVENT, syncPreferences);
    return () => window.removeEventListener(UI_PREFERENCES_EVENT, syncPreferences);
  }, []);

  const [showSkewnessExplainer, setShowSkewnessExplainer] = useState(false);

  const [chartTooltip, setChartTooltip] = useState<{
    date: string;
    revenue: string;
    orders_count: number;
    isZero: boolean;
    x: number;
    y: number;
  } | null>(null);

  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(0);

  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date>(new Date());

  const [minutesSinceUpdate, setMinutesSinceUpdate] = useState<number>(0);

  useEffect(() => {
    try {
      localStorage.setItem(PANELS_STORAGE_KEY, JSON.stringify(visiblePanels));
    } catch { }
  }, [visiblePanels]);

  useEffect(() => {
    try {
      localStorage.setItem(
        FILTERS_STORAGE_KEY,
        JSON.stringify({ period, currency, category, granularity })
      );
    } catch { }
  }, [period, branchId, currency, category, granularity]);

  useEffect(() => {
    apiClient
      .request<BranchItem[]>("/api/v1/branches")
      .then((res) => {
        setBranches(res || []);

      })
      .catch(() => { });

    apiClient
      .request<CategoryItem[]>("/api/v1/categories")
      .then((res) => {
        setCategories(res || []);
      })
      .catch(() => { });
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        categoryContainerRef.current &&
        !categoryContainerRef.current.contains(event.target as Node)
      ) {
        setCategoryDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      const diffMinutes = Math.floor((Date.now() - lastRefreshedAt.getTime()) / 60000);
      setMinutesSinceUpdate(diffMinutes);
    }, 30000);
    return () => clearInterval(timer);
  }, [lastRefreshedAt]);

  useEffect(() => {
    if (!autoRefreshInterval) return;
    const intervalId = setInterval(() => {
      if (document.visibilityState === "visible") {
        setRevision((r) => r + 1);
      }
    }, autoRefreshInterval * 60000);
    return () => clearInterval(intervalId);
  }, [autoRefreshInterval]);

  const activeCurrency = currency || summaryData?.currency || "USD";

  const formatMoney = useCallback(
    (val: string | number | null | undefined, customCurrency?: string) => {
      if (val === null || val === undefined) return "—";
      const num = typeof val === "number" ? val : Number(val);
      if (isNaN(num)) return "0.00";
      const curr = customCurrency || activeCurrency;
      return new Intl.NumberFormat("es-PE", {
        style: "currency",
        currency: curr,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(num);
    },
    [activeCurrency]
  );

  const buildQuery = useCallback(
    (extra = "") => {
      const params = new URLSearchParams();
      if (period) params.set("period", period);
      if (branchId) params.set("branch_id", branchId);
      if (currency) params.set("currency", currency);
      if (category) params.set("category", category);
      if (extra) {
        const extraParams = new URLSearchParams(extra);
        extraParams.forEach((v, k) => params.set(k, v));
      }
      return params.toString();
    },
    [period, branchId, currency, category]
  );

  const fetchSummary = useCallback(() => {
    const controller = new AbortController();
    setSummaryLoading(true);
    setSummaryError("");
    setSummaryData(null);
    apiClient
      .request<DashboardSummary>(`/api/v1/dashboard/summary?${buildQuery()}`, {
        signal: controller.signal
      })
      .then((val) => {
        if (!controller.signal.aborted) {
          setSummaryData(val);
          setLastRefreshedAt(new Date());
          setMinutesSinceUpdate(0);
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setSummaryError(
            typeof err?.detail === "string" ? err.detail : "Error al cargar resumen ejecutivo."
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSummaryLoading(false);
      });
    return () => controller.abort();
  }, [buildQuery]);

  const fetchSales = useCallback(() => {
    const controller = new AbortController();
    setSalesLoading(true);
    setSalesError("");
    apiClient
      .request<SalesAnalytics>(`/api/v1/analytics/sales?${buildQuery(`granularity=${granularity}`)}`, {
        signal: controller.signal
      })
      .then((val) => {
        if (!controller.signal.aborted) setSalesData(val);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setSalesError(
            typeof err?.detail === "string" ? err.detail : "Error al cargar serie temporal de ventas."
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSalesLoading(false);
      });
    return () => controller.abort();
  }, [buildQuery, granularity]);

  const fetchProducts = useCallback(() => {
    const controller = new AbortController();
    setProductsLoading(true);
    setProductsError("");
    apiClient
      .request<ProductsAnalytics>(`/api/v1/analytics/products?${buildQuery("limit=10")}`, {
        signal: controller.signal
      })
      .then((val) => {
        if (!controller.signal.aborted) setProductsData(val);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setProductsError(
            typeof err?.detail === "string" ? err.detail : "Error al cargar rentabilidad de productos."
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setProductsLoading(false);
      });
    return () => controller.abort();
  }, [buildQuery]);

  const fetchCustomers = useCallback(() => {
    const controller = new AbortController();
    setCustomersLoading(true);
    setCustomersError("");
    apiClient
      .request<CustomersAnalytics>(`/api/v1/analytics/customers?${buildQuery("limit=10")}`, {
        signal: controller.signal
      })
      .then((val) => {
        if (!controller.signal.aborted) setCustomersData(val);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setCustomersError(
            typeof err?.detail === "string" ? err.detail : "Error al cargar cartera de clientes."
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setCustomersLoading(false);
      });
    return () => controller.abort();
  }, [buildQuery]);

  const fetchSellers = useCallback(() => {
    const controller = new AbortController();
    setSellersLoading(true);
    setSellersError("");
    apiClient
      .request<SellersAnalytics>(`/api/v1/analytics/sellers?${buildQuery()}`, {
        signal: controller.signal
      })
      .then((val) => {
        if (!controller.signal.aborted) setSellersData(val);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setSellersError(
            typeof err?.detail === "string" ? err.detail : "Error al cargar equipo de ventas."
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSellersLoading(false);
      });
    return () => controller.abort();
  }, [buildQuery]);

  useEffect(() => {
    const cleanup = fetchSummary();
    return cleanup;
  }, [fetchSummary, revision]);

  useEffect(() => {
    const cleanup = fetchSales();
    return cleanup;
  }, [fetchSales, revision]);

  useEffect(() => {
    const cleanup = fetchProducts();
    return cleanup;
  }, [fetchProducts, revision]);

  useEffect(() => {
    const cleanup = fetchCustomers();
    return cleanup;
  }, [fetchCustomers, revision]);

  useEffect(() => {
    const cleanup = fetchSellers();
    return cleanup;
  }, [fetchSellers, revision]);

  const handleRefreshAll = () => {
    setRevision((r) => r + 1);
  };

  const handleResetFilters = () => {
    setBranchId("");
    setCurrency("");
    setCategory("");
    setPeriod("30d");
    setGranularity("day");
  };

  const activeBranchObj = branches.find((b) => String(b.branch_id) === String(branchId));

  const hasActiveFilters = Boolean(
    branchId || category || currency || (period && period !== "30d")
  );

  const isUpdatingAny = summaryLoading || salesLoading || productsLoading || customersLoading || sellersLoading;

  const exportSummaryCSV = async () => {
    if (!summaryData?.executive || summaryError || isUpdatingAny || exporting) return;
    setExporting(true);
    setExportError("");
    try {
      const params = new URLSearchParams({ period, currency: activeCurrency, as_of: summaryData.executive.as_of, granularity, expected_revenue: summaryData.total_revenue, expected_documents: String(summaryData.orders_count), visible_panels: Object.entries(visiblePanels).filter(([, shown]) => shown).map(([key]) => key).join(",") });
      if (branchId) params.set("branch_id", branchId);
      if (category) params.set("category", category);
      const { blob, filename } = await apiClient.downloadBlob(`/api/v1/dashboard/export?${params}`);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (failure) {
      const error = failure as { detail?: string; message?: string };
      setExportError(error.detail || error.message || "No se pudo descargar el ZIP con las tablas de datos.");
    } finally {
      setExporting(false);
    }
  };

  const trendSeries = salesData?.series || [];

  const maxRevenue = Math.max(1, ...trendSeries.map((s) => Number(s.revenue) || 0));

  const formatRecency = (days: number | null) => {
    if (days === null || days === undefined) return "—";
    if (days === 0) return "hoy";
    if (days === 1) return "hace 1 día";
    return `hace ${days} días`;
  };

  const getInitials = (name?: string) => {
    if (!name) return "--";
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return "--";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  };

  const filteredCategories = useMemo(() => {
    if (!categorySearch.trim()) return categories;
    const term = categorySearch.toLowerCase();
    return categories.filter(
      (c) => c.name.toLowerCase().includes(term) || c.code.toLowerCase().includes(term)
    );
  }, [categories, categorySearch]);

  const activeSellers = useMemo(() => {
    return (sellersData?.items || []).filter((s) => Number(s.total_revenue) > 0);
  }, [sellersData]);

  const zeroSellers = useMemo(() => {
    return (sellersData?.items || []).filter((s) => Number(s.total_revenue) <= 0);
  }, [sellersData]);

  const displayedSellers = useMemo(() => {
    if (showZeroSellers) {
      return [...activeSellers, ...zeroSellers];
    }
    return activeSellers.slice(0, 10);
  }, [activeSellers, zeroSellers, showZeroSellers]);

  const getQuotaColorClasses = (pctStr: string | null) => {
    if (!pctStr) return { bar: "bg-slate-400", text: "text-slate-400", label: "Sin cuota" };
    const pct = parseFloat(pctStr);
    if (isNaN(pct)) return { bar: "bg-slate-400", text: "text-slate-400", label: "Sin cuota" };
    if (pct < 50) return { bar: "bg-rose-500", text: "text-rose-600 dark:text-rose-400", label: "< 50%" };
    if (pct < 100) return { bar: "bg-amber-500", text: "text-amber-600 dark:text-amber-400", label: "50–99%" };
    return { bar: "bg-emerald-500", text: "text-emerald-600 dark:text-emerald-400", label: "≥ 100%" };
  };

  const handleNavigateToSales = () => {
    window.dispatchEvent(
      new CustomEvent("salesia:navigate", {
        detail: {
          view: "sales",
          branchId: branchId,
          currency: currency
        }
      })
    );
    setDrillDown(null);
  };

  const periodLabel = ({ "7d": "Últimos 7 días", "30d": "Últimos 30 días", "90d": "Últimos 90 días", "12m": "Últimos 12 meses", all: "Todo el historial" } as Record<string, string>)[period] || period;

  const activeFilterCount = [period !== "30d", Boolean(branchId), Boolean(currency), Boolean(category)].filter(Boolean).length;
  return { period, setPeriod, branchId, setBranchId, currency, setCurrency, category, setCategory, granularity, setGranularity, branches, categorySearch, setCategorySearch, categoryDropdownOpen, setCategoryDropdownOpen, categoryContainerRef, summaryData, summaryLoading, summaryError, salesLoading, salesError, productsData, productsLoading, productsError, customersData, customersLoading, customersError, sellersData, sellersLoading, sellersError, showZeroSellers, setShowZeroSellers, drillDown, setDrillDown, visiblePanels, setVisiblePanels, showConfig, setShowConfig, showFilters, setShowFilters, filterButtonRef, showAccessibleTables, showSkewnessExplainer, setShowSkewnessExplainer, chartTooltip, setChartTooltip, autoRefreshInterval, setAutoRefreshInterval, minutesSinceUpdate, activeCurrency, formatMoney, fetchSummary, fetchSales, fetchProducts, fetchCustomers, fetchSellers, handleRefreshAll, handleResetFilters, activeBranchObj, hasActiveFilters, isUpdatingAny, exporting, exportError, exportSummaryCSV, trendSeries, maxRevenue, formatRecency, getInitials, filteredCategories, zeroSellers, displayedSellers, getQuotaColorClasses, handleNavigateToSales, periodLabel, activeFilterCount };
}
