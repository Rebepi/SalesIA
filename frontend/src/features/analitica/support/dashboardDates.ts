export function shortDashboardDate(value: string) {
  const parts = value.split("-");
  return parts.length >= 2 ? `${parts[2]?.slice(0, 2) || "01"}/${parts[1]}` : value;
}

export function dashboardPeriodLabel(value: string, granularity: string) {
  if (granularity === "month") return `Mes ${value.slice(5, 7)}/${value.slice(0, 4)}`;
  const full = `${shortDashboardDate(value)}/${value.slice(0, 4)}`;
  if (granularity !== "week") return `Día ${full}`;
  const end = new Date(`${value}T12:00:00Z`);
  end.setUTCDate(end.getUTCDate() + 6);
  const endText = end.toISOString().slice(0, 10);
  return `Semana ${full}–${shortDashboardDate(endText)}/${endText.slice(0, 4)}`;
}
