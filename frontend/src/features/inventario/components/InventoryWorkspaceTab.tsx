import { useOperatingProfile } from "../../organizacion/components/OperatingProfileContext";
import { Panel1 } from "../sections/InventoryWorkspaceTab/Panel1";
import { Panel2 } from "../sections/InventoryWorkspaceTab/Panel2";
import { SeccionStock } from "../sections/InventoryWorkspaceTab/SeccionStock";
import { SeccionKardex } from "../sections/InventoryWorkspaceTab/SeccionKardex";
import { SeccionTransfers } from "../sections/InventoryWorkspaceTab/SeccionTransfers";
import { SeccionCounts } from "../sections/InventoryWorkspaceTab/SeccionCounts";
import { SeccionLots_serials } from "../sections/InventoryWorkspaceTab/SeccionLots_serials";
import { SeccionLocations_rules } from "../sections/InventoryWorkspaceTab/SeccionLocations_rules";
import { SeccionAlerts_reconcile } from "../sections/InventoryWorkspaceTab/SeccionAlerts_reconcile";
export type { TransferItem } from "../types/InventoryWorkspaceTab";
export type { CountItem } from "../types/InventoryWorkspaceTab";
import { useInventoryWorkspaceTab } from "../hooks/useInventoryWorkspaceTab";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { X } from "lucide-react";
import { PurchasesWorkspaceTab } from "../../compras/components/PurchasesWorkspaceTab";
import { DeliveriesWorkspaceTab } from "../../logistica/components/DeliveriesWorkspaceTab";
import { InventoryOperationDialog } from "./InventoryOperationDialog";
import { InventoryTransferDialog } from "./InventoryTransferDialog";
import { PhysicalCountDialog } from "./PhysicalCountDialog";
import { InventoryTraceDialog } from "./InventoryTraceDialog";
import { Submodule } from "../types/InventoryWorkspaceTab";
import { TransferItem } from "../types/InventoryWorkspaceTab";
import { CountItem } from "../types/InventoryWorkspaceTab";

