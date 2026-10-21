import { IconAction } from "../../../ui/components/primitives/IconAction";
import { useState, useRef } from "react";
import {
  FileText,
  CreditCard,
  RotateCcw,
  MoreHorizontal,
  Check,
  Printer,
  Send,
  CalendarClock,
  Eye,
  Trash2,
  Copy,
  FileCheck,
  AlertOctagon,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  RefreshCw,
  Truck,
  FilePlus,
} from "lucide-react";
import { SaleRecord } from "../types/ventas";
import { formatDateTime, formatDate, formatMoney } from "../utils/formateadores";
import {
  DocumentStatusBadge,
  PaymentStatusBadge,
  DeliveryStatusBadge,
  SunatStatusBadge,
  ReturnStatusBadge,
  VoucherTypeBadge,
} from "./VentasBadges";

interface VentasTableProps {
  rows: SaleRecord[];
  loading: boolean;
  selectionMode: boolean;
  selectedIds: string[];
  onSelectRow: (id: string) => void;
  onSelectAll: () => void;
  canWrite: boolean;
  canCancel: boolean;
  onOpenDetail: (sale: SaleRecord) => void;
  onConfirmSale: (sale: SaleRecord) => void;
  onOpenPayment: (sale: SaleRecord) => void;
  onRepeatSale: (sale: SaleRecord) => void;
  onDuplicateDraft: (sale: SaleRecord) => void;
  onDeleteDraft: (sale: SaleRecord) => void;
  onConvertToQuotation: (sale: SaleRecord) => void;
  onOpenReturn: (sale: SaleRecord) => void;
  onCancelSale: (sale: SaleRecord) => void;
  onRescheduleDueDate: (sale: SaleRecord) => void;
  onPrintSale: (sale: SaleRecord, format?: "A4" | "TICKET" | "A5") => void;
  onSendSale: (sale: SaleRecord) => void;
  onRetrySunat: (sale: SaleRecord) => void;
  onViewCancellationReason: (sale: SaleRecord) => void;
  onViewSunatError: (sale: SaleRecord) => void;
  onCreateDebitNote?: (sale: SaleRecord) => void;
  onGenerateGuide?: (sale: SaleRecord) => void;
  onDownloadXml?: (sale: SaleRecord) => void;
  onDownloadPdf?: (sale: SaleRecord) => void;
  columnsConfig: Array<{ key: string; label: string; visible: boolean }>;
  sortField: string;
  sortDirection: "asc" | "desc";
  onSort: (field: string) => void;
}

