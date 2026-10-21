import { DocumentStatus, PaymentStatus, DeliveryStatus, SunatStatus, ReturnStatus, SaleRecord, VoucherType } from "../types/ventas";
import { SaleDetailData } from "../types/SaleDetailModal";

export function formatearMoneda(amount: number | string | undefined | null, currency: string = "USD"): string {
  const num = typeof amount === "number" ? amount : Number(amount || 0);
  const safeNum = Number.isFinite(num) ? num : 0;
  const symbol = (currency || "USD").toUpperCase() === "PEN" ? "S/" : "$";
  const formattedNumber = safeNum.toLocaleString("es-PE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${symbol} ${formattedNumber}`;
}

export function formatMoney(amount: number | string | undefined | null, currency: string = "USD"): string {
  const num = typeof amount === "number" ? amount : Number(amount || 0);
  const safeNum = Number.isFinite(num) ? num : 0;
  const symbol = currency.toUpperCase() === "PEN" ? "S/" : "$";
  const formattedNumber = safeNum.toLocaleString("es-PE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${symbol} ${formattedNumber}`;
}

export function formatDateTime(isoString?: string | null): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleString("es-PE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

export function formatDate(isoString?: string | null): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleDateString("es-PE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

export function formatPaymentMethod(method?: string | null): string {
  if (!method) return "Pago";
  const m = String(method).toUpperCase().trim();
  switch (m) {
    case "CASH":
    case "EFECTIVO":
      return "Efectivo";
    case "CARD":
    case "TARJETA":
      return "Tarjeta de Débito / Crédito";
    case "TRANSFER":
    case "BANK_TRANSFER":
    case "TRANSFERENCIA":
      return "Transferencia Bancaria";
    case "CREDIT":
    case "CREDITO":
      return "Crédito Comercial";
    case "STORE_CREDIT":
      return "Crédito en Tienda";
    case "RETURN_CREDIT":
      return "Crédito por Devolución";
    case "EXCHANGE_CREDIT":
      return "Crédito por Canje";
    case "WALLET":
    case "YAPE":
    case "PLIN":
      return "Billetera Digital";
    default:
      if (m.startsWith("W_")) return "Billetera Digital";
      return method;
  }
}

export function formatPaymentMethodShort(method?: string | null): string {
  if (!method) return "Pago";
  const m = String(method).toUpperCase().trim();
  switch (m) {
    case "CASH":
    case "EFECTIVO":
      return "Efectivo";
    case "CARD":
    case "TARJETA":
      return "Tarjeta";
    case "TRANSFER":
    case "BANK_TRANSFER":
    case "TRANSFERENCIA":
      return "Transferencia";
    case "CREDIT":
    case "CREDITO":
      return "Crédito";
    case "WALLET":
    case "YAPE":
    case "PLIN":
      return "Billetera";
    default:
      if (m.startsWith("W_")) return "Billetera";
      return method;
  }
}

export function getDocumentStatusStyle(status: DocumentStatus): string {
  switch (status) {
    case "Borrador":
      return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-300";
    case "Confirmada":
      return "border-teal-200 bg-teal-50 text-teal-800 dark:border-teal-700/60 dark:bg-teal-950/40 dark:text-teal-300";
    case "Anulada":
      return "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-700/60 dark:bg-rose-950/40 dark:text-rose-300";
    default:
      return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300";
  }
}

export function getPaymentStatusStyle(status: PaymentStatus): string {
  switch (status) {
    case "Sin cobrar":
      return "border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300";
    case "Parcial":
      return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-300";
    case "Pagada":
      return "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-700/60 dark:bg-emerald-950/40 dark:text-emerald-300";
    case "Vencida":
      return "border-rose-300 bg-rose-100 text-rose-900 font-semibold dark:border-rose-700 dark:bg-rose-950/60 dark:text-rose-200";
    default:
      return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300";
  }
}

export function getDeliveryStatusStyle(status: DeliveryStatus): string {
  switch (status) {
    case "Pendiente":
      return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-300";
    case "Parcial":
      return "border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-700/60 dark:bg-blue-950/40 dark:text-blue-300";
    case "Entregada":
      return "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-700/60 dark:bg-emerald-950/40 dark:text-emerald-300";
    case "No aplica":
      return "border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400";
    default:
      return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300";
  }
}

export function getSunatStatusStyle(status: SunatStatus): string {
  switch (status) {
    case "No aplica":
      return "border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400";
    case "Pendiente":
      return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-300";
    case "Aceptado":
      return "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-700/60 dark:bg-emerald-950/40 dark:text-emerald-300";
    case "Observado":
      return "border-purple-200 bg-purple-50 text-purple-800 dark:border-purple-700/60 dark:bg-purple-950/40 dark:text-purple-300";
    case "Rechazado":
      return "border-rose-300 bg-rose-100 text-rose-900 font-semibold dark:border-rose-700 dark:bg-rose-950/60 dark:text-rose-200";
    case "Baja":
      return "border-zinc-300 bg-zinc-200 text-zinc-800 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
    default:
      return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300";
  }
}

export function getReturnStatusStyle(status: ReturnStatus): string {
  switch (status) {
    case "Sin devolución":
      return "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400";
    case "Parcial":
      return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-300";
    case "Total":
      return "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-700/60 dark:bg-rose-950/40 dark:text-rose-300";
    default:
      return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300";
  }
}

export function getVoucherTypeLabel(type: VoucherType | string | undefined): string {
  switch (type) {
    case "FACTURA":
    case "INVOICE":
      return "Factura";
    case "BOLETA":
    case "RECEIPT":
      return "Boleta de venta";
    case "NOTA_VENTA":
    case "SALE_NOTE":
      return "Nota de venta";
    case "NOTA_CREDITO":
      return "Nota de crédito";
    case "NOTA_DEBITO":
      return "Nota de débito";
    default:
      return type || "Comprobante";
  }
}

export function getVoucherTypeStyle(type: VoucherType | string | undefined): string {
  switch (type) {
    case "FACTURA":
    case "INVOICE":
      return "border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-700/60 dark:bg-blue-950/40 dark:text-blue-300";
    case "BOLETA":
    case "RECEIPT":
      return "border-teal-200 bg-teal-50 text-teal-800 dark:border-teal-700/60 dark:bg-teal-950/40 dark:text-teal-300";
    case "NOTA_VENTA":
    case "SALE_NOTE":
      return "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
    case "NOTA_CREDITO":
      return "border-purple-200 bg-purple-50 text-purple-800 dark:border-purple-700/60 dark:bg-purple-950/40 dark:text-purple-300";
    case "NOTA_DEBITO":
      return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-300";
    default:
      return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300";
  }
}

export function exportToCSV(rows: SaleRecord[], filename: string = "ventas.csv"): void {
  const headers = [
    "Fecha y Hora",
    "Tipo",
    "Número",
    "Cliente",
    "Documento Cliente",
    "Vendedor",
    "Sede",
    "Moneda",
    "Total",
    "Cobrado",
    "Saldo",
    "Vencimiento",
    "Estado Documento",
    "Estado Cobro",
    "Estado Entrega",
    "Estado SUNAT",
    "Estado Devolución",
  ];

  const escapeCSV = (value: string | number | undefined | null) => {
    const str = String(value ?? "");
    if (str.includes(",") || str.includes('"') || str.includes("\n")) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const lines = rows.map((r) => [
    escapeCSV(formatDateTime(r.created_at)),
    escapeCSV(r.document_type === "INVOICE" ? "Factura" : "Boleta"),
    escapeCSV(r.number),
    escapeCSV(r.customer_name || "Cliente General"),
    escapeCSV(r.customer_document),
    escapeCSV(r.sales_rep_name || "—"),
    escapeCSV(r.branch_name || "—"),
    escapeCSV(r.currency),
    escapeCSV(Number(r.total_amount).toFixed(2)),
    escapeCSV(Number(r.paid_amount).toFixed(2)),
    escapeCSV(Number(r.balance_amount ?? (Number(r.total_amount) - Number(r.paid_amount))).toFixed(2)),
    escapeCSV(formatDate(r.due_date)),
    escapeCSV(r.document_status),
    escapeCSV(r.payment_status),
    escapeCSV(r.delivery_status),
    escapeCSV(r.sunat_status),
    escapeCSV(r.return_status),
  ].join(","));

  const csvContent = "\uFEFF" + [headers.join(","), ...lines].join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function exportToExcel(rows: SaleRecord[], filename: string = "ventas.xls"): void {
  const tableRows = rows.map((r) => `
    <tr>
      <td>${formatDateTime(r.created_at)}</td>
      <td>${r.document_type === "INVOICE" ? "Factura" : "Boleta"}</td>
      <td>${r.number}</td>
      <td>${r.customer_name || "Cliente General"}</td>
      <td>${r.customer_document || "—"}</td>
      <td>${r.sales_rep_name || "—"}</td>
      <td>${r.branch_name || "—"}</td>
      <td>${r.currency}</td>
      <td style="text-align: right;">${Number(r.total_amount).toFixed(2)}</td>
      <td style="text-align: right;">${Number(r.paid_amount).toFixed(2)}</td>
      <td style="text-align: right;">${Number(r.balance_amount ?? (Number(r.total_amount) - Number(r.paid_amount))).toFixed(2)}</td>
      <td>${formatDate(r.due_date)}</td>
      <td>${r.document_status}</td>
      <td>${r.payment_status}</td>
      <td>${r.delivery_status}</td>
      <td>${r.sunat_status}</td>
      <td>${r.return_status}</td>
    </tr>
  `).join("");

  const html = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta http-equiv="content-type" content="application/vnd.ms-excel; charset=UTF-8">
      </head>
      <body>
        <table border="1">
          <thead>
            <tr style="background-color: #0f766e; color: #ffffff;">
              <th>Fecha y Hora</th>
              <th>Tipo</th>
              <th>Número</th>
              <th>Cliente</th>
              <th>Documento</th>
              <th>Vendedor</th>
              <th>Sede</th>
              <th>Moneda</th>
              <th>Total</th>
              <th>Cobrado</th>
              <th>Saldo</th>
              <th>Vencimiento</th>
              <th>Estado Documento</th>
              <th>Estado Cobro</th>
              <th>Estado Entrega</th>
              <th>Estado SUNAT</th>
              <th>Estado Devolución</th>
            </tr>
          </thead>
          <tbody>
            ${tableRows}
          </tbody>
        </table>
      </body>
    </html>
  `;

  const blob = new Blob([html], { type: "application/vnd.ms-excel;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function exportToPDF(rows: SaleRecord[], title: string = "Reporte de Ventas"): void {
  const printWindow = window.open("", "_blank");
  if (!printWindow) return;

  const html = `
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>${title}</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; margin: 20px; color: #1e293b; }
        h1 { font-size: 16px; margin-bottom: 4px; color: #0f766e; }
        p { margin-top: 0; color: #64748b; font-size: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { border: 1px solid #cbd5e1; padding: 4px 6px; text-align: left; }
        th { background-color: #f1f5f9; font-weight: 600; font-size: 9px; text-transform: uppercase; color: #475569; }
        .text-right { text-align: right; }
        .font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
        @media print {
          @page { size: landscape; margin: 10mm; }
        }
      </style>
    </head>
    <body>
      <h1>${title}</h1>
      <p>Generado el ${new Date().toLocaleString("es-PE")} · ${rows.length} comprobantes</p>
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Comprobante</th>
            <th>Cliente</th>
            <th>Documento</th>
            <th>Vendedor</th>
            <th>Sede</th>
            <th>Total</th>
            <th>Cobrado</th>
            <th>Saldo</th>
            <th>Doc</th>
            <th>Cobro</th>
            <th>Entrega</th>
            <th>SUNAT</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(r => `
            <tr>
              <td>${formatDateTime(r.created_at)}</td>
              <td class="font-mono"><strong>${r.number}</strong></td>
              <td>${r.customer_name || "Cliente General"}</td>
              <td>${r.customer_document || "—"}</td>
              <td>${r.sales_rep_name || "—"}</td>
              <td>${r.branch_name || "—"}</td>
              <td class="text-right font-mono">${formatMoney(r.total_amount, r.currency)}</td>
              <td class="text-right font-mono">${formatMoney(r.paid_amount, r.currency)}</td>
              <td class="text-right font-mono">${formatMoney(Number(r.balance_amount ?? (Number(r.total_amount) - Number(r.paid_amount))), r.currency)}</td>
              <td>${r.document_status}</td>
              <td>${r.payment_status}</td>
              <td>${r.delivery_status}</td>
              <td>${r.sunat_status}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      <script>
        window.onload = function() { window.print(); }
      </script>
    </body>
    </html>
  `;

  printWindow.document.write(html);
  printWindow.document.close();
}

export function exportSaleVoucherPDF(sale: SaleRecord | SaleDetailData): void {
  const pdfUrl = (sale as any).pdf_url;
  if (pdfUrl) {
    window.open(pdfUrl, "_blank");
    return;
  }

  const printWindow = window.open("", "_blank");
  if (!printWindow) return;

  const docTypeLabel =
    sale.document_type === "INVOICE"
      ? "FACTURA ELECTRÓNICA"
      : sale.document_type === "RECEIPT"
      ? "BOLETA DE VENTA ELECTRÓNICA"
      : "NOTA DE VENTA";

  const docNumber = sale.number || sale.series || sale.id?.substring(0, 8);
  const currency = sale.currency || "USD";
  const lines = (sale as any).lines || [];
  const subtotal =
    Number(sale.subtotal_amount) ||
    (lines.length > 0
      ? lines.reduce(
          (acc: number, l: any) =>
            acc +
            (Number(l.subtotal) ||
              Number(l.quantity) * Number(l.unit_price) - Number(l.discount || 0)),
          0
        )
      : Number(sale.total_amount || 0));
  const taxAmount = Number(sale.tax_amount) || 0;
  const total = Number(sale.total_amount) || 0;
  const paid = Number(sale.paid_amount) || 0;
  const balanceAmt = Math.max(0, total - paid);
  const isCredit = Boolean((sale as any).is_credit);
  const creditDays = (sale as any).credit_days || 30;

  const linesRows =
    lines.length > 0
      ? lines
          .map((l: any, idx: number) => {
            const qty = Number(l.quantity) || 0;
            const price = Number(l.unit_price) || 0;
            const discount = Number(l.discount) || 0;
            const lineTotal = Number(l.subtotal) || (qty * price - discount);
            return `
              <tr>
                <td style="padding: 7px 10px; border-bottom: 1px solid #e2e8f0; text-align: center; color: #64748b;">${idx + 1}</td>
                <td style="padding: 7px 10px; border-bottom: 1px solid #e2e8f0; font-family: monospace; color: #475569;">${l.sku || "—"}</td>
                <td style="padding: 7px 10px; border-bottom: 1px solid #e2e8f0; font-weight: 500;">${l.product_name || l.name || "Producto"}</td>
                <td style="padding: 7px 10px; border-bottom: 1px solid #e2e8f0; text-align: center; color: #64748b;">${l.unit_of_measure || "NIU"}</td>
                <td style="padding: 7px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-family: monospace;">${qty}</td>
                <td style="padding: 7px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-family: monospace;">${formatMoney(price, currency)}</td>
                <td style="padding: 7px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-family: monospace;">${discount > 0 ? formatMoney(discount, currency) : "—"}</td>
                <td style="padding: 7px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 600; font-family: monospace;">${formatMoney(lineTotal, currency)}</td>
              </tr>
            `;
          })
          .join("")
      : `
          <tr>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: center; color: #64748b;">1</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-family: monospace; color: #475569;">${sale.series || "ITEM"}</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-weight: 500;">Venta de mercaderías / servicios</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: center; color: #64748b;">NIU</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-family: monospace;">1</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-family: monospace;">${formatMoney(subtotal, currency)}</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-family: monospace;">—</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 600; font-family: monospace;">${formatMoney(subtotal, currency)}</td>
          </tr>
        `;

  const payments = (sale as any).payments || [];
  const paymentsRows =
    payments.length > 0
      ? payments
          .map(
            (p: any) => `
            <div style="display: flex; justify-content: space-between; padding: 3px 0; font-size: 11px;">
              <span style="color: #64748b;">${formatPaymentMethod(p.payment_method)}</span>
              <span style="font-family: monospace; font-weight: 600;">${formatMoney(p.amount, currency)}</span>
            </div>
          `
          )
          .join("")
      : `<div style="font-size: 11px; color: #64748b;">${isCredit ? "Venta a crédito" : "Pago al contado"}</div>`;

  const sunatHash = (sale as any).sunat_hash;
  const notes = sale.notes;
  const issueDate = formatDateTime(sale.created_at || (sale as any).confirmed_at);

  const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>${docTypeLabel} - ${docNumber}</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 12mm 15mm;
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 12px;
      color: #1e293b;
      background: #f8fafc;
      padding: 20px;
    }
    .page-container {
      max-width: 800px;
      margin: 0 auto;
      background: #ffffff;
      padding: 32px 36px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    @media print {
      body {
        background: #ffffff;
        padding: 0;
      }
      .page-container {
        border: none;
        box-shadow: none;
        padding: 0;
        max-width: 100%;
      }
      .no-print {
        display: none !important;
      }
    }
    .action-bar {
      max-width: 800px;
      margin: 0 auto 16px auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #0f766e;
      color: #ffffff;
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 13px;
    }
    .btn {
      background: #ffffff;
      color: #0f766e;
      border: none;
      padding: 6px 14px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 12px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn:hover {
      background: #f1f5f9;
    }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.2);
      color: #ffffff;
      margin-left: 8px;
    }
    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  </style>
</head>
<body>
  <div class="action-bar no-print">
    <div>
      <strong>Vista previa del comprobante A4</strong>
      <span style="opacity: 0.85; margin-left: 8px;">Presione "Guardar PDF" o use Ctrl + P</span>
    </div>
    <div>
      <button class="btn" onclick="window.print()">
        📄 Guardar como PDF / Imprimir
      </button>
      <button class="btn btn-secondary" onclick="window.close()">
        Cerrar
      </button>
    </div>
  </div>

  <div class="page-container">
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
      <tr>
        <td style="vertical-align: top; width: 62%;">
          <div style="font-size: 20px; font-weight: 800; color: #0f766e; letter-spacing: -0.5px; margin-bottom: 4px;">
            EMPRESA DEMO S.A.C.
          </div>
          <div style="font-size: 11px; color: #64748b; line-height: 1.5;">
            <div><strong>RUC:</strong> 20000000001</div>
            <div><strong>Dirección:</strong> Av. República de Panamá 3500, Lima, Perú</div>
            ${sale.branch_name ? `<div><strong>Sede / Sucursal:</strong> ${sale.branch_name}</div>` : ""}
            <div><strong>Email:</strong> facturacion@empresa.com · <strong>Tel:</strong> (01) 555-0100</div>
          </div>
        </td>
        <td style="vertical-align: top; width: 38%;">
          <div style="border: 2px solid #0f766e; border-radius: 8px; padding: 14px; text-align: center; background: #f0fdfa;">
            <div style="font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 4px;">
              R.U.C. 20000000001
            </div>
            <div style="font-size: 14px; font-weight: 800; color: #0f766e; padding: 4px 0; text-transform: uppercase;">
              ${docTypeLabel}
            </div>
            <div style="font-size: 15px; font-weight: 800; font-family: monospace; color: #0f172a; margin-top: 4px;">
              ${docNumber}
            </div>
          </div>
        </td>
      </tr>
    </table>

    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; background: #fafafa;">
      <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
        <tr>
          <td style="padding: 3px 0; width: 18%; color: #64748b; font-weight: 600;">SEÑOR(ES):</td>
          <td style="padding: 3px 0; width: 42%; font-weight: 700; color: #0f172a;">${sale.customer_name || "CLIENTE GENERAL"}</td>
          <td style="padding: 3px 0; width: 18%; color: #64748b; font-weight: 600;">FECHA EMISIÓN:</td>
          <td style="padding: 3px 0; width: 22%; font-family: monospace; font-weight: 600;">${issueDate}</td>
        </tr>
        <tr>
          <td style="padding: 3px 0; color: #64748b; font-weight: 600;">RUC / DNI:</td>
          <td style="padding: 3px 0; font-family: monospace; font-weight: 600; color: #334155;">${sale.customer_document || "Sin documento"}</td>
          <td style="padding: 3px 0; color: #64748b; font-weight: 600;">CONDICIÓN PAGO:</td>
          <td style="padding: 3px 0; font-weight: 600;">${isCredit ? `Crédito (${creditDays} días)` : "Al Contado"}</td>
        </tr>
        <tr>
          <td style="padding: 3px 0; color: #64748b; font-weight: 600;">DIRECCIÓN:</td>
          <td style="padding: 3px 0; color: #475569;">${(sale as any).customer_address || (sale as any).delivery_address || "Lima, Perú"}</td>
          <td style="padding: 3px 0; color: #64748b; font-weight: 600;">MONEDA:</td>
          <td style="padding: 3px 0; font-weight: 700; color: #0f766e;">${currency === "PEN" ? "SOLES (PEN)" : "DÓLARES AMERICANOS (USD)"}</td>
        </tr>
        <tr>
          <td style="padding: 3px 0; color: #64748b; font-weight: 600;">ATENDIDO POR:</td>
          <td style="padding: 3px 0; color: #475569;">${sale.sales_rep_name || "Ventas Mostrador"}</td>
          <td style="padding: 3px 0; color: #64748b; font-weight: 600;">ESTADO SUNAT:</td>
          <td style="padding: 3px 0; font-weight: 700; color: #059669;">${sale.sunat_status || "Aceptado"}</td>
        </tr>
      </table>
    </div>

    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 11px;">
      <thead>
        <tr style="background: #f1f5f9; color: #334155;">
          <th style="padding: 8px; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; text-align: center; width: 5%;">#</th>
          <th style="padding: 8px; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; text-align: left; width: 14%;">Código</th>
          <th style="padding: 8px; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; text-align: left; width: 38%;">Descripción</th>
          <th style="padding: 8px; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; text-align: center; width: 7%;">U.M.</th>
          <th style="padding: 8px; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; text-align: right; width: 8%;">Cant.</th>
          <th style="padding: 8px; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; text-align: right; width: 12%;">P. Unit</th>
          <th style="padding: 8px; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; text-align: right; width: 8%;">Dscto</th>
          <th style="padding: 8px; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; text-align: right; width: 12%;">Total</th>
        </tr>
      </thead>
      <tbody>
        ${linesRows}
      </tbody>
    </table>

    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
      <tr>
        <td style="vertical-align: top; width: 58%; padding-right: 20px;">
          <div style="border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; margin-bottom: 12px; background: #f8fafc;">
            <div style="font-size: 11px; font-weight: 700; color: #334155; margin-bottom: 4px;">Información de Pago</div>
            ${paymentsRows}
          </div>

          ${notes ? `
            <div style="font-size: 11px; color: #475569; margin-bottom: 8px;">
              <strong>Observaciones:</strong> ${notes}
            </div>
          ` : ""}

          <div style="border-top: 1px dashed #cbd5e1; padding-top: 10px; margin-top: 10px; font-size: 10px; color: #64748b; line-height: 1.4;">
            <div>Representación impresa de la ${docTypeLabel}, generada en el sistema empresarial.</div>
            ${sunatHash ? `<div><strong>Hash CPE:</strong> <span style="font-family: monospace;">${sunatHash}</span></div>` : ""}
            <div>Consulte la validez de este comprobante en el portal SUNAT con su clave SOL o código digital.</div>
          </div>
        </td>

        <td style="vertical-align: top; width: 42%;">
          <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
            <tr>
              <td style="padding: 4px 8px; color: #64748b;">Op. Gravada:</td>
              <td style="padding: 4px 8px; text-align: right; font-family: monospace; font-weight: 600;">${formatMoney(subtotal, currency)}</td>
            </tr>
            <tr>
              <td style="padding: 4px 8px; color: #64748b;">I.G.V. (18%):</td>
              <td style="padding: 4px 8px; text-align: right; font-family: monospace; font-weight: 600;">${formatMoney(taxAmount, currency)}</td>
            </tr>
            <tr style="border-top: 2px solid #0f766e; border-bottom: 2px solid #0f766e; background: #f0fdfa;">
              <td style="padding: 8px; font-size: 14px; font-weight: 800; color: #0f766e;">TOTAL:</td>
              <td style="padding: 8px; text-align: right; font-size: 15px; font-weight: 800; font-family: monospace; color: #0f766e;">${formatMoney(total, currency)}</td>
            </tr>
            ${paid > 0 ? `
              <tr>
                <td style="padding: 4px 8px; color: #059669; font-weight: 600;">Monto Cobrado:</td>
                <td style="padding: 4px 8px; text-align: right; font-family: monospace; font-weight: 700; color: #059669;">${formatMoney(paid, currency)}</td>
              </tr>
            ` : ""}
            ${balanceAmt > 0 ? `
              <tr>
                <td style="padding: 4px 8px; color: #b91c1c; font-weight: 700;">Saldo Pendiente:</td>
                <td style="padding: 4px 8px; text-align: right; font-family: monospace; font-weight: 800; color: #b91c1c;">${formatMoney(balanceAmt, currency)}</td>
              </tr>
            ` : ""}
          </table>
        </td>
      </tr>
    </table>
  </div>

  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 250);
    };
  </script>
</body>
</html>`;

  printWindow.document.write(html);
  printWindow.document.close();
}

