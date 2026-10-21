import { useOperatingProfile } from "../../../organizacion/components/OperatingProfileContext";
import { useState, useMemo } from "react";
import { AlertCircle, AlertTriangle, Check, ChevronDown, ChevronLeft, ChevronRight, Clock, FileEdit, FileText, LayoutGrid, List, LoaderCircle, Lock, Minus, Package, Plus, RefreshCw, Search, ShoppingCart, Tag, Trash2, BellPlus, X } from "lucide-react";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { CreditTermsPreview } from "../../components/CreditTermsPreview";
import { PosCustomerSelector } from "../../components/PosCustomerSelector";
import { PosPaymentEditor } from "../../components/PosPaymentEditor";
import { PosMissingProductAlertModal } from "../../components/PosMissingProductAlertModal";
import { PosFreeConceptModal } from "../../components/PosFreeConceptModal";
import { PosHoldSalesModal } from "../../components/PosHoldSalesModal";
import { PosHoldSale } from "../../support/posHoldSales";
import { CustomerItem, ProductItem, SaleCartLine, SerialItem, WarehouseItem, PricingResult, SalesRepItem } from "../../types/NewSalePOSModal";
import { money } from "../../support/NewSalePOSModal";
import { useToast } from "../../../../ui/toast/ToastContext";

interface SeccionNuevaVentaPuntoDeVentaProps {
  dialogRef: React.RefObject<HTMLDialogElement>;
  requestClose: () => void;
  customer: CustomerItem | undefined;
  selectCustomer: (cust: string | CustomerItem) => void;
  setCustomerDrawerOpen?: (open: boolean) => void;
  warehouseId: string;
  setWarehouseId: (id: string) => void;
  warehouses: WarehouseItem[];
  selectedWarehouse: WarehouseItem | undefined;
  contextBusy: boolean;
  documentType: "RECEIPT" | "INVOICE" | "SALE_NOTE";
  setDocumentType: (type: "RECEIPT" | "INVOICE" | "SALE_NOTE") => void;
  isCredit: boolean;
  setIsCredit: (isCredit: boolean) => void;
  allowCreditSales?: boolean;
  balance: number;
  currency: string;
  creditUnavailable: boolean;
  creditAvailable: number;
  salesRepId: string;
  setSalesRepId: (id: string) => void;
  salesReps: SalesRepItem[];
  exchangeRate: string;
  setExchangeRate: (rate: string) => void;
  couponCode: string;
  setCouponCode: (coupon: string) => void;
  deliveryAddress: string;
  setDeliveryAddress: (address: string) => void;
  notes: string;
  setNotes: (notes: string) => void;
  internalObservations: string;
  setInternalObservations: (obs: string) => void;
  searchInputRef: React.RefObject<HTMLInputElement>;
  search: string;
  setSearch: (search: string) => void;
  handleSearchKeyDown: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  productsBusy: boolean;
  products: ProductItem[];
  addProduct: (product: ProductItem) => void;
  productTotal: number;
  productOffset: number;
  setProductOffset: React.Dispatch<React.SetStateAction<number>> | ((offset: number) => void);
  error: string;
  cart: SaleCartLine[];
  pricing: Record<string, PricingResult>;
  updateSerials: (productId: string, serials: string[]) => void;
  availableSerials: Record<string, SerialItem[]>;
  updateQuantity: (productId: string, delta: number) => void;
  updateLineQuantityDirect: (productId: string, quantity: number) => void;
  updateLineNote: (productId: string, note: string) => void;
  addFreeConcept: (line: SaleCartLine) => void;
  setCart: React.Dispatch<React.SetStateAction<SaleCartLine[]>>;
  totals: { subtotal: number; discount: number; tax: number; total: number };
  taxIncluded: boolean;
  setPriceDetailsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  pricingBusy: boolean;
  priceDetailsOpen: boolean;
  busy: boolean;
  handlePaymentsChange: (payments: any, valid: boolean) => void;
  paymentsValid: boolean;
  confirmSale: () => void;
  suspendSale?: () => void;
  holdSales?: PosHoldSale[];
  holdModalOpen?: boolean;
  setHoldModalOpen?: (open: boolean) => void;
  retakeHoldSale?: (hold: PosHoldSale) => void;
  discardHoldSale?: (id: string) => void;
  showRucBoletaNotice?: boolean;
  confirmBlockerReason: string | null;
  boletaDniThreshold: number;
  defaultTaxRate?: string;
  tabFilter: "ALL" | "FAVORITES" | "TOP_SELLERS";
  setTabFilter: (tab: "ALL" | "FAVORITES" | "TOP_SELLERS") => void;
  onlyInStock: boolean;
  setOnlyInStock: React.Dispatch<React.SetStateAction<boolean>> | ((val: boolean) => void);
  viewMode: "GRID" | "LIST";
  setViewMode: (mode: "GRID" | "LIST") => void;
  categoryFilter: string;
  setCategoryFilter: (cat: string) => void;
  brandFilter: string;
  setBrandFilter: (brand: string) => void;
  availableCategories: string[];
  availableBrands: string[];
  retryLoadProducts: () => void;
}

