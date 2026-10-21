import { useState } from "react";
import { X, Tag, AlertCircle } from "lucide-react";
import { ProductItem, SaleCartLine } from "../types/NewSalePOSModal";

interface PosFreeConceptModalProps {
  isOpen: boolean;
  currency: string;
  defaultTaxRate?: string;
  onClose: () => void;
  onAddConcept: (line: SaleCartLine) => void;
}

export function PosFreeConceptModal({
  isOpen,
  currency,
  defaultTaxRate = "0.18",
  onClose,
  onAddConcept,
}: PosFreeConceptModalProps) {
  const [conceptName, setConceptName] = useState("");
  const [unitPrice, setUnitPrice] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [taxRate, setTaxRate] = useState(defaultTaxRate);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  if (!isOpen) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const cleanName = conceptName.trim();
    const priceNum = parseFloat(unitPrice) || 0;
    const qtyNum = parseFloat(quantity) || 1;

    if (!cleanName) {
      setError("Indica la descripción o nombre del concepto libre.");
      return;
    }
    if (priceNum <= 0) {
      setError("El precio unitario debe ser mayor a 0.");
      return;
    }
    if (qtyNum <= 0) {
      setError("La cantidad debe ser mayor a 0.");
      return;
    }

    const freeProduct: ProductItem = {
      id: `free_concept_${Date.now()}`,
      sku: "CONCEPTO-LIBRE",
      name: `[Concepto Libre] ${cleanName}`,
      unit_price: String(priceNum),
      tax_rate: taxRate,
      unit_of_measure: "UNI",
      available_quantity: "9999",
      physical_quantity: "9999",
      reserved_quantity: "0",
      track_inventory: false,
      has_lots: false,
      has_serials: false,
    };

    onAddConcept({
      product: freeProduct,
      quantity: qtyNum,
      unit_price: priceNum,
      note: note.trim() || undefined,
      is_free_concept: true,
      serialNumbers: [],
    });

    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400">
              <Tag className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Agregar Concepto Libre
              </h3>
              <p className="text-[11px] text-slate-500">
                Cobro de flete, recargo o servicio puntual sin registrar producto en el catálogo
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {error && (
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-rose-50 p-2.5 text-xs text-rose-800">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-3.5 text-xs">
          <div>
            <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Descripción o nombre del concepto *
            </label>
            <input
              type="text"
              required
              value={conceptName}
              onChange={e => setConceptName(e.target.value)}
              placeholder="Ej. Flete de entrega a domicilio, Servicio de armado..."
              className="w-full rounded-xl border border-slate-300 bg-white p-2.5 outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-1">
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Cantidad *
              </label>
              <input
                type="number"
                min="0.01"
                step="any"
                required
                value={quantity}
                onChange={e => setQuantity(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 font-mono outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </div>

            <div className="col-span-1">
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Precio Unit. ({currency}) *
              </label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                required
                value={unitPrice}
                onChange={e => setUnitPrice(e.target.value)}
                placeholder="0.00"
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 font-mono text-right outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </div>

            <div className="col-span-1">
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Impuesto
              </label>
              <select
                value={taxRate}
                onChange={e => setTaxRate(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="0.18">IGV 18%</option>
                <option value="0">Exonerado 0%</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Nota o detalle para la línea (opcional)
            </label>
            <input
              type="text"
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="Detalle visible en el comprobante..."
              className="w-full rounded-xl border border-slate-300 bg-white p-2.5 outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>

          <p className="rounded-xl bg-slate-50 p-2.5 text-[10px] text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
            Este ítem se registrará marcado como concepto libre puntual y no afectará el kardex de inventario.
          </p>

          <div className="flex gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-slate-300 py-2.5 font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 rounded-xl bg-amber-700 py-2.5 font-bold text-white shadow-md hover:bg-amber-800"
            >
              Agregar a la venta
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
