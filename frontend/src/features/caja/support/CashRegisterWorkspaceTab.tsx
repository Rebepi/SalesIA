export function formatMoney(value: number | string | null, currency: string) {
  if (value === null) return "Sin arqueo";
  try { return new Intl.NumberFormat("es-PE", { style: "currency", currency }).format(Number(value)); } catch { return `${currency} ${Number(value).toFixed(2)}`; }
}