export function InventoryWorkspaceTab({
  canWrite,
  initialSubmodule = "stock",
  initialTransfers = [],
  initialCounts = [],
}: {
  canWrite: boolean;
  initialSubmodule?: Submodule;
  initialTransfers?: TransferItem[];
  initialCounts?: CountItem[];
}) {
  const { enabled } = useOperatingProfile();
  const { ConfirmDialogNode, submodule, setSubmodule, warehouses, products, selectedWarehouseId, setSelectedWarehouseId, search, setSearch, setRevision, loading, error, navRef, canScrollLeft, canScrollRight, kardexItems, transfers, counts, lots, serials, locations, rules, alerts, quarantineItems, trace, setTrace, operation, setOperation, countProductIds, setCountProductIds, activeCount, setActiveCount, transferContext, setTransferContext, setProductFilter, modalType, setModalType, activeTransfer, setActiveTransfer, handleDispatchTransfer, handleCreateCount, handleApproveCount, handleRecalculateAlerts, handleRunReconcile, handleClassifyQuarantine, productName, warehouseName, blockLot, deactivateRule, filteredStock, totalAvailable, totalInTransit, totalQuarantine, totalReserved } = useInventoryWorkspaceTab({ canWrite, initialSubmodule, initialTransfers, initialCounts });
  return (
    <div className="inventory-workspace-root flex flex-col flex-1 min-h-0 h-full gap-2.5">
      <Panel1 warehouses={warehouses} selectedWarehouseId={selectedWarehouseId} setSelectedWarehouseId={setSelectedWarehouseId} search={search} setSearch={setSearch} setRevision={setRevision} loading={loading} />

      <Panel2 canScrollLeft={canScrollLeft} navRef={navRef} submodule={submodule} setSubmodule={setSubmodule} setSearch={setSearch} canScrollRight={canScrollRight} />

      {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-xs text-red-800 flex-shrink-0">{error}</div>}

      {submodule === "purchases" && (
        <PurchasesWorkspaceTab canWrite={canWrite && enabled("purchases")} />
      )}

      {submodule === "shipping" && (
        <DeliveriesWorkspaceTab canWrite={canWrite && enabled("delivery")} />
      )}

      {submodule === "stock" && (
        <SeccionStock totalAvailable={totalAvailable} totalReserved={totalReserved} totalInTransit={totalInTransit} totalQuarantine={totalQuarantine} filteredStock={filteredStock} productName={productName} warehouseName={warehouseName} setProductFilter={setProductFilter} setSubmodule={setSubmodule} canWrite={canWrite} setOperation={setOperation} setTransferContext={setTransferContext} setModalType={setModalType} />
      )}

      {submodule === "kardex" && (
        <SeccionKardex kardexItems={kardexItems} />
      )}

      {submodule === "transfers" && (
        <SeccionTransfers canWrite={canWrite} setModalType={setModalType} transfers={transfers} warehouses={warehouses} handleDispatchTransfer={handleDispatchTransfer} setActiveTransfer={setActiveTransfer} />
      )}

      {submodule === "counts" && (
        <SeccionCounts canWrite={canWrite} setModalType={setModalType} counts={counts} warehouses={warehouses} setActiveCount={setActiveCount} handleApproveCount={handleApproveCount} />
      )}

      {submodule === "lots_serials" && (
        <SeccionLots_serials canWrite={canWrite} setOperation={setOperation} lots={lots} search={search} productName={productName} blockLot={blockLot} setTrace={setTrace} selectedWarehouseId={selectedWarehouseId} serials={serials} warehouseName={warehouseName} />
      )}

      {submodule === "locations_rules" && (
        <SeccionLocations_rules canWrite={canWrite} setOperation={setOperation} selectedWarehouseId={selectedWarehouseId} locations={locations} warehouseName={warehouseName} rules={rules} productName={productName} deactivateRule={deactivateRule} />
      )}

      {submodule === "alerts_reconcile" && (
        <SeccionAlerts_reconcile handleRecalculateAlerts={handleRecalculateAlerts} setModalType={setModalType} alerts={alerts} quarantineItems={quarantineItems} productName={productName} warehouseName={warehouseName} handleClassifyQuarantine={handleClassifyQuarantine} />
      )}

      {modalType === "create_transfer" && <InventoryTransferDialog products={products} warehouses={warehouses} sourceId={transferContext.sourceId} productId={transferContext.productId} onClose={() => setModalType(null)} onSaved={() => { setModalType(null); setRevision(value => value + 1); }} />}
      {modalType === "receive_transfer" && activeTransfer && <InventoryTransferDialog transfer={activeTransfer} products={products} warehouses={warehouses} onClose={() => setModalType(null)} onSaved={() => { setModalType(null); setActiveTransfer(null); setRevision(value => value + 1); }} />}
      {operation && <InventoryOperationDialog operation={operation} products={products} warehouses={warehouses} onClose={() => setOperation(null)} onSaved={() => { setOperation(null); setRevision(value => value + 1); }} />}
      {activeCount && <PhysicalCountDialog canWrite={canWrite} count={activeCount} products={products} onClose={() => setActiveCount(null)} onSaved={() => { setActiveCount(null); setRevision(value => value + 1); }} />}

      {modalType === "create_count" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Iniciar Sesión de Conteo Ciego</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleCreateCount} className="mt-4 space-y-4">
              <label className="block text-xs font-semibold text-slate-700">
                Almacén a Contar
                <CustomSelect remote={{ resource: "warehouses" }} name="warehouse_id" required className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs">
                  {warehouses.map(w => (
                    <option key={w.warehouse_id} value={w.warehouse_id}>{w.name} ({w.code})</option>
                  ))}
                </CustomSelect>
              </label>
              <fieldset className="rounded-xl border p-3"><legend className="px-1 text-xs font-semibold">Productos del conteo</legend><p className="mb-2 text-xs text-slate-500">Sin selección se incluirán todos los productos activos del almacén.</p><CustomSelect remote={{ resource: "products" }} multiple aria-label="Productos del conteo" value={countProductIds} onChange={event => setCountProductIds(Array.from(event.target.selectedOptions, option => option.value))} className="w-full">{products.map(product => <option key={product.id} value={product.id}>{product.sku} · {product.name}</option>)}</CustomSelect></fieldset>
              <label className="block text-xs font-semibold text-slate-700">
                Notas / Instrucciones al Equipo
                <input name="notes" placeholder="Corte al cierre de turno" className="mt-1.5 w-full rounded-xl border border-slate-300 p-2.5 text-xs" />
              </label>
              <div className="flex justify-end gap-2 pt-3">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800">Iniciar Conteo</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalType === "reconcile" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Auditar Saldo de Stock vs Libro Kardex</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleRunReconcile} className="mt-4 space-y-4">
              <label className="block text-xs font-semibold text-slate-700">
                Almacén
                <CustomSelect remote={{ resource: "warehouses" }} name="warehouse_id" required className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs">
                  {warehouses.map(w => (
                    <option key={w.warehouse_id} value={w.warehouse_id}>{w.name}</option>
                  ))}
                </CustomSelect>
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Producto
                <CustomSelect remote={{ resource: "products" }} name="product_id" required className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs">
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                  ))}
                </CustomSelect>
              </label>
              <div className="flex justify-end gap-2 pt-3">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800">Ejecutar Auditoría</button>
              </div>
            </form>
          </div>
        </div>
      )}
      {trace && <InventoryTraceDialog kind={trace.kind} id={trace.id} onClose={() => setTrace(undefined)} />}
      {ConfirmDialogNode}
    </div>
  );
}
