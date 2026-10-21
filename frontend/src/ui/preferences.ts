export type FontScale = "small" | "standard" | "large";
export type ContrastMode = "standard" | "high";
export type SidebarMode = "expanded" | "collapsed";

export interface RemoteUiPreferences {
  font_scale?: string;
  contrast_mode?: string;
  default_page_size?: number;
  sidebar_mode?: string;
  accessible_tables?: boolean;
}

export const UI_PREFERENCES_EVENT = "salesia-ui-preferences-changed";

const FONT_SCALE_KEY = "salesia_font_scale";
const CONTRAST_KEY = "salesia_contrast_mode";
const PAGE_SIZE_KEY = "salesia_default_page_size";
const SIDEBAR_KEY = "salesia_sidebar_mode";
const ACCESSIBLE_TABLES_KEY = "salesia_accessible_tables";

function read(key: string): string | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string): void {
  try {
    if (typeof window !== "undefined") window.localStorage.setItem(key, value);
  } catch {
    return;
  }
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent(UI_PREFERENCES_EVENT, { detail: { key, value } }));
}

export function getFontScale(): FontScale {
  const value = read(FONT_SCALE_KEY);
  return value === "small" || value === "large" ? value : "standard";
}

export function setFontScale(value: FontScale): void {
  write(FONT_SCALE_KEY, value);
  if (typeof document !== "undefined") document.documentElement.dataset.fontScale = value;
}

export function getContrastMode(): ContrastMode {
  return read(CONTRAST_KEY) === "high" ? "high" : "standard";
}

export function setContrastMode(value: ContrastMode): void {
  write(CONTRAST_KEY, value);
  if (typeof document !== "undefined") document.documentElement.dataset.contrast = value;
}

export function getDefaultPageSize(): number {
  const value = Number(read(PAGE_SIZE_KEY));
  return [10, 25, 50, 100].includes(value) ? value : 25;
}

export function setDefaultPageSize(value: number): void {
  write(PAGE_SIZE_KEY, String([10, 25, 50, 100].includes(value) ? value : 25));
}

export function getSidebarMode(): SidebarMode {
  return read(SIDEBAR_KEY) === "collapsed" ? "collapsed" : "expanded";
}

export function setSidebarMode(value: SidebarMode): void {
  write(SIDEBAR_KEY, value);
}

export function getAccessibleTables(): boolean {
  return read(ACCESSIBLE_TABLES_KEY) === "true";
}

export function setAccessibleTables(value: boolean): void {
  write(ACCESSIBLE_TABLES_KEY, String(value));
}

export function applyStoredUiPreferences(): void {
  if (typeof document !== "undefined") {
    document.documentElement.dataset.fontScale = getFontScale();
    document.documentElement.dataset.contrast = getContrastMode();
  }
}

export function hydrateRemoteUiPreferences(profile: RemoteUiPreferences): void {
  if (read(FONT_SCALE_KEY) === null && ["small", "standard", "large"].includes(profile.font_scale || "")) setFontScale(profile.font_scale as FontScale);
  if (read(CONTRAST_KEY) === null && ["standard", "high"].includes(profile.contrast_mode || "")) setContrastMode(profile.contrast_mode as ContrastMode);
  if (read(PAGE_SIZE_KEY) === null && profile.default_page_size !== undefined) setDefaultPageSize(profile.default_page_size);
  if (read(SIDEBAR_KEY) === null && ["expanded", "collapsed"].includes(profile.sidebar_mode || "")) setSidebarMode(profile.sidebar_mode as SidebarMode);
  if (read(ACCESSIBLE_TABLES_KEY) === null && profile.accessible_tables !== undefined) setAccessibleTables(profile.accessible_tables);
}

applyStoredUiPreferences();
