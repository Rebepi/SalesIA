import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X } from "lucide-react";
import { ModalSurface } from "../../../../ui/components/ModalSurface";

export function SeccionCreate_supplier({ setModalType, returnToOrderAfterSupplier, handleCreateSupplier, companyCurrency }: { setModalType: ReturnType<typeof usePurchasesWorkspaceTab>["setModalType"]; returnToOrderAfterSupplier: ReturnType<typeof usePurchasesWorkspaceTab>["returnToOrderAfterSupplier"]; handleCreateSupplier: ReturnType<typeof usePurchasesWorkspaceTab>["handleCreateSupplier"]; companyCurrency: ReturnType<typeof usePurchasesWorkspaceTab>["companyCurrency"] }) {
  return (<ModalSurface labelledBy="supplier-editor-title" onClose={() => setModalType(returnToOrderAfterSupplier ? "create_order" : null)}>
    <div className="app-modal-panel w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 id="supplier-editor-title" className="font-bold text-slate-900">Registrar Ficha de Proveedor</h3>
        <button onClick={() => setModalType(returnToOrderAfterSupplier ? "create_order" : null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      <form onSubmit={handleCreateSupplier} className="mt-4 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            RUC / Identificación Fiscal
            <input name="tax_id" required placeholder="20100000001" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Razón Social
            <input name="legal_name" required placeholder="Distribuidora Ejemplo SAC" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            Contacto Comercial
            <input name="contact_name" placeholder="Juan Pérez" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Correo Electrónico
            <input name="email" type="email" placeholder="ventas@proveedor.pe" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            Plazo de Pago (Días)
            <input name="payment_terms_days" type="number" defaultValue="30" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Moneda
            <CustomSelect name="currency" value={companyCurrency} disabled className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs">
              <option value={companyCurrency}>{companyCurrency || "Cargando configuración"}</option>
            </CustomSelect>
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs font-semibold text-slate-700">
            Banco (Restringido)
            <input name="bank_name" placeholder="BCP / BBVA" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
          <label className="block text-xs font-semibold text-slate-700">
            Nº Cuenta Bancaria / CCI
            <input name="bank_account" placeholder="191-0000000-0-00" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
          </label>
        </div>
        <div className="flex justify-end gap-2 pt-3">
          <button type="button" onClick={() => setModalType(returnToOrderAfterSupplier ? "create_order" : null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
          <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800">Guardar Proveedor</button>
        </div>
      </form>
    </div>
  </ModalSurface>);
}
