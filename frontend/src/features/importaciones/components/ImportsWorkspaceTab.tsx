export type { RowErrorItem } from "../types/ImportsWorkspaceTab";
export type { ImportsWorkspaceTabProps } from "../types/ImportsWorkspaceTab";
import { useImportsWorkspaceTab } from "../hooks/useImportsWorkspaceTab";
import { PaginatedTable } from "../../../ui/components/PaginatedTable";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { CheckCircle2, ChevronRight, Download, Play, Upload } from "lucide-react";
import { writeDraft } from "../../../ui/drafts";
import { ImportsWorkspaceTabProps } from "../types/ImportsWorkspaceTab";
import { templates } from "../support/ImportsWorkspaceTab";

export function ImportsWorkspaceTab({ canWrite = true, permissions }: ImportsWorkspaceTabProps) {
  const { currentStep, setCurrentStep, targetEntity, setTargetEntity, file, setFile, staging, executing, progressPct, setProgressPct, job, setJob, setAttachmentId, inspection, setInspection, mapping, setMapping, corrections, setCorrections, history, mappingName, setMappingName, savedMappings, setSavedMappings, toast, targetPermissions, effectiveCanWrite, detectedColumns, rowErrors, handleDownloadTemplate, inspectFile, stageImport, executeImport, reset } = useImportsWorkspaceTab({ canWrite, permissions });
  return (
    <div id="scr-044-imports-workspace" data-testid="scr-044-imports-workspace" className="space-y-6">
      <NavbarSectionHeader view="imports" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">DATOS</span>
            <h1 className="text-xl font-bold text-slate-900">Importaciones Masivas y Asistente ETL</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">Carga verificada, validación por fila, preparación sin escritura y ejecución asíncrona controlada.</p>
        </div>
        <button onClick={handleDownloadTemplate} className="group inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50">
          <Download className="h-4 w-4 transition-transform group-hover:-translate-y-0.5" />
          Descargar Plantilla Modelo
        </button>
      </NavbarSectionHeader>

      <nav aria-label="Pasos de importación" className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
        {["Archivo", "Columnas", "Verificación", "Simulación (Dry-Run)", "Ejecución Atómica"].map((label, index) => {
          const step = index + 1;
          return <span key={label} className={`rounded-xl px-3.5 py-2 text-xs font-bold ${currentStep === step ? "bg-teal-700 text-white" : currentStep > step ? "bg-teal-50 text-teal-800" : "bg-slate-50 text-slate-500"}`}>{`${step}. ${label}`}</span>;
        })}
      </nav>

      {currentStep <= 3 && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
          <h2 className="text-base font-bold text-slate-900">Paso 1: Selección de Entidad y Archivo</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-xs font-semibold text-slate-700">Entidad de destino
              <CustomSelect value={targetEntity} onChange={(event) => { setTargetEntity(event.target.value as typeof targetEntity); setInspection(null); setAttachmentId(""); setCurrentStep(1); }} className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm">
                <option value="products" disabled={!targetPermissions.products}>Productos</option>
                <option value="customers" disabled={!targetPermissions.customers}>Clientes</option>
                <option value="inventory_adjustments" disabled={!targetPermissions.inventory_adjustments}>Ajustes de inventario</option>
              </CustomSelect>
            </label>
            <label className="text-xs font-semibold text-slate-700">Archivo CSV
              <input type="file" accept=".csv,text/csv" onChange={(event) => { setFile(event.target.files?.[0] || null); setInspection(null); setAttachmentId(""); setCurrentStep(2); }} className="mt-1.5 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" />
            </label>
          </div>
          <div onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); const dropped = event.dataTransfer.files[0]; if (!dropped?.name.toLowerCase().endsWith(".csv")) { toast.warning("Formato no admitido", "Arrastra un archivo CSV."); return; } setFile(dropped); setInspection(null); setAttachmentId(""); setCurrentStep(2); }} className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <Upload className="mx-auto h-8 w-8 text-slate-400 transition-transform hover:-translate-y-1" />
            <p className="mt-2 text-sm font-semibold text-slate-700">{file ? `${file.name} · ${(file.size / 1024).toFixed(1)} KB` : "Ningún archivo seleccionado"}</p>
            <p className="mt-1 text-xs text-slate-500">Arrastra un CSV o selecciónalo arriba. Detectamos coma, punto y coma, tabulación o barra, y codificación UTF-8 o Windows-1252.</p>
          </div>
          <div className="flex justify-end">
            <button onClick={() => inspection ? stageImport() : inspectFile()} disabled={!effectiveCanWrite || !targetPermissions[targetEntity] || !file || staging} className="group inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
              <ChevronRight className={`h-4 w-4 ${staging ? "animate-pulse" : "transition-transform group-hover:translate-x-1"}`} />
              {staging ? "Verificando archivo..." : inspection ? "Verificar y simular" : "Leer columnas del archivo"}
            </button>
          </div>
          {inspection && <section className="space-y-3 rounded-xl border p-4"><h3 className="text-sm font-bold">Mapear columnas</h3><p className="text-xs text-slate-500">{inspection.total_rows} filas · Separador: {inspection.delimiter === "\t" ? "tabulación" : inspection.delimiter} · Codificación: {inspection.encoding}</p><div className="grid gap-3 sm:grid-cols-2">{templates[targetEntity].split("\r\n")[0].split(",").map(column => <label key={column} className="text-xs font-semibold">{column}<CustomSelect value={mapping[column] || ""} onChange={event => setMapping(previous => { const next = { ...previous }; if (event.target.value) next[column] = event.target.value; else delete next[column]; return next; })} className="mt-1 w-full rounded-xl border p-2"><option value="">Seleccionar columna de origen</option>{inspection.columns.map(source => <option key={source} value={source}>{source}</option>)}</CustomSelect></label>)}</div><div className="flex flex-wrap gap-2"><input aria-label="Nombre de plantilla de columnas" value={mappingName} onChange={event => setMappingName(event.target.value)} placeholder="Nombre de esta plantilla" className="rounded-xl border p-2 text-xs" /><button type="button" disabled={!mappingName.trim()} onClick={() => { const next = { ...savedMappings, [`${targetEntity}:${mappingName.trim()}`]: mapping }; setSavedMappings(next); writeDraft("salesia_import_mappings", next); toast.success("Plantilla guardada", "Podrás reutilizar las columnas en la próxima carga."); }} className="rounded-xl border p-2 text-xs disabled:opacity-40">Guardar plantilla</button><CustomSelect aria-label="Usar plantilla de columnas" value="" onChange={event => setMapping(savedMappings[event.target.value] || {})} className="rounded-xl border p-2 text-xs"><option value="">Usar plantilla guardada</option>{Object.keys(savedMappings).filter(key => key.startsWith(`${targetEntity}:`)).map(key => <option key={key} value={key}>{key.split(":").slice(1).join(":")}</option>)}</CustomSelect></div></section>}
        </section>
      )}

      {currentStep === 4 && job?.result && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
          <div><h2 className="text-base font-bold text-slate-900">Resultado de la simulación</h2><p className="mt-1 text-xs text-slate-500">El trabajo está preparado y todavía no escribió registros del negocio.</p></div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-200 p-4"><span className="text-xs text-slate-500">Total</span><p className="text-2xl font-bold">{job.result.total_rows}</p></div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4"><span className="text-xs text-emerald-800">Válidas</span><p className="text-2xl font-bold text-emerald-900">{job.result.valid_rows}</p></div>
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4"><span className="text-xs text-rose-800">Observadas</span><p className="text-2xl font-bold text-rose-900">{job.result.invalid_rows}</p></div>
          </div>
          {detectedColumns.length > 0 && <p className="text-xs text-slate-600"><strong>Columnas detectadas:</strong> {detectedColumns.join(", ")}</p>}
          {job.result.is_duplicate_file && <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">El contenido coincide con un archivo importado anteriormente. La ejecución permanece bloqueada para evitar duplicados.</div>}
          {rowErrors.length > 0 && (
            <div className="pagination-shell"><PaginatedTable className="w-full text-left text-xs"><thead className="bg-slate-50 text-slate-500"><tr><th className="px-4 py-2">Fila</th><th className="px-4 py-2">Campo</th><th className="px-4 py-2">Motivo</th></tr></thead><tbody className="divide-y divide-slate-100">{rowErrors.map((error, index) => <tr key={`${error.row_number}-${error.field}-${index}`}><td className="px-4 py-2 font-mono">{error.row_number}</td><td className="px-4 py-2 font-mono">{error.field}</td><td className="px-4 py-2 text-rose-700">{error.reason}</td></tr>)}</tbody></PaginatedTable></div>
          )}
          {!!rowErrors.length && <section className="space-y-3 rounded-xl border border-rose-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-bold">Corregir filas observadas</h3><button type="button" onClick={() => { const lines = [["fila", "campo", "valor", "error"], ...rowErrors.map(error => [String(error.row_number), error.field, job.result?.rejected_rows?.find(row => row.row_number === error.row_number)?.values[error.field] || "", error.reason])]; const csv = lines.map(line => line.map(value => `"${value.replace(/"/g, '""')}"`).join(",")).join("\r\n"); const url = URL.createObjectURL(new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8" })); const anchor = document.createElement("a"); anchor.href = url; anchor.download = "filas_observadas.csv"; anchor.click(); URL.revokeObjectURL(url); }} className="rounded-xl border p-2 text-xs">Descargar errores</button></div><div className="max-h-72 space-y-3 overflow-y-auto">{job.result.rejected_rows?.map(row => <fieldset key={row.row_number} className="rounded-xl border p-3"><legend className="px-1 text-xs font-bold">Fila {row.row_number}</legend><div className="grid gap-2 sm:grid-cols-2">{Object.entries(row.values).map(([column, original]) => <label key={column} className="text-xs">{column}<input value={corrections[String(row.row_number)]?.[column] ?? original} onChange={event => setCorrections(previous => ({ ...previous, [String(row.row_number)]: { ...(previous[String(row.row_number)] || row.values), [column]: event.target.value } }))} className="mt-1 w-full rounded-lg border p-2" /></label>)}</div></fieldset>)}</div><button type="button" disabled={staging || !Object.keys(corrections).length} onClick={() => stageImport(true)} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-40">Guardar correcciones y volver a validar</button><p className="text-xs text-slate-500">Se crea una nueva simulación vinculada a la original para conservar la trazabilidad.</p></section>}
          <div className="flex justify-between"><button onClick={reset} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold">Cambiar archivo</button><button onClick={() => setCurrentStep(5)} disabled={job.result.valid_rows === 0 || job.result.is_duplicate_file} className="rounded-xl bg-teal-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">Continuar a ejecución</button></div>
        </section>
      )}

      {currentStep === 5 && job && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
          <h2 className="text-base font-bold text-slate-900">Ejecución del trabajo</h2>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><div className="flex justify-between text-xs font-semibold"><span>Estado: {job.status}</span><span>{progressPct}%</span></div><div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-teal-600 transition-all duration-300" style={{ width: `${progressPct}%` }} /></div></div>
          {job.status === "completed" ? (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900"><div className="flex items-start gap-3"><CheckCircle2 className="h-6 w-6" /><div><h3 className="font-bold">Importación completada</h3><p className="mt-1 text-xs">El worker confirmó el procesamiento de {job.result?.processed_rows ?? job.result?.imported ?? job.result?.valid_rows ?? 0} registros.</p></div></div><button onClick={reset} className="mt-4 rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white">Nueva importación</button></div>
          ) : (
            <div className="flex justify-end"><button onClick={executeImport} disabled={!effectiveCanWrite || !targetPermissions[targetEntity] || executing} className="group inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><Play className={`h-4 w-4 ${executing ? "animate-spin" : "transition-transform group-hover:scale-110"}`} />{executing ? "Procesando..." : "Confirmar importación"}</button></div>
          )}
        </section>
      )}
      {!!history.length && <section className="space-y-3 rounded-2xl border bg-white p-5"><h2 className="text-sm font-bold">Historial de mis importaciones</h2><div className="pagination-shell"><PaginatedTable className="w-full text-left text-xs"><thead><tr><th className="p-2">Fecha</th><th className="p-2">Entidad</th><th className="p-2">Estado</th><th className="p-2">Acción</th></tr></thead><tbody>{history.map(item => <tr key={item.job_id} className="border-t"><td className="p-2">{new Date(item.created_at).toLocaleString("es-PE", { timeZone: "America/Lima" })}</td><td className="p-2">{{ products: "Productos", customers: "Clientes", inventory_adjustments: "Ajustes de inventario" }[item.target_entity]}</td><td className="p-2">{item.status}</td><td className="p-2"><button type="button" onClick={() => { setJob(item); setTargetEntity(item.target_entity); setProgressPct(item.progress_pct); setCorrections({}); setCurrentStep(item.status === "staged" ? 4 : 5); }} className="font-semibold text-teal-700 underline">{item.status === "staged" ? "Retomar simulación" : "Consultar ejecución"}</button></td></tr>)}</tbody></PaginatedTable></div></section>}
    </div>
  );
}
