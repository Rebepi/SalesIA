import { RemoteEntityOption } from "../../../ui/components/RemoteEntitySelect";
import { ProductChoice } from "../types/PricingAndPromotionsTab";

export const productPriceOption = (item: ProductChoice): RemoteEntityOption<ProductChoice> => ({ value: item.id, label: item.name, description: `${item.sku} · ${item.unit_price}`, data: item });
