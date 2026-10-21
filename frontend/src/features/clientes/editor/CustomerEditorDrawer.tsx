import { AlertCircle, LoaderCircle, Save, UserPlus, X } from "lucide-react";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { useEditorCliente } from "../hooks/useEditorCliente";
import type { CustomerEditorDrawerProps } from "../types/clientes";
import { CondicionesCliente } from "./CondicionesCliente";
import { ContactoCliente } from "./ContactoCliente";
import { IdentidadCliente } from "./IdentidadCliente";
export type { CustomerData } from "../types/clientes";
export function CustomerEditorDrawer(props: CustomerEditorDrawerProps) {
  const { isOpen, initialData, quickMode = false } = props;
  const model = useEditorCliente(props);
  const { ConfirmDialogNode, busy, validating, error, handleSubmit, handleClose } = model;
  if (!isOpen) return null;
  return (
    <ModalSurface labelledBy="scr-008-drawer-title" onClose={() => void handleClose()} blocked={busy} className={quickMode ? "customer-editor-modal" : "customer-editor-modal customer-editor-side"}>
      <div
        id="scr-008-customer-drawer"
        className="app-modal-panel customer-editor-panel w-full bg-white shadow-2xl flex flex-col rounded-2xl"
      >
        <header className="flex items-center justify-between border-b border-slate-200 p-6 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <UserPlus className="h-5 w-5 text-teal-600" />
            <div>
              <h2 id="scr-008-drawer-title" className="text-lg font-bold text-slate-900">
                {initialData ? "Editar cliente" : "Alta rápida de cliente"}
              </h2>
              <p className="text-xs text-slate-500">{quickMode ? "Datos mínimos para continuar con la operación" : "Formulario estructurado en secciones con preservación de borrador"}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={busy}
            aria-label="Cerrar editor de cliente"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <form id="customer-editor-form" onSubmit={handleSubmit} className="min-h-0 flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div role="alert" className="flex items-center gap-2 rounded-xl bg-red-50 p-3 text-xs text-red-800">
              <AlertCircle className="h-4 w-4 flex-shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          <IdentidadCliente model={model} quickMode={quickMode} />

          <ContactoCliente model={model} quickMode={quickMode} />

          {!quickMode && <CondicionesCliente model={model} quickMode={quickMode} />}
        </form>

        <footer className="flex items-center justify-between border-t border-slate-200 p-4 bg-slate-50">
          <button
            type="button"
            onClick={handleClose}
            disabled={busy}
            className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-white"
          >
            Cancelar
          </button>
          <button
            type="submit"
            form="customer-editor-form"
            disabled={busy || validating}
            title={validating ? "Espera a que termine la validación del documento" : undefined}
            className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-5 py-2 text-xs font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
          >
            {busy ? <LoaderCircle className="h-4 w-4 motion-safe:animate-spin" /> : <Save className="h-4 w-4" />}
            {validating ? "Validando documento…" : "Guardar cliente"}
          </button>
        </footer>
      </div>
      {ConfirmDialogNode}
    </ModalSurface>
  );
}
