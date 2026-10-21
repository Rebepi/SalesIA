export interface PriceList {
  id: string;
  code: string;
  name: string;
  currency: string;
  priority: number;
  valid_from?: string;
  valid_to?: string;
  is_active: boolean;
  target_type?: string;
  target_id?: string;
}

export interface PriceItem { id: string; product_id: string; sku: string; product_name: string; base_price: string; fixed_price?: string; discount_percentage?: string }

export interface ProductChoice extends Record<string, unknown> { id: string; sku: string; name: string; unit_price: string }

export interface Promotion {
  id: string;
  code: string;
  name: string;
  priority: number;
  is_exclusive: boolean;
  start_date?: string;
  end_date?: string;
  discount_percentage: string;
  max_quota: number;
  current_uses: number;
  is_active: boolean;
}
