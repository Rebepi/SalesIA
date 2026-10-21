import * as transporte from "../api/CollaborationWorkspaceTab";
import { useEffect, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { NotificationItem } from "../types/CollaborationWorkspaceTab";
import { PreferenceItem } from "../types/CollaborationWorkspaceTab";
import { TaskItem } from "../types/CollaborationWorkspaceTab";
import { ApprovalItem } from "../types/CollaborationWorkspaceTab";
import { SavedViewItem } from "../types/CollaborationWorkspaceTab";
import { HelpArticleItem } from "../types/CollaborationWorkspaceTab";

export function useCollaborationWorkspaceTab(_props: {
  canApprove?: boolean;
}) {
  const [subTab, setSubTab] = useState<"notifications" | "tasks" | "approvals" | "preferences" | "views" | "help">("notifications");

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  const [unreadCount, setUnreadCount] = useState(0);

  const [priorityFilter, setPriorityFilter] = useState<string>("");

  const [preferences, setPreferences] = useState<PreferenceItem[]>([]);

  const [tasks, setTasks] = useState<TaskItem[]>([]);

  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);

  const [savedViews, setSavedViews] = useState<SavedViewItem[]>([]);

  const [helpArticles, setHelpArticles] = useState<HelpArticleItem[]>([]);

  const [newTaskTitle, setNewTaskTitle] = useState("");

  const [newViewName, setNewViewName] = useState("");

  const [loading, setLoading] = useState(false);

  const toast = useToast();

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const url = priorityFilter ? `/api/v1/notifications?priority=${priorityFilter}` : "/api/v1/notifications";
      const res = await transporte.solicitarLoadNotifications({ url });
      setNotifications(res.items);
      setUnreadCount(res.unread_count);
    } catch (err) {
      toast.error("Error al cargar notificaciones");
    } finally {
      setLoading(false);
    }
  };

  const loadPreferences = async () => {
    try {
      const res = await transporte.solicitarLoadPreferences();
      setPreferences(res.preferences);
    } catch {
      toast.error("Error al cargar preferencias");
    }
  };

  const loadTasks = async () => {
    try {
      const res = await transporte.solicitarLoadTasks();
      setTasks(res.items);
    } catch {
      toast.error("Error al cargar tareas");
    }
  };

  const loadApprovals = async () => {
    try {
      const res = await transporte.solicitarLoadApprovals();
      setApprovals(res.items);
    } catch {
      toast.error("Error al cargar aprobaciones");
    }
  };

  const loadViews = async () => {
    try {
      const res = await transporte.solicitarLoadViews();
      setSavedViews(res.items);
    } catch {
      toast.error("Error al cargar vistas guardadas");
    }
  };

  const loadHelp = async () => {
    try {
      const res = await transporte.solicitarLoadHelp();
      setHelpArticles(res.articles);
    } catch {
      toast.error("Error al cargar ayuda");
    }
  };

  useEffect(() => {
    if (subTab === "notifications") loadNotifications();
    else if (subTab === "preferences") loadPreferences();
    else if (subTab === "tasks") loadTasks();
    else if (subTab === "approvals") loadApprovals();
    else if (subTab === "views") loadViews();
    else if (subTab === "help") loadHelp();
  }, [subTab, priorityFilter]);

  const markRead = async (id: string) => {
    try {
      await transporte.solicitarMarkRead({ id });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
      setUnreadCount(c => Math.max(0, c - 1));
      toast.success("Notificación marcada como leída");
    } catch {
      toast.error("No se pudo marcar como leída");
    }
  };

  const togglePreference = async (pref: PreferenceItem) => {
    if (pref.is_mandatory && pref.enabled) {
      toast.warning("Aviso de seguridad obligatorio", "Las alertas críticas no se pueden silenciar.");
      return;
    }
    try {
      await transporte.solicitarTogglePreference({ pref });
      setPreferences(prev => prev.map(p => p.category === pref.category && p.channel === pref.channel ? { ...p, enabled: !p.enabled } : p));
      toast.success("Preferencia actualizada");
    } catch (err) {
      toast.error("Error al actualizar preferencia");
    }
  };

  const createTask = async () => {
    if (!newTaskTitle.trim()) return;
    try {
      await transporte.solicitarCreateTask({ newTaskTitle });
      setNewTaskTitle("");
      loadTasks();
      toast.success("Tarea creada");
    } catch {
      toast.error("Error al crear tarea");
    }
  };

  const completeTask = async (id: string) => {
    try {
      await transporte.solicitarCompleteTask({ id });
      loadTasks();
      toast.success("Tarea resuelta");
    } catch {
      toast.error("Error al actualizar tarea");
    }
  };

  const decideApproval = async (id: string, decision: "approved" | "rejected", version: number) => {
    try {
      await transporte.solicitarDecideApproval({ id, decision, version });
      loadApprovals();
      toast.success(`Aprobación ${decision === "approved" ? "confirmada" : "rechazada"}`);
    } catch (err) {
      toast.error("Error al resolver aprobación");
    }
  };

  const createView = async () => {
    if (!newViewName.trim()) return;
    try {
      await transporte.solicitarCreateView({ newViewName });
      setNewViewName("");
      loadViews();
      toast.success("Vista guardada");
    } catch {
      toast.error("Error al guardar vista");
    }
  };
  return { subTab, setSubTab, notifications, unreadCount, priorityFilter, setPriorityFilter, preferences, tasks, approvals, savedViews, helpArticles, newTaskTitle, setNewTaskTitle, newViewName, setNewViewName, loading, toast, loadNotifications, loadTasks, loadApprovals, loadViews, loadHelp, markRead, togglePreference, createTask, completeTask, decideApproval, createView };
}
