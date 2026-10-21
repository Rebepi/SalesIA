import { useSaleDetailModal } from "../../hooks/useSaleDetailModal";
import { X, Check, Circle } from "lucide-react";
import { SaleDetailModalProps } from "../../types/SaleDetailModal";
import { VentasBadges } from "../../components/VentasBadges";
import { formatMoney, formatDateTime, formatPaymentMethodShort } from "../../utils/formateadores";
import { DocumentStatus, PaymentStatus, DeliveryStatus, SunatStatus, ReturnStatus } from "../../types/ventas";

function TimelineStep({ label, timestamp, active, done }: { label: string; timestamp?: string | null; active?: boolean; done?: boolean }) {
  return (
    <div className={`flex flex-col items-center gap-1 ${done ? "opacity-100" : active ? "opacity-90" : "opacity-35"}`}>
      <div
        className={`timeline-step-circle flex h-7 w-7 items-center justify-center rounded-full border-2 transition ${
          done
            ? "timeline-step-done-circle border-emerald-600 bg-emerald-600 text-white dark:border-emerald-500 dark:bg-emerald-500 print:border-emerald-700 print:bg-emerald-50 print:text-emerald-700"
            : active
            ? "border-teal-600 bg-teal-600 text-white dark:border-teal-400 dark:bg-teal-500 print:border-teal-700 print:bg-teal-50 print:text-teal-700"
            : "border-slate-300 bg-white text-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500 print:border-slate-300 print:text-slate-400"
        }`}
      >
        {done ? <Check className="h-4 w-4 stroke-[3]" /> : <Circle className="h-3.5 w-3.5" />}
      </div>
      <span className={`text-[10px] font-semibold ${done ? "text-emerald-700 dark:text-emerald-400 print:text-emerald-800" : active ? "text-teal-800 dark:text-teal-300 print:text-teal-800" : "text-slate-400 dark:text-slate-500 print:text-slate-500"}`}>{label}</span>
      {timestamp && <span className="text-[9px] text-slate-400 dark:text-slate-500 print:text-slate-500">{formatDateTime(timestamp)}</span>}
    </div>
  );
}

