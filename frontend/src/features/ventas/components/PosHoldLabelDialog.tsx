import { useRef, useState } from "react";
import { Clock, Tag, X } from "lucide-react";

interface PosHoldLabelDialogProps {
  isOpen: boolean;
  defaultLabel: string;
  onConfirm: (label: string) => void;
  onCancel: () => void;
}

export function PosHoldLabelDialog({
  isOpen,
  defaultLabel,
  onConfirm,
  onCancel
}: PosHoldLabelDialogProps) {
  const [label, setLabel] = useState(defaultLabel);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onConfirm(label.trim() || defaultLabel);
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-sm rounded-3xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 shadow-2xl overflow-hidden">
        <header className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-700 dark:bg-amber-400/20 dark:text-amber-300">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Poner en espera</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Asigna un nombre para identificar este ticket</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-bold text-slate-700 dark:text-slate-300">
              Etiqueta / Nombre del ticket
            </label>
            <div className="relative">
              <Tag className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                ref={inputRef}
                autoFocus
                type="text"
                maxLength={60}
                value={label}
                onChange={e => setLabel(e.target.value)}
                placeholder={defaultLabel || "Ej: Mesa 5, Cliente con sombrero..."}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 py-2.5 pl-9 pr-4 text-sm text-slate-800 dark:text-slate-100 outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100 dark:focus:ring-amber-900/30 transition"
              />
            </div>
            <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
              Puedes dejarlo vacío para usar el nombre del cliente.
            </p>
          </div>

          <div className="rounded-xl border border-amber-200 bg-amber-50/60 dark:border-amber-900/40 dark:bg-amber-950/20 px-3.5 py-2.5 text-[11px] text-amber-800 dark:text-amber-300">
            <strong>Importante:</strong> El stock no se reserva. Si otro cliente compra el mismo producto antes de que regrese, recibirás un aviso al retomar la venta.
          </div>

          <div className="flex gap-2.5 pt-1">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 rounded-xl border border-slate-200 dark:border-slate-700 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 rounded-xl bg-amber-600 py-2.5 text-sm font-bold text-white hover:bg-amber-700 transition shadow-sm"
            >
              Guardar en espera
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
