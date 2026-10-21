export interface Category {
  id: string;
  code: string;
  name: string;
  parent_id?: string | null;
  level: number;
  sort_order: number;
  is_active: boolean;
}

export interface Unit {
  id: string;
  code: string;
  name: string;
  allow_fractions: boolean;
  precision_digits: number;
}

export interface UnitConversion {
  id: string;
  from_unit: string;
  to_unit: string;
  factor: string;
  product_id?: string | null;
}
