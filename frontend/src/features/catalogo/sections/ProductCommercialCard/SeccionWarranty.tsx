import type { useProductCommercialCard } from "../../hooks/useProductCommercialCard";
import { Shield } from "lucide-react";
import { RemoteEntitySelect } from "../../../../ui/components/RemoteEntitySelect";
import { SaleChoice } from "../../types/ProductCommercialCard";
import { Props } from "../../types/ProductCommercialCard";
import { saleOption } from "../../support/ProductCommercialCard";
import { inputStyle } from "../../support/ProductCommercialCard";
import { btnPrimary } from "../../support/ProductCommercialCard";

export function SeccionWarranty({ productData, canWrite, handleAddWarrantyClaim, warrantySale, setWarrantySale, productId }: { productData: NonNullable<ReturnType<typeof useProductCommercialCard>["productData"]>; handleAddWarrantyClaim: ReturnType<typeof useProductCommercialCard>["handleAddWarrantyClaim"]; warrantySale: ReturnType<typeof useProductCommercialCard>["warrantySale"]; setWarrantySale: ReturnType<typeof useProductCommercialCard>["setWarrantySale"] } & { canWrite: Props["canWrite"]; productId: Props["productId"] }) {
  return (<div className="space-y-6">
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Cobertura de garantía de fábrica</h4>
      <p className="mt-1 text-xs text-slate-500">
        Meses de cobertura: <strong className="text-slate-800">{String(productData.profile?.default_warranty_months || 0)} meses</strong>. Los cambios de póliza conservan los meses contratados en ventas previas (CAT-021).
      </p>
    </div>

    {canWrite && (
      <form onSubmit={handleAddWarrantyClaim} className="rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Registrar reclamo de garantía o servicio</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <input name="serial_number" placeholder="Número de serie del equipo" required className={inputStyle} />
          <RemoteEntitySelect<SaleChoice> name="sale_id" value={warrantySale?.sale_id || ""} onChange={(_, option) => setWarrantySale(option?.data)} endpoint={`/api/v1/products/${productId}/eligible-warranty-sales`} entityType="sale" mapOption={saleOption} initialOption={warrantySale ? saleOption(warrantySale) : undefined} label="Compra elegible" placeholder="Buscar por comprobante o cliente" required />
        </div>
        <div className="mt-3">
          <textarea name="description" placeholder="Descripción del reclamo o defecto" required rows={2} className={inputStyle} />
        </div>
        <div className="mt-3 flex justify-end">
          <button type="submit" className={btnPrimary}>
            <Shield className="h-4 w-4" /> Registrar reclamo
          </button>
        </div>
      </form>
    )}

    <div className="overflow-hidden rounded-xl border border-slate-200">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="p-3">Serie</th>
            <th className="p-3">Descripción</th>
            <th className="p-3">Estado</th>
            <th className="p-3">Fecha</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {productData.warranty_claims.length === 0 ? (
            <tr>
              <td colSpan={4} className="p-6 text-center text-slate-400">Sin reclamos registrados</td>
            </tr>
          ) : (
            productData.warranty_claims.map((claim, i) => (
              <tr key={String(claim.id || i)}>
                <td className="p-3 font-mono font-medium">{String(claim.serial_number)}</td>
                <td className="p-3">{String(claim.description)}</td>
                <td className="p-3"><span className="rounded bg-amber-50 px-2 py-0.5 font-semibold text-amber-800">{String(claim.status)}</span></td>
                <td className="p-3 text-slate-400">{String(claim.created_at)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  </div>);
}
