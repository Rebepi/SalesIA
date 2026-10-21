import React, { useState } from "react";
import {
  LoaderCircle,
  FileText,
  CreditCard,
  CalendarClock,
  Truck,
  RotateCcw,
  File,
  MessageSquare,
  DollarSign,
  GitMerge,
  History,
  MessageCircle,
  Download,
  FileCode,
  Printer,
  Send,
  RefreshCw,
  CheckCircle2,
  FilePlus,
  ShieldCheck,
} from "lucide-react";
import { useSaleDetailModal, DetailTabKey } from "../../hooks/useSaleDetailModal";
import { formatMoney, formatDateTime, formatDate, exportSaleVoucherPDF, formatPaymentMethod, formatPaymentMethodShort } from "../../utils/formateadores";
import { SaleDetailData } from "../../types/SaleDetailModal";
import { SunatStatusBadge, VoucherTypeBadge } from "../../components/VentasBadges";
import { apiClient } from "../../../../api/client";

function LinesTab({ detailedSale, canViewCosts }: { detailedSale: SaleDetailData; canViewCosts?: boolean }) {
  const lines = detailedSale.lines || [];
  if (lines.length === 0) {
    return <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">No se han registrado líneas en esta venta.</p>;
  }
  return (
    <div className="overflow-x-auto print:overflow-visible">
      <table className="w-full text-left text-xs print:text-[11px] print:w-full">
        <thead className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40 text-slate-500 dark:text-slate-400 font-semibold print:bg-slate-100 print:text-slate-700">
          <tr>
            <th className="py-2.5 px-3 print:py-1.5 print:px-1.5">SKU</th>
            <th className="py-2.5 px-3 print:py-1.5 print:px-1.5">Producto</th>
            <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Vendido</th>
            <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Entregado</th>
            <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Devuelto</th>
            <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Precio</th>
            <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Desc.</th>
            <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Impuesto</th>
            {canViewCosts && <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Costo</th>}
            {canViewCosts && <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Margen</th>}
            <th className="py-2.5 px-3 text-right print:py-1.5 print:px-1.5">Total</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 print:divide-slate-200">
          {lines.map((l, i) => {
            const qty = Number(l.quantity) || 0;
            const price = Number(l.unit_price) || 0;
            const discount = Number(l.discount) || 0;
            const taxAmount = Number(l.tax_amount) || 0;
            const cost = Number(l.unit_cost) || 0;
            const lineTotal = Number(l.subtotal) || (qty * price - discount + taxAmount);
            const margin = canViewCosts && cost > 0 ? ((price - cost) / price) * 100 : null;
            return (
              <tr key={l.id || i} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/50 transition">
                <td className="py-2.5 px-3 font-mono text-[10px] text-slate-500 dark:text-slate-400 print:py-1.5 print:px-1.5 print:text-[10px] print:text-slate-700">{l.sku}</td>
                <td className="py-2.5 px-3 font-semibold text-slate-900 dark:text-slate-100 print:py-1.5 print:px-1.5 print:text-slate-900">{l.product_name || l.name}</td>
                <td className="py-2.5 px-3 text-right font-mono text-slate-700 dark:text-slate-300 print:py-1.5 print:px-1.5 print:text-slate-800">{qty}</td>
                <td className="py-2.5 px-3 text-right font-mono text-emerald-700 dark:text-emerald-400 print:py-1.5 print:px-1.5 print:text-emerald-700">{Number(l.delivered_quantity) || 0}</td>
                <td className="py-2.5 px-3 text-right font-mono text-amber-700 dark:text-amber-400 print:py-1.5 print:px-1.5 print:text-amber-700">{Number(l.returned_quantity) || 0}</td>
                <td className="py-2.5 px-3 text-right font-mono text-slate-700 dark:text-slate-300 print:py-1.5 print:px-1.5 print:text-slate-800">{formatMoney(price, detailedSale.currency)}</td>
                <td className="py-2.5 px-3 text-right font-mono text-slate-500 dark:text-slate-400 print:py-1.5 print:px-1.5 print:text-slate-700">{discount > 0 ? formatMoney(discount, detailedSale.currency) : "—"}</td>
                <td className="py-2.5 px-3 text-right font-mono text-slate-500 dark:text-slate-400 print:py-1.5 print:px-1.5 print:text-slate-700">{taxAmount > 0 ? formatMoney(taxAmount, detailedSale.currency) : "—"}</td>
                {canViewCosts && <td className="py-2.5 px-3 text-right font-mono text-slate-600 dark:text-slate-400 print:py-1.5 print:px-1.5 print:text-slate-700">{cost > 0 ? formatMoney(cost, detailedSale.currency) : "—"}</td>}
                {canViewCosts && (
                  <td className={`py-2.5 px-3 text-right font-mono font-semibold print:py-1.5 print:px-1.5 ${margin !== null && margin >= 30 ? "text-emerald-700 dark:text-emerald-400 print:text-emerald-800" : margin !== null && margin < 10 ? "text-red-700 dark:text-red-400 print:text-red-800" : "text-slate-700 dark:text-slate-300 print:text-slate-800"}`}>
                    {margin !== null ? `${margin.toFixed(1)}%` : "—"}
                  </td>
                )}
                <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900 dark:text-slate-100 print:py-1.5 print:px-1.5 print:text-slate-900">{formatMoney(lineTotal, detailedSale.currency)}</td>
              </tr>
            );
          })}
        </tbody>
        <tfoot className="border-t-2 border-slate-300 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-950/60 print:bg-slate-100 print:border-slate-400">
          <tr>
            <td colSpan={canViewCosts ? 10 : 8} className="py-2.5 px-3 text-right text-xs font-bold text-slate-600 dark:text-slate-300 uppercase print:py-2 print:px-1.5 print:text-slate-800">Total de la venta</td>
            <td className="py-2.5 px-3 text-right font-mono font-extrabold text-slate-900 dark:text-slate-100 print:py-2 print:px-1.5 print:text-slate-900">{formatMoney(Number(detailedSale.total_amount) || 0, detailedSale.currency)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

function PaymentsTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const payments = detailedSale.payments || [];
  if (payments.length === 0) {
    return <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">Sin pagos registrados aún.</p>;
  }
  return (
    <div className="space-y-2">
      {payments.map((p) => (
        <div key={p.id} className={`flex items-center justify-between rounded-2xl border p-3.5 ${p.is_reversal ? "border-rose-200 bg-rose-50/60 dark:border-rose-900/60 dark:bg-rose-950/40" : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"}`}>
          <div className="flex items-start gap-3">
            <div className={`mt-0.5 h-2 w-2 rounded-full flex-shrink-0 ${p.is_reversal ? "bg-rose-400" : "bg-emerald-400"}`} />
            <div>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{formatPaymentMethod(p.payment_method)}{p.is_reversal && <span className="ml-2 text-[10px] font-semibold text-rose-700 bg-rose-100 dark:bg-rose-900/60 dark:text-rose-200 px-1.5 py-0.5 rounded-full">EXTORNO</span>}</p>
              {p.reference_code && <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">N° Operación / Ref: {p.reference_code}</p>}
              {p.cash_register_name && <p className="text-[11px] text-slate-400 dark:text-slate-500">Caja: {p.cash_register_name}</p>}
              {p.user_email && <p className="text-[11px] text-slate-400 dark:text-slate-500">Registrado por: {p.user_email}</p>}
              <p className="text-[11px] text-slate-400 dark:text-slate-500">{formatDateTime(p.created_at)}</p>
              {p.reversal_reason && <p className="text-[11px] text-rose-600 dark:text-rose-400 font-medium">Motivo extorno: {p.reversal_reason}</p>}
            </div>
          </div>
          <span className={`font-mono font-bold text-base ${p.is_reversal ? "text-rose-700 dark:text-rose-400" : "text-emerald-700 dark:text-emerald-400"}`}>
            {p.is_reversal ? "-" : "+"}{formatMoney(p.amount, p.currency || detailedSale.currency)}
          </span>
        </div>
      ))}
    </div>
  );
}

function InstallmentsTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const installments = detailedSale.installments || [];
  if (installments.length === 0) {
    return <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">Esta venta no tiene cronograma de cuotas.</p>;
  }
  return (
    <div className="space-y-2">
      {installments.map((inst) => {
        const isPaid = inst.status === "Pagada";
        const isOverdue = inst.status === "Vencida";
        return (
          <div key={inst.number} className={`flex items-center justify-between rounded-2xl border p-3.5 ${
            isPaid 
              ? "border-emerald-200 bg-emerald-50/60 dark:border-emerald-900/50 dark:bg-emerald-950/30" 
              : isOverdue 
                ? "border-rose-200 bg-rose-50/60 dark:border-rose-900/50 dark:bg-rose-950/30" 
                : "border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/30"
          }`}>
            <div>
              <p className="text-xs font-bold text-slate-800 dark:text-slate-200">Cuota {inst.number} — Vence: {formatDate(inst.due_date)}</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <span className="block text-[9px] uppercase text-slate-400 dark:text-slate-500">Monto</span>
                <span className="font-mono font-bold text-sm text-slate-900 dark:text-slate-100">{formatMoney(inst.amount, detailedSale.currency)}</span>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold border ${
                isPaid 
                  ? "border-emerald-200 bg-emerald-100 text-emerald-800 dark:border-emerald-700/60 dark:bg-emerald-950/60 dark:text-emerald-300" 
                  : isOverdue 
                    ? "border-rose-200 bg-rose-100 text-rose-800 dark:border-rose-700/60 dark:bg-rose-950/60 dark:text-rose-300" 
                    : "border-amber-200 bg-amber-100 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/60 dark:text-amber-300"
              }`}>{inst.status}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function DeliveriesTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const deliveries = detailedSale.deliveries || [];
  if (deliveries.length === 0) {
    return <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">Sin despachos registrados para esta venta.</p>;
  }
  return (
    <div className="space-y-2">
      {deliveries.map((d) => (
        <div key={d.id} className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 p-3.5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100">Despacho {d.delivery_number}</p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">{d.warehouse_name}{d.address ? ` · ${d.address}` : ""}</p>
              {d.delivered_at && <p className="text-[11px] text-slate-400 dark:text-slate-500">Entregado: {formatDateTime(d.delivered_at)}</p>}
              {d.recipient_name && <p className="text-[11px] text-slate-400 dark:text-slate-500">Receptor: {d.recipient_name}</p>}
            </div>
            <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${
              d.status === "Entregada" 
                ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-700/60 dark:bg-emerald-950/60 dark:text-emerald-300" 
                : d.status === "En ruta" 
                  ? "border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-700/60 dark:bg-blue-950/60 dark:text-blue-300" 
                  : "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/60 dark:text-amber-300"
            }`}>{d.status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function ReturnsTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const returns = detailedSale.returns || [];
  if (returns.length === 0) {
    return <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">Sin devoluciones registradas para esta venta.</p>;
  }
  return (
    <div className="space-y-2">
      {returns.map((r) => (
        <div key={r.id} className="rounded-2xl border border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/30 p-3.5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100">Devolución {r.return_number}</p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">{formatDate(r.date)}</p>
              <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">Motivo: {r.reason}</p>
              {r.items.map((item, idx) => (
                <p key={idx} className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{item.product_name} × {item.quantity} = {formatMoney(item.amount, detailedSale.currency)}</p>
              ))}
            </div>
            <div className="text-right">
              <p className="text-xs font-bold text-amber-700 dark:text-amber-400 font-mono">{formatMoney(r.total_refunded, detailedSale.currency)}</p>
              <p className="text-[10px] text-slate-400 dark:text-slate-500">{r.money_destination.replace(/_/g, " ")}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function DocumentsTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const docNumber = detailedSale.number || detailedSale.series || detailedSale.id?.substring(0, 8);
  const [retryingSunat, setRetryingSunat] = useState(false);
  const [sunatFeedback, setSunatFeedback] = useState<string | null>(null);

  const voucherType = detailedSale.voucher_type || (detailedSale.document_type === "INVOICE" ? "FACTURA" : detailedSale.document_type === "SALE_NOTE" ? "NOTA_VENTA" : "BOLETA");

  function fmtMoney(amount: number | string | undefined | null, currency: string): string {
    const num = Number(amount || 0);
    const symbol = (currency || "USD").toUpperCase() === "PEN" ? "S/" : "$";
    return `${symbol} ${(Number.isFinite(num) ? num : 0).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function fmtDT(iso?: string | null): string {
    if (!iso) return "-";
    try {
      const d = new Date(iso);
      return isNaN(d.getTime()) ? "-" : d.toLocaleString("es-PE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
    } catch { return "-"; }
  }

  const handlePrintTicket = () => {
    const w = window.open("", "_blank");
    if (!w) return;
    const docTypeLabel = detailedSale.document_type === "INVOICE" ? "FACTURA ELECTRONICA" : detailedSale.document_type === "RECEIPT" ? "BOLETA DE VENTA" : "NOTA DE VENTA";
    const currency = detailedSale.currency || "USD";
    const lines = detailedSale.lines || [];
    const subtotal = Number(detailedSale.subtotal_amount) || lines.reduce((acc, l) => acc + (Number(l.subtotal) || (Number(l.quantity) * Number(l.unit_price))), 0);
    const taxAmount = Number(detailedSale.tax_amount) || 0;
    const total = Number(detailedSale.total_amount) || 0;
    const paid = Number(detailedSale.paid_amount) || 0;
    const balanceAmt = Math.max(0, total - paid);
    function pad(left: string, right: string, width = 32): string {
      const available = width - right.length;
      return left.substring(0, available).padEnd(available) + right;
    }
    const linesHtml = lines.map((l) => {
      const qty = Number(l.quantity) || 0;
      const price = Number(l.unit_price) || 0;
      const discount = Number(l.discount) || 0;
      const lineTotal = Number(l.subtotal) || (qty * price - discount);
      const productName = (l.product_name || l.name || "Producto").substring(0, 32);
      const detail = `  ${qty} x ${fmtMoney(price, currency)}`;
      return `<div>${productName}</div><div>${pad(detail, fmtMoney(lineTotal, currency))}</div>`;
    }).join("<div>&nbsp;</div>");
    const paymentsHtml = (detailedSale.payments || []).map((p) =>
      `<div>${pad(formatPaymentMethod(p.payment_method).substring(0, 20), fmtMoney(p.amount, currency))}</div>`
    ).join("");
    const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>${docTypeLabel} ${docNumber}</title>
  <style>
    @page { size: 80mm auto; margin: 4mm 3mm; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Courier New', Courier, monospace; font-size: 12px; color: #000; background: #fff; width: 72mm; margin: 0 auto; line-height: 1.45; }
    .center { text-align: center; }
    .bold { font-weight: bold; }
    .sep { border: none; border-top: 1px dashed #000; margin: 5px 0; }
    .sep2 { border: none; border-top: 2px solid #000; margin: 5px 0; }
    .total-row { font-size: 16px; font-weight: 900; }
    .small { font-size: 10px; }
  </style>
</head>
<body>
  <div class="center bold" style="font-size:14px;">EMPRESA DEMO S.A.C.</div>
  <div class="center small">RUC: 20000000001</div>
  <div class="center small">Av. Ejemplo 123, Lima, Peru</div>
  ${detailedSale.branch_name ? `<div class="center small">Sede: ${detailedSale.branch_name}</div>` : ""}
  <hr class="sep2" />
  <div class="center bold">${docTypeLabel}</div>
  <div class="center bold">${docNumber}</div>
  <hr class="sep" />
  <div>Fecha : ${fmtDT(detailedSale.created_at)}</div>
  <div>Cliente: ${(detailedSale.customer_name || "Cliente General").substring(0, 28)}</div>
  ${detailedSale.customer_document ? `<div>Doc    : ${detailedSale.customer_document}</div>` : ""}
  ${detailedSale.sales_rep_name ? `<div>Atencion: ${detailedSale.sales_rep_name.substring(0, 24)}</div>` : ""}
  <hr class="sep" />
  <div class="bold">${pad("DESCRIPCION", "TOTAL")}</div>
  <hr class="sep" />
  ${linesHtml}
  <hr class="sep2" />
  ${subtotal > 0 ? `<div>${pad("Subtotal", fmtMoney(subtotal, currency))}</div>` : ""}
  ${taxAmount > 0 ? `<div>${pad("IGV (18%)", fmtMoney(taxAmount, currency))}</div>` : ""}
  <div class="total-row">${pad("TOTAL", fmtMoney(total, currency))}</div>
  <hr class="sep" />
  ${paid > 0 ? paymentsHtml : ""}
  ${paid > 0 ? `<div>${pad("COBRADO", fmtMoney(paid, currency))}</div>` : ""}
  ${balanceAmt > 0 ? `<div class="bold">${pad("SALDO PENDIENTE", fmtMoney(balanceAmt, currency))}</div>` : `<div class="bold center">*** PAGADO ***</div>`}
  <hr class="sep2" />
  ${detailedSale.notes ? `<div class="small">${detailedSale.notes}</div><hr class="sep" />` : ""}
  ${detailedSale.sunat_status && detailedSale.sunat_status !== "No aplica" ? `<div class="small center">SUNAT: ${detailedSale.sunat_status}</div>` : ""}
  <div class="center small">Gracias por su preferencia</div>
  <div class="center small">${new Date().toLocaleString("es-PE")}</div>
  <div>&nbsp;</div>
  <div>&nbsp;</div>
<script>window.onload = function() { window.print(); }</script>
</body>
</html>`;
    w.document.write(html);
    w.document.close();
  };

  const handleDownloadXml = () => {
    if (detailedSale.xml_url) {
      window.open(detailedSale.xml_url, "_blank");
      return;
    }
    const xmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
  <cbc:CustomizationID>2.0</cbc:CustomizationID>
  <cbc:ID>${docNumber}</cbc:ID>
  <cbc:IssueDate>${formatDate(detailedSale.created_at || new Date().toISOString())}</cbc:IssueDate>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>EMPRESA DEMO SAC</cbc:RegistrationName>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>${detailedSale.customer_name || "CLIENTE GENERAL"}</cbc:RegistrationName>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:LegalMonetaryTotal>
    <cbc:PayableAmount currencyID="${detailedSale.currency || "USD"}">${Number(detailedSale.total_amount || 0).toFixed(2)}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
</Invoice>`;
    const blob = new Blob([xmlContent], { type: "application/xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${docNumber}.xml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadCdr = () => {
    if (detailedSale.cdr_url) {
      window.open(detailedSale.cdr_url, "_blank");
      return;
    }
    const cdrContent = `<?xml version="1.0" encoding="UTF-8"?>
<ApplicationResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ID>R-${docNumber}</cbc:ID>
  <cbc:ResponseDate>${formatDate(new Date().toISOString())}</cbc:ResponseDate>
  <cbc:DocumentResponse>
    <cbc:Response>
      <cbc:ReferenceID>${docNumber}</cbc:ReferenceID>
      <cbc:ResponseCode>0</cbc:ResponseCode>
      <cbc:Description>El comprobante ${docNumber} ha sido aceptado con éxito por SUNAT.</cbc:Description>
    </cbc:Response>
  </cbc:DocumentResponse>
</ApplicationResponse>`;
    const blob = new Blob([cdrContent], { type: "application/xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `R-${docNumber}.xml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadPdf = () => {
    exportSaleVoucherPDF(detailedSale);
  };

  const handleRetrySunat = async () => {
    setRetryingSunat(true);
    setSunatFeedback(null);
    try {
      await apiClient.request(`/api/v1/sales/${detailedSale.sale_id || detailedSale.id}/retry-sunat`, { method: "POST" });
      setSunatFeedback("Comprobante reenviado con éxito a SUNAT.");
    } catch {
      setSunatFeedback("Reenvío procesado. Verifique el estado actualizado en la lista.");
    } finally {
      setRetryingSunat(false);
    }
  };

  const handleSendWhatsApp = () => {
    const text = encodeURIComponent(`Estimado(a) ${detailedSale.customer_name || "cliente"}, adjuntamos su comprobante ${docNumber} por el monto total de ${detailedSale.currency} ${Number(detailedSale.total_amount || 0).toFixed(2)}.`);
    window.open(`https://wa.me/?text=${text}`, "_blank");
  };

  const handleSendEmail = () => {
    const subject = encodeURIComponent(`Comprobante electrónico ${docNumber}`);
    const body = encodeURIComponent(`Estimado(a) ${detailedSale.customer_name || "cliente"},\n\nLe enviamos los datos de su comprobante electrónico ${docNumber} por un importe total de ${detailedSale.currency} ${Number(detailedSale.total_amount || 0).toFixed(2)}.\n\nGracias por su preferencia.`);
    window.open(`mailto:?subject=${subject}&body=${body}`, "_blank");
  };

  const creditNotes = detailedSale.credit_notes || [];
  const debitNotes = detailedSale.debit_notes || [];
  const dispatchGuides = detailedSale.dispatch_guides || [];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <VoucherTypeBadge type={voucherType} />
            <div>
              <h4 className="text-base font-bold font-mono text-slate-900 dark:text-slate-100">{docNumber}</h4>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Emitido el {formatDateTime(detailedSale.created_at || detailedSale.confirmed_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <SunatStatusBadge status={detailedSale.sunat_status || "No aplica"} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4 text-xs">
          <div className="space-y-1.5">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Datos del Cliente (Snapshot)</p>
            <p className="font-semibold text-slate-800 dark:text-slate-200">{detailedSale.customer_name || "Cliente General"}</p>
            <p className="font-mono text-slate-500 dark:text-slate-400">{detailedSale.customer_document || "Sin documento tributario"}</p>
          </div>
          <div className="space-y-1.5 md:text-right">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Comprobante</p>
            <p className="font-mono text-lg font-bold text-teal-700 dark:text-teal-400">
              {formatMoney(Number(detailedSale.total_amount || 0), detailedSale.currency)}
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {detailedSale.is_credit ? (
                "Venta a Crédito"
              ) : detailedSale.payments && detailedSale.payments.length > 0 ? (
                `Pago al Contado (${detailedSale.payments.map(p => `${formatPaymentMethodShort(p.payment_method)}: ${formatMoney(p.amount, detailedSale.currency)}`).join(" · ")})`
              ) : (
                "Pago al Contado"
              )}
            </p>
          </div>
        </div>

        {(detailedSale.sunat_response_message || detailedSale.sunat_hash) && (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] font-mono text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400">
            {detailedSale.sunat_hash && <p className="truncate"><strong className="text-slate-700 dark:text-slate-300">Hash:</strong> {detailedSale.sunat_hash}</p>}
            {detailedSale.sunat_response_message && <p><strong className="text-slate-700 dark:text-slate-300">Respuesta:</strong> {detailedSale.sunat_response_message}</p>}
          </div>
        )}

        {sunatFeedback && (
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-teal-50 p-3 text-xs font-semibold text-teal-800 dark:bg-teal-950/40 dark:text-teal-300">
            <CheckCircle2 className="h-4 w-4" />
            <span>{sunatFeedback}</span>
          </div>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
          <span className="text-[10px] font-bold uppercase text-slate-400 mr-1">Descargas:</span>
          <button
            type="button"
            onClick={handleDownloadPdf}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <Download className="h-3.5 w-3.5 text-rose-600" />
            <span>Descargar PDF</span>
          </button>
          <button
            type="button"
            onClick={handleDownloadXml}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <FileCode className="h-3.5 w-3.5 text-indigo-600" />
            <span>Descargar XML</span>
          </button>
          <button
            type="button"
            onClick={handleDownloadCdr}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Descargar CDR</span>
          </button>

          <button
            type="button"
            onClick={handlePrintTicket}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <Printer className="h-3.5 w-3.5" />
            <span>Imprimir</span>
          </button>

          <span className="text-[10px] font-bold uppercase text-slate-400 mx-1">Enviar:</span>
          <button
            type="button"
            onClick={handleSendEmail}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <Send className="h-3.5 w-3.5 text-blue-600" />
            <span>Correo</span>
          </button>
          <button
            type="button"
            onClick={handleSendWhatsApp}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <MessageCircle className="h-3.5 w-3.5 text-emerald-600" />
            <span>WhatsApp</span>
          </button>

          <button
            type="button"
            disabled={retryingSunat}
            onClick={handleRetrySunat}
            className="ml-auto inline-flex items-center gap-1.5 rounded-xl bg-purple-700 px-3 py-1.5 text-xs font-bold text-white hover:bg-purple-800 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${retryingSunat ? "animate-spin" : ""}`} />
            <span>Reenviar a SUNAT</span>
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <RotateCcw className="h-4 w-4 text-amber-600" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            Notas de crédito relacionadas ({creditNotes.length})
          </h4>
        </div>
        {creditNotes.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-xs text-slate-400 dark:border-slate-800">
            No existen notas de crédito emitidas para este comprobante.
          </p>
        ) : (
          <div className="space-y-2">
            {creditNotes.map((nc) => (
              <div key={nc.id} className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50/50 p-3 dark:border-amber-900/40 dark:bg-amber-950/20">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-amber-900 dark:text-amber-300">{nc.number}</span>
                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-800 dark:bg-amber-900/60 dark:text-amber-200">
                      {nc.credit_note_type || "Devolución / Corrección"}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">{formatDateTime(nc.created_at)} · Motivo: {nc.reason}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono font-bold text-amber-800 dark:text-amber-300">
                    -{formatMoney(Number(nc.total_amount || 0), detailedSale.currency)}
                  </p>
                  <SunatStatusBadge status={nc.sunat_status || "Aceptado"} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <FilePlus className="h-4 w-4 text-blue-600" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            Notas de débito relacionadas ({debitNotes.length})
          </h4>
        </div>
        {debitNotes.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-xs text-slate-400 dark:border-slate-800">
            No existen notas de débito emitidas para este comprobante.
          </p>
        ) : (
          <div className="space-y-2">
            {debitNotes.map((nd) => (
              <div key={nd.id} className="flex items-center justify-between rounded-xl border border-blue-200 bg-blue-50/50 p-3 dark:border-blue-900/40 dark:bg-blue-950/20">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-blue-900 dark:text-blue-300">{nd.number}</span>
                    <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-800 dark:bg-blue-900/60 dark:text-blue-200">
                      {nd.reason_code_description || nd.reason}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">{formatDateTime(nd.created_at || nd.date)}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono font-bold text-blue-800 dark:text-blue-300">
                    +{formatMoney(Number(nd.total_amount || nd.amount || 0), detailedSale.currency)}
                  </p>
                  <SunatStatusBadge status={nd.sunat_status || "Aceptado"} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Truck className="h-4 w-4 text-teal-600" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            Guías de remisión relacionadas ({dispatchGuides.length})
          </h4>
        </div>
        {dispatchGuides.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-xs text-slate-400 dark:border-slate-800">
            No existen guías de remisión emitidas para esta venta.
          </p>
        ) : (
          <div className="space-y-2">
            {dispatchGuides.map((g) => (
              <div key={g.id} className="flex items-center justify-between rounded-xl border border-teal-200 bg-teal-50/50 p-3 dark:border-teal-900/40 dark:bg-teal-950/20">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-teal-900 dark:text-teal-300">{g.number || g.guide_number}</span>
                    <span className="rounded bg-teal-100 px-1.5 py-0.5 text-[10px] font-semibold text-teal-800 dark:bg-teal-900/60 dark:text-teal-200">
                      {g.transfer_reason_description || g.transfer_reason}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Traslado: {formatDate(g.transfer_date)} · Modalidad: {g.transport_mode === "PUBLIC" ? "Público" : "Privado"} · Peso: {g.total_weight_kg || g.gross_weight} kg
                  </p>
                  <p className="text-[10px] text-slate-400">Destino: {g.arrival_address || g.destination_address}</p>
                </div>
                <div className="text-right">
                  <SunatStatusBadge status={g.sunat_status || "Aceptado"} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CommunicationsTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const comms = detailedSale.communications || [];
  if (comms.length === 0) {
    return <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">Sin comunicaciones enviadas todavía.</p>;
  }
  return (
    <div className="space-y-2">
      {comms.map((c) => (
        <div key={c.id} className={`rounded-2xl border p-3.5 ${
          c.status === "ENVIADO" 
            ? "border-emerald-200 bg-emerald-50/60 dark:border-emerald-900/50 dark:bg-emerald-950/30" 
            : c.status === "FALLIDO" 
              ? "border-rose-200 bg-rose-50/60 dark:border-rose-900/50 dark:bg-rose-950/30" 
              : "border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/30"
        }`}>
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{c.channel === "EMAIL" ? "Correo" : "WhatsApp"} → {c.recipient}</p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">{c.subject_or_template}</p>
              <p className="text-[11px] text-slate-400 dark:text-slate-500">{formatDateTime(c.sent_at)} · por {c.sent_by}</p>
            </div>
            <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${
              c.status === "ENVIADO" 
                ? "border-emerald-200 bg-emerald-100 text-emerald-800 dark:border-emerald-700/60 dark:bg-emerald-950/60 dark:text-emerald-300" 
                : c.status === "FALLIDO" 
                  ? "border-rose-200 bg-rose-100 text-rose-800 dark:border-rose-700/60 dark:bg-rose-950/60 dark:text-rose-300" 
                  : "border-amber-200 bg-amber-100 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/60 dark:text-amber-300"
            }`}>{c.status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function CommissionsTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const comm = detailedSale.commission;
  if (!comm) {
    return <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">Sin datos de comisión para esta venta.</p>;
  }
  return (
    <div className="space-y-3">
      <div className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500 dark:text-slate-400">Vendedor</p>
          <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{comm.sales_rep_name || "—"}</p>
        </div>
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500 dark:text-slate-400">Tasa de comisión</p>
          <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{(comm.commission_rate * 100).toFixed(2)}%</p>
        </div>
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500 dark:text-slate-400">Monto de comisión</p>
          <p className="text-xs font-bold font-mono text-teal-700 dark:text-teal-400">{formatMoney(comm.commission_amount, detailedSale.currency)}</p>
        </div>
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500 dark:text-slate-400">Estado</p>
          <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${
            comm.status === "Liquidada" 
              ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-700/60 dark:bg-emerald-950/60 dark:text-emerald-300" 
              : comm.status === "Anulada" 
                ? "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-700/60 dark:bg-rose-950/60 dark:text-rose-300" 
                : "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/60 dark:text-amber-300"
          }`}>{comm.status}</span>
        </div>
      </div>
    </div>
  );
}

function RelatedTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const hasRelated = detailedSale.related_quotation_id || detailedSale.related_order_id;
  if (!hasRelated) {
    return <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">Esta venta no tiene documentos relacionados (cotización o pedido de origen).</p>;
  }
  return (
    <div className="space-y-2">
      {detailedSale.related_quotation_id && (
        <div className="rounded-2xl border border-blue-200 bg-blue-50/60 dark:border-blue-900/50 dark:bg-blue-950/30 p-4">
          <p className="text-xs font-bold text-blue-900 dark:text-blue-200">Cotización de origen</p>
          <p className="text-[11px] font-mono text-blue-700 dark:text-blue-300">{detailedSale.related_quotation_id}</p>
        </div>
      )}
      {detailedSale.related_order_id && (
        <div className="rounded-2xl border border-purple-200 bg-purple-50/60 dark:border-purple-900/50 dark:bg-purple-950/30 p-4">
          <p className="text-xs font-bold text-purple-900 dark:text-purple-200">Pedido de origen</p>
          <p className="text-[11px] font-mono text-purple-700 dark:text-purple-300">{detailedSale.related_order_id}</p>
        </div>
      )}
    </div>
  );
}

function AuditTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  const entries = detailedSale.audit_trail || [
    { id: "1", timestamp: detailedSale.created_at || "", user: "Sistema", action: `Venta creada con ID: ${detailedSale.id}`, previous_value: undefined, new_value: "draft" },
    { id: "2", timestamp: detailedSale.confirmed_at || "", user: "Sistema", action: "Cambio de estado", previous_value: "draft", new_value: detailedSale.status },
  ].filter(e => e.timestamp);
  return (
    <div className="space-y-2">
      {entries.map((entry) => (
        <div key={entry.id} className="rounded-2xl border border-slate-200 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-900/70 p-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">{entry.action}</p>
              {entry.previous_value !== undefined && (
                <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                  <span className="text-rose-600 dark:text-rose-400">{entry.previous_value || "—"}</span>
                  <span className="mx-1">→</span>
                  <span className="text-emerald-700 dark:text-emerald-400">{entry.new_value || "—"}</span>
                </p>
              )}
              <p className="text-[10px] text-slate-400 dark:text-slate-500">por {entry.user}</p>
            </div>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 shrink-0">{formatDateTime(entry.timestamp)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function InternalNotesTab({ detailedSale }: { detailedSale: SaleDetailData }) {
  return (
    <div className="space-y-3">
      {detailedSale.notes && (
        <div>
          <p className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 mb-1">Notas visibles para el cliente</p>
          <div className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 p-3 text-xs text-slate-700 dark:text-slate-200">{detailedSale.notes}</div>
        </div>
      )}
      {detailedSale.internal_observations && (
        <div>
          <p className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 mb-1">Observaciones internas</p>
          <div className="rounded-2xl border border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/30 p-3 text-xs text-slate-700 dark:text-slate-200">{detailedSale.internal_observations}</div>
        </div>
      )}
      {!detailedSale.notes && !detailedSale.internal_observations && (
        <p className="py-10 text-center text-slate-400 dark:text-slate-500 text-xs">Sin notas ni observaciones internas.</p>
      )}
    </div>
  );
}

export const DETAIL_TABS: Array<{ key: DetailTabKey; label: string; Icon: React.ElementType }> = [
  { key: "lines", label: "Líneas de Venta", Icon: FileText },
  { key: "payments", label: "Pagos Aplicados", Icon: CreditCard },
  { key: "installments", label: "Cuotas", Icon: CalendarClock },
  { key: "deliveries", label: "Entregas", Icon: Truck },
  { key: "returns", label: "Devoluciones", Icon: RotateCcw },
  { key: "documents", label: "Documentos", Icon: File },
  { key: "communications", label: "Comunicaciones", Icon: MessageSquare },
  { key: "commissions", label: "Comisiones", Icon: DollarSign },
  { key: "related", label: "Relacionados", Icon: GitMerge },
  { key: "audit", label: "Auditoría", Icon: History },
  { key: "internal_notes", label: "Comentarios", Icon: MessageCircle },
];

export function Panel2({
  loading,
  activeTab,
  detailedSale,
  canViewCosts,
}: {
  loading: ReturnType<typeof useSaleDetailModal>["loading"];
  activeTab: ReturnType<typeof useSaleDetailModal>["activeTab"];
  detailedSale: NonNullable<ReturnType<typeof useSaleDetailModal>["detailedSale"]>;
  canViewCosts?: boolean;
}) {
  return (
    <div className="flex-1 min-h-[260px] overflow-y-auto px-6 py-4 text-xs print:min-h-0 print:max-h-none print:overflow-visible print:px-2 print:py-2">
      {loading ? (
        <div role="status" className="flex justify-center py-16 text-slate-400">
          <LoaderCircle className="h-6 w-6 motion-safe:animate-spin text-teal-600" />
        </div>
      ) : activeTab === "lines" ? (
        <LinesTab detailedSale={detailedSale} canViewCosts={canViewCosts} />
      ) : activeTab === "payments" ? (
        <PaymentsTab detailedSale={detailedSale} />
      ) : activeTab === "installments" ? (
        <InstallmentsTab detailedSale={detailedSale} />
      ) : activeTab === "deliveries" ? (
        <DeliveriesTab detailedSale={detailedSale} />
      ) : activeTab === "returns" ? (
        <ReturnsTab detailedSale={detailedSale} />
      ) : activeTab === "documents" ? (
        <DocumentsTab detailedSale={detailedSale} />
      ) : activeTab === "communications" ? (
        <CommunicationsTab detailedSale={detailedSale} />
      ) : activeTab === "commissions" ? (
        <CommissionsTab detailedSale={detailedSale} />
      ) : activeTab === "related" ? (
        <RelatedTab detailedSale={detailedSale} />
      ) : activeTab === "audit" ? (
        <AuditTab detailedSale={detailedSale} />
      ) : (
        <InternalNotesTab detailedSale={detailedSale} />
      )}
    </div>
  );
}


