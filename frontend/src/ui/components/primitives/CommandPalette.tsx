import React, { useState } from "react";
import { Button } from "./Button";

export interface CommandAction {
  id: string;
  title: string;
  category: string;
  shortcut?: string;
  isDestructive?: boolean;
  onExecute: () => void;
}

export const CommandPalette: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  actions: CommandAction[];
}> = ({ isOpen, onClose, actions }) => {
  const [filter, setFilter] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [confirmAction, setConfirmAction] = useState<CommandAction | null>(null);

  if (!isOpen) return null;

  const matched = actions.filter((a) => a.title.toLowerCase().includes(filter.toLowerCase()));

  const handleSelect = (action: CommandAction) => {
    if (action.isDestructive) {
      setConfirmAction(action);
    } else {
      action.onExecute();
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < matched.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : matched.length - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (matched[selectedIndex]) {
        handleSelect(matched[selectedIndex]);
      }
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-slate-950/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl p-4 flex flex-col gap-3">
        <input
          autoFocus
          aria-label="Ejecutar acción"
          placeholder="Escriba el nombre de una acción..."
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value);
            setSelectedIndex(0);
          }}
          onKeyDown={handleKeyDown}
          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none"
        />
        {confirmAction ? (
          <div role="alert" className="p-3 bg-rose-950/60 border border-rose-500/40 rounded-xl text-xs text-rose-200 flex items-center justify-between">
            <span>¿Confirmar ejecución de: {confirmAction.title}?</span>
            <div className="flex gap-2">
              <Button size="sm" variant="ghost" onClick={() => setConfirmAction(null)}>
                Cancelar
              </Button>
              <Button
                size="sm"
                variant="danger"
                onClick={() => {
                  confirmAction.onExecute();
                  setConfirmAction(null);
                  onClose();
                }}
              >
                Ejecutar
              </Button>
            </div>
          </div>
        ) : (
          <ul className="max-h-60 overflow-y-auto divide-y divide-slate-800 text-xs">
            {matched.length === 0 ? (
              <li className="p-3 text-slate-500 text-center">No hay acciones que coincidan</li>
            ) : (
              matched.map((action, idx) => (
                <li
                  key={action.id}
                  onClick={() => handleSelect(action)}
                  className={`p-2.5 rounded-lg flex items-center justify-between cursor-pointer ${idx === selectedIndex ? "bg-blue-600 text-white" : "text-slate-200 hover:bg-slate-800"
                    }`}
                >
                  <span>{action.title}</span>
                  {action.shortcut && (
                    <span className="font-mono text-[10px] opacity-75 bg-slate-800 px-1.5 py-0.5 rounded">
                      {action.shortcut}
                    </span>
                  )}
                </li>
              ))
            )}
          </ul>
        )}
      </div>
    </div>
  );
};
