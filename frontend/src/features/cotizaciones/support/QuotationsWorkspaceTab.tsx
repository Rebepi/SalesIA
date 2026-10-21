import { RemoteEntityOption } from "../../../ui/components/RemoteEntitySelect";
import { CustomerItem } from "../types/QuotationsWorkspaceTab";
import { ProductItem } from "../types/QuotationsWorkspaceTab";
import { QuotationLine } from "../types/QuotationsWorkspaceTab";
import { QuotationDraft } from "../types/QuotationsWorkspaceTab";

export const DRAFT_KEY = "salesia_quotation_draft_v2";

export const EMPTY_LINE: QuotationLine = { product_id: "", quantity: "1", discount_pct: "0" };

export const EMPTY_DRAFT: QuotationDraft = { branchId: "", validDays: "15", lines: [EMPTY_LINE], paymentTerms: "30", deliveryTerms: "", notes: "", specialConditions: "", sellerId: "" };

export function customerOption(customer: CustomerItem): RemoteEntityOption<CustomerItem> {
  return { value: customer.id || String(customer.customer_id), label: customer.legal_name, description: `${customer.doc_type} ${customer.doc_number} · ${customer.code}`, data: customer };
}

export function productOption(product: ProductItem): RemoteEntityOption<ProductItem> {
  return { value: product.id || String(product.product_id), label: product.name, description: `${product.sku} · ${product.unit_price} ${product.unit_of_measure || ""}`, data: product };
}
