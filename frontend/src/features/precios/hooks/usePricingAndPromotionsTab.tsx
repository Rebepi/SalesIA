import { apiClient } from "../../../api/client";
import * as transporte from "../api/PricingAndPromotionsTab";
import { useState, useEffect } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { usePrompt } from "../../../ui/components/ConfirmDialog";
import { PriceList } from "../types/PricingAndPromotionsTab";
import { PriceItem } from "../types/PricingAndPromotionsTab";
import { ProductChoice } from "../types/PricingAndPromotionsTab";
import { Promotion } from "../types/PricingAndPromotionsTab";

export function usePricingAndPromotionsTab({ canWrite = true }: {
  canWrite?: boolean;
}) {
  const { prompt, PromptDialogNode } = usePrompt();

  const [priceLists, setPriceLists] = useState<PriceList[]>([]);

  const [promotions, setPromotions] = useState<Promotion[]>([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [showSimulator, setShowSimulator] = useState(true);

  const [newPromoModalOpen, setNewPromoModalOpen] = useState(false);

  const [confirmDelete, setConfirmDelete] = useState<{
    type: "promo" | "price_list";
    id: string;
    code: string;
    name: string;
  } | null>(null);

  const [simProductId, setSimProductId] = useState("");

  const [simProducts, setSimProducts] = useState<{ id: string; name: string; sku: string }[]>([]);

  const [simCustomers, setSimCustomers] = useState<{ id: string; legal_name: string }[]>([]);

  const [simating, setSimulating] = useState(false);

  const [simQuantity, setSimQuantity] = useState("5");

  const [simSelectedList, setSimSelectedList] = useState("");

  const [simCouponCode, setSimCouponCode] = useState("");

  const [simResult, setSimResult] = useState<{ finalPrice: number; discount: number; conflict: string | null } | null>(null);

  const [newPromoCode, setNewPromoCode] = useState("");

  const [newPromoName, setNewPromoName] = useState("");

  const [newPromoDiscount, setNewPromoDiscount] = useState("10");

  const [newPromoPriority, setNewPromoPriority] = useState("50");

  const [newPromoExclusive, setNewPromoExclusive] = useState(false);

  const [busy, setBusy] = useState(false);

  const [managedList, setManagedList] = useState<PriceList | null>(null);

  const [priceItems, setPriceItems] = useState<PriceItem[]>([]);

  const [selectedProduct, setSelectedProduct] = useState<ProductChoice | undefined>();

  const [newFixedPrice, setNewFixedPrice] = useState("");

  const [newDiscount, setNewDiscount] = useState("");

  const [newListOpen, setNewListOpen] = useState(false);

  const toast = useToast();

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [plRes, prRes] = await Promise.allSettled([
        transporte.solicitarLoadData(),
        transporte.solicitarLoadData2()
      ]);
      if (plRes.status === "rejected") throw plRes.reason;
      if (prRes.status === "rejected") throw prRes.reason;
      if (plRes.status === "fulfilled") setPriceLists(plRes.value || []);
      if (prRes.status === "fulfilled") setPromotions(prRes.value || []);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar listas de precios";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!showSimulator) return;
    let active = true;
    Promise.all([
      apiClient.request<{ items: { id: string; name: string; sku: string }[] }>("/api/v1/products?limit=20"),
      apiClient.request<{ items: { id: string; legal_name: string }[] }>("/api/v1/customers?limit=20")
    ]).then(([products, customers]) => {
      if (active) { setSimProducts(products.items); setSimCustomers(customers.items); }
    }).catch(failure => { if (active) setError(String(failure?.detail || "No se pudieron cargar los datos del simulador.")); });
    return () => { active = false; };
  }, [showSimulator]);

  async function runSimulation() {
    if (!simProductId || Number(simQuantity) <= 0 || !Number.isFinite(Number(simQuantity))) return;
    setSimulating(true);
    setSimResult(null);
    try {
      const result = await transporte.solicitarRunSimulation({ simProductId, simQuantity, simSelectedList, simCouponCode });
      setSimResult({ finalPrice: Number(result.total_estimated), discount: Number(result.discount_applied), conflict: null });
    } catch (failure: unknown) {
      toast.error("No se pudo calcular el precio", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSimulating(false);
    }
  }

  async function handleCreatePromotion(e: React.FormEvent) {
    e.preventDefault();
    if (!newPromoCode || !newPromoName) return;
    setBusy(true);
    try {
      await transporte.solicitarHandleCreatePromotion({ newPromoCode, newPromoName, newPromoPriority, newPromoExclusive, newPromoDiscount });
      toast.success("Campaña creada", `Promoción ${newPromoCode} activada.`);
      setNewPromoCode("");
      setNewPromoName("");
      await loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al crear promoción";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function handleTogglePromotion(promo: Promotion) {
    if (!canWrite) return;
    try {
      await transporte.solicitarHandleTogglePromotion({ promo });
      toast.success(
        promo.is_active ? "Campaña pausada" : "Campaña activada",
        `La promoción ${promo.code} ahora está ${promo.is_active ? "inactiva" : "activa"}.`
      );
      await loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cambiar estado";
      toast.error("Error", msg);
    }
  }

  async function handleDeletePromotion(id: string, code: string) {
    if (!canWrite) return;
    setBusy(true);
    try {
      await transporte.solicitarHandleDeletePromotion({ id });
      toast.success("Campaña eliminada", `La promoción ${code} fue eliminada exitosamente.`);
      setConfirmDelete(null);
      await loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "No se pudo eliminar la promoción";
      toast.error("Acción denegada", msg);
    } finally {
      setBusy(false);
    }
  }

  async function handleTogglePriceList(pl: PriceList) {
    if (!canWrite) return;
    try {
      await transporte.solicitarHandleTogglePriceList({ pl });
      toast.success(
        pl.is_active ? "Lista pausada" : "Lista activada",
        `La lista ${pl.code} ahora está ${pl.is_active ? "inactiva" : "activa"}.`
      );
      await loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cambiar estado";
      toast.error("Error", msg);
    }
  }

  async function handleDeletePriceList(id: string, code: string) {
    if (!canWrite) return;
    setBusy(true);
    try {
      await transporte.solicitarHandleDeletePriceList({ id });
      toast.success("Lista eliminada", `La lista ${code} fue eliminada exitosamente.`);
      setConfirmDelete(null);
      await loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "No se pudo eliminar la lista";
      toast.error("Acción denegada", msg);
    } finally {
      setBusy(false);
    }
  }

  async function openPriceList(priceList: PriceList) {
    setManagedList(priceList);
    try {
      setPriceItems(await transporte.solicitarOpenPriceList({ priceList }));
    } catch (error: unknown) {
      toast.error("Error", error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudieron cargar los precios.");
    }
  }

  async function updateManagedList(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!managedList) return;
    const data = new FormData(event.currentTarget);
    await transporte.solicitarUpdateManagedList({ managedList, data });
    toast.success("Lista actualizada", "Vigencia, prioridad, moneda y alcance guardados.");
    await loadData();
  }

  async function addPriceItem() {
    if (!managedList || !selectedProduct || (!newFixedPrice && !newDiscount)) return;
    await transporte.solicitarAddPriceItem({ managedList, selectedProduct, newFixedPrice, newDiscount });
    setSelectedProduct(undefined);
    setNewFixedPrice("");
    setNewDiscount("");
    await openPriceList(managedList);
  }

  async function deletePriceItem(itemId: string) {
    if (!managedList) return;
    await transporte.solicitarDeletePriceItem({ managedList, itemId });
    await openPriceList(managedList);
  }

  async function updatePriceItem(item: PriceItem) {
    if (!managedList) return;
    const fixedPrice = await prompt({ title: "Precio fijo", label: "Deja vacío si usarás descuento", defaultValue: item.fixed_price || "" });
    if (fixedPrice === null) return;
    const discount = await prompt({ title: "Descuento porcentual", label: "Deja vacío si usarás precio fijo", defaultValue: item.discount_percentage ? String(Number(item.discount_percentage) * 100) : "" });
    if (discount === null || (!fixedPrice && !discount)) return;
    await transporte.solicitarUpdatePriceItem({ managedList, item, fixedPrice, discount });
    toast.success("Precio actualizado", `${item.product_name} ya usa la nueva regla.`);
    await openPriceList(managedList);
  }

  async function createPriceList(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await transporte.solicitarCreatePriceList({ data });
    setNewListOpen(false);
    toast.success("Lista creada", "La nueva lista ya puede recibir productos y precios.");
    await loadData();
  }
  return { PromptDialogNode, priceLists, promotions, loading, error, showSimulator, setShowSimulator, newPromoModalOpen, setNewPromoModalOpen, confirmDelete, setConfirmDelete, simProductId, setSimProductId, simProducts, simCustomers, simating, simQuantity, setSimQuantity, simSelectedList, setSimSelectedList, simCouponCode, setSimCouponCode, simResult, setSimResult, newPromoCode, setNewPromoCode, newPromoName, setNewPromoName, newPromoDiscount, setNewPromoDiscount, newPromoPriority, setNewPromoPriority, newPromoExclusive, setNewPromoExclusive, busy, managedList, setManagedList, priceItems, selectedProduct, setSelectedProduct, newFixedPrice, setNewFixedPrice, newDiscount, setNewDiscount, newListOpen, setNewListOpen, loadData, runSimulation, handleCreatePromotion, handleTogglePromotion, handleDeletePromotion, handleTogglePriceList, handleDeletePriceList, openPriceList, updateManagedList, addPriceItem, deletePriceItem, updatePriceItem, createPriceList };
}
