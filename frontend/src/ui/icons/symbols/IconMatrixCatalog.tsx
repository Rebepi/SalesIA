import React from "react";
import { ICON_DEPENDENCY_REGISTRY, IconRegistryEntry } from "../registry";
import { ICON_COMPONENT_MAP } from "./ICON_COMPONENT_MAP";
import { FallbackCatalogIcon } from "./FallbackCatalogIcon";

export const IconMatrixCatalog: React.FC<{ limit?: number }> = ({ limit = 55 }) => {
  const items = ICON_DEPENDENCY_REGISTRY.slice(0, limit);

  return (
    <div className="space-y-6 overflow-x-auto">
      <div className="min-w-[800px] border border-slate-700/60 rounded-2xl overflow-hidden bg-slate-900/60 shadow-xl">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
              <th className="p-3">ID / Ficha</th>
              <th className="p-3">Nombre</th>
              <th className="p-3 text-center">Normal</th>
              <th className="p-3 text-center">Hover</th>
              <th className="p-3 text-center">Foco</th>
              <th className="p-3 text-center">Pressed</th>
              <th className="p-3 text-center">Disabled</th>
              <th className="p-3 text-center">Loading</th>
              <th className="p-3 text-center">Reducido</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {items.map((entry: IconRegistryEntry) => {
              const Comp = ICON_COMPONENT_MAP[entry.id] ?? FallbackCatalogIcon;
              return (
                <tr key={entry.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-3 font-mono font-bold text-blue-400">{entry.id}</td>
                  <td className="p-3">
                    <div className="font-semibold text-slate-200">{entry.name}</div>
                    <div className="text-[10px] text-slate-400 truncate max-w-[180px]">{entry.gestureType} ({entry.durationMs}ms)</div>
                  </td>
                  <td className="p-3 text-center">
                    <span className="inline-flex p-1.5 rounded-lg bg-slate-800/40">
                      <Comp size={18} state="rest" />
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className="inline-flex p-1.5 rounded-lg bg-slate-800/40">
                      <Comp size={18} state="hover" />
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className="inline-flex p-1.5 rounded-lg bg-slate-800/40">
                      <Comp size={18} state="focus" />
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className="inline-flex p-1.5 rounded-lg bg-slate-800/40">
                      <Comp size={18} state="pressed" />
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className="inline-flex p-1.5 rounded-lg bg-slate-800/40">
                      <Comp size={18} state="disabled" />
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className="inline-flex p-1.5 rounded-lg bg-slate-800/40">
                      <Comp size={18} state="loading" />
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className="inline-flex p-1.5 rounded-lg bg-slate-800/40">
                      <Comp size={18} state="hover" reducedMotion={true} />
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
