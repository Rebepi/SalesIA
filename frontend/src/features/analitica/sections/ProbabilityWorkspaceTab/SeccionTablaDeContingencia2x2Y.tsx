import type { useProbabilityWorkspaceTab } from "../../hooks/useProbabilityWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionTablaDeContingencia2x2Y({ probResult, contingencyTable }: { probResult: NonNullable<ReturnType<typeof useProbabilityWorkspaceTab>["probResult"]>; contingencyTable: NonNullable<NonNullable<ReturnType<typeof useProbabilityWorkspaceTab>["probResult"]>["contingency_table"]> }) {
  return (<article className="pagination-group">
    <header className="border-b border-slate-100 pb-4 dark:border-slate-800">
      <div className="flex items-center gap-2"><h3 className="text-base font-semibold text-slate-900 dark:text-white">Tabla de Contingencia 2x2 y Soporte Muestral</h3><InfoTooltip title="Tabla de contingencia" description="Cruza ocurrencias y complementos de A y B para mostrar los conteos que sustentan las probabilidades." /></div>
      <p className="text-xs text-slate-500">
        Distribución conjunta de las cuatro celdas observadas y sus totales marginales.
      </p>
    </header>

    <div className="mt-4 pagination-shell">
      <PaginatedTable className="w-full text-left text-sm border-collapse">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700 text-xs uppercase text-slate-500">
            <th className="py-2.5 px-3">Evento</th>
            <th className="py-2.5 px-3 text-right">Evento B (Ocurre)</th>
            <th className="py-2.5 px-3 text-right">No B (Complemento)</th>
            <th className="py-2.5 px-3 text-right font-bold">Total A</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono text-xs">
          <tr>
            <td className="py-3 px-3 font-sans font-semibold text-slate-800 dark:text-slate-200">Evento A (Ocurre)</td>
            <td className="py-3 px-3 text-right font-bold text-teal-700 dark:text-teal-300">
              {contingencyTable.a_and_b}
            </td>
            <td className="py-3 px-3 text-right">{contingencyTable.a_and_not_b}</td>
            <td className="py-3 px-3 text-right font-bold">{contingencyTable.total_a}</td>
          </tr>
          <tr>
            <td className="py-3 px-3 font-sans font-semibold text-slate-800 dark:text-slate-200">No A (Complemento)</td>
            <td className="py-3 px-3 text-right">{contingencyTable.not_a_and_b}</td>
            <td className="py-3 px-3 text-right">{contingencyTable.not_a_and_not_b}</td>
            <td className="py-3 px-3 text-right font-bold">{contingencyTable.total_not_a}</td>
          </tr>
          <tr className="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
            <td className="py-3 px-3 font-sans">Total B</td>
            <td className="py-3 px-3 text-right">{contingencyTable.total_b}</td>
            <td className="py-3 px-3 text-right">{contingencyTable.total_not_b}</td>
            <td className="py-3 px-3 text-right text-teal-800 dark:text-teal-200">{contingencyTable.grand_total}</td>
          </tr>
        </tbody>
      </PaginatedTable>
    </div>

    {probResult.low_sample_warning && (
      <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300">
        <p className="font-semibold">Advertencia de Frecuencias Bajas</p>
        <p className="mt-1">{probResult.warning_message}</p>
      </div>
    )}
  </article>);
}
