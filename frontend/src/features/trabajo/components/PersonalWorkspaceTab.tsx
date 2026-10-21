import { Panel1 } from "../sections/PersonalWorkspaceTab/Panel1";
import { Panel2 } from "../sections/PersonalWorkspaceTab/Panel2";
import { Panel3 } from "../sections/PersonalWorkspaceTab/Panel3";
import { Panel4 } from "../sections/PersonalWorkspaceTab/Panel4";
import { Panel5 } from "../sections/PersonalWorkspaceTab/Panel5";
import { SeccionMisTareas } from "../sections/PersonalWorkspaceTab/SeccionMisTareas";
import { SeccionMetaPersonal } from "../sections/PersonalWorkspaceTab/SeccionMetaPersonal";
import { SeccionPedidosEnCurso } from "../sections/PersonalWorkspaceTab/SeccionPedidosEnCurso";
import { SeccionMiCartera } from "../sections/PersonalWorkspaceTab/SeccionMiCartera";
import { SeccionEditarTarea } from "../sections/PersonalWorkspaceTab/SeccionEditarTarea";
import { SeccionEliminarActividad } from "../sections/PersonalWorkspaceTab/SeccionEliminarActividad";
import { Panel12 } from "../sections/PersonalWorkspaceTab/Panel12";
import { Panel13 } from "../sections/PersonalWorkspaceTab/Panel13";
export type { PersonalWorkspaceTabProps } from "../types/PersonalWorkspaceTab";
import { usePersonalWorkspaceTab } from "../hooks/usePersonalWorkspaceTab";
import { AlertCircle, FileText } from "lucide-react";
import { PersonalWorkspaceTabProps } from "../types/PersonalWorkspaceTab";

