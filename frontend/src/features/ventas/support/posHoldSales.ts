import { CustomerItem, SaleCartLine, WarehouseItem } from "../types/NewSalePOSModal";

export type HoldExpirationUnit = "MINUTES" | "HOURS" | "DAYS";

export interface HoldExpirationConfig {
  value: number;
  unit: HoldExpirationUnit;
}

export interface PosHoldSale {
  id: string;
  label: string;
  createdAt: string;
  expiresAt: string;
  customer?: CustomerItem;
  warehouseId: string;
  selectedWarehouse?: WarehouseItem;
  currency: string;
  isCredit: boolean;
  documentType: "RECEIPT" | "INVOICE" | "SALE_NOTE";
  couponCode: string;
  notes: string;
  deliveryAddress: string;
  internalObservations: string;
  exchangeRate: string;
  salesRepId: string;
  cart: SaleCartLine[];
  totals: {
    subtotal: number;
    tax: number;
    total: number;
  };
}

const DEFAULT_CONFIG: HoldExpirationConfig = {
  value: 2,
  unit: "HOURS"
};

function getScope(): string {
  if (typeof sessionStorage === "undefined") return "default";
  return sessionStorage.getItem("salesia_company_id") || "default";
}

function getConfigKey(): string {
  return `${getScope()}:salesia_pos_hold_expiration_cfg`;
}

function getListKey(): string {
  return `${getScope()}:salesia_pos_hold_sales_list`;
}

function getAllowCreditKey(): string {
  return `${getScope()}:salesia_allow_credit_sales`;
}

export function getAllowCreditSalesConfig(): boolean {
  if (typeof localStorage === "undefined") return true;
  try {
    const raw = localStorage.getItem(getAllowCreditKey());
    if (raw === null) return true;
    return raw === "true";
  } catch {
    return true;
  }
}

export function setAllowCreditSalesConfig(allowed: boolean): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(getAllowCreditKey(), String(allowed));
    window.dispatchEvent(new CustomEvent("salesia:allow-credit-changed", { detail: { allowed } }));
  } catch {}
}

export function getHoldExpirationConfig(): HoldExpirationConfig {
  if (typeof localStorage === "undefined") return DEFAULT_CONFIG;
  try {
    const raw = localStorage.getItem(getConfigKey());
    if (!raw) return DEFAULT_CONFIG;
    const parsed = JSON.parse(raw);
    const value = Math.max(1, Number(parsed.value) || 2);
    const unit: HoldExpirationUnit = parsed.unit === "MINUTES" || parsed.unit === "DAYS" ? parsed.unit : "HOURS";
    return { value, unit };
  } catch {
    return DEFAULT_CONFIG;
  }
}

export function setHoldExpirationConfig(cfg: HoldExpirationConfig): void {
  if (typeof localStorage === "undefined") return;
  try {
    const value = Math.max(1, Number(cfg.value) || 1);
    const unit: HoldExpirationUnit = cfg.unit === "MINUTES" || cfg.unit === "DAYS" ? cfg.unit : "HOURS";
    localStorage.setItem(getConfigKey(), JSON.stringify({ value, unit }));
  } catch { }
}

export function calculateExpirationDurationMs(cfg: HoldExpirationConfig): number {
  const value = Math.max(1, Number(cfg.value) || 1);
  if (cfg.unit === "MINUTES") return value * 60 * 1000;
  if (cfg.unit === "DAYS") return value * 24 * 60 * 60 * 1000;
  return value * 60 * 60 * 1000;
}

export function getHoldSales(): PosHoldSale[] {
  if (typeof localStorage === "undefined") return [];
  try {
    const raw = localStorage.getItem(getListKey());
    if (!raw) return [];
    const list: PosHoldSale[] = JSON.parse(raw);
    const now = Date.now();
    const active = list.filter(item => {
      const exp = new Date(item.expiresAt).getTime();
      return !Number.isNaN(exp) && exp > now;
    });
    if (active.length !== list.length) {
      localStorage.setItem(getListKey(), JSON.stringify(active));
    }
    return active.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  } catch {
    return [];
  }
}

export function saveHoldSale(data: Omit<PosHoldSale, "id" | "createdAt" | "expiresAt">): PosHoldSale {
  const cfg = getHoldExpirationConfig();
  const durationMs = calculateExpirationDurationMs(cfg);
  const now = Date.now();
  const holdSale: PosHoldSale = {
    ...data,
    id: crypto.randomUUID(),
    createdAt: new Date(now).toISOString(),
    expiresAt: new Date(now + durationMs).toISOString()
  };
  if (typeof localStorage === "undefined") return holdSale;
  try {
    const existing = getHoldSales();
    const nextList = [holdSale, ...existing];
    localStorage.setItem(getListKey(), JSON.stringify(nextList));
  } catch { }
  return holdSale;
}

export function deleteHoldSale(id: string): void {
  if (typeof localStorage === "undefined") return;
  try {
    const existing = getHoldSales();
    const filtered = existing.filter(item => item.id !== id);
    localStorage.setItem(getListKey(), JSON.stringify(filtered));
  } catch { }
}

export function formatTimeRemaining(expiresAt: string): string {
  const diffMs = new Date(expiresAt).getTime() - Date.now();
  if (diffMs <= 0) return "Expirada";
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHours = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays >= 1) {
    const remHours = diffHours % 24;
    return `${diffDays}d ${remHours}h restantes`;
  }
  if (diffHours >= 1) {
    const remMin = diffMin % 60;
    return `${diffHours}h ${remMin}m restantes`;
  }
  if (diffMin >= 1) {
    return `${diffMin} min restantes`;
  }
  return "< 1 min restante";
}