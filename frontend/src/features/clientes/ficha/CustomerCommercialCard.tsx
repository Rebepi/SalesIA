import { ModalSurface } from "../../../ui/components/ModalSurface";
import "../clientes.css";
import { X } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useFichaCliente } from "../hooks/useFichaCliente";
import type { FichaClienteProps, FichaClienteTab } from "../types/clientes";
import { CondicionesComercialesCliente } from "./CondicionesComercialesCliente";
import { ContactosCliente } from "./ContactosCliente";
import { DireccionesCliente } from "./DireccionesCliente";
import { btnPrimary, btnSecondary, inputStyle } from "./estilos";
import { FusionCliente } from "./FusionCliente";
import { HistorialCliente } from "./HistorialCliente";
import { NotasCliente } from "./NotasCliente";
import { ResumenCliente } from "./ResumenCliente";
export function CustomerCommercialCard(props: FichaClienteProps) {
  const { customerName, canWrite, onClose, onAction } = props;
  const model = useFichaCliente(props);
  const { tab, setTab, loading, error, contacts, addresses, notes, companyCurrency, quickPanel, setQuickPanel, handleQuickActivity, handleQuickOpportunity } = model;
  return (
    <ModalSurface labelledBy="card-title" onClose={onClose} className="customer-card-modal">
    <div id="scr-007-customer-card" className="customer-commercial-card flex max-h-[92dvh] w-[min(96vw,1100px)] flex-col overflow-hidden rounded-2xl border bg-white shadow-2xl">
      <header className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <span className="text-xs uppercase tracking-wider text-slate-400">Ficha comercial completa</span>
          <h2 id="card-title" className="text-xl font-bold text-slate-900">{customerName}</h2>
        </div>
        <button type="button" onClick={onClose} className={btnSecondary} aria-label="Cerrar ficha">
          <X className="h-4 w-4" />
        </button>
      </header>

      {canWrite && <div className="flex flex-wrap gap-2 border-b border-slate-100 bg-white px-6 py-3 text-xs"><button type="button" onClick={() => onAction?.("quotation")} className={btnPrimary}>Crear cotización</button><button type="button" onClick={() => onAction?.("order")} className={btnSecondary}>Crear pedido</button><button type="button" onClick={() => onAction?.("sale")} className={btnSecondary}>Nueva venta</button><button type="button" onClick={() => onAction?.("payment")} className={btnSecondary}>Registrar cobro</button><button type="button" onClick={() => setQuickPanel("activity")} className={btnSecondary}>Crear tarea</button><button type="button" onClick={() => setQuickPanel("opportunity")} className={btnSecondary}>Crear oportunidad</button><button type="button" onClick={() => setTab("notes")} className={btnSecondary}>Agregar nota</button></div>}

      {quickPanel === "activity" && <form onSubmit={handleQuickActivity} className="grid gap-3 border-b border-slate-100 bg-teal-50/60 px-6 py-4 sm:grid-cols-[150px_1fr_190px_auto]"><CustomSelect name="activity_type" className={inputStyle}><option value="call">Llamada</option><option value="meeting">Reunión</option><option value="followup">Seguimiento</option><option value="email">Correo</option></CustomSelect><input name="subject" required minLength={2} placeholder="Asunto de la tarea" className={inputStyle} /><input name="due_date" type="datetime-local" required className={inputStyle} /><div className="flex gap-2"><button className={btnPrimary}>Guardar tarea</button><button type="button" onClick={() => setQuickPanel(null)} className={btnSecondary}>Cancelar</button></div></form>}
      {quickPanel === "opportunity" && <form onSubmit={handleQuickOpportunity} className="grid gap-3 border-b border-slate-100 bg-teal-50/60 px-6 py-4 sm:grid-cols-[1fr_150px_120px_auto]"><input name="title" required minLength={2} placeholder="Nombre de la oportunidad" className={inputStyle} /><input name="estimated_amount" type="number" min="0" step="0.01" placeholder={`Importe ${companyCurrency}`} className={inputStyle} /><input name="probability" type="number" min="0" max="100" defaultValue="50" aria-label="Probabilidad" className={inputStyle} /><div className="flex gap-2"><button className={btnPrimary}>Guardar</button><button type="button" onClick={() => setQuickPanel(null)} className={btnSecondary}>Cancelar</button></div></form>}

      <nav aria-label="Secciones de la ficha comercial" className="customer-card-tabs flex shrink-0 flex-wrap gap-1 border-b border-slate-100 px-6 py-3 text-xs font-medium">
        {[
          { key: "overview" as FichaClienteTab, label: "Resumen y Calidad" },
          { key: "contacts" as FichaClienteTab, label: `Contactos (${contacts.length})` },
          { key: "addresses" as FichaClienteTab, label: `Direcciones (${addresses.length})` },
          { key: "terms" as FichaClienteTab, label: "Condiciones comerciales" },
          { key: "history" as FichaClienteTab, label: "Compras e historial" },
          { key: "notes" as FichaClienteTab, label: `Notas (${notes.length})` },
          { key: "merge" as FichaClienteTab, label: "Fusión segura" }
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            type="button"
            aria-current={tab === t.key ? "page" : undefined}
            className="customer-card-tab rounded-lg px-3 py-2 transition"
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="min-h-0 flex-1 overflow-y-auto p-6 text-sm">
        {loading ? (
          <div className="flex h-48 items-center justify-center text-slate-400">Cargando expediente...</div>
        ) : error ? (
          <div role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">{error}<button type="button" className={btnSecondary} onClick={() => void model.loadData()}>Reintentar carga</button></div>
        ) : (
          <>
            {tab === "overview" && (<ResumenCliente {...props} model={model} />)}

            {tab === "contacts" && (<ContactosCliente {...props} model={model} />)}

            {tab === "addresses" && (<DireccionesCliente {...props} model={model} />)}

            {tab === "terms" && (<CondicionesComercialesCliente {...props} model={model} />)}

            {tab === "history" && (<HistorialCliente {...props} model={model} />)}

            {tab === "notes" && (<NotasCliente {...props} model={model} />)}

            {tab === "merge" && (<FusionCliente {...props} model={model} />)}
          </>
        )}
      </div>
    </div>
    </ModalSurface>
  );
}
