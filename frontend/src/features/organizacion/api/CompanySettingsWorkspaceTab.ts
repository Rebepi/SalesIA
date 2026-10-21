import { type ToastPosition } from "../../../ui/toast/preferences";
import { apiClient } from "../../../api/client";
import { ThemeMode, DensityMode } from "../../../ui/tokens";
import { type ContrastMode, type FontScale, type SidebarMode } from "../../../ui/preferences";
import { Company } from "../types/CompanySettingsWorkspaceTab";
import { Branch } from "../types/CompanySettingsWorkspaceTab";
import { Warehouse } from "../types/CompanySettingsWorkspaceTab";
import { CompanySettings } from "../types/CompanySettingsWorkspaceTab";
import { Sequence } from "../types/CompanySettingsWorkspaceTab";
import { TaxRule } from "../types/CompanySettingsWorkspaceTab";

export function solicitarDatos() {
  return apiClient.request<Company>("/api/v1/companies/current");
}

export function solicitarDatos2() {
  return apiClient.request<CompanySettings>("/api/v1/companies/current/settings");
}

export function solicitarDatos3() {
  return apiClient.request<Branch[]>("/api/v1/branches");
}

export function solicitarDatos4() {
  return apiClient.request<Warehouse[]>("/api/v1/warehouses");
}

export function solicitarDatos5() {
  return apiClient.request<Sequence[]>("/api/v1/organization/sequences");
}

export function solicitarDatos6() {
  return apiClient.request<TaxRule[]>("/api/v1/organization/tax-rules");
}

export function solicitarDatos7() {
  return apiClient.request<{
    ui_theme?: ThemeMode;
    ui_density?: DensityMode;
    reduced_motion?: boolean;
    font_scale?: FontScale;
    contrast_mode?: ContrastMode;
    default_page_size?: number;
    sidebar_mode?: SidebarMode;
    accessible_tables?: boolean;
    toast_position?: ToastPosition;
  }>("/api/v1/auth/profile");
}

export function solicitarSaveCompany({ legalName, tradeName, baseCurrency }: { legalName: string; tradeName: string; baseCurrency: string }) {
  return apiClient.request<Company>("/api/v1/companies/current", {
    method: "PATCH",
    body: JSON.stringify({
      legal_name: legalName.trim(),
      trade_name: tradeName.trim(),
      base_currency: baseCurrency
    })
  });
}

export function solicitarSaveCommercialSettings({ settings, taxRate, roundingMode, creditLimitStrict, taxIncluded }: { settings: CompanySettings | null; taxRate: string; roundingMode: string; creditLimitStrict: boolean; taxIncluded: boolean }) {
  return apiClient.request<CompanySettings>("/api/v1/companies/current/settings", {
    method: "PATCH",
    body: JSON.stringify({
      version: settings?.version ?? 0,
      default_tax_rate: Number(taxRate),
      rounding_mode: roundingMode,
      credit_limit_strict: creditLimitStrict,
      tax_included_in_price: taxIncluded
    })
  });
}

export function solicitarSaveBranding({ settings, brandingName, logoUrl, footerText }: { settings: CompanySettings | null; brandingName: string; logoUrl: string; footerText: string }) {
  return apiClient.request<CompanySettings>("/api/v1/companies/current/settings", {
    method: "PATCH",
    body: JSON.stringify({
      version: settings?.version ?? 0,
      branding: {
        legal_name: brandingName.trim(),
        logo_url: logoUrl.trim(),
        footer_text: footerText.trim()
      }
    })
  });
}

export function solicitarHandleCreateBranch({ newBranchCode, newBranchName, newBranchTimezone }: { newBranchCode: string; newBranchName: string; newBranchTimezone: string }) {
  return apiClient.request<Branch>("/api/v1/branches", {
    method: "POST",
    body: JSON.stringify({
      code: newBranchCode.trim().toUpperCase(),
      name: newBranchName.trim(),
      timezone: newBranchTimezone
    })
  });
}

export function solicitarToggleBranchActive({ branch }: { branch: Branch }) {
  return apiClient.request<Branch>(`/api/v1/branches/${branch.branch_id}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: !branch.is_active })
  });
}

export function solicitarHandleCreateWarehouse({ newWarehouseBranchId, newWarehouseCode, newWarehouseName }: { newWarehouseBranchId: string; newWarehouseCode: string; newWarehouseName: string }) {
  return apiClient.request<Warehouse>("/api/v1/warehouses", {
    method: "POST",
    body: JSON.stringify({
      branch_id: newWarehouseBranchId,
      code: newWarehouseCode.trim().toUpperCase(),
      name: newWarehouseName.trim()
    })
  });
}

export function solicitarHandleReserveSequence({ cleanSeries }: { cleanSeries: string }) {
  return apiClient.request<{ series: string; assigned_number: number }>(
    `/api/v1/organization/sequences/reserve?series=${encodeURIComponent(cleanSeries)}`,
    { method: "POST" }
  );
}

export function solicitarSaveTaxRule({ ruleDraft }: { ruleDraft: TaxRule }) {
  return apiClient.request<TaxRule[]>("/api/v1/organization/tax-rules", {
    method: "POST",
    body: JSON.stringify({
      code: ruleDraft.code.trim().toUpperCase(),
      rate: Number(ruleDraft.rate),
      name: ruleDraft.name.trim(),
      is_active: ruleDraft.is_active
    })
  });
}

export function solicitarPersistPreferences({ changes }: { changes: Record<string, string | number | boolean> }) {
  return apiClient.request("/api/v1/auth/profile", {
    method: "PATCH",
    body: JSON.stringify({
      ...changes
    })
  });
}
