import "./numbering.css";
import type { useCompanySettingsWorkspaceTab } from "../../hooks/useCompanySettingsWorkspaceTab";
import { Calculator } from "lucide-react";
import { CompanySettingsWorkspaceTabProps } from "../../types/CompanySettingsWorkspaceTab";

export function SeccionNumbering({ sequences, handleReserveSequence, canWrite, saving, newSeriesCode, setNewSeriesCode, inputClass }: { sequences: ReturnType<typeof useCompanySettingsWorkspaceTab>["sequences"]; handleReserveSequence: ReturnType<typeof useCompanySettingsWorkspaceTab>["handleReserveSequence"]; saving: ReturnType<typeof useCompanySettingsWorkspaceTab>["saving"]; newSeriesCode: ReturnType<typeof useCompanySettingsWorkspaceTab>["newSeriesCode"]; setNewSeriesCode: ReturnType<typeof useCompanySettingsWorkspaceTab>["setNewSeriesCode"]; inputClass: ReturnType<typeof useCompanySettingsWorkspaceTab>["inputClass"] } & { canWrite: NonNullable<CompanySettingsWorkspaceTabProps["canWrite"]> }) {
  return (<div className="settings-numbering space-y-6">
    <section className="numbering-panel space-y-5">
      <div className="numbering-heading flex items-center justify-between">
        <div>
          <h2 className="numbering-title font-bold">Series y Correlativos de Documentos</h2>
          <p className="numbering-description text-xs">Control de secuencias oficiales emitidas en base de datos.</p>
        </div>
        <span className="numbering-badge">
          Autoincremento atómico
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {sequences.map(sequence => (
          <article key={sequence.series} className="numbering-sequence">
            <div className="flex items-center justify-between">
              <span className="numbering-series-name text-xs font-bold uppercase tracking-wider">
                Serie {sequence.series}
              </span>
              <button
                type="button"
                onClick={() => void handleReserveSequence(sequence.series)}
                disabled={!canWrite || saving}
                className="numbering-reserve"
              >
                +1 Reservar
              </button>
            </div>
            <p className="numbering-current mt-2 font-mono text-xl font-bold">
              {sequence.series}-{String(sequence.value).padStart(8, "0")}
            </p>
            <p className="numbering-description mt-1 text-xs">Último correlativo registrado</p>
          </article>
        ))}
        {sequences.length === 0 && (
          <div className="numbering-empty col-span-full p-6 text-center text-sm">
            No hay series creadas todavía.
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (newSeriesCode.trim()) void handleReserveSequence(newSeriesCode);
        }}
        className="numbering-form space-y-3"
      >
        <h3 className="numbering-form-title text-xs font-bold uppercase tracking-wider">
          Inicializar o Reservar Nueva Serie
        </h3>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="numbering-label flex-1 text-xs font-semibold">
            Código de serie (ejemplo: F001, B001, NV01, COT-1)
            <input
              required
              maxLength={16}
              value={newSeriesCode}
              onChange={event => setNewSeriesCode(event.target.value.toUpperCase())}
              disabled={!canWrite || saving}
              placeholder="F001"
              className={`${inputClass} numbering-code-input`}
            />
          </label>
          <button
            type="submit"
            disabled={!canWrite || saving || !newSeriesCode.trim()}
            className="numbering-submit inline-flex items-center justify-center gap-2"
          >
            <Calculator className="h-4 w-4" />
            Inicializar y Reservar Siguiente
          </button>
        </div>
      </form>
    </section>
  </div>);
}
