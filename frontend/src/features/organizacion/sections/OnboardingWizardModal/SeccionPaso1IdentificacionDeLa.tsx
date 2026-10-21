import type { useOnboardingWizardModal } from "../../hooks/useOnboardingWizardModal";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { ChevronRight, ChevronLeft, LoaderCircle, AlertCircle } from "lucide-react";

export function SeccionPaso1IdentificacionDeLa({ handleSubmit, error, step, formData, updateField, setStep, busy }: { handleSubmit: ReturnType<typeof useOnboardingWizardModal>["handleSubmit"]; error: ReturnType<typeof useOnboardingWizardModal>["error"]; step: ReturnType<typeof useOnboardingWizardModal>["step"]; formData: ReturnType<typeof useOnboardingWizardModal>["formData"]; updateField: ReturnType<typeof useOnboardingWizardModal>["updateField"]; setStep: ReturnType<typeof useOnboardingWizardModal>["setStep"]; busy: ReturnType<typeof useOnboardingWizardModal>["busy"] }) {
  return (<div className="grid lg:grid-cols-[1fr_260px] min-h-[360px]">
    <form onSubmit={handleSubmit} className="p-6 space-y-4">
      {error && (
        <div role="alert" className="flex items-center gap-2 rounded-xl bg-red-50 p-3 text-xs text-red-800">
          <AlertCircle className="h-4 w-4 flex-shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-slate-900">Paso 1: Identificación de la Empresa</h3>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
            RUC / Identificación tributaria
            <input
              required
              value={formData.tax_id}
              onChange={e => updateField("tax_id", e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
            />
          </label>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
            Razón Social
            <input
              required
              value={formData.legal_name}
              onChange={e => updateField("legal_name", e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
              Nombre Comercial
              <input
                value={formData.trade_name}
                onChange={e => updateField("trade_name", e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
              />
            </label>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
              Moneda Base
              <CustomSelect
                value={formData.base_currency}
                onChange={e => updateField("base_currency", e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
              >
                <option value="USD">USD (Dólares)</option>
                <option value="PEN">PEN (Soles)</option>
                <option value="EUR">EUR (Euros)</option>
              </CustomSelect>
            </label>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-slate-900">Paso 2: Sede Principal (Sucursal)</h3>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
              Código de Sede
              <input
                required
                value={formData.branch_code}
                onChange={e => updateField("branch_code", e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
              />
            </label>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
              Nombre de Sede
              <input
                required
                value={formData.branch_name}
                onChange={e => updateField("branch_name", e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
              />
            </label>
          </div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
            Zona Horaria
            <input
              required
              value={formData.timezone}
              onChange={e => updateField("timezone", e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
            />
          </label>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-slate-900">Paso 3: Almacén Inicial</h3>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
            Código de Almacén
            <input
              required
              value={formData.warehouse_code}
              onChange={e => updateField("warehouse_code", e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
            />
          </label>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
            Nombre de Almacén
            <input
              required
              value={formData.warehouse_name}
              onChange={e => updateField("warehouse_name", e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
            />
          </label>
        </div>
      )}

      {step === 4 && (
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-slate-900">Paso 4: Correlativos y Facturación</h3>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
            Serie de Facturación Inicial
            <input
              required
              value={formData.series}
              onChange={e => updateField("series", e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
            />
          </label>
          <p className="text-xs text-slate-500">
            La serie F001 inicializará los correlativos inmutables de ventas para la sede configurada.
          </p>
        </div>
      )}

      <div className="flex items-center justify-between pt-6 border-t border-slate-100">
        {step > 1 ? (
          <button
            type="button"
            onClick={() => setStep(s => s - 1)}
            className="inline-flex items-center gap-1 rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <ChevronLeft className="h-4 w-4" /> Anterior
          </button>
        ) : <div />}

        <button
          type="submit"
          disabled={busy}
          className="inline-flex items-center gap-1 rounded-xl bg-teal-700 px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-teal-800 disabled:opacity-50"
        >
          {busy && <LoaderCircle className="h-4 w-4 motion-safe:animate-spin" />}
          {step === 4 ? "Finalizar configuración" : "Siguiente"}
          {step < 4 && <ChevronRight className="h-4 w-4" />}
        </button>
      </div>
    </form>

    <aside className="border-t lg:border-t-0 lg:border-l border-slate-100 bg-slate-50/70 p-5 space-y-4">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Resumen Lateral</p>
      <div className="space-y-3 text-xs text-slate-700">
        <div>
          <span className="block text-[11px] text-slate-400">Razón Social:</span>
          <strong className="text-slate-900">{formData.legal_name || "—"}</strong>
        </div>
        <div>
          <span className="block text-[11px] text-slate-400">RUC:</span>
          <span>{formData.tax_id || "—"}</span>
        </div>
        <div>
          <span className="block text-[11px] text-slate-400">Moneda:</span>
          <span className="font-semibold text-teal-800">{formData.base_currency}</span>
        </div>
        <div>
          <span className="block text-[11px] text-slate-400">Sede:</span>
          <span>{formData.branch_name} ({formData.branch_code})</span>
        </div>
        <div>
          <span className="block text-[11px] text-slate-400">Almacén:</span>
          <span>{formData.warehouse_name} ({formData.warehouse_code})</span>
        </div>
        <div>
          <span className="block text-[11px] text-slate-400">Serie Inicial:</span>
          <span className="font-mono font-semibold">{formData.series}</span>
        </div>
      </div>
      <p className="text-[10px] text-slate-400 pt-3 border-t border-slate-200">
        Los datos se guardan localmente para poder retomar el asistente en cualquier momento sin duplicar registros.
      </p>
    </aside>
  </div>);
}
