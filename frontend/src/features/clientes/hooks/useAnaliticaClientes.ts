import type { MeasurementContext } from "../../analitica/components/MeasurementDefinitions";
import { useEffect, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";
import * as analiticaApi from "../api/analiticaApi";
import type { CustomerAnalyticsItem, CustomerAnalyticsSummary, CustomerCohortItem } from "../types/clientes";
export function useAnaliticaClientes() {
  const [period, setPeriod] = useState("30d");

  const [selectedSegment, setSelectedSegment] = useState<string>("all");

  const [loading, setLoading] = useState(false);
  const [currency, setCurrency] = useState("");
  const [measurement, setMeasurement] = useState<MeasurementContext | undefined>(undefined);

  const [error, setError] = useState("");

  const [summary, setSummary] = useState<CustomerAnalyticsSummary | null>(null);

  const [customers, setCustomers] = useState<CustomerAnalyticsItem[]>([]);

  const [cohorts, setCohorts] = useState<CustomerCohortItem[]>([]);

  const toast = useToast();

  useEffect(() => {
    let unmounted = false;
    const controller = new AbortController();
    setSummary(null); setCustomers([]); setCohorts([]); setMeasurement(undefined);
    setLoading(true);
    setError("");

    analiticaApi.consultar(period, controller.signal).then((res) => {
      if (unmounted) return;
      setCurrency(res.currency); setMeasurement(res.measurement_context);
      if (res.summary) setSummary(res.summary);
      if (res.items) setCustomers(res.items);
      if (res.cohorts) setCohorts(res.cohorts);
    }).catch((failure: unknown) => {
      if (!unmounted) setError(String((failure as { detail?: string }).detail || failure));
    }).finally(() => {
      if (!unmounted) setLoading(false);
    });

    return () => {
      unmounted = true;
      controller.abort();
    };
  }, [period]);

  const filteredCustomers = customers.filter((c) => {
    if (selectedSegment === "all") return true;
    return c.customer_type === selectedSegment;
  });

  const handleExport = () => {
    if (filteredCustomers.length === 0) {
      toast.warning("No hay datos para exportar", "La vista seleccionada no contiene clientes.");
      return;
    }
    const escape = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
    const rows = filteredCustomers.map((customer) => [customer.code, customer.legal_name, customer.customer_type, customer.orders_count, customer.total_revenue, customer.recency_days ?? "", customer.average_ticket ?? "", customer.revenue_share_pct, currency].map(escape).join(","));
    const csv = ["code,legal_name,segment,orders_count,total_revenue,recency_days,average_ticket,revenue_share_pct,currency", ...rows].join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `segmentos-clientes-${period}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast.success("Exportación generada", `${filteredCustomers.length} clientes fueron incluidos en el archivo CSV.`);
  };
  return {
    loading, currency, measurement,
    period,
    setPeriod,
    selectedSegment,
    setSelectedSegment,
    error,
    summary,
    cohorts,
    filteredCustomers,
    handleExport
  };
}
