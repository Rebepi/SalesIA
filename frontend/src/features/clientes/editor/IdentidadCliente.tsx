import { documentoClienteRules, limpiarDocumentoCliente } from "../utils/validacionCliente";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import type { useEditorCliente } from "../hooks/useEditorCliente";
type EditorClienteModel = ReturnType<typeof useEditorCliente>;
export function IdentidadCliente({ model, quickMode }: { model: EditorClienteModel; quickMode: boolean }) {
  const { formData, busy, validating, duplicateWarning, duplicateCandidates, fiscalStatus, handleChange, checkDuplicateDoc, chooseDuplicate } = model;
  return (<fieldset className="rounded-2xl border border-slate-200 p-4 space-y-3">
    <legend className="px-2 text-xs font-bold uppercase tracking-wider text-teal-700">
      1. Identidad Fiscal
    </legend>
    <div className="grid grid-cols-3 gap-3">
      <div>
        <label htmlFor="customer-doc_type" className="block text-[11px] font-semibold text-slate-600">Tipo Doc</label>
        <CustomSelect
          id="customer-doc_type"
          value={formData.doc_type}
          onChange={e => handleChange("doc_type", e.target.value)}
          className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs outline-none focus:border-teal-600"
        >
          <option value="RUC">RUC</option>
          <option value="DNI">DNI</option>
          <option value="CE">CE</option>
          <option value="OTRO">OTRO</option>
        </CustomSelect>
      </div>
      <div className="col-span-2">
        <label htmlFor="customer-doc_number" className="block text-[11px] font-semibold text-slate-600">
          Número de Documento {validating && <span className="text-teal-600 text-[10px]">Validando...</span>}
        </label>
        <input
          required
          id="customer-doc_number"
          minLength={documentoClienteRules(formData.doc_type).min}
          maxLength={documentoClienteRules(formData.doc_type).max}
          inputMode={documentoClienteRules(formData.doc_type).numeric ? "numeric" : "text"}
          pattern={documentoClienteRules(formData.doc_type).pattern}
          value={formData.doc_number}
          onChange={e => {
            const next = limpiarDocumentoCliente(formData.doc_type, e.target.value);
            handleChange("doc_number", next);
            checkDuplicateDoc(next);
          }}
          className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs outline-none focus:border-teal-600"
        />
      </div>
    </div>
    {duplicateWarning && (
      <div role="alert" className="space-y-2 rounded-lg bg-amber-50 p-3 text-[11px] font-medium text-amber-800"><p>{duplicateWarning}</p>{duplicateCandidates.map(candidate => <button key={candidate.id} type="button" disabled={busy} onClick={() => void chooseDuplicate(candidate)} className="block w-full rounded-lg border border-amber-200 bg-white px-3 py-2 text-left"><strong>{candidate.legal_name}</strong><span className="ml-2">{candidate.doc_number}</span><span className="ml-2 text-teal-700">Usar este cliente</span></button>)}</div>
    )}
    {fiscalStatus && <p className="rounded-lg bg-emerald-50 px-3 py-2 text-[11px] font-medium text-emerald-800">{fiscalStatus}</p>}
    <div>
      <label htmlFor="customer-legal_name" className="block text-[11px] font-semibold text-slate-600">Razón Social / Nombre Completo</label>
      <input
        required
        id="customer-legal_name"
        minLength={2}
        maxLength={255}
        value={formData.legal_name}
        onChange={e => handleChange("legal_name", e.target.value)}
        className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs outline-none focus:border-teal-600"
      />
    </div>
    {!quickMode && <div>
      <label htmlFor="customer-code" className="block text-[11px] font-semibold text-slate-600">Código Interno</label>
      <input
        id="customer-code"
        minLength={2}
        maxLength={64}
        value={formData.code}
        onChange={e => handleChange("code", e.target.value)}
        placeholder="Se asignará automáticamente si queda vacío"
        className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs outline-none focus:border-teal-600"
      />
    </div>}
  </fieldset>);
}
