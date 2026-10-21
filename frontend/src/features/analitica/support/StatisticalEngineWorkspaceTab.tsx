import { type ProblemDetails } from "../../../api/client";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";

export function problemMessage(error: unknown): string {
  const problem = error as ProblemDetails;
  return problem?.detail || problem?.title || "No fue posible completar el cálculo estadístico.";
}

export function Metric({ label, value, detail, accent = false, compact = false }: { label: string; value: string; detail: string; accent?: boolean; compact?: boolean }) {
  return <div className={`rounded-2xl border p-5 shadow-sm ${accent ? "border-teal-200 bg-teal-50/50" : "border-slate-200 bg-white"}`}><span className={`flex items-center gap-1.5 text-xs font-semibold uppercase ${accent ? "text-teal-800" : "text-slate-500"}`}>{label}<InfoTooltip title={label} description={detail} /></span><p className={`mt-1.5 font-bold ${compact ? "text-base" : "text-2xl"} ${accent ? "text-teal-950" : "text-slate-900"}`}>{value}</p><span className={`text-xs ${accent ? "text-teal-700" : "text-slate-400"}`}>{detail}</span></div>;
}

export function TraceRow({ label, value, accent = false, strong = false }: { label: string; value: string; accent?: boolean; strong?: boolean }) {
  return <tr><th scope="row" className="w-1/3 py-2.5 font-semibold text-slate-600">{label}</th><td className={`py-2.5 font-mono ${accent ? "text-teal-800" : "text-slate-900"} ${strong ? "font-bold" : ""}`}>{value}</td></tr>;
}
