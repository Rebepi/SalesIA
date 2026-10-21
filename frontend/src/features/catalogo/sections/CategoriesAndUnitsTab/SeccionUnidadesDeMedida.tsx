import type { useCategoriesAndUnitsTab } from "../../hooks/useCategoriesAndUnitsTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";

export function SeccionUnidadesDeMedida({ units, canWrite, handleCreateUnit, newUnitCode, setNewUnitCode, newUnitName, setNewUnitName, newUnitAllowFrac, setNewUnitAllowFrac, busy, handleCreateConversion, convFrom, setConvFrom, convTo, setConvTo, convFactor, setConvFactor, conversions }: { units: ReturnType<typeof useCategoriesAndUnitsTab>["units"]; handleCreateUnit: ReturnType<typeof useCategoriesAndUnitsTab>["handleCreateUnit"]; newUnitCode: ReturnType<typeof useCategoriesAndUnitsTab>["newUnitCode"]; setNewUnitCode: ReturnType<typeof useCategoriesAndUnitsTab>["setNewUnitCode"]; newUnitName: ReturnType<typeof useCategoriesAndUnitsTab>["newUnitName"]; setNewUnitName: ReturnType<typeof useCategoriesAndUnitsTab>["setNewUnitName"]; newUnitAllowFrac: ReturnType<typeof useCategoriesAndUnitsTab>["newUnitAllowFrac"]; setNewUnitAllowFrac: ReturnType<typeof useCategoriesAndUnitsTab>["setNewUnitAllowFrac"]; busy: ReturnType<typeof useCategoriesAndUnitsTab>["busy"]; handleCreateConversion: ReturnType<typeof useCategoriesAndUnitsTab>["handleCreateConversion"]; convFrom: ReturnType<typeof useCategoriesAndUnitsTab>["convFrom"]; setConvFrom: ReturnType<typeof useCategoriesAndUnitsTab>["setConvFrom"]; convTo: ReturnType<typeof useCategoriesAndUnitsTab>["convTo"]; setConvTo: ReturnType<typeof useCategoriesAndUnitsTab>["setConvTo"]; convFactor: ReturnType<typeof useCategoriesAndUnitsTab>["convFactor"]; setConvFactor: ReturnType<typeof useCategoriesAndUnitsTab>["setConvFactor"]; conversions: ReturnType<typeof useCategoriesAndUnitsTab>["conversions"] } & { canWrite: NonNullable<{ canWrite?: boolean }["canWrite"]> }) {
  return (<div className="grid lg:grid-cols-2 gap-6 items-start">
    <section className="space-y-4 pagination-group">
      <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3">
        Unidades de Medida
      </h3>
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500 font-semibold">
              <th className="pb-2">Código</th>
              <th className="pb-2">Nombre</th>
              <th className="pb-2">Fracciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {units.map(u => (
              <tr key={u.id} className="hover:bg-slate-50">
                <td className="py-2.5 font-mono font-bold text-teal-800">{u.code}</td>
                <td className="py-2.5 text-slate-800">{u.name}</td>
                <td className="py-2.5 text-slate-500">{u.allow_fractions ? "Permitidas" : "Solo enteros"}</td>
              </tr>
            ))}
          </tbody>
        </PaginatedTable>
      </div>

      {canWrite && (
        <form onSubmit={handleCreateUnit} className="pt-4 border-t border-slate-100 space-y-3 text-xs">
          <p className="font-semibold text-slate-800">Registrar Nueva Unidad</p>
          <div className="grid grid-cols-2 gap-3">
            <input
              required
              placeholder="Código (ej. NIU, KGM)"
              value={newUnitCode}
              onChange={e => setNewUnitCode(e.target.value)}
              className="rounded-xl border border-slate-300 p-2 outline-none focus:border-teal-600"
            />
            <input
              required
              placeholder="Nombre (ej. Unidad, Kilo)"
              value={newUnitName}
              onChange={e => setNewUnitName(e.target.value)}
              className="rounded-xl border border-slate-300 p-2 outline-none focus:border-teal-600"
            />
          </div>
          <label className="flex items-center gap-2 text-slate-600">
            <input
              type="checkbox"
              checked={newUnitAllowFrac}
              onChange={e => setNewUnitAllowFrac(e.target.checked)}
              className="rounded"
            />
            Permite cantidades decimales/fracciones
          </label>
          <button
            type="submit"
            disabled={busy}
            className="rounded-xl bg-teal-700 px-4 py-2 font-semibold text-white hover:bg-teal-800"
          >
            Registrar Unidad
          </button>
        </form>
      )}
    </section>

    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3">
        Equivalencias y Conversiones
      </h3>
      {canWrite && (
        <form onSubmit={handleCreateConversion} className="space-y-3 text-xs pb-4 border-b border-slate-100">
          <p className="font-semibold text-slate-800">Nueva Regla de Conversión</p>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-[10px] text-slate-400">Unidad Base</label>
              <input
                required
                value={convFrom}
                onChange={e => setConvFrom(e.target.value)}
                placeholder="NIU"
                className="w-full rounded-xl border border-slate-300 p-2 outline-none focus:border-teal-600"
              />
            </div>
            <div>
              <label className="block text-[10px] text-slate-400">Unidad Superior</label>
              <input
                required
                value={convTo}
                onChange={e => setConvTo(e.target.value)}
                placeholder="BX"
                className="w-full rounded-xl border border-slate-300 p-2 outline-none focus:border-teal-600"
              />
            </div>
            <div>
              <label className="block text-[10px] text-slate-400">Factor Multiplicador</label>
              <input
                required
                type="number"
                step="any"
                value={convFactor}
                onChange={e => setConvFactor(e.target.value)}
                className="w-full rounded-xl border border-slate-300 p-2 outline-none focus:border-teal-600"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="rounded-xl bg-teal-700 px-4 py-2 font-semibold text-white hover:bg-teal-800"
          >
            Crear Equivalencia
          </button>
        </form>
      )}

      <ul className="space-y-2 text-xs">
        {conversions.map(c => (
          <li key={c.id} className="rounded-xl border border-slate-100 p-2.5 flex justify-between bg-slate-50">
            <span>1 {c.to_unit}</span>
            <span className="font-bold text-teal-800">= {c.factor} {c.from_unit}</span>
          </li>
        ))}
        {conversions.length === 0 && <li className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-slate-500">No hay reglas de conversión registradas.</li>}
      </ul>
    </section>
  </div>);
}
