import React from "react";
import { Button } from "./Button";

export interface RecoverableErrorBannerProps {
  errorType?: "payment_timeout" | "network_error" | "validation_error";
  title: string;
  message: string;
  onQueryStatus?: () => void;
  onRetry?: () => void;
}

export const RecoverableErrorBanner: React.FC<RecoverableErrorBannerProps> = ({
  errorType = "network_error",
  title,
  message,
  onQueryStatus,
  onRetry
}) => {
  return (
    <div
      role="alert"
      className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/40 text-amber-200 text-left space-y-3"
    >
      <div>
        <h4 className="font-semibold text-sm">{title}</h4>
        <p className="text-xs opacity-90 mt-1">{message}</p>
      </div>
      <div className="flex gap-2 pt-1">
        {errorType === "payment_timeout" && onQueryStatus && (
          <Button size="sm" variant="secondary" onClick={onQueryStatus}>
            Consultar estado de la transacción
          </Button>
        )}
        {onRetry && (
          <Button size="sm" variant="outline" onClick={onRetry}>
            Reintentar operación
          </Button>
        )}
      </div>
    </div>
  );
};
