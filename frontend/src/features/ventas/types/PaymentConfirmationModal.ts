export type PaymentProcessStatus = "pending" | "confirmed" | "rejected" | "unknown";

export interface PaymentConfirmationModalProps {
  isOpen: boolean;
  amount: string | number;
  currency: string;
  customerName: string;
  documentNumber: string;
  paymentMethod: string;
  balance?: string | number;
  referenceCode?: string;
  initialStatus?: PaymentProcessStatus;
  onConfirm: () => Promise<{ status: string } | void>;
  onClose: () => void;
}
