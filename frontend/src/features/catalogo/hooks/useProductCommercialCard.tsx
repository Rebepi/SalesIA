import * as transporte from "../api/ProductCommercialCard";
import { FormEvent, useEffect, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { usePrompt } from "../../../ui/components/ConfirmDialog";
import { Row } from "../types/ProductCommercialCard";
import { SaleChoice } from "../types/ProductCommercialCard";
import { Props } from "../types/ProductCommercialCard";
import { Tab } from "../types/ProductCommercialCard";

export function useProductCommercialCard({ productId, productName, onRefresh }: Props) {
  const { prompt, PromptDialogNode } = usePrompt();

  const [tab, setTab] = useState<Tab>("overview");

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [productData, setProductData] = useState<{
    product: Row;
    profile: Row;
    variants: Row[];
    barcodes: Row[];
    volume_tiers: Row[];
    kit_items: Row[];
    warranty_claims: Row[];
    attachments: Row[];
  } | null>(null);

  const [previewQty, setPreviewQty] = useState("1");

  const [previewCurrency, setPreviewCurrency] = useState("USD");

  const [previewResult, setPreviewResult] = useState<Row | null>(null);

  const [previewLoading, setPreviewLoading] = useState(false);

  const [scannerCode, setScannerCode] = useState("");

  const [scannerResult, setScannerResult] = useState<Row | null>(null);

  const [warrantySale, setWarrantySale] = useState<SaleChoice | undefined>();

  const toast = useToast();

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const res = await transporte.solicitarLoadData({ productId });
      setProductData(res);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar ficha de producto";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, [productId]);

  async function handleUpdateProfile(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await transporte.solicitarHandleUpdateProfile({ productId, data });
      toast.success("Perfil comercial actualizado");
      void loadData();
      onRefresh();
    } catch {
      toast.error("No se pudo actualizar el perfil");
    }
  }

  async function handleAddVariant(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    let attributes = {};
    try {
      attributes = data.attributes ? JSON.parse(String(data.attributes)) : { talla: data.size, color: data.color };
    } catch {
      attributes = { talla: data.size, color: data.color };
    }
    try {
      await transporte.solicitarHandleAddVariant({ productId, data, attributes });
      toast.success("Variante añadida");
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al crear variante";
      toast.error("Error", msg);
    }
  }

  async function handleAddBarcode(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await transporte.solicitarHandleAddBarcode({ productId, data });
      toast.success("Código de barras añadido");
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al registrar código";
      toast.error("Error", msg);
    }
  }

  async function handleLookupBarcode() {
    if (!scannerCode.trim()) return;
    try {
      const res = await transporte.solicitarHandleLookupBarcode({ scannerCode });
      setScannerResult(res);
      toast.success("Código localizado", `Producto: ${String(res.product_name)}`);
    } catch {
      setScannerResult(null);
      toast.error("Código no encontrado", "No existe ningún producto asociado a este código.");
    }
  }

  async function handleRunPricePreview() {
    setPreviewLoading(true);
    setPreviewResult(null);
    try {
      const res = await transporte.solicitarHandleRunPricePreview({ previewCurrency, productId, previewQty });
      setPreviewResult(res);
      toast.success("Simulación calculada");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error en simulación de precio";
      toast.error("Error", msg);
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleAddVolumeTier(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await transporte.solicitarHandleAddVolumeTier({ productId, data });
      toast.success("Escala por volumen agregada");
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al agregar escala";
      toast.error("Error", msg);
    }
  }

  async function handleAddKitItem(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await transporte.solicitarHandleAddKitItem({ productId, data });
      toast.success("Componente agregado al kit");
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al agregar componente";
      toast.error("Error", msg);
    }
  }

  async function handleAddAttachment(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await transporte.solicitarHandleAddAttachment({ productId, data });
      toast.success("Archivo adjunto registrado");
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch {
      toast.error("Error al registrar adjunto");
    }
  }

  async function handleAddWarrantyClaim(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await transporte.solicitarHandleAddWarrantyClaim({ data, productId });
      toast.success("Reclamo de garantía registrado");
      setWarrantySale(undefined);
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch {
      toast.error("Error al registrar reclamo");
    }
  }

  async function handleDuplicate() {
    const sku = await prompt({ title: "Duplicar producto", label: "SKU para el producto duplicado", defaultValue: `${String(productData?.product?.sku || "COPIA")}-COPIA` });
    if (!sku) return;
    const name = await prompt({ title: "Nombre del producto duplicado", defaultValue: `${productName} copia` });
    if (!name) return;
    const barcode = await prompt({ title: "Código de barras", label: "Deja vacío si no aplica", defaultValue: "" }) || null;
    try {
      await transporte.solicitarHandleDuplicate({ productId, sku, name, barcode });
      toast.success("Producto duplicado", "La copia quedó activa y lista para editar.");
      onRefresh();
    } catch (err: unknown) {
      const detail = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "No se pudo duplicar el producto.";
      toast.error("Duplicación rechazada", detail);
    }
  }

  async function handleArchiveToggle() {
    const active = Boolean(productData?.product?.is_active);
    try {
      await transporte.solicitarHandleArchiveToggle({ productId, active });
      toast.success(active ? "Producto archivado" : "Producto restaurado");
      await loadData();
      onRefresh();
    } catch (err: unknown) {
      const detail = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "No se pudo cambiar el estado del producto.";
      toast.error("Operación rechazada", detail);
    }
  }
  return { PromptDialogNode, tab, setTab, loading, error, productData, previewQty, setPreviewQty, previewCurrency, setPreviewCurrency, previewResult, previewLoading, scannerCode, setScannerCode, scannerResult, warrantySale, setWarrantySale, handleUpdateProfile, handleAddVariant, handleAddBarcode, handleLookupBarcode, handleRunPricePreview, handleAddVolumeTier, handleAddKitItem, handleAddAttachment, handleAddWarrantyClaim, handleDuplicate, handleArchiveToggle };
}
