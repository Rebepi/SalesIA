import * as transporte from "../api/CategoriesAndUnitsTab";
import { useState, useEffect, useMemo, useRef } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { Category } from "../types/CategoriesAndUnitsTab";
import { Unit } from "../types/CategoriesAndUnitsTab";
import { UnitConversion } from "../types/CategoriesAndUnitsTab";

export function useCategoriesAndUnitsTab(_props: {
  canWrite?: boolean;
}) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [subtab, setSubtab] = useState<"categories" | "units">("categories");

  const [categories, setCategories] = useState<Category[]>([]);

  const [units, setUnits] = useState<Unit[]>([]);

  const [conversions, setConversions] = useState<UnitConversion[]>([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [selectedCat, setSelectedCat] = useState<Category | null>(null);

  const [editingCat, setEditingCat] = useState<Partial<Category> | null>(null);

  const [newUnitCode, setNewUnitCode] = useState("");

  const [newUnitName, setNewUnitName] = useState("");

  const [newUnitAllowFrac, setNewUnitAllowFrac] = useState(false);

  const [convFrom, setConvFrom] = useState("NIU");

  const [convTo, setConvTo] = useState("BX");

  const [convFactor, setConvFactor] = useState("12");

  const [busy, setBusy] = useState(false);

  const [impact, setImpact] = useState<{ category_count: number; product_count: number } | null>(null);

  const toast = useToast();

  const impactRequest = useRef(0);

  const orderedCategories = useMemo(() => {
    const result: Category[] = [];
    const visited = new Set<string>();
    const visit = (parent: string | null) => {
      categories.filter(item => (item.parent_id || null) === parent).sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name, "es")).forEach(item => {
        if (visited.has(item.id)) return;
        visited.add(item.id);
        result.push(item);
        visit(item.id);
      });
    };
    visit(null);
    categories.filter(item => !visited.has(item.id)).forEach(item => result.push(item));
    return result;
  }, [categories]);

  function descendants(id: string) {
    const found = new Set([id]);
    let previous = 0;
    while (found.size !== previous) {
      previous = found.size;
      categories.forEach(item => { if (item.parent_id && found.has(item.parent_id)) found.add(item.id); });
    }
    return found;
  }

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [catRes, unitRes, conversionRes] = await Promise.allSettled([
        transporte.solicitarLoadData(),
        transporte.solicitarLoadData2(),
        transporte.solicitarLoadData3()
      ]);
      if (catRes.status === "fulfilled") setCategories(catRes.value || []);
      if (unitRes.status === "fulfilled") setUnits(unitRes.value || []);
      if (conversionRes.status === "fulfilled") setConversions(conversionRes.value || []);
      const failure = [catRes, unitRes, conversionRes].find((result) => result.status === "rejected");
      if (failure?.status === "rejected") throw failure.reason;
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar categorías";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveCategory(e: React.FormEvent) {
    e.preventDefault();
    if (!editingCat || !editingCat.name) return;
    if (editingCat.id && editingCat.parent_id === editingCat.id) {
      toast.error("Ciclo no permitido", "Una categoría no puede ser subcategoría de sí misma.");
      return;
    }
    setBusy(true);
    try {
      if (editingCat.id) {
        await transporte.solicitarHandleSaveCategory({ editingCat });
        toast.success("Categoría actualizada", `Se guardaron los cambios para ${editingCat.name}`);
      } else {
        await transporte.solicitarHandleSaveCategory2({ editingCat });
        toast.success("Categoría creada", "Nueva categoría registrada en el árbol.");
      }
      setEditingCat(null);
      await loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al guardar categoría";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function selectCategory(category: Category) {
    const request = ++impactRequest.current;
    setSelectedCat(category);
    setEditingCat(category);
    setImpact(null);
    try {
      const result = await transporte.solicitarSelectCategory({ category });
      if (request === impactRequest.current) setImpact(result);
    } catch {
      if (request === impactRequest.current) toast.error("Impacto no disponible", "Vuelve a seleccionar la categoría antes de archivarla.");
    }
  }

  async function archiveCategory() {
    if (!editingCat?.id || !impact || busy) return;
    if (!await confirm({ title: "¿Archivar categoría?", text: `Se archivarán ${impact?.category_count || 1} categorías y se conservarán ${impact?.product_count || 0} productos.`, danger: true, confirmLabel: "Archivar" })) return;
    setBusy(true);
    try {
      const categoryId = editingCat.id;
      const result = await transporte.solicitarArchiveCategory({ categoryId });
      setEditingCat(null);
      setSelectedCat(null);
      setImpact(null);
      toast.success("Categoría archivada", "Los productos se conservaron y la categoría dejó de estar disponible para nuevas asignaciones.", { duration: 8000, undo: { label: "Deshacer archivado", execute: async () => { await transporte.solicitarDatos({ categoryId, result }); await loadData(); } } });
      await loadData();
    } catch (error: unknown) {
      toast.error("Error", error && typeof error === "object" && "detail" in error ? String((error as { detail: unknown }).detail) : "No se pudo archivar la categoría.");
    } finally { setBusy(false); }
  }

  async function handleCreateUnit(e: React.FormEvent) {
    e.preventDefault();
    if (!newUnitCode || !newUnitName) return;
    setBusy(true);
    try {
      await transporte.solicitarHandleCreateUnit({ newUnitCode, newUnitName, newUnitAllowFrac });
      toast.success("Unidad creada", `Unidad ${newUnitCode} registrada.`);
      setNewUnitCode("");
      setNewUnitName("");
      await loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al crear unidad";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateConversion(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const conv = await transporte.solicitarHandleCreateConversion({ convFrom, convTo, convFactor });
      setConversions(prev => [conv, ...prev]);
      toast.success("Equivalencia creada", `1 ${convTo} = ${convFactor} ${convFrom}`);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al crear conversión";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }
  return { confirm, ConfirmDialogNode, subtab, setSubtab, categories, units, conversions, loading, error, selectedCat, editingCat, setEditingCat, newUnitCode, setNewUnitCode, newUnitName, setNewUnitName, newUnitAllowFrac, setNewUnitAllowFrac, convFrom, setConvFrom, convTo, setConvTo, convFactor, setConvFactor, busy, setBusy, impact, toast, orderedCategories, descendants, loadData, handleSaveCategory, selectCategory, archiveCategory, handleCreateUnit, handleCreateConversion };
}
