import { Children, cloneElement, isValidElement, useId, type InputHTMLAttributes, type ReactElement, type ReactNode } from "react";
import { InfoTooltip } from "./InfoTooltip";
const help: Record<string, string> = {
  "Tasa Fiscal Predeterminada": "Tasa usada de forma predeterminada en el cálculo de impuestos. Se expresa como fracción: 0.18 equivale a 18 %.",
  "Modo de Redondeo": "Bancario redondea los empates hacia el último dígito par; comercial redondea los empates hacia arriba. Determina cómo se resuelven los decimales en los cálculos.",
  "Duración": "Tiempo que puede permanecer en espera una venta del mostrador antes de caducar. Se combina con la unidad de tiempo elegida.",
  "Unidad de Tiempo": "Indica si la duración de las ventas en espera se mide en minutos, horas o días.",
  "Código de regla fiscal": "Identificador de la regla de impuesto, por ejemplo IGV o EXO. Al seleccionar una regla del catálogo se carga para editarla.",
  "Tasa de la regla fiscal": "Fracción del importe que corresponde al impuesto: 0.18 equivale al 18 % y 0 a una tasa de 0 %.",
  "Nombre de la regla fiscal": "Descripción que permite identificar la regla fiscal en el catálogo.",
  "Cantidad mínima": "Cantidad desde la que se aplica este tramo de descuento por volumen.",
  "Porcentaje": "Porcentaje aplicable a este tramo, expresado entre 0 y 100. Por ejemplo, escribe 7 para un 7 %.",
  "Cumplimiento mínimo %": "Nivel mínimo de cumplimiento de meta necesario para aplicar el porcentaje de comisión del tramo. Debe existir un tramo desde 0.",
  "Plazo de reposición predeterminado en días": "Tiempo estimado para reponer un artículo cuando no tiene un plazo propio. Se utiliza en las recomendaciones de abastecimiento.",
  "Días de historia para demanda": "Cantidad de días anteriores que se consideran para estimar la demanda en abastecimiento.",
  "Tolerancia de precio unitario %": "Diferencia porcentual de precio unitario admitida al conciliar una factura de compra. Las diferencias de cantidad o impuesto requieren corregir la operación.",
  "Tolerancia de redondeo del total": "Diferencia monetaria máxima admitida por redondeo al conciliar el total de una factura de compra.",
  "Días de historia": "Período de operaciones que se toma como muestra para evaluar el desempeño de los proveedores.",
  "Muestra mínima de líneas recibidas": "Número mínimo de líneas recibidas que debe tener un proveedor para obtener una puntuación global.",
  "Peso de puntualidad": "Importancia relativa de recibir en la fecha prevista. Los pesos se normalizan entre los indicadores que tienen datos.",
  "Peso de cumplimiento de cantidad": "Importancia relativa de recibir las cantidades acordadas. Los pesos se normalizan entre los indicadores disponibles.",
  "Peso de aceptación": "Importancia relativa de la aceptación de lo recibido al evaluar al proveedor.",
  "Peso de facturación conforme": "Importancia relativa de las facturas conformes al evaluar al proveedor.",
  "Código": "Identificador único de la política de aprobación. Se conserva al editar una política existente.",
  "Documento": "Tipo de documento sobre el que se evaluará la política de aprobación.",
  "Acción protegida": "Acción que quedará bloqueada hasta completar las aprobaciones requeridas cuando se cumpla la condición.",
  "Condición": "Dato que se evalúa para decidir si hace falta aprobación. Siempre aplica la política a todos los casos de esta acción.",
  "Comparación": "Operador con el que se compara la condición y su umbral: mayor, menor o igual.",
  "Umbral": "Valor a partir del cual se aplica la comparación. Para importes utiliza la moneda del documento; para descuentos o márgenes, un porcentaje.",
  "Nombre": "Nombre de la etapa que verán las personas responsables de aprobar la operación.",
  "Responsables autorizados": "Personas que pueden decidir en esta etapa. Puedes elegir varias; el solicitante no puede aprobar su propia operación.",
  "Decisiones favorables necesarias": "Cantidad de aprobaciones requeridas para completar la etapa. No puede superar la cantidad de responsables seleccionados.",
  "Plazo de etapa, horas": "Tiempo disponible para resolver esta etapa de aprobación, expresado en horas.",
  "Responsable titular": "Persona cuyas decisiones de aprobación se delegarán durante el intervalo indicado.",
  "Reemplazo autorizado": "Persona que podrá actuar por el titular durante la vigencia de la delegación.",
  "Desde, hora de Lima": "Inicio de la delegación temporal, interpretado en la zona horaria America/Lima.",
  "Hasta, hora de Lima": "Fin de la delegación temporal. Después de esa fecha y hora deja de estar vigente.",
  "Motivo": "Sustento del cambio o autorización. Queda registrado para poder consultar por qué se realizó.",
  "Fecha inclusive": "Última fecha que se cerrará para los módulos seleccionados, incluyéndola. Primero se deben revisar los bloqueos y pendientes.",
  "Módulo": "Módulo que se autoriza a operar temporalmente dentro de fechas ya cerradas.",
  "Fecha inicial": "Primer día cerrado para el que se permitirá operar mediante la autorización temporal.",
  "Fecha final inclusive": "Último día incluido en la reapertura. Todo el intervalo debe estar previamente cerrado.",
  "Vigencia de la autorización en horas": "Tiempo durante el que se podrá utilizar la reapertura, hasta un máximo de 168 horas (7 días). Es distinto del intervalo de fechas autorizado.",
  "Justificación": "Explica por qué es necesario operar en un período cerrado. Se conserva en la auditoría de la autorización."
};
export function SettingLabel({ children, className = "" }: { children: ReactNode; className?: string }) {
  const id = useId();
  const parts = Children.toArray(children);
  const label = parts.filter(part => typeof part === "string" || typeof part === "number").join("").trim();
  const controls = parts.filter(part => isValidElement(part));
  return <div className={`settings-field ${className}`}><div className="settings-field-heading"><label htmlFor={id}>{label}</label>{help[label] && <InfoTooltip title={label} description={help[label]} interactive />}</div>{controls.map((part, index) => index === 0 ? cloneElement(part as ReactElement<{ id?: string }>, { id }) : part)}</div>;
}
export function SettingSwitch({ label, description, className: _className, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; description: string }) {
  return <div className="settings-switch-row"><label className="settings-switch-label"><input {...props} type="checkbox" role="switch" aria-label={label} /><span>{label}</span></label><InfoTooltip title={label} description={description} interactive /></div>;
}
export function SettingsHelp({ title, description }: { title: string; description: string }) {
  return <InfoTooltip title={title} description={description} interactive />;
}
