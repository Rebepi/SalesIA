import { Calendar, DollarSign, Clock, AlertTriangle, Truck, FileX2, FileEdit } from "lucide-react";
import { SaleKPIs, VentasFilterState } from "../types/ventas";
import { formatMoney } from "../utils/formateadores";

interface VentasKPIBarProps {
  kpis: SaleKPIs;
  activeFilter: VentasFilterState;
  onSelectKpi: (patch: Partial<VentasFilterState>) => void;
  currency?: string;
  clickable?: boolean;
}

export function VentasKPIBar({ kpis, activeFilter, onSelectKpi, currency = "USD", clickable = true }: VentasKPIBarProps) {
  const isTodayActive = activeFilter.date_shortcut === "today";
  const isMonthActive = activeFilter.date_shortcut === "this_month";
  const isReceivableActive = activeFilter.only_with_balance;
  const isOverdueActive = activeFilter.only_overdue;
  const isDeliveryActive = activeFilter.delivery_status === "Pendiente";
  const isSunatRejectedActive = activeFilter.sunat_status === "Rechazado";
  const isOldDraftsActive = activeFilter.document_status === "Borrador";

  const cardBase = "flex flex-col justify-between rounded-xl lg:rounded-2xl border px-3 py-2 sm:px-3.5 sm:py-2.5 text-left transition";

  const kpiCards = [
    {
      key: "today",
      label: "Hoy",
      icon: <Calendar className="h-4 w-4 shrink-0 text-teal-600 dark:text-teal-400" />,
      value: <strong className="block text-sm lg:text-base font-bold tabular-nums text-slate-900 dark:text-slate-100">{formatMoney(kpis.today_amount, currency)}</strong>,
      sub: `${kpis.today_count} comprobantes`,
      active: isTodayActive,
      activeClass: "border-teal-500 bg-teal-50/70 shadow-sm dark:border-teal-400 dark:bg-teal-950/40",
      onClick: () => onSelectKpi({ date_shortcut: isTodayActive ? "all" : "today" }),
    },
    {
      key: "month",
      label: "Mes actual",
      icon: <DollarSign className="h-4 w-4 shrink-0 text-teal-600 dark:text-teal-400" />,
      value: <strong className="block text-sm lg:text-base font-bold tabular-nums text-slate-900 dark:text-slate-100">{formatMoney(kpis.month_amount, currency)}</strong>,
      sub: `${kpis.month_count} ventas`,
      active: isMonthActive,
      activeClass: "border-teal-500 bg-teal-50/70 shadow-sm dark:border-teal-400 dark:bg-teal-950/40",
      onClick: () => onSelectKpi({ date_shortcut: isMonthActive ? "all" : "this_month" }),
    },
    {
      key: "receivable",
      label: "Por cobrar",
      icon: <Clock className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />,
      value: <strong className="block text-sm lg:text-base font-bold tabular-nums text-amber-700 dark:text-amber-400">{formatMoney(kpis.receivable_amount, currency)}</strong>,
      sub: `${kpis.receivable_count} con saldo`,
      active: isReceivableActive,
      activeClass: "border-amber-500 bg-amber-50/70 shadow-sm dark:border-amber-400 dark:bg-amber-950/40",
      onClick: () => onSelectKpi({ only_with_balance: !isReceivableActive }),
    },
    {
      key: "overdue",
      label: "Vencido",
      icon: <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />,
      value: <strong className="block text-sm lg:text-base font-bold tabular-nums text-rose-700 dark:text-rose-400">{formatMoney(kpis.overdue_amount, currency)}</strong>,
      sub: `${kpis.overdue_count} vencidas`,
      active: isOverdueActive,
      activeClass: "border-rose-500 bg-rose-50/70 shadow-sm dark:border-rose-400 dark:bg-rose-950/40",
      onClick: () => onSelectKpi({ only_overdue: !isOverdueActive }),
    },
    {
      key: "delivery",
      label: "Por entregar",
      icon: <Truck className="h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400" />,
      value: <strong className="block text-sm lg:text-base font-bold tabular-nums text-blue-700 dark:text-blue-400">{kpis.pending_delivery_count}</strong>,
      sub: "Despachos pendientes",
      active: isDeliveryActive,
      activeClass: "border-blue-500 bg-blue-50/70 shadow-sm dark:border-blue-400 dark:bg-blue-950/40",
      onClick: () => onSelectKpi({ delivery_status: isDeliveryActive ? "" : "Pendiente" }),
    },
    {
      key: "sunat",
      label: "Rechazadas SUNAT",
      icon: <FileX2 className="h-4 w-4 shrink-0 text-purple-600 dark:text-purple-400" />,
      value: <strong className="block text-sm lg:text-base font-bold tabular-nums text-purple-700 dark:text-purple-400">{kpis.sunat_rejected_count}</strong>,
      sub: "Requieren corrección",
      active: isSunatRejectedActive,
      activeClass: "border-purple-500 bg-purple-50/70 shadow-sm dark:border-purple-400 dark:bg-purple-950/40",
      onClick: () => onSelectKpi({ sunat_status: isSunatRejectedActive ? "" : "Rechazado" }),
    },
    {
      key: "drafts",
      label: "Borradores",
      icon: <FileEdit className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />,
      value: <strong className="block text-sm lg:text-base font-bold tabular-nums text-slate-800 dark:text-slate-200">{kpis.old_drafts_count}</strong>,
      sub: "En edición",
      active: isOldDraftsActive,
      activeClass: "border-amber-500 bg-amber-50/70 shadow-sm dark:border-amber-400 dark:bg-amber-950/40",
      onClick: () => onSelectKpi({ document_status: isOldDraftsActive ? "" : "Borrador" }),
    },
  ];

  const inactiveClass = "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700";
  const staticClass = "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900";

  return (
    <div className="grid w-full grid-cols-2 gap-2 sm:gap-2.5 sm:grid-cols-3 lg:grid-cols-7">
      {kpiCards.map((card) =>
        clickable ? (
          <button
            key={card.key}
            type="button"
            onClick={card.onClick}
            className={`${cardBase} ${card.active ? card.activeClass : inactiveClass}`}
          >
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span className="truncate">{card.label}</span>
              {card.icon}
            </div>
            <div className="mt-1 sm:mt-1.5">
              {card.value}
              <span className="block truncate text-[10px] sm:text-[11px] text-slate-500 dark:text-slate-400">{card.sub}</span>
            </div>
          </button>
        ) : (
          <div
            key={card.key}
            className={`${cardBase} ${staticClass}`}
          >
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span className="truncate">{card.label}</span>
              {card.icon}
            </div>
            <div className="mt-1 sm:mt-1.5">
              {card.value}
              <span className="block truncate text-[10px] sm:text-[11px] text-slate-500 dark:text-slate-400">{card.sub}</span>
            </div>
          </div>
        )
      )}
    </div>
  );
}
