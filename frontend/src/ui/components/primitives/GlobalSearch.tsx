import React, { useState, useEffect } from "react";
import { Button } from "./Button";

export interface GlobalSearchResult {
  id: string;
  title: string;
  category: "customers" | "products" | "orders";
  companyId: string;
  metadata?: string;
}

export const GlobalSearch: React.FC<{
  currentCompanyId: string;
  dataset: GlobalSearchResult[];
  onSelect: (item: GlobalSearchResult) => void;
}> = ({ currentCompanyId, dataset, onSelect }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  const tenantFiltered = dataset.filter((d) => d.companyId === currentCompanyId);
  const matched = query.trim()
    ? tenantFiltered.filter((d) => d.title.toLowerCase().includes(query.toLowerCase()))
    : [];

  const grouped = {
    customers: matched.filter((m) => m.category === "customers"),
    products: matched.filter((m) => m.category === "products"),
    orders: matched.filter((m) => m.category === "orders")
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-slate-950/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <input
            autoFocus
            aria-label="Búsqueda global"
            placeholder="Buscar clientes, productos, pedidos (Ctrl+K)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none"
          />
          <Button size="sm" variant="ghost" onClick={() => setIsOpen(false)}>
            Cerrar
          </Button>
        </div>
        <div className="max-h-72 overflow-y-auto space-y-3 text-xs">
          {query.trim() === "" ? (
            <p className="text-slate-500 text-center py-4">Escriba un término para buscar en su empresa</p>
          ) : matched.length === 0 ? (
            <p className="text-slate-500 text-center py-4">No se encontraron resultados en esta empresa</p>
          ) : (
            <>
              {grouped.customers.length > 0 && (
                <div>
                  <span className="font-semibold text-slate-400 uppercase tracking-wider block mb-1">Clientes</span>
                  {grouped.customers.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => { onSelect(c); setIsOpen(false); }}
                      className="p-2 rounded-lg hover:bg-slate-800 cursor-pointer flex justify-between text-slate-200"
                    >
                      <span>{c.title}</span>
                      <span className="text-slate-400">{c.metadata}</span>
                    </div>
                  ))}
                </div>
              )}
              {grouped.products.length > 0 && (
                <div>
                  <span className="font-semibold text-slate-400 uppercase tracking-wider block mb-1">Productos</span>
                  {grouped.products.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => { onSelect(p); setIsOpen(false); }}
                      className="p-2 rounded-lg hover:bg-slate-800 cursor-pointer flex justify-between text-slate-200"
                    >
                      <span>{p.title}</span>
                      <span className="text-slate-400">{p.metadata}</span>
                    </div>
                  ))}
                </div>
              )}
              {grouped.orders.length > 0 && (
                <div>
                  <span className="font-semibold text-slate-400 uppercase tracking-wider block mb-1">Pedidos</span>
                  {grouped.orders.map((o) => (
                    <div
                      key={o.id}
                      onClick={() => { onSelect(o); setIsOpen(false); }}
                      className="p-2 rounded-lg hover:bg-slate-800 cursor-pointer flex justify-between text-slate-200"
                    >
                      <span>{o.title}</span>
                      <span className="text-slate-400">{o.metadata}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