export function PersonalWorkspaceTab({
  branchId,
  branches = [],
  baseCurrency = "USD",
  onNavigate,
  onOpenOrder,
  onOpenCustomer,
  onOpenResource
}: PersonalWorkspaceTabProps) {
  const { currentUserId, isSupervisorOrAdmin, canReadSales, canReadCustomers, selectedPeriod, tasks, tasksLoading, tasksError, taskFilter, setTaskFilter, taskSearch, setTaskSearch, quickTitle, setQuickTitle, quickPriority, setQuickPriority, quickDueDate, setQuickDueDate, quickDueTime, setQuickDueTime, quickResource, setQuickResource, quickNote, setQuickNote, showNoteTextarea, setShowNoteTextarea, activePopover, setActivePopover, setIsFocused, quickSaving, quickError, setQuickError, highlightedTaskId, linkTab, setLinkTab, linkSearchQuery, setLinkSearchQuery, linkSearchLoading, linkCustomers, linkOrders, titleInputRef, noteTextareaRef, composerRef, taskToEdit, setTaskToEdit, editSaving, taskToDelete, setTaskToDelete, deleteSaving, salesProgress, salesLoading, salesError, orders, ordersLoading, ordersError, ordersScope, setOrdersScope, selectedOrderModal, setSelectedOrderModal, customers, customersLoading, customersError, customersScope, setCustomersScope, selectedCustomerModal, setSelectedCustomerModal, tasksSectionRef, quotaSectionRef, ordersSectionRef, customersSectionRef, applyDateShortcut, formatQuickDateChip, isQuickDateInPast, loadTasks, loadSalesQuota, loadOrders, loadCustomers, shiftPeriod, resetCurrentPeriod, handleToggleTaskStatus, handleCreateQuickTask, handleSaveEditTask, handleConfirmDeleteTask, pendingTasks, overdueTasks, completedTasks, filteredTasks, attainmentNum, progressColor, progressBadge, scrollToSection, isComposerExpanded } = usePersonalWorkspaceTab({ branchId, branches, baseCurrency, onNavigate, onOpenOrder, onOpenCustomer, onOpenResource });
  return (
    <div id="scr-005-personal-workspace" className="space-y-6">


      <Panel1 setTaskFilter={setTaskFilter} scrollToSection={scrollToSection} tasksSectionRef={tasksSectionRef} pendingTasks={pendingTasks} overdueTasks={overdueTasks} ordersSectionRef={ordersSectionRef} orders={orders} quotaSectionRef={quotaSectionRef} salesProgress={salesProgress} baseCurrency={baseCurrency} />

      <section
        ref={composerRef}
        aria-label="Nueva actividad rápida"
        className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 shadow-sm transition-all duration-200"
      >
        <span className="sr-only">Nueva actividad rápida...</span>

        <form onSubmit={handleCreateQuickTask} className="space-y-2">
          <Panel2 titleInputRef={titleInputRef} quickTitle={quickTitle} setIsFocused={setIsFocused} setQuickTitle={setQuickTitle} quickError={quickError} setQuickError={setQuickError} handleCreateQuickTask={handleCreateQuickTask} quickSaving={quickSaving} />

          {quickError && (
            <div className="flex items-center justify-between rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 p-2.5 text-xs text-rose-800 dark:text-rose-300">
              <span className="flex items-center gap-1.5 font-medium">
                <AlertCircle className="h-3.5 w-3.5 text-rose-600 shrink-0" />
                {quickError}
              </span>
              <button
                type="button"
                onClick={() => handleCreateQuickTask()}
                className="font-bold underline hover:text-rose-900 dark:hover:text-rose-200"
              >
                Reintentar
              </button>
            </div>
          )}

          {isComposerExpanded && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 transition-all duration-200">
              <Panel3 quickPriority={quickPriority} activePopover={activePopover} setActivePopover={setActivePopover} setQuickPriority={setQuickPriority} />

              <Panel4 activePopover={activePopover} setActivePopover={setActivePopover} quickDueDate={quickDueDate} formatQuickDateChip={formatQuickDateChip} quickDueTime={quickDueTime} setQuickDueDate={setQuickDueDate} setQuickDueTime={setQuickDueTime} applyDateShortcut={applyDateShortcut} isQuickDateInPast={isQuickDateInPast} />

              {(canReadCustomers || canReadSales) && (
                <Panel5 activePopover={activePopover} setActivePopover={setActivePopover} canReadCustomers={canReadCustomers} canReadSales={canReadSales} setLinkTab={setLinkTab} quickResource={quickResource} setQuickResource={setQuickResource} setLinkSearchQuery={setLinkSearchQuery} linkTab={linkTab} linkSearchQuery={linkSearchQuery} linkSearchLoading={linkSearchLoading} linkCustomers={linkCustomers} linkOrders={linkOrders} />
              )}

              <button
                type="button"
                aria-label="Añadir nota adicional"
                aria-expanded={showNoteTextarea}
                onClick={() => {
                  setShowNoteTextarea(prev => {
                    const next = !prev;
                    if (next) setTimeout(() => noteTextareaRef.current?.focus(), 50);
                    return next;
                  });
                }}
                className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium border transition ${quickNote.trim() || showNoteTextarea
                  ? "border-teal-300 dark:border-teal-700 bg-teal-50/50 dark:bg-teal-950/40 text-teal-800 dark:text-teal-200"
                  : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/80 text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-700"
                  }`}
              >
                <FileText className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
                <span>{quickNote.trim() ? "Con nota" : "Nota"}</span>
                {quickNote.trim() && <span className="h-1.5 w-1.5 rounded-full bg-teal-600 dark:bg-teal-400" />}
              </button>
            </div>
          )}

          {showNoteTextarea && (
            <div className="mt-2.5 pt-2 border-t border-slate-100 dark:border-slate-800/80 space-y-1 transition-all duration-200">
              <textarea
                ref={noteTextareaRef}
                rows={2}
                maxLength={2000}
                value={quickNote}
                onChange={e => setQuickNote(e.target.value)}
                onKeyDown={e => {
                  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                    e.preventDefault();
                    handleCreateQuickTask();
                  }
                }}
                placeholder="Detalles, recordatorios o contexto adicional (Ctrl+Enter para guardar)..."
                aria-label="Nota adicional"
                disabled={quickSaving}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/70 p-2.5 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-teal-600 focus:bg-white dark:focus:bg-slate-900"
              />
              <div className="flex justify-between items-center text-[10px] text-slate-400">
                <span className="hidden sm:inline">Presiona Ctrl+Enter para agregar</span>
                <span className="ml-auto font-mono tabular-nums">{quickNote.length} / 2000</span>
              </div>
            </div>
          )}
        </form>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <SeccionMisTareas tasksSectionRef={tasksSectionRef} tasks={tasks} setTaskFilter={setTaskFilter} taskFilter={taskFilter} pendingTasks={pendingTasks} overdueTasks={overdueTasks} completedTasks={completedTasks} taskSearch={taskSearch} setTaskSearch={setTaskSearch} tasksError={tasksError} loadTasks={loadTasks} currentUserId={currentUserId} tasksLoading={tasksLoading} filteredTasks={filteredTasks} highlightedTaskId={highlightedTaskId} handleToggleTaskStatus={handleToggleTaskStatus} onOpenResource={onOpenResource} setTaskToEdit={setTaskToEdit} setTaskToDelete={setTaskToDelete} />

        <SeccionMetaPersonal quotaSectionRef={quotaSectionRef} shiftPeriod={shiftPeriod} resetCurrentPeriod={resetCurrentPeriod} selectedPeriod={selectedPeriod} canReadSales={canReadSales} salesError={salesError} loadSalesQuota={loadSalesQuota} currentUserId={currentUserId} branchId={branchId} salesLoading={salesLoading} salesProgress={salesProgress} baseCurrency={baseCurrency} progressBadge={progressBadge} attainmentNum={attainmentNum} progressColor={progressColor} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SeccionPedidosEnCurso ordersSectionRef={ordersSectionRef} orders={orders} isSupervisorOrAdmin={isSupervisorOrAdmin} setOrdersScope={setOrdersScope} ordersScope={ordersScope} onNavigate={onNavigate} canReadSales={canReadSales} ordersError={ordersError} loadOrders={loadOrders} currentUserId={currentUserId} branchId={branchId} ordersLoading={ordersLoading} onOpenOrder={onOpenOrder} setSelectedOrderModal={setSelectedOrderModal} baseCurrency={baseCurrency} />

        <SeccionMiCartera customersSectionRef={customersSectionRef} customers={customers} isSupervisorOrAdmin={isSupervisorOrAdmin} setCustomersScope={setCustomersScope} customersScope={customersScope} onNavigate={onNavigate} canReadCustomers={canReadCustomers} customersError={customersError} loadCustomers={loadCustomers} currentUserId={currentUserId} customersLoading={customersLoading} onOpenCustomer={onOpenCustomer} setSelectedCustomerModal={setSelectedCustomerModal} baseCurrency={baseCurrency} />
      </div>

      {taskToEdit && (
        <SeccionEditarTarea setTaskToEdit={setTaskToEdit} handleSaveEditTask={handleSaveEditTask} taskToEdit={taskToEdit} editSaving={editSaving} />
      )}

      {taskToDelete && (
        <SeccionEliminarActividad setTaskToDelete={setTaskToDelete} taskToDelete={taskToDelete} handleConfirmDeleteTask={handleConfirmDeleteTask} deleteSaving={deleteSaving} />
      )}

      {selectedOrderModal && (
        <Panel12 setSelectedOrderModal={setSelectedOrderModal} selectedOrderModal={selectedOrderModal} baseCurrency={baseCurrency} onNavigate={onNavigate} />
      )}

      {selectedCustomerModal && (
        <Panel13 setSelectedCustomerModal={setSelectedCustomerModal} selectedCustomerModal={selectedCustomerModal} baseCurrency={baseCurrency} onNavigate={onNavigate} />
      )}
    </div>
  );
}
