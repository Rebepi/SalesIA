import React from "react";
import { createRoot } from "react-dom/client";
import { apiClient } from "../src/api/client";
import { PurchaseReceiptDialog } from "../src/features/compras/components/PurchaseReceiptDialog";
import { ToastProvider } from "../src/ui/toast/ToastContext";
import "../src/index.css";
import "../src/ui/workspace.css";

const context = { order_id: "order", version: 4, status: "partially_received", warehouse_id: "warehouse", warehouse_name: "Central", supplier_name: "Proveedor real", currency: "PEN", locations: [], receipts: [], lines: [{ product_id: "lot", name: "Barniz", sku: "BAR-01", tracking_mode: "LOT", ordered_quantity: "5", received_quantity: "1", rejected_quantity: "0", pending_quantity: "4", unit_cost: "9" }, { product_id: "serial", name: "Equipo", sku: "EQU-01", tracking_mode: "SERIAL", ordered_quantity: "2", received_quantity: "0", rejected_quantity: "0", pending_quantity: "2", unit_cost: "25" }] };

apiClient.request = async path => path.includes("receiving-context") ? context as never : { id: "receipt-preview", items: [] } as never;
document.documentElement.dataset.theme = new URLSearchParams(window.location.search).get("theme") === "light" ? "light" : "dark";
createRoot(document.getElementById("root")!).render(<ToastProvider><main className="enterprise-workspace min-h-screen"><PurchaseReceiptDialog orderId="order" onClose={() => {}} onSaved={() => {}} /></main></ToastProvider>);
