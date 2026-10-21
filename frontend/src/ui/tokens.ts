export type ThemeMode = "light" | "dark";
export type DensityMode = "comfortable" | "compact";
export type MotionMode = "normal" | "reduced";

export interface SemanticColors {
  background: string;
  surface: string;
  surfaceSecondary: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
  primary: string;
  primaryHover: string;
  accent: string;
  success: string;
  warning: string;
  danger: string;
  focusRing: string;
}

export const LIGHT_THEME: SemanticColors = {
  background: "#f8fafc",
  surface: "#ffffff",
  surfaceSecondary: "#f1f5f9",
  textPrimary: "#0f172a",
  textSecondary: "#475569",
  border: "#cbd5e1",
  primary: "#1d4ed8",
  primaryHover: "#1e40af",
  accent: "#0e7490",
  success: "#166534",
  warning: "#92400e",
  danger: "#b91c1c",
  focusRing: "#2563eb"
};

export const DARK_THEME: SemanticColors = {
  background: "#0b1220",
  surface: "#111c2e",
  surfaceSecondary: "#18263b",
  textPrimary: "#f1f5f9",
  textSecondary: "#94a3b8",
  border: "#334155",
  primary: "#3b82f6",
  primaryHover: "#60a5fa",
  accent: "#22d3ee",
  success: "#22c55e",
  warning: "#f59e0b",
  danger: "#ef4444",
  focusRing: "#60a5fa"
};

export const TYPOGRAPHY_TOKENS = {
  fontFamilySans: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
  fontFamilyMono: "'JetBrains Mono', monospace",
  fontSizeXs: "0.75rem",
  fontSizeSm: "0.875rem",
  fontSizeBase: "1rem",
  fontSizeLg: "1.125rem",
  fontSizeXl: "1.25rem",
  fontSize2xl: "1.5rem",
  fontSize3xl: "1.875rem",
  lineHeightNormal: "1.5",
  lineHeightTight: "1.25",
  fontWeightRegular: "400",
  fontWeightMedium: "500",
  fontWeightSemibold: "600",
  fontWeightBold: "700"
};

export const SPACING_TOKENS: Record<number, string> = {
  0: "0px",
  1: "0.25rem",
  2: "0.5rem",
  3: "0.75rem",
  4: "1rem",
  6: "1.5rem",
  8: "2rem",
  12: "3rem",
  16: "4rem"
};

export const RADIUS_TOKENS = {
  none: "0px",
  sm: "0.25rem",
  md: "0.5rem",
  lg: "0.75rem",
  xl: "1rem",
  "2xl": "1.5rem",
  full: "9999px"
};

export const SHADOW_TOKENS = {
  sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
  xl: "0 20px 25px -5px rgb(0 0 0 / 0.1)",
  "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)"
};

export interface DensitySettings {
  tableRowHeight: string;
  tableCellPadding: string;
  buttonPadding: string;
  fontSize: string;
  gapSize: string;
}

export const DENSITY_TOKENS: Record<DensityMode, DensitySettings> = {
  comfortable: {
    tableRowHeight: "h-12",
    tableCellPadding: "py-3 px-4",
    buttonPadding: "py-2 px-4",
    fontSize: "text-sm",
    gapSize: "gap-4"
  },
  compact: {
    tableRowHeight: "h-9",
    tableCellPadding: "py-1.5 px-3",
    buttonPadding: "py-1 px-2.5",
    fontSize: "text-xs",
    gapSize: "gap-2"
  }
};

export const Z_INDEX_TOKENS = {
  base: 0,
  sticky: 10,
  dropdown: 20,
  overlay: 30,
  modal: 40,
  toast: 50
};

export type BadgeVariant = "success" | "warning" | "danger" | "info" | "neutral";

