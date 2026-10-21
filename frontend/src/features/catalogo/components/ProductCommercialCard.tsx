import { SeccionResumen } from "../sections/ProductCommercialCard/SeccionResumen";
import { SeccionVariants } from "../sections/ProductCommercialCard/SeccionVariants";
import { SeccionBarcodes } from "../sections/ProductCommercialCard/SeccionBarcodes";
import { SeccionPricing } from "../sections/ProductCommercialCard/SeccionPricing";
import { SeccionKits } from "../sections/ProductCommercialCard/SeccionKits";
import { SeccionWarranty } from "../sections/ProductCommercialCard/SeccionWarranty";
import { SeccionAdjuntos } from "../sections/ProductCommercialCard/SeccionAdjuntos";
import { useProductCommercialCard } from "../hooks/useProductCommercialCard";
import { Archive, ArchiveRestore, Barcode, Box, Calculator, Copy, Layers, Package, Shield, Upload, X } from "lucide-react";
import { Props } from "../types/ProductCommercialCard";
import { Tab } from "../types/ProductCommercialCard";

export function ProductCommercialCard({ productId, productName, canWrite, allProducts, onClose, onRefresh }: Props) {
  const { PromptDialogNode, tab, setTab, loading, error, productData, previewQty, setPreviewQty, previewCurrency, setPreviewCurrency, previewResult, previewLoading, scannerCode, setScannerCode, scannerResult, warrantySale, setWarrantySale, handleUpdateProfile, handleAddVariant, handleAddBarcode, handleLookupBarcode, handleRunPricePreview, handleAddVolumeTier, handleAddKitItem, handleAddAttachment, handleAddWarrantyClaim, handleDuplicate, handleArchiveToggle } = useProductCommercialCard({ productId, productName, canWrite, allProducts, onClose, onRefresh });
  return (
    <div id="scr-010-product-card" className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
      <div className="app-modal-panel flex h-[92vh] w-full max-w-5xl flex-col rounded-2xl bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-100 p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
              <Package className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-slate-900">{productName}</h2>
                {productData?.product?.is_active ? (
                  <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">Activo</span>
                ) : (
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">Archivado</span>
                )}
                <span className="rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-semibold text-teal-800">
                  {String(productData?.profile?.product_type || "product").toUpperCase()}
                </span>
              </div>
              <p className="text-xs text-slate-500">SKU: {String(productData?.product?.sku || "—")} · Unidad: {String(productData?.product?.unit_of_measure || "NIU")}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {canWrite && <button type="button" onClick={handleDuplicate} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"><Copy className="h-4 w-4" />Duplicar</button>}
            {canWrite && <button type="button" onClick={handleArchiveToggle} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50">{productData?.product?.is_active ? <Archive className="h-4 w-4" /> : <ArchiveRestore className="h-4 w-4" />}{productData?.product?.is_active ? "Archivar" : "Restaurar"}</button>}
            <button onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700" aria-label="Cerrar ficha"><X className="h-5 w-5" /></button>
          </div>
        </header>

        <nav className="flex gap-1 border-b border-slate-100 bg-slate-50 px-6 pt-2">
          {[
            { key: "overview" as Tab, label: "Ficha técnica", icon: Package },
            { key: "variants" as Tab, label: "Variantes", icon: Layers },
            { key: "barcodes" as Tab, label: "Códigos de barra", icon: Barcode },
            { key: "pricing" as Tab, label: "Precios y simulación", icon: Calculator },
            { key: "kits" as Tab, label: "Kits y combos", icon: Box },
            { key: "warranty" as Tab, label: "Garantía comercial", icon: Shield },
            { key: "attachments" as Tab, label: "Imágenes y adjuntos", icon: Upload }
          ].map(item => (
            <button
              key={item.key}
              onClick={() => setTab(item.key)}
              className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-semibold transition ${tab === item.key ? "border-teal-700 bg-white text-teal-800" : "border-transparent text-slate-500 hover:text-slate-900"
                }`}
            >
              <item.icon className="h-3.5 w-3.5" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <p className="p-12 text-center text-sm text-slate-500">Cargando datos del producto...</p>
          ) : error ? (
            <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>
          ) : !productData ? null : (
            <>
              {tab === "overview" && (
                <SeccionResumen handleUpdateProfile={handleUpdateProfile} productData={productData} canWrite={canWrite} />
              )}

              {tab === "variants" && (
                <SeccionVariants canWrite={canWrite} handleAddVariant={handleAddVariant} productData={productData} />
              )}

              {tab === "barcodes" && (
                <SeccionBarcodes scannerCode={scannerCode} setScannerCode={setScannerCode} handleLookupBarcode={handleLookupBarcode} scannerResult={scannerResult} canWrite={canWrite} handleAddBarcode={handleAddBarcode} productData={productData} />
              )}

              {tab === "pricing" && (
                <SeccionPricing previewQty={previewQty} setPreviewQty={setPreviewQty} previewCurrency={previewCurrency} setPreviewCurrency={setPreviewCurrency} handleRunPricePreview={handleRunPricePreview} previewLoading={previewLoading} previewResult={previewResult} canWrite={canWrite} handleAddVolumeTier={handleAddVolumeTier} productData={productData} />
              )}

              {tab === "kits" && (
                <SeccionKits canWrite={canWrite} handleAddKitItem={handleAddKitItem} allProducts={allProducts} productId={productId} productData={productData} />
              )}

              {tab === "warranty" && (
                <SeccionWarranty productData={productData} canWrite={canWrite} handleAddWarrantyClaim={handleAddWarrantyClaim} warrantySale={warrantySale} setWarrantySale={setWarrantySale} productId={productId} />
              )}

              {tab === "attachments" && (
                <SeccionAdjuntos canWrite={canWrite} handleAddAttachment={handleAddAttachment} productData={productData} />
              )}
            </>
          )}
        </div>
      </div>
      {PromptDialogNode}
    </div>
  );
}
