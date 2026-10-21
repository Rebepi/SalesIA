import { apiClient } from "../../../api/client";
import { Row } from "../types/ProductCommercialCard";

export function solicitarLoadData({ productId }: { productId: string }) {
  return apiClient.request<{
    product: Row;
    profile: Row;
    variants: Row[];
    barcodes: Row[];
    volume_tiers: Row[];
    kit_items: Row[];
    warranty_claims: Row[];
    attachments: Row[];
  }>(`/api/v1/products/${productId}/profile`);
}

export function solicitarHandleUpdateProfile({ productId, data }: { productId: string; data: { [k: string]: FormDataEntryValue; } }) {
  return apiClient.request(`/api/v1/products/${productId}/profile`, {
    method: "POST",
    body: JSON.stringify({
      product_type: data.product_type,
      track_inventory: data.track_inventory === "true",
      default_warranty_months: Number(data.default_warranty_months || 0),
      allow_fractional: data.allow_fractional === "true"
    })
  });
}

export function solicitarHandleAddVariant({ productId, data, attributes }: { productId: string; data: { [k: string]: FormDataEntryValue; }; attributes: {} }) {
  return apiClient.request(`/api/v1/products/${productId}/variants`, {
    method: "POST",
    body: JSON.stringify({
      sku: data.sku,
      name: data.name,
      attributes,
      price_delta: data.price_delta || "0.00"
    })
  });
}

export function solicitarHandleAddBarcode({ productId, data }: { productId: string; data: { [k: string]: FormDataEntryValue; } }) {
  return apiClient.request(`/api/v1/products/${productId}/barcodes`, {
    method: "POST",
    body: JSON.stringify({
      barcode: data.barcode,
      barcode_type: data.symbology || "EAN13",
      is_primary: data.is_primary === "true"
    })
  });
}

export function solicitarHandleLookupBarcode({ scannerCode }: { scannerCode: string }) {
  return apiClient.request<Row>(`/api/v1/barcodes/lookup?barcode=${encodeURIComponent(scannerCode.trim())}`);
}

export function solicitarHandleRunPricePreview({ previewCurrency, productId, previewQty }: { previewCurrency: string; productId: string; previewQty: string }) {
  return apiClient.request<Row>("/api/v1/prices/preview", {
    method: "POST",
    body: JSON.stringify({
      currency: previewCurrency,
      lines: [{ product_id: productId, quantity: Number(previewQty) }]
    })
  });
}

export function solicitarHandleAddVolumeTier({ productId, data }: { productId: string; data: { [k: string]: FormDataEntryValue; } }) {
  return apiClient.request(`/api/v1/products/${productId}/volume-tiers`, {
    method: "POST",
    body: JSON.stringify({
      min_quantity: Number(data.min_quantity),
      max_quantity: data.max_quantity ? Number(data.max_quantity) : null,
      unit_price: data.unit_price || null,
      discount_percent: data.discount_percent || null
    })
  });
}

export function solicitarHandleAddKitItem({ productId, data }: { productId: string; data: { [k: string]: FormDataEntryValue; } }) {
  return apiClient.request(`/api/v1/products/${productId}/kit-items`, {
    method: "POST",
    body: JSON.stringify({
      component_product_id: data.component_product_id,
      quantity: Number(data.quantity)
    })
  });
}

export function solicitarHandleAddAttachment({ productId, data }: { productId: string; data: { [k: string]: FormDataEntryValue; } }) {
  return apiClient.request(`/api/v1/products/${productId}/attachments`, {
    method: "POST",
    body: JSON.stringify({
      file_url: data.file_url,
      file_name: data.file_name,
      content_type: "application/octet-stream",
      file_size_bytes: 1,
      is_primary: data.is_primary === "true"
    })
  });
}

export function solicitarHandleAddWarrantyClaim({ data, productId }: { data: { [k: string]: FormDataEntryValue; }; productId: string }) {
  return apiClient.request("/api/v1/products/warranty/claims", {
    method: "POST",
    body: JSON.stringify({
      sale_id: data.sale_id,
      product_id: productId,
      serial_number: data.serial_number,
      issue_description: data.description
    })
  });
}

export function solicitarHandleDuplicate({ productId, sku, name, barcode }: { productId: string; sku: string; name: string; barcode: string | null }) {
  return apiClient.request(`/api/v1/products/${productId}/duplicate`, { method: "POST", body: JSON.stringify({ sku, name, barcode }) });
}

export function solicitarHandleArchiveToggle({ productId, active }: { productId: string; active: boolean }) {
  return apiClient.request(`/api/v1/products/${productId}/${active ? "archive" : "restore"}`, { method: "POST" });
}
