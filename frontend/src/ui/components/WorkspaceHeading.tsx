import { NavbarSectionHeader } from "./NavbarSectionHeader";
import { Building2, Package, ShieldCheck, ShoppingCart, Users } from "lucide-react";

const details = {
  team: { icon: Users, group: "COMERCIAL", title: "Equipo y comisiones", description: "Gestiona vendedores, metas y liquidaciones de comisiones." },
  collaboration: { icon: Users, group: "COLABORACIÓN", title: "Colaboración", description: "Organiza tareas, avisos, aprobaciones y preferencias del equipo." },
  customers: { icon: Users, group: "COMERCIAL", title: "Clientes", description: "Gestiona contactos, condiciones comerciales y el historial de cada cliente." },
  products: { icon: Package, group: "CATÁLOGO", title: "Productos", description: "Organiza tu catálogo, precios y disponibilidad desde una sola vista." },
  sales: { icon: ShoppingCart, group: "COMERCIAL", title: "Ventas y cobros", description: "Consulta documentos, registra ventas y da seguimiento a los pagos." },
  organization: { icon: Building2, group: "ADMINISTRACIÓN", title: "Organización", description: "Administra la estructura de tu empresa, sus sedes y almacenes." },
  security: { icon: ShieldCheck, group: "SEGURIDAD", title: "Mi cuenta", description: "Revisa tus sesiones activas y controla el acceso a tu cuenta." }
};

export function WorkspaceHeading({ view, count, loading }: { view: string; count?: number; loading?: boolean }) {
  const item = details[view as keyof typeof details];
  if (!item) return null;
  const Icon = item.icon;
  return <NavbarSectionHeader view={view} className="workspace-heading mb-6 flex flex-wrap items-center justify-between gap-5">
    <div className="flex items-start gap-4">
      <div className="workspace-heading-icon"><Icon size={23} aria-hidden="true" /></div>
      <div><p className="workspace-eyebrow">{item.group}</p><h1>{item.title}</h1><p className="mt-2 text-sm text-slate-500">{item.description}</p></div>
    </div>
    {count !== undefined && <div className="workspace-record-count"><span>{loading ? "…" : count.toLocaleString("es-PE")}</span><small>registros encontrados</small></div>}
  </NavbarSectionHeader>;
}
