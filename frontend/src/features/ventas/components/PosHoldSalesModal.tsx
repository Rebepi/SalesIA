import { Clock, Search, ShoppingCart, Trash2, ArrowRight, X, AlertTriangle, AlertCircle, Package } from "lucide-react";
import { PosHoldSale, formatTimeRemaining } from "../support/posHoldSales";
import { money } from "../support/NewSalePOSModal";
import { useState, useMemo } from "react";

interface PosHoldSalesModalProps {
  isOpen: boolean;
  onClose: () => void;
  holdSales: PosHoldSale[];
  currency: string;
  onRetake: (holdSale: PosHoldSale) => void;
  onDiscard: (id: string) => void;
}

function hasStockIssue(sale: PosHoldSale): boolean {
  return sale.cart.some(line => {
    if (!line.product.track_inventory || line.is_free_concept) return false;
    const available = Number(line.product.available_quantity || 0);
    return available < line.quantity;
  });
}

function getStockWarnings(sale: PosHoldSale): string[] {
  return sale.cart
    .filter(line => line.product.track_inventory && !line.is_free_concept)
    .filter(line => Number(line.product.available_quantity || 0) < line.quantity)
    .map(line => {
      const available = Number(line.product.available_quantity || 0);
      if (available <= 0) return `${line.product.name}: sin stock`;
      return `${line.product.name}: disponible ${available}, necesitas ${line.quantity}`;
    });
}

export function PosHoldSalesModal({
  isOpen,
  onClose,
  holdSales,
  currency,
  onRetake,
  onDiscard
}: PosHoldSalesModalProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return holdSales;
    return holdSales.filter(sale => {
      const label = (sale.label || "").toLowerCase();
      const name = (sale.customer?.legal_name || "").toLowerCase();
      const doc = (sale.customer?.doc_number || "").toLowerCase();
      return label.includes(q) || name.includes(q) || doc.includes(q);
    });
  }, [holdSales, searchQuery]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-3xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 shadow-2xl overflow-hidden">
        <header className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80 px-6 py-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-700 dark:bg-amber-400/20 dark:text-amber-300">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Ventas en Espera ({holdSales.length})
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Tickets pausados temporalmente · el stock NO está reservado
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar ventana de ventas en espera"
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        {holdSales.length > 0 && (
          <div className="shrink-0 border-b border-slate-100 dark:border-slate-800 px-6 py-3">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                placeholder="Buscar por etiqueta o nombre de cliente..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 py-2 pl-9 pr-4 text-sm text-slate-800 dark:text-slate-100 outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100 dark:focus:ring-amber-900/30 transition"
              />
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6 space-y-3.5">
          {holdSales.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 mb-3">
                <ShoppingCart className="h-6 w-6" />
              </div>
              <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200">
                No hay ventas en espera
              </h4>
              <p className="mt-1 text-xs text-slate-400 dark:text-slate-500 max-w-sm">
              Cuando un cliente necesite unos minutos, presiona &quot;Poner en espera&quot; en el mostrador para guardar el ticket aquí sin ocupar correlativos fiscales.
              </p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <Search className="h-10 w-10 text-slate-300 dark:text-slate-600 mb-3" />
              <p className="text-sm text-slate-500 dark:text-slate-400">No se encontraron tickets con ese criterio.</p>
            </div>
          ) : (
            filtered.map(sale => {
              const label = sale.label || sale.customer?.legal_name || "Ticket sin nombre";
              const customerName = sale.customer?.legal_name;
              const customerDoc = sale.customer?.doc_number ? `${sale.customer.doc_type || "DOC"}: ${sale.customer.doc_number}` : null;
              const itemsCount = sale.cart.reduce((sum, item) => sum + item.quantity, 0);
              const remaining = formatTimeRemaining(sale.expiresAt);
              const isUrgent = remaining.startsWith("<") || (remaining.includes("min") && !remaining.includes("h") && !remaining.includes("d"));
              const stockIssue = hasStockIssue(sale);
              const stockWarnings = stockIssue ? getStockWarnings(sale) : [];

              return (
                <div
                  key={sale.id}
                  className={`flex flex-col gap-3 rounded-2xl border p-4 transition hover:shadow-md ${stockIssue ? "border-rose-200 bg-rose-50/50 dark:border-rose-900/50 dark:bg-rose-950/20" : "border-slate-200 bg-white hover:border-amber-300 dark:border-slate-800 dark:bg-slate-900/90 dark:hover:border-amber-600/60"}`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <strong className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">
                          {label}
                        </strong>
                        {customerName && label !== customerName && (
                          <span className="text-xs text-slate-500 dark:text-slate-400 truncate">
                            {customerName}
                          </span>
                        )}
                        {customerDoc && (
                          <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500">
                            {customerDoc}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600 dark:text-slate-300">
                        <span className="flex items-center gap-1 font-semibold text-teal-700 dark:text-teal-400">
                          <Package className="h-3.5 w-3.5" />
                          {itemsCount} {itemsCount === 1 ? "artículo" : "artículos"}
                        </span>
                        <span>·</span>
                        <span className="font-bold text-slate-900 dark:text-slate-100">
                          {money(sale.totals.total, sale.currency || currency)}
                        </span>
                        <span>·</span>
                        <span className="text-[11px] text-slate-400 dark:text-slate-500">
                          {new Date(sale.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 pt-0.5">
                        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${isUrgent ? "bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300" : "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300"}`}>
                          <Clock className="h-3 w-3" />
                          {remaining}
                        </span>
                        {stockIssue && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-bold text-rose-800 dark:bg-rose-950/50 dark:text-rose-300">
                            <AlertCircle className="h-3 w-3" />
                            Stock insuficiente
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-start">
                      <button
                        type="button"
                        onClick={() => onDiscard(sale.id)}
                        title="Descartar esta venta en espera"
                        className="inline-flex items-center gap-1 rounded-xl border border-slate-200 dark:border-slate-700 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 dark:text-rose-400 transition"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span>Descartar</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => onRetake(sale)}
                        className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-teal-800 transition"
                      >
                        <span>Retomar</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {stockIssue && (
                    <div className="rounded-xl border border-rose-200 bg-rose-50 dark:border-rose-900/50 dark:bg-rose-950/30 px-3 py-2 space-y-1">
                      <p className="text-[11px] font-bold text-rose-800 dark:text-rose-300 flex items-center gap-1">
                        <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                        Advertencia de stock — el producto puede haber sido vendido a otro cliente:
                      </p>
                      {stockWarnings.map((warning, i) => (
                        <p key={i} className="text-[11px] text-rose-700 dark:text-rose-400 pl-5">
                          · {warning}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        <footer className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/60 px-6 py-3 text-xs text-slate-500 dark:text-slate-400 shrink-0">
          <div className="flex items-center gap-1.5 text-[11px]">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            <span>Tickets temporales. El stock no se reserva hasta confirmar la venta.</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 dark:border-slate-700 px-3.5 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            Cerrar
          </button>
        </footer>
      </div>
    </div>
  );
}
