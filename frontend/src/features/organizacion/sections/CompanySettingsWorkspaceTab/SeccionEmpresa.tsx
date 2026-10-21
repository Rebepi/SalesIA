import type { useCompanySettingsWorkspaceTab } from "../../hooks/useCompanySettingsWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Building2, Loader2, Save } from "lucide-react";
import { CompanySettingsWorkspaceTabProps } from "../../types/CompanySettingsWorkspaceTab";

export function SeccionEmpresa({ saveCompany, legalName, setLegalName, canWrite, inputClass, tradeName, setTradeName, company, baseCurrency, setBaseCurrency, saving }: { saveCompany: ReturnType<typeof useCompanySettingsWorkspaceTab>["saveCompany"]; legalName: ReturnType<typeof useCompanySettingsWorkspaceTab>["legalName"]; setLegalName: ReturnType<typeof useCompanySettingsWorkspaceTab>["setLegalName"]; inputClass: ReturnType<typeof useCompanySettingsWorkspaceTab>["inputClass"]; tradeName: ReturnType<typeof useCompanySettingsWorkspaceTab>["tradeName"]; setTradeName: ReturnType<typeof useCompanySettingsWorkspaceTab>["setTradeName"]; company: ReturnType<typeof useCompanySettingsWorkspaceTab>["company"]; baseCurrency: ReturnType<typeof useCompanySettingsWorkspaceTab>["baseCurrency"]; setBaseCurrency: ReturnType<typeof useCompanySettingsWorkspaceTab>["setBaseCurrency"]; saving: ReturnType<typeof useCompanySettingsWorkspaceTab>["saving"] } & { canWrite: NonNullable<CompanySettingsWorkspaceTabProps["canWrite"]> }) {
  return (<form onSubmit={saveCompany} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
    <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-4">
      <div className="flex items-center gap-3">
        <Building2 className="h-5 w-5 text-teal-700" />
        <div>
          <h2 className="font-bold text-slate-900">Identificación Fiscal y Moneda Base</h2>
          <p className="text-xs text-slate-500">Parámetros principales de la persona jurídica registrada.</p>
        </div>
      </div>
      <span className="rounded-md bg-teal-50 px-2.5 py-1 text-xs font-bold text-teal-800 border border-teal-200">
        Registro de Vigencia e Impacto (ALC-009)
      </span>
    </div>

    <div className="grid gap-4 md:grid-cols-2">
      <label className="text-xs font-semibold text-slate-700">
        Razón Social
        <input
          required
          maxLength={255}
          value={legalName}
          onChange={event => setLegalName(event.target.value)}
          disabled={!canWrite}
          placeholder="Distribuidora Mayorista Lima S.A.C."
          className={inputClass}
        />
      </label>

      <label className="text-xs font-semibold text-slate-700">
        Nombre Comercial
        <input
          required
          maxLength={255}
          value={tradeName}
          onChange={event => setTradeName(event.target.value)}
          disabled={!canWrite}
          placeholder="SalesIA Distribución"
          className={inputClass}
        />
      </label>

      <label className="text-xs font-semibold text-slate-700">
        Número de Identificación Fiscal (RUC / NIT)
        <input
          value={company?.tax_id || ""}
          disabled
          title="El identificador fiscal está bloqueado para preservar trazabilidad fiscal"
          className={inputClass}
        />
        <span className="mt-1 block text-[11px] text-slate-400">Dato protegido inmutable por normativa.</span>
      </label>

      <label className="text-xs font-semibold text-slate-700">
        Moneda Base Contable
        <CustomSelect
          value={baseCurrency}
          onChange={event => setBaseCurrency(event.target.value)}
          disabled={!canWrite}
          className={inputClass}
        >
          <option value="PEN">Sol Peruano (PEN - S/)</option>
          <option value="USD">Dólar Estadounidense (USD - $)</option>
          <option value="EUR">Euro (EUR - €)</option>
        </CustomSelect>
        <span className="mt-1 block text-[11px] text-slate-400">Afecta toda la contabilidad y saldos registrados.</span>
      </label>
    </div>

    <div className="flex justify-end border-t border-slate-100 pt-4">
      <button
        type="submit"
        disabled={!canWrite || saving}
        className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
      >
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        Guardar datos de empresa
      </button>
    </div>
  </form>);
}
