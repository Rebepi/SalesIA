import type { useProductCommercialCard } from "../../hooks/useProductCommercialCard";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Plus } from "lucide-react";
import { Props } from "../../types/ProductCommercialCard";
import { inputStyle } from "../../support/ProductCommercialCard";
import { btnPrimary } from "../../support/ProductCommercialCard";

export function SeccionBarcodes({ scannerCode, setScannerCode, handleLookupBarcode, scannerResult, canWrite, handleAddBarcode, productData }: { scannerCode: ReturnType<typeof useProductCommercialCard>["scannerCode"]; setScannerCode: ReturnType<typeof useProductCommercialCard>["setScannerCode"]; handleLookupBarcode: ReturnType<typeof useProductCommercialCard>["handleLookupBarcode"]; scannerResult: ReturnType<typeof useProductCommercialCard>["scannerResult"]; handleAddBarcode: ReturnType<typeof useProductCommercialCard>["handleAddBarcode"]; productData: NonNullable<ReturnType<typeof useProductCommercialCard>["productData"]> } & { canWrite: Props["canWrite"] }) {
  return (<div className="space-y-6">
    <div className="rounded-xl border border-teal-200 bg-teal-50 p-4">
      <h4 className="text-xs font-bold uppercase tracking-wider text-teal-800">Simulación de lectura y escáner manual</h4>
      <div className="mt-2 flex gap-2">
        <input
          placeholder="Código de barras a escanear"
          value={scannerCode}
          onChange={e => setScannerCode(e.target.value)}
          className={inputStyle}
        />
        <button onClick={handleLookupBarcode} className={btnPrimary}>
          Escanear
        </button>
      </div>
      {scannerResult && (
        <div className="mt-3 rounded-lg bg-white p-3 text-xs text-slate-800 shadow-sm">
          <p className="font-semibold text-teal-800">Código reconocido: {String(scannerResult.barcode)}</p>
          <p>Producto: {String(scannerResult.product_name)} (SKU: {String(scannerResult.sku)})</p>
        </div>
      )}
    </div>

    {canWrite && (
      <form onSubmit={handleAddBarcode} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Registrar nuevo código de barras</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <input name="barcode" placeholder="Código (ej. 7751234567890)" required className={inputStyle} />
          <CustomSelect name="symbology" defaultValue="EAN13" className={inputStyle}>
            <option value="EAN13">EAN-13</option>
            <option value="UPC">UPC-A</option>
            <option value="CODE128">Code 128</option>
          </CustomSelect>
          <CustomSelect name="is_primary" defaultValue="false" className={inputStyle}>
            <option value="false">Secundario</option>
            <option value="true">Principal</option>
          </CustomSelect>
        </div>
        <div className="mt-3 flex justify-end">
          <button type="submit" className={btnPrimary}>
            <Plus className="h-4 w-4" /> Añadir código
          </button>
        </div>
      </form>
    )}

    <div className="overflow-hidden rounded-xl border border-slate-200">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="p-3">Código</th>
            <th className="p-3">Simbología</th>
            <th className="p-3">Principal</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {productData.barcodes.length === 0 ? (
            <tr>
              <td colSpan={3} className="p-6 text-center text-slate-400">Sin códigos de barras asociados</td>
            </tr>
          ) : (
            productData.barcodes.map((b, i) => (
              <tr key={String(b.id || i)}>
                <td className="p-3 font-mono font-bold">{String(b.barcode)}</td>
                <td className="p-3">{String(b.barcode_type)}</td>
                <td className="p-3">{b.is_primary ? "Sí" : "No"}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  </div>);
}
