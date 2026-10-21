import type { useProductCommercialCard } from "../../hooks/useProductCommercialCard";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Package, Upload } from "lucide-react";
import { Props } from "../../types/ProductCommercialCard";
import { inputStyle } from "../../support/ProductCommercialCard";
import { btnPrimary } from "../../support/ProductCommercialCard";

export function SeccionAdjuntos({ canWrite, handleAddAttachment, productData }: { handleAddAttachment: ReturnType<typeof useProductCommercialCard>["handleAddAttachment"]; productData: NonNullable<ReturnType<typeof useProductCommercialCard>["productData"]> } & { canWrite: Props["canWrite"] }) {
  return (<div className="space-y-6">
    {canWrite && (
      <form onSubmit={handleAddAttachment} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Adjuntar imagen o documento</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <input name="file_url" placeholder="URL de la imagen o documento" required className={inputStyle} />
          <input name="file_name" placeholder="Nombre descriptivo" required className={inputStyle} />
          <CustomSelect name="is_primary" defaultValue="false" className={inputStyle}>
            <option value="false">Secundaria</option>
            <option value="true">Imagen Principal</option>
          </CustomSelect>
        </div>
        <div className="mt-3 flex justify-end">
          <button type="submit" className={btnPrimary}>
            <Upload className="h-4 w-4" /> Adjuntar archivo
          </button>
        </div>
      </form>
    )}

    <div className="grid gap-4 sm:grid-cols-3">
      {productData.attachments.length === 0 ? (
        <div className="col-span-3 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 p-8 text-center">
          <Package className="h-10 w-10 text-slate-300" />
          <p className="mt-2 text-xs text-slate-400">Sin imágenes registradas. Se utiliza imagen de respaldo predeterminada.</p>
        </div>
      ) : (
        productData.attachments.map((att, i) => (
          <div key={String(att.id || i)} className="overflow-hidden rounded-xl border border-slate-200 bg-white p-3">
            <img
              src={String(att.file_url)}
              alt={String(att.file_name)}
              onError={e => {
                (e.target as HTMLImageElement).src = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300";
              }}
              className="h-32 w-full rounded-lg object-cover"
            />
            <p className="mt-2 truncate text-xs font-semibold text-slate-800">{String(att.file_name)}</p>
            <p className="text-[10px] text-slate-400">{att.is_primary ? "Principal" : "Secundario"}</p>
          </div>
        ))
      )}
    </div>
  </div>);
}
