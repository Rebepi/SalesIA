import * as transporte from "../api/PersonalWorkspaceTab";
import { useState, useEffect, useRef, useCallback } from "react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { PersonalWorkspaceTabProps } from "../types/PersonalWorkspaceTab";
import { PersonalTask } from "../types/PersonalWorkspaceTab";
import { AssignedOrder } from "../types/PersonalWorkspaceTab";
import { AssignedCustomer } from "../types/PersonalWorkspaceTab";
import { SalesProgressData } from "../types/PersonalWorkspaceTab";
import { getBranchMonthPeriod } from "../support/PersonalWorkspaceTab";
import { isDateOverdue } from "../support/PersonalWorkspaceTab";

export function usePersonalWorkspaceTab({ branchId, branches = [] }: PersonalWorkspaceTabProps) {
  const toast = useToast();

  const [currentUserId, setCurrentUserId] = useState("");

  const [currentUserRole, setCurrentUserRole] = useState("");

  const [userPermissions, setUserPermissions] = useState<string[]>([]);

  const isSupervisorOrAdmin = ["company_admin", "manager", "platform_admin"].includes(currentUserRole) ||
    userPermissions.includes("operations:manage") ||
    userPermissions.includes("approvals:manage");

  const canReadSales = userPermissions.length === 0 || userPermissions.includes("sales:read");

  const canReadCustomers = userPermissions.length === 0 || userPermissions.includes("customers:read");

  const activeBranch = branches.find(b => String(b.branch_id) === String(branchId));

  const branchTz = activeBranch?.timezone;

  const [selectedPeriod, setSelectedPeriod] = useState<string>(() => getBranchMonthPeriod(new Date(), branchTz));

  const [tasks, setTasks] = useState<PersonalTask[]>([]);

  const [tasksLoading, setTasksLoading] = useState(false);

  const [tasksError, setTasksError] = useState("");

  const [taskFilter, setTaskFilter] = useState<"pending" | "overdue" | "completed" | "all">("pending");

  const [taskSearch, setTaskSearch] = useState("");

  const [quickTitle, setQuickTitle] = useState("");

  const [quickPriority, setQuickPriority] = useState<"low" | "normal" | "high" | "urgent">("normal");

  const [quickDueDate, setQuickDueDate] = useState("");

  const [quickDueTime, setQuickDueTime] = useState("");

  const [quickResource, setQuickResource] = useState<{ type: "customer" | "order"; id: string; name: string } | null>(null);

  const [quickNote, setQuickNote] = useState("");

  const [showNoteTextarea, setShowNoteTextarea] = useState(false);

  const [activePopover, setActivePopover] = useState<"priority" | "date" | "link" | null>(null);

  const [isFocused, setIsFocused] = useState(false);

  const [quickSaving, setQuickSaving] = useState(false);

  const [quickError, setQuickError] = useState("");

  const [highlightedTaskId, setHighlightedTaskId] = useState<string | null>(null);

  const [linkTab, setLinkTab] = useState<"customer" | "order">("customer");

  const [linkSearchQuery, setLinkSearchQuery] = useState("");

  const [linkSearchLoading, setLinkSearchLoading] = useState(false);

  const [linkCustomers, setLinkCustomers] = useState<Array<{ id: string; legal_name: string; doc_number: string }>>([]);

  const [linkOrders, setLinkOrders] = useState<Array<{ order_id: string; order_number: string; customer_name?: string }>>([]);

  const titleInputRef = useRef<HTMLInputElement>(null);

  const noteTextareaRef = useRef<HTMLTextAreaElement>(null);

  const composerRef = useRef<HTMLDivElement>(null);

  const [taskToEdit, setTaskToEdit] = useState<PersonalTask | null>(null);

  const [editSaving, setEditSaving] = useState(false);

  const [taskToDelete, setTaskToDelete] = useState<PersonalTask | null>(null);

  const [deleteSaving, setDeleteSaving] = useState(false);

  const [salesProgress, setSalesProgress] = useState<SalesProgressData | null>(null);

  const [salesLoading, setSalesLoading] = useState(false);

  const [salesError, setSalesError] = useState("");

  const [orders, setOrders] = useState<AssignedOrder[]>([]);

  const [ordersLoading, setOrdersLoading] = useState(false);

  const [ordersError, setOrdersError] = useState("");

  const [ordersScope, setOrdersScope] = useState<"mine" | "all">("mine");

  const [selectedOrderModal, setSelectedOrderModal] = useState<AssignedOrder | null>(null);

  const [customers, setCustomers] = useState<AssignedCustomer[]>([]);

  const [customersLoading, setCustomersLoading] = useState(false);

  const [customersError, setCustomersError] = useState("");

  const [customersScope, setCustomersScope] = useState<"mine" | "all">("mine");

  const [selectedCustomerModal, setSelectedCustomerModal] = useState<AssignedCustomer | null>(null);

  const [refreshingAll, setRefreshingAll] = useState(false);

  const tasksSectionRef = useRef<HTMLElement>(null);

  const quotaSectionRef = useRef<HTMLElement>(null);

  const ordersSectionRef = useRef<HTMLElement>(null);

  const customersSectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    let isMounted = true;
    apiClient.getMe().then(profile => {
      if (!isMounted) return;
      setCurrentUserId(profile.user_id);
      setCurrentUserRole(profile.role);
      setUserPermissions(profile.permissions || []);
    }).catch(() => { });
    return () => { isMounted = false; };
  }, []);

  const getLocalDateStr = useCallback((date: Date): string => {
    try {
      if (branchTz) {
        const formatter = new Intl.DateTimeFormat("en-CA", {
          timeZone: branchTz,
          year: "numeric",
          month: "2-digit",
          day: "2-digit"
        });
        return formatter.format(date);
      }
    } catch { }
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }, [branchTz]);

  function applyDateShortcut(type: "today" | "tomorrow" | "friday" | "next_week") {
    const now = new Date();
    if (type === "today") {
      setQuickDueDate(getLocalDateStr(now));
    } else if (type === "tomorrow") {
      now.setDate(now.getDate() + 1);
      setQuickDueDate(getLocalDateStr(now));
    } else if (type === "friday") {
      const day = now.getDay();
      let diff = 5 - day;
      if (diff <= 0) diff += 7;
      now.setDate(now.getDate() + diff);
      setQuickDueDate(getLocalDateStr(now));
    } else if (type === "next_week") {
      const day = now.getDay();
      let diff = 1 - day;
      if (diff <= 0) diff += 7;
      now.setDate(now.getDate() + diff);
      setQuickDueDate(getLocalDateStr(now));
    }
    setActivePopover(null);
  }

  function formatQuickDateChip(dateStr: string, timeStr?: string): string {
    if (!dateStr) return "Fecha";
    try {
      const todayStr = getLocalDateStr(new Date());
      const tmrw = new Date();
      tmrw.setDate(tmrw.getDate() + 1);
      const tmrwStr = getLocalDateStr(tmrw);
      let base = "";
      if (dateStr === todayStr) {
        base = "Hoy";
      } else if (dateStr === tmrwStr) {
        base = "Mañana";
      } else {
        const [y, m, d] = dateStr.split("-").map(Number);
        const obj = new Date(y, m - 1, d);
        base = new Intl.DateTimeFormat("es-PE", {
          weekday: "short",
          day: "numeric",
          month: "short"
        }).format(obj);
      }
      return timeStr ? `${base} ${timeStr}` : base;
    } catch {
      return dateStr;
    }
  }

  function isQuickDateInPast(dateStr: string, timeStr?: string): boolean {
    if (!dateStr) return false;
    try {
      const [y, m, d] = dateStr.split("-").map(Number);
      const target = new Date(y, m - 1, d);
      if (timeStr) {
        const [hh, mm] = timeStr.split(":").map(Number);
        target.setHours(hh || 0, mm || 0, 0, 0);
      } else {
        target.setHours(23, 59, 59, 999);
      }
      return target.getTime() < Date.now();
    } catch {
      return false;
    }
  }

  useEffect(() => {
    if (activePopover !== "link") return;
    const timer = setTimeout(async () => {
      setLinkSearchLoading(true);
      try {
        if (linkTab === "customer" && canReadCustomers) {
          const q = linkSearchQuery.trim();
          const param = q ? `&search=${encodeURIComponent(q)}` : "";
          const res = await transporte.solicitarDatos({ param });
          setLinkCustomers(res.items || []);
        } else if (linkTab === "order" && canReadSales) {
          const q = linkSearchQuery.trim();
          const param = q ? `&order_number=${encodeURIComponent(q)}` : "";
          const branchParam = branchId ? `&branch_id=${branchId}` : "";
          const res = await transporte.solicitarDatos2({ param, branchParam });
          setLinkOrders(res || []);
        }
      } catch {
        if (linkTab === "customer") setLinkCustomers([]);
        else setLinkOrders([]);
      } finally {
        setLinkSearchLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [activePopover, linkTab, linkSearchQuery, canReadCustomers, canReadSales, branchId]);

  useEffect(() => {
    function handleGlobalClick(e: MouseEvent) {
      if (composerRef.current && !composerRef.current.contains(e.target as Node)) {
        setActivePopover(null);
        if (!quickTitle.trim() && !quickNote.trim() && !quickDueDate && !quickResource) {
          setIsFocused(false);
          setShowNoteTextarea(false);
        }
      }
    }
    function handleGlobalKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        if (activePopover) {
          setActivePopover(null);
        } else if (!quickTitle.trim() && !quickNote.trim() && !quickDueDate && !quickResource) {
          setIsFocused(false);
          setShowNoteTextarea(false);
          titleInputRef.current?.blur();
        }
      }
    }
    document.addEventListener("mousedown", handleGlobalClick);
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleGlobalClick);
      window.removeEventListener("keydown", handleGlobalKeyDown);
    };
  }, [activePopover, quickTitle, quickNote, quickDueDate, quickResource]);

  const loadTasks = useCallback(async (userId: string, search = "") => {
    if (!userId) return;
    setTasksLoading(true);
    setTasksError("");
    try {
      const searchParam = search ? `&search=${encodeURIComponent(search)}` : "";
      const res = await transporte.solicitarDatos3({ userId, searchParam });
      setTasks(res.items || []);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar las tareas.";
      setTasksError(msg);
    } finally {
      setTasksLoading(false);
    }
  }, []);

  const loadSalesQuota = useCallback(async (userId: string, period: string, bId?: string) => {
    if (!canReadSales) return;
    setSalesLoading(true);
    setSalesError("");
    try {
      const branchParam = bId ? `&branch_id=${bId}` : "";
      const res = await transporte.solicitarDatos4({ period, branchParam });

      const rep = (res.items || []).find(item => item.user_id === userId);
      if (!rep) {
        setSalesProgress({
          isRepresentative: false,
          hasQuota: false,
          currentSales: 0,
          grossSales: 0,
          refunds: 0,
          netSales: 0,
          quota: 0,
          attainment: null,
          gap: 0
        });
      } else {
        const quotaVal = rep.target_quota !== null && rep.target_quota !== undefined ? parseFloat(String(rep.target_quota)) : 0;
        const netVal = rep.net_sales !== undefined ? parseFloat(String(rep.net_sales)) : parseFloat(String(rep.current_sales || 0));
        const grossVal = rep.gross_sales !== undefined ? parseFloat(String(rep.gross_sales)) : netVal;
        const refundsVal = rep.refunds !== undefined ? parseFloat(String(rep.refunds)) : Math.max(0, grossVal - netVal);
        const attainmentVal = rep.quota_attainment_pct !== null && rep.quota_attainment_pct !== undefined ? parseFloat(String(rep.quota_attainment_pct)) : (quotaVal > 0 ? (netVal / quotaVal) * 100 : null);
        const gapVal = netVal - quotaVal;

        setSalesProgress({
          isRepresentative: true,
          hasQuota: quotaVal > 0,
          currentSales: netVal,
          grossSales: grossVal,
          refunds: refundsVal,
          netSales: netVal,
          quota: quotaVal,
          attainment: attainmentVal,
          gap: gapVal
        });
      }
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar la meta de ventas.";
      setSalesError(msg);
    } finally {
      setSalesLoading(false);
    }
  }, [canReadSales]);

  const loadOrders = useCallback(async (userId: string, scope: "mine" | "all", bId?: string) => {
    if (!canReadSales) return;
    setOrdersLoading(true);
    setOrdersError("");
    try {
      const params = new URLSearchParams();
      params.set("active_only", "true");
      params.set("limit", "10");
      if (scope === "mine" && userId) {
        params.set("sales_rep_id", userId);
      }
      if (bId) {
        params.set("branch_id", bId);
      }
      const res = await transporte.solicitarDatos5({ params });
      setOrders(res || []);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar pedidos en curso.";
      setOrdersError(msg);
    } finally {
      setOrdersLoading(false);
    }
  }, [canReadSales]);

  const loadCustomers = useCallback(async (userId: string, scope: "mine" | "all") => {
    if (!canReadCustomers) return;
    setCustomersLoading(true);
    setCustomersError("");
    try {
      const params = new URLSearchParams();
      params.set("limit", "10");
      if (scope === "mine" && userId) {
        params.set("sales_rep_id", userId);
      }
      const res = await transporte.solicitarDatos6({ params });
      setCustomers(res.items || []);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al consultar la cartera de clientes.";
      setCustomersError(msg);
    } finally {
      setCustomersLoading(false);
    }
  }, [canReadCustomers]);

  const refreshAll = useCallback(async () => {
    if (!currentUserId) return;
    setRefreshingAll(true);
    await Promise.allSettled([
      loadTasks(currentUserId, taskSearch),
      loadSalesQuota(currentUserId, selectedPeriod, branchId),
      loadOrders(currentUserId, ordersScope, branchId),
      loadCustomers(currentUserId, customersScope)
    ]);
    setRefreshingAll(false);
  }, [currentUserId, taskSearch, selectedPeriod, branchId, ordersScope, customersScope, loadTasks, loadSalesQuota, loadOrders, loadCustomers]);

  useEffect(() => {
    if (currentUserId) {
      loadTasks(currentUserId, taskSearch);
    }
  }, [currentUserId, taskSearch, loadTasks]);

  useEffect(() => {
    if (currentUserId) {
      loadSalesQuota(currentUserId, selectedPeriod, branchId);
    }
  }, [currentUserId, selectedPeriod, branchId, loadSalesQuota]);

  useEffect(() => {
    if (currentUserId) {
      loadOrders(currentUserId, ordersScope, branchId);
    }
  }, [currentUserId, ordersScope, branchId, loadOrders]);

  useEffect(() => {
    if (currentUserId) {
      loadCustomers(currentUserId, customersScope);
    }
  }, [currentUserId, customersScope, loadCustomers]);

  useEffect(() => {
    const timer = setInterval(() => {
      if (document.hidden) return;
      if (currentUserId && !refreshingAll) {
        refreshAll();
      }
    }, 90000);
    return () => clearInterval(timer);
  }, [currentUserId, refreshingAll, refreshAll]);

  function shiftPeriod(delta: number) {
    try {
      const [year, month] = selectedPeriod.split("-").map(Number);
      const target = new Date(year, month - 1 + delta, 1);
      setSelectedPeriod(getBranchMonthPeriod(target, branchTz));
    } catch {
      setSelectedPeriod(getBranchMonthPeriod(new Date(), branchTz));
    }
  }

  function resetCurrentPeriod() {
    setSelectedPeriod(getBranchMonthPeriod(new Date(), branchTz));
  }

  async function handleToggleTaskStatus(task: PersonalTask) {
    const nextStatus = task.status === "completed" ? "pending" : "completed";
    setTasks(prev => prev.map(t => t.id === task.id ? { ...t, status: nextStatus } : t));
    try {
      await transporte.solicitarHandleToggleTaskStatus({ task, nextStatus });
      toast.success(nextStatus === "completed" ? "Tarea completada" : "Tarea reabierta", task.title);
    } catch (err: unknown) {
      setTasks(prev => prev.map(t => t.id === task.id ? { ...t, status: task.status } : t));
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al actualizar estado.";
      toast.error("No se pudo cambiar el estado", msg);
    }
  }

  async function handleCreateQuickTask(e?: React.FormEvent) {
    if (e) e.preventDefault();
    const cleanTitle = quickTitle.trim();
    if (!cleanTitle || !currentUserId || quickSaving) return;

    setQuickSaving(true);
    setQuickError("");
    try {
      let fullDueDate: string | undefined = undefined;
      if (quickDueDate) {
        const timePart = quickDueTime ? `${quickDueTime}:00` : "23:59:59";
        fullDueDate = `${quickDueDate}T${timePart}`;
      }

      const payload: {
        title: string;
        assignee_id: string;
        priority: "low" | "normal" | "high" | "urgent";
        description?: string;
        due_date?: string;
        resource_type?: string;
        resource_id?: string;
      } = {
        title: cleanTitle,
        assignee_id: currentUserId,
        priority: quickPriority
      };

      if (quickNote.trim()) payload.description = quickNote.trim();
      if (fullDueDate) payload.due_date = fullDueDate;
      if (quickResource) {
        payload.resource_type = quickResource.type;
        payload.resource_id = quickResource.id;
      }

      const res = await transporte.solicitarHandleCreateQuickTask({ payload });

      const newTaskWithDetails: PersonalTask = {
        ...res,
        resource_name: quickResource ? quickResource.name : res.resource_name
      };

      setTasks(prev => [newTaskWithDetails, ...prev]);
      setHighlightedTaskId(res.id);
      setTimeout(() => setHighlightedTaskId(null), 2500);

      setQuickTitle("");
      setQuickNote("");
      setQuickPriority("normal");
      setQuickDueDate("");
      setQuickDueTime("");
      setQuickResource(null);
      setShowNoteTextarea(false);
      setActivePopover(null);
      setQuickError("");

      titleInputRef.current?.focus();
      toast.success("Tarea registrada", "La actividad se agregó exitosamente.");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err
        ? String((err as { detail: unknown }).detail)
        : "Error al registrar la actividad. Comprueba la conexión.";
      setQuickError(msg);
      toast.error("No se pudo registrar la tarea", msg);
    } finally {
      setQuickSaving(false);
    }
  }

  async function handleSaveEditTask(e: React.FormEvent) {
    e.preventDefault();
    if (!taskToEdit || editSaving) return;
    setEditSaving(true);
    try {
      const updated = await transporte.solicitarHandleSaveEditTask({ taskToEdit });
      setTasks(prev => prev.map(t => t.id === updated.id ? updated : t));
      toast.success("Tarea modificada", "Los cambios se guardaron correctamente.");
      setTaskToEdit(null);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al modificar la tarea.";
      toast.error("No se pudo actualizar", msg);
    } finally {
      setEditSaving(false);
    }
  }

  async function handleConfirmDeleteTask() {
    if (!taskToDelete || deleteSaving) return;
    setDeleteSaving(true);
    try {
      await transporte.solicitarHandleConfirmDeleteTask({ taskToDelete });
      setTasks(prev => prev.filter(t => t.id !== taskToDelete.id));
      toast.success("Tarea eliminada", "La actividad fue descartada.");
      setTaskToDelete(null);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "No autorizado o error al eliminar.";
      toast.error("No se pudo eliminar", msg);
    } finally {
      setDeleteSaving(false);
    }
  }

  const pendingTasks = tasks.filter(t => t.status === "pending" || t.status === "in_progress");

  const overdueTasks = tasks.filter(t => (t.status === "pending" || t.status === "in_progress") && isDateOverdue(t.due_date));

  const completedTasks = tasks.filter(t => t.status === "completed");

  const filteredTasks = tasks.filter(t => {
    if (taskFilter === "pending") return t.status === "pending" || t.status === "in_progress";
    if (taskFilter === "overdue") return (t.status === "pending" || t.status === "in_progress") && isDateOverdue(t.due_date);
    if (taskFilter === "completed") return t.status === "completed";
    return true;
  });

  const attainmentNum = salesProgress?.attainment !== null && salesProgress?.attainment !== undefined ? Math.round(salesProgress.attainment) : null;

  const progressColor = attainmentNum === null ? "bg-slate-300" : attainmentNum < 50 ? "bg-rose-500" : attainmentNum < 100 ? "bg-amber-500" : "bg-emerald-500";

  const progressBadge = attainmentNum === null ? "bg-slate-100 text-slate-700" : attainmentNum < 50 ? "bg-rose-100 text-rose-800" : attainmentNum < 100 ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800";

  function scrollToSection(ref: React.RefObject<HTMLElement>) {
    ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const isComposerExpanded = isFocused ||
    quickTitle.length > 0 ||
    quickPriority !== "normal" ||
    Boolean(quickDueDate) ||
    Boolean(quickResource) ||
    showNoteTextarea ||
    activePopover !== null;
  return { currentUserId, isSupervisorOrAdmin, canReadSales, canReadCustomers, selectedPeriod, tasks, tasksLoading, tasksError, taskFilter, setTaskFilter, taskSearch, setTaskSearch, quickTitle, setQuickTitle, quickPriority, setQuickPriority, quickDueDate, setQuickDueDate, quickDueTime, setQuickDueTime, quickResource, setQuickResource, quickNote, setQuickNote, showNoteTextarea, setShowNoteTextarea, activePopover, setActivePopover, setIsFocused, quickSaving, quickError, setQuickError, highlightedTaskId, linkTab, setLinkTab, linkSearchQuery, setLinkSearchQuery, linkSearchLoading, linkCustomers, linkOrders, titleInputRef, noteTextareaRef, composerRef, taskToEdit, setTaskToEdit, editSaving, taskToDelete, setTaskToDelete, deleteSaving, salesProgress, salesLoading, salesError, orders, ordersLoading, ordersError, ordersScope, setOrdersScope, selectedOrderModal, setSelectedOrderModal, customers, customersLoading, customersError, customersScope, setCustomersScope, selectedCustomerModal, setSelectedCustomerModal, tasksSectionRef, quotaSectionRef, ordersSectionRef, customersSectionRef, applyDateShortcut, formatQuickDateChip, isQuickDateInPast, loadTasks, loadSalesQuota, loadOrders, loadCustomers, shiftPeriod, resetCurrentPeriod, handleToggleTaskStatus, handleCreateQuickTask, handleSaveEditTask, handleConfirmDeleteTask, pendingTasks, overdueTasks, completedTasks, filteredTasks, attainmentNum, progressColor, progressBadge, scrollToSection, isComposerExpanded };
}
