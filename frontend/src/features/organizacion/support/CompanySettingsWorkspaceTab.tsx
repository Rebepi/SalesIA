import { Company } from "../types/CompanySettingsWorkspaceTab";

export function errorMessage(error: unknown) {
  if (error && typeof error === "object" && "detail" in error) {
    if (typeof error.detail === "string") return error.detail;
    if (error.detail && typeof error.detail === "object" && "title" in error.detail) return String(error.detail.title);
  }
  return error instanceof Error ? error.message : "No fue posible completar la operación.";
}

export const DEFAULT_COMPANY: Company = {
  company_id: "",
  tax_id: "",
  legal_name: "",
  trade_name: "",
  base_currency: "USD",
  is_active: true
};

export const TIMEZONE_OPTIONS = [
  { value: "America/Lima", label: "Perú / Bogotá (America/Lima - GMT-5)" },
  { value: "America/Bogota", label: "Colombia (America/Bogota - GMT-5)" },
  { value: "America/Santiago", label: "Chile (America/Santiago - GMT-4)" },
  { value: "America/Mexico_City", label: "México (America/Mexico_City - GMT-6)" },
  { value: "America/Argentina/Buenos_Aires", label: "Argentina (GMT-3)" },
  { value: "America/New_York", label: "Estados Unidos Este (GMT-5)" },
  { value: "Europe/Madrid", label: "España (Europe/Madrid - GMT+1)" },
  { value: "UTC", label: "Tiempo Universal Coordinado (UTC)" }
];
