import type { MeasurementContext, MetricDefinition } from "../components/MeasurementDefinitions";

export interface ComparativePeriod {
  previous_period_label: string;
  previous_revenue: string;
  previous_gross_revenue?: string;
  previous_refunds?: string;
  previous_orders_count: number;
  delta_revenue_pct: string | null;
  delta_orders_pct: string | null;
  has_prior_data?: boolean;
  is_partial_day: boolean;
  cutoff_time: string;
  business_days: number;
}

export interface UnitBreakdownItem {
  unit: string;
  physical: string;
  available: string;
}

export interface InventorySummary {
  total_physical: string;
  total_available: string;
  valuation_total: string | null;
  cost_visible?: boolean;
  valuation_method: string;
  cutoff_date: string;
  has_mixed_units?: boolean;
  units_breakdown?: UnitBreakdownItem[];
  filters_applied?: {
    branch_id: string | null;
    category: string | null;
  };
}

export interface HistogramBin {
  bin_index: number;
  interval: string;
  lower_limit: string;
  upper_limit: string;
  count: number;
  relative_frequency: string;
}

export interface DashboardSummary {
  executive?: ExecutiveSummary;
  measurement_context?: MeasurementContext;
  kpi_definitions?: Record<string, MetricDefinition>;
  total_revenue: string;
  gross_revenue?: string;
  net_revenue?: string;
  orders_count: number;
  active_customers: number;
  active_purchasing_customers?: number;
  active_products: number;
  average_ticket: string | null;
  median_ticket: string | null;
  currency: string;
  period: string;
  sample_count: number;
  distribution: Record<"min" | "q1" | "median" | "q3" | "max", string | null>;
  comparative_period?: ComparativePeriod;
  refunds_amount?: string;
  tax_amount?: string;
  unassigned_sales?: { orders_count: number; revenue: string };
  trend: { date: string; revenue: string; orders_count?: number; is_partial?: boolean }[];
  top_products: { sku: string; name: string; units: string; revenue: string; share_pct?: string }[];
  histogram?: {
    bin_policy?: string;
    bins_count?: number;
    total_observations?: number;
    bins?: HistogramBin[];
  };
  boxplot?: {
    min: string | null;
    q1: string | null;
    median: string | null;
    q3: string | null;
    max: string | null;
    lower_fence: string | null;
    upper_fence: string | null;
    outliers: string[];
    outliers_count: number;
  };
  inventory_summary?: InventorySummary | null;
  restrictions?: { inventory: boolean; costs: boolean };
  generated_at?: string;
}

export interface ExecutiveMetric {
  amount: string | null;
  status: "available" | "restricted" | "review" | "empty" | "unavailable" | "inactive" | "not_applicable";
  note: string;
  count?: number | null;
  percent?: string | null;
  total_open?: string;
  current_open?: string;
  partial?: { amount: string; percent: string | null; commercial_base: string; revenue: string; coverage_pct: string | null; definition: string };
}

export interface ExecutiveSummary {
  currency: string;
  inventory_currency: string;
  as_of: string;
  business_date: string;
  timezone: string;
  scope_note: string;
  concentration?: { peak_day: { date: string; revenue: string; orders_count: number; percent: string | null } | null; largest: { count: number; amount: string; percent: string | null }; definition: string };
  allowed_views: string[];
  drilldowns?: Record<string, boolean>;
  export_permissions?: { costs: boolean; payments: boolean; cash: boolean; inventory: boolean; sales: boolean };
  margin: ExecutiveMetric;
  collections: ExecutiveMetric;
  receivables: ExecutiveMetric;
  payables: ExecutiveMetric;
  funds: ExecutiveMetric;
  inventory: { status: string; out_of_stock: number | null; cost_coverage?: { products_with_stock: number; valued_products: number; missing_count: number; status: "review" | "available" }; view: string; note?: string; preview?: { id: string; nombre: string; sku: string }[] };
  alerts: { key: string; count?: number; severity: "warning" | "danger"; title: string; description: string; view: string }[];
}

export interface SalesAnalytics {
  count: number;
  mean_sale: string | null;
  median_sale: string | null;
  min_sale: string | null;
  max_sale: string | null;
  total_volume: string;
  skewness: string | null;
  granularity: string;
  period: string;
  currency?: string;
  series: { date: string; revenue: string; orders_count: number; status: string; has_data: boolean }[];
  breakdown: { recorded_days: number; zero_sales_days: number; no_data_days: number };
}

export interface ProductItem {
  has_zero_cost?: boolean | null;
  product_id: string;
  sku: string;
  name: string;
  category: string;
  unit_price: string;
  unit_cost: string | null;
  historical_cost?: string | null;
  units: string;
  base_commercial: string;
  revenue: string;
  share_pct: string;
  margin_amount: string | null;
  margin_pct: string | null;
  returns_units: string;
  returns_amount: string;
}

export interface ProductsAnalytics {
  coverage?: { percent: string | null; document_revenue: string; detail_revenue: string; documents_without_detail: number; amount_without_detail: string; definition: string };
  measurement_context?: MeasurementContext;
  cost_visible?: boolean;
  definitions?: Record<string, string>;
  items: ProductItem[];
  count: number;
  total_revenue: string;
  currency?: string;
  other_categories?: {
    name: string;
    products_count: number;
    units?: string;
    revenue: string;
    share_pct: string;
    margin_amount?: string | null;
    margin_pct?: string | null;
  } | null;
}

export interface CustomerItem {
  customer_id: string;
  code: string;
  legal_name: string;
  credit_limit: string;
  current_balance: string;
  orders_count: number;
  total_revenue: string;
  average_ticket: string | null;
  revenue_share_pct: string;
  last_order_date: string | null;
  recency_days: number | null;
  customer_type: "new" | "recurring" | "prospect" | "final_consumer";
}

export interface CustomersAnalytics {
  measurement_context?: MeasurementContext;
  items: CustomerItem[];
  count: number;
  currency?: string;
  summary: {
    total_customers: number;
    active_in_period: number;
    total_revenue: string;
    new_customers_count: number;
  final_consumers_count?: number;
    recurring_customers_count: number;
    top_20_concentration_pct: string;
  };
}

export interface SellerItem {
  is_active?: boolean;
  identifier?: string;
  seller_id: string;
  seller_email: string;
  seller_name: string;
  role: string;
  sales_count: number;
  deals_closed: number;
  total_revenue: string;
  average_ticket: string | null;
  customers_served: number;
  returns_amount: string;
  quota_target: string | null;
  quota_completion_pct: string | null;
}

export interface SellersAnalytics {
  categories?: Record<"active" | "inactive" | "unassigned" | "unidentifiable", { sales_count: number; total_revenue: string }>;
  unidentifiable?: { sales_count: number; total_revenue: string };
  items: SellerItem[];
  count: number;
  total_revenue: string;
  currency?: string;
  unassigned: {
    seller_name: string;
    sales_count: number;
    total_revenue: string;
    average_ticket: string | null;
  };
  reconciliation_checked: boolean;
}

export interface CategoryItem {
  id: string;
  code: string;
  name: string;
}

export interface BranchItem {
  branch_id: string;
  code: string;
  name: string;
}
