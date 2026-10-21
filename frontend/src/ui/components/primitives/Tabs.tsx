import React, { useState } from "react";
import type { TabItem } from "./TabItem";
import { Button } from "./Button";

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onTabChange: (id: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onTabChange }) => {
  const [pendingTabId, setPendingTabId] = useState<string | null>(null);

  const handleTabClick = (tabId: string) => {
    const current = tabs.find((t) => t.id === activeTab);
    if (current?.isDirty && tabId !== activeTab) {
      setPendingTabId(tabId);
    } else {
      onTabChange(tabId);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === "ArrowRight") {
      const nextIndex = (index + 1) % tabs.length;
      handleTabClick(tabs[nextIndex].id);
    } else if (e.key === "ArrowLeft") {
      const prevIndex = (index - 1 + tabs.length) % tabs.length;
      handleTabClick(tabs[prevIndex].id);
    } else if (e.key === "Home") {
      handleTabClick(tabs[0].id);
    } else if (e.key === "End") {
      handleTabClick(tabs[tabs.length - 1].id);
    }
  };

  return (
    <div className="w-full">
      <div
        role="tablist"
        aria-label="Pestañas de navegación"
        className="flex border-b border-slate-800 gap-2 mb-4 overflow-x-auto"
      >
        {tabs.map((tab, idx) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              role="tab"
              id={`tab-${tab.id}`}
              aria-controls={`panel-${tab.id}`}
              aria-selected={isActive}
              tabIndex={isActive ? 0 : -1}
              onClick={() => handleTabClick(tab.id)}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              className={`flex items-center gap-2 py-2.5 px-4 text-sm font-medium border-b-2 transition-all duration-150 whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${isActive
                ? "border-blue-500 text-blue-400 font-semibold"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
            >
              {tab.icon}
              {tab.label}
              {tab.isDirty && <span className="w-1.5 h-1.5 rounded-full bg-amber-400" title="Cambios sin guardar" />}
            </button>
          );
        })}
      </div>
      {pendingTabId && (
        <div role="alert" className="mb-4 p-3 rounded-xl bg-amber-950/60 border border-amber-500/40 text-xs text-amber-200 flex items-center justify-between">
          <span>Esta pestaña contiene cambios sin guardar. ¿Desea descartar y cambiar?</span>
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" onClick={() => setPendingTabId(null)}>
              Permanecer
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const target = pendingTabId;
                setPendingTabId(null);
                onTabChange(target);
              }}
            >
              Cambiar de pestaña
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
