import type { usePricingAndPromotionsTab } from "../../hooks/usePricingAndPromotionsTab";
import { Tag, Flame, Plus, Power, Trash2, Pencil } from "lucide-react";

export function SeccionListasDePreciosYVigencias({ priceLists, canWrite, setNewListOpen, openPriceList, handleTogglePriceList, setConfirmDelete, promotions, setNewPromoModalOpen, handleTogglePromotion }: { priceLists: ReturnType<typeof usePricingAndPromotionsTab>["priceLists"]; setNewListOpen: ReturnType<typeof usePricingAndPromotionsTab>["setNewListOpen"]; openPriceList: ReturnType<typeof usePricingAndPromotionsTab>["openPriceList"]; handleTogglePriceList: ReturnType<typeof usePricingAndPromotionsTab>["handleTogglePriceList"]; setConfirmDelete: ReturnType<typeof usePricingAndPromotionsTab>["setConfirmDelete"]; promotions: ReturnType<typeof usePricingAndPromotionsTab>["promotions"]; setNewPromoModalOpen: ReturnType<typeof usePricingAndPromotionsTab>["setNewPromoModalOpen"]; handleTogglePromotion: ReturnType<typeof usePricingAndPromotionsTab>["handleTogglePromotion"] } & { canWrite: NonNullable<{ canWrite?: boolean }["canWrite"]> }) {
  return (<div className="grid lg:grid-cols-2 gap-4 sm:gap-5 items-start">

    <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-4 sm:p-5 shadow-sm dark:shadow-lg dark:shadow-black/20 flex flex-col space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20">
            <Tag className="h-3.5 w-3.5" />
          </div>
          <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">Listas de Precios y Vigencias</h3>
          <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/60">
            {priceLists.length}
          </span>
        </div>
        {canWrite && <button type="button" onClick={() => setNewListOpen(true)} className="inline-flex items-center gap-1 rounded-lg border border-teal-500/30 px-3 py-1.5 text-xs font-semibold text-teal-700 dark:text-teal-300"><Plus className="h-3.5 w-3.5" />Nueva lista</button>}
      </div>

      {priceLists.length === 0 ? (
        <p className="py-10 text-center text-sm text-slate-400 dark:text-slate-500">Sin listas registradas.</p>
      ) : (
        <div className="grid gap-2.5 max-h-[340px] overflow-y-auto pr-1">
          {priceLists.map(pl => (
            <div
              key={pl.id}
              className={`relative rounded-xl border p-3.5 transition-all ${pl.is_active
                ? "border-teal-500/25 bg-teal-500/5 dark:bg-teal-500/8"
                : "border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/40"
                }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2.5">
                <div className="min-w-0">
                  <p className="font-mono font-bold text-[11px] text-teal-700 dark:text-teal-400 truncate">{pl.code}</p>
                  <p className="font-semibold text-slate-900 dark:text-slate-100 text-xs truncate mt-0.5">{pl.name}</p>
                </div>
                {pl.is_active ? (
                  <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Activa
                  </span>
                ) : (
                  <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-slate-200 dark:bg-slate-700/50 px-2 py-0.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-600/40">
                    <span className="h-1.5 w-1.5 rounded-full bg-slate-400"></span> Pausada
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                <span className="rounded-md bg-teal-50 dark:bg-teal-500/15 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-500/30 px-2 py-0.5 font-bold">{pl.currency}</span>
                <span className="rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50 px-2 py-0.5">Prioridad {pl.priority}</span>
                <span className="rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50 px-2 py-0.5">
                  {pl.valid_to ? `Hasta ${pl.valid_to.substring(0, 10)}` : "Vigencia indefinida"}
                </span>
              </div>

              {canWrite && (
                <div className="flex items-center gap-2 mt-3 pt-2.5 border-t border-slate-200/70 dark:border-slate-700/40">
                  <button type="button" onClick={() => openPriceList(pl)} className="inline-flex items-center gap-1.5 rounded-lg border border-teal-500/40 px-3 py-1.5 text-xs font-semibold text-teal-700 dark:text-teal-300"><Pencil className="h-3.5 w-3.5" />Gestionar</button>
                  <button
                    type="button"
                    onClick={() => handleTogglePriceList(pl)}
                    className={`flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg border py-1.5 text-xs font-semibold transition ${pl.is_active
                      ? "border-amber-500/40 bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-500/20"
                      : "border-emerald-500/40 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-500/20"
                      }`}
                  >
                    <Power className="h-3.5 w-3.5" />
                    {pl.is_active ? "Pausar" : "Activar"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDelete({ type: "price_list", id: pl.id, code: pl.code, name: pl.name })}
                    title="Eliminar lista de precios"
                    className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-rose-500/40 bg-rose-50 dark:bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-700 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-500/20 transition"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Eliminar
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>

    <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-4 sm:p-5 shadow-sm dark:shadow-lg dark:shadow-black/20 flex flex-col space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
            <Flame className="h-3.5 w-3.5" />
          </div>
          <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">Reglas de Promoción y Campañas</h3>
          <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/60">
            {promotions.length}
          </span>
        </div>
        {canWrite && (
          <button
            type="button"
            onClick={() => setNewPromoModalOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-teal-500/30 bg-teal-50 dark:bg-teal-500/10 px-3 py-1.5 text-xs font-semibold text-teal-700 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-500/20 transition shadow-xs"
          >
            <Plus className="h-3.5 w-3.5" />
            Crear campaña
          </button>
        )}
      </div>

      {promotions.length === 0 ? (
        <p className="py-10 text-center text-sm text-slate-400 dark:text-slate-500">Sin promociones registradas.</p>
      ) : (
        <div className="grid gap-2.5 max-h-[340px] overflow-y-auto pr-1">
          {promotions.map(pr => {
            const isExpired = pr.end_date && new Date(pr.end_date) < new Date();
            const isExhausted = pr.current_uses >= pr.max_quota;
            const canDelete = pr.current_uses === 0;

            const statusBadge = !pr.is_active ? (
              <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-slate-200 dark:bg-slate-700/50 px-2 py-0.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-600/40">
                <span className="h-1.5 w-1.5 rounded-full bg-slate-400"></span> Pausada
              </span>
            ) : isExpired ? (
              <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/30">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span> Expirada
              </span>
            ) : isExhausted ? (
              <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-purple-500/15 px-2 py-0.5 text-[10px] font-semibold text-purple-600 dark:text-purple-400 border border-purple-500/30">
                <span className="h-1.5 w-1.5 rounded-full bg-purple-500"></span> Agotada
              </span>
            ) : (
              <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Activa
              </span>
            );

            return (
              <div
                key={pr.id}
                className={`relative rounded-xl border p-3.5 transition-all ${pr.is_active && !isExpired && !isExhausted
                  ? "border-orange-500/25 bg-orange-500/5 dark:bg-orange-500/8"
                  : "border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/40"
                  }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2.5">
                  <div className="min-w-0">
                    <p className="font-mono font-bold text-[11px] text-orange-700 dark:text-orange-400 truncate">{pr.code}</p>
                    <p className="font-semibold text-slate-900 dark:text-slate-100 text-xs truncate mt-0.5">{pr.name}</p>
                  </div>
                  {statusBadge}
                </div>

                <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                  <span className="rounded-md bg-amber-50 dark:bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30 px-2 py-0.5 font-bold">
                    {(parseFloat(pr.discount_percentage) * 100).toFixed(0)}% dto.
                  </span>
                  {pr.is_exclusive ? (
                    <span className="rounded-md bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-500/30 px-2 py-0.5 font-semibold">Exclusiva</span>
                  ) : (
                    <span className="rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50 px-2 py-0.5">Combinable</span>
                  )}
                  <span className="rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50 px-2 py-0.5">Prioridad {pr.priority}</span>
                  <span className={`rounded-md px-2 py-0.5 font-mono ${isExhausted
                    ? "bg-purple-50 dark:bg-purple-500/15 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50"
                    }`}>
                    Usos: {pr.current_uses}/{pr.max_quota}
                  </span>
                </div>

                {canWrite && (
                  <div className="flex items-center gap-2 mt-3 pt-2.5 border-t border-slate-200/70 dark:border-slate-700/40">
                    <button
                      type="button"
                      onClick={() => handleTogglePromotion(pr)}
                      className={`flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg border py-1.5 text-xs font-semibold transition ${pr.is_active
                        ? "border-amber-500/40 bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-500/20"
                        : "border-emerald-500/40 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-500/20"
                        }`}
                    >
                      <Power className="h-3.5 w-3.5" />
                      {pr.is_active ? "Pausar" : "Activar"}
                    </button>
                    <button
                      type="button"
                      disabled={!canDelete}
                      onClick={() => {
                        if (canDelete) setConfirmDelete({ type: "promo", id: pr.id, code: pr.code, name: pr.name });
                      }}
                      title={
                        canDelete
                          ? "Eliminar campaña (sin usos registrados)"
                          : "No eliminable: tiene transacciones. Desactívela para pausar."
                      }
                      className={`inline-flex items-center justify-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${canDelete
                        ? "border-rose-500/40 bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-500/20 cursor-pointer"
                        : "border-slate-200 dark:border-slate-700/50 bg-slate-100 dark:bg-slate-800/60 text-slate-400 dark:text-slate-600 opacity-50 cursor-not-allowed"
                        }`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Eliminar
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  </div>);
}
