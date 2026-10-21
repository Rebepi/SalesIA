import type { BreadcrumbItem } from "./Breadcrumbs";

export function reconstructBreadcrumbsFromPath(pathname: string): BreadcrumbItem[] {
  const parts = pathname.split("/").filter(Boolean);
  const items: BreadcrumbItem[] = [{ label: "Inicio", href: "/" }];
  let accum = "";
  parts.forEach((part, index) => {
    accum += `/${part}`;
    const isLast = index === parts.length - 1;
    let label = part;
    if (part === "sales") label = "Ventas";
    else if (part === "customers") label = "Clientes";
    else if (part === "products") label = "Productos";
    else if (part === "orders") label = "Pedidos";
    items.push({
      label,
      href: isLast ? undefined : accum,
      current: isLast
    });
  });
  return items;
}
