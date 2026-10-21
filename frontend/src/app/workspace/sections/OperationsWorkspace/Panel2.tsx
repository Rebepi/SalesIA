import type { useOperationsWorkspace } from "../../hooks/useOperationsWorkspace";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { setSidebarMode as persistSidebarMode } from "../../../../ui/preferences";

export function Panel2({ sidebarCollapsed, setSidebarCollapsed, setSidebarHoveredTooltip }: { sidebarCollapsed: ReturnType<typeof useOperationsWorkspace>["sidebarCollapsed"]; setSidebarCollapsed: ReturnType<typeof useOperationsWorkspace>["setSidebarCollapsed"]; setSidebarHoveredTooltip: ReturnType<typeof useOperationsWorkspace>["setSidebarHoveredTooltip"] }) {
  return (<div style={{ borderTop: "1px solid var(--sb-border)" }} className="p-3">

    {sidebarCollapsed ? (

      <div className="flex justify-center">

        <button

          type="button"

          onClick={() => { setSidebarCollapsed(false); persistSidebarMode("expanded"); setSidebarHoveredTooltip(null); }}

          aria-label="Expandir menú"

          title="Expandir menú"

          style={{ color: "var(--sb-muted)" }}

          onMouseEnter={e => {

            (e.currentTarget as HTMLElement).style.background = "var(--sb-hover)";

            (e.currentTarget as HTMLElement).style.color = "var(--sb-text)";

            const rect = e.currentTarget.getBoundingClientRect();

            setSidebarHoveredTooltip({ label: "Expandir menú", top: rect.top + rect.height / 2 });

          }}

          onMouseLeave={e => {

            (e.currentTarget as HTMLElement).style.background = "transparent";

            (e.currentTarget as HTMLElement).style.color = "var(--sb-muted)";

            setSidebarHoveredTooltip(null);

          }}

          className="flex h-10 w-10 items-center justify-center rounded-xl transition-colors"

        >

          <ChevronRight className="h-5 w-5 shrink-0" />

        </button>

      </div>

    ) : (

      <button

        type="button"

        onClick={() => { setSidebarCollapsed(true); persistSidebarMode("collapsed"); setSidebarHoveredTooltip(null); }}

        aria-label="Colapsar menú"

        title="Colapsar menú"

        style={{ color: "var(--sb-muted)" }}

        onMouseEnter={e => {

          (e.currentTarget as HTMLElement).style.background = "var(--sb-hover)";

          (e.currentTarget as HTMLElement).style.color = "var(--sb-text)";

        }}

        onMouseLeave={e => {

          (e.currentTarget as HTMLElement).style.background = "transparent";

          (e.currentTarget as HTMLElement).style.color = "var(--sb-muted)";

        }}

        className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-[13px] font-medium transition-colors"

      >

        <ChevronLeft className="h-4 w-4 shrink-0" />

        <span className="truncate">Colapsar menú</span>

      </button>

    )}

  </div>);
}
