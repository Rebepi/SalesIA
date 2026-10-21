import type { MeasurementContext } from "../components/MeasurementDefinitions";
export interface SalesSeriesItem {
  date: string;
  revenue: string;
  orders_count: number;
  status: string;
  has_data: boolean;
}

export interface ProductItem {
  product_id: string;
  sku: string;
  name: string;
  units: string;
  revenue: string;
  share_pct: string;
}

export interface SellerItem {
  seller_id: string;
  seller_name: string;
  sales_count: number;
  total_revenue: string;
  average_ticket: string | null;
}

export interface BranchItem {
  branch_id: string;
  code: string;
  name: string;
  sales_count: number;
  total_revenue: string;
  average_ticket: string | null;
  share_pct: string;
}

export interface SalesAnalyticsData {
  measurement_context?: MeasurementContext;
  series: SalesSeriesItem[];
  total_volume: string;
  count: number;
  mean_sale: string | null;
  median_sale: string | null;
}

export interface SalesAnalyticsTabProps {
  canWrite?: boolean;
}
