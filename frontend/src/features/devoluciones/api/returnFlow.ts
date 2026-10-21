export function returnProblem(cause: unknown) {
  const detail = (cause as { detail?: unknown; message?: string })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(item => `${item.loc?.slice(1).join(" · ") || "Datos"}: ${item.msg || "Valor inválido"}`).join(". ");
  return (cause as { message?: string })?.message || "No se pudo completar la devolución. Inténtalo nuevamente.";
}
