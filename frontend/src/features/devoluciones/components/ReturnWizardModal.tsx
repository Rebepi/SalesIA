import { SeccionDevolucionConfirmadaConExito } from "../sections/ReturnWizardModal/SeccionDevolucionConfirmadaConExito";
import { Panel2 } from "../sections/ReturnWizardModal/Panel2";
import { Panel3 } from "../sections/ReturnWizardModal/Panel3";
import { Panel4 } from "../sections/ReturnWizardModal/Panel4";
import { Panel5 } from "../sections/ReturnWizardModal/Panel5";
import { Panel6 } from "../sections/ReturnWizardModal/Panel6";
export type { ReturnWizardModalProps } from "../types/ReturnWizardModal";
export type { EligibleLine } from "../types/ReturnWizardModal";
import { useReturnWizardModal } from "../hooks/useReturnWizardModal";
import { FormEvent, useEffect, useRef } from "react";
import { Check, RotateCcw, X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { returnProblem } from "../api/returnFlow";
import "../../ventas/components/ventas-return.css";
import { ReturnWizardModalProps } from "../types/ReturnWizardModal";

export function ReturnWizardModal({
  isOpen,
  onClose,
  saleId,
  documentNumber,
  customerName,
  warehouseId,
  onSuccess,
  renderCompletion
}: ReturnWizardModalProps) {
  const { independentReviewRequired, awaitingReview, setAwaitingReview, retryLoad, canGrantStoreCredit, finalSettlement, setFinalSettlement, finalValuation, setFinalValuation, conditions, setConditions, packaging, setPackaging, evidenceNotes, setEvidenceNotes, waiveRetention, setWaiveRetention, canAuthorizeException, currency, businessDate, pendingRequests, submittingLock, serialSelections, setSerialSelections, step, setStep, lines, quantities, setQuantities, dispositions, setDispositions, reason, setReason, creditAction, setCreditAction, authorizedException, setAuthorizedException, exceptionReason, setExceptionReason, loading, isSubmitting, setIsSubmitting, isSuccess, setIsSuccess, generatedReturnId, setGeneratedReturnId, error, setError, toast } = useReturnWizardModal({ isOpen, onClose, saleId, documentNumber, customerName, warehouseId, onSuccess });
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (!isOpen) return;
    const element = dialog.current;
    const previous = document.activeElement as HTMLElement | null;
    element?.showModal();
    return () => { element?.close(); if (previous?.isConnected) previous.focus(); };
  }, [isOpen]);
  if (!isOpen) return null;

  const selectedItems = lines.filter((l) => (quantities[l.sale_line_id || l.product_id] || 0) > 0);

  const estimatedRefundTotal = selectedItems.reduce((acc, line) => {
    const qty = quantities[line.sale_line_id || line.product_id] || 0;
    const price = Number(line.unit_price) || 0;
    const retained = waiveRetention ? 0 : Number(line.return_policy?.rule.retention_percentage || 0);
    return acc + qty * price * (1 - retained / 100) * (1 + Number(line.tax_rate_snapshot || 0));
  }, 0);

  function handleQuantityChange(productId: string, val: number, max: number) {
    const sanitized = Number.isFinite(val) ? Math.max(0, Math.min(val, max)) : 0;
    setQuantities((prev) => ({ ...prev, [productId]: sanitized }));
  }

  function handleDispositionChange(productId: string, disp: "RESTOCK" | "QUARANTINE" | "DISPOSE") {
    setDispositions((prev) => ({ ...prev, [productId]: disp }));
  }

  function canProceedStep1(): boolean {
    if (selectedItems.length === 0) return false;
    if (reason.trim().length < 3 || reason.trim().length > 255) return false;
    if (selectedItems.some(line => { const quantity = quantities[line.sale_line_id || line.product_id]; return !Number.isFinite(quantity) || quantity <= 0 || quantity > Number(line.eligible_quantity); })) return false;
    if ((authorizedException || waiveRetention) && (!canAuthorizeException || exceptionReason.trim().length < 5)) return false;
    if (selectedItems.some(line => {
      const policy = line.return_policy;
      if (!policy) return false;
      const key = line.sale_line_id || line.product_id;
      const rule = policy.rule;
      if (rule.evidence_required && (evidenceNotes[key] || "").trim().length < 5) return true;
      const fails = !rule.returnable || (line.policy_evaluation?.deadline || businessDate) < businessDate || !rule.allowed_conditions.includes(conditions[key] || "unused") || !rule.allowed_packaging.includes(packaging[key] || "sealed");
      return (fails && (!authorizedException || !rule.allow_exceptions)) || (waiveRetention && Number(rule.retention_percentage) > 0 && !rule.allow_exceptions);
    })) return false;
    if (selectedItems.some(line => (line.serial_numbers?.length || 0) > 0 && (serialSelections[line.sale_line_id || line.product_id]?.length || 0) !== quantities[line.sale_line_id || line.product_id])) return false;
    return true;
  }

  async function handleSubmitReturn(e: FormEvent) {
    e.preventDefault();
    if (submittingLock.current || isSubmitting || selectedItems.length === 0 || !canProceedStep1()) return;

    if (!warehouseId) {
      setError("La venta no tiene un almacén asociado. Configura o corrige el almacén antes de registrar la devolución.");
      return;
    }

    submittingLock.current = true;
    setIsSubmitting(true);
    setError("");

    try {
      const itemsPayload = selectedItems.map((line) => ({
        product_id: line.product_id,
        sale_line_id: line.sale_line_id,
        serial_numbers: serialSelections[line.sale_line_id || line.product_id] || [],
        quantity: String(quantities[line.sale_line_id || line.product_id]),
        disposition: dispositions[line.sale_line_id || line.product_id] || "RESTOCK",
        condition: conditions[line.sale_line_id || line.product_id] || "unused",
        packaging: packaging[line.sale_line_id || line.product_id] || "sealed",
        evidence_note: evidenceNotes[line.sale_line_id || line.product_id] || ""
      }));

      const body = {
        sale_id: saleId,
        warehouse_id: warehouseId,
        reason: reason.trim(),
        items: itemsPayload,
        authorized_exception: authorizedException,
        waive_retention: waiveRetention,
        exception_reason: authorizedException || waiveRetention ? exceptionReason.trim() : null
      };

      const signature = JSON.stringify(body);
      const createKey = pendingRequests.current.get(signature) || crypto.randomUUID();
      pendingRequests.current.set(signature, createKey);
      const res = generatedReturnId ? { id: generatedReturnId } : await apiClient.request<{ id: string }>("/api/v1/returns", {
        method: "POST",
        headers: { "Idempotency-Key": createKey },
        body: JSON.stringify(body)
      });

      const returnId = res.id;
      setGeneratedReturnId(returnId);
      if (independentReviewRequired) {
        setAwaitingReview(true);
        setIsSuccess(true);
        toast.success("Solicitud de devolución registrada", "Otra persona autorizada debe revisarla antes de mover inventario o liquidar dinero.");
        onSuccess?.(returnId);
        return;
      }

      const acceptSignature = JSON.stringify({ returnId, creditAction, itemsPayload });
      const acceptKey = pendingRequests.current.get(acceptSignature) || crypto.randomUUID();
      pendingRequests.current.set(acceptSignature, acceptKey);
      const accepted = await apiClient.request<{ valuation?: { retained_total: string; refundable_total: string }; settlement?: { available_amount: string; movements?: { kind: string; amount: string }[] } }>(`/api/v1/returns/${returnId}/accept`, {
        method: "POST",
        headers: {
          "Idempotency-Key": acceptKey
        },
        body: JSON.stringify({
          create_credit_note: true,
          credit_action: creditAction,
          inspections: itemsPayload.map((it) => ({
            product_id: it.product_id,
            sale_line_id: it.sale_line_id,
            disposition: it.disposition
          }))
        })
      });

      setFinalValuation(accepted.valuation || null);
      setFinalSettlement(accepted.settlement ? { available_amount: accepted.settlement.available_amount, movements: accepted.settlement.movements || [] } : null);
      setIsSuccess(true);
      toast.success("Devolución y efectos procesados", `Devolución ${returnId} aceptada con éxito.`);
      if (onSuccess) onSuccess(returnId);
    } catch (err: unknown) {
      const msg = returnProblem(err);
      setError(msg);
      toast.error("Error en la devolución", msg);
    } finally {
      submittingLock.current = false;
      setIsSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialog}
      onCancel={event => { event.preventDefault(); if (!isSubmitting) onClose(); }}
      id="scr-029-return-wizard"
      role="dialog"
      aria-modal="true"
      aria-labelledby="return-wizard-title"
      className="sales-return-dialog m-auto max-h-[94dvh] max-w-[96vw] overflow-hidden rounded-2xl border-0 bg-transparent p-0"
    >
      <div className="sales-return-workspace app-modal-panel flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-100 text-teal-700">
              <RotateCcw className="h-5 w-5" />
            </div>
            <div>
              <h2 id="return-wizard-title" className="text-lg font-semibold text-slate-900">
                Asistente de Devolución Comercial
              </h2>
              <p className="text-xs text-slate-500">
                Documento: <span className="font-medium text-slate-700">{documentNumber}</span> · Cliente:{" "}
                <span className="font-medium text-slate-700">{customerName}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-200 hover:text-slate-700"
            aria-label="Cerrar asistente"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <nav aria-label="Pasos de la devolución" className="border-b border-slate-200 bg-slate-100/60 px-6 py-3">
          <ol className="flex items-center justify-between gap-2 text-xs font-medium">
            <li className={`flex items-center gap-2 ${step === 1 ? "font-bold text-teal-700" : step > 1 ? "text-emerald-700" : "text-slate-400"}`}>
              <span className={`flex h-6 w-6 items-center justify-center rounded-full ${step === 1 ? "bg-teal-700 text-white" : step > 1 ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"}`}>
                {step > 1 ? <Check className="h-3.5 w-3.5" /> : "1"}
              </span>
              <span>1. Productos</span>
            </li>
            <span className="text-slate-300">→</span>
            <li className={`flex items-center gap-2 ${step === 2 ? "font-bold text-teal-700" : step > 2 ? "text-emerald-700" : "text-slate-400"}`}>
              <span className={`flex h-6 w-6 items-center justify-center rounded-full ${step === 2 ? "bg-teal-700 text-white" : step > 2 ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"}`}>
                {step > 2 ? <Check className="h-3.5 w-3.5" /> : "2"}
              </span>
              <span>2. Destino físico</span>
            </li>
            <span className="text-slate-300">→</span>
            <li className={`flex items-center gap-2 ${step === 3 ? "font-bold text-teal-700" : step > 3 ? "text-emerald-700" : "text-slate-400"}`}>
              <span className={`flex h-6 w-6 items-center justify-center rounded-full ${step === 3 ? "bg-teal-700 text-white" : step > 3 ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"}`}>
                {step > 3 ? <Check className="h-3.5 w-3.5" /> : "3"}
              </span>
              <span>3. Crédito y Dinero</span>
            </li>
            <span className="text-slate-300">→</span>
            <li className={`flex items-center gap-2 ${step === 4 ? "font-bold text-teal-700" : "text-slate-400"}`}>
              <span className={`flex h-6 w-6 items-center justify-center rounded-full ${step === 4 ? "bg-teal-700 text-white" : "bg-slate-200 text-slate-600"}`}>
                4
              </span>
              <span>4. Resumen</span>
            </li>
          </ol>
        </nav>

        <div className="min-h-0 flex-1 overflow-y-auto p-6">
          {error && (
            <div role="alert" className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              {error}
              {!generatedReturnId && !lines.length && <button type="button" onClick={retryLoad}>Reintentar carga de productos</button>}
              {generatedReturnId && <p className="mt-2">La devolución {generatedReturnId} ya está registrada y pendiente de aceptación. El reintento continuará con ese documento.</p>}
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-500">
              <RotateCcw className="h-8 w-8 animate-spin text-teal-600" />
              <p className="mt-3 text-sm">Consultando líneas elegibles de la venta…</p>
            </div>
          ) : isSuccess ? (
            awaitingReview ? <div role="status" className="space-y-4 rounded-xl border p-5"><h3 className="font-bold">Solicitud de devolución registrada</h3><p>Identificador: {generatedReturnId}</p><p>Está pendiente de revisión independiente. Otra persona autorizada puede abrir esta venta, elegir «Continuar devolución» y aceptarla. Todavía no se han movido existencias ni desembolsado dinero.</p><button type="button" onClick={onClose}>Cerrar solicitud</button></div> : <><SeccionDevolucionConfirmadaConExito generatedReturnId={generatedReturnId} creditAction={creditAction} onClose={onClose} currency={currency} finalValuation={finalValuation} finalSettlement={finalSettlement} hideClose={Boolean(renderCompletion)} />{renderCompletion?.(generatedReturnId, setIsSubmitting)}</>
          ) : (
            <form onSubmit={handleSubmitReturn}>
              {!lines.some(line => Number(line.eligible_quantity) > 0) && !loading && !error && <p role="status" className="mb-4 rounded-xl border p-4">No quedan unidades entregadas disponibles para devolver. Las devoluciones aceptadas y las solicitudes pendientes ya se descontaron.</p>}
              <fieldset disabled={isSubmitting || Boolean(generatedReturnId)} className="min-w-0">
              {step === 1 && (
                <Panel2 lines={lines} quantities={quantities} handleQuantityChange={handleQuantityChange} reason={reason} setReason={setReason} authorizedException={authorizedException} setAuthorizedException={setAuthorizedException} exceptionReason={exceptionReason} setExceptionReason={setExceptionReason} canAuthorizeException={canAuthorizeException} currency={currency} />
              )}

              {step === 1 && selectedItems.map(line => {
                const key = line.sale_line_id || line.product_id;
                const policy = line.return_policy;
                return <fieldset key={`policy-${key}`} className="my-4 space-y-3 rounded-xl border p-4"><legend className="px-2 text-sm font-semibold">Condiciones de {line.product_name}</legend>{policy && <p className="text-xs text-slate-600">Política {policy.version} · {policy.source === "legacy_default" ? "Condiciones históricas" : `Vigente al vender el ${policy.sold_on}`} · Plazo hasta {line.policy_evaluation?.deadline} · Retención {policy.rule.retention_percentage}% {policy.rule.retention_description}</p>}
                  {line.policy_evaluation?.reasons.filter(item => !["evidence", "condition_missing", "packaging_missing"].includes(item.code)).map(item => <p key={item.code} className="text-xs text-amber-800">{item.message}</p>)}
                  {policy && (!policy.rule.allowed_conditions.includes(conditions[key] || "unused") || !policy.rule.allowed_packaging.includes(packaging[key] || "sealed")) && <p className="text-xs text-amber-800">El estado o empaque seleccionado requiere una excepción permitida por la política.</p>}
                  <div className="grid gap-3 sm:grid-cols-2"><label className="grid gap-1 text-xs">Estado del artículo<select className="rounded-lg border p-2" value={conditions[key] || "unused"} onChange={event => setConditions(previous => ({ ...previous, [key]: event.target.value }))}>{[["unused", "Sin uso"], ["used", "Usado"], ["damaged", "Dañado"], ["not_applicable", "No aplica"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label className="grid gap-1 text-xs">Estado del empaque<select className="rounded-lg border p-2" value={packaging[key] || "sealed"} onChange={event => setPackaging(previous => ({ ...previous, [key]: event.target.value }))}>{[["sealed", "Sellado"], ["opened", "Abierto"], ["missing", "Sin empaque"], ["not_applicable", "No aplica"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
                  <label className="grid gap-1 text-xs">Evidencia y sustento {policy?.rule.evidence_required ? "(obligatorio)" : "(opcional)"}<textarea className="rounded-lg border p-2" maxLength={2000} minLength={policy?.rule.evidence_required ? 5 : undefined} value={evidenceNotes[key] || ""} onChange={event => setEvidenceNotes(previous => ({ ...previous, [key]: event.target.value }))} /></label>
                </fieldset>;
              })}
              {step === 1 && canAuthorizeException && <label className="my-3 flex gap-2 text-xs"><input type="checkbox" checked={waiveRetention} onChange={event => { setWaiveRetention(event.target.checked); if (event.target.checked) setAuthorizedException(true); }} />Exonerar retenciones con justificación de la excepción</label>}
              {step === 1 && <p className="my-3 text-xs text-slate-600">Valoración estimada tras retenciones: {currency} {estimatedRefundTotal.toFixed(2)}. La evidencia obligatoria no se omite mediante una excepción.</p>}
              {step === 1 && selectedItems.filter(line => (line.serial_numbers?.length || 0) > 0).map(line => {
                const key = line.sale_line_id || line.product_id;
                const selected = serialSelections[key] || [];
                return <fieldset key={key} className="my-4 rounded-xl border border-slate-200 p-4"><legend className="px-2 text-sm font-semibold">Series de {line.product_name}: {selected.length} de {quantities[key]}</legend><div className="flex flex-wrap gap-3">{line.serial_numbers?.map(serial => <label key={serial} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={selected.includes(serial)} onChange={event => setSerialSelections(previous => ({ ...previous, [key]: event.target.checked ? [...selected, serial] : selected.filter(value => value !== serial) }))} />{serial}</label>)}</div></fieldset>;
              })}

              {step === 2 && (
                <Panel3 selectedItems={selectedItems} quantities={quantities} dispositions={dispositions} handleDispositionChange={handleDispositionChange} />
              )}

              {step === 3 && (
                <Panel4 estimatedRefundTotal={estimatedRefundTotal} creditAction={creditAction} setCreditAction={setCreditAction} currency={currency} canGrantStoreCredit={canGrantStoreCredit} />
              )}

              {step === 4 && independentReviewRequired && <p className="mb-4 rounded-xl border p-4 text-sm">La empresa exige revisión independiente: se registrará una solicitud pendiente para que otra persona autorizada la acepte. El inventario y la liquidación se aplican después de esa aceptación.</p>}
              {step === 4 && (
                <Panel5 selectedItems={selectedItems} creditAction={creditAction} estimatedRefundTotal={estimatedRefundTotal} currency={currency} />
              )}

              </fieldset>
              <Panel6 step={step} setStep={setStep} isSubmitting={isSubmitting} onClose={onClose} canProceedStep1={canProceedStep1} independentReviewRequired={independentReviewRequired} />
            </form>
          )}
        </div>
      </div>
    </dialog>
  );
}
