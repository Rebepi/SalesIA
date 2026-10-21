import { useState } from "react";
import { PurchaseAgreementsPanel } from "./PurchaseAgreementsPanel";
import { SupplierQualificationDialog } from "./SupplierQualificationDialog";
import { SupplierOffersDialog } from "./SupplierOffersDialog";
import { Panel1 } from "../sections/PurchasesWorkspaceTab/Panel1";
import { SeccionSuppliers } from "../sections/PurchasesWorkspaceTab/SeccionSuppliers";
import { SeccionOrders } from "../sections/PurchasesWorkspaceTab/SeccionOrders";
import { SeccionReplenishment } from "../sections/PurchasesWorkspaceTab/SeccionReplenishment";
import { SeccionRequisitions } from "../sections/PurchasesWorkspaceTab/SeccionRequisitions";
import { SeccionCreate_supplier } from "../sections/PurchasesWorkspaceTab/SeccionCreate_supplier";
import { SeccionLanded_cost } from "../sections/PurchasesWorkspaceTab/SeccionLanded_cost";
import { SeccionSupplier_performance } from "../sections/PurchasesWorkspaceTab/SeccionSupplier_performance";
import { SeccionOrder_timeline } from "../sections/PurchasesWorkspaceTab/SeccionOrder_timeline";
export type { Supplier } from "../types/PurchasesWorkspaceTab";
export type { PurchaseOrder } from "../types/PurchasesWorkspaceTab";
import { usePurchasesWorkspaceTab } from "../hooks/usePurchasesWorkspaceTab";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { X } from "lucide-react";
import { PurchaseOrderEditor } from "./PurchaseOrderEditor";
import { PurchaseReceiptDialog } from "./PurchaseReceiptDialog";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { PurchaseOrder } from "../types/PurchasesWorkspaceTab";
import { PurchaseOrderControlDialog } from "./PurchaseOrderControlDialog";
import { PurchaseInvoiceDialog } from "./PurchaseInvoiceDialog";
import { SupplierCatalogPanel } from "./SupplierCatalogPanel";
import { SupplierClaimsPanel } from "./SupplierClaimsPanel";

