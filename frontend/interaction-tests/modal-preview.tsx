import React from "react";
import { createRoot } from "react-dom/client";
import { apiClient } from "../src/api/client";
import { NewSalePOSModal } from "../src/features/ventas/components/NewSalePOSModal";
import { ToastProvider } from "../src/ui/toast/ToastContext";
import "../src/index.css";
import "../src/ui/workspace.css";

const customer = { id: "c1", code: "CLI-01", legal_name: "Cliente existente", doc_type: "RUC", doc_number: "20123456789", credit_limit: "1000" };
const newCustomer = { ...customer, id: "c2", code: "CLI-02", legal_name: "Cliente nuevo", doc_number: "20234567890" };
const product = { id: "p1", sku: "TAB-01", name: "Tablero", unit_price: "10", available_quantity: "20", unit_of_measure: "NIU", track_inventory: true };

async function respond(path: string, options?: { method?: string }) {
  if (path.endsWith("/companies/current")) return { base_currency: "PEN" };
  if (path.endsWith("/settings")) return { default_tax_rate: "0.18", rounding_mode: "ROUND_HALF_EVEN", tax_included_in_price: false };
  if (path.includes("/warehouses")) return [{ warehouse_id: "w1", branch_id: "b1", code: "ALM-01", name: "Principal" }];
  if (path.includes("/branches")) return [{ branch_id: "b1", name: "Lima", timezone: "America/Lima" }];
  if (path.endsWith("walk-in/ensure") || path.endsWith("/customers/c1")) return customer;
  if (path.endsWith("/customers/c2")) return newCustomer;
  if (path.includes("duplicates/check")) return { exact_matches: [], potential_matches: [] };
  if (path.includes("fiscal/validate")) return { valid: true };
  if (path.endsWith("/customers") && options?.method === "POST") return newCustomer;
  if (path.includes("/customers")) return { items: [customer], total_count: 1 };
  if (path.includes("payment-methods")) return [];
  if (path.includes("cash-sessions")) return { session: null };
  if (path.includes("search-availability")) return { items: [product], total_count: 1 };
  if (path.includes("prices/preview")) return { product_id: "p1", final_unit_price: "10", total_estimated: "11.8", rules_applied: [] };
  return { items: [] };
}

apiClient.request = respond as typeof apiClient.request;
function Preview() {
  const dark = new URLSearchParams(window.location.search).get("theme") !== "light";
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  return <ToastProvider><main className="enterprise-workspace min-h-screen"><NewSalePOSModal isOpen onClose={() => {}} onSaleCreated={() => {}} /></main></ToastProvider>;
}
createRoot(document.getElementById("root")!).render(<Preview />);
