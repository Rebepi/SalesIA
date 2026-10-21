import { Clock3, ShieldCheck, ArrowRight, PackageCheck } from "lucide-react";
import { ReturnHelp } from "./ReturnHelp";

export function ReturnPendingConfirmation({ returnId, documentNumber, onClose }: { returnId: string; documentNumber: string; onClose: () => void }) {
  return <section role="status" className="return-pending-confirmation">
    <div className="return-pending-heading"><span className="return-pending-icon"><Clock3 size={25} /></span><span className="return-pending-badge">Pendiente de revisión</span></div>
    <h3>Solicitud de devolución registrada</h3>
    <p className="return-pending-lead">La solicitud de <strong>{documentNumber}</strong> está lista para que otra persona autorizada la revise.</p>
    <div className="return-pending-reference"><span>Número de seguimiento <ReturnHelp title="Número de seguimiento" description="Identifica esta solicitud de forma única. Se conserva al cerrar la ventana; podrás continuarla desde la misma venta." /></span><code>{returnId}</code></div>
    <div className="return-pending-next"><ShieldCheck size={20} /><div><strong>Cómo continuar <ReturnHelp title="Revisión independiente" description="La configuración de la empresa exige que quien acepta la devolución sea distinto de quien la solicitó. Se revisan cantidades y destinos antes de aplicar efectos." /></strong><p>La persona revisora abre esta venta y selecciona <b>Continuar devolución</b> para comprobarla y aceptarla.</p></div></div>
    <p className="return-pending-note"><PackageCheck size={17} /> El inventario y el dinero se actualizarán después de la aceptación.</p>
    <footer><button type="button" className="sales-return-primary" onClick={onClose}>Cerrar solicitud <ArrowRight size={16} /></button></footer>
  </section>;
}
