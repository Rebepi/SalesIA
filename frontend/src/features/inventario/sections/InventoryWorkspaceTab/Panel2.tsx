import { useOperatingProfile } from "../../../organizacion/components/OperatingProfileContext";
import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { Boxes, ClipboardCheck, History, Layers, MapPin, Send, ShieldAlert, ShoppingBag, Truck } from "lucide-react";
import { Submodule } from "../../types/InventoryWorkspaceTab";

export function Panel2({ canScrollLeft, navRef, submodule, setSubmodule, setSearch, canScrollRight }: { canScrollLeft: ReturnType<typeof useInventoryWorkspaceTab>["canScrollLeft"]; navRef: ReturnType<typeof useInventoryWorkspaceTab>["navRef"]; submodule: ReturnType<typeof useInventoryWorkspaceTab>["submodule"]; setSubmodule: ReturnType<typeof useInventoryWorkspaceTab>["setSubmodule"]; setSearch: ReturnType<typeof useInventoryWorkspaceTab>["setSearch"]; canScrollRight: ReturnType<typeof useInventoryWorkspaceTab>["canScrollRight"] }) {
  const { enabled } = useOperatingProfile();
  return (<div className="inventory-nav-container flex-shrink-0">
    <div
      aria-hidden="true"
      className={`inventory-nav-fade-left ${canScrollLeft ? "opacity-100" : "opacity-0"}`}
    />

    <nav
      ref={navRef}
      aria-label="Submódulos de inventario"
      className="inventory-module-nav"
    >
      {[
        { key: "stock" as Submodule, label: "Existencias y Disponibilidad", Icon: Boxes },
        { key: "kardex" as Submodule, label: "Kardex y Libro Mayor", Icon: History },
        { key: "purchases" as Submodule, label: "Compras y Proveedores", Icon: ShoppingBag },
        { key: "shipping" as Submodule, label: "Entregas y Logística", Icon: Send },
        { key: "transfers" as Submodule, label: "Transferencias en Tránsito", Icon: Truck },
        { key: "counts" as Submodule, label: "Conteos Físicos Ciegos", Icon: ClipboardCheck },
        { key: "lots_serials" as Submodule, label: "Lotes y Series", Icon: Layers },
        { key: "locations_rules" as Submodule, label: "Ubicaciones y Reglas", Icon: MapPin },
        { key: "alerts_reconcile" as Submodule, label: "Alertas y Reconciliación", Icon: ShieldAlert }
      ].map(({ key, label, Icon }) => (
        <button
          key={key}
          aria-current={submodule === key ? "page" : undefined}
          onClick={e => {
            e.currentTarget.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
            setSubmodule(key);
            setSearch("");
          }}
          className={`inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition ${submodule === key
            ? "bg-teal-700 text-white shadow-sm"
            : "border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:border-teal-300 hover:bg-teal-50 dark:hover:bg-slate-800"
            }`}
        >
          <Icon className="h-3.5 w-3.5" />
          {label}{key === "purchases" && !enabled("purchases") || key === "shipping" && !enabled("delivery") ? " · Historial" : ""}
        </button>
      ))}
    </nav>

    <div
      aria-hidden="true"
      className={`inventory-nav-fade-right ${canScrollRight ? "opacity-100" : "opacity-0"}`}
    />
  </div>);
}
