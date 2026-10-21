import { InfoTooltip } from "../InfoTooltip";
import React from "react";
import { TrendUpIcon, TrendDownIcon } from "../../icons/index";

export interface KpiCardProps {
  title: string;
  value: string | number;
  delta?: string;
  isPositiveDelta?: boolean;
  icon?: React.ReactNode;
  unit?: string;
  period?: string;
  cutoffDate?: string;
  comparisonCurrent?: number;
  comparisonBase?: number;
  definitionTooltip?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  delta,
  isPositiveDelta = true,
  icon,
  unit,
  period,
  cutoffDate,
  comparisonCurrent,
  comparisonBase,
  definitionTooltip
}) => {
  let computedDelta = delta;
  let computedPositive = isPositiveDelta;

  if (comparisonCurrent !== undefined && comparisonBase !== undefined) {
    if (comparisonBase === 0) {
      computedDelta = "N/C (No calculable)";
      computedPositive = true;
    } else {
      const pct = ((comparisonCurrent - comparisonBase) / comparisonBase) * 100;
      computedDelta = `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
      computedPositive = pct >= 0;
    }
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
      <div className="flex justify-between items-start text-slate-400">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider">{title}</span>
          {definitionTooltip && (
            <InfoTooltip title={title} description={definitionTooltip} />
          )}
        </div>
        {icon && <div className="text-blue-400 p-2 bg-slate-800/60 rounded-xl">{icon}</div>}
      </div>
      <div className="mt-3">
        <div className="flex items-baseline gap-1.5">
          <span className="text-2xl font-black text-white tracking-tight tabular-nums">
            {value}
          </span>
          {unit && <span className="text-xs text-slate-400 font-semibold">{unit}</span>}
        </div>
        {computedDelta && (
          <div
            className={`flex items-center gap-1 text-xs mt-1.5 font-medium ${computedDelta.startsWith("N/C")
              ? "text-slate-400"
              : computedPositive
                ? "text-emerald-400"
                : "text-rose-400"
              }`}
          >
            {computedDelta.startsWith("N/C") ? null : computedPositive ? (
              <TrendUpIcon size={14} />
            ) : (
              <TrendDownIcon size={14} />
            )}
            <span>{computedDelta}</span>
          </div>
        )}
        {(period || cutoffDate) && (
          <div className="flex justify-between text-[10px] text-slate-500 mt-2 border-t border-slate-800/60 pt-1.5">
            {period && <span>{`Periodo: ${period}`}</span>}
            {cutoffDate && <span>{`Corte: ${cutoffDate}`}</span>}
          </div>
        )}
      </div>
    </div>
  );
};
