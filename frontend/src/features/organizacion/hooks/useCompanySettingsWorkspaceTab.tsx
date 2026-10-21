import * as transporte from "../api/CompanySettingsWorkspaceTab";
import { getToastPosition, setToastPosition, type ToastPosition } from "../../../ui/toast/preferences";
import { type FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { getStoredDensityPreference, getStoredThemePreference, resolveThemePreference, setStoredThemePreference, ThemeMode, DensityMode } from "../../../ui/tokens";
import { getStoredMotionPreference } from "../../../ui/motion";
import { getAccessibleTables, getContrastMode, getDefaultPageSize, getFontScale, getSidebarMode, setAccessibleTables as persistAccessibleTables, setContrastMode as persistContrastMode, setDefaultPageSize as persistDefaultPageSize, setFontScale as persistFontScale, setSidebarMode as persistSidebarMode, type ContrastMode, type FontScale, type SidebarMode } from "../../../ui/preferences";
import { CompanySettingsWorkspaceTabProps } from "../types/CompanySettingsWorkspaceTab";
import { Section } from "../types/CompanySettingsWorkspaceTab";
import { Company } from "../types/CompanySettingsWorkspaceTab";
import { Branch } from "../types/CompanySettingsWorkspaceTab";
import { Warehouse } from "../types/CompanySettingsWorkspaceTab";
import { CompanySettings } from "../types/CompanySettingsWorkspaceTab";
import { Sequence } from "../types/CompanySettingsWorkspaceTab";
import { TaxRule } from "../types/CompanySettingsWorkspaceTab";
import { errorMessage } from "../support/CompanySettingsWorkspaceTab";
import { DEFAULT_COMPANY } from "../support/CompanySettingsWorkspaceTab";
import { getHoldExpirationConfig, setHoldExpirationConfig, HoldExpirationUnit, getAllowCreditSalesConfig, setAllowCreditSalesConfig } from "../../ventas/support/posHoldSales";

export function useCompanySettingsWorkspaceTab({ canWrite = true }: CompanySettingsWorkspaceTabProps) {
  const [activeSection, setActiveSection] = useState<Section>("company");

  const [company, setCompany] = useState<Company | null>(null);

  const [settings, setSettings] = useState<CompanySettings | null>(null);

  const [branches, setBranches] = useState<Branch[]>([]);

  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);

  const [sequences, setSequences] = useState<Sequence[]>([]);

  const [taxRules, setTaxRules] = useState<TaxRule[]>([]);

  const [loading, setLoading] = useState(true);

  const [saving, setSaving] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [legalName, setLegalName] = useState(DEFAULT_COMPANY.legal_name);

  const [tradeName, setTradeName] = useState(DEFAULT_COMPANY.trade_name);

  const [baseCurrency, setBaseCurrency] = useState(DEFAULT_COMPANY.base_currency);

  const [taxRate, setTaxRate] = useState("0.18");

  const [roundingMode, setRoundingMode] = useState("ROUND_HALF_EVEN");

  const [creditLimitStrict, setCreditLimitStrict] = useState(true);

  const [taxIncluded, setTaxIncluded] = useState(false);
  const [allowCreditSales, setAllowCreditSales] = useState<boolean>(() => getAllowCreditSalesConfig());

  const [holdExpirationValue, setHoldExpirationValue] = useState<number>(() => getHoldExpirationConfig().value);

  const [holdExpirationUnit, setHoldExpirationUnit] = useState<HoldExpirationUnit>(() => getHoldExpirationConfig().unit);

  const [brandingName, setBrandingName] = useState(DEFAULT_COMPANY.legal_name);

  const [logoUrl, setLogoUrl] = useState("");

  const [footerText, setFooterText] = useState("");

  const [newSeriesCode, setNewSeriesCode] = useState("");

  const [ruleDraft, setRuleDraft] = useState<TaxRule>({ code: "", rate: "0.18", name: "", is_active: true });

  const [showNewBranchModal, setShowNewBranchModal] = useState(false);

  const [newBranchCode, setNewBranchCode] = useState("");

  const [newBranchName, setNewBranchName] = useState("");

  const [newBranchTimezone, setNewBranchTimezone] = useState("America/Lima");

  const [savingBranch, setSavingBranch] = useState(false);

  const [showNewWarehouseModal, setShowNewWarehouseModal] = useState(false);

  const [newWarehouseBranchId, setNewWarehouseBranchId] = useState("");

  const [newWarehouseCode, setNewWarehouseCode] = useState("");

  const [newWarehouseName, setNewWarehouseName] = useState("");

  const [savingWarehouse, setSavingWarehouse] = useState(false);

  const [toastPosition, setSelectedToastPosition] = useState<ToastPosition>(getToastPosition);

  const [uiTheme, setUiTheme] = useState<ThemeMode>(() => getStoredThemePreference());

  const [uiDensity, setUiDensity] = useState<DensityMode>(() => getStoredDensityPreference());

  const [reducedMotion, setReducedMotion] = useState(() => getStoredMotionPreference() === "reduced");

  const [accessibleTables, setAccessibleTables] = useState(getAccessibleTables);

  const [fontScale, setFontScale] = useState<FontScale>(getFontScale);

  const [contrastMode, setContrastMode] = useState<ContrastMode>(getContrastMode);

  const [defaultPageSize, setDefaultPageSize] = useState(getDefaultPageSize);

  const [sidebarMode, setSidebarMode] = useState<SidebarMode>(getSidebarMode);

  const [appearanceSaveState, setAppearanceSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const appearanceRequestVersion = useRef(0);

  const toast = useToast();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const results = await Promise.allSettled([
        transporte.solicitarDatos(),
        transporte.solicitarDatos2(),
        transporte.solicitarDatos3(),
        transporte.solicitarDatos4(),
        transporte.solicitarDatos5(),
        transporte.solicitarDatos6()
      ]);

      const [resComp, resSet, resBra, resWar, resSeq, resTax] = results;
      const failed = results.filter((result): result is PromiseRejectedResult => result.status === "rejected");
      if (failed.length) setError(`No se pudo cargar parte de la configuración: ${failed.map(result => errorMessage(result.reason)).join(" · ")}`);

      if (resComp.status === "fulfilled") {
        setCompany(resComp.value);
        setLegalName(resComp.value.legal_name || "");
        setTradeName(resComp.value.trade_name || "");
        setBaseCurrency(resComp.value.base_currency || "USD");
      }

      if (resSet.status === "fulfilled") {
        setSettings(resSet.value);
        setTaxRate(String(resSet.value.default_tax_rate ?? "0.18"));
        setRoundingMode(resSet.value.rounding_mode || "ROUND_HALF_EVEN");
        setCreditLimitStrict(Boolean(resSet.value.credit_limit_strict));
        setTaxIncluded(Boolean(resSet.value.tax_included_in_price));
        const initialBranding = resSet.value.branding?.legal_name || (resComp.status === "fulfilled" ? resComp.value.legal_name : "");
        setBrandingName(initialBranding || "");
        setLogoUrl(resSet.value.branding?.logo_url || "");
        setFooterText(resSet.value.branding?.footer_text || "");
      }

      if (resBra.status === "fulfilled") {
        setBranches(resBra.value);
        if (resBra.value.length > 0 && !newWarehouseBranchId) {
          setNewWarehouseBranchId(resBra.value[0].branch_id);
        }
      }

      if (resWar.status === "fulfilled") {
        setWarehouses(resWar.value);
      }

      if (resSeq.status === "fulfilled") {
        setSequences(resSeq.value);
      }

      if (resTax.status === "fulfilled") {
        setTaxRules(resTax.value);
      }

      try {
        const profile = await transporte.solicitarDatos7();
        const localTheme = resolveThemePreference(profile.ui_theme);
        const localDensity = getStoredDensityPreference();
        setUiTheme(localTheme);
        setUiDensity(localDensity || profile.ui_density || "comfortable");
        setReducedMotion(getStoredMotionPreference() === "reduced");
        if (typeof window !== "undefined") {
          if (window.localStorage.getItem("salesia_font_scale") === null && profile.font_scale) persistFontScale(profile.font_scale);
          if (window.localStorage.getItem("salesia_contrast_mode") === null && profile.contrast_mode) persistContrastMode(profile.contrast_mode);
          if (window.localStorage.getItem("salesia_default_page_size") === null && profile.default_page_size) persistDefaultPageSize(profile.default_page_size);
          if (window.localStorage.getItem("salesia_sidebar_mode") === null && profile.sidebar_mode) persistSidebarMode(profile.sidebar_mode);
          if (window.localStorage.getItem("salesia_accessible_tables") === null && profile.accessible_tables !== undefined) persistAccessibleTables(profile.accessible_tables);
          if (window.localStorage.getItem("salesia-toast-position") === null && profile.toast_position) setToastPosition(profile.toast_position);
        }
        setFontScale(getFontScale());
        setContrastMode(getContrastMode());
        setDefaultPageSize(getDefaultPageSize());
        setSidebarMode(getSidebarMode());
        setAccessibleTables(getAccessibleTables());
        setSelectedToastPosition(getToastPosition());
      } catch {
        if (typeof window !== "undefined" && window.localStorage) {
          const storedTheme = window.localStorage.getItem("salesia_theme_preference") as ThemeMode | null;
          if (storedTheme === "light" || storedTheme === "dark") {
            setUiTheme(storedTheme);
            setStoredThemePreference(storedTheme);
          }
          const storedDensity = window.localStorage.getItem("salesia_density_preference") as DensityMode | null;
          if (storedDensity === "comfortable" || storedDensity === "compact") setUiDensity(storedDensity);
        }
      }
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setLoading(false);
    }
  }, [newWarehouseBranchId]);

  useEffect(() => {
    void load();
  }, [load]);

  const warehousesByBranch = useMemo(() => {
    const grouped = new Map<string, Warehouse[]>();
    for (const warehouse of warehouses) {
      grouped.set(warehouse.branch_id, [...(grouped.get(warehouse.branch_id) || []), warehouse]);
    }
    return grouped;
  }, [warehouses]);

  const saveCompany = async (event: FormEvent) => {
    event.preventDefault();
    if (!canWrite || saving || !company) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await transporte.solicitarSaveCompany({ legalName, tradeName, baseCurrency });
      setCompany(updated);
      toast.success("Empresa actualizada", "Los datos fiscales y comerciales se guardaron correctamente.");
    } catch (failure) {
      const message = errorMessage(failure);
      setError(message);
      toast.error("No se pudo actualizar la empresa", message);
    } finally {
      setSaving(false);
    }
  };

  const saveCommercialSettings = async (event: FormEvent) => {
    event.preventDefault();
    if (!canWrite || saving || !company) return;
    setSaving(true);
    setError(null);
    try {
      setHoldExpirationConfig({
        value: Math.max(1, Number(holdExpirationValue) || 1),
        unit: holdExpirationUnit
      });
      setAllowCreditSalesConfig(allowCreditSales);
      const updated = await transporte.solicitarSaveCommercialSettings({ settings, taxRate, roundingMode, creditLimitStrict, taxIncluded });
      setSettings(updated);
      toast.success("Políticas guardadas", `Se actualizó la configuración comercial (versión ${updated.version}).`);
    } catch (failure) {
      const message = errorMessage(failure);
      setError(message);
      toast.error("No se pudo guardar la configuración", message);
    } finally {
      setSaving(false);
    }
  };

  const saveBranding = async (event: FormEvent) => {
    event.preventDefault();
    if (!canWrite || saving || !company) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await transporte.solicitarSaveBranding({ settings, brandingName, logoUrl, footerText });
      setSettings(updated);
      toast.success("Marca guardada", "La identidad gráfica y pie documental fueron actualizados.");
    } catch (failure) {
      const message = errorMessage(failure);
      setError(message);
      toast.error("No se pudo guardar la marca", message);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateBranch = async (event: FormEvent) => {
    event.preventDefault();
    if (!canWrite || !newBranchCode.trim() || !newBranchName.trim()) return;
    setSavingBranch(true);
    try {
      const created = await transporte.solicitarHandleCreateBranch({ newBranchCode, newBranchName, newBranchTimezone });
      setBranches(prev => [...prev, created]);
      setNewBranchCode("");
      setNewBranchName("");
      setShowNewBranchModal(false);
      toast.success("Sucursal creada", `Sede ${created.name} (${created.code}) registrada.`);
    } catch (failure) {
      toast.error("Error al crear sucursal", errorMessage(failure));
    } finally {
      setSavingBranch(false);
    }
  };

  const handleCreateWarehouse = async (event: FormEvent) => {
    event.preventDefault();
    if (!canWrite || !newWarehouseBranchId || !newWarehouseCode.trim() || !newWarehouseName.trim()) return;
    setSavingWarehouse(true);
    try {
      const created = await transporte.solicitarHandleCreateWarehouse({ newWarehouseBranchId, newWarehouseCode, newWarehouseName });
      setWarehouses(prev => [...prev, created]);
      setNewWarehouseCode("");
      setNewWarehouseName("");
      setShowNewWarehouseModal(false);
      toast.success("Almacén creado", `Almacén ${created.name} (${created.code}) registrado.`);
    } catch (failure) {
      toast.error("Error al crear almacén", errorMessage(failure));
    } finally {
      setSavingWarehouse(false);
    }
  };

  const handleReserveSequence = async (seriesCode: string) => {
    if (!canWrite || !seriesCode.trim()) return;
    setSaving(true);
    try {
      const cleanSeries = seriesCode.trim().toUpperCase();
      const reserved = await transporte.solicitarHandleReserveSequence({ cleanSeries });
      setSequences(current => {
        const found = current.some(item => item.series === reserved.series);
        return found
          ? current.map(item => item.series === reserved.series ? { ...item, value: reserved.assigned_number } : item)
          : [...current, { series: reserved.series, value: reserved.assigned_number }];
      });
      setNewSeriesCode("");
      toast.success("Correlativo reservado", `${reserved.series}-${String(reserved.assigned_number).padStart(8, "0")}`);
    } catch (failure) {
      toast.error("No se pudo reservar el correlativo", errorMessage(failure));
    } finally {
      setSaving(false);
    }
  };

  const saveTaxRule = async (event: FormEvent) => {
    event.preventDefault();
    if (!canWrite || !ruleDraft.code.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await transporte.solicitarSaveTaxRule({ ruleDraft });
      setTaxRules(updated);
      setRuleDraft({ code: "", rate: "0.18", name: "", is_active: true });
      toast.success("Regla fiscal guardada", "La regla tributaria fue registrada correctamente.");
    } catch (failure) {
      const message = errorMessage(failure);
      setError(message);
      toast.error("No se pudo guardar la regla", message);
    } finally {
      setSaving(false);
    }
  };

  const persistPreferences = async (changes: Record<string, string | number | boolean>) => {
    const requestVersion = ++appearanceRequestVersion.current;
    setAppearanceSaveState("saving");
    try {
      await transporte.solicitarPersistPreferences({ changes });
      if (requestVersion === appearanceRequestVersion.current) setAppearanceSaveState("saved");
    } catch (failure) {
      if (requestVersion === appearanceRequestVersion.current) setAppearanceSaveState("error");
      toast.error("No se pudo guardar la apariencia", errorMessage(failure));
    }
  };

  const tabs: Array<{ key: Section; label: string }> = [
    { key: "company", label: "Empresa" },
    { key: "branches", label: "Sucursales y Almacenes" },
    { key: "numbering", label: "Series y Correlativos" },
    { key: "rules", label: "Políticas y Fiscal" },
    { key: "branding", label: "Marca e Impresión" },
    { key: "appearance", label: "Apariencia" }
  ];

  const inputClass = "mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-100 disabled:bg-slate-100 disabled:text-slate-500";
  return { activeSection, setActiveSection, company, settings, branches, sequences, taxRules, loading, saving, error, legalName, setLegalName, tradeName, setTradeName, baseCurrency, setBaseCurrency, taxRate, setTaxRate, roundingMode, setRoundingMode, creditLimitStrict, setCreditLimitStrict, taxIncluded, setTaxIncluded, allowCreditSales, setAllowCreditSales, holdExpirationValue, setHoldExpirationValue, holdExpirationUnit, setHoldExpirationUnit, brandingName, setBrandingName, logoUrl, setLogoUrl, footerText, setFooterText, newSeriesCode, setNewSeriesCode, ruleDraft, setRuleDraft, showNewBranchModal, setShowNewBranchModal, newBranchCode, setNewBranchCode, newBranchName, setNewBranchName, newBranchTimezone, setNewBranchTimezone, savingBranch, showNewWarehouseModal, setShowNewWarehouseModal, newWarehouseBranchId, setNewWarehouseBranchId, newWarehouseCode, setNewWarehouseCode, newWarehouseName, setNewWarehouseName, savingWarehouse, toastPosition, setSelectedToastPosition, uiTheme, setUiTheme, uiDensity, setUiDensity, reducedMotion, setReducedMotion, accessibleTables, setAccessibleTables, fontScale, setFontScale, contrastMode, setContrastMode, defaultPageSize, setDefaultPageSize, sidebarMode, setSidebarMode, appearanceSaveState, warehousesByBranch, saveCompany, saveCommercialSettings, saveBranding, handleCreateBranch, reloadLocations: load, handleCreateWarehouse, handleReserveSequence, saveTaxRule, persistPreferences, tabs, inputClass };
}
