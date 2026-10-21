import type { ReactNode } from "react";

export interface ReturnWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  saleId: string;
  documentNumber: string;
  customerName: string;
  warehouseId?: string;
  onSuccess?: (returnId: string) => void;
  renderCompletion?: (returnId: string, onBusyChange: (busy: boolean) => void) => ReactNode;
}

export interface EligibleLine {
  sale_line_id: string;
  product_id: string;
  sku: string;
  product_name: string;
  unit_price: string | number;
  unit_of_measure?: string;
  allow_fractions?: boolean;
  tax_rate_snapshot?: string | number;
  serial_numbers?: string[];
  return_policy?: {
    version: number;
    source: string;
    product_type: string;
    sold_on: string;
    rule: { returnable: boolean; days: number; allowed_conditions: string[]; allowed_packaging: string[]; evidence_required: boolean; allow_exceptions: boolean; retention_percentage: string; retention_description: string };
  };
  policy_evaluation?: { deadline: string; eligible: boolean; reasons: { code: string; message: string }[] };
  original_quantity: string | number;
  returned_quantity: string | number;
  eligible_quantity: string | number;
}
