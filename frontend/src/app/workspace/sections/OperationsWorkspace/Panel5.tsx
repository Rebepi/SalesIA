import type { useOperationsWorkspace } from "../../hooks/useOperationsWorkspace";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { inputStyle } from "../../support/OperationsWorkspace";
import { buttonStyle } from "../../support/OperationsWorkspace";
import { Dialog } from "../../support/OperationsWorkspace";

export function Panel5({ editor, busy, setEditor, setError, save, error }: { editor: NonNullable<ReturnType<typeof useOperationsWorkspace>["editor"]>; busy: ReturnType<typeof useOperationsWorkspace>["busy"]; setEditor: ReturnType<typeof useOperationsWorkspace>["setEditor"]; setError: ReturnType<typeof useOperationsWorkspace>["setError"]; save: ReturnType<typeof useOperationsWorkspace>["save"]; error: ReturnType<typeof useOperationsWorkspace>["error"] }) {
  return (<Dialog title={editor.title} close={() => { if (!busy) { setEditor(null); setError(""); } }}>

    <form onSubmit={save} className="space-y-5 p-6" aria-busy={busy}>

      {editor.fields.map(field => (

        <label key={field.name} className="block text-sm font-medium" htmlFor={`field-${field.name}`}>

          {field.label}

          {field.options ? (

            <CustomSelect id={`field-${field.name}`} name={field.name} required={!field.optional} defaultValue={field.value ?? ""} className={inputStyle}>

              <option value="" disabled>Seleccionar</option>

              {field.options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}

            </CustomSelect>

          ) : (

            <input id={`field-${field.name}`} name={field.name} type={field.type || "text"} step={field.type === "number" ? "any" : undefined} required={!field.optional} defaultValue={field.value} className={inputStyle} autoComplete={field.type === "password" ? "current-password" : "off"} />

          )}

        </label>

      ))}

      {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}

      <div className="flex justify-end gap-3 border-t border-slate-100 pt-5">

        <button type="button" className={buttonStyle} disabled={busy} onClick={() => { setEditor(null); setError(""); }}>Cancelar</button>

        <button disabled={busy} className="rounded-lg bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800 focus-visible:outline focus-visible:outline-teal-300 disabled:opacity-50">

          {busy ? "Guardando…" : "Guardar"}

        </button>

      </div>

    </form>

  </Dialog>);
}