export function getBadgeClass(variant: BadgeVariant, isDark: boolean = true): string {
  if (isDark) {
    switch (variant) {
      case "success":
        return "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30";
      case "warning":
        return "bg-amber-500/15 text-amber-300 border border-amber-500/30";
      case "danger":
        return "bg-rose-500/15 text-rose-300 border border-rose-500/30";
      case "info":
        return "bg-sky-500/15 text-sky-300 border border-sky-500/30";
      default:
        return "bg-slate-500/15 text-slate-300 border border-slate-500/30";
    }
  } else {
    switch (variant) {
      case "success":
        return "bg-emerald-50 text-emerald-800 border border-emerald-300";
      case "warning":
        return "bg-amber-50 text-amber-800 border border-amber-300";
      case "danger":
        return "bg-rose-50 text-rose-800 border border-rose-300";
      case "info":
        return "bg-sky-50 text-sky-800 border border-sky-300";
      default:
        return "bg-slate-100 text-slate-700 border border-slate-300";
    }
  }
}

export type ActionVariant = "primary" | "secondary" | "danger" | "ghost" | "outline";

export function getActionButtonClass(variant: ActionVariant, isDark: boolean = true): string {
  if (isDark) {
    switch (variant) {
      case "primary":
        return "bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-sm transition-colors focus:ring-2 focus:ring-indigo-400 focus:outline-none";
      case "secondary":
        return "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium transition-colors focus:ring-2 focus:ring-slate-500 focus:outline-none";
      case "outline":
        return "border border-slate-600 hover:bg-slate-800 text-slate-200 font-medium transition-colors focus:ring-2 focus:ring-slate-500 focus:outline-none";
      case "danger":
        return "bg-rose-600 hover:bg-rose-500 text-white font-medium shadow-sm transition-colors focus:ring-2 focus:ring-rose-400 focus:outline-none";
      case "ghost":
        return "bg-transparent hover:bg-slate-800 text-slate-300 font-medium transition-colors focus:ring-2 focus:ring-slate-600 focus:outline-none";
    }
  } else {
    switch (variant) {
      case "primary":
        return "bg-blue-700 hover:bg-blue-800 text-white font-medium shadow-sm transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none";
      case "secondary":
        return "bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 font-medium transition-colors focus:ring-2 focus:ring-slate-400 focus:outline-none";
      case "outline":
        return "border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium transition-colors focus:ring-2 focus:ring-slate-400 focus:outline-none";
      case "danger":
        return "bg-rose-700 hover:bg-rose-800 text-white font-medium shadow-sm transition-colors focus:ring-2 focus:ring-rose-500 focus:outline-none";
      case "ghost":
        return "bg-transparent hover:bg-slate-100 text-slate-700 font-medium transition-colors focus:ring-2 focus:ring-slate-300 focus:outline-none";
    }
  }
}

export function parseHexColor(hex: string): [number, number, number] {
  let clean = hex.replace("#", "").trim();
  if (clean.length === 3) {
    clean = clean.split("").map((c) => c + c).join("");
  }
  const r = parseInt(clean.substring(0, 2), 16) || 0;
  const g = parseInt(clean.substring(2, 4), 16) || 0;
  const b = parseInt(clean.substring(4, 6), 16) || 0;
  return [r, g, b];
}

