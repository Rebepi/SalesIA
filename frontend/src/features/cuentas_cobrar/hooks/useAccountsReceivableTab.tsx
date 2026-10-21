import * as transporte from "../api/AccountsReceivableTab";
import { useEffect, useState } from "react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { ReceivableItem } from "../types/AccountsReceivableTab";
import { CreditNoteItem } from "../types/AccountsReceivableTab";
import { AccountsReceivableResponse } from "../types/AccountsReceivableTab";
import { AccountsReceivableTabProps } from "../types/AccountsReceivableTab";

export function useAccountsReceivableTab(_props: AccountsReceivableTabProps) {
  const [revision, setRevision] = useState(0);

  const [action, setAction] = useState<{ saleId: string; mode: "payment" | "activity" | "context" } | null>(null);

  const [items, setItems] = useState<ReceivableItem[]>([]);

  const [summaries, setSummaries] = useState<AccountsReceivableResponse["totals_by_currency"]>({});

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [selectedBucket, setSelectedBucket] = useState<string>("ALL");

  const [search, setSearch] = useState("");

  const [activeItem, setActiveItem] = useState<ReceivableItem | null>(null);

  const [creditNotes, setCreditNotes] = useState<CreditNoteItem[]>([]);

  const [loadingReconcile, setLoadingReconcile] = useState(false);

  const [reconcileNotes, setReconcileNotes] = useState("");

  const toast = useToast();

  useEffect(() => {
    setLoading(true);
    setError("");
    apiClient
      .request<AccountsReceivableResponse>("/api/v1/receivables")
      .then(res => {
        setItems(res.items || []);
        setSummaries(res.totals_by_currency || {});
      })
      .catch(err => {
        setError(String(err?.detail || "No se pudieron cargar las cuentas por cobrar."));
      })
      .finally(() => setLoading(false));
  }, [revision]);

  async function openReconciliation(item: ReceivableItem) {
    setActiveItem(item);
    setLoadingReconcile(true);
    setReconcileNotes("");
    try {
      const res = await transporte.solicitarOpenReconciliation({ item });
      setCreditNotes(res || []);
    } catch (requestError: unknown) {
      setCreditNotes([]);
      toast.warning("No se pudieron cargar las notas de crédito", String((requestError as { detail?: string }).detail || requestError));
    } finally {
      setLoadingReconcile(false);
    }
  }

  const filteredItems = items.filter(item => {
    const matchesBucket = selectedBucket === "ALL" || (item.aging_balances ? Number(item.aging_balances[selectedBucket] || 0) > 0 : item.aging_bucket === selectedBucket);
    const matchesSearch =
      search.trim() === "" ||
      item.series_number.toLowerCase().includes(search.toLowerCase()) ||
      (item.customer_name || "").toLowerCase().includes(search.toLowerCase()) || item.customer_id.toLowerCase().includes(search.toLowerCase());
    return matchesBucket && matchesSearch;
  }).map(item => ({ ...item, selected_bucket_balance: selectedBucket === "ALL" ? null : item.aging_balances?.[selectedBucket] || item.balance_due }));

  const currencies = [...new Set([...Object.keys(summaries), ...items.map(item => item.currency || "Sin moneda")])].sort();
  const metrics = currencies.map(currency => {
    const currencyItems = items.filter(item => (item.currency || "Sin moneda") === currency);
    const bucketBalance = (bucket: string) => currencyItems.reduce((sum, item) => sum + Number(item.aging_balances?.[bucket] || (item.aging_bucket === bucket ? item.balance_due : "0")), 0);
    return {
      currency,
      notDue: Number(summaries[currency]?.not_due ?? bucketBalance("not_due")),
      totalReceivable: Number(summaries[currency]?.total_receivable ?? currencyItems.reduce((sum, item) => sum + Number(item.balance_due), 0)),
      totalDisputed: Number(summaries[currency]?.total_disputed || "0"),
      "0-30": bucketBalance("0-30"),
      "31-60": bucketBalance("31-60"),
      "61-90": bucketBalance("61-90"),
      "90+": bucketBalance("90+")
    };
  });
  return { metrics, setRevision, action, setAction, loading, error, selectedBucket, setSelectedBucket, search, setSearch, activeItem, setActiveItem, creditNotes, loadingReconcile, reconcileNotes, setReconcileNotes, toast, openReconciliation, filteredItems };
}
