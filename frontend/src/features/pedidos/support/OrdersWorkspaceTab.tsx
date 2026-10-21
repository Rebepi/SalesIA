import { RemoteEntityOption } from "../../../ui/components/RemoteEntitySelect";
import { CustomerChoice } from "../types/OrdersWorkspaceTab";
import { ProductChoice } from "../types/OrdersWorkspaceTab";

export const customerOption = (item: CustomerChoice): RemoteEntityOption<CustomerChoice> => ({ value: item.id, label: item.legal_name, description: [item.doc_number, item.code].filter(Boolean).join(" · "), data: item });

export const productOption = (item: ProductChoice): RemoteEntityOption<ProductChoice> => ({ value: item.id, label: item.name, description: `${item.sku}${item.unit_price ? ` · ${item.unit_price}` : ""}`, data: item });
