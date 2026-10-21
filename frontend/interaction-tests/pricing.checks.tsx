import React from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { PricingAndPromotionsTab } from "../src/features/precios/components/PricingAndPromotionsTab";

const toast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => toast }));

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("uses the pricing preview API and converts campaign percentages", async () => {
  vi.spyOn(apiClient, "request").mockImplementation(async (path, options) => {
    if (path.startsWith("/api/v1/products")) return { items: [{ id: "product-1", name: "Producto", sku: "SKU-1" }] };
    if (path.startsWith("/api/v1/customers")) return { items: [{ id: "customer-1", legal_name: "Cliente" }] };
    if (path === "/api/v1/prices/preview") return { total_estimated: "118.00", discount_applied: "10.00" };
    if (path === "/api/v1/promotions" && options?.method === "POST") return {};
    return [];
  });
  render(<PricingAndPromotionsTab />);
  await waitFor(() => expect(document.querySelectorAll("#sim-product-native option")).toHaveLength(2));
  fireEvent.change(document.getElementById("sim-product-native")!, { target: { value: "product-1" } });
  fireEvent.click(screen.getByRole("button", { name: "Calcular precio" }));
  await screen.findByText("Total Simulado: $118.00");
  expect(apiClient.request).toHaveBeenCalledWith("/api/v1/prices/preview", expect.objectContaining({ method: "POST" }));
  fireEvent.click(screen.getByRole("button", { name: "Crear campaña" }));
  fireEvent.change(screen.getByPlaceholderText("Ej. CYBER20"), { target: { value: "cyber20" } });
  fireEvent.change(screen.getByPlaceholderText("Ej. Promo Verano 2026"), { target: { value: "Cyber" } });
  fireEvent.click(screen.getByRole("button", { name: "Registrar Campaña" }));
  await waitFor(() => expect(apiClient.request).toHaveBeenCalledWith("/api/v1/promotions", expect.objectContaining({ body: expect.stringContaining('"discount_percentage":"0.1"') })));
});
