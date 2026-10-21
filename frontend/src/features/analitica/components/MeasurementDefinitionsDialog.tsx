import { useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { Info } from "lucide-react";
import { Modal } from "../../../ui/components/primitives/Modal";
import { MeasurementDefinitions, type MeasurementContext, type MetricDefinition } from "./MeasurementDefinitions";

type Props = {
  context?: MeasurementContext;
  definitions?: Record<string, MetricDefinition | string>;
  title?: string;
  label?: string;
};

export function MeasurementDefinitionsDialog({ context, definitions, title = "Cómo se calculan los indicadores", label = "Ver definiciones" }: Props) {
  const [open, setOpen] = useState(false);
  const close = useCallback(() => setOpen(false), []);
  if (!context && !definitions) return null;
  return <>
    <button type="button" onClick={() => setOpen(true)} aria-haspopup="dialog" aria-label={label || title} className="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 focus-visible:outline focus-visible:outline-teal-500 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
      <Info className="h-3.5 w-3.5" aria-hidden="true" />
      {label}
    </button>
    {open && createPortal(<Modal isOpen={open} onClose={close} title={title} size="xl" footer={<button type="button" onClick={close} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800">Cerrar</button>}>
      <MeasurementDefinitions context={context} definitions={definitions} expanded />
    </Modal>, document.body)}
  </>;
}
