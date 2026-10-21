import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { FileText, Layers, Plus, RefreshCw, ShoppingBag, UserCheck } from "lucide-react";
import { PurchaseOrder } from "../../types/PurchasesWorkspaceTab";

export function Panel1({ setSubtab, setSearch, subtab, setRevision, loading, canWrite, setModalType, setEditorSource, setEditorMode }: { setSubtab: ReturnType<typeof usePurchasesWorkspaceTab>["setSubtab"]; setSearch: ReturnType<typeof usePurchasesWorkspaceTab>["setSearch"]; subtab: ReturnType<typeof usePurchasesWorkspaceTab>["subtab"]; setRevision: ReturnType<typeof usePurchasesWorkspaceTab>["setRevision"]; loading: ReturnType<typeof usePurchasesWorkspaceTab>["loading"]; setModalType: ReturnType<typeof usePurchasesWorkspaceTab>["setModalType"]; setEditorSource: ReturnType<typeof usePurchasesWorkspaceTab>["setEditorSource"]; setEditorMode: ReturnType<typeof usePurchasesWorkspaceTab>["setEditorMode"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubtab?: "suppliers" | "orders" | "requisitions" | "replenishment";
    initialModalType?: string | null;
    initialActiveOrder?: PurchaseOrder | null;
  }["canWrite"]
}) {
  return (<div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
    <div className="flex flex-wrap gap-2">
      {[
        { key: "orders" as const, label: "Órdenes de Compra", Icon: FileText },
        { key: "suppliers" as const, label: "Fichas de Proveedores", Icon: UserCheck },
        { key: "requisitions" as const, label: "Requerimientos Internos", Icon: Layers },
        { key: "replenishment" as const, label: "Reposición Asistida", Icon: ShoppingBag }
      ].map(({ key, label, Icon }) => (
        <button
          key={key}
          onClick={() => { setSubtab(key); setSearch(""); }}
          className={`inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition ${subtab === key
            ? "bg-slate-900 text-white shadow-sm"
            : "border border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
            }`}
        >
          <Icon className="h-3.5 w-3.5" />
          {label}
        </button>
      ))}
    </div>
    <div className="flex items-center gap-2">
      <button
        onClick={() => setRevision(r => r + 1)}
        disabled={loading}
        aria-label="Actualizar datos de compras"
        className="group rounded-xl border border-slate-200 bg-white p-2 text-slate-600 transition hover:bg-slate-100 disabled:opacity-50"
      >
        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : "group-hover:rotate-90"}`} />
      </button>
      {canWrite && subtab === "suppliers" && (
        <button
          onClick={() => setModalType("create_supplier")}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-800"
        >
          <Plus className="h-3.5 w-3.5" />
          Nuevo Proveedor
        </button>
      )}
      {canWrite && subtab === "orders" && (
        <button
          onClick={() => { setEditorSource(undefined); setEditorMode("order"); setModalType("create_order"); }}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-800"
        >
          <Plus className="h-3.5 w-3.5" />
          Nueva Orden de Compra
        </button>
      )}
    </div>
  </div>);
}
