export const PRIORITY_LABELS: Record<string, string> = {
  low: "Baja",
  normal: "Normal",
  high: "Alta",
  urgent: "Urgente"
};

export const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-slate-400 dark:bg-slate-500",
  normal: "bg-sky-500 dark:bg-sky-400",
  high: "bg-amber-500 dark:bg-amber-400",
  urgent: "bg-rose-500 dark:bg-rose-400"
};

export function formatMoney(amount: number | string | null | undefined, currency = "USD"): string {
  if (amount === null || amount === undefined || amount === "") return "—";
  const num = typeof amount === "number" ? amount : parseFloat(String(amount));
  if (Number.isNaN(num)) return "—";
  try {
    return new Intl.NumberFormat("es-PE", {
      style: "currency",
      currency: currency || "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  } catch {
    return `${currency || "USD"} ${new Intl.NumberFormat("es-PE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num)}`;
  }
}

export function getBranchMonthPeriod(date: Date, timezone?: string): string {
  try {
    if (timezone) {
      const formatter = new Intl.DateTimeFormat("en-CA", {
        timeZone: timezone,
        year: "numeric",
        month: "2-digit"
      });
      return formatter.format(date);
    }
  } catch { }
  return date.toISOString().slice(0, 7);
}

export function formatPeriodLabel(periodStr: string): string {
  try {
    const [year, month] = periodStr.split("-").map(Number);
    if (!year || !month) return periodStr;
    const date = new Date(year, month - 1, 1);
    const label = new Intl.DateTimeFormat("es-PE", { month: "long", year: "numeric" }).format(date);
    return label.charAt(0).toUpperCase() + label.slice(1);
  } catch {
    return periodStr;
  }
}

export function isDateToday(dateStr: string | null): boolean {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const now = new Date();
  return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
}

export function isDateOverdue(dateStr: string | null): boolean {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  return d < startOfToday;
}

export function formatDisplayDate(dateStr: string | null): string {
  if (!dateStr) return "Sin vencimiento";
  try {
    const d = new Date(dateStr);
    if (isDateToday(dateStr)) return "Vence hoy";
    return d.toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return dateStr;
  }
}
