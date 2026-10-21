import React, { useState } from "react";
import { Button } from "./Button";

export interface BulkActionItemResult {
  id: string;
  status: "success" | "failed";
  error?: string;
}

export interface BulkActionBarProps {
  selectedCount: number;
  scopeDescription: string;
  onExecute: (actionKey: string) => Promise<BulkActionItemResult[]>;
  onClear: () => void;
  actions: { key: string; label: string; isSensitive?: boolean }[];
}

export const BulkActionBar: React.FC<BulkActionBarProps> = ({
  selectedCount,
  scopeDescription,
  onExecute,
  onClear,
  actions
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<BulkActionItemResult[] | null>(null);
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  if (selectedCount === 0 && !results) return null;

  const handleActionClick = (actionKey: string, isSensitive?: boolean) => {
    if (isSensitive) {
      setPendingAction(actionKey);
    } else {
      executeAction(actionKey);
    }
  };

  const executeAction = (actionKey: string) => {
    setIsRunning(true);
    onExecute(actionKey)
      .then((res) => {
        setResults(res);
        setIsRunning(false);
      })
      .catch(() => {
        setIsRunning(false);
      });
  };

  const failedItems = results ? results.filter((r) => r.status === "failed") : [];

  return (
    <div
      role="region"
      aria-label="Acciones masivas"
      className="p-4 bg-slate-900 border border-blue-500/50 rounded-2xl shadow-xl flex flex-col gap-3 my-3"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <span className="font-bold text-sm text-white">
            {`${selectedCount} elementos seleccionados`}
          </span>
          <p className="text-xs text-slate-400">{scopeDescription}</p>
        </div>
        <div className="flex items-center gap-2">
          {actions.map((act) => (
            <Button
              key={act.key}
              size="sm"
              variant={act.isSensitive ? "danger" : "secondary"}
              disabled={isRunning}
              onClick={() => handleActionClick(act.key, act.isSensitive)}
            >
              {act.label}
            </Button>
          ))}
          <Button size="sm" variant="ghost" disabled={isRunning} onClick={onClear}>
            Cancelar selección
          </Button>
        </div>
      </div>

      {pendingAction && (
        <div className="p-3 bg-rose-950/50 border border-rose-500/50 rounded-xl text-xs text-rose-200 flex items-center justify-between">
          <span>Esta acción masiva es sensible. ¿Desea proceder con los {selectedCount} registros?</span>
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" onClick={() => setPendingAction(null)}>
              No, cancelar
            </Button>
            <Button
              size="sm"
              variant="danger"
              onClick={() => {
                const act = pendingAction;
                setPendingAction(null);
                executeAction(act);
              }}
            >
              Sí, ejecutar
            </Button>
          </div>
        </div>
      )}

      {results && (
        <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-slate-200">
              {`Resultado: ${results.length - failedItems.length} exitosos, ${failedItems.length} fallidos`}
            </span>
            {failedItems.length > 0 && (
              <Button
                size="sm"
                variant="outline"
                disabled={isRunning}
                onClick={() => executeAction("retry_failed")}
              >
                {`Reintentar solo fallidos (${failedItems.length})`}
              </Button>
            )}
          </div>
          <ul className="space-y-1">
            {results.map((item) => (
              <li
                key={item.id}
                className={item.status === "success" ? "text-emerald-400" : "text-rose-400"}
              >
                {item.id}: {item.status === "success" ? "Completado" : `Error: ${item.error || "Fallo"}`}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
