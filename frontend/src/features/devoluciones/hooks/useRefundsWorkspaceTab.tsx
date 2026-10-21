import * as transporte from "../api/RefundsWorkspaceTab";
import { FormEvent, useEffect, useRef, useState } from "react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { RefundItem } from "../types/RefundsWorkspaceTab";
import { RefundsWorkspaceTabProps } from "../types/RefundsWorkspaceTab";
import { RefundPaymentDetails } from "../types/RefundsWorkspaceTab";
import { PaymentChoice } from "../types/RefundsWorkspaceTab";

export function useRefundsWorkspaceTab(_props: RefundsWorkspaceTabProps) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [refunds, setRefunds] = useState<RefundItem[]>([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  const [search, setSearch] = useState("");

  const [currencyOptions, setCurrencyOptions] = useState<string[]>([]);
  const [currencyFilter, setCurrencyFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [returnFilter, setReturnFilter] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  useEffect(() => { const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300); return () => window.clearTimeout(timer); }, [search]);

  const [revision, setRevision] = useState(0);

  const [modalType, setModalType] = useState<"create_refund" | "update_status" | null>(null);

  const [activeRefund, setActiveRefund] = useState<RefundItem | null>(null);

  const [refundBusy, setRefundBusy] = useState(false);

  const [paymentDetails, setPaymentDetails] = useState<RefundPaymentDetails | null>(null);
  const [selectedReturnId, setSelectedReturnId] = useState("");
  const refundLock = useRef(false);
  const selectedReturn = paymentDetails?.options.returns.find(row => row.id === selectedReturnId);
  const maxRefundAmount = selectedReturn?.available_amount || (paymentDetails?.options.requires_return ? "0" : paymentDetails?.options.available_amount || "0");

  const [selectedPayment, setSelectedPayment] = useState<PaymentChoice | undefined>();

  const toast = useToast();

  useEffect(() => {
    if (_props.section && _props.section !== "refunds") return;
    setLoading(true);
    setError("");
    const controller = new AbortController();
    if (dateFrom && dateTo && dateFrom > dateTo) { setLoading(false); setRefunds([]); setError("La fecha inicial no puede ser posterior a la fecha final."); return () => controller.abort(); }
    const query = new URLSearchParams();
    if (selectedStatus !== "ALL") query.set("status", selectedStatus);
    if (debouncedSearch) query.set("search", debouncedSearch);
    if (currencyFilter) query.set("currency", currencyFilter);
    if (dateFrom) query.set("date_from", dateFrom);
    if (dateTo) query.set("date_to", dateTo);
    if (returnFilter) query.set("linked_return", returnFilter);
    apiClient.request<RefundItem[]>(`/api/v1/refunds${query.size ? `?${query}` : ""}`, { signal: controller.signal })
      .then(res => { if (!controller.signal.aborted) { setRefunds(res || []); setCurrencyOptions(previous => [...new Set([...previous, ...(res || []).map(row => row.currency)])].sort()); } })
      .catch(err => { if (!controller.signal.aborted) { setRefunds([]); setError(String(err?.detail || "No se pudo cargar la cola de reembolsos.")); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [selectedStatus, revision, debouncedSearch, currencyFilter, dateFrom, dateTo, returnFilter, _props.section]);

  useEffect(() => {
    setPaymentDetails(null);
    setSelectedReturnId("");
    if (!selectedPayment) return;
    let active = true;
    transporte.solicitarDatos({ selectedPayment }).then(result => { if (active) { setPaymentDetails(result); setSelectedReturnId(result.options.returns.find(row => Number(row.available_amount) > 0)?.id || ""); } }).catch(() => { if (active) toast.error("No se pudo verificar el saldo", "Selecciona nuevamente el pago antes de solicitar el reembolso."); });
    return () => { active = false; };
  }, [selectedPayment?.id, revision]);

  async function handleCreateRefund(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (refundLock.current || refundBusy || !selectedPayment || !paymentDetails || Number(maxRefundAmount) <= 0) return;
    const data = new FormData(e.currentTarget);
    const paymentId = selectedPayment.id;
    const reason = String(data.get("reason") || "").trim();
    const amountVal = String(data.get("amount") || "").trim() || maxRefundAmount;
    const payoutReference = String(data.get("payout_reference") || "").trim();
    const cashSessionId = String(data.get("cash_session_id") || "") || null;
    if (!Number.isFinite(Number(amountVal)) || Number(amountVal) <= 0 || Number(amountVal) > Number(maxRefundAmount)) { toast.warning("Importe no elegible", "El importe debe respetar el saldo del pago, la devolución y las aplicaciones anteriores."); return; }
    refundLock.current = true;
    try {
      if (!await confirm({ title: "¿Registrar reembolso?", text: `Se registrará el desembolso de ${selectedPayment.currency} ${amountVal} sobre ${selectedPayment.sale_number}${selectedReturnId ? `, vinculado a la devolución ${selectedReturnId}` : ""}. El efectivo se retirará de la caja seleccionada cuando corresponda.`, danger: true, confirmLabel: "Registrar desembolso" })) return;
      setRefundBusy(true);
      await transporte.solicitarHandleCreateRefund({ paymentId, reason, amountVal, returnId: selectedReturnId || null, cashSessionId, payoutReference });
      toast.success("Reembolso registrado", "El desembolso quedó vinculado al pago y a su liquidación, con sus movimientos de efectivo cuando corresponda.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al registrar reembolso";
      toast.error("Error", msg);
    } finally { setRefundBusy(false); refundLock.current = false; }
  }

  async function handleUpdateStatus(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!activeRefund) return;
    const data = new FormData(e.currentTarget);
    const nextStatus = String(data.get("status"));
    const providerRef = String(data.get("provider_reference") || "") || undefined;
    const failureReason = String(data.get("failure_reason") || "") || undefined;

    try {
      await transporte.solicitarHandleUpdateStatus({ activeRefund, nextStatus, providerRef, failureReason });
      toast.success("Estado actualizado", `El reembolso pasó a estado ${nextStatus}.`);
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error en transición de reembolso";
      toast.error("Error", msg);
    }
  }

  const filteredRefunds = refunds;
  const resetFilters = () => { setSelectedStatus("ALL"); setSearch(""); setCurrencyFilter(""); setDateFrom(""); setDateTo(""); setReturnFilter(""); };

  const isUncertain = (status: string) => {
    return status === "requiere_conciliacion" || status === "enviado" || status === "pendiente";
  };
  return { currencyOptions, currencyFilter, setCurrencyFilter, dateFrom, setDateFrom, dateTo, setDateTo, returnFilter, setReturnFilter, resetFilters, selectedReturnId, setSelectedReturnId, selectedReturn, maxRefundAmount, revision, ConfirmDialogNode, refunds, loading, error, selectedStatus, setSelectedStatus, search, setSearch, setRevision, modalType, setModalType, activeRefund, setActiveRefund, refundBusy, paymentDetails, selectedPayment, setSelectedPayment, handleCreateRefund, handleUpdateStatus, filteredRefunds, isUncertain };
}
