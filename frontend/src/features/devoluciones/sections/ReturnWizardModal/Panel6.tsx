import type { useReturnWizardModal } from "../../hooks/useReturnWizardModal";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { ReturnWizardModalProps } from "../../types/ReturnWizardModal";

export function Panel6({ step, setStep, isSubmitting, onClose, canProceedStep1, independentReviewRequired, formId }: { step: ReturnType<typeof useReturnWizardModal>["step"]; setStep: ReturnType<typeof useReturnWizardModal>["setStep"]; isSubmitting: ReturnType<typeof useReturnWizardModal>["isSubmitting"] } & { onClose: ReturnWizardModalProps["onClose"] } & { canProceedStep1: () => boolean; independentReviewRequired?: boolean; formId?: string }) {
  return (<footer className="return-wizard-actions">
    {step > 1 ? (
      <button
        type="button"
        onClick={() => setStep((s) => s - 1)}
        disabled={isSubmitting}
        className="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
      >
        <ChevronLeft className="h-4 w-4" />
        Anterior
      </button>
    ) : (
      <button
        type="button"
        onClick={onClose}
        disabled={isSubmitting}
        className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
      >
        Cancelar
      </button>
    )}

    {step < 4 ? (
      <button
        type="button"
        disabled={step === 1 && !canProceedStep1()}
        onClick={() => setStep((s) => s + 1)}
        className="inline-flex items-center gap-1 rounded-xl bg-teal-700 px-5 py-2 text-xs font-semibold text-white transition hover:bg-teal-800 disabled:opacity-40"
      >
        Siguiente
        <ChevronRight className="h-4 w-4" />
      </button>
    ) : (
      <button
        type="submit"
        form={formId}
        disabled={isSubmitting}
        className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-6 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-800 focus:outline-none focus:ring-4 focus:ring-teal-100 disabled:opacity-50"
      >
        {isSubmitting ? "Procesando…" : independentReviewRequired ? "Enviar solicitud a revisión" : "Confirmar devolución y efectos"}
      </button>
    )}
  </footer>);
}
