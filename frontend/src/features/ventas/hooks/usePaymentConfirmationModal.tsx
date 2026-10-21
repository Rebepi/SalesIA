import { useEffect, useState } from "react";
import { PaymentProcessStatus } from "../types/PaymentConfirmationModal";
import { PaymentConfirmationModalProps } from "../types/PaymentConfirmationModal";

export function usePaymentConfirmationModal({ isOpen, referenceCode, initialStatus = "pending", onClose }: PaymentConfirmationModalProps) {
  const [loading, setLoading] = useState(false);

  const [status, setStatus] = useState<PaymentProcessStatus>(initialStatus);

  const [refCode, setRefCode] = useState(referenceCode || "");

  const [error, setError] = useState("");

  useEffect(() => {
    setStatus(initialStatus);
    setRefCode(referenceCode || "");
  }, [initialStatus, referenceCode, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !loading) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, loading, onClose]);
  return { loading, setLoading, status, setStatus, refCode, setRefCode, error, setError };
}
