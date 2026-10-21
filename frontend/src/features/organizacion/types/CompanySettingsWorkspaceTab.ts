export interface CompanySettingsWorkspaceTabProps {
  canWrite?: boolean;
  section?: Section;
}

export type Section = "company" | "branches" | "numbering" | "rules" | "branding" | "appearance" | "profile" | "functions" | "calendar";

export interface Company {
  company_id: string;
  tax_id: string;
  legal_name: string;
  trade_name: string;
  base_currency: string;
  is_active: boolean;
}

export interface Branch {
  branch_id: string;
  code: string;
  name: string;
  timezone: string;
  is_active: boolean;
}

export interface Warehouse {
  warehouse_id: string;
  branch_id: string;
  code: string;
  name: string;
  is_active: boolean;
}

export interface CompanySettings {
  version: number;
  rounding_mode: string;
  default_tax_rate: string;
  credit_limit_strict: boolean;
  tax_included_in_price: boolean;
  branding?: {
    logo_url?: string;
    legal_name?: string;
    footer_text?: string;
  };
}

export interface Sequence {
  series: string;
  value: number;
}

export interface TaxRule {
  code: string;
  rate: string;
  name: string;
  is_active: boolean;
}
