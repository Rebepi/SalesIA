import { SeccionDevolucionConfirmadaConExito } from "../sections/ReturnWizardModal/SeccionDevolucionConfirmadaConExito";
import { ReturnPendingConfirmation } from "./ReturnPendingConfirmation";
import { ReturnHelp } from "./ReturnHelp";
import { Panel2 } from "../sections/ReturnWizardModal/Panel2";
import { Panel3 } from "../sections/ReturnWizardModal/Panel3";
import { Panel4 } from "../sections/ReturnWizardModal/Panel4";
import { Panel5 } from "../sections/ReturnWizardModal/Panel5";
import { Panel6 } from "../sections/ReturnWizardModal/Panel6";
export type { ReturnWizardModalProps } from "../types/ReturnWizardModal";
export type { EligibleLine } from "../types/ReturnWizardModal";
import { useReturnWizardModal } from "../hooks/useReturnWizardModal";
import { FormEvent, useEffect, useRef } from "react";
import { Check, RotateCcw, X, Package, PackageCheck, Wallet, ClipboardCheck } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { apiClient } from "../../../api/client";
import { returnProblem, allowsFractionalReturn } from "../api/returnFlow";
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
    const line = lines.find(item => (item.sale_line_id || item.product_id) === productId);
    const allowsFractions = allowsFractionalReturn(line);
    const normalized = allowsFractions ? val : Math.trunc(val);
    const sanitized = Number.isFinite(normalized) ? Math.max(0, Math.min(normalized, max)) : 0;
    setQuantities((prev) => ({ ...prev, [productId]: sanitized }));
  }

  function handleDispositionChange(productId: string, disp: "RESTOCK" | "QUARANTINE" | "DISPOSE") {
    setDispositions((prev) => ({ ...prev, [productId]: disp }));
  }

  function canProceedStep1(): boolean {
    if (selectedItems.length === 0) return false;
    if (reason.trim().length < 3 || reason.trim().length > 255) return false;
    if (selectedItems.some(line => { const quantity = quantities[line.sale_line_id || line.product_id]; return !Number.isFinite(quantity) || quantity <= 0 || quantity > Number(line.eligible_quantity) || (!allowsFractionalReturn(line) && !Number.isInteger(quantity)); })) return false;
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
      data-stage={awaitingReview ? "pending" : "editing"}
      className="sales-return-dialog m-auto w-[min(96vw,1100px)] max-h-[94dvh] max-w-[96vw] overflow-hidden rounded-2xl border-0 bg-transparent p-0"
    >
      <div className={`sales-return-workspace return-wizard-panel app-modal-panel ${awaitingReview ? "is-pending-review" : ""}`}>
        <header className="return-wizard-header">
          <div className="flex items-center gap-3">
            <div className="return-wizard-symbol">
              <RotateCcw className="h-5 w-5" />
            </div>
            <div>
              <h2 id="return-wizard-title" className="text-lg font-semibold text-slate-900">
                Devolución de venta
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
            className="return-wizard-close"
            aria-label="Cerrar asistente"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        {!isSuccess && <nav aria-label="Pasos de la devolución" className="return-wizard-steps">
          <ol>{[
            { title: "Productos", subtitle: "Cantidades y condiciones", icon: Package },
            { title: "Destino físico", subtitle: "Inspección y almacén", icon: PackageCheck },
            { title: "Crédito y dinero", subtitle: "Destino de la devolución", icon: Wallet },
            { title: "Resumen", subtitle: "Revisar y confirmar", icon: ClipboardCheck }
          ].map((item, index) => <li key={item.title} aria-current={step === index + 1 ? "step" : undefined} data-complete={step > index + 1}>
            <span className="return-step-symbol">{step > index + 1 ? <Check size={18} /> : <item.icon size={18} />}</span>
            <span><strong><small>{index + 1}.</small> {item.title}</strong><span className="return-step-description">{item.subtitle}</span></span>
          </li>)}</ol>
        </nav>}

        <div className="return-wizard-body">
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
            awaitingReview ? <ReturnPendingConfirmation returnId={generatedReturnId} documentNumber={documentNumber} onClose={onClose} /> : <><SeccionDevolucionConfirmadaConExito generatedReturnId={generatedReturnId} creditAction={creditAction} onClose={onClose} currency={currency} finalValuation={finalValuation} finalSettlement={finalSettlement} hideClose={Boolean(renderCompletion)} />{renderCompletion?.(generatedReturnId, setIsSubmitting)}</>
          ) : (
            <form id="sales-return-form" onSubmit={handleSubmitReturn}>
              {!lines.some(line => Number(line.eligible_quantity) > 0) && !loading && !error && <p role="status" className="mb-4 rounded-xl border p-4">No quedan unidades entregadas disponibles para devolver. Las devoluciones aceptadas y las solicitudes pendientes ya se descontaron.</p>}
              <fieldset disabled={isSubmitting || Boolean(generatedReturnId)} className="min-w-0">
              {step === 1 && (
                <Panel2 lines={lines} quantities={quantities} handleQuantityChange={handleQuantityChange} reason={reason} setReason={setReason} authorizedException={authorizedException} setAuthorizedException={setAuthorizedException} exceptionReason={exceptionReason} setExceptionReason={setExceptionReason} canAuthorizeException={canAuthorizeException} currency={currency} />
              )}

              {step === 1 && selectedItems.map(line => {
                const key = line.sale_line_id || line.product_id;
                const policy = line.return_policy;
                return <fieldset key={`policy-${key}`} className="return-policy-card my-4 space-y-3"><legend className="px-2 text-sm font-semibold">Condiciones de {line.product_name}</legend>{policy && <p className="text-xs text-slate-600"><ReturnHelp title="Política de devolución" description="Son las condiciones aplicables a este artículo al venderlo: plazo, estados admitidos, evidencia y porcentaje de retención. El sistema las verifica al registrar la solicitud." /> Política {policy.version} · {policy.source === "legacy_default" ? "Condiciones históricas" : `Vigente al vender el ${policy.sold_on}`} · Plazo hasta {line.policy_evaluation?.deadline} · Retención {policy.rule.retention_percentage}% {policy.rule.retention_description}</p>}
                  {line.policy_evaluation?.reasons.filter(item => !["evidence", "condition_missing", "packaging_missing"].includes(item.code)).map(item => <p key={item.code} className="text-xs text-amber-800">{item.message}</p>)}
                  {policy && (!policy.rule.allowed_conditions.includes(conditions[key] || "unused") || !policy.rule.allowed_packaging.includes(packaging[key] || "sealed")) && <p className="text-xs text-amber-800">El estado o empaque seleccionado requiere una excepción permitida por la política.</p>}
                  <div className="grid gap-3 sm:grid-cols-2"><label className="grid gap-1 text-xs"><span className="return-field-heading">Estado del artículo <ReturnHelp title="Estado del artículo" description="Indica si el producto está sin uso, usado o dañado. Debe coincidir con la inspección y con las condiciones permitidas por la política." /></span><CustomSelect className="rounded-lg border p-2" value={conditions[key] || "unused"} onChange={event => setConditions(previous => ({ ...previous, [key]: event.target.value }))}>{[["unused", "Sin uso"], ["used", "Usado"], ["damaged", "Dañado"], ["not_applicable", "No aplica"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label><label className="grid gap-1 text-xs"><span className="return-field-heading">Estado del empaque <ReturnHelp title="Estado del empaque" description="Registra si el empaque está sellado, abierto o ausente. Si la política no acepta ese estado, una excepción requiere autorización y justificación." /></span><CustomSelect className="rounded-lg border p-2" value={packaging[key] || "sealed"} onChange={event => setPackaging(previous => ({ ...previous, [key]: event.target.value }))}>{[["sealed", "Sellado"], ["opened", "Abierto"], ["missing", "Sin empaque"], ["not_applicable", "No aplica"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label></div>
                  <label className="grid gap-1 text-xs"><span className="return-field-heading">Evidencia y sustento {policy?.rule.evidence_required ? "(obligatorio)" : "(opcional)"} <ReturnHelp title="Evidencia de devolución" description="Describe la falla, la inspección o el sustento de la devolución. Cuando la política lo exige, registra al menos cinco caracteres; una excepción no elimina este requisito." /></span><textarea aria-label={`Evidencia y sustento ${policy?.rule.evidence_required ? "(obligatorio)" : "(opcional)"}`} className="rounded-lg border p-2" maxLength={2000} minLength={policy?.rule.evidence_required ? 5 : undefined} value={evidenceNotes[key] || ""} onChange={event => setEvidenceNotes(previous => ({ ...previous, [key]: event.target.value }))} /></label>
                </fieldset>;
              })}
              {step === 1 && canAuthorizeException && <label className="my-3 flex gap-2 text-xs"><input type="checkbox" checked={waiveRetention} onChange={event => { setWaiveRetention(event.target.checked); if (event.target.checked) setAuthorizedException(true); }} />Exonerar retenciones con justificación de la excepción</label>}
              {step === 1 && <p className="my-3 text-xs text-slate-600">La evidencia obligatoria debe completarse también cuando se autoriza una excepción.</p>}
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
                <Panel5 quantities={quantities} dispositions={dispositions} selectedItems={selectedItems} creditAction={creditAction} estimatedRefundTotal={estimatedRefundTotal} currency={currency} />
              )}

              </fieldset>

            </form>
          )}
        </div>
        {!loading && !isSuccess && <div className="return-wizard-footer">
          <div className="return-wizard-total"><span>Importe estimado a devolver <ReturnHelp title="Importe estimado" description="Considera el precio neto vendido, los impuestos y las retenciones de los artículos seleccionados. El servidor confirma el valor definitivo al aceptar la devolución." /></span><strong>{currency} {estimatedRefundTotal.toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong><small>Después de retenciones e impuestos</small></div>
          <Panel6 step={step} setStep={setStep} isSubmitting={isSubmitting} onClose={onClose} canProceedStep1={canProceedStep1} independentReviewRequired={independentReviewRequired} formId="sales-return-form" />
        </div>}
      </div>
    </dialog>
  );
}
