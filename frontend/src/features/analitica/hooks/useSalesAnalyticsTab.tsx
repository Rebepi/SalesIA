import * as transporte from "../api/SalesAnalyticsTab";
import { useEffect, useState } from "react";

import { ProductItem } from "../types/SalesAnalyticsTab";
import { SellerItem } from "../types/SalesAnalyticsTab";
import { BranchItem } from "../types/SalesAnalyticsTab";
import { SalesAnalyticsData } from "../types/SalesAnalyticsTab";
import { SalesAnalyticsTabProps } from "../types/SalesAnalyticsTab";

export function useSalesAnalyticsTab(_props: SalesAnalyticsTabProps) {
  const [period, setPeriod] = useState("30d");

  const [granularity, setGranularity] = useState("day");

  const [currency, setCurrency] = useState("");

  const [breakdownTab, setBreakdownTab] = useState<"day" | "product" | "branch" | "seller">("day");

  const [, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [salesData, setSalesData] = useState<SalesAnalyticsData | null>(null);

  const [products, setProducts] = useState<ProductItem[]>([]);

  const [sellers, setSellers] = useState<SellerItem[]>([]);

  const [branches, setBranches] = useState<BranchItem[]>([]);

  const [drillDownItem, setDrillDownItem] = useState<{ title: string; subtitle: string; rows: { label: string; value: string }[] } | null>(null);

  useEffect(() => {
    transporte.solicitarDatos()
      .then((company) => setCurrency(company.base_currency))
      .catch((requestError) => setError(requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No se pudo determinar la moneda base."));
  }, []);

  useEffect(() => {
    let unmounted = false;
    setLoading(true);
    setError("");

    Promise.allSettled([
      transporte.solicitarDatos2({ period, granularity, currency }),
      transporte.solicitarDatos3({ period, currency }),
      transporte.solicitarDatos4({ period }),
      transporte.solicitarDatos5({ period, currency })
    ]).then(([salesRes, prodRes, sellRes, branchRes]) => {
      if (unmounted) return;
      if (salesRes.status === "fulfilled") setSalesData(salesRes.value);
      else setError("No se pudieron cargar las series de ventas.");
      if (prodRes.status === "fulfilled" && prodRes.value?.items) setProducts(prodRes.value.items);
      if (sellRes.status === "fulfilled" && sellRes.value?.items) setSellers(sellRes.value.items);
      if (branchRes.status === "fulfilled" && branchRes.value?.items) setBranches(branchRes.value.items);
      if ([prodRes, sellRes, branchRes].some((response) => response.status === "rejected")) setError((current) => current || "Parte del desglose analítico no pudo cargarse.");
    }).finally(() => {
      if (!unmounted) setLoading(false);
    });

    return () => {
      unmounted = true;
    };
  }, [period, granularity, currency]);

  const handleDrillDown = (name: string, type: string, extra: Record<string, string>) => {
    setDrillDownItem({
      title: `Desglose granular: ${name}`,
      subtitle: `Filtro aplicado: ${type} · Período conservado: ${period} · Moneda: ${currency}`,
      rows: Object.entries(extra).map(([label, value]) => ({ label, value }))
    });
  };
  return { period, setPeriod, granularity, setGranularity, currency, breakdownTab, setBreakdownTab, error, salesData, products, sellers, branches, drillDownItem, setDrillDownItem, handleDrillDown };
}
