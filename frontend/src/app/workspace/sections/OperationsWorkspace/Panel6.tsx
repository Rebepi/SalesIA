import type { useOperationsWorkspace } from "../../hooks/useOperationsWorkspace";


export function Panel6({ sidebarHoveredTooltip }: { sidebarHoveredTooltip: NonNullable<ReturnType<typeof useOperationsWorkspace>["sidebarHoveredTooltip"]> }) {
  return (<div

    role="tooltip"

    className="pointer-events-none fixed z-[9999] flex items-center rounded-lg px-2.5 py-1.5 text-xs font-semibold shadow-2xl border border-slate-700 whitespace-nowrap animate-in fade-in zoom-in-95 duration-100"

    style={{

      left: "80px",

      top: `${sidebarHoveredTooltip.top}px`,

      transform: "translateY(-50%)",

      background: "#0f172a",

      color: "#f8fafc",

      boxShadow: "0 10px 25px -5px rgba(0,0,0,0.6)",

    }}

  >

    <span className="relative z-10">{sidebarHoveredTooltip.label}</span>

    <span

      className="absolute -left-1 top-1/2 -translate-y-1/2 h-2 w-2 rotate-45 border-l border-b border-slate-700"

      style={{ background: "#0f172a" }}

    />

  </div>);
}