export function VentasTable({
  rows,
  loading,
  selectionMode,
  selectedIds,
  onSelectRow,
  onSelectAll,
  canWrite,
  canCancel,
  onOpenDetail,
  onConfirmSale,
  onOpenPayment,
  onRepeatSale,
  onDuplicateDraft,
  onDeleteDraft,
  onConvertToQuotation,
  onOpenReturn,
  onCancelSale,
  onRescheduleDueDate,
  onPrintSale,
  onSendSale,
  onRetrySunat,
  onViewCancellationReason,
  onViewSunatError,
  onCreateDebitNote,
  onGenerateGuide,
  onDownloadPdf,
  columnsConfig,
  sortField,
  sortDirection,
  onSort,
}: VentasTableProps) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  const isVisible = (key: string) => {
    const col = columnsConfig.find((c) => c.key === key);
    return col ? col.visible : true;
  };

  const renderSortIcon = (field: string) => {
    if (sortField !== field) return <ArrowUpDown className="h-3 w-3 opacity-40" />;
    return sortDirection === "asc" ? (
      <ArrowUp className="h-3 w-3 text-teal-600" />
    ) : (
      <ArrowDown className="h-3 w-3 text-teal-600" />
    );
  };

  const allSelected = rows.length > 0 && selectedIds.length === rows.length;

  const headerRef = useRef<HTMLDivElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (headerRef.current) {
      headerRef.current.scrollLeft = e.currentTarget.scrollLeft;
    }
  };

  const renderColGroup = () => (
    <colgroup>
      {selectionMode && <col className="w-12" style={{ width: "48px" }} />}
      {isVisible("created_at") && <col className="w-44" style={{ width: "176px" }} />}
      {isVisible("voucher_type") && <col className="w-24" style={{ width: "96px" }} />}
      {isVisible("document") && <col className="w-36" style={{ width: "144px" }} />}
      {isVisible("customer") && <col />}
      {isVisible("sales_rep") && <col className="w-32" style={{ width: "128px" }} />}
      {isVisible("branch") && <col className="w-32" style={{ width: "128px" }} />}
      {isVisible("total") && <col className="w-24" style={{ width: "96px" }} />}
      {isVisible("paid") && <col className="w-24" style={{ width: "96px" }} />}
      {isVisible("balance") && <col className="w-24" style={{ width: "96px" }} />}
      {isVisible("due_date") && <col className="w-28" style={{ width: "112px" }} />}
      {isVisible("statuses") && <col className="w-44" style={{ width: "176px" }} />}
      <col className="w-36" style={{ width: "144px" }} />
    </colgroup>
  );

  return (
    <div className="relative flex-1 min-h-0 flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 w-full">
      <div
        ref={headerRef}
        className="table-header-region shrink-0 overflow-x-hidden"
      >
        <table className="w-full text-left text-xs table-fixed min-w-[1000px]">
          {renderColGroup()}
          <thead className="uppercase tracking-wider text-slate-600 dark:text-slate-300">
            <tr className="h-11">
              {selectionMode && (
                <th scope="col" className="w-12 px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    aria-label="Seleccionar todas las ventas visibles"
                    checked={allSelected}
                    onChange={onSelectAll}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 dark:border-slate-700"
                  />
                </th>
              )}
              {isVisible("created_at") && (
                <th scope="col" onClick={() => onSort("created_at")} className="cursor-pointer px-4 py-3 hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center gap-1.5"><span>Fecha y Hora</span>{renderSortIcon("created_at")}</div>
                </th>
              )}
              {isVisible("voucher_type") && (
                <th scope="col" onClick={() => onSort("voucher_type")} className="cursor-pointer px-4 py-3 hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center gap-1.5"><span>Tipo</span>{renderSortIcon("voucher_type")}</div>
                </th>
              )}
              {isVisible("document") && (
                <th scope="col" onClick={() => onSort("number")} className="cursor-pointer px-4 py-3 hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center gap-1.5"><span>Documento</span>{renderSortIcon("number")}</div>
                </th>
              )}
              {isVisible("customer") && (
                <th scope="col" onClick={() => onSort("customer_name")} className="cursor-pointer px-4 py-3 hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center gap-1.5"><span>Cliente</span>{renderSortIcon("customer_name")}</div>
                </th>
              )}
              {isVisible("sales_rep") && (
                <th scope="col" onClick={() => onSort("sales_rep_name")} className="cursor-pointer px-4 py-3 hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center gap-1.5"><span>Vendedor</span>{renderSortIcon("sales_rep_name")}</div>
                </th>
              )}
              {isVisible("branch") && (
                <th scope="col" onClick={() => onSort("branch_name")} className="cursor-pointer px-4 py-3 hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center gap-1.5"><span>Sede</span>{renderSortIcon("branch_name")}</div>
                </th>
              )}
              {isVisible("total") && (
                <th scope="col" onClick={() => onSort("total_amount")} className="cursor-pointer px-4 py-3 text-right hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center justify-end gap-1.5"><span>Total</span>{renderSortIcon("total_amount")}</div>
                </th>
              )}
              {isVisible("paid") && (
                <th scope="col" onClick={() => onSort("paid_amount")} className="cursor-pointer px-4 py-3 text-right hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center justify-end gap-1.5"><span>Cobrado</span>{renderSortIcon("paid_amount")}</div>
                </th>
              )}
              {isVisible("balance") && (
                <th scope="col" onClick={() => onSort("balance")} className="cursor-pointer px-4 py-3 text-right hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center justify-end gap-1.5"><span>Saldo</span>{renderSortIcon("balance")}</div>
                </th>
              )}
              {isVisible("due_date") && (
                <th scope="col" onClick={() => onSort("due_date")} className="cursor-pointer px-4 py-3 hover:text-slate-900 dark:hover:text-slate-200">
                  <div className="flex items-center gap-1.5"><span>Vencimiento</span>{renderSortIcon("due_date")}</div>
                </th>
              )}
              {isVisible("statuses") && <th scope="col" className="px-4 py-3">Estados</th>}
              <th scope="col" className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
        </table>
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="table-scroll-region flex-1 min-h-0 overflow-auto"
        tabIndex={0}
        role="region"
        aria-label="Listado de ventas con desplazamiento"
      >
        {loading && (
          <div role="status" className="flex items-center justify-center p-12 text-center text-sm text-slate-500">
            <RefreshCw className="mr-2 h-4 w-4 animate-spin text-teal-600" />
            <span>Cargando comprobantes...</span>
          </div>
        )}
        {!loading && rows.length === 0 && (
          <div className="p-12 text-center text-sm text-slate-500">
            No se encontraron ventas para los criterios seleccionados.
          </div>
        )}
        {!loading && rows.length > 0 && (
          <table className="w-full text-left text-xs table-fixed min-w-[1000px]">
            {renderColGroup()}
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {rows.map((row) => {
                const totalNum = Number(row.total_amount || 0);
                const paidNum = Number(row.paid_amount || 0);
                const balanceNum = Number(row.balance_amount ?? Math.max(0, totalNum - paidNum));
                const isSelected = selectedIds.includes(row.id || row.sale_id);
                const menuOpen = openMenuId === (row.id || row.sale_id);

                const isDraft = row.document_status === "Borrador";
                const isConfirmed = row.document_status === "Confirmada";
                const isCancelled = row.document_status === "Anulada";
                const isSunatRejected = row.sunat_status === "Rechazado";
                const isPaid = row.payment_status === "Pagada";
                const isPartialPaid = row.payment_status === "Parcial";
                const isUnpaid = row.payment_status === "Sin cobrar";

                return (
                  <tr
                    key={row.id || row.sale_id}
                    className={`transition ${isSelected
                      ? "bg-teal-50/50 dark:bg-teal-950/20"
                      : isCancelled
                        ? "bg-rose-50/20 opacity-75 dark:bg-rose-950/10"
                        : "hover:bg-slate-50/80 dark:hover:bg-slate-800/40"
                      }`}
                  >
                    {selectionMode && (
                      <td className="px-4 py-3 text-center">
                        <input
                          type="checkbox"
                          aria-label={`Seleccionar venta ${row.number}`}
                          checked={isSelected}
                          onChange={() => onSelectRow(row.id || row.sale_id)}
                          className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 dark:border-slate-700"
                        />
                      </td>
                    )}

                    {isVisible("created_at") && (
                      <td className="px-4 py-3 tabular-nums text-slate-600 dark:text-slate-400">
                        {formatDateTime(row.created_at)}
                      </td>
                    )}

                    {isVisible("voucher_type") && (
                      <td className="px-4 py-3">
                        <VoucherTypeBadge type={row.voucher_type || (row.document_type === "INVOICE" ? "FACTURA" : row.document_type === "SALE_NOTE" ? "NOTA_VENTA" : "BOLETA")} />
                      </td>
                    )}

                    {isVisible("document") && (
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5 font-mono">
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                            {row.document_type === "INVOICE" ? "FAC" : row.document_type === "SALE_NOTE" ? "NV" : "BOL"}
                          </span>
                          <strong className="text-slate-900 dark:text-slate-100">{row.number}</strong>{row.zero_cost_lines_count !== undefined && <span className="mt-1 block text-[11px] text-amber-600 dark:text-amber-400">{row.zero_cost_lines_count} {row.zero_cost_lines_count === 1 ? "línea con costo cero" : "líneas con costo cero"}</span>}
                        </div>
                      </td>
                    )}

                    {isVisible("customer") && (
                      <td className="px-4 py-3">
                        <div>
                          <strong className="block text-slate-900 dark:text-slate-100">
                            {row.customer_name || "Cliente General"}
                          </strong>
                          <span className="block font-mono text-[10px] text-slate-500 dark:text-slate-400">
                            {row.customer_document || "Sin documento"}
                          </span>
                        </div>
                      </td>
                    )}

                    {isVisible("sales_rep") && (
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                        {row.sales_rep_name || "—"}
                      </td>
                    )}

                    {isVisible("branch") && (
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                        {row.branch_name || "—"}
                      </td>
                    )}

                    {isVisible("total") && (
                      <td className="px-4 py-3 text-right font-mono font-bold text-slate-900 dark:text-slate-100">
                        {formatMoney(totalNum, row.currency)}
                      </td>
                    )}

                    {isVisible("paid") && (
                      <td className="px-4 py-3 text-right font-mono text-emerald-700 dark:text-emerald-400">
                        {formatMoney(paidNum, row.currency)}
                      </td>
                    )}

                    {isVisible("balance") && (
                      <td className="px-4 py-3 text-right font-mono">
                        <span className={balanceNum > 0 ? "font-bold text-amber-700 dark:text-amber-400" : "text-slate-400"}>
                          {formatMoney(balanceNum, row.currency)}
                        </span>
                      </td>
                    )}

                    {isVisible("due_date") && (
                      <td className="px-4 py-3 tabular-nums text-slate-600 dark:text-slate-400">
                        {row.is_credit ? formatDate(row.due_date) : "Al contado"}
                      </td>
                    )}

                    {isVisible("statuses") && (
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5 whitespace-nowrap">
                          <DocumentStatusBadge status={row.document_status} compact />
                          <PaymentStatusBadge status={row.payment_status} compact />
                          <DeliveryStatusBadge status={row.delivery_status} compact />
                          <SunatStatusBadge status={row.sunat_status} compact />
                          <ReturnStatusBadge status={row.return_status} compact />
                        </div>
                      </td>
                    )}

                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {isDraft && canWrite && (
                          <IconAction className="!border-emerald-200 !bg-emerald-50 !text-emerald-700 enabled:hover:!bg-emerald-100 dark:!border-emerald-700/60 dark:!bg-emerald-500/15 dark:!text-emerald-300 dark:enabled:hover:!bg-emerald-500/25" label="Confirmar" tone="primary" onClick={() => onConfirmSale(row)}><Check className="h-3.5 w-3.5" /></IconAction>
                        )}


                        {isSunatRejected && (
                          <IconAction className="!border-violet-200 !bg-violet-50 !text-violet-700 enabled:hover:!bg-violet-100 dark:!border-violet-700/60 dark:!bg-violet-500/15 dark:!text-violet-300 dark:enabled:hover:!bg-violet-500/25" label="Corregir y reenviar" tone="neutral" onClick={() => onRetrySunat(row)}><RefreshCw className="h-3.5 w-3.5" /></IconAction>
                        )}

                        {isConfirmed && isUnpaid && (
                          <>
                            <IconAction className="!border-amber-200 !bg-amber-50 !text-amber-700 enabled:hover:!bg-amber-100 dark:!border-amber-700/60 dark:!bg-amber-500/15 dark:!text-amber-300 dark:enabled:hover:!bg-amber-500/25" label="Cobrar" tone="primary" onClick={() => onOpenPayment(row)}><CreditCard className="h-3.5 w-3.5" /></IconAction>
                            <IconAction className="!border-sky-200 !bg-sky-50 !text-sky-700 enabled:hover:!bg-sky-100 dark:!border-sky-700/60 dark:!bg-sky-500/15 dark:!text-sky-300 dark:enabled:hover:!bg-sky-500/25" label="Ver detalle" tone="neutral" onClick={() => onOpenDetail(row)}><Eye className="h-3.5 w-3.5" /></IconAction>
                          </>
                        )}

                        {isConfirmed && isPartialPaid && (
                          <>
                            <IconAction className="!border-amber-200 !bg-amber-50 !text-amber-700 enabled:hover:!bg-amber-100 dark:!border-amber-700/60 dark:!bg-amber-500/15 dark:!text-amber-300 dark:enabled:hover:!bg-amber-500/25" label="Cobrar saldo" tone="primary" onClick={() => onOpenPayment(row)}><CreditCard className="h-3.5 w-3.5" /></IconAction>
                            <IconAction className="!border-sky-200 !bg-sky-50 !text-sky-700 enabled:hover:!bg-sky-100 dark:!border-sky-700/60 dark:!bg-sky-500/15 dark:!text-sky-300 dark:enabled:hover:!bg-sky-500/25" label="Ver detalle" tone="neutral" onClick={() => onOpenDetail(row)}><Eye className="h-3.5 w-3.5" /></IconAction>
                          </>
                        )}

                        {isPaid && (
                          <>
                            <IconAction className="!border-sky-200 !bg-sky-50 !text-sky-700 enabled:hover:!bg-sky-100 dark:!border-sky-700/60 dark:!bg-sky-500/15 dark:!text-sky-300 dark:enabled:hover:!bg-sky-500/25" label="Ver detalle" tone="neutral" onClick={() => onOpenDetail(row)}><Eye className="h-3.5 w-3.5" /></IconAction>
                            <IconAction className="!border-teal-200 !bg-teal-50 !text-teal-700 enabled:hover:!bg-teal-100 dark:!border-teal-700/60 dark:!bg-teal-500/15 dark:!text-teal-300 dark:enabled:hover:!bg-teal-500/25" label="Repetir venta" tone="neutral" onClick={() => onRepeatSale(row)}><Copy className="h-3.5 w-3.5" /></IconAction>
                          </>
                        )}

                        {isCancelled && (
                          <IconAction className="!border-sky-200 !bg-sky-50 !text-sky-700 enabled:hover:!bg-sky-100 dark:!border-sky-700/60 dark:!bg-sky-500/15 dark:!text-sky-300 dark:enabled:hover:!bg-sky-500/25" label="Ver detalle" tone="neutral" onClick={() => onOpenDetail(row)}><Eye className="h-3.5 w-3.5" /></IconAction>
                        )}

                        <div className="relative">
                          <IconAction className="!border-slate-200 !bg-slate-50 !text-slate-700 enabled:hover:!bg-slate-100 dark:!border-slate-700/60 dark:!bg-slate-500/15 dark:!text-slate-300 dark:enabled:hover:!bg-slate-500/25" label="Más opciones" tone="neutral" onClick={() => setOpenMenuId(menuOpen ? null : row.id || row.sale_id)}><MoreHorizontal className="h-4 w-4" /></IconAction>

                          {menuOpen && (
                            <div
                              onMouseLeave={() => setOpenMenuId(null)}
                              className="absolute right-0 top-8 z-40 w-48 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-slate-800 dark:bg-slate-900"
                            >
                              {isDraft && (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onDuplicateDraft(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Copy className="h-3.5 w-3.5" />
                                    <span>Duplicar borrador</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onConvertToQuotation(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <FileCheck className="h-3.5 w-3.5" />
                                    <span>Convertir a cotización</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onDeleteDraft(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    <span>Eliminar borrador</span>
                                  </button>
                                </>
                              )}

                              {isConfirmed && isUnpaid && (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onRepeatSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Copy className="h-3.5 w-3.5" />
                                    <span>Repetir venta</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onPrintSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Printer className="h-3.5 w-3.5" />
                                    <span>Imprimir comprobante</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onSendSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Send className="h-3.5 w-3.5" />
                                    <span>Enviar a cliente</span>
                                  </button>
                                  {onCreateDebitNote && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onCreateDebitNote(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                    >
                                      <FilePlus className="h-3.5 w-3.5 text-amber-600" />
                                      <span>Crear nota de débito</span>
                                    </button>
                                  )}
                                  {onGenerateGuide && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onGenerateGuide(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                    >
                                      <Truck className="h-3.5 w-3.5 text-teal-600" />
                                      <span>Generar guía</span>
                                    </button>
                                  )}
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (onDownloadPdf) onDownloadPdf(row);
                                      else onPrintSale(row, "A4");
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <FileText className="h-3.5 w-3.5 text-rose-600" />
                                    <span>Descargar PDF</span>
                                  </button>
                                  {canCancel && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onCancelSale(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
                                    >
                                      <AlertOctagon className="h-3.5 w-3.5" />
                                      <span>Anular venta</span>
                                    </button>
                                  )}
                                </>
                              )}

                              {isConfirmed && isPartialPaid && (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onOpenDetail(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Eye className="h-3.5 w-3.5" />
                                    <span>Ver pagos aplicados</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onRescheduleDueDate(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <CalendarClock className="h-3.5 w-3.5" />
                                    <span>Reprogramar vencimiento</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onRepeatSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Copy className="h-3.5 w-3.5" />
                                    <span>Repetir venta</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onPrintSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Printer className="h-3.5 w-3.5" />
                                    <span>Imprimir comprobante</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onSendSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Send className="h-3.5 w-3.5" />
                                    <span>Enviar a cliente</span>
                                  </button>
                                  {onCreateDebitNote && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onCreateDebitNote(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                    >
                                      <FilePlus className="h-3.5 w-3.5 text-amber-600" />
                                      <span>Crear nota de débito</span>
                                    </button>
                                  )}
                                  {onGenerateGuide && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onGenerateGuide(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                    >
                                      <Truck className="h-3.5 w-3.5 text-teal-600" />
                                      <span>Generar guía</span>
                                    </button>
                                  )}
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (onDownloadPdf) onDownloadPdf(row);
                                      else onPrintSale(row, "A4");
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <FileText className="h-3.5 w-3.5 text-rose-600" />
                                    <span>Descargar PDF</span>
                                  </button>
                                  {canCancel && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onCancelSale(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
                                    >
                                      <AlertOctagon className="h-3.5 w-3.5" />
                                      <span>Anular venta</span>
                                    </button>
                                  )}
                                </>
                              )}

                              {isPaid && (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onOpenReturn(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-950/40"
                                  >
                                    <RotateCcw className="h-3.5 w-3.5" />
                                    <span>Iniciar devolución</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onPrintSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Printer className="h-3.5 w-3.5" />
                                    <span>Reimprimir comprobante</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onSendSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Send className="h-3.5 w-3.5" />
                                    <span>Enviar a cliente</span>
                                  </button>
                                  {onCreateDebitNote && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onCreateDebitNote(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                    >
                                      <FilePlus className="h-3.5 w-3.5 text-amber-600" />
                                      <span>Crear nota de débito</span>
                                    </button>
                                  )}
                                  {onGenerateGuide && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onGenerateGuide(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                    >
                                      <Truck className="h-3.5 w-3.5 text-teal-600" />
                                      <span>Generar guía</span>
                                    </button>
                                  )}
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (onDownloadPdf) onDownloadPdf(row);
                                      else onPrintSale(row, "A4");
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <FileText className="h-3.5 w-3.5 text-rose-600" />
                                    <span>Descargar PDF</span>
                                  </button>
                                </>
                              )}

                              {isCancelled && (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onRepeatSale(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <Copy className="h-3.5 w-3.5" />
                                    <span>Repetir como nueva venta</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onViewCancellationReason(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                                  >
                                    <FileText className="h-3.5 w-3.5" />
                                    <span>Ver motivo de anulación</span>
                                  </button>
                                </>
                              )}

                              {isSunatRejected && (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      onViewSunatError(row);
                                      setOpenMenuId(null);
                                    }}
                                    className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
                                  >
                                    <AlertOctagon className="h-3.5 w-3.5" />
                                    <span>Ver error SUNAT</span>
                                  </button>
                                  {canCancel && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onCancelSale(row);
                                        setOpenMenuId(null);
                                      }}
                                      className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
                                    >
                                      <Trash2 className="h-3.5 w-3.5" />
                                      <span>Anular comprobante</span>
                                    </button>
                                  )}
                                </>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}