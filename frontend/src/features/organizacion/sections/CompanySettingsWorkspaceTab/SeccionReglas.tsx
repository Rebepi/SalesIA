import { useId, useState } from "react";
import "./commercial-policies.css";
import { SettingLabel, SettingSwitch, SettingsHelp } from "../../../../ui/components/SettingsControls";
import { AccountingPeriodsEditor } from "../../components/AccountingPeriodsEditor";
import { ApprovalPoliciesEditor } from "../../../aprobaciones/components/ApprovalPoliciesEditor";
import { BusinessPoliciesEditor } from "../../components/BusinessPoliciesEditor";
import type { useCompanySettingsWorkspaceTab } from "../../hooks/useCompanySettingsWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Clock, Loader2, Save, Settings2, Receipt, BadgePercent, ShieldCheck, CalendarCheck } from "lucide-react";
import { CompanySettingsWorkspaceTabProps } from "../../types/CompanySettingsWorkspaceTab";

export function SeccionReglas({ saveCommercialSettings, settings, taxRate, setTaxRate, canWrite, inputClass, roundingMode, setRoundingMode, creditLimitStrict, setCreditLimitStrict, taxIncluded, setTaxIncluded, allowCreditSales, setAllowCreditSales, holdExpirationValue, setHoldExpirationValue, holdExpirationUnit, setHoldExpirationUnit, saving, taxRules, setRuleDraft, saveTaxRule, ruleDraft }: { saveCommercialSettings: ReturnType<typeof useCompanySettingsWorkspaceTab>["saveCommercialSettings"]; settings: ReturnType<typeof useCompanySettingsWorkspaceTab>["settings"]; taxRate: ReturnType<typeof useCompanySettingsWorkspaceTab>["taxRate"]; setTaxRate: ReturnType<typeof useCompanySettingsWorkspaceTab>["setTaxRate"]; inputClass: ReturnType<typeof useCompanySettingsWorkspaceTab>["inputClass"]; roundingMode: ReturnType<typeof useCompanySettingsWorkspaceTab>["roundingMode"]; setRoundingMode: ReturnType<typeof useCompanySettingsWorkspaceTab>["setRoundingMode"]; creditLimitStrict: ReturnType<typeof useCompanySettingsWorkspaceTab>["creditLimitStrict"]; setCreditLimitStrict: ReturnType<typeof useCompanySettingsWorkspaceTab>["setCreditLimitStrict"]; taxIncluded: ReturnType<typeof useCompanySettingsWorkspaceTab>["taxIncluded"]; setTaxIncluded: ReturnType<typeof useCompanySettingsWorkspaceTab>["setTaxIncluded"]; allowCreditSales: ReturnType<typeof useCompanySettingsWorkspaceTab>["allowCreditSales"]; setAllowCreditSales: ReturnType<typeof useCompanySettingsWorkspaceTab>["setAllowCreditSales"]; holdExpirationValue: ReturnType<typeof useCompanySettingsWorkspaceTab>["holdExpirationValue"]; setHoldExpirationValue: ReturnType<typeof useCompanySettingsWorkspaceTab>["setHoldExpirationValue"]; holdExpirationUnit: ReturnType<typeof useCompanySettingsWorkspaceTab>["holdExpirationUnit"]; setHoldExpirationUnit: ReturnType<typeof useCompanySettingsWorkspaceTab>["setHoldExpirationUnit"]; saving: ReturnType<typeof useCompanySettingsWorkspaceTab>["saving"]; taxRules: ReturnType<typeof useCompanySettingsWorkspaceTab>["taxRules"]; setRuleDraft: ReturnType<typeof useCompanySettingsWorkspaceTab>["setRuleDraft"]; saveTaxRule: ReturnType<typeof useCompanySettingsWorkspaceTab>["saveTaxRule"]; ruleDraft: ReturnType<typeof useCompanySettingsWorkspaceTab>["ruleDraft"] } & { canWrite: NonNullable<CompanySettingsWorkspaceTabProps["canWrite"]> }) {
  const [activeTab, setActiveTab] = useState("sales");
  const id = useId();
  const tabs = [{ key: "sales", label: "Ventas y crédito", icon: Settings2 }, { key: "tax", label: "Reglas fiscales", icon: Receipt }, { key: "business", label: "Precios y abastecimiento", icon: BadgePercent }, { key: "approvals", label: "Aprobaciones", icon: ShieldCheck }, { key: "periods", label: "Cierres y reaperturas", icon: CalendarCheck }];
  return (<div className="commercial-policies space-y-5">
    <div className="settings-policy-tabs" role="tablist" aria-label="Apartados de políticas comerciales y fiscales">{tabs.map(({ key, label, icon: Icon }) => <button type="button" key={key} role="tab" id={`${id}-tab-${key}`} aria-controls={`${id}-panel-${key}`} aria-selected={activeTab === key} tabIndex={activeTab === key ? 0 : -1} onClick={() => setActiveTab(key)} onKeyDown={event => {
      const index = tabs.findIndex(tab => tab.key === key);
      const next = event.key === "ArrowRight" ? tabs[(index + 1) % tabs.length] : event.key === "ArrowLeft" ? tabs[(index + tabs.length - 1) % tabs.length] : event.key === "Home" ? tabs[0] : event.key === "End" ? tabs[tabs.length - 1] : null;
      if (next) { event.preventDefault(); setActiveTab(next.key); document.getElementById(`${id}-tab-${next.key}`)?.focus(); }
    }}><Icon size={17} aria-hidden="true" />{label}</button>)}</div>
    <div role="tabpanel" id={`${id}-panel-sales`} aria-labelledby={`${id}-tab-sales`} hidden={activeTab !== "sales"}>
    <form onSubmit={saveCommercialSettings} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
      <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
        <Settings2 className="h-5 w-5 text-teal-700" />
        <div>
          <div className="settings-section-heading"><h2 className="font-bold text-slate-900">Políticas Comerciales</h2><SettingsHelp title="Políticas comerciales" description="Define los valores generales de impuestos, redondeo, crédito y caducidad de ventas en espera. Guarda esta sección para aplicar sus cambios." /></div>
          <p className="text-xs text-slate-500">Versión actual: {settings?.version ?? 0}</p>
        </div>
      </div>

      <section className="settings-policy-subsection space-y-4"><h3>Impuestos y redondeo</h3><div className="grid gap-4 sm:grid-cols-2">
        <SettingLabel className="text-xs font-semibold text-slate-700">
          Tasa Fiscal Predeterminada
          <input
            required
            type="number"
            min="0"
            max="1"
            step="0.0001"
            value={taxRate}
            onChange={event => setTaxRate(event.target.value)}
            disabled={!canWrite}
            className={inputClass}
          />
          <span className="mt-1 block text-[11px] text-slate-400">Ejemplo: 0.18 equivale al 18%</span>
        </SettingLabel>

        <SettingLabel className="text-xs font-semibold text-slate-700">
          Modo de Redondeo
          <CustomSelect
            value={roundingMode}
            onChange={event => setRoundingMode(event.target.value)}
            disabled={!canWrite}
            className={inputClass}
          >
            <option value="ROUND_HALF_EVEN">Bancario · Empates al par</option>
            <option value="ROUND_HALF_UP">Comercial · Empates hacia arriba</option>
          </CustomSelect>
          <span className="mt-1 block text-[11px] text-slate-400">Algoritmo de cálculo decimal</span>
        </SettingLabel>
      </div>

      </section><section className="settings-policy-subsection space-y-4"><h3>Crédito y precios del catálogo</h3><div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/50 p-4">
        <SettingSwitch label="Permitir ventas a crédito en punto de venta (POS)" description="Al activarlo, el punto de venta puede registrar ventas con saldo pendiente. Al desactivarlo exige el pago total al contado." checked={allowCreditSales} onChange={event => setAllowCreditSales(event.target.checked)} disabled={!canWrite || saving} />
        <SettingSwitch label="Bloqueo estricto por superación de límite de crédito" description="Impide las operaciones a crédito que superen el límite configurado del cliente. Se evalúa junto con los controles de crédito del sistema." checked={creditLimitStrict} onChange={event => setCreditLimitStrict(event.target.checked)} disabled={!canWrite || saving} />
        <SettingSwitch label="Los precios del catálogo incluyen impuesto" description="Indica si el precio del catálogo ya incluye el impuesto para interpretar correctamente la base y el total de la venta." checked={taxIncluded} onChange={event => setTaxIncluded(event.target.checked)} disabled={!canWrite || saving} />
      </div>

      </section><div className="settings-hold-policy space-y-3">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-amber-600" />
          <h3 className="text-xs font-bold text-slate-800">
            Caducidad de Ventas en Espera (Mostrador)
          </h3>
        </div>
        <p className="text-[11px] text-slate-500">
          Define cuánto tiempo se conserva una venta en espera en el mostrador.
        </p>

        <div className="grid grid-cols-2 gap-3">
          <SettingLabel className="text-xs font-semibold text-slate-700">
            Duración
            <input
              required
              type="number"
              min="1"
              max="999"
              value={holdExpirationValue}
              onChange={event => setHoldExpirationValue(Math.max(1, Number(event.target.value) || 1))}
              disabled={!canWrite}
              className={inputClass}
            />
          </SettingLabel>

          <SettingLabel className="text-xs font-semibold text-slate-700">
            Unidad de Tiempo
            <CustomSelect
              value={holdExpirationUnit}
              onChange={event => setHoldExpirationUnit(event.target.value as any)}
              disabled={!canWrite}
              className={inputClass}
            >
              <option value="MINUTES">Minutos</option>
              <option value="HOURS">Horas</option>
              <option value="DAYS">Días</option>
            </CustomSelect>
          </SettingLabel>
        </div>
      </div>

      <div className="flex justify-end border-t border-slate-100 pt-4">
        <button
          type="submit"
          disabled={!canWrite || saving}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Guardar políticas
        </button>
      </div>
    </form>
    </div><div role="tabpanel" id={`${id}-panel-tax`} aria-labelledby={`${id}-tab-tax`} hidden={activeTab !== "tax"}>
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
      <div>
        <div className="settings-section-heading"><h2 className="font-bold text-slate-900">Catálogo de Reglas Fiscales</h2><SettingsHelp title="Catálogo de reglas fiscales" description="Selecciona una regla existente para editar su código, descripción, tasa o estado. Guardar registra los cambios; limpiar deja el formulario listo para otra regla." /></div>
        <p className="text-xs text-slate-500">Selecciona una regla para editarla o crea una nueva.</p>
      </div>

      <div className="space-y-2"><h3>Reglas registradas</h3>
        {taxRules.map(rule => (
          <button
            type="button"
            key={rule.code}
            onClick={() => setRuleDraft(rule)}
            aria-pressed={ruleDraft.code === rule.code}
            className="settings-tax-rule"
          >
            <div>
              <strong className="text-sm text-slate-900">{rule.code}</strong>
              <span className="ml-2 text-xs text-slate-500">{rule.name}</span>
              {!rule.is_active && (
                <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">Inactiva</span>
              )}
            </div>
            <span className="font-mono text-sm font-bold text-teal-700">
              {(Number(rule.rate) * 100).toFixed(1)}%
            </span>
          </button>
        ))}
        {taxRules.length === 0 && (
          <p className="text-xs text-slate-400 italic">No hay reglas registradas.</p>
        )}
      </div>

      <form onSubmit={saveTaxRule} className="space-y-3 border-t border-slate-100 pt-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          {ruleDraft.code ? `Editar Regla ${ruleDraft.code}` : "Nueva Regla Fiscal"}
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <SettingLabel>Código de regla fiscal<input
            required
            maxLength={32}
            value={ruleDraft.code}
            onChange={event => setRuleDraft(current => ({ ...current, code: event.target.value.toUpperCase() }))}
            disabled={!canWrite}
            placeholder="Código (ej. IGV, ICBPER)"
            className={inputClass}
          /></SettingLabel>
          <SettingLabel>Tasa de la regla fiscal<input
            required
            type="number"
            min="0"
            max="1"
            step="0.0001"
            value={ruleDraft.rate}
            onChange={event => setRuleDraft(current => ({ ...current, rate: event.target.value }))}
            disabled={!canWrite}
            placeholder="Tasa (ej. 0.18)"
            className={inputClass}
          /></SettingLabel>
        </div>
        <SettingLabel>Nombre de la regla fiscal<input
          required
          maxLength={128}
          value={ruleDraft.name}
          onChange={event => setRuleDraft(current => ({ ...current, name: event.target.value }))}
          disabled={!canWrite}
          placeholder="Nombre descriptivo (ej. Impuesto General a las Ventas)"
          className={inputClass}
        /></SettingLabel>
        <div className="flex items-center justify-between pt-1">
          <SettingSwitch label="Regla activa" description="Una regla activa queda disponible para su uso fiscal. Desactivarla conserva el registro sin ofrecerla como regla vigente." checked={ruleDraft.is_active} onChange={event => setRuleDraft(current => ({ ...current, is_active: event.target.checked }))} disabled={!canWrite || saving} />
          {ruleDraft.code && (
            <button
              type="button"
              onClick={() => setRuleDraft({ code: "", rate: "0.18", name: "", is_active: true })}
              className="text-xs text-slate-500 hover:text-slate-700"
            >
              Limpiar formulario
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={!canWrite || saving}
          className="settings-primary w-full"
        >
          Guardar regla fiscal
        </button>
      </form>
    </section>
  </div>
    <div role="tabpanel" id={`${id}-panel-business`} aria-labelledby={`${id}-tab-business`} hidden={activeTab !== "business"}><BusinessPoliciesEditor canWrite={canWrite} /></div>
    <div role="tabpanel" id={`${id}-panel-approvals`} aria-labelledby={`${id}-tab-approvals`} hidden={activeTab !== "approvals"}><ApprovalPoliciesEditor canWrite={canWrite} /></div>
    <div role="tabpanel" id={`${id}-panel-periods`} aria-labelledby={`${id}-tab-periods`} hidden={activeTab !== "periods"}><AccountingPeriodsEditor canWrite={canWrite} /></div>
  </div>);
}
