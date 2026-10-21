import type { useProductCommercialCard } from "../../hooks/useProductCommercialCard";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Calculator, Plus } from "lucide-react";
import { Row } from "../../types/ProductCommercialCard";
import { Props } from "../../types/ProductCommercialCard";
import { inputStyle } from "../../support/ProductCommercialCard";
import { btnPrimary } from "../../support/ProductCommercialCard";

export function SeccionPricing({ previewQty, setPreviewQty, previewCurrency, setPreviewCurrency, handleRunPricePreview, previewLoading, previewResult, canWrite, handleAddVolumeTier, productData }: { previewQty: ReturnType<typeof useProductCommercialCard>["previewQty"]; setPreviewQty: ReturnType<typeof useProductCommercialCard>["setPreviewQty"]; previewCurrency: ReturnType<typeof useProductCommercialCard>["previewCurrency"]; setPreviewCurrency: ReturnType<typeof useProductCommercialCard>["setPreviewCurrency"]; handleRunPricePreview: ReturnType<typeof useProductCommercialCard>["handleRunPricePreview"]; previewLoading: ReturnType<typeof useProductCommercialCard>["previewLoading"]; previewResult: ReturnType<typeof useProductCommercialCard>["previewResult"]; handleAddVolumeTier: ReturnType<typeof useProductCommercialCard>["handleAddVolumeTier"]; productData: NonNullable<ReturnType<typeof useProductCommercialCard>["productData"]> } & { canWrite: Props["canWrite"] }) {
  return (<div className="space-y-6">
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-900">Simulación y previsualización de precios (API-028)</h3>
      <p className="text-xs text-slate-500">Calcula deterministamente el precio considerando listas, escalas de volumen, promociones e impuestos.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <label className="text-xs font-medium text-slate-600">Cantidad</label>
          <input
            type="number"
            value={previewQty}
            onChange={e => setPreviewQty(e.target.value)}
            min="1"
            className={inputStyle}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">Moneda</label>
          <CustomSelect
            value={previewCurrency}
            onChange={e => setPreviewCurrency(e.target.value)}
            className={inputStyle}
          >
            <option value="USD">USD - Dólares</option>
            <option value="PEN">PEN - Soles</option>
          </CustomSelect>
        </div>
        <div className="flex items-end">
          <button
            onClick={handleRunPricePreview}
            disabled={previewLoading}
            className={btnPrimary}
          >
            <Calculator className="h-4 w-4" />
            {previewLoading ? "Calculando..." : "Simular precio"}
          </button>
        </div>
      </div>

      {previewResult && (
        <div className="mt-5 rounded-xl border border-teal-200 bg-teal-50/50 p-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-teal-800">Resultado de la simulación</h4>
          <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4 text-xs">
            <div>
              <span className="text-slate-500">Subtotal base</span>
              <p className="text-sm font-semibold">${String(previewResult.subtotal)}</p>
            </div>
            <div>
              <span className="text-slate-500">Descuento aplicado</span>
              <p className="text-sm font-semibold text-rose-600">-${String(previewResult.discount_total)}</p>
            </div>
            <div>
              <span className="text-slate-500">Impuestos</span>
              <p className="text-sm font-semibold">${String(previewResult.tax_total)}</p>
            </div>
            <div>
              <span className="text-slate-500">Total liquidado</span>
              <p className="text-base font-bold text-teal-800">${String(previewResult.total)}</p>
            </div>
          </div>
          {Array.isArray(previewResult.lines) && (previewResult.lines[0] as Row)?.rules_applied && (
            <div className="mt-3 rounded bg-white p-3 text-xs text-slate-600">
              <span className="font-semibold text-slate-700">Reglas explicadas:</span>
              <ul className="mt-1 list-disc pl-4">
                {(((previewResult.lines[0] as Row).rules_applied as unknown) as string[]).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>

    <div className="space-y-4">
      <h3 className="font-semibold text-slate-900">Escalas de precio por volumen (CAT-020)</h3>
      {canWrite && (
        <form onSubmit={handleAddVolumeTier} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Agregar escala de volumen</h4>
          <div className="mt-3 grid gap-3 sm:grid-cols-4">
            <input name="min_quantity" type="number" placeholder="Mínimo (ej. 10)" required className={inputStyle} />
            <input name="max_quantity" type="number" placeholder="Máximo (opcional)" className={inputStyle} />
            <input name="unit_price" placeholder="Precio unitario" className={inputStyle} />
            <input name="discount_percent" placeholder="% Descuento (ej. 0.15)" className={inputStyle} />
          </div>
          <div className="mt-3 flex justify-end">
            <button type="submit" className={btnPrimary}>
              <Plus className="h-4 w-4" /> Agregar escala
            </button>
          </div>
        </form>
      )}
      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="p-3">Cantidad mínima</th>
              <th className="p-3">Cantidad máxima</th>
              <th className="p-3">Precio fijado</th>
              <th className="p-3">% Descuento</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {productData.volume_tiers.length === 0 ? (
              <tr>
                <td colSpan={4} className="p-6 text-center text-slate-400">Sin escalas por volumen configuradas</td>
              </tr>
            ) : (
              productData.volume_tiers.map((vt, i) => (
                <tr key={String(vt.id || i)}>
                  <td className="p-3 font-semibold">{String(vt.min_quantity)}</td>
                  <td className="p-3">{vt.max_quantity ? String(vt.max_quantity) : "Sin límite"}</td>
                  <td className="p-3">{vt.unit_price ? `$${String(vt.unit_price)}` : "—"}</td>
                  <td className="p-3">{vt.discount_percent ? `${Number(vt.discount_percent) * 100}%` : "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  </div>);
}