export function calculateLuminance(hex: string): number {
  const [r, g, b] = parseHexColor(hex);
  const toLinear = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

export function getContrastRatio(fgHex: string, bgHex: string): number {
  const l1 = calculateLuminance(fgHex);
  const l2 = calculateLuminance(bgHex);
  const max = Math.max(l1, l2);
  const min = Math.min(l1, l2);
  return Number(((max + 0.05) / (min + 0.05)).toFixed(2));
}

export function verifyWcagContrast(
  fgHex: string,
  bgHex: string,
  isLargeText: boolean = false
): boolean {
  const threshold = isLargeText ? 3.0 : 4.5;
  return getContrastRatio(fgHex, bgHex) >= threshold;
}

let activeTheme: ThemeMode = "dark";
let inMemoryThemeTokens: SemanticColors = { ...DARK_THEME };

export function applyBrandTokens(brandOverrides: Partial<SemanticColors>): SemanticColors {
  inMemoryThemeTokens = {
    ...(activeTheme === "light" ? LIGHT_THEME : DARK_THEME),
    ...brandOverrides
  };
  if (typeof document !== "undefined" && document.documentElement) {
    const root = document.documentElement;
    Object.entries(inMemoryThemeTokens).forEach(([key, value]) => {
      root.style.setProperty(`--brand-${key}`, value);
    });
  }
  return inMemoryThemeTokens;
}

export function getStoredThemePreference(): ThemeMode {
  if (typeof window !== "undefined" && window.localStorage) {
    const item = window.localStorage.getItem("salesia_theme_preference");
    if (item === "light" || item === "dark") {
      activeTheme = item;
      return item;
    }
  }
  return activeTheme;
}

export function resolveThemePreference(remoteTheme?: ThemeMode): ThemeMode {
  if (typeof window !== "undefined" && window.localStorage) {
    const storedTheme = window.localStorage.getItem("salesia_theme_preference");
    if (storedTheme === "light" || storedTheme === "dark") return storedTheme;
  } else {
    return activeTheme;
  }
  return remoteTheme === "light" || remoteTheme === "dark" ? remoteTheme : activeTheme;
}

export function setStoredThemePreference(theme: ThemeMode): void {
  activeTheme = theme;
  inMemoryThemeTokens = { ...(theme === "light" ? LIGHT_THEME : DARK_THEME) };
  if (typeof window !== "undefined" && window.localStorage) {
    window.localStorage.setItem("salesia_theme_preference", theme);
  }
  if (typeof document !== "undefined" && document.documentElement) {
    if (theme === "light") {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.classList.remove("light");
      document.documentElement.classList.add("dark");
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }
}

if (typeof window !== "undefined" && typeof document !== "undefined" && document.documentElement) {
  const bootTheme = getStoredThemePreference();
  setStoredThemePreference(bootTheme);
}

let activeDensity: DensityMode = "comfortable";

export function getStoredDensityPreference(): DensityMode {
  if (typeof window !== "undefined" && window.localStorage) {
    const item = window.localStorage.getItem("salesia_density_preference");
    if (item === "comfortable" || item === "compact") {
      activeDensity = item;
      return item;
    }
  }
  return activeDensity;
}

export function setStoredDensityPreference(density: DensityMode): void {
  activeDensity = density;
  if (typeof window !== "undefined" && window.localStorage) {
    window.localStorage.setItem("salesia_density_preference", density);
  }
}

export function getActionHierarchyVariant(
  action: "confirm" | "draft" | "cancel" | "secondary"
): "primary" | "secondary" | "outline" | "danger" {
  switch (action) {
    case "confirm":
      return "primary";
    case "draft":
      return "outline";
    case "cancel":
      return "danger";
    case "secondary":
      return "secondary";
  }
}

export function getDualEncodedStatus(status: string): {
  symbol: string;
  text: string;
  variant: BadgeVariant;
} {
  const normalized = status.toLowerCase();
  if (
    normalized.includes("approved") ||
    normalized.includes("confirmed") ||
    normalized.includes("active") ||
    normalized.includes("paid")
  ) {
    return { symbol: "✓", text: "Confirmado", variant: "success" };
  }
  if (
    normalized.includes("pending") ||
    normalized.includes("draft") ||
    normalized.includes("low") ||
    normalized.includes("waiting")
  ) {
    return { symbol: "⏳", text: "Pendiente", variant: "warning" };
  }
  if (
    normalized.includes("rejected") ||
    normalized.includes("cancel") ||
    normalized.includes("out_of_stock") ||
    normalized.includes("danger")
  ) {
    return { symbol: "✕", text: "Anulado", variant: "danger" };
  }
  if (normalized.includes("info") || normalized.includes("process")) {
    return { symbol: "ℹ", text: "En proceso", variant: "info" };
  }
  return { symbol: "•", text: status, variant: "neutral" };
}
