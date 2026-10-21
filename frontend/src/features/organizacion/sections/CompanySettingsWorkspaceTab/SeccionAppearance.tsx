import type { useCompanySettingsWorkspaceTab } from "../../hooks/useCompanySettingsWorkspaceTab";
import { setToastPosition, TOAST_POSITIONS, type ToastPosition } from "../../../../ui/toast/preferences";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Check, Loader2, X } from "lucide-react";
import { setStoredThemePreference, setStoredDensityPreference, ThemeMode, DensityMode } from "../../../../ui/tokens";
import { setStoredMotionPreference } from "../../../../ui/motion";
import { setAccessibleTables as persistAccessibleTables, setContrastMode as persistContrastMode, setDefaultPageSize as persistDefaultPageSize, setFontScale as persistFontScale, setSidebarMode as persistSidebarMode, type ContrastMode, type FontScale, type SidebarMode } from "../../../../ui/preferences";

export function SeccionAppearance({ appearanceSaveState, uiTheme, setUiTheme, persistPreferences, inputClass, uiDensity, setUiDensity, reducedMotion, setReducedMotion, fontScale, setFontScale, contrastMode, setContrastMode, defaultPageSize, setDefaultPageSize, sidebarMode, setSidebarMode, toastPosition, setSelectedToastPosition, accessibleTables, setAccessibleTables }: { appearanceSaveState: ReturnType<typeof useCompanySettingsWorkspaceTab>["appearanceSaveState"]; uiTheme: ReturnType<typeof useCompanySettingsWorkspaceTab>["uiTheme"]; setUiTheme: ReturnType<typeof useCompanySettingsWorkspaceTab>["setUiTheme"]; persistPreferences: ReturnType<typeof useCompanySettingsWorkspaceTab>["persistPreferences"]; inputClass: ReturnType<typeof useCompanySettingsWorkspaceTab>["inputClass"]; uiDensity: ReturnType<typeof useCompanySettingsWorkspaceTab>["uiDensity"]; setUiDensity: ReturnType<typeof useCompanySettingsWorkspaceTab>["setUiDensity"]; reducedMotion: ReturnType<typeof useCompanySettingsWorkspaceTab>["reducedMotion"]; setReducedMotion: ReturnType<typeof useCompanySettingsWorkspaceTab>["setReducedMotion"]; fontScale: ReturnType<typeof useCompanySettingsWorkspaceTab>["fontScale"]; setFontScale: ReturnType<typeof useCompanySettingsWorkspaceTab>["setFontScale"]; contrastMode: ReturnType<typeof useCompanySettingsWorkspaceTab>["contrastMode"]; setContrastMode: ReturnType<typeof useCompanySettingsWorkspaceTab>["setContrastMode"]; defaultPageSize: ReturnType<typeof useCompanySettingsWorkspaceTab>["defaultPageSize"]; setDefaultPageSize: ReturnType<typeof useCompanySettingsWorkspaceTab>["setDefaultPageSize"]; sidebarMode: ReturnType<typeof useCompanySettingsWorkspaceTab>["sidebarMode"]; setSidebarMode: ReturnType<typeof useCompanySettingsWorkspaceTab>["setSidebarMode"]; toastPosition: ReturnType<typeof useCompanySettingsWorkspaceTab>["toastPosition"]; setSelectedToastPosition: ReturnType<typeof useCompanySettingsWorkspaceTab>["setSelectedToastPosition"]; accessibleTables: ReturnType<typeof useCompanySettingsWorkspaceTab>["accessibleTables"]; setAccessibleTables: ReturnType<typeof useCompanySettingsWorkspaceTab>["setAccessibleTables"] }) {
  return (<section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
    <div className="flex justify-end">
      <div className="min-w-28 text-right text-xs font-medium" aria-live="polite" aria-atomic="true">
        {appearanceSaveState === "saving" && <span className="inline-flex items-center gap-1.5 text-slate-500"><Loader2 className="h-3.5 w-3.5 animate-spin" />Guardando…</span>}
        {appearanceSaveState === "saved" && <span className="inline-flex items-center gap-1.5 text-emerald-700"><Check className="h-3.5 w-3.5" />Guardado</span>}
        {appearanceSaveState === "error" && <span className="inline-flex items-center gap-1.5 text-rose-700"><X className="h-3.5 w-3.5" />Sin sincronizar</span>}
      </div>
    </div>

    <div className="grid gap-6 sm:grid-cols-3">
      <div>
        <label htmlFor="cfg-theme-select" className="block text-xs font-semibold text-slate-700">
          Tema Visual
        </label>
        <CustomSelect
          id="cfg-theme-select"
          value={uiTheme}
          onChange={(e) => {
            const next = e.target.value as ThemeMode;
            setUiTheme(next);
            setStoredThemePreference(next);
            void persistPreferences({ ui_theme: next });
          }}
          className={inputClass}
        >
          <option value="light">Claro (Light)</option>
          <option value="dark">Oscuro (Dark)</option>
        </CustomSelect>
        <p className="mt-1.5 text-[11px] text-slate-400">Alterna entre esquema luminoso u oscuro.</p>
      </div>

      <div>
        <label htmlFor="cfg-density-select" className="block text-xs font-semibold text-slate-700">
          Densidad de Interfaz
        </label>
        <CustomSelect
          id="cfg-density-select"
          value={uiDensity}
          onChange={(e) => {
            const next = e.target.value as DensityMode;
            setUiDensity(next);
            setStoredDensityPreference(next);
            void persistPreferences({ ui_density: next });
          }}
          className={inputClass}
        >
          <option value="comfortable">Cómoda (espaciado estándar)</option>
          <option value="compact">Compacta (tablas y filas densas)</option>
        </CustomSelect>
        <p className="mt-1.5 text-[11px] text-slate-400">Controla el espaciado vertical de tablas y paneles.</p>
      </div>

      <div>
        <label htmlFor="cfg-motion-select" className="block text-xs font-semibold text-slate-700">
          Movimiento y Animaciones
        </label>
        <CustomSelect
          id="cfg-motion-select"
          value={reducedMotion ? "reduced" : "normal"}
          onChange={(e) => {
            const isReduced = e.target.value === "reduced";
            setReducedMotion(isReduced);
            setStoredMotionPreference(isReduced ? "reduced" : "normal");
            void persistPreferences({ reduced_motion: isReduced });
          }}
          className={inputClass}
        >
          <option value="normal">Normal (transiciones y animaciones fluidas)</option>
          <option value="reduced">Reducido (sin animaciones para mayor fluidez)</option>
        </CustomSelect>
        <p className="mt-1.5 text-[11px] text-slate-400">Recomendado para accesibilidad o equipos con recursos limitados.</p>
      </div>
    </div>

    <div className="grid gap-6 border-t border-slate-100 pt-5 sm:grid-cols-2 lg:grid-cols-4">
      <div>
        <label htmlFor="cfg-font-scale" className="block text-xs font-semibold text-slate-700">Tamaño del texto</label>
        <CustomSelect id="cfg-font-scale" value={fontScale} className={inputClass} onChange={(event) => {
          const next = event.target.value as FontScale;
          setFontScale(next);
          persistFontScale(next);
          void persistPreferences({ font_scale: next });
        }}>
          <option value="small">Pequeño</option>
          <option value="standard">Estándar</option>
          <option value="large">Grande</option>
        </CustomSelect>
        <p className="mt-1.5 text-[11px] text-slate-400">Ajusta la escala de texto en todo el sistema.</p>
      </div>

      <div>
        <label htmlFor="cfg-contrast" className="block text-xs font-semibold text-slate-700">Contraste</label>
        <CustomSelect id="cfg-contrast" value={contrastMode} className={inputClass} onChange={(event) => {
          const next = event.target.value as ContrastMode;
          setContrastMode(next);
          persistContrastMode(next);
          void persistPreferences({ contrast_mode: next });
        }}>
          <option value="standard">Estándar</option>
          <option value="high">Alto contraste</option>
        </CustomSelect>
        <p className="mt-1.5 text-[11px] text-slate-400">Refuerza bordes, foco y legibilidad del contenido.</p>
      </div>

      <div>
        <label htmlFor="cfg-page-size" className="block text-xs font-semibold text-slate-700">Filas predeterminadas</label>
        <CustomSelect id="cfg-page-size" value={defaultPageSize} className={inputClass} onChange={(event) => {
          const next = Number(event.target.value);
          setDefaultPageSize(next);
          persistDefaultPageSize(next);
          void persistPreferences({ default_page_size: next });
        }}>
          {[10, 25, 50, 100].map((size) => <option key={size} value={size}>{size} filas</option>)}
        </CustomSelect>
        <p className="mt-1.5 text-[11px] text-slate-400">Se aplica a tablas nuevas y a las que estén abiertas.</p>
      </div>

      <div>
        <label htmlFor="cfg-sidebar-mode" className="block text-xs font-semibold text-slate-700">Menú lateral</label>
        <CustomSelect id="cfg-sidebar-mode" value={sidebarMode} className={inputClass} onChange={(event) => {
          const next = event.target.value as SidebarMode;
          setSidebarMode(next);
          persistSidebarMode(next);
          void persistPreferences({ sidebar_mode: next });
        }}>
          <option value="expanded">Expandido</option>
          <option value="collapsed">Colapsado</option>
        </CustomSelect>
        <p className="mt-1.5 text-[11px] text-slate-400">Cambia inmediatamente el ancho de la navegación.</p>
      </div>
    </div>

    <div className="space-y-2 border-t border-slate-100 pt-5">
      <label htmlFor="cfg-toast-position" className="block text-xs font-semibold text-slate-700">Posición de las notificaciones</label>
      <CustomSelect id="cfg-toast-position" value={toastPosition} className={`${inputClass} sm:max-w-sm`} onChange={event => {
        const next = event.target.value as ToastPosition;
        setSelectedToastPosition(next);
        setToastPosition(next);
        void persistPreferences({ toast_position: next });
      }}>
        {TOAST_POSITIONS.map(position => <option key={position.value} value={position.value}>{position.label}</option>)}
      </CustomSelect>
      <p className="text-xs text-slate-500">Se aplica y se guarda automáticamente en este navegador. Por defecto: abajo a la derecha.</p>
    </div>

    <div className="border-t border-slate-100 pt-5">
      <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700 transition hover:border-teal-300">
        <input
          type="checkbox"
          checked={accessibleTables}
          onChange={(event) => {
            const enabled = event.target.checked;
            setAccessibleTables(enabled);
            persistAccessibleTables(enabled);
            void persistPreferences({ accessible_tables: enabled });
          }}
          className="mt-0.5 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
        />
        <span>
          <strong className="block font-semibold text-slate-900">Tablas accesibles para lectores de pantalla</strong>
          <span className="mt-0.5 block text-xs text-slate-500">Muestra tablas de datos equivalentes debajo de los gráficos de analítica.</span>
        </span>
      </label>
    </div>

  </section>);
}
