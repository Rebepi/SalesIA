import { RemoteEntityOption } from "../../../ui/components/RemoteEntitySelect";
import { PaymentChoice } from "../types/RefundsWorkspaceTab";

export function paymentOption(payment: PaymentChoice): RemoteEntityOption<PaymentChoice> {
  return { value: payment.id, label: `${payment.sale_number} · ${payment.customer_name}`, description: `${payment.customer_document} · ${payment.currency} ${Number(payment.amount).toFixed(2)} · ${payment.payment_method}`, data: payment };
}
