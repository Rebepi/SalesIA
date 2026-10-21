import type { useOperationsWorkspace } from "../../hooks/useOperationsWorkspace";
import { Building2 } from "lucide-react";

export function Panel3({ organization }: { organization: ReturnType<typeof useOperationsWorkspace>["organization"] }) {
  return (<section className="grid gap-4 sm:grid-cols-2">

    {[

      { action: "onboarding" as const, title: "Asistente de alta guiada", description: "Configuración inicial guiada de empresa, sede, almacén y series correlativas." },

      { action: "company" as const, title: "Datos de empresa", description: "Nombre comercial, razón social y moneda base." },

      { action: "branch" as const, title: "Crear sucursal", description: "Registra una sede y su zona horaria." },

      { action: "warehouse" as const, title: "Crear almacén", description: "Vincula un almacén con una sucursal activa." },

      { action: "settings" as const, title: "Configuración comercial", description: "Impuestos predeterminados, redondeo y cierre contable." }

    ].map(item => (

      <button

        key={item.action}

        onClick={() => void organization(item.action)}

        className="group rounded-2xl border border-slate-200 bg-white p-6 text-left transition hover:border-teal-400 hover:shadow-md focus-visible:outline focus-visible:outline-teal-400"

      >

        <Building2 className="mb-5 h-6 w-6 text-teal-700 motion-safe:transition-transform motion-safe:group-hover:-translate-y-1" />

        <h2 className="font-semibold">{item.title}</h2>

        <p className="mt-2 text-sm text-slate-500">{item.description}</p>

      </button>

    ))}

  </section>);
}
