import * as transporte from "../api/NotificationsWorkspaceTab";
import { useEffect, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";

import { SystemNotificationItem } from "../types/NotificationsWorkspaceTab";
import { NotificationsWorkspaceTabProps } from "../types/NotificationsWorkspaceTab";

export function useNotificationsWorkspaceTab({ onNavigate, refreshKey = false, onUnreadCountChange }: NotificationsWorkspaceTabProps) {
  const [notifications, setNotifications] = useState<SystemNotificationItem[]>([]);

  const [loading, setLoading] = useState(true);

  const [loadError, setLoadError] = useState<string | null>(null);

  const [filterRead, setFilterRead] = useState<"all" | "unread" | "read">("all");

  const [filterCategory, setFilterCategory] = useState<string>("all");

  const [deniedResource, setDeniedResource] = useState<{ title: string; requiredPermission: string } | null>(null);

  const toast = useToast();

  useEffect(() => {
    let active = true;
    setLoading(true);
    transporte.solicitarDatos()
      .then((response) => {
        if (active) {
          setNotifications(response.items || []);
          setLoadError(null);
        }
      })
      .catch((failure: unknown) => {
        if (active) setLoadError(String((failure as { detail?: string }).detail || failure));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [refreshKey]);

  const handleMarkAllRead = async () => {
    try {
      const response = await transporte.solicitarHandleMarkAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      toast.success("Notificaciones leídas", `${response.marked_read_count} notificaciones fueron marcadas como leídas.`);
    } catch (failure: unknown) {
      toast.error("No se pudieron actualizar las notificaciones", String((failure as { detail?: string }).detail || failure));
    }
  };

  const handleToggleRead = async (notification: SystemNotificationItem) => {
    try {
      const read = !notification.read;
      await transporte.solicitarHandleToggleRead({ notification, read });
      setNotifications((prev) => prev.map((item) => item.id === notification.id ? { ...item, read } : item));
    } catch (failure: unknown) {
      toast.error("No se pudo actualizar la notificación", String((failure as { detail?: string }).detail || failure));
    }
  };

  const handleOpenResource = async (notif: SystemNotificationItem) => {
    try {
      const resource = await transporte.solicitarHandleOpenResource({ notif });
      const views: Record<string, string> = { customer: "customers", product: "products", sale: "sales", inventory: "inventory", report_run: "reports", task: "collaboration", approval: "approvals" };
      if (!resource.access_granted) throw new Error("No tienes permiso para abrir este recurso.");
      if (resource.resource_type && onNavigate && views[resource.resource_type]) {
        onNavigate(views[resource.resource_type], resource.resource_id);
      } else if (resource.resource_type && resource.resource_id && onNavigate) {
        sessionStorage.setItem("salesia_record_context", JSON.stringify({ type: resource.resource_type, id: resource.resource_id }));
        onNavigate("records", resource.resource_id);
        window.dispatchEvent(new Event("salesia:open-record"));
      } else {
        toast.info("Recurso autorizado", resource.resource_id ? `Identificador: ${resource.resource_id}` : "La notificación no tiene un recurso navegable asociado.");
      }
    } catch (failure: unknown) {
      setDeniedResource({
        title: notif.title,
        requiredPermission: String((failure as { detail?: string }).detail || "Permiso vigente requerido")
      });
    }
  };

  const filtered = notifications.filter((n) => {
    const matchesRead = filterRead === "all" ? true : filterRead === "unread" ? !n.read : n.read;
    const matchesCat = filterCategory === "all" || n.category === filterCategory;
    return matchesRead && matchesCat;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => { onUnreadCountChange?.(unreadCount); }, [unreadCount, onUnreadCountChange]);
  return { notifications, loading, loadError, filterRead, setFilterRead, filterCategory, setFilterCategory, deniedResource, setDeniedResource, handleMarkAllRead, handleToggleRead, handleOpenResource, filtered, unreadCount };
}
