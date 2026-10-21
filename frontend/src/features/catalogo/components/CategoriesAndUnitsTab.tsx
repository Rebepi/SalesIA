import { SeccionJerarquiaDeCategorias } from "../sections/CategoriesAndUnitsTab/SeccionJerarquiaDeCategorias";
import { SeccionUnidadesDeMedida } from "../sections/CategoriesAndUnitsTab/SeccionUnidadesDeMedida";
import { useCategoriesAndUnitsTab } from "../hooks/useCategoriesAndUnitsTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { FolderTree, Scale, LoaderCircle, AlertCircle } from "lucide-react";

export function CategoriesAndUnitsTab({ canWrite = true }: { canWrite?: boolean }) {
  const { confirm, ConfirmDialogNode, subtab, setSubtab, categories, units, conversions, loading, error, selectedCat, editingCat, setEditingCat, newUnitCode, setNewUnitCode, newUnitName, setNewUnitName, newUnitAllowFrac, setNewUnitAllowFrac, convFrom, setConvFrom, convTo, setConvTo, convFactor, setConvFactor, busy, setBusy, impact, toast, orderedCategories, descendants, loadData, handleSaveCategory, selectCategory, archiveCategory, handleCreateUnit, handleCreateConversion } = useCategoriesAndUnitsTab({ canWrite });
  return (
    <div id="scr-011-categories-and-units" className="space-y-6">
      <NavbarSectionHeader view="categories" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Categorías y Unidades</h2>
          <p className="text-xs text-slate-500">
            Árbol taxonómico accesible de productos y factores de conversión métrica
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setSubtab("categories")}
            className={`inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold transition ${subtab === "categories" ? "bg-teal-700 text-white" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}
          >
            <FolderTree className="h-4 w-4" /> Árbol de Categorías
          </button>
          <button
            type="button"
            onClick={() => setSubtab("units")}
            className={`inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold transition ${subtab === "units" ? "bg-teal-700 text-white" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}
          >
            <Scale className="h-4 w-4" /> Unidades y Equivalencias
          </button>
        </div>
      </NavbarSectionHeader>

      {error && (
        <div role="alert" className="flex items-center gap-2 rounded-2xl bg-red-50 p-4 text-xs text-red-800">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <div className="flex-1">
            <p className="font-semibold">{error}</p>
            <button type="button" onClick={loadData} className="mt-1 font-bold underline">Reintentar</button>
          </div>
        </div>
      )}

      {loading ? (
        <div role="status" className="flex justify-center py-20 text-slate-400">
          <LoaderCircle className="h-8 w-8 motion-safe:animate-spin text-teal-600" />
        </div>
      ) : subtab === "categories" ? (
        <SeccionJerarquiaDeCategorias canWrite={canWrite} setEditingCat={setEditingCat} categories={categories} orderedCategories={orderedCategories} selectedCat={selectedCat} selectCategory={selectCategory} editingCat={editingCat} handleSaveCategory={handleSaveCategory} descendants={descendants} impact={impact} busy={busy} archiveCategory={archiveCategory} confirm={confirm} setBusy={setBusy} loadData={loadData} toast={toast} />
      ) : (
        <SeccionUnidadesDeMedida units={units} canWrite={canWrite} handleCreateUnit={handleCreateUnit} newUnitCode={newUnitCode} setNewUnitCode={setNewUnitCode} newUnitName={newUnitName} setNewUnitName={setNewUnitName} newUnitAllowFrac={newUnitAllowFrac} setNewUnitAllowFrac={setNewUnitAllowFrac} busy={busy} handleCreateConversion={handleCreateConversion} convFrom={convFrom} setConvFrom={setConvFrom} convTo={convTo} setConvTo={setConvTo} convFactor={convFactor} setConvFactor={setConvFactor} conversions={conversions} />
      )}
      {ConfirmDialogNode}
    </div>
  );
}