export function SeccionNuevaVentaPuntoDeVenta({
  dialogRef,
  requestClose,
  customer,
  selectCustomer,
  warehouseId,
  setWarehouseId,
  warehouses,
  selectedWarehouse,
  contextBusy,
  documentType,
  setDocumentType,
  isCredit,
  setIsCredit,
  allowCreditSales = true,
  balance,
  currency,
  creditUnavailable,
  creditAvailable,
  salesRepId,
  setSalesRepId,
  salesReps,
  exchangeRate,
  setExchangeRate,
  couponCode,
  setCouponCode,
  deliveryAddress,
  setDeliveryAddress,
  notes,
  setNotes,
  internalObservations,
  setInternalObservations,
  searchInputRef,
  search,
  setSearch,
  handleSearchKeyDown,
  productsBusy,
  products,
  addProduct,
  productTotal,
  productOffset,
  setProductOffset,
  error,
  cart,
  pricing,
  updateSerials,
  availableSerials,
  updateQuantity,
  updateLineQuantityDirect,
  updateLineNote,
  addFreeConcept,
  setCart,
  totals,
  taxIncluded,
  setPriceDetailsOpen,
  pricingBusy,
  priceDetailsOpen,
  busy,
  handlePaymentsChange,
  paymentsValid,
  confirmSale,
  suspendSale,
  holdSales = [],
  holdModalOpen = false,
  setHoldModalOpen,
  retakeHoldSale,
  discardHoldSale,
  showRucBoletaNotice,
  confirmBlockerReason,
  boletaDniThreshold,
  defaultTaxRate = "0.18",
  tabFilter,
  setTabFilter,
  onlyInStock,
  setOnlyInStock,
  viewMode,
  setViewMode,
  categoryFilter,
  setCategoryFilter,
  brandFilter,
  setBrandFilter,
  availableCategories,
  availableBrands,
  retryLoadProducts,
}: SeccionNuevaVentaPuntoDeVentaProps) {
  const toast = useToast();
  const { enabled } = useOperatingProfile();
  const [missingModalOpen, setMissingModalOpen] = useState(false);
  const [freeConceptModalOpen, setFreeConceptModalOpen] = useState(false);
  const [moreOptionsOpen, setMoreOptionsOpen] = useState(false);
  const [openNoteLineId, setOpenNoteLineId] = useState<string | null>(null);
  const [paymentsCount, setPaymentsCount] = useState(1);
  const [userExpandedCart, setUserExpandedCart] = useState(false);

  const cartCollapsed = paymentsCount >= 2 && !userExpandedCart;

  const cartSummaryText = useMemo(() => {
    const count = cart.length;
    const label = count === 1 ? "1 producto" : `${count} productos`;
    return `${label} · ${money(totals.total, currency)}`;
  }, [cart.length, totals.total, currency]);

  const isInvoice = documentType === "INVOICE";
  const isSaleNote = documentType === "SALE_NOTE";
  const customerHasRuc = Boolean(customer && (customer.doc_type?.toUpperCase() === "RUC" || customer.doc_number?.replace(/\D/g, "").length === 11));
  const isWalkIn = Boolean(!customer || customer.is_walk_in || customer.doc_type === "SIN_DOCUMENTO");

  const dualCurrencyEquivalent = useMemo(() => {
    const rate = Number(exchangeRate) || 1;
    if (rate <= 0) return null;
    if (currency === "USD") {
      return `~ S/ ${(totals.total * rate).toFixed(2)} PEN`;
    }
    if (currency === "PEN") {
      return `~ $ ${(totals.total / rate).toFixed(2)} USD`;
    }
    return null;
  }, [totals.total, exchangeRate, currency]);

  return (
    <dialog
      ref={dialogRef}
      id="scr-016-new-sale-pos-dialog"
      onCancel={event => { event.preventDefault(); requestClose(); }}
      aria-labelledby="pos-title"
      className="app-modal-panel pos-modal flex h-[96vh] max-h-[96vh] w-[min(98vw,1620px)] flex-col rounded-3xl border-0 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 p-0 shadow-2xl backdrop:bg-slate-950/75 overflow-hidden"
    >
      <header className="flex shrink-0 items-center justify-between border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/90 px-5 py-2.5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-teal-700 text-white shadow-md">
            <ShoppingCart className="h-4 w-4" />
          </div>
          <div>
            <h2 id="pos-title" className="text-sm font-bold text-slate-900 dark:text-slate-100">
              Nueva Venta (Punto de Venta / Mostrador)
            </h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Catálogo de disponibilidad a la izquierda y canasta de compra a la derecha en tiempo real
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {setHoldModalOpen && (
            <button
              type="button"
              onClick={() => setHoldModalOpen(true)}
              className="relative flex items-center gap-1.5 rounded-xl border border-amber-300 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/40 px-3 py-1.5 text-xs font-semibold text-amber-900 dark:text-amber-200 hover:bg-amber-100 dark:hover:bg-amber-900/60 transition shadow-sm"
              title="Ver ventas en espera (pausadas)"
            >
              <Clock className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
              <span>En espera</span>
              {holdSales.length > 0 && (
                <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-amber-600 px-1.5 text-[10px] font-bold text-white">
                  {holdSales.length}
                </span>
              )}
            </button>
          )}
          <button
            type="button"
            onClick={requestClose}
            aria-label="Cerrar mostrador de venta"
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-200/60 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </header>

      <div className="shrink-0 border-b border-slate-100 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-900/60 px-5 py-2">
        <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-[1fr_1.3fr_1fr_0.8fr]">
          <div>
            <label className="mb-0.5 block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Almacén de Despacho
            </label>
            {warehouses.length === 0 ? (
              <div className="rounded-xl border border-amber-300 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/40 px-2 py-1 text-[11px] font-semibold text-amber-900 dark:text-amber-200 truncate">
                No tienes un almacén asignado. Pide a un administrador que te lo configure.
              </div>
            ) : warehouses.length === 1 ? (
              <div className="flex h-[34px] items-center gap-2 rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-700 dark:bg-slate-800 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 shadow-inner">
                <Lock className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                <span className="truncate">{warehouses[0].name} ({warehouses[0].code})</span>
              </div>
            ) : (
              <CustomSelect remote={{ resource: "warehouses" }}
                value={warehouseId || ""}
                onChange={event => { setWarehouseId(event.target.value); setProductOffset(0); }}
                searchable
                className="h-[34px] w-full rounded-xl border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-2 py-1 text-xs outline-none focus:border-teal-600"
              >
                <option value="">Seleccionar almacén</option>
                {warehouses.map(item => (
                  <option key={item.warehouse_id} value={item.warehouse_id}>
                    {item.name} ({item.code})
                  </option>
                ))}
              </CustomSelect>
            )}
          </div>

          <PosCustomerSelector
            value={customer}
            onChange={selectCustomer}
            documentType={documentType}
            onRequestInvoice={() => setDocumentType("INVOICE")}
            disabled={busy}
          />

          <div>
            <label className="mb-0.5 block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Tipo de Comprobante
            </label>
            <CustomSelect
              value={documentType}
              onChange={event => setDocumentType(event.target.value as "RECEIPT" | "INVOICE" | "SALE_NOTE")}
              className="h-[34px] w-full rounded-xl border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-2 py-1 text-xs font-semibold outline-none focus:border-teal-600"
            >
              <option value="RECEIPT">Boleta de venta</option>
              <option value="INVOICE">Factura</option>
              <option value="SALE_NOTE">Nota de venta (sin valor tributario)</option>
            </CustomSelect>
          </div>

          <div>
            <label className="mb-0.5 block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Condición de Pago
            </label>
            <CustomSelect
              value={isCredit ? "credit" : "cash"}
              onChange={event => setIsCredit(event.target.value === "credit")}
              className="h-[34px] w-full rounded-xl border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 px-2 py-1 text-xs outline-none focus:border-teal-600"
            >
              <option value="cash">Contado</option>
              {allowCreditSales ? (
                <option value="credit" disabled={isWalkIn || !enabled("credit")}>Crédito comercial</option>
              ) : (
                <option value="credit" disabled>Crédito comercial (Desactivado en configuración)</option>
              )}
            </CustomSelect>
          </div>
        </div>

        {showRucBoletaNotice && (
          <div className="mt-2 flex items-center justify-between rounded-xl border border-amber-300 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/40 px-3 py-1.5 text-xs text-amber-900 dark:text-amber-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
              <span>
                Este cliente tiene <strong>RUC</strong> ({customer?.doc_number}). Con boleta no podrá usar crédito fiscal.
              </span>
            </div>
            <button
              type="button"
              onClick={() => setDocumentType("INVOICE")}
              className="rounded-lg bg-amber-700 px-2.5 py-1 text-[11px] font-bold text-white shadow-sm hover:bg-amber-800"
            >
              Cambiar a Factura
            </button>
          </div>
        )}

        {isSaleNote && (
          <div className="mt-2 flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 dark:border-blue-900/50 dark:bg-blue-950/40 px-3 py-1.5 text-xs text-blue-900 dark:text-blue-200">
            <FileText className="h-4 w-4 shrink-0 text-blue-600" />
            <span>Documento interno de control, sin valor tributario ante SUNAT. Estado tributario: No aplica.</span>
          </div>
        )}

        {isInvoice && customer && !customerHasRuc && (
          <div className="mt-2 flex items-center gap-2 rounded-xl border border-rose-300 bg-rose-50 dark:border-rose-900/50 dark:bg-rose-950/40 px-3 py-1.5 text-xs text-rose-900 dark:text-rose-200">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
            <span>Para emitir una <strong>Factura</strong> se exige un cliente con RUC válido (11 dígitos), razón social y dirección fiscal.</span>
          </div>
        )}

        {documentType === "RECEIPT" && totals.total >= boletaDniThreshold && isWalkIn && (
          <div className="mt-2 flex items-center gap-2 rounded-xl border border-amber-300 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/40 px-3 py-1.5 text-xs text-amber-900 dark:text-amber-200">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
            <span>Para este monto ({money(totals.total, currency)}) se necesita identificar al comprador con DNI según normativa SUNAT (umbral: {money(boletaDniThreshold, currency)}).</span>
          </div>
        )}

        {customer?.is_credit_blocked && (
          <div role="alert" className="mt-2 rounded-xl bg-rose-50 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300 px-3 py-1.5 text-xs font-semibold">
            Crédito bloqueado: {customer.credit_block_reason || "requiere revisión comercial"}
          </div>
        )}
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 overflow-hidden lg:grid-cols-[1.25fr_0.75fr] xl:grid-cols-[1.3fr_0.7fr]">
        <section className="flex flex-col border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 p-3.5 overflow-hidden">
          <div className="shrink-0 mb-2.5 flex flex-wrap items-center gap-2 text-xs">
            <div className="relative flex-1 min-w-[140px]">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                ref={searchInputRef}
                value={search}
                onChange={event => { setSearch(event.target.value); setProductOffset(0); }}
                onKeyDown={handleSearchKeyDown}
                disabled={!warehouseId}
                placeholder={warehouseId ? "Buscar nombre, SKU, código…" : "Selecciona un almacén..."}
                title="Buscar por nombre, SKU, marca o código de barras"
                aria-label="Buscar producto o escanear"
                className="w-full rounded-xl border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 py-1.5 pl-8 pr-3 text-xs shadow-sm outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100 dark:focus:ring-teal-950 disabled:bg-slate-100 dark:disabled:bg-slate-800"
              />
            </div>

            <div className="flex shrink-0 items-center gap-0.5 rounded-xl bg-slate-200/60 dark:bg-slate-800/80 p-0.5">
              <button
                type="button"
                onClick={() => setTabFilter("ALL")}
                className={`rounded-lg px-2 py-1 text-[11px] font-bold transition ${tabFilter === "ALL" ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"}`}
              >
                Todos
              </button>
              <button
                type="button"
                onClick={() => setTabFilter("FAVORITES")}
                className={`rounded-lg px-2 py-1 text-[11px] font-bold transition ${tabFilter === "FAVORITES" ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"}`}
              >
                Favoritos
              </button>
              <button
                type="button"
                onClick={() => setTabFilter("TOP_SELLERS")}
                className={`rounded-lg px-2 py-1 text-[11px] font-bold transition ${tabFilter === "TOP_SELLERS" ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"}`}
              >
                Más vendidos
              </button>
            </div>

            <label className="flex shrink-0 items-center gap-1.5 cursor-pointer text-[11px] font-medium text-slate-600 dark:text-slate-300 whitespace-nowrap">
              <input
                type="checkbox"
                checked={onlyInStock}
                onChange={e => setOnlyInStock(e.target.checked)}
                className="h-3.5 w-3.5 rounded border-slate-300 dark:border-slate-600 dark:bg-slate-800 text-teal-600 focus:ring-teal-500"
              />
              <span>Solo con stock</span>
            </label>

            {availableCategories.length > 0 && (
              <select
                value={categoryFilter}
                onChange={e => setCategoryFilter(e.target.value)}
                className="shrink-0 rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 px-2 py-1 text-[11px] font-medium text-slate-700 outline-none"
              >
                <option value="">Categorías</option>
                {availableCategories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            )}

            {availableBrands.length > 0 && (
              <select
                value={brandFilter}
                onChange={e => setBrandFilter(e.target.value)}
                className="shrink-0 rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 px-2 py-1 text-[11px] font-medium text-slate-700 outline-none"
              >
                <option value="">Marcas</option>
                {availableBrands.map(b => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            )}

            <div className="flex shrink-0 items-center rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 p-0.5">
              <button
                type="button"
                onClick={() => setViewMode("GRID")}
                title="Vista en tarjetas"
                className={`rounded p-1 ${viewMode === "GRID" ? "bg-slate-100 text-teal-700 dark:bg-slate-700 dark:text-teal-300" : "text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"}`}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setViewMode("LIST")}
                title="Vista en lista"
                className={`rounded p-1 ${viewMode === "LIST" ? "bg-slate-100 text-teal-700 dark:bg-slate-700 dark:text-teal-300" : "text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"}`}
              >
                <List className="h-3.5 w-3.5" />
              </button>
            </div>

            <button
              type="button"
              onClick={() => setMissingModalOpen(true)}
              title="Avisar falta"
              aria-label="Avisar falta"
              className="shrink-0 flex h-7 w-7 items-center justify-center rounded-lg border border-teal-200 bg-teal-50 dark:border-teal-800/60 dark:bg-teal-950/50 text-teal-700 dark:text-teal-300 shadow-sm transition hover:bg-teal-100 dark:hover:bg-teal-900/60"
            >
              <BellPlus className="h-3.5 w-3.5" />
            </button>

            <button
              type="button"
              onClick={() => setFreeConceptModalOpen(true)}
              title="Concepto libre"
              aria-label="Concepto libre"
              className="shrink-0 flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 text-slate-700 dark:text-slate-200 shadow-sm transition hover:bg-slate-50 dark:hover:bg-slate-700"
            >
              <Tag className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto pr-1">
            {productsBusy ? (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-4">
                {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                  <div key={i} className="animate-pulse rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 p-2.5 space-y-2">
                    <div className="flex items-start justify-between">
                      <div className="h-3.5 w-3/4 rounded bg-slate-200 dark:bg-slate-800" />
                      <div className="h-3.5 w-5 rounded-full bg-slate-200 dark:bg-slate-800" />
                    </div>
                    <div className="h-2.5 w-1/2 rounded bg-slate-100 dark:bg-slate-800/60" />
                    <div className="mt-2 flex items-center justify-between pt-1.5 border-t border-slate-100 dark:border-slate-800">
                      <div className="h-3.5 w-12 rounded bg-slate-200 dark:bg-slate-800" />
                      <div className="h-3.5 w-10 rounded-full bg-slate-200 dark:bg-slate-800" />
                    </div>
                  </div>
                ))}
              </div>
            ) : !warehouseId ? (
              <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8 text-center text-xs text-slate-500 dark:text-slate-400">
                <Package className="mb-2 h-8 w-8 text-slate-400 dark:text-slate-500" />
                <p className="font-semibold text-slate-700 dark:text-slate-200">Elige un almacén para ver productos.</p>
              </div>
            ) : error ? (
              <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-rose-200 bg-rose-50/50 dark:border-rose-900/40 dark:bg-rose-950/30 p-8 text-center text-xs text-rose-800 dark:text-rose-300">
                <AlertCircle className="mb-2 h-8 w-8 text-rose-500" />
                <p className="font-bold text-sm">No pudimos cargar el catálogo</p>
                <p className="mt-1 text-slate-500 dark:text-slate-400">{error}</p>
                <button
                  type="button"
                  onClick={retryLoadProducts}
                  className="mt-3 inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-4 py-2 font-bold text-white shadow hover:bg-teal-800"
                >
                  <RefreshCw className="h-3.5 w-3.5" /> Reintentar
                </button>
              </div>
            ) : products.length === 0 && search.trim() ? (
              <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8 text-center text-xs text-slate-500 dark:text-slate-400">
                <Package className="mb-2 h-8 w-8 text-slate-400 dark:text-slate-500" />
                <p className="font-semibold text-slate-700 dark:text-slate-200">Nada para &apos;{search}&apos;. Revisa la ortografía o quita filtros.</p>
                <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
                  <button
                    type="button"
                    onClick={() => setMissingModalOpen(true)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-teal-600 bg-teal-50 dark:border-teal-700 dark:bg-teal-950/60 dark:text-teal-300 px-3 py-1.5 font-bold text-teal-800 hover:bg-teal-100 dark:hover:bg-teal-900/60"
                  >
                    <BellPlus className="h-3.5 w-3.5" /> Avisar que falta este producto
                  </button>
                  <button
                    type="button"
                    onClick={() => setFreeConceptModalOpen(true)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 px-3 py-1.5 font-bold text-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700"
                  >
                    <Tag className="h-3.5 w-3.5" /> Concepto libre
                  </button>
                </div>
              </div>
            ) : products.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8 text-center text-xs text-slate-500 dark:text-slate-400">
                <Package className="mb-2 h-8 w-8 text-slate-400 dark:text-slate-500" />
                <p className="font-semibold text-slate-700 dark:text-slate-200">Este almacén no tiene productos con stock.</p>
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() => setFreeConceptModalOpen(true)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700"
                  >
                    <Tag className="h-3.5 w-3.5" /> Cobrar concepto libre (flete / servicio)
                  </button>
                </div>
              </div>
            ) : viewMode === "GRID" ? (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-4">
                {products.map(product => {
                  const available = Number(product.available_quantity || 0);
                  const isAvailable = available > 0 || !product.track_inventory;
                  const inCart = cart.find(c => c.product.id === product.id);
                  const otherStockCount = product.other_warehouse_stock ? Object.values(product.other_warehouse_stock).reduce((sum, qty) => sum + qty, 0) : 0;

                  return (
                    <button
                      key={product.id}
                      type="button"
                      onClick={() => addProduct(product)}
                      className={`group relative flex flex-col justify-between rounded-xl border p-2 text-left transition-all duration-150 hover:shadow-sm ${inCart ? "border-teal-500 bg-teal-50/70 ring-1 ring-teal-400 dark:border-teal-400 dark:bg-teal-950/60 dark:ring-teal-700" : !isAvailable && product.track_inventory ? "opacity-50 hover:opacity-90 border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-900/50" : "border-slate-200 bg-white hover:border-teal-400 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-teal-500"}`}
                    >
                      <div>
                        <div className="flex items-start justify-between gap-1">
                          <strong className="line-clamp-1 text-xs font-semibold text-slate-900 dark:text-slate-100 group-hover:text-teal-700 dark:group-hover:text-teal-300" title={product.name}>
                            {product.name}
                          </strong>
                          {inCart && (
                            <span className="flex h-4 min-w-[16px] px-1 shrink-0 items-center justify-center rounded-full bg-teal-700 dark:bg-teal-600 text-[9px] font-bold text-white shadow-sm">
                              {inCart.quantity}
                            </span>
                          )}
                        </div>
                        <div className="mt-0.5 flex items-center gap-1 font-mono text-[10px] text-slate-500 dark:text-slate-400 font-normal tracking-tight">
                          <span>{product.sku}</span>
                          <span>·</span>
                          <span>{product.unit_of_measure}</span>
                          {product.brand_name && (
                            <>
                              <span>·</span>
                              <span className="font-sans font-medium text-slate-600 dark:text-slate-400 truncate max-w-[60px]">{product.brand_name}</span>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="mt-2 flex items-center justify-between border-t border-slate-100 dark:border-slate-800/80 pt-1">
                        <strong className="text-xs font-bold text-teal-800 dark:text-teal-400 font-mono">
                          {money(Number(product.unit_price), currency)}
                        </strong>
                        <div className="flex flex-col items-end gap-0.5">
                          <span
                            className={`rounded-full px-1.5 py-0.2 text-[9px] font-semibold ${!product.track_inventory ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300" : isAvailable ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300" : "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"}`}
                          >
                            {!product.track_inventory ? "Servicio" : isAvailable ? `${available} disp.` : "Sin stock"}
                          </span>
                          {otherStockCount > 0 && !isAvailable && (
                            <span className="text-[9px] font-medium text-slate-500 dark:text-slate-400">
                              +{otherStockCount} en otro almacén
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
                {products.map(product => {
                  const available = Number(product.available_quantity || 0);
                  const isAvailable = available > 0 || !product.track_inventory;
                  const inCart = cart.find(c => c.product.id === product.id);

                  return (
                    <div
                      key={product.id}
                      className={`flex items-center justify-between gap-2.5 p-2 transition hover:bg-slate-50 dark:hover:bg-slate-800/60 ${!isAvailable && product.track_inventory ? "opacity-50 hover:opacity-90 bg-slate-50/50 dark:bg-slate-900/40" : inCart ? "bg-teal-50/40 dark:bg-teal-950/40" : ""}`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0 flex-1">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                          <Package className="h-3.5 w-3.5" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <strong className="block truncate text-xs font-semibold text-slate-900 dark:text-slate-100">
                            {product.name}
                          </strong>
                          <div className="flex items-center gap-1 font-mono text-[10px] text-slate-500 dark:text-slate-400 font-normal tracking-tight">
                            <span>{product.sku}</span>
                            <span>·</span>
                            <span>{product.unit_of_measure}</span>
                            {product.brand_name && (
                              <>
                                <span>·</span>
                                <span className="font-sans font-medium text-slate-600 dark:text-slate-400">{product.brand_name}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        <div className="text-right">
                          <strong className="block font-mono text-xs font-bold text-teal-800 dark:text-teal-400">
                            {money(Number(product.unit_price), currency)}
                          </strong>
                          <span
                            className={`inline-block rounded-full px-1.5 py-0.2 text-[9px] font-semibold ${!product.track_inventory ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300" : isAvailable ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300" : "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"}`}
                          >
                            {!product.track_inventory ? "Servicio" : isAvailable ? `${available} disp.` : "Sin stock"}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => addProduct(product)}
                          className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-700 hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-500 text-white shadow-sm transition active:scale-95"
                          aria-label={`Agregar ${product.name}`}
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {productTotal > 24 && (
            <div className="mt-2 flex shrink-0 items-center justify-between border-t border-slate-200 dark:border-slate-800 pt-1.5 text-[11px] text-slate-500 dark:text-slate-400">
              <span>{productOffset + 1}-{Math.min(productOffset + 24, productTotal)} de {productTotal}</span>
              <div className="flex gap-1">
                <button
                  type="button"
                  disabled={productOffset === 0}
                  onClick={() => setProductOffset(Math.max(0, productOffset - 24))}
                  className="rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-800 p-1 hover:bg-slate-50 disabled:opacity-40"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  disabled={productOffset + 24 >= productTotal}
                  onClick={() => setProductOffset(productOffset + 24)}
                  className="rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-800 p-1 hover:bg-slate-50 disabled:opacity-40"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
        </section>

        <section className="flex flex-col bg-white dark:bg-slate-900 overflow-hidden min-h-0">
          <div className="relative flex shrink-0 items-center justify-between border-b border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/80 px-4 py-2.5">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
              Productos de la venta ({cart.length})
            </span>
            <div className="flex items-center gap-2">
              {cart.length > 0 && (
                <button
                  type="button"
                  onClick={() => setCart([])}
                  className="text-[11px] font-semibold text-rose-600 dark:text-rose-400 hover:underline"
                >
                  Vaciar canasta
                </button>
              )}
              {userExpandedCart && paymentsCount >= 2 && (
                <button
                  type="button"
                  onClick={() => setUserExpandedCart(false)}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-[11px] font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 shadow-sm"
                  title="Colapsar canasta"
                >
                  <ChevronRight className="h-3 w-3" />
                  <span>Colapsar</span>
                </button>
              )}
              <button
                type="button"
                onClick={() => setMoreOptionsOpen(!moreOptionsOpen)}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-[11px] font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 shadow-sm"
              >
                <span>⋯ Opciones</span>
                <ChevronDown className={`h-3 w-3 transition ${moreOptionsOpen ? "rotate-180" : ""}`} />
              </button>
            </div>

            {moreOptionsOpen && (
              <div className="absolute right-4 top-full z-40 mt-1 w-80 rounded-2xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 p-3 text-[11px] shadow-2xl space-y-2">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-1.5">
                  <strong className="text-xs font-bold text-slate-900 dark:text-slate-100">Más opciones</strong>
                  <button
                    type="button"
                    onClick={() => setMoreOptionsOpen(false)}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div>
                  <label className="block font-medium text-slate-600 dark:text-slate-300">Vendedor responsable</label>
                  <CustomSelect remote={{ resource: "sales_reps" }}
                    value={salesRepId}
                    onChange={e => setSalesRepId(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 p-1.5 text-xs outline-none"
                  >
                    <option value="">Usuario actual / predeterminado</option>
                    {salesReps.map(rep => (
                      <option key={rep.id} value={rep.id}>
                        {rep.full_name} ({rep.code})
                      </option>
                    ))}
                  </CustomSelect>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block font-medium text-slate-600 dark:text-slate-300">Moneda</label>
                    <input
                      type="text"
                      disabled
                      value={currency}
                      className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-100 dark:border-slate-700 dark:bg-slate-800 p-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-slate-600 dark:text-slate-300">Tipo de cambio</label>
                    <input
                      type="number"
                      step="0.001"
                      value={exchangeRate}
                      onChange={e => setExchangeRate(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 p-1.5 text-xs outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-slate-600 dark:text-slate-300">Cupón promocional</label>
                  <input
                    type="text"
                    value={couponCode}
                    onChange={e => setCouponCode(e.target.value)}
                    placeholder="Código de descuento o cupón"
                    className="mt-1 w-full rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 p-1.5 text-xs outline-none"
                  />
                </div>

                <div>
                  <label className="block font-medium text-slate-600 dark:text-slate-300">Dirección y datos de entrega (si aplica)</label>
                  <input
                    type="text"
                    value={deliveryAddress}
                    onChange={e => setDeliveryAddress(e.target.value)}
                    placeholder="Dirección, referencia o contacto de entrega"
                    className="mt-1 w-full rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 p-1.5 text-xs outline-none"
                  />
                </div>

                <div>
                  <label className="block font-medium text-slate-600 dark:text-slate-300">Notas en comprobante</label>
                  <input
                    type="text"
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="Texto visible impreso en el comprobante"
                    className="mt-1 w-full rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 p-1.5 text-xs outline-none"
                  />
                </div>

                <div>
                  <label className="block font-medium text-slate-600 dark:text-slate-300">Observaciones internas</label>
                  <input
                    type="text"
                    value={internalObservations}
                    onChange={e => setInternalObservations(e.target.value)}
                    placeholder="Notas internas de auditoría (no se imprimen)"
                    className="mt-1 w-full rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 p-1.5 text-xs outline-none"
                  />
                </div>
              </div>
            )}
          </div>

          {cartCollapsed && cart.length > 0 ? (
            <div className="shrink-0 border-b border-slate-100 dark:border-slate-800 px-3 py-2">
              <button
                type="button"
                onClick={() => setUserExpandedCart(true)}
                className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/60 px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 transition"
              >
                <div className="flex items-center gap-2">
                  <ShoppingCart className="h-3.5 w-3.5 shrink-0 text-slate-500 dark:text-slate-400" />
                  <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-200">{cartSummaryText}</span>
                </div>
                <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
              </button>
            </div>
          ) : (
          <div className="flex-1 min-h-[154px] overflow-y-auto p-2.5 space-y-1.5">
            {cart.length === 0 ? (
              <div className="flex h-full min-h-[150px] flex-col items-center justify-center p-4 text-center text-slate-400 dark:text-slate-500">
                <ShoppingCart className="mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
                <p className="text-xs">No hay productos en la canasta del cliente.</p>
                <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">Haz clic en los productos del catálogo a la izquierda para agregarlos.</p>
              </div>
            ) : (
              cart.map(line => {
                const resolved = pricing[line.product.id];
                const missingSerials = line.product.has_serials && line.serialNumbers?.length !== line.quantity;
                const isDeficit = line.product.track_inventory && !line.is_free_concept && line.quantity > Number(line.product.available_quantity || 0);
                const isExpanded = Boolean(openNoteLineId === line.product.id || line.product.has_serials || isDeficit);

                return (
                  <div
                    key={line.product.id}
                    className={`flex flex-col justify-center rounded-xl border px-2.5 py-1 ${isExpanded ? "min-h-[64px]" : "h-[64px]"} transition ${isDeficit || missingSerials ? "border-rose-300 bg-rose-50/70 dark:border-rose-900/60 dark:bg-rose-950/40" : "border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-800/50"}`}
                  >
                    <div className="flex items-center justify-between gap-2.5 min-h-[40px]">
                      <div className="flex-1 min-w-0 pr-1">
                        <div className="flex items-center gap-1.5">
                          {line.is_free_concept && (
                            <span className="rounded bg-amber-100 dark:bg-amber-950/60 dark:text-amber-300 px-1 py-0.2 text-[9px] font-bold text-amber-900 leading-none">
                              Concepto libre
                            </span>
                          )}
                          <strong className="block truncate text-xs font-bold text-slate-900 dark:text-slate-100 leading-tight" title={line.product.name}>
                            {line.product.name}
                          </strong>
                        </div>
                        <div className="flex items-center gap-1 font-mono text-[10px] text-slate-500 dark:text-slate-400 font-medium leading-none mt-0.5">
                          <span className="truncate">{line.product.sku}</span>
                          <span>·</span>
                          <span>{line.product.unit_of_measure}</span>
                        </div>
                      </div>

                      <div className="inline-flex shrink-0 items-center gap-0.5 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800 p-0.5">
                        <button
                          type="button"
                          onClick={() => updateQuantity(line.product.id, -1)}
                          aria-label={`Reducir ${line.product.name}`}
                          className="flex h-5 w-5 items-center justify-center rounded hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300"
                        >
                          <Minus className="h-2.5 w-2.5" />
                        </button>
                        <input
                          type="number"
                          min="1"
                          value={line.quantity}
                          onChange={e => updateLineQuantityDirect(line.product.id, parseInt(e.target.value) || 1)}
                          className="w-8 text-center font-mono text-xs font-bold text-slate-800 dark:text-slate-100 bg-transparent outline-none leading-none"
                          aria-label={`Cantidad para ${line.product.name}`}
                        />
                        <button
                          type="button"
                          onClick={() => updateQuantity(line.product.id, 1)}
                          aria-label={`Aumentar ${line.product.name}`}
                          className="flex h-5 w-5 items-center justify-center rounded hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300"
                        >
                          <Plus className="h-2.5 w-2.5" />
                        </button>
                      </div>

                      <div className="text-right shrink-0 min-w-[70px]">
                        <span className="block font-mono text-xs font-bold text-slate-900 dark:text-slate-100 leading-tight">
                          {money(Number(resolved?.subtotal ?? (line.quantity * Number(resolved?.final_unit_price ?? line.product.unit_price))), currency)}
                        </span>
                        <span className="block text-[10px] text-slate-500 dark:text-slate-400 font-mono leading-tight mt-0.5">
                          {money(Number(resolved?.final_unit_price ?? line.product.unit_price), currency)} c/u
                        </span>
                        {resolved && Number(resolved.discount_applied) > 0 && (
                          <span className="block text-[9px] font-semibold text-emerald-600 dark:text-emerald-400 leading-tight">
                            Desc. -{money(Number(resolved.discount_applied), currency)}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-0.5 shrink-0">
                        <button
                          type="button"
                          onClick={() => setOpenNoteLineId(openNoteLineId === line.product.id ? null : line.product.id)}
                          title="Agregar nota a este producto"
                          className={`rounded-lg p-1 transition ${line.note ? "bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 font-semibold" : "text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600 dark:hover:text-slate-300"}`}
                        >
                          <FileEdit className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setCart(previous => previous.filter(item => item.product.id !== line.product.id))}
                          aria-label={`Quitar ${line.product.name}`}
                          className="rounded-lg p-1 text-slate-400 dark:text-slate-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 hover:text-rose-600 dark:hover:text-rose-400"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>

                    {openNoteLineId === line.product.id && (
                      <div className="mt-1.5 pt-1.5 border-t border-slate-100 dark:border-slate-800">
                        <input
                          type="text"
                          value={line.note || ""}
                          onChange={e => updateLineNote(line.product.id, e.target.value)}
                          placeholder="Nota para el producto (ej. empaque especial, entrega parcial)..."
                          className="w-full rounded-lg border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 px-2 py-1 text-[11px] outline-none focus:border-teal-600"
                        />
                      </div>
                    )}

                    {line.product.has_serials && (
                      <div className="mt-1.5 rounded-xl border border-indigo-100 bg-indigo-50/50 dark:border-indigo-900/50 dark:bg-indigo-950/30 p-2">
                        <label className="block text-[10px] font-bold text-indigo-800 dark:text-indigo-300">
                          Series ({line.serialNumbers?.length || 0}/{line.quantity})
                        </label>
                        <select
                          multiple
                          value={line.serialNumbers || []}
                          onChange={event => updateSerials(line.product.id, Array.from(event.currentTarget.selectedOptions).map(option => option.value).slice(0, line.quantity))}
                          size={Math.min(3, Math.max(2, availableSerials[line.product.id]?.length || 2))}
                          className="mt-1 w-full rounded-lg border border-indigo-200 bg-white dark:border-indigo-800 dark:bg-slate-900 dark:text-slate-100 p-1 text-[10px]"
                        >
                          {(availableSerials[line.product.id] || []).map(serial => (
                            <option key={serial.id} value={serial.serial_number}>
                              {serial.serial_number}
                            </option>
                          ))}
                        </select>
                        {missingSerials && (
                          <span className="mt-1 block text-[9px] font-semibold text-rose-700 dark:text-rose-400">
                            Selecciona {line.quantity} series requeridas.
                          </span>
                        )}
                      </div>
                    )}

                    {isDeficit && (
                      <div className="mt-1 flex items-center gap-1 text-[10px] font-bold text-rose-700 dark:text-rose-400">
                        <AlertCircle className="h-3 w-3 shrink-0" />
                        <span>La cantidad supera el stock del almacén. Disponible: {line.product.available_quantity}</span>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
          )}

          <aside className="shrink-0 border-t border-slate-200 dark:border-slate-800 bg-slate-50/95 dark:bg-slate-900/95 p-2.5 space-y-1.5">
            <div className="flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-300">
              <div className="flex items-center gap-3">
                <span>Subtotal: <strong className="font-mono text-slate-900 dark:text-slate-100">{money(totals.subtotal, currency)}</strong></span>
                <span>Impuestos IGV: <strong className="font-mono text-slate-900 dark:text-slate-100">{money(totals.tax, currency)}</strong></span>
              </div>
              {totals.discount > 0 && (
                <span className="font-semibold text-emerald-700 dark:text-emerald-400">
                  Desc: -<strong className="font-mono">{money(totals.discount, currency)}</strong>
                </span>
              )}
            </div>

            <div className="relative rounded-xl bg-teal-900 dark:bg-teal-950 px-3 py-1.5 text-white shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-teal-300">
                      Total a Cobrar
                    </span>
                    <button
                      type="button"
                      onClick={() => setPriceDetailsOpen(value => !value)}
                      className="shrink-0 whitespace-nowrap inline-flex items-center gap-1 rounded-full bg-teal-800/80 px-2 py-0.5 text-[9px] font-semibold text-teal-200 hover:bg-teal-700/80 transition"
                    >
                      <span className="shrink-0 whitespace-nowrap">{pricingBusy ? "Calculando…" : "Reglas comerciales"}</span>
                      <ChevronDown className={`h-2.5 w-2.5 shrink-0 transition ${priceDetailsOpen ? "rotate-180" : ""}`} />
                    </button>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 text-[10px] text-teal-200">
                    <span>{taxIncluded ? "Precios con IGV" : "IGV añadido"} · {currency}</span>
                    {dualCurrencyEquivalent && (
                      <span className="font-mono">{dualCurrencyEquivalent}</span>
                    )}
                  </div>
                </div>
                <p className="font-mono text-xl font-black">{money(totals.total, currency)}</p>
              </div>

              {priceDetailsOpen && (
                <div className="mt-2 max-h-24 space-y-1 overflow-y-auto rounded-xl border border-teal-800 bg-teal-950/90 p-2 text-[10px] text-teal-100">
                  {cart.flatMap(line => (pricing[line.product.id]?.rules_applied || []).map((rule, index) => (
                    <div key={`${line.product.id}-${index}`}>
                      <strong>{line.product.name}</strong>: {rule.rule_type === "PRICE_LIST" ? `Lista ${rule.name || rule.code}` : rule.rule_type === "PROMOTION" ? `Promoción ${rule.name || rule.code}` : "Descuento por volumen"} {rule.discount_percentage ? `· ${rule.discount_percentage}%` : ""}
                    </div>
                  )))}
                  {!Object.values(pricing).some(item => item.rules_applied.length) && (
                    <p className="text-teal-300/70">Se aplicó precio base del catálogo.</p>
                  )}
                </div>
              )}
            </div>

            {!isCredit && (
              <PosPaymentEditor
                total={totals.total}
                currency={currency}
                branchId={selectedWarehouse?.branch_id}
                disabled={busy}
                onChange={handlePaymentsChange}
                onCountChange={setPaymentsCount}
              />
            )}

            {isCredit && (
              <div className="space-y-2 rounded-2xl border border-indigo-200 bg-indigo-50/60 dark:border-indigo-900/50 dark:bg-indigo-950/30 p-2.5 text-xs text-indigo-950 dark:text-indigo-200">
                <div className="flex items-center justify-between">
                  <strong className="text-indigo-900 dark:text-indigo-200 font-bold">Condiciones de Crédito Comercial</strong>
                  <span className="font-semibold text-indigo-800 dark:text-indigo-300">{customer?.payment_terms_days ?? 0} días de plazo</span>
                </div>
                <CreditTermsPreview branchId={selectedWarehouse?.branch_id} days={customer?.payment_terms_days ?? 0} />
                <div className="flex items-center justify-between border-t border-indigo-100 dark:border-indigo-900/40 pt-1 text-[11px]">
                  <span>Saldo pendiente: <strong className="text-indigo-950 dark:text-indigo-100">{money(balance, currency)}</strong></span>
                  <span>Crédito disponible: <strong className={creditUnavailable ? "text-rose-700 dark:text-rose-400 font-bold" : "text-indigo-950 dark:text-indigo-100"}>{money(creditAvailable, currency)}</strong></span>
                </div>
              </div>
            )}

            <div>
              <div className="flex items-center gap-2">
                {suspendSale && (
                  <button
                    type="button"
                    disabled={Boolean(busy || pricingBusy || contextBusy || !cart.length)}
                    onClick={suspendSale}
                    title="Guarda esta venta en espera para atender a otro cliente y retomarla después"
                    className="flex items-center justify-center gap-1.5 rounded-xl border border-amber-300 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/40 px-3.5 py-2 text-xs font-semibold text-amber-900 dark:text-amber-200 hover:bg-amber-100 dark:hover:bg-amber-900/60 transition disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                  >
                    <Clock className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                    <span>Poner en espera</span>
                  </button>
                )}
                <button
                  type="button"
                  disabled={Boolean(busy || pricingBusy || contextBusy || confirmBlockerReason || (!isCredit && !paymentsValid))}
                  onClick={confirmSale}
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-teal-700 py-2 text-xs font-bold text-white shadow-md transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {busy ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                  <span>Confirmar venta y cobro</span>
                </button>
              </div>
              <p className="mt-1 text-[9px] text-center text-slate-400 dark:text-slate-500">
                Operación protegida con claves de idempotencia únicas.
              </p>

              {confirmBlockerReason && (
                <div className="mt-1 flex items-center justify-center gap-1.5 rounded-lg border border-amber-300 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/40 px-2 py-0.5 text-center text-[10px] font-semibold text-amber-900 dark:text-amber-200 truncate">
                  <AlertCircle className="h-3 w-3 shrink-0 text-amber-600 dark:text-amber-400" />
                  <span className="truncate">{confirmBlockerReason}</span>
                </div>
              )}
            </div>
          </aside>
        </section>
      </div>

      <PosMissingProductAlertModal
        isOpen={missingModalOpen}
        searchedTerm={search}
        warehouseName={selectedWarehouse?.name}
        onClose={() => setMissingModalOpen(false)}
        onSuccess={msg => toast.success("Aviso enviado", msg)}
      />

      <PosFreeConceptModal
        isOpen={freeConceptModalOpen}
        currency={currency}
        defaultTaxRate={defaultTaxRate}
        onClose={() => setFreeConceptModalOpen(false)}
        onAddConcept={line => {
          addFreeConcept(line);
          toast.success("Concepto agregado", `${line.product.name} añadido a la venta.`);
          setFreeConceptModalOpen(false);
        }}
      />

      <PosHoldSalesModal
        isOpen={holdModalOpen}
        onClose={() => setHoldModalOpen?.(false)}
        holdSales={holdSales}
        currency={currency}
        onRetake={hold => retakeHoldSale?.(hold)}
        onDiscard={id => discardHoldSale?.(id)}
      />
    </dialog>
  );
}