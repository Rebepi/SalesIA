import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { Play, Eye, Search } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";
import { writeDraft } from "../../../../ui/drafts";

export function SeccionCatalog({ catalogSearch, setCatalogSearch, areas, setSelectedArea, selectedArea, onlyFavorites, setOnlyFavorites, filteredTemplates, templates, favoriteTemplates, setFavoriteTemplates, handleOpenPreview, canExport, handleOpenLaunch }: { catalogSearch: ReturnType<typeof useReportsWorkspaceTab>["catalogSearch"]; setCatalogSearch: ReturnType<typeof useReportsWorkspaceTab>["setCatalogSearch"]; areas: ReturnType<typeof useReportsWorkspaceTab>["areas"]; setSelectedArea: ReturnType<typeof useReportsWorkspaceTab>["setSelectedArea"]; selectedArea: ReturnType<typeof useReportsWorkspaceTab>["selectedArea"]; onlyFavorites: ReturnType<typeof useReportsWorkspaceTab>["onlyFavorites"]; setOnlyFavorites: ReturnType<typeof useReportsWorkspaceTab>["setOnlyFavorites"]; filteredTemplates: ReturnType<typeof useReportsWorkspaceTab>["filteredTemplates"]; templates: ReturnType<typeof useReportsWorkspaceTab>["templates"]; favoriteTemplates: ReturnType<typeof useReportsWorkspaceTab>["favoriteTemplates"]; setFavoriteTemplates: ReturnType<typeof useReportsWorkspaceTab>["setFavoriteTemplates"]; handleOpenPreview: ReturnType<typeof useReportsWorkspaceTab>["handleOpenPreview"]; handleOpenLaunch: ReturnType<typeof useReportsWorkspaceTab>["handleOpenLaunch"] } & { canExport: NonNullable<{ canExport?: boolean }["canExport"]> }) {
  return (<section className="space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar reporte por código o nombre..."
            value={catalogSearch}
            onChange={e => setCatalogSearch(e.target.value)}
            className="w-72 rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-100"
          />
        </div>
        <div className="flex items-center gap-1 rounded-xl border border-slate-200 bg-white p-1">
          {areas.map(a => (
            <button
              key={a.key}
              onClick={() => setSelectedArea(a.key)}
              className={`rounded-lg px-3 py-1 text-xs font-semibold transition ${selectedArea === a.key ? "bg-teal-600 text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
                }`}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>
      <p className="text-xs text-slate-500">
        <label className="mr-3 inline-flex items-center gap-1"><input type="checkbox" checked={onlyFavorites} onChange={event => setOnlyFavorites(event.target.checked)} />Mis favoritos</label>Mostrando {filteredTemplates.length} de {templates.length} reportes certificados
      </p>
    </div>

    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {filteredTemplates.filter(template => !onlyFavorites || favoriteTemplates.includes(template.code)).map(tpl => (
        <article
          key={tpl.code}
          className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow-md"
        >
          <div>
            <div className="flex items-center justify-between gap-2">
              <span className="rounded-md border border-slate-200 bg-slate-100 px-2 py-0.5 text-xs font-mono font-medium text-slate-700">
                {tpl.code}
              </span>
              <span className="rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-semibold text-teal-700">
                {tpl.area}
              </span>
            </div>
            <div className="mt-3 flex items-start gap-2"><h2 className="text-base font-bold text-slate-900">{tpl.name}</h2><InfoTooltip align="right" title={tpl.name} description={tpl.objective} /></div>
            <p className="mt-1 text-xs leading-relaxed text-slate-600">{tpl.objective}</p>

            <div className="mt-4 space-y-2 border-t border-slate-100 pt-3 text-xs text-slate-600">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Campo fecha:</span>
                <span className="font-mono font-medium text-slate-800">{tpl.date_field}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Moneda:</span>
                <span className="font-medium text-slate-800">{tpl.currency_support}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Permiso requerido:</span>
                <span className="rounded bg-amber-50 px-1.5 py-0.5 font-mono text-amber-800">
                  {tpl.required_permission}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Formatos disponibles:</span>
                <div className="flex gap-1">
                  {tpl.allowed_formats.map(fmt => (
                    <span
                      key={fmt}
                      className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${fmt === "pdf"
                        ? "bg-red-100 text-red-800"
                        : fmt === "xlsx"
                          ? "bg-emerald-100 text-emerald-800"
                          : fmt === "csv"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-purple-100 text-purple-800"
                        }`}
                    >
                      {fmt}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-end gap-2 border-t border-slate-100 pt-3"><button type="button" aria-pressed={favoriteTemplates.includes(tpl.code)} onClick={() => { const codes = favoriteTemplates.includes(tpl.code) ? favoriteTemplates.filter(code => code !== tpl.code) : [...favoriteTemplates, tpl.code]; setFavoriteTemplates(codes); writeDraft("salesia_report_favorites", { codes }); }} className="mr-auto text-xs font-semibold text-amber-700">{favoriteTemplates.includes(tpl.code) ? "★ Favorito" : "☆ Guardar favorito"}</button>
            <button
              onClick={() => handleOpenPreview(tpl)}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline focus-visible:outline-teal-500"
            >
              <Eye className="h-3.5 w-3.5" />
              Vista previa
            </button>
            {canExport && <button
              onClick={() => handleOpenLaunch(tpl)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-800 focus-visible:outline focus-visible:outline-teal-500"
            >
              <Play className="h-3.5 w-3.5" />
              Generar
            </button>}
          </div>
        </article>
      ))}
    </div>
  </section>);
}
