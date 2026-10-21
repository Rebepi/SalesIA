import { SeccionPaso1IdentificacionDeLa } from "../sections/OnboardingWizardModal/SeccionPaso1IdentificacionDeLa";
import { useOnboardingWizardModal } from "../hooks/useOnboardingWizardModal";
import { Check, X } from "lucide-react";
import { OnboardingWizardModalProps } from "../types/OnboardingWizardModal";

export function OnboardingWizardModal({ isOpen, onClose, onCompleted }: OnboardingWizardModalProps) {
  const { step, setStep, formData, busy, error, dialogRef, updateField, handleSubmit, steps } = useOnboardingWizardModal({ isOpen, onClose, onCompleted });
  if (!isOpen) return null;

  return (
    <dialog
      ref={dialogRef}
      id="scr-003-onboarding-dialog"
      onCancel={onClose}
      aria-labelledby="scr-003-title"
      className="max-h-[92vh] w-[min(96vw,840px)] rounded-3xl border-0 bg-white p-0 shadow-2xl backdrop:bg-slate-950/70"
    >
      <header className="flex items-center justify-between border-b border-slate-100 p-6">
        <div>
          <h2 id="scr-003-title" className="text-xl font-semibold text-slate-900">
            Asistente de alta guiada
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Configuración inicial de entidad, sede física, depósito y correlativos comerciales
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          disabled={busy}
          aria-label="Cerrar asistente"
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div className="grid border-b border-slate-100 bg-slate-50 grid-cols-4 px-6 py-3">
        {steps.map(s => {
          const isDone = s.num < step;
          const isCurrent = s.num === step;
          return (
            <div
              key={s.num}
              className={`flex items-center gap-2 text-xs font-medium ${isCurrent ? "text-teal-700 font-bold" : isDone ? "text-slate-700" : "text-slate-400"
                }`}
            >
              <span
                className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] ${isCurrent
                  ? "bg-teal-700 text-white shadow-sm"
                  : isDone
                    ? "bg-teal-100 text-teal-800"
                    : "bg-slate-200 text-slate-600"
                  }`}
              >
                {isDone ? <Check className="h-3 w-3" /> : s.num}
              </span>
              <span className="hidden sm:inline">{s.title}</span>
            </div>
          );
        })}
      </div>

      <SeccionPaso1IdentificacionDeLa handleSubmit={handleSubmit} error={error} step={step} formData={formData} updateField={updateField} setStep={setStep} busy={busy} />
    </dialog>
  );
}
