import type { ReactNode } from "react";
import type { DashboardSummary, ProductsAnalytics, CustomersAnalytics, SellersAnalytics } from "../types/DashboardAnalyticsTab";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";

const sellerCategoryNames: Record<string, string> = { active: "Activos", inactive: "Inactivos", unassigned: "Sin asignar", unidentifiable: "Vendedor no identificable" };

type Props = {
  summary: DashboardSummary | null;
  products: ProductsAnalytics | null;
  customers: CustomersAnalytics | null;
  sellers: SellersAnalytics | null;
  productsLoading: boolean;
  customersLoading: boolean;
  sellersLoading: boolean;
  productsError: string;
  customersError: string;
  sellersError: string;
  retryProducts: () => unknown;
  retryCustomers: () => unknown;
  retrySellers: () => unknown;
  visible: { products: boolean; sellers: boolean; customers: boolean; inventory: boolean };
  formatMoney: (value: string | number) => string;
  navigate: (view: string, key?: string, expectedCount?: number) => void;
};

function Card({ title, subtitle, children, action, help, compact = false }: { title: string; subtitle?: string; children: ReactNode; action?: ReactNode; help?: string; compact?: boolean }) {
  return <article className={`flex min-w-0 flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 ${compact ? "self-start" : "h-full"}`}><header className="flex flex-wrap items-start justify-between gap-2"><div><h2 className="flex items-center gap-1.5 text-base font-bold text-slate-900 dark:text-white"><span>{title}</span>{help && <InfoTooltip interactive title={title} description={help} />}</h2>{subtitle && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>}</div>{action}</header><div className="mt-3">{children}</div></article>;
}

function Status({ loading, error, retry }: { loading: boolean; error: string; retry: () => unknown }) {
  if (error) return <div role="alert" className="text-sm text-rose-700 dark:text-rose-400"><p>{error}</p><button type="button" className="mt-2 font-semibold underline" onClick={retry}>Reintentar</button></div>;
  if (loading) return <p role="status" className="text-sm text-slate-500">Actualizando resumen…</p>;
  return null;
}

