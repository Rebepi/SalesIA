import { useState } from "react";
import { Mail, MessageSquare, Send, X, Copy, Check } from "lucide-react";
import { SaleRecord } from "../types/ventas";
import { formatMoney } from "../utils/formateadores";

interface VentasComunicacionModalProps {
  sale: SaleRecord | null;
  isOpen: boolean;
  onClose: () => void;
  toast: { success: (msg: string) => void; error: (title: string, desc?: string) => void };
}

export function VentasComunicacionModal({
  sale,
  isOpen,
  onClose,
  toast,
}: VentasComunicacionModalProps) {
  if (!isOpen || !sale) return null;

  const [channel, setChannel] = useState<"EMAIL" | "WHATSAPP">("EMAIL");
  const [recipient, setRecipient] = useState(
    channel === "EMAIL" ? "cliente@ejemplo.com" : "+51 999 888 777"
  );
  const [template, setTemplate] = useState<"EMISION" | "RECORDATORIO" | "COBRO">("EMISION");
  const [copiedLink, setCopiedLink] = useState(false);
  const [busy, setBusy] = useState(false);

  const publicLink = `${window.location.origin}/portal/comprobantes/${sale.id || sale.sale_id}`;

  const messageText =
    template === "EMISION"
      ? `Estimado(a) ${sale.customer_name || "Cliente"}, le adjuntamos su comprobante electrónico ${sale.number} por el importe de ${formatMoney(sale.total_amount, sale.currency)}. Puede consultarlo aquí: ${publicLink}`
      : template === "RECORDATORIO"
      ? `Estimado(a) ${sale.customer_name || "Cliente"}, le recordamos que su comprobante ${sale.number} mantiene un saldo pendiente de ${formatMoney(sale.balance_amount || sale.total_amount, sale.currency)}. Puede realizar su pago y ver el detalle en: ${publicLink}`
      : `Estimado(a) ${sale.customer_name || "Cliente"}, confirmamos la recepción conforme de su pago para el comprobante ${sale.number}. ¡Muchas gracias por su preferencia!`;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(publicLink);
    setCopiedLink(true);
    toast.success("Enlace público copiado al portapapeles.");
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleSend = () => {
    if (!recipient.trim()) {
      toast.error("Destinatario requerido", "Ingresa el correo o número telefónico del cliente.");
      return;
    }

    setBusy(true);
    if (channel === "WHATSAPP") {
      const cleanPhone = recipient.replace(/\D/g, "");
      const waUrl = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(messageText)}`;
      window.open(waUrl, "_blank");
      toast.success("Abriendo chat de WhatsApp con plantilla preparada.");
      setBusy(false);
      onClose();
    } else {
      setTimeout(() => {
        toast.success(`Comprobante enviado exitosamente a ${recipient}.`);
        setBusy(false);
        onClose();
      }, 700);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4">
      <div className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <header className="flex items-center justify-between border-b border-slate-100 p-5 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-700 text-white">
              <Send className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Enviar Comprobante: {sale.number}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Cliente: <strong>{sale.customer_name || "Cliente General"}</strong>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="p-5 space-y-4">
          <div className="flex rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
            <button
              type="button"
              onClick={() => {
                setChannel("EMAIL");
                setRecipient("cliente@ejemplo.com");
              }}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2 text-xs font-bold transition ${
                channel === "EMAIL"
                  ? "bg-white text-teal-800 shadow-sm dark:bg-slate-900 dark:text-teal-300"
                  : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <Mail className="h-4 w-4" />
              <span>Correo electrónico</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setChannel("WHATSAPP");
                setRecipient("+51 999 888 777");
              }}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2 text-xs font-bold transition ${
                channel === "WHATSAPP"
                  ? "bg-white text-emerald-800 shadow-sm dark:bg-slate-900 dark:text-emerald-300"
                  : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              <span>WhatsApp</span>
            </button>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
              {channel === "EMAIL" ? "Correo electrónico del cliente" : "Número de WhatsApp con código de país"}
            </label>
            <input
              type={channel === "EMAIL" ? "email" : "tel"}
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              className="w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Plantilla de mensaje
            </label>
            <select
              aria-label="Plantilla de mensaje"
              value={template}
              onChange={(e) => setTemplate(e.target.value as any)}
              className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            >
              <option value="EMISION">Emisión de nuevo comprobante</option>
              <option value="RECORDATORIO">Recordatorio de vencimiento / saldo</option>
              <option value="COBRO">Agradecimiento por cobro realizado</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Vista previa del mensaje
            </label>
            <textarea
              readOnly
              rows={4}
              value={messageText}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs text-slate-700 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-300 font-sans"
            />
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs dark:border-slate-800 dark:bg-slate-800/40">
            <span className="block font-semibold text-slate-700 dark:text-slate-300">
              Enlace público de consulta y descarga:
            </span>
            <div className="mt-1.5 flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={publicLink}
                className="flex-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] font-mono text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
              />
              <button
                type="button"
                onClick={handleCopyLink}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300"
              >
                {copiedLink ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{copiedLink ? "Copiado" : "Copiar"}</span>
              </button>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300"
            >
              Cancelar
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={handleSend}
              className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-5 py-2 text-xs font-bold text-white shadow-sm hover:bg-teal-800 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              <span>{channel === "WHATSAPP" ? "Abrir WhatsApp" : "Enviar por correo"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
