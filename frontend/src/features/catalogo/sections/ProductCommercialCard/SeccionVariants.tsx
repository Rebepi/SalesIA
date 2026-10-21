import type { useProductCommercialCard } from "../../hooks/useProductCommercialCard";
import { Plus } from "lucide-react";
import { Props } from "../../types/ProductCommercialCard";
import { inputStyle } from "../../support/ProductCommercialCard";
import { btnPrimary } from "../../support/ProductCommercialCard";

export function SeccionVariants({ canWrite, handleAddVariant, productData }: { handleAddVariant: ReturnType<typeof useProductCommercialCard>["handleAddVariant"]; productData: NonNullable<ReturnType<typeof useProductCommercialCard>["productData"]> } & { canWrite: Props["canWrite"] }) {
  return (<div className="space-y-6">
    <p className="rounded-xl bg-teal-50 p-3 text-xs text-teal-800">Cada variante tiene un SKU operativo propio. Compra, reserva, vende y devuelve ese SKU para conservar sus existencias y costos por separado. El producto principal conserva sus existencias anteriores.</p>
    {canWrite && (
      <form onSubmit={handleAddVariant} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Crear nueva variante</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-5">
          <input name="sku" placeholder="SKU Variante" required className={inputStyle} />
          <input name="name" placeholder="Nombre (ej. Talla L / Rojo)" required className={inputStyle} />
          <input name="size" placeholder="Talla" className={inputStyle} />
          <input name="color" placeholder="Color" className={inputStyle} />
          <input name="price_delta" placeholder="Delta precio (+/-)" defaultValue="0.00" className={inputStyle} />
        </div>
        <div className="mt-3 flex justify-end">
          <button type="submit" className={btnPrimary}>
            <Plus className="h-4 w-4" /> Añadir variante
          </button>
        </div>
      </form>
    )}

    <div className="overflow-hidden rounded-xl border border-slate-200">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="p-3">SKU</th>
            <th className="p-3">Nombre</th>
            <th className="p-3">Atributos</th>
            <th className="p-3">Delta precio</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {productData.variants.length === 0 ? (
            <tr>
              <td colSpan={4} className="p-6 text-center text-slate-400">Sin variantes registradas</td>
            </tr>
          ) : (
            productData.variants.map((v, i) => (
              <tr key={String(v.id || i)}>
                <td className="p-3 font-mono font-medium">{String(v.sku)}</td>
                <td className="p-3">{String(v.name)}</td>
                <td className="p-3">{JSON.stringify(v.attributes)}</td>
                <td className="p-3 font-semibold text-slate-800">{String(v.price_delta)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  </div>);
}
