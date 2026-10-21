import React, { useState } from "react";

export interface AccordionItem {
  id: string;
  title: string;
  content: React.ReactNode;
}

export const Accordion: React.FC<{ items: AccordionItem[] }> = ({ items }) => {
  const [openIds, setOpenIds] = useState<string[]>([]);

  const toggle = (id: string) => {
    setOpenIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  return (
    <div className="divide-y divide-slate-800 rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
      {items.map((item) => {
        const isOpen = openIds.includes(item.id);
        const headerId = `accordion-header-${item.id}`;
        const panelId = `accordion-panel-${item.id}`;
        return (
          <div key={item.id} className="text-left">
            <button
              id={headerId}
              aria-expanded={isOpen}
              aria-controls={panelId}
              onClick={() => toggle(item.id)}
              className="w-full py-3.5 px-4 flex justify-between items-center text-sm font-semibold text-slate-200 hover:bg-slate-800/40 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <span>{item.title}</span>
              <span
                className={`transition-transform duration-200 text-slate-400 ${isOpen ? "rotate-180" : ""
                  }`}
              >
                ▼
              </span>
            </button>
            {isOpen && (
              <div
                id={panelId}
                role="region"
                aria-labelledby={headerId}
                className="p-4 pt-1 text-sm text-slate-300 border-t border-slate-800/40 bg-slate-950/20"
              >
                {item.content}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
