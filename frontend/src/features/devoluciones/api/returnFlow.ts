import type { EligibleLine } from "../types/ReturnWizardModal";

export function returnProblem(cause: unknown) {
  const detail = (cause as { detail?: unknown; message?: string })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(item => `${item.loc?.slice(1).join(" · ") || "Datos"}: ${item.msg || "Valor inválido"}`).join(". ");
  return (cause as { message?: string })?.message || "No se pudo completar la devolución. Inténtalo nuevamente.";
}

export function allowsFractionalReturn(line?: EligibleLine) {
  if (line?.serial_numbers?.length) return false;
  return line?.allow_fractions ?? Boolean(line?.unit_of_measure && !["NIU", "UNIT", "UNIDAD", "PIECE", "SERIAL"].includes(line.unit_of_measure.toUpperCase()));
}
