import type { useOrdersWorkspaceTab } from "../../hooks/useOrdersWorkspaceTab";
import { NavbarSectionHeader } from "../../../../ui/components/NavbarSectionHeader";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { LayoutGrid, List, Plus } from "lucide-react";

export function SeccionPedidosDeVenta({ canWrite, setEditorOpen, setViewMode, viewMode, filterStatus, setFilterStatus }: { setEditorOpen: ReturnType<typeof useOrdersWorkspaceTab>["setEditorOpen"]; setViewMode: ReturnType<typeof useOrdersWorkspaceTab>["setViewMode"]; viewMode: ReturnType<typeof useOrdersWorkspaceTab>["viewMode"]; filterStatus: ReturnType<typeof useOrdersWorkspaceTab>["filterStatus"]; setFilterStatus: ReturnType<typeof useOrdersWorkspaceTab>["setFilterStatus"] } & { canWrite: NonNullable<{ canWrite?: boolean }["canWrite"]> }) {
  return (<NavbarSectionHeader view="orders" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
    <div>
      <h2 className="text-xl font-bold text-slate-900">Pedidos de Venta</h2>
      <p className="text-xs text-slate-500">
        Control de reservas en almacén, preparación y entregas parciales con trazabilidad
      </p>
    </div>
    <div className="flex flex-wrap items-center gap-2">
      {canWrite && <button type="button" onClick={() => setEditorOpen(true)} className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-600"><Plus className="h-4 w-4" />Nuevo pedido</button>}
      <div className="flex rounded-xl border border-slate-200 bg-white p-0.5">
        <button
          type="button"
          onClick={() => setViewMode("table")}
          className={`p-1.5 rounded-lg text-xs ${viewMode === "table" ? "bg-teal-700 text-white font-bold" : "text-slate-600 hover:bg-slate-50"}`}
          title="Vista tabla"
        >
          <List className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => setViewMode("board")}
          className={`p-1.5 rounded-lg text-xs ${viewMode === "board" ? "bg-teal-700 text-white font-bold" : "text-slate-600 hover:bg-slate-50"}`}
          title="Vista tablero"
        >
          <LayoutGrid className="h-4 w-4" />
        </button>
      </div>
      <CustomSelect
        value={filterStatus}
        onChange={e => setFilterStatus(e.target.value)}
        className="rounded-xl border border-slate-300 px-3 py-1.5 text-xs outline-none focus:border-teal-600"
      >
        <option value="">Todos los estados</option>
        <option value="draft">Borrador</option>
        <option value="confirmed">Confirmado / Reservado</option>
        <option value="partially_fulfilled">Despacho Parcial</option>
        <option value="fulfilled">Completado</option>
      </CustomSelect>
    </div>
  </NavbarSectionHeader>);
}
