import React from "react";

export interface PrintableDocumentLayoutProps {
  documentNumber: string;
  date: string;
  customerName: string;
  total: string;
  children: React.ReactNode;
}

export const PrintableDocumentLayout: React.FC<PrintableDocumentLayoutProps> = ({
  documentNumber,
  date,
  customerName,
  total,
  children
}) => {
  return (
    <div className="printable-document w-full bg-white text-slate-900 p-8 rounded-2xl shadow-sm text-left">
      <header className="border-b border-slate-200 pb-4 mb-6 flex justify-between items-start print-avoid-break">
        <div>
          <h2 className="text-xl font-bold tracking-tight">SalesIA Enterprise</h2>
          <p className="text-xs text-slate-500">Comprobante Electrónico</p>
        </div>
        <div className="text-right">
          <span className="text-sm font-mono font-semibold block">{documentNumber}</span>
          <span className="text-xs text-slate-500">{date}</span>
        </div>
      </header>
      <section className="mb-6 print-avoid-break">
        <p className="text-xs text-slate-500">Cliente:</p>
        <p className="text-sm font-semibold">{customerName}</p>
      </section>
      <main className="mb-6">{children}</main>
      <footer className="border-t border-slate-200 pt-4 flex justify-between items-center print-avoid-break">
        <span className="text-xs text-slate-500">Página 1 de 1 · SalesIA Enterprise</span>
        <span className="text-base font-bold font-mono">{total}</span>
      </footer>
    </div>
  );
};
