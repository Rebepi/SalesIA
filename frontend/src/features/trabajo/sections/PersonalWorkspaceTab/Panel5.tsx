import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { Link as LinkIcon, Search, ShoppingCart, User, X, LoaderCircle } from "lucide-react";

export function Panel5({ activePopover, setActivePopover, canReadCustomers, canReadSales, setLinkTab, quickResource, setQuickResource, setLinkSearchQuery, linkTab, linkSearchQuery, linkSearchLoading, linkCustomers, linkOrders }: { activePopover: ReturnType<typeof usePersonalWorkspaceTab>["activePopover"]; setActivePopover: ReturnType<typeof usePersonalWorkspaceTab>["setActivePopover"]; canReadCustomers: ReturnType<typeof usePersonalWorkspaceTab>["canReadCustomers"]; canReadSales: ReturnType<typeof usePersonalWorkspaceTab>["canReadSales"]; setLinkTab: ReturnType<typeof usePersonalWorkspaceTab>["setLinkTab"]; quickResource: ReturnType<typeof usePersonalWorkspaceTab>["quickResource"]; setQuickResource: ReturnType<typeof usePersonalWorkspaceTab>["setQuickResource"]; setLinkSearchQuery: ReturnType<typeof usePersonalWorkspaceTab>["setLinkSearchQuery"]; linkTab: ReturnType<typeof usePersonalWorkspaceTab>["linkTab"]; linkSearchQuery: ReturnType<typeof usePersonalWorkspaceTab>["linkSearchQuery"]; linkSearchLoading: ReturnType<typeof usePersonalWorkspaceTab>["linkSearchLoading"]; linkCustomers: ReturnType<typeof usePersonalWorkspaceTab>["linkCustomers"]; linkOrders: ReturnType<typeof usePersonalWorkspaceTab>["linkOrders"] }) {
  return (<div className="relative">
    <div className={`inline-flex items-center rounded-lg border text-xs font-medium transition ${activePopover === "link" ? "border-teal-500 dark:border-teal-500 bg-teal-50 dark:bg-teal-950/60 text-teal-800 dark:text-teal-200 ring-1 ring-teal-400 dark:ring-teal-600" : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/80 text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-700"}`}>
      <button
        type="button"
        aria-label="Vincular a cliente o pedido"
        aria-haspopup="true"
        aria-expanded={activePopover === "link"}
        onClick={() => {
          setActivePopover(prev => prev === "link" ? null : "link");
          if (!canReadCustomers && canReadSales) setLinkTab("order");
        }}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${quickResource ? "text-teal-700 dark:text-teal-300 font-semibold" : ""
          }`}
      >
        <LinkIcon className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
        <span className="truncate max-w-[150px]">
          {quickResource ? quickResource.name : "Vincular"}
        </span>
      </button>
      {quickResource && (
        <button
          type="button"
          aria-label="Desvincular recurso"
          onClick={() => setQuickResource(null)}
          className="p-1 pr-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>

    {activePopover === "link" && (
      <div className="absolute left-0 top-full mt-1.5 z-40 w-72 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 shadow-xl space-y-2.5">
        <div className="flex items-center rounded-lg bg-slate-100 dark:bg-slate-800 p-0.5 text-xs font-semibold">
          {canReadCustomers && (
            <button
              type="button"
              onClick={() => {
                setLinkTab("customer");
                setLinkSearchQuery("");
              }}
              className={`flex-1 rounded-md py-1 text-center transition ${linkTab === "customer"
                ? "bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                }`}
            >
              Cliente
            </button>
          )}
          {canReadSales && (
            <button
              type="button"
              onClick={() => {
                setLinkTab("order");
                setLinkSearchQuery("");
              }}
              className={`flex-1 rounded-md py-1 text-center transition ${linkTab === "order"
                ? "bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                }`}
            >
              Pedido
            </button>
          )}
        </div>

        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            value={linkSearchQuery}
            onChange={e => setLinkSearchQuery(e.target.value)}
            placeholder={linkTab === "customer" ? "Buscar por nombre o RUC..." : "Buscar por número de pedido..."}
            className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 py-1.5 pl-8 pr-2 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-teal-600 focus:bg-white dark:focus:bg-slate-900"
          />
        </div>

        <div className="max-h-40 overflow-y-auto space-y-1">
          {linkSearchLoading ? (
            <div className="flex justify-center py-4 text-slate-400">
              <LoaderCircle className="h-5 w-5 animate-spin text-teal-600" />
            </div>
          ) : linkTab === "customer" ? (
            linkCustomers.length === 0 ? (
              <p className="py-3 text-center text-[11px] text-slate-400">Sin resultados de clientes</p>
            ) : (
              linkCustomers.map(cust => (
                <button
                  key={cust.id}
                  type="button"
                  onClick={() => {
                    setQuickResource({ type: "customer", id: cust.id, name: cust.legal_name });
                    setActivePopover(null);
                    setLinkSearchQuery("");
                  }}
                  className="w-full flex items-center justify-between rounded-lg p-2 text-left text-xs hover:bg-slate-50 dark:hover:bg-slate-800/70 transition"
                >
                  <div className="min-w-0 pr-2">
                    <p className="font-semibold text-slate-900 dark:text-slate-100 truncate">{cust.legal_name}</p>
                    <p className="text-[10px] text-slate-400 font-mono">{cust.doc_number}</p>
                  </div>
                  <User className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                </button>
              ))
            )
          ) : (
            linkOrders.length === 0 ? (
              <p className="py-3 text-center text-[11px] text-slate-400">Sin resultados de pedidos</p>
            ) : (
              linkOrders.map(ord => (
                <button
                  key={ord.order_id}
                  type="button"
                  onClick={() => {
                    setQuickResource({ type: "order", id: ord.order_id, name: ord.order_number });
                    setActivePopover(null);
                    setLinkSearchQuery("");
                  }}
                  className="w-full flex items-center justify-between rounded-lg p-2 text-left text-xs hover:bg-slate-50 dark:hover:bg-slate-800/70 transition"
                >
                  <div className="min-w-0 pr-2">
                    <p className="font-semibold text-slate-900 dark:text-slate-100">{ord.order_number}</p>
                    <p className="text-[10px] text-slate-400 truncate">{ord.customer_name || "Cliente"}</p>
                  </div>
                  <ShoppingCart className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                </button>
              ))
            )
          )}
        </div>
      </div>
    )}
  </div>);
}
