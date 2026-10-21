import React from "react";
import { CancelXIcon } from "../../icons/index";
import { IconButton } from "./IconButton";

export interface AlertBannerProps {
  type?: "info" | "warning" | "error" | "success";
  title: string;
  message?: string;
  onClose?: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type = "info",
  title,
  message,
  onClose
}) => {
  const typeStyles = {
    info: "border-blue-500/40 bg-blue-950/40 text-blue-200",
    warning: "border-amber-500/40 bg-amber-950/40 text-amber-200",
    error: "border-rose-500/40 bg-rose-950/40 text-rose-200",
    success: "border-emerald-500/40 bg-emerald-950/40 text-emerald-200"
  };
  return (
    <div
      role={type === "error" ? "alert" : "status"}
      className={`p-4 rounded-xl border flex items-start justify-between gap-3 ${typeStyles[type]}`}
    >
      <div>
        <h4 className="font-semibold text-sm">{title}</h4>
        {message && <p className="text-xs opacity-90 mt-1">{message}</p>}
      </div>
      {onClose && (
        <IconButton
          ariaLabel="Cerrar alerta"
          size="sm"
          icon={<CancelXIcon size={14} />}
          onClick={onClose}
        />
      )}
    </div>
  );
};
