import { RemoteEntityOption } from "../../../ui/components/RemoteEntitySelect";
import { CustomerItem } from "../types/NewSalePOSModal";
import { PosDraft } from "../types/NewSalePOSModal";

export const DRAFT_KEY = "salesia_pos_sale_draft_v2";

export const EMPTY_DRAFT: PosDraft = { warehouseId: "", isCredit: false, documentType: "RECEIPT", cart: [] };

export function customerOption(customer: CustomerItem): RemoteEntityOption<CustomerItem> {
  const isWalkIn = Boolean(customer.is_walk_in || customer.doc_type === "SIN_DOCUMENTO" || customer.legal_name?.toLowerCase().includes("consumidor final"));
  return {
    value: customer.id || String(customer.customer_id),
    label: isWalkIn ? "Consumidor final · Sin identificar" : customer.legal_name,
    description: isWalkIn ? "Sin identificar · Contado · Lista estándar" : `${customer.doc_type ? `${customer.doc_type} ` : ""}${customer.doc_number || ""}${customer.phone ? ` · Tel: ${customer.phone}` : ""}`,
    data: customer
  };
}

export function money(value: number, currency: string) {
  try {
    return new Intl.NumberFormat("es-PE", { style: "currency", currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
  } catch {
    return `${currency} ${value.toFixed(2)}`;
  }
}
