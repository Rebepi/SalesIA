import { OperatingProfileEditor } from "./OperatingProfileEditor";
import { FunctionSeparationEditor } from "./FunctionSeparationEditor";
import { OperatingCalendarEditor } from "./OperatingCalendarEditor";
import { SeccionEmpresa } from "../sections/CompanySettingsWorkspaceTab/SeccionEmpresa";
import { SeccionSedes } from "../sections/CompanySettingsWorkspaceTab/SeccionSedes";
import { SeccionNumbering } from "../sections/CompanySettingsWorkspaceTab/SeccionNumbering";
import { SeccionReglas } from "../sections/CompanySettingsWorkspaceTab/SeccionReglas";
import { SeccionMarca } from "../sections/CompanySettingsWorkspaceTab/SeccionMarca";
import { SeccionAppearance } from "../sections/CompanySettingsWorkspaceTab/SeccionAppearance";
export type { CompanySettingsWorkspaceTabProps } from "../types/CompanySettingsWorkspaceTab";
import { useCompanySettingsWorkspaceTab } from "../hooks/useCompanySettingsWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { Loader2 } from "lucide-react";
import { CompanySettingsWorkspaceTabProps } from "../types/CompanySettingsWorkspaceTab";

export function CompanySettingsWorkspaceTab({ canWrite = true, section }: CompanySettingsWorkspaceTabProps) {
  const { activeSection: storedSection, setActiveSection, company, settings, branches, sequences, taxRules, loading, saving, error, legalName, setLegalName, tradeName, setTradeName, baseCurrency, setBaseCurrency, taxRate, setTaxRate, roundingMode, setRoundingMode, creditLimitStrict, setCreditLimitStrict, taxIncluded, setTaxIncluded, allowCreditSales, setAllowCreditSales, holdExpirationValue, setHoldExpirationValue, holdExpirationUnit, setHoldExpirationUnit, brandingName, setBrandingName, logoUrl, setLogoUrl, footerText, setFooterText, newSeriesCode, setNewSeriesCode, ruleDraft, setRuleDraft, showNewBranchModal, setShowNewBranchModal, newBranchCode, setNewBranchCode, newBranchName, setNewBranchName, newBranchTimezone, setNewBranchTimezone, savingBranch, showNewWarehouseModal, setShowNewWarehouseModal, newWarehouseBranchId, setNewWarehouseBranchId, newWarehouseCode, setNewWarehouseCode, newWarehouseName, setNewWarehouseName, savingWarehouse, toastPosition, setSelectedToastPosition, uiTheme, setUiTheme, uiDensity, setUiDensity, reducedMotion, setReducedMotion, accessibleTables, setAccessibleTables, fontScale, setFontScale, contrastMode, setContrastMode, defaultPageSize, setDefaultPageSize, sidebarMode, setSidebarMode, appearanceSaveState, warehousesByBranch, saveCompany, saveCommercialSettings, saveBranding, handleCreateBranch, reloadLocations, handleCreateWarehouse, handleReserveSequence, saveTaxRule, persistPreferences, tabs, inputClass } = useCompanySettingsWorkspaceTab({ canWrite });
  const activeSection = section || storedSection;
  return (
    <div id="scr-046-configuration-workspace" data-testid="scr-046-configuration-workspace" className="space-y-6">
      <NavbarSectionHeader view={section && section !== "company" ? `settings_${section}` : "settings"} className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">ADMINISTRACIÓN</span>
            <h1 className="text-xl font-bold text-slate-900">Configuración de Empresa y Sucursales</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Administración de datos fiscales, sedes, almacenes, correlativos, reglas comerciales, marca y apariencia.
          </p>
        </div>

      </NavbarSectionHeader>

      {error && (
        <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </div>
      )}

      {!canWrite && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Modo de solo consulta. Se requiere permiso de administración de la organización para aplicar modificaciones.
        </div>
      )}

      {loading ? (
        <div role="status" className="flex min-h-64 items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-500">
          <Loader2 className="mr-2 h-5 w-5 animate-spin text-teal-600" />
          Cargando configuración del sistema...
        </div>
      ) : (
        <>
          {!section && <nav className="flex flex-wrap gap-2 border-b border-slate-200 pb-2" aria-label="Secciones de configuración">
            {tabs.map(tab => (
              <button
                key={tab.key}
                type="button"
                id={`tab-config-${tab.key}`}
                onClick={() => setActiveSection(tab.key)}
                aria-current={activeSection === tab.key ? "page" : undefined}
                className={`rounded-xl px-4 py-2 text-xs font-bold transition ${activeSection === tab.key
                  ? "bg-teal-700 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>}

          {activeSection === "company" && (
            <SeccionEmpresa saveCompany={saveCompany} legalName={legalName} setLegalName={setLegalName} canWrite={canWrite} inputClass={inputClass} tradeName={tradeName} setTradeName={setTradeName} company={company} baseCurrency={baseCurrency} setBaseCurrency={setBaseCurrency} saving={saving} />
          )}

          {activeSection === "branches" && (
            <SeccionSedes setShowNewBranchModal={setShowNewBranchModal} canWrite={canWrite} setShowNewWarehouseModal={setShowNewWarehouseModal} branches={branches} showNewBranchModal={showNewBranchModal} handleCreateBranch={handleCreateBranch} newBranchCode={newBranchCode} setNewBranchCode={setNewBranchCode} inputClass={inputClass} newBranchName={newBranchName} setNewBranchName={setNewBranchName} newBranchTimezone={newBranchTimezone} setNewBranchTimezone={setNewBranchTimezone} savingBranch={savingBranch} showNewWarehouseModal={showNewWarehouseModal} handleCreateWarehouse={handleCreateWarehouse} newWarehouseBranchId={newWarehouseBranchId} setNewWarehouseBranchId={setNewWarehouseBranchId} newWarehouseCode={newWarehouseCode} setNewWarehouseCode={setNewWarehouseCode} newWarehouseName={newWarehouseName} setNewWarehouseName={setNewWarehouseName} savingWarehouse={savingWarehouse} warehousesByBranch={warehousesByBranch} reloadLocations={reloadLocations} />
          )}

          {activeSection === "numbering" && (
            <SeccionNumbering sequences={sequences} handleReserveSequence={handleReserveSequence} canWrite={canWrite} saving={saving} newSeriesCode={newSeriesCode} setNewSeriesCode={setNewSeriesCode} inputClass={inputClass} />
          )}

          {(activeSection === "profile" || (!section && activeSection === "rules")) && <OperatingProfileEditor canWrite={canWrite} />}
          {(activeSection === "functions" || (!section && activeSection === "rules")) && <FunctionSeparationEditor canWrite={canWrite} />}

          {(activeSection === "calendar" || (!section && activeSection === "rules")) && <OperatingCalendarEditor canWrite={canWrite} />}

          {activeSection === "rules" && (
            <SeccionReglas saveCommercialSettings={saveCommercialSettings} settings={settings} taxRate={taxRate} setTaxRate={setTaxRate} canWrite={canWrite} inputClass={inputClass} roundingMode={roundingMode} setRoundingMode={setRoundingMode} creditLimitStrict={creditLimitStrict} setCreditLimitStrict={setCreditLimitStrict} taxIncluded={taxIncluded} setTaxIncluded={setTaxIncluded} allowCreditSales={allowCreditSales} setAllowCreditSales={setAllowCreditSales} holdExpirationValue={holdExpirationValue} setHoldExpirationValue={setHoldExpirationValue} holdExpirationUnit={holdExpirationUnit} setHoldExpirationUnit={setHoldExpirationUnit} saving={saving} taxRules={taxRules} setRuleDraft={setRuleDraft} saveTaxRule={saveTaxRule} ruleDraft={ruleDraft} />
          )}

          {activeSection === "branding" && (
            <SeccionMarca saveBranding={saveBranding} brandingName={brandingName} setBrandingName={setBrandingName} canWrite={canWrite} inputClass={inputClass} logoUrl={logoUrl} setLogoUrl={setLogoUrl} footerText={footerText} setFooterText={setFooterText} saving={saving} company={company} />
          )}

          {activeSection === "appearance" && (
            <SeccionAppearance appearanceSaveState={appearanceSaveState} uiTheme={uiTheme} setUiTheme={setUiTheme} persistPreferences={persistPreferences} inputClass={inputClass} uiDensity={uiDensity} setUiDensity={setUiDensity} reducedMotion={reducedMotion} setReducedMotion={setReducedMotion} fontScale={fontScale} setFontScale={setFontScale} contrastMode={contrastMode} setContrastMode={setContrastMode} defaultPageSize={defaultPageSize} setDefaultPageSize={setDefaultPageSize} sidebarMode={sidebarMode} setSidebarMode={setSidebarMode} toastPosition={toastPosition} setSelectedToastPosition={setSelectedToastPosition} accessibleTables={accessibleTables} setAccessibleTables={setAccessibleTables} />
          )}
        </>
      )}
    </div>
  );
}