export function ExecutiveHighlights(props: Props) {
  const { summary, products, customers, sellers, visible, formatMoney, navigate } = props;
  const executive = summary?.executive;
  const link = (label: string, view: string, key?: string, count?: number) => executive?.allowed_views.includes(view) && (!key || executive.drilldowns?.[key]) ? <button type="button" onClick={() => navigate(view, key, count)} className="text-xs font-semibold text-teal-700 hover:underline dark:text-teal-400">{label} →</button> : null;
  const inventory = summary?.inventory_summary;
  const inventoryCurrency = executive?.inventory_currency || summary?.currency || "USD";
  const valuation = inventory?.valuation_total === null ? "Restringido" : inventory?.valuation_total === undefined ? "Sin información" : new Intl.NumberFormat("es-PE", { style: "currency", currency: inventoryCurrency, maximumFractionDigits: 2 }).format(Number(inventory.valuation_total));
  return <section aria-label="Resumen comercial y operativo" className="grid items-stretch gap-4 lg:grid-cols-2">
    {visible.products && <Card title="Productos que impulsan las ventas · Top 5" help="Participación sobre las líneas de productos seleccionadas. Cobertura sobre la facturación total con los mismos filtros. Los documentos sin detalle no aportan líneas a este ranking." action={link("Ver análisis", "sales_analytics")}>
      <Status loading={props.productsLoading} error={props.productsError} retry={props.retryProducts} />
      {!props.productsLoading && !props.productsError && <>{products?.items.length ? <ol className="divide-y divide-slate-100 dark:divide-slate-800">{products.items.slice(0, 5).map((product, index) => <li key={product.product_id} className="flex items-center justify-between gap-3 py-2"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-900 dark:text-white" title={product.name}>{index + 1}. {product.name}</p><p className="mt-1 text-xs text-slate-500">{product.sku} · {product.share_pct}% del detalle de productos · Margen {product.margin_pct === null ? "restringido" : summary?.currency !== executive?.inventory_currency ? "sin equivalencia histórica" : product.has_zero_cost || Number(product.historical_cost || "0") <= 0 ? "por revisar" : `${product.margin_pct}%`}</p></div><strong className="shrink-0 text-sm tabular-nums text-slate-900 dark:text-white">{formatMoney(product.revenue)}</strong></li>)}</ol> : <p className="text-sm text-slate-500">Sin ventas de productos en este período.</p>}{products?.coverage && <p className="mt-2 flex items-center gap-1 text-[11px] text-slate-500">Detalle de producto en {products.coverage.percent ?? "—"}% de la facturación · {products.coverage.documents_without_detail} {products.coverage.documents_without_detail === 1 ? "documento sin detalle" : "documentos sin detalle"} ({formatMoney(products.coverage.amount_without_detail)})</p>}</>}
    </Card>}
    {visible.customers && <Card title="Clientes y concentración" help="Nuevo: sin compras anteriores al inicio del período. Recurrente: con compras anteriores. En todo el historial se distingue una compra de varias. Consumidor final se muestra aparte y no cuenta como nuevo ni recurrente. La concentración del 20% describe dependencia de clientes; no es una meta." subtitle="Compradores del período y dependencia de la cartera" action={link("Ver clientes", "customer_analytics")}>
      <Status loading={props.customersLoading} error={props.customersError} retry={props.retryCustomers} />
      {!props.customersLoading && !props.customersError && (customers ? <><div className="grid grid-cols-2 gap-3 text-center sm:grid-cols-4"><div><strong className="text-xl text-slate-900 dark:text-white">{customers.summary.active_in_period}</strong><p className="text-xs text-slate-500">Con compras</p></div><div><strong className="text-xl text-slate-900 dark:text-white">{customers.summary.new_customers_count}</strong><p className="text-xs text-slate-500">Nuevos</p></div><div><strong className="text-xl text-slate-900 dark:text-white">{customers.summary.recurring_customers_count}</strong><p className="text-xs text-slate-500">Recurrentes</p></div><div><strong className="text-xl text-slate-900 dark:text-white">{customers.summary.final_consumers_count ?? 0}</strong><p className="text-xs text-slate-500">Consumidor final</p></div></div><p className="mt-4 rounded-xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-600 dark:bg-slate-950 dark:text-slate-400">El 20% de compradores con mayor facturación concentra el <strong>{customers.summary.top_20_concentration_pct}%</strong> de las ventas.</p><ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">{customers.items.slice(0, 3).map(customer => <li key={customer.customer_id} className="flex justify-between gap-3 py-2 text-sm"><span className="min-w-0"><span className="block truncate text-slate-700 dark:text-slate-300" title={customer.legal_name}>{customer.legal_name}</span><span className="block text-[11px] text-slate-500">{customer.code}</span></span><strong className="shrink-0 tabular-nums text-slate-900 dark:text-white">{formatMoney(customer.total_revenue)}</strong></li>)}</ul></> : <p className="text-sm text-slate-500">Sin información de clientes.</p>)}
    </Card>}
    {visible.sellers && <Card title="Contribución del equipo comercial · Top 3" help="Los tres vendedores con mayor facturación del período. Las metas mensuales se consultan en Equipo y comisiones." action={link("Ver equipo y comisiones", "team")}>
      <Status loading={props.sellersLoading} error={props.sellersError} retry={props.retrySellers} />
      {!props.sellersLoading && !props.sellersError && (sellers ? <><ol className="divide-y divide-slate-100 dark:divide-slate-800">{sellers.items.filter(seller => Number(seller.total_revenue) > 0).sort((left, right) => Number(right.total_revenue) - Number(left.total_revenue)).slice(0, 3).map(seller => <li key={seller.seller_id} className="flex justify-between gap-3 py-2"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-900 dark:text-white">{seller.seller_name}{seller.is_active === false ? " (inactivo)" : ""}</p><p className="text-xs text-slate-500" title={seller.identifier || seller.seller_id}>{(seller.identifier || seller.seller_id).slice(0, 8)} · {seller.sales_count} {seller.sales_count === 1 ? "documento" : "documentos"}</p></div><strong className="shrink-0 text-sm tabular-nums text-slate-900 dark:text-white">{formatMoney(seller.total_revenue)}</strong></li>)}</ol><p className="mt-3 rounded-xl bg-slate-50 p-3 text-xs text-slate-600 dark:bg-slate-950 dark:text-slate-400">Sin vendedor asignado: <strong>{formatMoney(sellers.unassigned.total_revenue)}</strong> en {sellers.unassigned.sales_count} {sellers.unassigned.sales_count === 1 ? "documento" : "documentos"}.</p>{sellers.categories && <details className="mt-2 text-xs text-slate-500"><summary className="cursor-pointer font-medium">Atribución completa y conciliación</summary><dl className="mt-2 space-y-1">{Object.entries(sellers.categories).map(([key, row]) => <div className="flex justify-between gap-2" key={key}><dt>{sellerCategoryNames[key] || key} · {row.sales_count} {row.sales_count === 1 ? "documento" : "documentos"}</dt><dd>{formatMoney(row.total_revenue)}</dd></div>)}</dl></details>}</> : <p className="text-sm text-slate-500">Sin información del equipo.</p>)}
    </Card>}
    {visible.inventory && <Card title="Inventario actual" help={`Existencias actuales al costo promedio registrado, en moneda base. ${executive?.inventory.cost_coverage ? `Valorado en ${executive.inventory.cost_coverage.valued_products} de ${executive.inventory.cost_coverage.products_with_stock} productos con stock. ` : ""}Sin disponibilidad: stock agregado disponible menor o igual a cero; excluye productos sin registros de existencias.`} action={link("Revisar inventario", "inventory", "inventory", executive?.inventory.out_of_stock ?? undefined)}>
      {executive?.inventory.status === "restricted" ? <p className="text-sm text-slate-500">Requiere permiso de lectura de inventario.</p> : executive?.inventory.status === "inactive" ? <p className="text-sm text-slate-500">El área de inventario está desactivada.</p> : <><div className="grid gap-3 sm:grid-cols-2"><div><p className="text-xs text-slate-500">Valor de existencias · {inventoryCurrency}</p><strong className="mt-1 block text-2xl text-slate-900 dark:text-white">{valuation}</strong>{executive?.inventory.cost_coverage?.status === "review" && <span className="mt-1 block text-xs font-semibold text-amber-600 dark:text-amber-400">Por revisar</span>}</div><div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950"><strong className="text-xl text-slate-900 dark:text-white">{executive?.inventory.out_of_stock ?? "—"}</strong><span className="ml-2 text-sm text-slate-600 dark:text-slate-400">productos sin disponibilidad</span></div></div>{executive?.inventory.preview?.length ? <ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">{executive.inventory.preview.map(product => <li key={product.id} className="flex justify-between gap-2 py-2 text-sm"><span>{product.nombre}</span><span className="text-xs text-slate-500">{product.sku}</span></li>)}</ul> : null}{executive?.drilldowns?.inventory && <button type="button" className="mt-2 text-xs font-semibold text-teal-700 dark:text-teal-400" onClick={() => navigate("inventory", "inventory", executive.inventory.out_of_stock ?? undefined)}>Ver todos →</button>}</>}
    </Card>}
  </section>;
}