export function SeccionVenta({
  docNumber,
  detailedSale,
  total,
  paid,
  balance,
  onClose,
}: {
  detailedSale: NonNullable<ReturnType<typeof useSaleDetailModal>["detailedSale"]>;
  onClose: SaleDetailModalProps["onClose"];
  docNumber: string;
  total: number;
  paid: number;
  balance: number;
}) {
  const docStatus = (detailedSale.document_status || (
    detailedSale.status === "cancelled" ? "Anulada" :
    detailedSale.status === "draft" ? "Borrador" :
    "Confirmada"
  )) as DocumentStatus;

  const paymentStatus = (detailedSale.payment_status || "Sin cobrar") as PaymentStatus;
  const deliveryStatus = (detailedSale.delivery_status || "No aplica") as DeliveryStatus;
  const sunatStatus = (detailedSale.sunat_status || "No aplica") as SunatStatus;
  const returnStatus = (detailedSale.return_status || "Sin devolución") as ReturnStatus;

  const isConfirmed = !["draft", "Borrador"].includes(detailedSale.status);
  const isCancelled = ["cancelled", "Anulada"].includes(detailedSale.status);
  const isSunatSent = sunatStatus !== "No aplica" && sunatStatus !== "Pendiente";
  const isCobrada = paymentStatus === "Pagada";
  const isEntregada = deliveryStatus === "Entregada";

  const currency = detailedSale.currency || "USD";
  const dueAt = detailedSale.due_at || detailedSale.due_date;
  const calendar = detailedSale.due_calendar;

  return (
    <header className="flex-shrink-0 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/90">
      <div className="flex flex-wrap items-start justify-between gap-3 px-6 pt-5 pb-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <h2 id="sale-detail-title" className="text-lg font-mono font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
              <span className="sr-only">Venta: </span>{detailedSale.document_type === "INVOICE" ? "Factura" : detailedSale.document_type === "RECEIPT" ? "Boleta" : "Venta"} #{docNumber}
            </h2>
            <VentasBadges
              documentStatus={docStatus}
              paymentStatus={paymentStatus}
              deliveryStatus={deliveryStatus}
              sunatStatus={sunatStatus}
              returnStatus={returnStatus}
              tooltipPlacement="bottom"
            />
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
            <span>
              Cliente: <strong className="text-slate-800 dark:text-slate-200 font-bold">{detailedSale.customer_name || "Cliente General"}</strong>
              {detailedSale.customer_document && (
                <span className="ml-1 font-mono text-slate-500 dark:text-slate-400">({detailedSale.customer_document})</span>
              )}
            </span>
            {detailedSale.sales_rep_name && (
              <span>Vendedor: <strong className="text-slate-700 dark:text-slate-300 font-semibold">{detailedSale.sales_rep_name}</strong></span>
            )}
            {detailedSale.branch_name && (
              <span>Sede: <strong className="text-slate-700 dark:text-slate-300 font-semibold">{detailedSale.branch_name}</strong></span>
            )}
            {dueAt && (
              <span>Vencimiento: <strong className={balance > 0 && new Date(dueAt) < new Date() ? "text-rose-600 dark:text-rose-400" : "text-slate-700 dark:text-slate-300"}>{new Date(dueAt).toLocaleString("es-PE", { timeZone: calendar?.calendar.timezone })}</strong></span>
            )}
            <span>
              {detailedSale.is_credit ? (
                <>Condición: <strong className="text-indigo-700 dark:text-indigo-300 font-semibold">Crédito Comercial</strong></>
              ) : (detailedSale.payments && detailedSale.payments.length > 0) ? (
                <>
                  {detailedSale.payments.length > 1 ? "Medios de pago: " : "Medio de pago: "}
                  <strong className="text-slate-800 dark:text-slate-200 font-bold">
                    {detailedSale.payments.map(p => `${formatPaymentMethodShort(p.payment_method)} (${formatMoney(p.amount, p.currency || currency)})`).join(" + ")}
                  </strong>
                </>
              ) : (
                <>Condición: <strong className="text-slate-700 dark:text-slate-300 font-semibold">Contado</strong></>
              )}
            </span>
            {calendar && detailedSale.is_credit && <details className="w-full text-xs"><summary className="cursor-pointer">Condiciones de vencimiento conservadas al confirmar</summary><p>{calendar.payment_terms_days} días · {calendar.legacy_elapsed_days ? "Días transcurridos, condición anterior al calendario operativo" : calendar.basis === "business" ? "Días hábiles" : "Días calendario"} · {calendar.calendar.timezone}</p><p>Calendario de sede {calendar.calendar.version} / empresa {calendar.calendar.company_version} · Traslado: {({ none: "Conservar fecha", next: "Siguiente hábil", previous: "Hábil anterior", modified_next: "Siguiente hábil o anterior si cambia el mes" } as Record<string, string>)[calendar.roll || "none"]}</p>{calendar.before_roll && <p>Fecha antes del traslado: {calendar.before_roll}</p>}</details>}
          </div>
        </div>

        <div className="flex items-start gap-4">
          <div className="flex items-end gap-5 font-mono text-right">
            <div>
              <span className="block text-[9px] uppercase font-bold tracking-wider text-slate-400 dark:text-slate-500">Total</span>
              <strong className="text-xl font-extrabold text-slate-900 dark:text-slate-100">{formatMoney(total, currency)}</strong>
            </div>
            <div>
              <span className="block text-[9px] uppercase font-bold tracking-wider text-slate-400 dark:text-slate-500">Cobrado</span>
              <strong className="text-base font-bold text-emerald-700 dark:text-emerald-400">{formatMoney(paid, currency)}</strong>
            </div>
            <div>
              <span className="block text-[9px] uppercase font-bold tracking-wider text-slate-400 dark:text-slate-500">Saldo</span>
              <strong className={`text-base font-bold ${balance > 0 ? "text-amber-700 dark:text-amber-400" : "text-slate-400 dark:text-slate-500"}`}>{formatMoney(balance, currency)}</strong>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            autoFocus
            aria-label="Cerrar detalle de venta"
            className="rounded-xl p-2 text-slate-400 hover:bg-slate-200/60 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition print:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      <div className="flex items-start justify-between px-6 pb-4 overflow-x-auto print:overflow-visible">
        <TimelineStep label="Creada" timestamp={detailedSale.created_at} done={true} />
        <div className={`flex-1 border-t-2 min-w-4 self-start mt-3.5 ${isConfirmed ? "timeline-connector-done border-emerald-500 dark:border-emerald-500" : "border-slate-200 dark:border-slate-800"}`} />
        <TimelineStep label="Confirmada" timestamp={detailedSale.confirmed_at} done={isConfirmed && !isCancelled} active={!isConfirmed} />
        <div className={`flex-1 border-t-2 min-w-4 self-start mt-3.5 ${isSunatSent ? "timeline-connector-done border-emerald-500 dark:border-emerald-500" : "border-slate-200 dark:border-slate-800"}`} />
        <TimelineStep label="SUNAT" timestamp={detailedSale.sunat_sent_at} done={isSunatSent} active={isConfirmed && !isSunatSent && !isCancelled} />
        <div className={`flex-1 border-t-2 min-w-4 self-start mt-3.5 ${isCobrada ? "timeline-connector-done border-emerald-500 dark:border-emerald-500" : "border-slate-200 dark:border-slate-800"}`} />
        <TimelineStep label="Cobrada" done={isCobrada} active={isConfirmed && !isCobrada && !isCancelled} />
        <div className={`flex-1 border-t-2 min-w-4 self-start mt-3.5 ${isEntregada ? "timeline-connector-done border-emerald-500 dark:border-emerald-500" : "border-slate-200 dark:border-slate-800"}`} />
        <TimelineStep label="Entregada" done={isEntregada} active={isCobrada && !isEntregada && !isCancelled} />
      </div>
    </header>
  );
}
