import type { ProblemDetails } from "./client";

const fieldNames: Record<string, string> = { customer_id: "cliente", product_id: "producto", warehouse_id: "almacén", branch_id: "sede", quantity: "cantidad", amount: "importe", unit_price: "precio", unit_cost: "costo", tax_rate: "impuesto", email: "correo", password: "contraseña", sku: "SKU", name: "nombre", currency: "moneda", payment_method: "medio de pago", due_date: "vencimiento", recipients: "destinatarios", notes: "notas" };

export function userProblem(payload: unknown, status: number, traceId?: string | null): ProblemDetails {
  const raw = payload && typeof payload === "object" ? payload as Record<string, unknown> : {};
  let detail: string;
  if (status >= 500) detail = "El servicio no pudo completar la operación. Actualiza el documento para comprobar su estado y vuelve a intentar. Si continúa, contacta a soporte con la referencia del error.";
  else if (Array.isArray(raw.detail)) {
    const fields = raw.detail.map(item => {
      const location = Array.isArray(item?.loc) ? item.loc.filter((value: unknown) => typeof value === "string" && !["body", "query", "path"].includes(value as string)) : [];
      return fieldNames[String(location[location.length - 1])] || "un campo del formulario";
    });
    detail = `Revisa los datos de ${Array.from(new Set(fields)).join(", ") || "los campos obligatorios"}. Completa los valores solicitados y vuelve a guardar.`;
  } else if (typeof raw.detail === "object" && raw.detail) detail = String((raw.detail as Record<string, unknown>).title || "Revisa la información del formulario y vuelve a intentar.");
  else if (typeof raw.detail === "string" && raw.detail.trim() && !/Traceback|sqlalchemy|IntegrityError|OperationalError|SELECT\s|INSERT\s|UPDATE\s|DELETE\s|<html|<!doctype|\[SQL:|stack trace/i.test(raw.detail)) detail = raw.detail;
  else detail = status === 401 ? "Tu sesión venció. Inicia sesión nuevamente para continuar." : status === 403 ? "Tu usuario no tiene permiso para esta acción. Solicita el acceso al administrador." : status === 404 ? "El registro ya no está disponible. Actualiza la lista y selecciona otro registro." : status === 409 ? "El documento cambió o su estado no permite esta operación. Actualiza y revisa los datos." : status === 422 ? "Revisa los campos obligatorios y los valores ingresados." : status === 429 ? "Hay muchas solicitudes en proceso. Espera unos segundos y vuelve a intentar." : "No se pudo completar la solicitud. Revisa la conexión y vuelve a intentar.";
  return { type: typeof raw.type === "string" ? raw.type : "about:blank", title: status >= 500 ? "Servicio temporalmente no disponible" : "No se pudo completar la operación", status, detail, code: typeof raw.code === "string" ? raw.code : undefined, trace_id: traceId || (typeof raw.trace_id === "string" ? raw.trace_id : undefined) };
}
