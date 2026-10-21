import { SeccionVenta } from "../sections/SaleDetailModal/SeccionVenta";
import { Panel2, DETAIL_TABS } from "../sections/SaleDetailModal/Panel2";
import { Panel3 } from "../sections/SaleDetailModal/Panel3";
export type { SaleDetailData } from "../types/SaleDetailModal";
import { useSaleDetailModal } from "../hooks/useSaleDetailModal";
import { SaleDetailModalProps } from "../types/SaleDetailModal";

export function SaleDetailModal({
  sale,
  canWrite = true,
  canViewCosts = false,
  onClose,
  onConfirmSale,
  onOpenPayment,
  onOpenReturn,
  onCancelSale,
  onDuplicateSale,
  onOpenCommunication,
}: SaleDetailModalProps) {
  const { activeTab, setActiveTab, detailedSale, loading, dialogRef } = useSaleDetailModal({
    sale,
    canWrite,
    onClose,
    onConfirmSale,
    onOpenPayment,
    onOpenReturn,
    onCancelSale,
    onDuplicateSale,
    onOpenCommunication,
  });

  if (!sale || !detailedSale) return null;

  const total = Number(detailedSale.total_amount || 0);
  const paid = Number(detailedSale.paid_amount || 0);
  const balance = Math.max(0, total - paid);
  const docNumber = detailedSale.number || detailedSale.series || detailedSale.id.substring(0, 8);

  return (
    <dialog
      ref={dialogRef}
      id="scr-017-sale-detail-dialog"
      data-status={detailedSale.status}
      onCancel={onClose}
      aria-labelledby="sale-detail-title"
      className="m-auto max-h-[92vh] w-[min(98vw,1000px)] rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 p-0 shadow-2xl backdrop:bg-slate-950/70 flex flex-col overflow-hidden print:w-full print:max-w-none print:max-h-none print:rounded-xl print:shadow-none print:overflow-visible print:border-slate-300 print:m-0"
      style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}
    >
      <SeccionVenta
        docNumber={docNumber}
        detailedSale={detailedSale}
        total={total}
        paid={paid}
        balance={balance}
        onClose={onClose}
      />

      <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/60 px-4 gap-1 overflow-x-auto flex-shrink-0 print:hidden">
        {DETAIL_TABS.map((t) => {
          const Icon = t.Icon;
          const isActive = activeTab === t.key;
          const count = t.key === "payments"
            ? (detailedSale.payments?.length ?? 0)
            : t.key === "lines"
              ? (detailedSale.lines?.length ?? 0)
              : null;
          return (
            <button
              key={t.key}
              type="button"
              onClick={() => setActiveTab(t.key)}
              className={`flex items-center gap-1.5 border-b-2 py-2.5 px-2.5 text-[11px] font-semibold whitespace-nowrap transition ${
                isActive
                  ? "border-teal-600 text-teal-700 dark:border-teal-400 dark:text-teal-300"
                  : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:border-slate-700"
              }`}
            >
              <Icon className="h-3 w-3 flex-shrink-0" />
              <span>{t.label}</span>
              {count !== null && count > 0 && (
                <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-mono font-bold leading-none ${
                  isActive
                    ? "bg-teal-100 text-teal-800 dark:bg-teal-900/60 dark:text-teal-200"
                    : "bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                }`}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <Panel2
        loading={loading}
        activeTab={activeTab}
        detailedSale={detailedSale}
        canViewCosts={canViewCosts}
      />

      <Panel3
        canWrite={canWrite}
        detailedSale={detailedSale}
        onConfirmSale={onConfirmSale}
        balance={balance}
        onOpenPayment={onOpenPayment}
        onOpenReturn={onOpenReturn}
        onCancelSale={onCancelSale}
        onDuplicateSale={onDuplicateSale}
        onOpenCommunication={onOpenCommunication}
        onClose={onClose}
      />
    </dialog>
  );
}
