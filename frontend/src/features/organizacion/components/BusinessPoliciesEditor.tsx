import { SettingLabel, SettingSwitch, SettingsHelp } from "../../../ui/components/SettingsControls";
import { useEffect, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Tier = { minimum: string; percentage: string };
type Settings = {
  version: number;
  purchase_matching_policy?: { unit_price_tolerance_percentage: string; rounding_tolerance: string };
  pricing_policy: { default_volume_discounts_enabled: boolean; volume_tiers: { min_quantity: string; discount_percentage: string }[]; minimum_margin_percentage: string; maximum_manual_discount_percentage: string };
  commission_policy: { version: number; tiers: { minimum_attainment: string; rate: string }[] };
  supplier_performance_policy?: { history_days: number; minimum_samples: number; on_time_weight: string; fill_weight: string; acceptance_weight: string; invoice_weight: string };
  replenishment_policy: { default_lead_time_days: number; history_days: number };
};

export function BusinessPoliciesEditor({ canWrite }: { canWrite: boolean }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [volume, setVolume] = useState<Tier[]>([]);
  const [commission, setCommission] = useState<Tier[]>([]);
  const [enabled, setEnabled] = useState(true);
  const [leadDays, setLeadDays] = useState(7);
  const [historyDays, setHistoryDays] = useState(30);
  const [purchasePriceTolerance, setPurchasePriceTolerance] = useState("0");
  const [purchaseRounding, setPurchaseRounding] = useState("0.01");
  const [supplierPolicy, setSupplierPolicy] = useState({ history_days: "365", minimum_samples: "3", on_time_weight: "35", fill_weight: "25", acceptance_weight: "25", invoice_weight: "15" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const input = "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
  const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";

  function apply(value: Settings) {
    setSettings(value);
    setEnabled(value.pricing_policy.default_volume_discounts_enabled);
    setVolume(value.pricing_policy.volume_tiers.map(tier => ({ minimum: tier.min_quantity, percentage: String(Number((Number(tier.discount_percentage) * 100).toFixed(8))) })));
    setCommission(value.commission_policy.tiers.map(tier => ({ minimum: tier.minimum_attainment, percentage: String(Number((Number(tier.rate) * 100).toFixed(8))) })));
    setLeadDays(value.replenishment_policy.default_lead_time_days);
    setHistoryDays(value.replenishment_policy.history_days);
    setPurchasePriceTolerance(value.purchase_matching_policy?.unit_price_tolerance_percentage || "0");
    setPurchaseRounding(value.purchase_matching_policy?.rounding_tolerance || "0.01");
    if (value.supplier_performance_policy) { const policy = value.supplier_performance_policy; setSupplierPolicy({ history_days: String(policy.history_days), minimum_samples: String(policy.minimum_samples), on_time_weight: policy.on_time_weight, fill_weight: policy.fill_weight, acceptance_weight: policy.acceptance_weight, invoice_weight: policy.invoice_weight }); }
  }

  async function load() {
    setError("");
    try { apply(await apiClient.request<Settings>("/api/v1/companies/current/settings")); }
    catch (failure) { setError(String((failure as { detail?: string }).detail || "No se pudieron cargar las políticas.")); }
  }

  useEffect(() => { void load(); }, []);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!settings || saving || !canWrite) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const payload = {
        version: settings.version,
        pricing_policy: { ...settings.pricing_policy, default_volume_discounts_enabled: enabled, volume_tiers: volume.map(tier => ({ min_quantity: tier.minimum, discount_percentage: String(Number(tier.percentage) / 100) })) },
        commission_policy: { tiers: commission.map(tier => ({ minimum_attainment: tier.minimum, rate: String(Number(tier.percentage) / 100) })) },
        supplier_performance_policy: { ...supplierPolicy, history_days: Number(supplierPolicy.history_days), minimum_samples: Number(supplierPolicy.minimum_samples) },
        purchase_matching_policy: { unit_price_tolerance_percentage: purchasePriceTolerance, rounding_tolerance: purchaseRounding },
        replenishment_policy: { default_lead_time_days: leadDays, history_days: historyDays }
      };
      apply(await apiClient.request<Settings>("/api/v1/companies/current/settings", { method: "PATCH", body: JSON.stringify(payload) }));
      setNotice("Políticas guardadas. Las liquidaciones existentes conservan sus reglas originales.");
    } catch (failure) { setError(String((failure as { detail?: string }).detail || "No se pudieron guardar las políticas. Recarga si cambió la versión.")); }
    finally { setSaving(false); }
  }

  function tiersEditor(title: string, rows: Tier[], change: (rows: Tier[]) => void, minimumLabel: string) {
    return <fieldset disabled={!canWrite || saving} className="space-y-3 rounded-xl border border-slate-200 p-4">
      <legend className="px-2 font-semibold">{title}</legend><div className="settings-tier-help"><SettingsHelp title={title} description={minimumLabel === "Cantidad mínima" ? "Define los descuentos aplicables a partir de cada cantidad mínima. Los porcentajes se expresan entre 0 y 100." : "Define la comisión según el cumplimiento de meta. Incluye un tramo desde 0; las liquidaciones existentes conservan sus reglas originales."} /></div>
      {rows.map((tier, index) => <div key={index} className="grid grid-cols-[1fr_1fr_auto] items-end gap-2">
        <SettingLabel className="text-xs">{minimumLabel}<input className={input} type="number" required min="0" step="0.000001" value={tier.minimum} onChange={event => change(rows.map((row, position) => position === index ? { ...row, minimum: event.target.value } : row))} /></SettingLabel>
        <SettingLabel className="text-xs">Porcentaje<input className={input} type="number" required min="0" max="100" step="0.0001" value={tier.percentage} onChange={event => change(rows.map((row, position) => position === index ? { ...row, percentage: event.target.value } : row))} /></SettingLabel>
        <button type="button" className={button} aria-label={`Quitar tramo ${index + 1} de ${title}`} onClick={() => change(rows.filter((_, position) => position !== index))}>Quitar</button>
      </div>)}
      <button type="button" className={button} onClick={() => change([...rows, { minimum: "", percentage: "" }])}>Agregar tramo</button>
    </fieldset>;
  }

  return <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 text-slate-900 shadow-sm">
    <div className="flex items-center justify-between gap-3"><div className="settings-section-heading"><h2 className="text-lg font-semibold">Precios, comisiones y abastecimiento</h2><SettingsHelp title="Precios, comisiones y abastecimiento" description="Configura escalas generales, comisiones futuras, reposición, conciliación de compras y evaluación de proveedores. Guarda esta sección de forma independiente." /></div><button type="button" className={button} disabled={saving} onClick={() => void load()}>Recargar políticas</button></div>
    {error && <p role="alert" className="my-3 text-sm text-red-700">{error}</p>}
    {notice && <p role="status" className="my-3 text-sm text-teal-700">{notice}</p>}
    {!settings ? <p className="mt-3 text-sm">Las políticas se mostrarán al completar la carga.</p> : <form onSubmit={save} className="mt-4 space-y-5">
      <SettingSwitch label="Aplicar escalas generales cuando el producto no tenga escalas propias" description="Utiliza los tramos de descuento generales para productos sin escalas propias. Los productos con escalas propias conservan su configuración." checked={enabled} disabled={!canWrite || saving} onChange={event => setEnabled(event.target.checked)} />
      <div className="grid gap-4 xl:grid-cols-2">{tiersEditor("Descuento por volumen", volume, setVolume, "Cantidad mínima")}{tiersEditor(`Comisión por cumplimiento · versión ${settings.commission_policy.version}`, commission, setCommission, "Cumplimiento mínimo %")}</div>
      <section className="settings-policy-subsection space-y-4"><h3>Reposición y demanda</h3><div className="grid gap-4 sm:grid-cols-2">
        <SettingLabel className="text-sm">Plazo de reposición predeterminado en días<input className={input} required type="number" min="0" max="3650" disabled={!canWrite || saving} value={leadDays} onChange={event => setLeadDays(Number(event.target.value))} /></SettingLabel>
        <SettingLabel className="text-sm">Días de historia para demanda<input className={input} required type="number" min="1" max="1095" disabled={!canWrite || saving} value={historyDays} onChange={event => setHistoryDays(Number(event.target.value))} /></SettingLabel>
      </div>
      </section><fieldset disabled={!canWrite || saving} className="grid gap-3 rounded-xl border p-4 sm:grid-cols-2"><legend className="px-2 font-semibold">Conciliación de facturas de compra</legend><SettingLabel className="text-sm">Tolerancia de precio unitario %<input className={input} required type="number" min="0" max="25" step="0.000001" value={purchasePriceTolerance} onChange={event => setPurchasePriceTolerance(event.target.value)} /></SettingLabel><SettingLabel className="text-sm">Tolerancia de redondeo del total<input className={input} required type="number" min="0" max="1" step="0.000001" value={purchaseRounding} onChange={event => setPurchaseRounding(event.target.value)} /></SettingLabel><p className="text-xs text-slate-500 sm:col-span-2">Las diferencias de cantidad o impuesto requieren corregir la operación. La política queda guardada con cada conciliación.</p></fieldset>
      <fieldset disabled={!canWrite || saving} className="grid gap-3 rounded-xl border p-4 sm:grid-cols-3"><legend className="px-2 font-semibold">Desempeño de proveedores</legend>{([['history_days', 'Días de historia', 1, 3650], ['minimum_samples', 'Muestra mínima de líneas recibidas', 1, 1000], ['on_time_weight', 'Peso de puntualidad', 0, 100], ['fill_weight', 'Peso de cumplimiento de cantidad', 0, 100], ['acceptance_weight', 'Peso de aceptación', 0, 100], ['invoice_weight', 'Peso de facturación conforme', 0, 100]] as const).map(([field, label, minimum, maximum]) => <SettingLabel className="text-sm" key={field}>{label}<input className={input} required type="number" min={minimum} max={maximum} step={field === "history_days" || field === "minimum_samples" ? "1" : "0.0001"} value={supplierPolicy[field]} onChange={event => setSupplierPolicy(previous => ({ ...previous, [field]: event.target.value }))} /></SettingLabel>)}<p className="text-xs text-slate-500 sm:col-span-3">Los pesos se normalizan entre los indicadores con datos. La muestra insuficiente no recibe una puntuación global.</p></fieldset>
      <p className="text-xs text-slate-500">La comisión requiere un tramo desde cero. Las nuevas reglas se aplican a cálculos futuros.</p>
      <button type="submit" disabled={!canWrite || saving} className="rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Guardando…" : "Guardar estas políticas"}</button>
    </form>}
  </section>;
}
