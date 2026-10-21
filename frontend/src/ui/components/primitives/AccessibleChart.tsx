import React, { useState } from "react";
import { Button } from "./Button";

export interface ChartPoint {
  label: string;
  value: number;
}

export const AccessibleChart: React.FC<{
  title: string;
  points: ChartPoint[];
  unit: string;
  description: string;
}> = ({ title, points, unit, description }) => {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  const maxValue = Math.max(...points.map((p) => p.value), 1);

  const downloadCsv = () => {
    const csvContent = "data:text/csv;charset=utf-8," +
      ["Categoría,Valor", ...points.map((p) => `"${p.label}",${p.value}`)].join("\n");
    const encoded = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encoded);
    link.setAttribute("download", `${title.replace(/\s+/g, "_")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4 text-left">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-bold text-white text-base">{title}</h4>
          <p className="text-xs text-slate-400">{description}</p>
        </div>
        <Button size="sm" variant="outline" onClick={downloadCsv}>
          Exportar CSV
        </Button>
      </div>

      <div role="img" aria-label={`${title}: ${description}`} className="space-y-2">
        {points.map((pt) => {
          const pct = Math.round((pt.value / maxValue) * 100);
          return (
            <div key={pt.label} className="text-xs">
              <div className="flex justify-between text-slate-300 mb-1">
                <span>{pt.label}</span>
                <span className="font-mono font-semibold">{`${pt.value} ${unit}`}</span>
              </div>
              <div
                tabIndex={0}
                onFocus={() => setActiveTooltip(`${pt.label}: ${pt.value} ${unit}`)}
                onBlur={() => setActiveTooltip(null)}
                className="w-full bg-slate-800 h-3 rounded-full overflow-hidden focus:ring-2 focus:ring-blue-500"
              >
                <div className="bg-blue-500 h-full transition-all duration-300" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      {activeTooltip && (
        <div role="status" className="p-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-blue-300">
          Detalle: {activeTooltip}
        </div>
      )}

      <div className="border-t border-slate-800 pt-3">
        <span className="text-xs font-semibold text-slate-400 mb-2 block">Tabla accesible alternativa:</span>
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="text-slate-400 border-b border-slate-800">
              <th className="py-1">Categoría</th>
              <th className="py-1 text-right">Valor ({unit})</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {points.map((pt) => (
              <tr key={pt.label}>
                <td className="py-1 text-slate-300">{pt.label}</td>
                <td className="py-1 text-right font-mono text-slate-200">{pt.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
