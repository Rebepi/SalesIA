import type { useEditorCliente } from "../hooks/useEditorCliente";
type EditorClienteModel = ReturnType<typeof useEditorCliente>;
export function ContactoCliente({ model }: { model: EditorClienteModel; quickMode: boolean }) {
  const { formData, handleChange } = model;
  return (<fieldset className="rounded-2xl border border-slate-200 p-4 space-y-3">
    <legend className="px-2 text-xs font-bold uppercase tracking-wider text-teal-700">
      2. Contacto y Comunicación
    </legend>
    <div className="grid grid-cols-2 gap-3">
      <div>
        <label htmlFor="customer-email" className="block text-[11px] font-semibold text-slate-600">Correo Electrónico</label>
        <input
          type="email"
          id="customer-email"
          maxLength={255}
          value={formData.email || ""}
          onChange={e => handleChange("email", e.target.value)}
          className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs outline-none focus:border-teal-600"
        />
      </div>
      <div>
        <label htmlFor="customer-phone" className="block text-[11px] font-semibold text-slate-600">Teléfono</label>
        <input
          id="customer-phone"
          type="tel"
          minLength={6}
          maxLength={32}
          value={formData.phone || ""}
          onChange={e => handleChange("phone", e.target.value)}
          className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs outline-none focus:border-teal-600"
        />
      </div>
    </div>
  </fieldset>);
}
