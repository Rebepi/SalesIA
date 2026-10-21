import { Seccionundefined } from "../sections/NotificationsWorkspaceTab/Seccionundefined";
export type { SystemNotificationItem } from "../types/NotificationsWorkspaceTab";
export type { NotificationsWorkspaceTabProps } from "../types/NotificationsWorkspaceTab";
import { useNotificationsWorkspaceTab } from "../hooks/useNotificationsWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { CheckCheck, Lock } from "lucide-react";
import { NotificationsWorkspaceTabProps } from "../types/NotificationsWorkspaceTab";

export function NotificationsWorkspaceTab({ canWrite: _canWrite = true, userPermissions: _userPermissions = [], onNavigate, compact = false, refreshKey = false, onUnreadCountChange }: NotificationsWorkspaceTabProps) {
  const { notifications, loading, loadError, filterRead, setFilterRead, filterCategory, setFilterCategory, deniedResource, setDeniedResource, handleMarkAllRead, handleToggleRead, handleOpenResource, filtered, unreadCount } = useNotificationsWorkspaceTab({ canWrite: _canWrite, userPermissions: _userPermissions, onNavigate, compact, refreshKey, onUnreadCountChange });
  return (
    <div id="scr-043-notifications-workspace" data-testid="scr-043-notifications-workspace" className={compact ? "notification-inbox space-y-4" : "space-y-6"}>
      <NavbarSectionHeader view="notifications" inline={compact} className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            {!compact && <span className="rounded-md bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700">SCR-043</span>}
            <h2 id="notification-inbox-title" className="text-lg font-bold text-slate-900">{compact ? "Notificaciones" : "Centro de Notificaciones del Sistema"}</h2>
            {unreadCount > 0 && (
              <span className="rounded-full bg-teal-600 px-2 py-0.5 text-xs font-bold text-white">
                {unreadCount} sin leer
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Tus novedades y avisos, en un solo lugar.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={unreadCount === 0 || loading}
            onClick={handleMarkAllRead}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            <CheckCheck className="h-4 w-4" />
            Marcar todas como leídas
          </button>
        </div>
      </NavbarSectionHeader>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">Cargando notificaciones...</div>}
      {loadError && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{loadError}</div>}

      {deniedResource && (
        <div role="alert" className="flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-amber-900 shadow-sm">
          <Lock className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
          <div className="flex-1">
            <h4 className="font-bold">Acceso no autorizado: tus permisos para este recurso han cambiado</h4>
            <p className="mt-1 text-xs leading-relaxed">
              El servidor rechazó el acceso al recurso enlazado a «{deniedResource.title}»: <span className="font-semibold">{deniedResource.requiredPermission}</span>
            </p>
          </div>
          <button onClick={() => setDeniedResource(null)} className="text-amber-700 hover:text-amber-900">
            Cerrar
          </button>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap gap-2">
          {(["all", "unread", "read"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setFilterRead(r)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${filterRead === r
                ? "bg-teal-700 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
            >
              {r === "all" ? "Todas" : r === "unread" ? "No leídas" : "Leídas"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="filter-notif-category" className="text-xs font-semibold text-slate-600">Categoría:</label>
          <CustomSelect
            id="filter-notif-category"
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-700"
          >
            <option value="all">Todas las categorías</option>
            {[...new Set(notifications.map((item) => item.category))].map((category) => <option key={category} value={category}>{category}</option>)}
          </CustomSelect>
        </div>
      </div>

      <Seccionundefined filtered={filtered} handleOpenResource={handleOpenResource} handleToggleRead={handleToggleRead} loading={loading} />
    </div>
  );
}
