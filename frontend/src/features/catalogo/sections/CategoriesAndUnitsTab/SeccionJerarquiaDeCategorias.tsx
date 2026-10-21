import type { useCategoriesAndUnitsTab } from "../../hooks/useCategoriesAndUnitsTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Plus, Edit2, ChevronRight, X } from "lucide-react";
import { apiClient } from "../../../../api/client";

export function SeccionJerarquiaDeCategorias({ canWrite, setEditingCat, categories, orderedCategories, selectedCat, selectCategory, editingCat, handleSaveCategory, descendants, impact, busy, archiveCategory, confirm, setBusy, loadData, toast }: { setEditingCat: ReturnType<typeof useCategoriesAndUnitsTab>["setEditingCat"]; categories: ReturnType<typeof useCategoriesAndUnitsTab>["categories"]; orderedCategories: ReturnType<typeof useCategoriesAndUnitsTab>["orderedCategories"]; selectedCat: ReturnType<typeof useCategoriesAndUnitsTab>["selectedCat"]; selectCategory: ReturnType<typeof useCategoriesAndUnitsTab>["selectCategory"]; editingCat: ReturnType<typeof useCategoriesAndUnitsTab>["editingCat"]; handleSaveCategory: ReturnType<typeof useCategoriesAndUnitsTab>["handleSaveCategory"]; descendants: ReturnType<typeof useCategoriesAndUnitsTab>["descendants"]; impact: ReturnType<typeof useCategoriesAndUnitsTab>["impact"]; busy: ReturnType<typeof useCategoriesAndUnitsTab>["busy"]; archiveCategory: ReturnType<typeof useCategoriesAndUnitsTab>["archiveCategory"]; confirm: ReturnType<typeof useCategoriesAndUnitsTab>["confirm"]; setBusy: ReturnType<typeof useCategoriesAndUnitsTab>["setBusy"]; loadData: ReturnType<typeof useCategoriesAndUnitsTab>["loadData"]; toast: ReturnType<typeof useCategoriesAndUnitsTab>["toast"] } & { canWrite: NonNullable<{ canWrite?: boolean }["canWrite"]> }) {
  return (<div className="grid lg:grid-cols-[1fr_360px] gap-6 items-start">
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <h3 className="font-bold text-slate-900 text-sm">Jerarquía de Categorías</h3>
        {canWrite && (
          <button
            type="button"
            onClick={() => setEditingCat({ code: "", name: "", parent_id: null })}
            className="inline-flex items-center gap-1 rounded-xl bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-700 hover:bg-teal-100"
          >
            <Plus className="h-3.5 w-3.5" /> Nueva Categoría
          </button>
        )}
      </div>

      {categories.length === 0 ? (
        <p className="py-8 text-center text-xs text-slate-400">Sin categorías registradas.</p>
      ) : (
        <ul role="tree" aria-label="Árbol de categorías" tabIndex={0} className="max-h-[60vh] overflow-y-auto overscroll-contain space-y-1 pr-2">
          {orderedCategories.map(c => {
            const isChild = Boolean(c.parent_id);
            const isSelected = selectedCat?.id === c.id;
            return (
              <li
                key={c.id}
                role="treeitem"
                aria-selected={isSelected}
                aria-level={c.level}
                style={{ paddingLeft: `${(c.level - 1) * 20}px` }}
                className="group"
              >
                <div
                  className={`flex items-center justify-between p-2.5 rounded-xl transition ${isSelected ? "bg-teal-50 border border-teal-300" : "hover:bg-slate-50 border border-transparent"
                    }`}
                >
                  <div className="flex items-center gap-2">
                    {isChild && <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}
                    <span className="font-mono text-xs text-slate-400">{c.code}</span>
                    <span className="text-xs font-medium text-slate-800">{c.name}{!c.is_active && <span className="ml-2 text-[10px] text-amber-700">Archivada</span>}</span>
                  </div>
                  {canWrite && (
                    <button
                      type="button"
                      aria-label={`Editar ${c.name}`}
                      onClick={() => selectCategory(c)}
                      className="p-1 text-slate-500 hover:text-teal-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-600"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>

    {editingCat ? (
      <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="font-bold text-slate-900 text-sm">
            {editingCat.id ? "Editar Categoría" : "Alta de Categoría"}
          </h3>
          <button type="button" onClick={() => setEditingCat(null)} className="text-slate-400 hover:text-slate-700">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSaveCategory} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-600 mb-1">Nombre</label>
            <input
              required
              value={editingCat.name || ""}
              onChange={e => setEditingCat({ ...editingCat, name: e.target.value })}
              className="w-full rounded-xl border border-slate-300 p-2.5 outline-none focus:border-teal-600"
            />
          </div>
          {!editingCat.id && (
            <div>
              <label className="block font-semibold text-slate-600 mb-1">Código (opcional)</label>
              <input
                value={editingCat.code || ""}
                onChange={e => setEditingCat({ ...editingCat, code: e.target.value })}
                placeholder="CAT-001"
                className="w-full rounded-xl border border-slate-300 p-2.5 outline-none focus:border-teal-600"
              />
            </div>
          )}
          <div>
            <label className="block font-semibold text-slate-600 mb-1">Categoría Padre (Jerarquía)</label>
            <CustomSelect remote={{ resource: "categories", exclude_subtree: editingCat.id || undefined, active_only: true }}
              value={editingCat.parent_id || ""}
              onChange={e => setEditingCat({ ...editingCat, parent_id: e.target.value || null })}
              className="w-full rounded-xl border border-slate-300 p-2.5 outline-none focus:border-teal-600"
            >
              <option value="">Raíz (Sin padre)</option>
              {orderedCategories.filter(c => c.is_active && (!editingCat.id || !descendants(editingCat.id).has(c.id))).map(c => (
                <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
              ))}
            </CustomSelect>
          </div>
          <div>
            <label className="block font-semibold text-slate-600 mb-1">Orden dentro del nivel</label>
            <input type="number" min="0" value={editingCat.sort_order || 0} onChange={e => setEditingCat({ ...editingCat, sort_order: Number(e.target.value) })} className="w-full rounded-xl border border-slate-300 p-2.5 outline-none focus:border-teal-600" />
          </div>
          {editingCat.id && <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600"><strong className="block text-slate-800">Impacto del cambio</strong>{impact ? `${impact.product_count} productos en ${impact.category_count} categorías del subárbol.` : "Calculando productos afectados…"}</div>}
          <div className="flex justify-end gap-2 pt-3">
            {editingCat.id && editingCat.is_active !== false && <button type="button" disabled={busy || !impact} onClick={archiveCategory} className="mr-auto rounded-xl border border-amber-300 px-3 py-2 font-semibold text-amber-700">Archivar</button>}
            {editingCat.id && editingCat.is_active === false && <button type="button" disabled={busy} onClick={async () => {
              if (!editingCat.id || busy) return;
              const ids = [...descendants(editingCat.id)];
              if (!await confirm({ title: "¿Restaurar categoría?", text: `Se habilitarán ${ids.length} categorías para asignar productos de nuevo.`, confirmLabel: "Restaurar" })) return;
              setBusy(true);
              try { await apiClient.request(`/api/v1/categories/${editingCat.id}/restore`, { method: "POST", body: JSON.stringify({ category_ids: ids }) }); setEditingCat(null); await loadData(); toast.success("Categorías restauradas"); } catch { toast.error("No se pudo restaurar", "Revisa que la categoría padre esté activa e inténtalo de nuevo."); } finally { setBusy(false); }
            }} className="mr-auto rounded-xl border px-3 py-2 font-semibold text-teal-700">Restaurar</button>}
            <button
              type="button"
              onClick={() => setEditingCat(null)}
              className="rounded-xl border border-slate-200 px-3 py-2 font-semibold text-slate-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={busy}
              className="rounded-xl bg-teal-700 px-4 py-2 font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
            >
              {busy ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      </aside>
    ) : (
      <aside className="rounded-3xl border border-slate-200 bg-slate-50 p-6 text-center text-xs text-slate-400">
        Selecciona una categoría del árbol para editar o presiona "Nueva Categoría" para añadir un nodo.
      </aside>
    )}
  </div>);
}
