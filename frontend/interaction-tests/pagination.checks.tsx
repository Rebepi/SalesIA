import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { PaginatedTable } from "../src/ui/components/PaginatedTable";
import { requestAllPages } from "../src/api/pagination";
import { apiClient } from "../src/api/client";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

function Records({ count }: { count: number }) {
  return <PaginatedTable aria-label="Clientes"><thead><tr><th>Nombre</th></tr></thead><tbody>{Array.from({ length: count }, (_, index) => <tr key={index}><td>Cliente {index + 1}</td></tr>)}</tbody></PaginatedTable>;
}

describe("Real collection pagination", () => {
  it("changes visible records and clamps the page after filtering", () => {
    const { rerender } = render(<Records count={55}/>);
    expect(screen.getByText("Cliente 1")).toBeTruthy();
    expect(screen.queryByText("Cliente 26")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Página siguiente" }));
    expect(screen.getByText("Cliente 26")).toBeTruthy();
    expect(screen.queryByText("Cliente 1")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Página siguiente" }));
    expect(screen.getByText("Cliente 55")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Página siguiente" }) as HTMLButtonElement).disabled).toBe(true);
    rerender(<Records count={12}/>);
    expect(screen.getByText("Cliente 1")).toBeTruthy();
    expect(screen.getByText("Página 1 de 1")).toBeTruthy();
    expect(screen.getByRole("region", { name: "Clientes" }).className).toBe("table-scroll-region");
  });

  it("changes page size and returns to the first page", () => {
    render(<Records count={55}/>);
    fireEvent.click(screen.getByRole("button", { name: "Página siguiente" }));
    fireEvent.change(document.querySelector("select")!, { target: { value: "10" } });
    expect(screen.getByText("Cliente 1")).toBeTruthy();
    expect(screen.queryByText("Cliente 11")).toBeNull();
    expect(screen.getByText("Página 1 de 6")).toBeTruthy();
  });

  it("loads all offset pages even when count describes only the current page", async () => {
    const request = vi.spyOn(apiClient, "request").mockImplementation(async path => {
      const offset = Number(new URL(path, "http://localhost").searchParams.get("offset"));
      const items = Array.from({ length: offset === 0 ? 100 : 17 }, (_, index) => ({ id: offset + index }));
      return { items, count: items.length };
    });
    const result = await requestAllPages<{ items: { id: number }[] }>("/api/v1/inventory/movements?warehouse_id=wh");
    expect(result.items).toHaveLength(117);
    expect(result.items[116].id).toBe(116);
    expect(request.mock.calls[1][0]).toContain("offset=100");
    expect(request.mock.calls[1][0]).toContain("warehouse_id=wh");
  });

  it("follows a real cursor including empty filtered pages", async () => {
    const request = vi.spyOn(apiClient, "request").mockResolvedValueOnce({ items: [], next_cursor: "cursor-real" }).mockResolvedValueOnce({ items: [{ id: "record-real" }], next_cursor: null });
    const result = await requestAllPages<{ items: unknown[] }>("/api/v1/audit/logs", "cursor");
    expect(result.items).toEqual([{ id: "record-real" }]);
    expect(request.mock.calls[1][0]).toContain("cursor=cursor-real");
  });

  it("requests subsequent server pages and stops at the total", async () => {
    const request = vi.spyOn(apiClient, "request").mockResolvedValueOnce({ items: Array.from({ length: 100 }, (_, id) => ({ id })), total_count: 101 }).mockResolvedValueOnce({ items: [{ id: 100 }], total_count: 101 });
    const result = await requestAllPages<{ items: unknown[] }>("/api/v1/users", "page");
    expect(result.items).toHaveLength(101);
    expect(request.mock.calls[1][0]).toContain("page=2");
  });

  it("rejects a repeated page instead of inventing progress", async () => {
    vi.spyOn(apiClient, "request").mockResolvedValue({ items: Array.from({ length: 100 }, (_, id) => ({ id })) });
    await expect(requestAllPages("/api/v1/analyses")).rejects.toThrow("repitió una página");
  });
});
