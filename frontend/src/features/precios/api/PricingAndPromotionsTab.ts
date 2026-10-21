import { apiClient } from "../../../api/client";
import { PriceList } from "../types/PricingAndPromotionsTab";
import { PriceItem } from "../types/PricingAndPromotionsTab";
import { ProductChoice } from "../types/PricingAndPromotionsTab";
import { Promotion } from "../types/PricingAndPromotionsTab";

export function solicitarLoadData() {
  return apiClient.request<PriceList[]>("/api/v1/price-lists");
}

export function solicitarLoadData2() {
  return apiClient.request<Promotion[]>("/api/v1/promotions");
}

export function solicitarRunSimulation({ simProductId, simQuantity, simSelectedList, simCouponCode }: { simProductId: string; simQuantity: string; simSelectedList: string; simCouponCode: string }) {
  return apiClient.request<{ total_estimated: string; discount_applied: string }>("/api/v1/prices/preview", {
    method: "POST",
    body: JSON.stringify({ product_id: simProductId, quantity: simQuantity, customer_id: simSelectedList || null, coupon_code: simCouponCode.trim() || null })
  });
}

export function solicitarHandleCreatePromotion({ newPromoCode, newPromoName, newPromoPriority, newPromoExclusive, newPromoDiscount }: { newPromoCode: string; newPromoName: string; newPromoPriority: string; newPromoExclusive: boolean; newPromoDiscount: string }) {
  return apiClient.request("/api/v1/promotions", {
    method: "POST",
    body: JSON.stringify({
      code: newPromoCode.trim().toUpperCase(),
      name: newPromoName.trim(),
      priority: Number(newPromoPriority),
      is_exclusive: newPromoExclusive,
      discount_percentage: String(Number(newPromoDiscount) / 100),
      min_quantity: 1,
      max_quota: 1000,
      start_date: new Date().toISOString(),
      end_date: new Date(Date.now() + 30 * 86400000).toISOString()
    })
  });
}

export function solicitarHandleTogglePromotion({ promo }: { promo: Promotion }) {
  return apiClient.request(`/api/v1/promotions/${promo.id}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: !promo.is_active })
  });
}

export function solicitarHandleDeletePromotion({ id }: { id: string }) {
  return apiClient.request(`/api/v1/promotions/${id}`, {
    method: "DELETE"
  });
}

export function solicitarHandleTogglePriceList({ pl }: { pl: PriceList }) {
  return apiClient.request(`/api/v1/price-lists/${pl.id}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: !pl.is_active })
  });
}

export function solicitarHandleDeletePriceList({ id }: { id: string }) {
  return apiClient.request(`/api/v1/price-lists/${id}`, {
    method: "DELETE"
  });
}

export function solicitarOpenPriceList({ priceList }: { priceList: PriceList }) {
  return apiClient.request<PriceItem[]>(`/api/v1/price-lists/${priceList.id}/items`);
}

export function solicitarUpdateManagedList({ managedList, data }: { managedList: PriceList; data: FormData }) {
  return apiClient.request(`/api/v1/price-lists/${managedList.id}`, { method: "PATCH", body: JSON.stringify({ name: String(data.get("name")), currency: String(data.get("currency")), priority: Number(data.get("priority")), valid_from: data.get("valid_from") ? new Date(String(data.get("valid_from"))).toISOString() : null, valid_to: data.get("valid_to") ? new Date(String(data.get("valid_to"))).toISOString() : null, target_type: String(data.get("target_type")), target_id: String(data.get("target_id") || "") || null }) });
}

export function solicitarAddPriceItem({ managedList, selectedProduct, newFixedPrice, newDiscount }: { managedList: PriceList; selectedProduct: ProductChoice; newFixedPrice: string; newDiscount: string }) {
  return apiClient.request(`/api/v1/price-lists/${managedList.id}/items`, { method: "POST", body: JSON.stringify({ product_id: selectedProduct.id, fixed_price: newFixedPrice || null, discount_percentage: newDiscount ? String(Number(newDiscount) / 100) : null }) });
}

export function solicitarDeletePriceItem({ managedList, itemId }: { managedList: PriceList; itemId: string }) {
  return apiClient.request(`/api/v1/price-lists/${managedList.id}/items/${itemId}`, { method: "DELETE" });
}

export function solicitarUpdatePriceItem({ managedList, item, fixedPrice, discount }: { managedList: PriceList; item: PriceItem; fixedPrice: string; discount: string }) {
  return apiClient.request(`/api/v1/price-lists/${managedList.id}/items/${item.id}`, { method: "PATCH", body: JSON.stringify({ fixed_price: fixedPrice || null, discount_percentage: discount ? String(Number(discount) / 100) : null }) });
}

export function solicitarCreatePriceList({ data }: { data: FormData }) {
  return apiClient.request("/api/v1/price-lists", { method: "POST", body: JSON.stringify({ code: String(data.get("code")).toUpperCase(), name: String(data.get("name")), currency: String(data.get("currency")).toUpperCase(), priority: Number(data.get("priority")), target_type: String(data.get("target_type")), target_id: String(data.get("target_id") || "") || null, valid_from: data.get("valid_from") ? new Date(String(data.get("valid_from"))).toISOString() : null, valid_to: data.get("valid_to") ? new Date(String(data.get("valid_to"))).toISOString() : null }) });
}
