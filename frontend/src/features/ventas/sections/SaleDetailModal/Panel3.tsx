import { useSaleDetailModal } from "../../hooks/useSaleDetailModal";
import { CreditCard, RotateCcw, Check, Ban, Copy, MessageSquare } from "lucide-react";
import { SaleDetailModalProps } from "../../types/SaleDetailModal";

export function Panel3({
  canWrite,
  detailedSale,
  onConfirmSale,
  balance,
  onOpenPayment,
  onOpenReturn,
  onCancelSale,
  onDuplicateSale,
  onOpenCommunication,
  onClose,
}: {
  detailedSale: NonNullable<ReturnType<typeof useSaleDetailModal>["detailedSale"]>;
  canWrite: NonNullable<SaleDetailModalProps["canWrite"]>;
  onConfirmSale: SaleDetailModalProps["onConfirmSale"];
  onOpenPayment: SaleDetailModalProps["onOpenPayment"];
  onOpenReturn: SaleDetailModalProps["onOpenReturn"];
  onCancelSale: SaleDetailModalProps["onCancelSale"];
  onDuplicateSale: SaleDetailModalProps["onDuplicateSale"];
  onOpenCommunication: SaleDetailModalProps["onOpenCommunication"];
  onClose: SaleDetailModalProps["onClose"];
  balance: number;
}) {
  const saleId = String(detailedSale.sale_id || detailedSale.id);
  const isDraft = detailedSale.status === "draft";
  const isConfirmed = detailedSale.status === "confirmed";
  const isPaid = detailedSale.status === "paid" || detailedSale.payment_status === "Pagada";
  const isCancelled = detailedSale.status === "cancelled";
  const canCobrar = isConfirmed && balance > 0;
  const canDevolver = (isConfirmed || isPaid) && !isCancelled;
  const canAnular = (isDraft || isConfirmed) && !isCancelled;
  const canCobrarSaldo = isPaid && balance > 0;

  return (
    <footer className="flex-shrink-0 flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 dark:border-slate-800 bg-slate-50/90 dark:bg-slate-950/90 px-5 py-3 print:hidden">
      <div className="flex flex-wrap gap-1.5">
        {canWrite && isDraft && onConfirmSale && (
          <button
            type="button"
            onClick={() => onConfirmSale(saleId)}
            className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3.5 py-2 text-xs font-bold text-white hover:bg-teal-800 transition shadow-sm"
          >
            <Check className="h-3.5 w-3.5" />
            Confirmar
          </button>
        )}

        {canWrite && (canCobrar || canCobrarSaldo) && onOpenPayment && (
          <button
            type="button"
            onClick={() => onOpenPayment(detailedSale)}
            className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition shadow-sm"
          >
            <CreditCard className="h-3.5 w-3.5" />
            <span className="sr-only">Registrar Cobro </span>
            {canCobrarSaldo ? "Cobrar Saldo" : "Cobrar"}
          </button>
        )}

        {canWrite && canDevolver && onOpenReturn && (
          <button
            type="button"
            onClick={() => onOpenReturn(detailedSale)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-2 text-xs font-semibold text-amber-800 hover:bg-amber-100 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-300 dark:hover:bg-amber-900/60 transition"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Devolver
          </button>
        )}

        {onDuplicateSale && (
          <button
            type="button"
            onClick={() => onDuplicateSale(detailedSale)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 transition"
          >
            <Copy className="h-3.5 w-3.5" />
            Duplicar
          </button>
        )}

        {onOpenCommunication && (
          <button
            type="button"
            onClick={() => onOpenCommunication(detailedSale)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 transition"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            Enviar
          </button>
        )}

        {canWrite && canAnular && onCancelSale && (
          <button
            type="button"
            onClick={() => onCancelSale(saleId)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 dark:border-rose-700/60 dark:bg-rose-950/40 dark:text-rose-300 dark:hover:bg-rose-900/60 transition"
          >
            <Ban className="h-3.5 w-3.5" />
            Anular
          </button>
        )}
      </div>

      <button
        type="button"
        onClick={onClose}
        className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 transition"
      >
        Cerrar
      </button>
    </footer>
  );
}