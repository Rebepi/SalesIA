import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { DashboardAnalyticsTab } from "../src/features/analitica/components/DashboardAnalyticsTab";

vi.mock("../src/api/client", () => ({ apiClient: { request: () => new Promise(() => {}) } }));
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ error: vi.fn(), success: vi.fn(), info: vi.fn(), warning: vi.fn() }) }));
afterEach(cleanup);

describe("Executive dashboard filters", () => {
  it("starts collapsed, preserves selection while closed and restores focus on Escape", () => {
    localStorage.clear();
    render(<DashboardAnalyticsTab />);
    const toggle = screen.getByRole("button", { name: "Filtros" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByRole("region", { name: "Filtros del resumen ejecutivo" })).toBeNull();
    fireEvent.click(toggle);
    const panel = screen.getByRole("region", { name: "Filtros del resumen ejecutivo" });
    const period = document.getElementById("dash-period-select-native") as HTMLSelectElement;
    fireEvent.change(period, { target: { value: "7d" } });
    fireEvent.keyDown(panel, { key: "Escape" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(document.activeElement).toBe(toggle);
    expect(screen.getByRole("button", { name: "Restablecer periodo a 30 días" })).toBeTruthy();
    fireEvent.click(toggle);
    expect(period.value).toBe("7d");
    fireEvent.click(screen.getByRole("button", { name: "Limpiar filtros" }));
    expect(period.value).toBe("30d");
  });
});
