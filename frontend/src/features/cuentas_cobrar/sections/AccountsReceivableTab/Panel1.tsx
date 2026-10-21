import type { useAccountsReceivableTab } from "../../hooks/useAccountsReceivableTab";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

const cards = [
  { key: "notDue", label: "Aún no vencido", tone: "teal", description: "Saldo pendiente cuya fecha de vencimiento todavía no ha pasado." },
  { key: "totalReceivable", label: "Total cartera pendiente", tone: "blue", description: "Suma de saldos pendientes de cobro, incluidos los importes por vencer y vencidos. Cada moneda se muestra por separado." },
  { key: "0-30", label: "Tramo 0 a 30 días", tone: "amber", description: "Saldo pendiente con una mora de hasta 30 días." },
  { key: "31-60", label: "Tramo 31 a 60 días", tone: "orange", description: "Saldo pendiente con una mora de entre 31 y 60 días." },
  { key: "61-90", label: "Tramo 61 a 90 días", tone: "rose", description: "Saldo pendiente con una mora de entre 61 y 90 días." },
  { key: "90+", label: "Más de 90 días", tone: "red", description: "Saldo vencido por más de 90 días que requiere atención prioritaria de cobranza." },
  { key: "totalDisputed", label: "En disputa", tone: "violet", description: "Importe pendiente sujeto a una observación, reclamo o proceso de conciliación." }
] as const;

export function Panel1({ metrics, id }: { metrics: ReturnType<typeof useAccountsReceivableTab>["metrics"]; id: string }) {
  return <section id={id} aria-label="Resumen de cuentas por cobrar" className="receivables-metrics">
    {cards.map(card => <div key={card.key} className={`receivables-metric receivables-metric-${card.tone}`}>
      <div className="receivables-metric-heading"><h2>{card.label}</h2><InfoTooltip title={card.label} description={card.description} interactive align={card.key === "totalDisputed" ? "right" : "center"} /></div>
      <div className="receivables-metric-values">{metrics.length ? metrics.map(metric => <p key={metric.currency}>{metric.currency} {metric[card.key].toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>) : <p className="receivables-metric-empty">Sin saldos</p>}</div>
    </div>)}
  </section>;
}
