import { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { DocumentStatus, PaymentStatus, DeliveryStatus, SunatStatus, ReturnStatus, VoucherType } from "../types/ventas";
import {
  getDocumentStatusStyle,
  getPaymentStatusStyle,
  getDeliveryStatusStyle,
  getSunatStatusStyle,
  getReturnStatusStyle,
  getVoucherTypeStyle,
  getVoucherTypeLabel,
} from "../utils/formateadores";

export function VoucherTypeBadge({ type }: { type: VoucherType | string | undefined }) {
  const style = getVoucherTypeStyle(type);
  const label = getVoucherTypeLabel(type);
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold ${style}`}>
      {label}
    </span>
  );
}

interface StatusCircleProps {
  category: string;
  status: string;
  letter: string;
  style: string;
  placement?: "top" | "bottom";
}

function StatusCircle({ category, status, letter, style, placement = "top" }: StatusCircleProps) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState<{ top: number; left: number; place: "top" | "bottom" } | null>(null);
  const triggerRef = useRef<HTMLSpanElement>(null);

  const updateCoords = useCallback(() => {
    if (!triggerRef.current || typeof window === "undefined") return;
    const rect = triggerRef.current.getBoundingClientRect();
    const place = rect.top >= 48 ? (placement === "bottom" ? "bottom" : "top") : "bottom";
    const top = place === "top" ? rect.top - 6 : rect.bottom + 6;
    const left = rect.left + rect.width / 2;
    setCoords({ top, left, place });
  }, [placement]);

  const handleMouseEnter = () => {
    updateCoords();
    setVisible(true);
  };

  const handleMouseLeave = () => {
    setVisible(false);
  };

  useEffect(() => {
    if (!visible) return;
    updateCoords();
    const onScrollOrResize = () => updateCoords();
    window.addEventListener("scroll", onScrollOrResize, true);
    window.addEventListener("resize", onScrollOrResize);
    return () => {
      window.removeEventListener("scroll", onScrollOrResize, true);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [visible, updateCoords]);

  return (
    <div className="relative inline-flex">
      <span
        ref={triggerRef}
        tabIndex={0}
        role="img"
        aria-label={`${category}: ${status}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleMouseEnter}
        onBlur={handleMouseLeave}
        className={`inline-flex h-6 w-6 items-center justify-center rounded-full border text-[10px] font-bold cursor-help transition-transform hover:scale-110 select-none ${style}`}
      >
        {letter}
      </span>
      {visible && coords && typeof document !== "undefined"
        ? createPortal(
            <div
              role="tooltip"
              style={{
                position: "fixed",
                top: `${coords.top}px`,
                left: `${coords.left}px`,
                transform: coords.place === "top" ? "translate(-50%, -100%)" : "translate(-50%, 0)",
                zIndex: 99999,
              }}
              className="pointer-events-none flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-slate-700 bg-slate-900/95 px-2.5 py-1 text-[11px] font-medium text-slate-100 shadow-2xl backdrop-blur-sm animate-in fade-in duration-100"
            >
              <span className="text-slate-400 font-medium">{category}:</span>
              <span className="font-semibold text-white">{status}</span>
              <div
                className={`absolute left-1/2 -translate-x-1/2 h-2 w-2 rotate-45 bg-slate-900 ${
                  coords.place === "bottom"
                    ? "-top-1 border-l border-t border-slate-700"
                    : "-bottom-1 border-r border-b border-slate-700"
                }`}
              />
            </div>,
            document.body
          )
        : null}
    </div>
  );
}

export function DocumentStatusBadge({ status, compact = false, placement = "top" }: { status: DocumentStatus; compact?: boolean; placement?: "top" | "bottom" }) {
  const style = getDocumentStatusStyle(status);
  const letter = status ? String(status).charAt(0).toUpperCase() : "";
  if (compact) {
    return <StatusCircle category="Documento" status={status} letter={letter} style={style} placement={placement} />;
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${style}`}>
      {status}
    </span>
  );
}

export function PaymentStatusBadge({ status, compact = false, placement = "top" }: { status: PaymentStatus; compact?: boolean; placement?: "top" | "bottom" }) {
  const style = getPaymentStatusStyle(status);
  const letter = status ? String(status).charAt(0).toUpperCase() : "";
  if (compact) {
    return <StatusCircle category="Pago" status={status} letter={letter} style={style} placement={placement} />;
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold ${style}`}>
      {status}
    </span>
  );
}

export function DeliveryStatusBadge({ status, compact = false, placement = "top" }: { status: DeliveryStatus; compact?: boolean; placement?: "top" | "bottom" }) {
  const style = getDeliveryStatusStyle(status);
  const letter = status === "No aplica" ? "—" : status ? String(status).charAt(0).toUpperCase() : "";
  if (compact) {
    return <StatusCircle category="Entrega" status={status} letter={letter} style={style} placement={placement} />;
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${style}`}>
      {status}
    </span>
  );
}

export function SunatStatusBadge({ status, compact = false, placement = "top" }: { status: SunatStatus; compact?: boolean; placement?: "top" | "bottom" }) {
  const style = getSunatStatusStyle(status);
  const letter = status === "No aplica" ? "—" : status ? String(status).charAt(0).toUpperCase() : "";
  if (compact) {
    return <StatusCircle category="SUNAT" status={status} letter={letter} style={style} placement={placement} />;
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${style}`}>
      SUNAT: {status}
    </span>
  );
}

export function ReturnStatusBadge({ status, compact = false, placement = "top" }: { status: ReturnStatus; compact?: boolean; placement?: "top" | "bottom" }) {
  if (status === "Sin devolución") return null;
  const style = getReturnStatusStyle(status);
  const letter = "D";
  if (compact) {
    return <StatusCircle category="Devolución" status={status} letter={letter} style={style} placement={placement} />;
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${style}`}>
      Dev: {status}
    </span>
  );
}

interface VentasBadgesProps {
  documentStatus: DocumentStatus;
  paymentStatus: PaymentStatus;
  deliveryStatus: DeliveryStatus;
  sunatStatus: SunatStatus;
  returnStatus: ReturnStatus;
  compact?: boolean;
  tooltipPlacement?: "top" | "bottom";
}

export function VentasBadges({
  documentStatus,
  paymentStatus,
  deliveryStatus,
  sunatStatus,
  returnStatus,
  compact = true,
  tooltipPlacement = "top",
}: VentasBadgesProps) {
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      <DocumentStatusBadge status={documentStatus} compact={compact} placement={tooltipPlacement} />
      <PaymentStatusBadge status={paymentStatus} compact={compact} placement={tooltipPlacement} />
      <DeliveryStatusBadge status={deliveryStatus} compact={compact} placement={tooltipPlacement} />
      <SunatStatusBadge status={sunatStatus} compact={compact} placement={tooltipPlacement} />
      <ReturnStatusBadge status={returnStatus} compact={compact} placement={tooltipPlacement} />
    </span>
  );
}