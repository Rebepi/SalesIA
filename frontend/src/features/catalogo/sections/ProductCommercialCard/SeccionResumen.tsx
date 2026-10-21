import type { useProductCommercialCard } from "../../hooks/useProductCommercialCard";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Props } from "../../types/ProductCommercialCard";
import { inputStyle } from "../../support/ProductCommercialCard";
import { btnPrimary } from "../../support/ProductCommercialCard";

export function SeccionResumen({ handleUpdateProfile, productData, canWrite }: { handleUpdateProfile: ReturnType<typeof useProductCommercialCard>["handleUpdateProfile"]; productData: NonNullable<ReturnType<typeof useProductCommercialCard>["productData"]> } & { canWrite: Props["canWrite"] }) {
  return (<div className="grid gap-6 md:grid-cols-2">
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-900">Configuración operativa</h3>
      <form onSubmit={handleUpdateProfile} className="space-y-4">
        <div>
          <label className="text-xs font-medium text-slate-600">Tipo de producto</label>
          <CustomSelect
            name="product_type"
            defaultValue={String(productData.profile?.product_type || "product")}
            disabled={!canWrite}
            className={inputStyle}
          >
            <option value="product">Producto físico</option>
            <option value="service">Servicio (sin stock físico)</option>
            <option value="kit">Kit / Combo compuesto</option>
          </CustomSelect>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">Seguimiento de existencias</label>
          <CustomSelect
            name="track_inventory"
            defaultValue={String(productData.profile?.track_inventory !== false)}
            disabled={!canWrite}
            className={inputStyle}
          >
            <option value="true">Sí, controlar existencias e inventario</option>
            <option value="false">No, exento de control de inventario</option>
          </CustomSelect>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">Permitir cantidades fraccionarias</label>
          <CustomSelect
            name="allow_fractional"
            defaultValue={String(productData.profile?.allow_fractional || false)}
            disabled={!canWrite}
            className={inputStyle}
          >
            <option value="false">No (solo enteros)</option>
            <option value="true">Sí (fracciones decimales autorizadas)</option>
          </CustomSelect>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">Garantía comercial predeterminada (meses)</label>
          <input
            type="number"
            name="default_warranty_months"
            defaultValue={String(productData.profile?.default_warranty_months || 0)}
            disabled={!canWrite}
            className={inputStyle}
          />
        </div>
        {canWrite && (
          <button type="submit" className={btnPrimary}>
            Guardar configuración
          </button>
        )}
      </form>
    </div>

    <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-5">
      <h3 className="font-semibold text-slate-900">Resumen y estado</h3>
      <dl className="grid grid-cols-2 gap-4 text-xs">
        <div>
          <dt className="text-slate-500">Precio base</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">${String(productData.product.unit_price)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Costo base (restringido)</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">
            {productData.product.unit_cost !== null && productData.product.unit_cost !== undefined ? `$${String(productData.product.unit_cost)}` : "Oculto por política"}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Impuesto (IGV/IVA)</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">{Number(productData.product.tax_rate) * 100}%</dd>
        </div>
        <div>
          <dt className="text-slate-500">Categoría</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">{String(productData.product.category || "General")}</dd>
        </div>
      </dl>
    </div>
  </div>);
}
