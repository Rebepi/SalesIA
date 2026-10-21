import { useState } from "react";
import { X, Truck, CheckCircle2, AlertCircle } from "lucide-react";
import { SaleRecord } from "../types/ventas";

const TRANSFER_REASONS = [
  { code: "01", label: "Venta" },
  { code: "02", label: "Venta sujeta a confirmación del comprador" },
  { code: "04", label: "Traslado entre establecimientos de la misma empresa" },
  { code: "08", label: "Importación" },
  { code: "09", label: "Exportación" },
  { code: "13", label: "Otros" },
];

interface VentasGuiaRemisionModalProps {
  isOpen: boolean;
  sale: SaleRecord | null;
  onClose: () => void;
  onSuccess: (guide: unknown) => void;
  toast?: { success?: (msg: string) => void; error?: (msg: string) => void };
}

export function VentasGuiaRemisionModal({ isOpen, sale, onClose, onSuccess, toast }: VentasGuiaRemisionModalProps) {
  const [transferReason, setTransferReason] = useState("01");
  const [transportMode, setTransportMode] = useState<"PUBLIC" | "PRIVATE">("PRIVATE");
  const [transferDate, setTransferDate] = useState(new Date().toISOString().slice(0, 10));
  const [grossWeight, setGrossWeight] = useState("10.00");
  const [originAddress, setOriginAddress] = useState("Almacén Principal - Av. Los Industriales 1240, Lima");
  const [destinationAddress, setDestinationAddress] = useState(sale?.delivery_address || "Dirección del cliente");
  const [vehiclePlate, setVehiclePlate] = useState("");
  const [driverName, setDriverName] = useState("");
  const [driverDoc, setDriverDoc] = useState("");
  const [carrierRuc, setCarrierRuc] = useState("");
  const [carrierName, setCarrierName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen || !sale) return null;

  const originalNumber = sale.number || `${sale.series}-${sale.correlative}`;
  const suggestedSeries = transportMode === "PUBLIC" ? "V001" : "T001";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!sale) return;
    if (!destinationAddress.trim()) {
      setError("El punto de llegada / dirección de entrega es obligatorio.");
      return;
    }
    if (transportMode === "PRIVATE" && (!vehiclePlate.trim() || !driverDoc.trim())) {
      setError("En transporte privado se requiere la placa del vehículo y documento del conductor.");
      return;
    }
    if (transportMode === "PUBLIC" && (!carrierRuc.trim() || !carrierName.trim())) {
      setError("En transporte público se requiere el RUC y Razón Social de la empresa transportista.");
      return;
    }

    setBusy(true);
    setError("");

    try {
      const guidePayload = {
        sale_id: sale.id || sale.sale_id,
        reference_sale: originalNumber,
        series: suggestedSeries,
        guide_number: `${suggestedSeries}-${Math.floor(100000 + Math.random() * 900000)}`,
        transfer_reason: transferReason,
        transport_mode: transportMode,
        transfer_date: transferDate,
        gross_weight: parseFloat(grossWeight) || 1,
        weight_unit: "KGM",
        origin_address: originAddress,
        destination_address: destinationAddress,
        vehicle_plate: vehiclePlate.trim() || undefined,
        driver_name: driverName.trim() || undefined,
        driver_document: driverDoc.trim() || undefined,
        carrier_ruc: carrierRuc.trim() || undefined,
        carrier_name: carrierName.trim() || undefined,
        status: "Pendiente",
        sunat_status: "Pendiente",
        created_at: new Date().toISOString(),
      };

      onSuccess(guidePayload);
      if (toast?.success) {
        toast.success(`Guía de remisión generada exitosamente vinculada a ${originalNumber}.`);
      }
      onClose();
    } catch {
      setError("No se pudo generar la guía de remisión. Inténtalo de nuevo.");
      if (toast?.error) toast.error("Error al generar guía");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="flex max-h-[92vh] w-full max-w-2xl flex-col rounded-3xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
        <header className="flex items-center justify-between border-b border-slate-100 bg-slate-50/80 px-6 py-4 dark:border-slate-800 dark:bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-700 text-white shadow-md">
              <Truck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Generar Guía de Remisión Electrónica
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Sustento de traslado para {sale.document_type === "INVOICE" ? "Factura" : "Boleta"} <strong className="font-mono text-slate-700 dark:text-slate-300">{originalNumber}</strong>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar modal"
            className="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col overflow-y-auto p-6 space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Motivo del traslado
              </label>
              <select
                value={transferReason}
                onChange={(e) => setTransferReason(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-800 shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                {TRANSFER_REASONS.map((r) => (
                  <option key={r.code} value={r.code}>
                    {r.code} - {r.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Modalidad de transporte
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setTransportMode("PRIVATE")}
                  className={`flex-1 rounded-xl border py-2 text-xs font-semibold ${transportMode === "PRIVATE" ? "border-teal-600 bg-teal-50 text-teal-800 font-bold dark:border-teal-700 dark:bg-teal-950/50 dark:text-teal-300" : "border-slate-200 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"}`}
                >
                  Privado (Propio)
                </button>
                <button
                  type="button"
                  onClick={() => setTransportMode("PUBLIC")}
                  className={`flex-1 rounded-xl border py-2 text-xs font-semibold ${transportMode === "PUBLIC" ? "border-teal-600 bg-teal-50 text-teal-800 font-bold dark:border-teal-700 dark:bg-teal-950/50 dark:text-teal-300" : "border-slate-200 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"}`}
                >
                  Público (Tercero)
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Fecha programada de traslado
              </label>
              <input
                type="date"
                value={transferDate}
                onChange={(e) => setTransferDate(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Peso bruto total estimado (KGM)
              </label>
              <input
                type="number"
                step="0.01"
                min="0.1"
                value={grossWeight}
                onChange={(e) => setGrossWeight(e.target.value)}
                placeholder="10.00"
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 font-mono text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              />
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Punto de partida (Dirección origen)
              </label>
              <input
                type="text"
                value={originAddress}
                onChange={(e) => setOriginAddress(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Punto de llegada (Dirección destino / entrega)
              </label>
              <input
                type="text"
                value={destinationAddress}
                onChange={(e) => setDestinationAddress(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              />
            </div>
          </div>

          {transportMode === "PRIVATE" ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 space-y-3 dark:border-slate-800 dark:bg-slate-950/40">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Datos del transporte privado
              </span>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Placa del vehículo
                  </label>
                  <input
                    type="text"
                    value={vehiclePlate}
                    onChange={(e) => setVehiclePlate(e.target.value.toUpperCase())}
                    placeholder="ABC-123"
                    className="w-full rounded-lg border border-slate-300 bg-white p-2 font-mono text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    DNI / Doc conductor
                  </label>
                  <input
                    type="text"
                    value={driverDoc}
                    onChange={(e) => setDriverDoc(e.target.value)}
                    placeholder="8 dígitos"
                    className="w-full rounded-lg border border-slate-300 bg-white p-2 font-mono text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Nombre del conductor
                  </label>
                  <input
                    type="text"
                    value={driverName}
                    onChange={(e) => setDriverName(e.target.value)}
                    placeholder="Nombres completos"
                    className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 space-y-3 dark:border-slate-800 dark:bg-slate-950/40">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Empresa de Transporte Público
              </span>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    RUC de la empresa transportista
                  </label>
                  <input
                    type="text"
                    value={carrierRuc}
                    onChange={(e) => setCarrierRuc(e.target.value)}
                    placeholder="11 dígitos"
                    className="w-full rounded-lg border border-slate-300 bg-white p-2 font-mono text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Razón Social
                  </label>
                  <input
                    type="text"
                    value={carrierName}
                    onChange={(e) => setCarrierName(e.target.value)}
                    placeholder="Nombre o razón social de transporte"
                    className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs shadow-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 rounded-xl bg-rose-50 p-3 text-xs text-rose-800 dark:bg-rose-950/40 dark:text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={busy}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-5 py-2 text-xs font-bold text-white shadow-md hover:bg-teal-800 disabled:opacity-50"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>{busy ? "Generando..." : "Emitir Guía de Remisión"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
