import * as transporte from "../api/SaleDetailModal";
import { useState, useEffect, useRef } from "react";
import { SaleDetailData } from "../types/SaleDetailModal";
import { SaleDetailModalProps } from "../types/SaleDetailModal";

export type DetailTabKey =
  | "lines"
  | "payments"
  | "installments"
  | "deliveries"
  | "returns"
  | "documents"
  | "communications"
  | "commissions"
  | "related"
  | "audit"
  | "internal_notes";

export function useSaleDetailModal({ sale }: SaleDetailModalProps) {
  const [activeTab, setActiveTab] = useState<DetailTabKey>("lines");
  const [detailedSale, setDetailedSale] = useState<SaleDetailData | null>(null);
  const [loading, setLoading] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const activeSale = (detailedSale && sale && String(detailedSale.sale_id || detailedSale.id) === String(sale.sale_id || sale.id))
    ? detailedSale
    : sale;

  useEffect(() => {
    const controller = new AbortController();
    const dialog = dialogRef.current;
    if (sale && dialog) {
      if (!dialog.open) {
        dialog.showModal();
      }
      dialog.scrollTop = 0;
      void loadFullSale(String(sale.sale_id || sale.id), controller.signal);
    }
    return () => {
      controller.abort();
      if (dialog?.open) {
        dialog.close();
      }
    };
  }, [sale]);

  async function loadFullSale(id: string, signal: AbortSignal) {
    setLoading(true);
    try {
      const res = await transporte.solicitarLoadFullSale({ id, signal });
      if (signal.aborted) return;
      setDetailedSale(res);
      requestAnimationFrame(() => {
        if (signal.aborted) return;
        if (dialogRef.current) {
          dialogRef.current.scrollTop = 0;
        }
      });
    } catch {
      if (!signal.aborted) setDetailedSale(null);
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  }

  return { activeTab, setActiveTab, detailedSale: activeSale, setDetailedSale, loading, dialogRef };
}
