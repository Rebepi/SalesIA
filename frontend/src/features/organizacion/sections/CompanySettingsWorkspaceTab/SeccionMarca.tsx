import type { useCompanySettingsWorkspaceTab } from "../../hooks/useCompanySettingsWorkspaceTab";
import { Eye, Loader2, Save } from "lucide-react";
import { CompanySettingsWorkspaceTabProps } from "../../types/CompanySettingsWorkspaceTab";

export function SeccionMarca({ saveBranding, brandingName, setBrandingName, canWrite, inputClass, logoUrl, setLogoUrl, footerText, setFooterText, saving, company }: { saveBranding: ReturnType<typeof useCompanySettingsWorkspaceTab>["saveBranding"]; brandingName: ReturnType<typeof useCompanySettingsWorkspaceTab>["brandingName"]; setBrandingName: ReturnType<typeof useCompanySettingsWorkspaceTab>["setBrandingName"]; inputClass: ReturnType<typeof useCompanySettingsWorkspaceTab>["inputClass"]; logoUrl: ReturnType<typeof useCompanySettingsWorkspaceTab>["logoUrl"]; setLogoUrl: ReturnType<typeof useCompanySettingsWorkspaceTab>["setLogoUrl"]; footerText: ReturnType<typeof useCompanySettingsWorkspaceTab>["footerText"]; setFooterText: ReturnType<typeof useCompanySettingsWorkspaceTab>["setFooterText"]; saving: ReturnType<typeof useCompanySettingsWorkspaceTab>["saving"]; company: ReturnType<typeof useCompanySettingsWorkspaceTab>["company"] } & { canWrite: NonNullable<CompanySettingsWorkspaceTabProps["canWrite"]> }) {
  return (<div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
    <form onSubmit={saveBranding} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
      <div className="border-b border-slate-100 pb-4">
        <h2 className="font-bold text-slate-900">Identidad Gráfica y Documental</h2>
        <p className="text-xs text-slate-500">Parámetros impresos en cotizaciones, comprobantes y reportes.</p>
      </div>

      <div className="grid gap-4">
        <label className="text-xs font-semibold text-slate-700">
          Nombre Mostrado en Cabecera
          <input
            maxLength={128}
            value={brandingName}
            onChange={event => setBrandingName(event.target.value)}
            disabled={!canWrite}
            placeholder="Distribuidora Mayorista Lima S.A.C."
            className={inputClass}
          />
        </label>

        <label className="text-xs font-semibold text-slate-700">
          URL del Logotipo Institucional
          <input
            type="url"
            maxLength={512}
            value={logoUrl}
            onChange={event => setLogoUrl(event.target.value)}
            disabled={!canWrite}
            placeholder="https://ejemplo.com/logo.png"
            className={inputClass}
          />
          <span className="mt-1 block text-[11px] text-slate-400">URL pública accesible con formato PNG o SVG.</span>
        </label>

        <label className="text-xs font-semibold text-slate-700">
          Pie de Página Documental
          <textarea
            maxLength={255}
            rows={3}
            value={footerText}
            onChange={event => setFooterText(event.target.value)}
            disabled={!canWrite}
            placeholder="Gracias por confiar en nuestros productos. Para consultas contáctenos a soporte@empresa.com"
            className={inputClass}
          />
        </label>
      </div>

      <div className="flex justify-end border-t border-slate-100 pt-4">
        <button
          type="submit"
          disabled={!canWrite || saving}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Guardar marca
        </button>
      </div>
    </form>

    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <Eye className="h-4 w-4 text-teal-700" />
        <h3 className="font-bold text-slate-900">Vista Previa de Impresión</h3>
      </div>

      <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 space-y-6 text-slate-800">
        <div className="flex items-start justify-between border-b border-slate-200 pb-4">
          <div>
            {logoUrl ? (
              <img
                src={logoUrl}
                alt="Logotipo"
                className="h-10 max-w-[160px] object-contain mb-2"
                onError={(e) => { (e.currentTarget as HTMLElement).style.display = "none"; }}
              />
            ) : (
              <div className="flex h-10 w-28 items-center justify-center rounded border border-dashed border-slate-300 bg-white text-[11px] text-slate-400 mb-2">
                Sin logotipo
              </div>
            )}
            <h4 className="font-bold text-sm text-slate-900">{brandingName || company?.legal_name || "Nombre de Empresa"}</h4>
            <p className="text-[11px] text-slate-500">RUC: {company?.tax_id || "20000000000"}</p>
          </div>
          <div className="text-right">
            <span className="rounded bg-teal-100 px-2 py-0.5 font-mono text-xs font-bold text-teal-800">
              COTIZACIÓN
            </span>
            <p className="font-mono text-xs text-slate-600 mt-1">F001-00000001</p>
          </div>
        </div>

        <div className="space-y-2 py-2">
          <div className="h-2 w-3/4 rounded bg-slate-200" />
          <div className="h-2 w-1/2 rounded bg-slate-200" />
        </div>

        <div className="border-t border-slate-200 pt-4 text-center">
          <p className="text-xs text-slate-500 italic">
            {footerText || "Gracias por su preferencia."}
          </p>
        </div>
      </div>
    </div>
  </div>);
}
