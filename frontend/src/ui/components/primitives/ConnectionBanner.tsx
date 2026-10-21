import React from "react";
import type { ConnectionState } from "./canExecuteFinancialAction";
import { Button } from "./Button";

export const ConnectionBanner: React.FC<{
  connectionState: ConnectionState;
  onRetry?: () => void;
}> = ({ connectionState, onRetry }) => {
  if (connectionState === "online") return null;

  return (
    <div
      role="alert"
      className="p-3 bg-amber-950/80 border border-amber-500/50 text-amber-200 text-xs flex items-center justify-between rounded-xl my-2"
    >
      <div className="flex items-center gap-2">
        <span className="font-bold">
          {connectionState === "offline"
            ? "Sin conexión"
            : connectionState === "reconnecting"
              ? "Reconectando..."
              : "Datos desactualizados"}
          :
        </span>
        <span>
          Cobro definitivo y reserva final de stock suspendidos para evitar duplicidad o sobreventa.
        </span>
      </div>
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry}>
          Reintentar conexión
        </Button>
      )}
    </div>
  );
};
