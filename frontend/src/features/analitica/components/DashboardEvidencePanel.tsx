import { useEffect, useState } from "react";
import { apiClient } from "../../../api/client";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";

const titles: Record<string, string> = { revenue: "Ventas que respaldan la facturación", margin: "Líneas que respaldan el margen comercial", costs: "Líneas de venta con costo cero", collections: "Cobros recibidos o verificados", receivables: "Cuentas con importes vencidos", installments: "Cronogramas pendientes de conciliación", payables: "Obligaciones vencidas", payable_origins: "Obligaciones sin sede identificada", funds: "Cuentas de custodia", inventory_cost: "Productos con existencias sin costo promedio", inventory: "Productos sin disponibilidad", unassigned: "Ventas sin vendedor asignado" };
const destinations: Record<string, string[]> = { revenue: ["sales"], margin: ["sales"], costs: ["sales"], collections: ["receivables"], receivables: ["receivables"], installments: ["receivables"], payables: ["payables"], payable_origins: ["payables"], funds: ["cash"], inventory_cost: ["inventory"], inventory: ["inventory"], unassigned: ["sales"] };

export function hasDashboardEvidence(view: string) {
  if (view === "sales") return false;
  const key = new URLSearchParams(window.location.search).get("dashboard_evidence") || "";
  return destinations[key]?.includes(view) ?? false;
}

type Evidence = { items: Record<string, string>[]; total_count: number; scope_note: string; as_of: string; timezone: string; currency: string; period: string; branch_id: string | null; category: string | null };

export function DashboardEvidencePanel({ onBack, onOpenModule }: { onBack: () => void; onOpenModule: () => void }) {
  const context = window.location.search;
  const [data, setData] = useState<Evidence | null>(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const params = new URLSearchParams(context);
  const key = params.get("dashboard_evidence") || "";
  const expected = params.get("dashboard_expected");
  useEffect(() => {
    const controller = new AbortController();
    const source = new URLSearchParams(context);
    const query = new URLSearchParams({ key: source.get("dashboard_evidence") || "" });
    for (const name of ["period", "currency", "category", "as_of"]) { const value = source.get(`dashboard_${name}`); if (value) query.set(name, value); }
    const branch = source.get("dashboard_branch");
    if (branch) query.set("branch_id", branch);
    setData(null); setError(""); setPage(0);
    apiClient.request<Evidence>(`/api/v1/dashboard/evidence?${query}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) setData(result); }).catch(failure => { if (!controller.signal.aborted) setError(String(failure?.detail || failure?.message || "No se pudo consultar el respaldo.")); });
    return () => controller.abort();
  }, [context, revision]);
  const columns = Array.from(new Set(data?.items.flatMap(row => Object.keys(row)) || []));
  return <section className="min-h-0 space-y-3 overflow-auto rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"><header className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-base font-bold text-slate-900 dark:text-white">{titles[key] || "Respaldo del dashboard"}</h1><div className="flex gap-3 text-xs font-semibold text-teal-700 dark:text-teal-400"><button type="button" onClick={onBack}>Volver al dashboard</button><button type="button" onClick={onOpenModule}>Salir del respaldo y abrir módulo</button></div></header>{error ? <div role="alert" className="text-sm text-rose-600">{error}<button type="button" className="ml-3 underline" onClick={() => setRevision(value => value + 1)}>Reintentar</button></div> : !data ? <p role="status" className="text-sm text-slate-500">Consultando registros de respaldo…</p> : <><p className="flex flex-wrap items-center gap-2 text-xs text-slate-500">{data.total_count} {data.total_count === 1 ? "registro" : "registros"} · {data.currency} · Período: {data.period} · {data.branch_id ? `Sede: ${data.branch_id}` : "Todas las sedes"}{data.category ? ` · Categoría: ${data.category}` : ""}<InfoTooltip interactive title="Alcance del respaldo" description={`${data.scope_note} Corte de referencia: ${new Date(data.as_of).toLocaleString("es-PE", { timeZone: data.timezone })} · ${data.timezone}. El estado de los documentos y los saldos actuales pueden cambiar después de consultar el dashboard; no se simula un cierre histórico.`} /></p>{expected !== null && Number(expected) !== data.total_count && <p role="status" className="text-sm text-amber-600">El dashboard mostraba {expected} registros y ahora hay {data.total_count}. Los datos cambiaron desde la consulta; vuelve al dashboard para actualizarlo.</p>}<div className="overflow-x-auto">{data.items.length ? <table className="w-full text-left text-sm"><thead><tr>{columns.map(column => <th key={column} className="whitespace-nowrap border-b border-slate-200 px-3 py-2 font-semibold dark:border-slate-700">{column.replace(/_/g, " ")}</th>)}</tr></thead><tbody>{data.items.slice(page * 25, (page + 1) * 25).map(row => <tr key={row.id}>{columns.map(column => <td key={column} className="whitespace-nowrap border-b border-slate-100 px-3 py-2 tabular-nums dark:border-slate-800">{row[column] || "—"}</td>)}</tr>)}</tbody></table> : <p className="py-4 text-sm text-slate-500">Sin registros para este respaldo.</p>}</div>{data.total_count > 25 && <nav aria-label="Páginas del respaldo" className="flex items-center gap-3 text-sm"><button type="button" disabled={!page} onClick={() => setPage(value => value - 1)}>Anterior</button><span>{page + 1} / {Math.ceil(data.total_count / 25)}</span><button type="button" disabled={(page + 1) * 25 >= data.total_count} onClick={() => setPage(value => value + 1)}>Siguiente</button></nav>}</>}</section>;
}
