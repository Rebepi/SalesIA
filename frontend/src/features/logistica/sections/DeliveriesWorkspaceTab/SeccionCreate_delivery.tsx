import type { useDeliveriesWorkspaceTab } from "../../hooks/useDeliveriesWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X } from "lucide-react";

export function SeccionCreate_delivery({ setModalType, handleCreateDelivery, eligibleSales, warehouses, carrierMode, setCarrierMode, deliveryCurrency }: { setModalType: ReturnType<typeof useDeliveriesWorkspaceTab>["setModalType"]; handleCreateDelivery: ReturnType<typeof useDeliveriesWorkspaceTab>["handleCreateDelivery"]; eligibleSales: ReturnType<typeof useDeliveriesWorkspaceTab>["eligibleSales"]; warehouses: ReturnType<typeof useDeliveriesWorkspaceTab>["warehouses"]; carrierMode: ReturnType<typeof useDeliveriesWorkspaceTab>["carrierMode"]; setCarrierMode: ReturnType<typeof useDeliveriesWorkspaceTab>["setCarrierMode"]; deliveryCurrency: ReturnType<typeof useDeliveriesWorkspaceTab>["deliveryCurrency"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
    <div className="app-modal-panel w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="font-bold text-slate-900">Preparar Entrega y Snapshot de Destino</h3>
        <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      <form onSubmit={handleCreateDelivery} className="mt-4 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            Venta confirmada
            <CustomSelect name="sale_id" required searchable className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs"><option value="">Seleccionar venta</option>{eligibleSales.map(sale => <option key={sale.sale_id} value={sale.sale_id}>{sale.number} · {sale.currency} {Number(sale.total_amount).toFixed(2)}</option>)}</CustomSelect>
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Almacén de origen
            <CustomSelect remote={{ resource: "warehouses" }} name="warehouse_id" required searchable className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs"><option value="">Seleccionar almacén</option>{warehouses.map(warehouse => <option key={warehouse.warehouse_id} value={warehouse.warehouse_id}>{warehouse.name} ({warehouse.code})</option>)}</CustomSelect>
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            Destinatario
            <input name="recipient_name" required placeholder="Nombre de quien recibe" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Teléfono de Contacto
            <input name="recipient_phone" placeholder="+51 999 999 999" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
        </div>
        <label className="block text-xs font-semibold text-slate-700">
          Dirección Inmutable de Entrega (Snapshot)
          <input name="delivery_address" required placeholder="Av. Principal 123, Of. 401, Lima" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            Transportista
            <CustomSelect value={carrierMode} onChange={event => setCarrierMode(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs">
              <option value="DHL Express">DHL Express</option>
              <option value="FedEx">FedEx</option>
              <option value="Olva Express">Olva Express</option>
              <option value="Transporte Propio">Transporte Propio</option>
              <option value="__new__">Crear transportista en esta entrega</option>
            </CustomSelect>
            {carrierMode === "__new__" ? <input name="carrier" required placeholder="Nombre del nuevo transportista" className="mt-2 w-full rounded-xl border border-slate-300 p-2 text-xs" /> : <input type="hidden" name="carrier" value={carrierMode} />}
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Nº de Guía / Tracking
            <input name="tracking_number" required placeholder="TRACK123456" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
        </div>
        <label className="block text-xs font-semibold text-slate-700">
          Enlace Oficial de Rastreo (Validado por Dominio)
          <input name="tracking_url" type="url" placeholder="https://www.dhl.com/track/123456" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            Tarifa Cobrada al Cliente ({deliveryCurrency})
            <input name="shipping_fee_charged" type="number" step="0.01" min="0" placeholder="0.00" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Costo Logístico Real ({deliveryCurrency})
            <input name="logistics_cost" type="number" step="0.01" min="0" placeholder="0.00" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            Fecha Prometida de Entrega
            <input name="estimated_delivery_date" type="datetime-local" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Compromiso
            <CustomSelect name="is_guaranteed" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs">
              <option value="false">Fecha Estimada (No contractual)</option>
              <option value="true">Garantizada por SLA</option>
            </CustomSelect>
          </label>
        </div>
        <div className="flex justify-end gap-2 pt-3">
          <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
          <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800">Guardar Preparación</button>
        </div>
      </form>
    </div>
  </div>);
}
