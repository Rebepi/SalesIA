import type { useEditorCliente } from "../hooks/useEditorCliente";
type EditorClienteModel = ReturnType<typeof useEditorCliente>;
export function CondicionesCliente({ model }: { model: EditorClienteModel; quickMode: boolean }) {
  const { formData, handleChange } = model;
  return (<fieldset className="rounded-2xl border border-slate-200 p-4 space-y-3">
    <legend className="px-2 text-xs font-bold uppercase tracking-wider text-teal-700">
      3. Condiciones Comerciales
    </legend>
    <div>
      <label htmlFor="customer-credit_limit" className="block text-[11px] font-semibold text-slate-600">Límite de Crédito Autorizado</label>
      <input
        type="number"
        step="any"
        id="customer-credit_limit"
        value={formData.credit_limit || "0"}
        onChange={e => handleChange("credit_limit", e.target.value)}
        className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs outline-none focus:border-teal-600"
      />
    </div>
  </fieldset>);
}