export function PurchasesWorkspaceTab({
  canWrite,
  initialSubtab = "orders",
  initialModalType = null,
  initialActiveOrder = null,
}: {
  canWrite: boolean;
  initialSubtab?: "suppliers" | "orders" | "requisitions" | "replenishment";
  initialModalType?: string | null;
  initialActiveOrder?: PurchaseOrder | null;
}) {
  const [qualificationSupplier, setQualificationSupplier] = useState<string | null>(null);
  const [offerRequisition, setOfferRequisition] = useState<string | null>(null);
  const { subtab, setSubtab, orders, requisitions, suggestions, loading, error, search, setSearch, setRevision, activeOrder, setActiveOrder, activePerformance, activeTimeline, setActiveReceiptId, returnProductId, setReturnProductId, receiptActionBusy, selectedReceipt, returnLine, modalType, setModalType, warehouses, companyCurrency, defaultTaxRate, editorSource, setEditorSource, editorMode, setEditorMode, selectedSuggestions, setSelectedSuggestions, replenishmentWarehouse, setReplenishmentWarehouse, returnToOrderAfterSupplier, setReturnToOrderAfterSupplier, toast, ConfirmDialogNode, handleCreateSupplier, prepareSuggestions, handleApproveOrder, receiptSelector, handleLandedCost, handlePurchaseReturn, handleViewPerformance, handleViewTimeline, filteredSuppliers } = usePurchasesWorkspaceTab({ canWrite, initialSubtab, initialModalType, initialActiveOrder });
  return (
    <div className="space-y-6">
      <Panel1 setSubtab={setSubtab} setSearch={setSearch} subtab={subtab} setRevision={setRevision} loading={loading} canWrite={canWrite} setModalType={setModalType} setEditorSource={setEditorSource} setEditorMode={setEditorMode} />

      {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-xs text-red-800">{error}</div>}

      {subtab === "suppliers" && (
        <><SeccionSuppliers onQualification={setQualificationSupplier} search={search} setSearch={setSearch} filteredSuppliers={filteredSuppliers} handleViewPerformance={handleViewPerformance} /><SupplierCatalogPanel canWrite={canWrite} /><SupplierClaimsPanel onChanged={() => setRevision(value => value + 1)} /></>
      )}

      {subtab === "orders" && (
        <SeccionOrders orders={orders} handleViewTimeline={handleViewTimeline} setActiveOrder={setActiveOrder} setModalType={setModalType} canWrite={canWrite} handleApproveOrder={handleApproveOrder} />
      )}

      {subtab === "replenishment" && (
        <SeccionReplenishment replenishmentWarehouse={replenishmentWarehouse} setReplenishmentWarehouse={setReplenishmentWarehouse} setSelectedSuggestions={setSelectedSuggestions} warehouses={warehouses} canWrite={canWrite} selectedSuggestions={selectedSuggestions} prepareSuggestions={prepareSuggestions} suggestions={suggestions} />
      )}

      {subtab === "requisitions" && (
        <><PurchaseAgreementsPanel canWrite={canWrite} warehouses={warehouses} onChanged={() => setRevision(value => value + 1)} /><SeccionRequisitions onCompareOffers={setOfferRequisition} requisitions={requisitions} canWrite={canWrite} setEditorMode={setEditorMode} setEditorSource={setEditorSource} setModalType={setModalType} toast={toast} setRevision={setRevision} /></>
      )}

      {qualificationSupplier && <SupplierQualificationDialog supplierId={qualificationSupplier} canWrite={canWrite} onClose={() => setQualificationSupplier(null)} onChanged={() => setRevision(value => value + 1)} />}

      {offerRequisition && <SupplierOffersDialog requisitionId={offerRequisition} canWrite={canWrite} onClose={() => setOfferRequisition(null)} onChanged={() => setRevision(value => value + 1)} />}

      {modalType === "create_supplier" && (
        <SeccionCreate_supplier setModalType={setModalType} returnToOrderAfterSupplier={returnToOrderAfterSupplier} handleCreateSupplier={handleCreateSupplier} companyCurrency={companyCurrency} />
      )}

      <PurchaseOrderEditor isOpen={modalType === "create_order" || (modalType === "create_supplier" && returnToOrderAfterSupplier)} mode={editorMode} source={editorSource} warehouses={warehouses} companyCurrency={companyCurrency} defaultTaxRate={defaultTaxRate} onCreateSupplier={() => { setReturnToOrderAfterSupplier(true); setModalType("create_supplier"); }} onClose={() => setModalType(null)} onSaved={() => { setModalType(null); setSelectedSuggestions([]); setSubtab(editorMode === "order" ? "orders" : "requisitions"); setRevision(value => value + 1); }} />

      {modalType === "order_control" && activeOrder && <PurchaseOrderControlDialog orderId={activeOrder.id} canWrite={canWrite} onClose={() => setModalType(null)} onChanged={() => setRevision(value => value + 1)} />}

      {modalType === "receive_goods" && activeOrder && <PurchaseReceiptDialog canWrite={canWrite} orderId={activeOrder.id} onClose={() => setModalType(null)} onSaved={receiptId => { setActiveReceiptId(receiptId); setModalType(null); setRevision(value => value + 1); }} />}

      {modalType === "landed_cost" && (
        <SeccionLanded_cost receiptActionBusy={receiptActionBusy} setModalType={setModalType} handleLandedCost={handleLandedCost} receiptSelector={receiptSelector} activeOrder={activeOrder} selectedReceipt={selectedReceipt} />
      )}

      {modalType === "purchase_return" && activeOrder && (
        <ModalSurface labelledBy="purchase-return-title" blocked={receiptActionBusy} onClose={() => setModalType(null)}>
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 id="purchase-return-title" className="font-bold text-slate-900">Devolución al Proveedor</h3>
              <button disabled={receiptActionBusy} onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handlePurchaseReturn} className="mt-4 space-y-3">
              {receiptSelector()}
              <label className="block text-xs font-semibold">Producto a devolver<CustomSelect aria-label="Producto a devolver" required value={returnProductId} onChange={event => setReturnProductId(event.target.value)} className="mt-1 w-full"><option value="">Seleccionar producto de la recepción</option>{selectedReceipt?.returnable_lines.filter(line => Number(line.returnable_quantity) > 0).map(line => <option key={line.product_id} value={line.product_id}>{line.name} · {line.sku} · Saldo {line.returnable_quantity}</option>)}</CustomSelect></label>
              {returnLine && <p className="text-xs text-slate-500">Recibido: {returnLine.quantity} · Disponible para devolver: {returnLine.returnable_quantity}. Esta operación registra la salida física y el crédito esperado del proveedor.</p>}
              {Boolean(returnLine?.lots.length) && <label className="block text-xs font-semibold">Lote<CustomSelect name="lot_id" required className="mt-1 w-full"><option value="">Seleccionar lote recibido</option>{returnLine?.lots.map(lot => <option key={lot.lot_id} value={lot.lot_id}>{lot.lot_code} · Recibido {lot.quantity}</option>)}</CustomSelect></label>}
              {Boolean(returnLine?.serial_numbers.length) && <label className="block text-xs font-semibold">Series a devolver<textarea name="serial_numbers" required placeholder="Una serie por línea" className="mt-1 w-full rounded-xl border p-2" /><span className="text-[10px] text-slate-500">Series disponibles de esta recepción: {returnLine?.serial_numbers.join(", ")}. Se comprobarán nuevamente al confirmar.</span></label>}
              <label className="block text-xs font-semibold text-slate-700">
                Cantidad a Devolver
                <input name="quantity" max={returnLine?.returnable_quantity} type="number" step="any" min="0.000001" required defaultValue="1" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Motivo de Devolución
                <input name="reason" required placeholder="Producto defectuoso de origen" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
              </label>

              <div className="flex justify-end gap-2 pt-3">
                <button type="button" disabled={receiptActionBusy} onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" disabled={!returnLine || receiptActionBusy} className="rounded-xl bg-red-700 px-4 py-2 text-xs font-semibold text-white hover:bg-red-800">Confirmar Devolución</button>
              </div>
            </form>
          </div>
        </ModalSurface>
      )}

      {modalType === "three_way_match" && activeOrder && <PurchaseInvoiceDialog orderId={activeOrder.id} canWrite={canWrite} onClose={() => setModalType(null)} onChanged={() => setRevision(value => value + 1)} />}

      {modalType === "supplier_performance" && activePerformance && (
        <SeccionSupplier_performance canWrite={canWrite} onReload={() => { if (activePerformance) void handleViewPerformance(activePerformance.supplier_id); }} activePerformance={activePerformance} setModalType={setModalType} />
      )}

      {modalType === "order_timeline" && activeTimeline && (
        <SeccionOrder_timeline activeTimeline={activeTimeline} setModalType={setModalType} />
      )}
      {ConfirmDialogNode}
    </div>
  );
}
