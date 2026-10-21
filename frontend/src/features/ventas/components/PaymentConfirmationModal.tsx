import { SeccionConfirmacionDeCobroIrreversible } from "../sections/PaymentConfirmationModal/SeccionConfirmacionDeCobroIrreversible";
export type { PaymentProcessStatus } from "../types/PaymentConfirmationModal";
export type { PaymentConfirmationModalProps } from "../types/PaymentConfirmationModal";
import { usePaymentConfirmationModal } from "../hooks/usePaymentConfirmationModal";
import { PaymentConfirmationModalProps } from "../types/PaymentConfirmationModal";

export function PaymentConfirmationModal({
  isOpen,
  amount,
  currency,
  customerName,
  documentNumber,
  paymentMethod,
  balance,
  referenceCode,
  initialStatus = "pending",
  onConfirm,
  onClose
}: PaymentConfirmationModalProps) {
  const { loading, setLoading, status, setStatus, refCode, setRefCode, error, setError } = usePaymentConfirmationModal({ isOpen, amount, currency, customerName, documentNumber, paymentMethod, balance, referenceCode, initialStatus, onConfirm, onClose });
  if (!isOpen) return null;

  async function handleConfirm() {
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      const res = await onConfirm();
      if (res && typeof res.status === "string") {
        if (res.status === "confirmed") {
          setStatus("confirmed");
        } else if (res.status === "rejected") {
          setStatus("rejected");
        } else if (res.status === "unknown") {
          setStatus("unknown");
        } else {
          setStatus("confirmed");
        }
      } else {
        setStatus("confirmed");
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Error al procesar el cobro.");
      }
      setStatus("rejected");
    } finally {
      setLoading(false);
    }
  }

  const remainingBalance = balance !== undefined
    ? (Number(balance) - Number(amount)).toFixed(2)
    : undefined;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
      <SeccionConfirmacionDeCobroIrreversible loading={loading} onClose={onClose} status={status} error={error} setStatus={setStatus} setError={setError} documentNumber={documentNumber} customerName={customerName} paymentMethod={paymentMethod} currency={currency} balance={balance} amount={amount} remainingBalance={remainingBalance} refCode={refCode} setRefCode={setRefCode} handleConfirm={handleConfirm} />
    </div>
  );
}
