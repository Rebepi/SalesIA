export type Row = Record<string, string | number | boolean | null>;

export interface SaleChoice extends Record<string, unknown> {
  sale_id: string;
  receipt: string;
  customer_name: string;
  purchased_at: string;
  warranty_until: string;
}

export interface Props {
  productId: string;
  productName: string;
  canWrite: boolean;
  allProducts: Row[];
  onClose: () => void;
  onRefresh: () => void;
}

export type Tab = "overview" | "variants" | "barcodes" | "pricing" | "kits" | "warranty" | "attachments";
