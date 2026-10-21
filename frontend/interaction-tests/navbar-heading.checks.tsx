import React, { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { NavbarHeaderProvider, NavbarHeaderSlot, NavbarSectionHeader } from "../src/ui/components/NavbarSectionHeader";

afterEach(cleanup);

function Page() {
  const [view, setView] = useState("customers");
  const [count, setCount] = useState(270);
  return <NavbarHeaderProvider view={view}>
    <nav aria-label="Principal"><NavbarHeaderSlot view={view} title={view === "customers" ? "Clientes" : "Catálogo"} /></nav>
    <main>
      <button onClick={() => setView("products")}>Productos</button>
      {view === "customers" ? <NavbarSectionHeader view="customers"><h1>Clientes</h1><span>{count} registros</span><button onClick={() => setCount(count + 1)}>Actualizar</button></NavbarSectionHeader> : <NavbarSectionHeader view="products"><h1>Catálogo</h1></NavbarSectionHeader>}
      <NavbarSectionHeader inline><h2>Encabezado de ventana</h2></NavbarSectionHeader>
    </main>
  </NavbarHeaderProvider>;
}

describe("Navbar section heading", () => {
  it("keeps only title and description in the navbar while actions remain in the page", () => {
    render(<Page />);
    const navbar = within(screen.getByRole("navigation"));
    const main = within(screen.getByRole("main"));
    expect(navbar.getByRole("heading", { name: "Clientes" })).toBeTruthy();
    expect(main.queryByRole("heading", { name: "Clientes" })).toBeNull();
    expect(navbar.queryByRole("button", { name: "Actualizar" })).toBeNull();
    fireEvent.click(main.getByRole("button", { name: "Actualizar" }));
    expect(main.getByText("271 registros")).toBeTruthy();
    expect(main.getByRole("heading", { name: "Encabezado de ventana" })).toBeTruthy();
    fireEvent.click(main.getByRole("button", { name: "Productos" }));
    expect(navbar.queryByRole("heading", { name: "Clientes" })).toBeNull();
    expect(navbar.getByRole("heading", { name: "Catálogo" })).toBeTruthy();
  });
});
