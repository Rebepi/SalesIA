import { PaginatedTable } from "../../../ui/components/PaginatedTable";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Search } from "lucide-react";
import { apiClient, type ProblemDetails } from "../../../api/client";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";

export type VariableScaleType = "quantitative_continuous" | "quantitative_discrete" | "qualitative_nominal" | "qualitative_ordinal";

export interface VariableItem {
  id: string;
  name: string;
  label: string;
  scale: VariableScaleType;
  scale_label: string;
  data_type: string;
  source_table: string;
  description: string;
  allowed_operations: string[];
  sample_values: string[];
  summary: {
    mean?: string | null;
    median?: string | null;
    min?: string | null;
    max?: string | null;
    mode?: string | null;
    distinct_count: number;
    null_count: number;
    frequencies?: { value: string; count: number; pct: string }[];
  };
}

export interface VariablesDictionaryTabProps {
  canWrite?: boolean;
}

function problemMessage(error: unknown) {
  const problem = error as ProblemDetails;
  return problem?.detail || problem?.title || "No fue posible cargar el diccionario de variables.";
}

export function VariablesDictionaryTab({ canWrite: _canWrite = true }: VariablesDictionaryTabProps) {
  const [variables, setVariables] = useState<VariableItem[]>([]);
  const [selectedVarId, setSelectedVarId] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    apiClient.request<{ items: VariableItem[] }>("/api/v1/analytics/variables")
      .then((response) => {
        if (!active) return;
        if (response.items) {
          setVariables(response.items);
          setSelectedVarId((current) => response.items.some((item) => item.id === current) ? current : response.items[0]?.id || "");
        }
      })
      .catch((requestError) => {
        if (active) setError(problemMessage(requestError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const selectedVariable = variables.find((variable) => variable.id === selectedVarId) ?? null;
  const filteredVariables = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return variables;
    return variables.filter((variable) => [variable.name, variable.label, variable.scale_label, variable.source_table].some((value) => value.toLowerCase().includes(term)));
  }, [search, variables]);

  return (
    <div id="scr-035-variables-dictionary" data-testid="scr-035-variables-dictionary" className="space-y-6">
      <NavbarSectionHeader view="variables" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2"><span className="workspace-eyebrow">DATOS</span><h1 className="text-xl font-bold text-slate-900">Diccionario de Variables Estadísticas</h1></div>
          <p className="mt-1 text-sm text-slate-500">Clasificación por escala de medida y resumen calculado con los datos operativos de la empresa activa.</p>
        </div>

      </NavbarSectionHeader>

      {error && <div role="alert" className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"><AlertTriangle className="h-5 w-5" /><span>{error}</span></div>}
      {loading && variables.length === 0 && <div role="status" className="rounded-2xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">Cargando variables y resúmenes…</div>}
      {!loading && variables.length === 0 && !error && <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center text-sm text-slate-600">No hay variables operativas disponibles.</div>}

      {variables.length > 0 && <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <aside className="space-y-4 lg:col-span-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="relative"><Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" /><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar variable…" className="w-full rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-sm text-slate-800" /></div>
            <nav className="mt-4 space-y-1.5" aria-label="Variables del sistema">
              {filteredVariables.map((variable) => <button key={variable.id} onClick={() => setSelectedVarId(variable.id)} className={`w-full rounded-xl px-3.5 py-2.5 text-left transition hover:-translate-y-0.5 ${selectedVariable?.id === variable.id ? "bg-teal-700 text-white shadow-sm" : "text-slate-800 hover:bg-slate-100"}`}><div className="flex items-center justify-between gap-2"><span className={`text-sm font-semibold leading-snug ${selectedVariable?.id === variable.id ? "text-white" : "text-slate-800"}`}>{variable.label}</span><span className={`shrink-0 rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${selectedVariable?.id === variable.id ? "bg-teal-800 text-teal-100" : "bg-slate-100 text-slate-600"}`}>{variable.scale.startsWith("quant") ? "Cuantitativa" : "Cualitativa"}</span></div></button>)}
              {filteredVariables.length === 0 && <p className="px-3 py-6 text-center text-xs text-slate-500">No hay coincidencias.</p>}
            </nav>
          </div>
        </aside>

        {selectedVariable && <main className="space-y-6 lg:col-span-8">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-4">
              <div><span className="font-mono text-xs font-bold text-teal-700">{selectedVariable.name}</span><h2 className="text-xl font-bold text-slate-900">{selectedVariable.label}</h2><p className="mt-1 text-xs text-slate-500">{selectedVariable.description}</p></div>
              <div className="text-right"><span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${selectedVariable.scale === "qualitative_nominal" ? "border-amber-300 bg-amber-100 text-amber-800" : selectedVariable.scale === "qualitative_ordinal" ? "border-purple-300 bg-purple-100 text-purple-800" : "border-emerald-300 bg-emerald-100 text-emerald-800"}`}>{selectedVariable.scale_label}</span><p className="mt-1 font-mono text-[11px] text-slate-400">{selectedVariable.data_type} · {selectedVariable.source_table}</p></div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <SummaryCard label="Media" value={selectedVariable.summary.mean ?? "No aplicable"} />
              <SummaryCard label="Mediana" value={selectedVariable.summary.median ?? "No aplicable"} />
              <SummaryCard label="Moda" value={selectedVariable.summary.mode ?? "Sin datos"} />
              <SummaryCard label="Valores distintos" value={String(selectedVariable.summary.distinct_count)} />
            </div>

            {selectedVariable.summary.frequencies && selectedVariable.summary.frequencies.length > 0 && <div className="mt-6"><div className="flex items-center gap-2"><h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Distribución de Frecuencia</h3><InfoTooltip title="Distribución de frecuencia" description="Indica cuántas veces aparece cada valor observado y qué porcentaje representa en la muestra." /></div><div className="mt-3 pagination-shell"><PaginatedTable className="w-full text-left text-xs"><thead className="bg-slate-50 font-semibold uppercase text-slate-600"><tr><th className="px-4 py-2.5">Valor</th><th className="px-4 py-2.5">Frecuencia</th><th className="px-4 py-2.5">Porcentaje</th></tr></thead><tbody className="divide-y divide-slate-100">{selectedVariable.summary.frequencies.map((frequency) => <tr key={frequency.value} className="hover:bg-slate-50"><td className="px-4 py-2.5 font-mono font-medium text-slate-900">{selectedVariable.name === "customer_id" ? `${frequency.value.slice(0, 8)}…` : frequency.value}</td><td className="px-4 py-2.5 tabular-nums text-slate-700">{frequency.count}</td><td className="px-4 py-2.5 tabular-nums font-semibold text-teal-700">{frequency.pct}%</td></tr>)}</tbody></PaginatedTable></div></div>}

            <div className="mt-6 grid gap-4 border-t border-slate-100 pt-4 sm:grid-cols-2">
              <div><p className="text-xs font-semibold uppercase text-slate-500">Operaciones permitidas:</p><div className="mt-2 flex flex-wrap gap-2">{selectedVariable.allowed_operations.map((operation) => <span key={operation} className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-800">{operation}</span>)}</div></div>
              <div><p className="text-xs font-semibold uppercase text-slate-500">Muestra observada</p><div className="mt-2 flex flex-wrap gap-2">{selectedVariable.sample_values.length > 0 ? selectedVariable.sample_values.map((value, index) => <code key={`${value}-${index}`} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-700">{value}</code>) : <span className="text-xs text-slate-500">Sin observaciones registradas.</span>}</div></div>
            </div>
          </div>
        </main>}
      </div>}
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  const descriptions: Record<string, string> = { Media: "Promedio aritmético de los valores numéricos observados.", Mediana: "Valor central de la muestra ordenada; es resistente a valores extremos.", Moda: "Valor que aparece con mayor frecuencia en la muestra.", "Valores distintos": "Cantidad de valores únicos observados para la variable." };
  return <div className="rounded-xl border border-slate-100 bg-slate-50 p-3.5"><span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase text-slate-500">{label}<InfoTooltip title={label} description={descriptions[label] || "Resumen calculado para la variable seleccionada."} /></span><p className="mt-1 break-words text-lg font-bold text-slate-900">{value}</p></div>;
}
