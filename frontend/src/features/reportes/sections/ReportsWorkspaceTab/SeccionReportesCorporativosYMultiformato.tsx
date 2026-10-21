import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { NavbarSectionHeader } from "../../../../ui/components/NavbarSectionHeader";
import { Calendar, Clock, GitCompare, Layers, FileSpreadsheet } from "lucide-react";

export function SeccionReportesCorporativosYMultiformato({ branding, setActiveTab, activeTab, templates, runs, schedules }: { branding: ReturnType<typeof useReportsWorkspaceTab>["branding"]; setActiveTab: ReturnType<typeof useReportsWorkspaceTab>["setActiveTab"]; activeTab: ReturnType<typeof useReportsWorkspaceTab>["activeTab"]; templates: ReturnType<typeof useReportsWorkspaceTab>["templates"]; runs: ReturnType<typeof useReportsWorkspaceTab>["runs"]; schedules: ReturnType<typeof useReportsWorkspaceTab>["schedules"] }) {
  return (<NavbarSectionHeader view="reports" className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-600 text-white shadow-md shadow-teal-500/20">
          <FileSpreadsheet className="h-6 w-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Reportes Corporativos y Multiformato</h1>
            {branding && (
              <span className="rounded-md border border-teal-200 bg-teal-50 px-2 py-0.5 text-xs font-semibold text-teal-800">
                {branding.template_version}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-sm text-slate-500">
            Catálogo oficial certificado, generación asíncrona, exportación segura en PDF, XLSX, CSV y JSON con sellado criptográfico.
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">

      </div>
    </div>

    <nav aria-label="Secciones de reportes" className="flex flex-wrap gap-2">
      <button
        onClick={() => setActiveTab("catalog")}
        className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${activeTab === "catalog" ? "bg-teal-700 text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
          }`}
      >
        <Layers className="h-4 w-4" />
        Catálogo Oficial ({templates.length})
      </button>
      <button
        onClick={() => setActiveTab("runs")}
        className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${activeTab === "runs" ? "bg-teal-700 text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
          }`}
      >
        <Clock className="h-4 w-4" />
        Historial de Ejecuciones ({runs.length})
      </button>
      <button
        onClick={() => setActiveTab("schedules")}
        className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${activeTab === "schedules" ? "bg-teal-700 text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
          }`}
      >
        <Calendar className="h-4 w-4" />
        Programaciones Automáticas ({schedules.length})
      </button>
      <button
        onClick={() => setActiveTab("compare")}
        className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${activeTab === "compare" ? "bg-teal-700 text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
          }`}
      >
        <GitCompare className="h-4 w-4" />
        Comparación de Cortes
      </button>
    </nav>
  </NavbarSectionHeader>);
}
