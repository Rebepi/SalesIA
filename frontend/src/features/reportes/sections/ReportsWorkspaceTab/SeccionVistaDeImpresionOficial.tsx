import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { Printer } from "lucide-react";

export function SeccionVistaDeImpresionOficial({ setPrintableRun, branding, printableRun }: { setPrintableRun: ReturnType<typeof useReportsWorkspaceTab>["setPrintableRun"]; branding: ReturnType<typeof useReportsWorkspaceTab>["branding"]; printableRun: NonNullable<ReturnType<typeof useReportsWorkspaceTab>["printableRun"]> }) {
  return (<div className="fixed inset-0 z-50 flex flex-col bg-white p-8 text-slate-900 print:m-0 print:p-0">
    <div className="flex items-center justify-between border-b border-slate-300 pb-4 print:hidden">
      <h2 className="text-base font-bold">Vista de Impresión Oficial</h2>
      <div className="flex gap-2">
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-4 py-2 text-xs font-bold text-white shadow"
        >
          <Printer className="h-4 w-4" />
          Imprimir ahora
        </button>
        <button
          onClick={() => setPrintableRun(null)}
          className="rounded-xl border border-slate-300 px-4 py-2 text-xs font-bold text-slate-700"
        >
          Cerrar
        </button>
      </div>
    </div>

    <div className="mt-6 space-y-4">
      <div className="flex items-center justify-between border-b-2 border-teal-800 pb-4">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider text-teal-900">
            {branding?.legal_name || branding?.company_name || "SALESIA ENTERPRISE S.A.C."}
          </h1>
          <p className="text-xs font-semibold text-slate-600">
            RUC: {branding?.tax_id || "20601234567"} · Versión Plantilla: {branding?.template_version || "v1.2"}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-mono font-bold text-slate-800">EXP-RUN: {printableRun.run_id}</p>
          <p className="text-xs text-slate-500">Corte: {new Date(printableRun.cutoff_at).toLocaleString()}</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-bold text-slate-700">Reporte: {printableRun.template_code}</p>
            <p className="text-xs text-slate-600">Filas certificadas: {printableRun.row_count}</p>
          </div>
          {String(printableRun.parameters.status) === "cancelled" ? (
            <span className="rounded border-2 border-red-600 px-3 py-1 text-sm font-black text-red-600">
              DOCUMENTO ANULADO
            </span>
          ) : (
            <span className="rounded border border-emerald-600 px-2 py-0.5 text-xs font-bold text-emerald-700">
              ESTADO: {String(printableRun.parameters.status || "CONFIRMADO").toUpperCase()}
            </span>
          )}
        </div>
      </div>

      <div className="py-8 text-center text-xs text-slate-500">
        <p>Sello de Seguridad Criptográfico SHA-256:</p>
        <p className="mt-1 font-mono font-bold text-slate-800">{printableRun.sha256_hash}</p>
      </div>

      <footer className="mt-12 border-t border-slate-300 pt-4 text-center text-[10px] text-slate-500">
        {branding?.footer_text || "Documento generado por SalesIA Enterprise. Todos los derechos reservados."}
      </footer>
    </div>
  </div>);
}
