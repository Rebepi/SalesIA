import type { MeasurementContext, MetricDefinition } from "../components/MeasurementDefinitions";

const labels: Record<string, string> = { confirmed: "Confirmada", paid: "Pagada", approved: "Aprobado", processed: "Procesado", completed: "Completado", is_active: "Activo" };

export function measurementHelp(context?: MeasurementContext, definitions?: Record<string, MetricDefinition | string>) {
  const parts: string[] = [];
  if (context) parts.push(context.date_reference, context.period_definition, `Desde ${context.from ? new Date(context.from).toLocaleString("es-PE", { timeZone: context.timezone }) : "el inicio del historial"} hasta ${new Date(context.to).toLocaleString("es-PE", { timeZone: context.timezone })}. Zona horaria ${context.timezone}.`, `Moneda: ${context.currency}. ${context.currency_policy}`, `Estados incluidos: ${context.states_included.map(state => labels[state] || state).join(", ")}.`, context.cancellations, context.comparability, context.date_quality || "");
  for (const definition of Object.values(definitions || {})) {
    if (typeof definition === "string") parts.push(definition);
    else parts.push(`${definition.name}${definition.version ? ` · Versión ${definition.version}` : ""}: ${definition.formula}`, definition.grain ? `Unidad de observación: ${definition.grain}` : "", definition.date_reference ? `Fecha: ${definition.date_reference}` : "", definition.states ? `Estados: ${definition.states.map(state => labels[state] || state).join(", ")}` : "", definition.currency ? `Moneda: ${definition.currency}` : "", definition.rounding || "", definition.limitations || "");
  }
  return parts.filter(Boolean).join(" ");
}

export const indicatorStatesHelp = "Disponible: importe calculado con el alcance indicado. Por revisar: hay datos pendientes de conciliación. Sin registros: no se encontraron registros para esa consulta. Restringido: requiere permiso. No disponible: no puede consolidarse con los datos actuales. Área desactivada: módulo no habilitado. Filtro no aplicable: ese filtro comercial no se puede atribuir al indicador.";
