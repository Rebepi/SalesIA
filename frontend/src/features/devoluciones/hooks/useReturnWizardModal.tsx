import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { ReturnWizardModalProps } from "../types/ReturnWizardModal";
import { EligibleLine } from "../types/ReturnWizardModal";

export function useReturnWizardModal({ isOpen, saleId }: ReturnWizardModalProps) {
  const [independentReviewRequired, setIndependentReviewRequired] = useState(false);
  const [awaitingReview, setAwaitingReview] = useState(false);
  const [loadRevision, setLoadRevision] = useState(0);
  const [step, setStep] = useState<number>(1);
  const [conditions, setConditions] = useState<Record<string, string>>({});
  const [packaging, setPackaging] = useState<Record<string, string>>({});
  const [evidenceNotes, setEvidenceNotes] = useState<Record<string, string>>({});
  const [waiveRetention, setWaiveRetention] = useState(false);
  const [canGrantStoreCredit, setCanGrantStoreCredit] = useState(false);
  const [canAuthorizeException, setCanAuthorizeException] = useState(false);
  const [currency, setCurrency] = useState("");
  const [businessDate, setBusinessDate] = useState("");
  const [finalSettlement, setFinalSettlement] = useState<{ available_amount: string; movements: { kind: string; amount: string }[] } | null>(null);
  const [finalValuation, setFinalValuation] = useState<{ retained_total: string; refundable_total: string } | null>(null);

  const [lines, setLines] = useState<EligibleLine[]>([]);

  const [quantities, setQuantities] = useState<Record<string, number>>({});

  const [dispositions, setDispositions] = useState<Record<string, "RESTOCK" | "QUARANTINE" | "DISPOSE">>({});

  const [serialSelections, setSerialSelections] = useState<Record<string, string[]>>({});

  const [reason, setReason] = useState<string>("Devolución solicitada por cliente");

  const [creditAction, setCreditAction] = useState<"CREDIT_NOTE" | "STORE_CREDIT" | "REFUND">("CREDIT_NOTE");

  const [authorizedException, setAuthorizedException] = useState<boolean>(false);

  const [exceptionReason, setExceptionReason] = useState<string>("");

  const [loading, setLoading] = useState<boolean>(false);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  const [generatedReturnId, setGeneratedReturnId] = useState<string>("");

  const [error, setError] = useState<string>("");

  const pendingRequests = useRef(new Map<string, string>());
  const submittingLock = useRef(false);
  const toast = useToast();

  useEffect(() => {
    if (!isOpen || !saleId) return;
    const controller = new AbortController();
    setStep(1);
    setAwaitingReview(false);
    setIndependentReviewRequired(false);
    setReason("Devolución solicitada por cliente");
    pendingRequests.current.clear();
    setConditions({});
    setPackaging({});
    setEvidenceNotes({});
    setAuthorizedException(false);
    setExceptionReason("");
    setWaiveRetention(false);
    setFinalValuation(null);
    setFinalSettlement(null);
    setCanAuthorizeException(false);
    setCanGrantStoreCredit(false);
    setCreditAction("CREDIT_NOTE");
    setIsSuccess(false);
    setGeneratedReturnId("");
    setSerialSelections({});
    setQuantities({});
    setLines([]);
    setError("");
    setLoading(true);

    apiClient
      .request<{ independent_review_required?: boolean; lines: EligibleLine[]; currency: string; business_date: string; can_authorize_exception: boolean; can_grant_store_credit: boolean }>(`/api/v1/returns/sales/${saleId}/eligible`, { signal: controller.signal })
      .then((res) => {
        if (controller.signal.aborted) return;
        setCurrency(res.currency);
        setIndependentReviewRequired(Boolean(res.independent_review_required));
        setBusinessDate(res.business_date);
        setCanAuthorizeException(res.can_authorize_exception);
        setCanGrantStoreCredit(res.can_grant_store_credit);
        const fetchedLines = res.lines || [];
        setLines(fetchedLines);
        const initQty: Record<string, number> = {};
        const initDisp: Record<string, "RESTOCK" | "QUARANTINE" | "DISPOSE"> = {};
        for (const line of fetchedLines) {
          const eligible = Number(line.eligible_quantity) || 0;
          initQty[line.sale_line_id || line.product_id] = eligible > 0 ? Math.min(1, eligible) : 0;
          initDisp[line.sale_line_id || line.product_id] = "RESTOCK";
        }
        setQuantities(initQty);
        setDispositions(initDisp);
        setConditions(Object.fromEntries(fetchedLines.map(line => [line.sale_line_id || line.product_id, line.return_policy?.product_type === "service" ? "not_applicable" : "unused"])));
        setPackaging(Object.fromEntries(fetchedLines.map(line => [line.sale_line_id || line.product_id, line.return_policy?.product_type === "service" ? "not_applicable" : "sealed"])));
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(String(err?.detail || "No se pudieron cargar las líneas elegibles de la venta."));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [isOpen, saleId, loadRevision]);
  return { independentReviewRequired, awaitingReview, setAwaitingReview, retryLoad: () => setLoadRevision(value => value + 1), canGrantStoreCredit, finalSettlement, setFinalSettlement, finalValuation, setFinalValuation, conditions, setConditions, packaging, setPackaging, evidenceNotes, setEvidenceNotes, waiveRetention, setWaiveRetention, canAuthorizeException, currency, businessDate, pendingRequests, submittingLock, serialSelections, setSerialSelections, step, setStep, lines, quantities, setQuantities, dispositions, setDispositions, reason, setReason, creditAction, setCreditAction, authorizedException, setAuthorizedException, exceptionReason, setExceptionReason, loading, isSubmitting, setIsSubmitting, isSuccess, setIsSuccess, generatedReturnId, setGeneratedReturnId, error, setError, toast };
}
