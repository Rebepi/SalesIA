import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { Plus, LoaderCircle } from "lucide-react";

export function Panel2({ titleInputRef, quickTitle, setIsFocused, setQuickTitle, quickError, setQuickError, handleCreateQuickTask, quickSaving }: { titleInputRef: ReturnType<typeof usePersonalWorkspaceTab>["titleInputRef"]; quickTitle: ReturnType<typeof usePersonalWorkspaceTab>["quickTitle"]; setIsFocused: ReturnType<typeof usePersonalWorkspaceTab>["setIsFocused"]; setQuickTitle: ReturnType<typeof usePersonalWorkspaceTab>["setQuickTitle"]; quickError: ReturnType<typeof usePersonalWorkspaceTab>["quickError"]; setQuickError: ReturnType<typeof usePersonalWorkspaceTab>["setQuickError"]; handleCreateQuickTask: ReturnType<typeof usePersonalWorkspaceTab>["handleCreateQuickTask"]; quickSaving: ReturnType<typeof usePersonalWorkspaceTab>["quickSaving"] }) {
  return (<div className="flex items-center gap-2">
    <div className="relative flex-1">
      <input
        ref={titleInputRef}
        type="text"
        maxLength={200}
        value={quickTitle}
        onFocus={() => setIsFocused(true)}
        onChange={e => {
          setQuickTitle(e.target.value);
          if (quickError) setQuickError("");
        }}
        onKeyDown={e => {
          if (e.key === "Enter") {
            e.preventDefault();
            handleCreateQuickTask();
          }
        }}
        placeholder="¿Qué tienes pendiente?"
        aria-label="¿Qué tienes pendiente?"
        disabled={quickSaving}
        className="w-full rounded-xl border border-transparent bg-slate-50/80 dark:bg-slate-800/60 px-3.5 py-2 text-xs font-medium text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 outline-none focus:border-teal-600 dark:focus:border-teal-500 focus:bg-white dark:focus:bg-slate-900 focus:ring-4 focus:ring-teal-100 dark:focus:ring-teal-950/40 disabled:opacity-50 transition"
      />
    </div>

    <div className="flex items-center gap-2 shrink-0">
      <span className="hidden sm:inline-block text-[10px] text-slate-400 dark:text-slate-500 select-none">
        Enter para agregar
      </span>
      <button
        type="submit"
        disabled={!quickTitle.trim() || quickSaving}
        className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold shadow-sm transition ${!quickTitle.trim() || quickSaving
          ? "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-600 opacity-60 cursor-not-allowed"
          : "bg-teal-700 dark:bg-teal-600 text-white hover:bg-teal-800 dark:hover:bg-teal-500 active:scale-95"
          }`}
      >
        {quickSaving ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
        <span>{quickSaving ? "Guardando…" : "Agregar"}</span>
      </button>
    </div>
  </div>);
}
