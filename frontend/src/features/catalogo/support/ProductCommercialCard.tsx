import { RemoteEntityOption } from "../../../ui/components/RemoteEntitySelect";
import { SaleChoice } from "../types/ProductCommercialCard";

export function saleOption(sale: SaleChoice): RemoteEntityOption<SaleChoice> {
  return { value: sale.sale_id, label: `${sale.receipt} · ${sale.customer_name}`, description: `Compra ${sale.purchased_at.substring(0, 10)} · cobertura hasta ${sale.warranty_until.substring(0, 10)}`, data: sale };
}

export const inputStyle = "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100";

export const btnPrimary = "inline-flex items-center justify-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:opacity-50";
