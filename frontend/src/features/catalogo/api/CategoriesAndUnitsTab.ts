import { apiClient } from "../../../api/client";
import { Category } from "../types/CategoriesAndUnitsTab";
import { Unit } from "../types/CategoriesAndUnitsTab";
import { UnitConversion } from "../types/CategoriesAndUnitsTab";

export function solicitarLoadData() {
  return apiClient.request<Category[]>("/api/v1/categories");
}

export function solicitarLoadData2() {
  return apiClient.request<Unit[]>("/api/v1/units");
}

export function solicitarLoadData3() {
  return apiClient.request<UnitConversion[]>("/api/v1/units/conversions");
}

export function solicitarHandleSaveCategory({ editingCat }: { editingCat: Partial<Category> }) {
  return apiClient.request(`/api/v1/categories/${editingCat.id}`, {
    method: "PATCH",
    body: JSON.stringify({
      name: editingCat.name,
      parent_id: editingCat.parent_id || null,
      sort_order: editingCat.sort_order || 0
    })
  });
}

export function solicitarHandleSaveCategory2({ editingCat }: { editingCat: Partial<Category> }) {
  return apiClient.request("/api/v1/categories", {
    method: "POST",
    body: JSON.stringify({
      code: editingCat.code || undefined,
      name: editingCat.name,
      parent_id: editingCat.parent_id || null,
      sort_order: 0
    })
  });
}

export function solicitarSelectCategory({ category }: { category: Category }) {
  return apiClient.request<{ category_count: number; product_count: number }>(`/api/v1/categories/${category.id}/impact`);
}

export function solicitarArchiveCategory({ categoryId }: { categoryId: string }) {
  return apiClient.request<{ archived_ids: string[] }>(`/api/v1/categories/${categoryId}/archive`, { method: "POST" });
}

export function solicitarDatos({ categoryId, result }: { categoryId: string; result: { archived_ids: string[]; } }) {
  return apiClient.request(`/api/v1/categories/${categoryId}/restore`, { method: "POST", body: JSON.stringify({ category_ids: result.archived_ids }) });
}

export function solicitarHandleCreateUnit({ newUnitCode, newUnitName, newUnitAllowFrac }: { newUnitCode: string; newUnitName: string; newUnitAllowFrac: boolean }) {
  return apiClient.request("/api/v1/units", {
    method: "POST",
    body: JSON.stringify({
      code: newUnitCode.trim().toUpperCase(),
      name: newUnitName.trim(),
      allow_fractions: newUnitAllowFrac,
      precision_digits: newUnitAllowFrac ? 2 : 0
    })
  });
}

export function solicitarHandleCreateConversion({ convFrom, convTo, convFactor }: { convFrom: string; convTo: string; convFactor: string }) {
  return apiClient.request<UnitConversion>("/api/v1/units/conversions", {
    method: "POST",
    body: JSON.stringify({
      from_unit: convFrom.toUpperCase(),
      to_unit: convTo.toUpperCase(),
      factor: convFactor
    })
  });
}
