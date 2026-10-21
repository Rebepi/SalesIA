import { IconAction } from "../../../ui/components/primitives/IconAction";
import { Printer, Send, Download, UserCheck, RefreshCw, X } from "lucide-react";

interface VentasBulkActionBarProps {
  selectedCount: number;
  onClearSelection: () => void;
  onBatchPrint: () => void;
  onBatchResend: () => void;
  onExportSelected: () => void;
  onAssignSeller: () => void;
  onRetrySunat: () => void;
}

export function VentasBulkActionBar({
  selectedCount,
  onClearSelection,
  onBatchPrint,
  onBatchResend,
  onExportSelected,
  onAssignSeller,
  onRetrySunat,
}: VentasBulkActionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 z-40 flex -translate-x-1/2 items-center gap-3 rounded-3xl border border-slate-700 bg-slate-900 px-5 py-3 text-white shadow-2xl">
      <div className="flex items-center gap-2 border-r border-slate-700 pr-3">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-500 text-[11px] font-bold text-slate-950">
          {selectedCount}
        </span>
        <span className="text-xs font-semibold">seleccionados</span>
      </div>

      <div className="flex items-center gap-1">
        <IconAction label="Imprimir lote" tone="neutral" className="!text-slate-200 !border-slate-700 hover:!bg-slate-800" onClick={onBatchPrint}><Printer className="h-3.5 w-3.5 text-teal-400" /></IconAction>

        <IconAction label="Reenviar" tone="neutral" className="!text-slate-200 !border-slate-700 hover:!bg-slate-800" onClick={onBatchResend}><Send className="h-3.5 w-3.5 text-blue-400" /></IconAction>

        <IconAction label="Exportar" tone="neutral" className="!text-slate-200 !border-slate-700 hover:!bg-slate-800" onClick={onExportSelected}><Download className="h-3.5 w-3.5 text-emerald-400" /></IconAction>

        <IconAction label="Asignar vendedor" tone="neutral" className="!text-slate-200 !border-slate-700 hover:!bg-slate-800" onClick={onAssignSeller}><UserCheck className="h-3.5 w-3.5 text-amber-400" /></IconAction>

        <IconAction label="Reintentar SUNAT" tone="neutral" className="!text-slate-200 !border-slate-700 hover:!bg-slate-800" onClick={onRetrySunat}><RefreshCw className="h-3.5 w-3.5 text-purple-400" /></IconAction>
      </div>

      <IconAction label="Deseleccionar todos" tone="neutral" className="!text-slate-200 !border-slate-700 hover:!bg-slate-800" onClick={onClearSelection}><X className="h-4 w-4" /></IconAction>
    </div>
  );
}
