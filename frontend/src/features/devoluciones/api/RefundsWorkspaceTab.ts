import { apiClient } from "../../../api/client";
import { RefundItem } from "../types/RefundsWorkspaceTab";
import { RefundPaymentDetails } from "../types/RefundsWorkspaceTab";
import { PaymentChoice } from "../types/RefundsWorkspaceTab";

export async function solicitarDatos({ selectedPayment }: { selectedPayment: PaymentChoice }): Promise<RefundPaymentDetails> {
  const [payment, options] = await Promise.all([
    apiClient.request<Omit<RefundPaymentDetails, "options">>(`/api/v1/payments/${selectedPayment.id}`),
    apiClient.request<RefundPaymentDetails["options"]>(`/api/v1/refund-options/${selectedPayment.id}`)
  ]);
  return { ...payment, options };
}

const refundKeys = new Map<string, string>();

export async function solicitarHandleCreateRefund({ paymentId, reason, amountVal, returnId, cashSessionId, payoutReference }: { paymentId: string; reason: string; amountVal: string; returnId: string | null; cashSessionId: string | null; payoutReference: string }) {
  const body = JSON.stringify({ payment_id: paymentId, reason, amount: amountVal, return_id: returnId, cash_session_id: cashSessionId, payout_reference: payoutReference });
  const key = refundKeys.get(body) || crypto.randomUUID();
  refundKeys.set(body, key);
  const result = await apiClient.request("/api/v1/refunds", { method: "POST", headers: { "Idempotency-Key": key }, body });
  refundKeys.delete(body);
  return result;
}

export function solicitarHandleUpdateStatus({ activeRefund, nextStatus, providerRef, failureReason }: { activeRefund: RefundItem; nextStatus: string; providerRef: string | undefined; failureReason: string | undefined }) {
  return apiClient.request(`/api/v1/refunds/${activeRefund.id}/status`, {
    method: "POST",
    body: JSON.stringify({
      status: nextStatus,
      provider_reference: providerRef,
      failure_reason: failureReason
    })
  });
}
