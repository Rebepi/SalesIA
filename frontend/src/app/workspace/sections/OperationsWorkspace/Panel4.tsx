import { IconAction } from "../../../../ui/components/primitives/IconAction";
import type { useOperationsWorkspace } from "../../hooks/useOperationsWorkspace";
import { TablePagination } from "../../../../ui/components/TablePagination";
import { CreditCard, FileText, LogOut, Pencil, Plus, RefreshCw, RotateCcw, Search, ShieldCheck, Trash2 } from "lucide-react";
import { apiClient } from "../../../../api/client";
import { SaleDetailData } from "../../../../features/ventas/components/SaleDetailModal";
import { setDefaultPageSize as persistDefaultPageSize } from "../../../../ui/preferences";
import { primaryButtonStyle } from "../../support/OperationsWorkspace";
import { buttonStyle } from "../../support/OperationsWorkspace";
import { iconStyle } from "../../support/OperationsWorkspace";
import { iconStyleSm } from "../../support/OperationsWorkspace";
import { sections } from "../../support/OperationsWorkspace";
import { message } from "../../support/OperationsWorkspace";

export function Panel4({ view, loading, total, search, setSearch, setPage, setRevision, can, setEditor, setProductDialogOpen, busy, setPosInitialCustomerId, setPosSourceSaleId, setPosModalOpen, error, editor, confirm, columns, rows, setSelectedProduct, openEntity, setConfirm, setSaleDetailModalSale, setActiveReturnSale, toast, page, pageSize, setPageSize }: { view: ReturnType<typeof useOperationsWorkspace>["view"]; loading: ReturnType<typeof useOperationsWorkspace>["loading"]; total: ReturnType<typeof useOperationsWorkspace>["total"]; search: ReturnType<typeof useOperationsWorkspace>["search"]; setSearch: ReturnType<typeof useOperationsWorkspace>["setSearch"]; setPage: ReturnType<typeof useOperationsWorkspace>["setPage"]; setRevision: ReturnType<typeof useOperationsWorkspace>["setRevision"]; can: ReturnType<typeof useOperationsWorkspace>["can"]; setEditor: ReturnType<typeof useOperationsWorkspace>["setEditor"]; setProductDialogOpen: ReturnType<typeof useOperationsWorkspace>["setProductDialogOpen"]; busy: ReturnType<typeof useOperationsWorkspace>["busy"]; setPosInitialCustomerId: ReturnType<typeof useOperationsWorkspace>["setPosInitialCustomerId"]; setPosSourceSaleId: ReturnType<typeof useOperationsWorkspace>["setPosSourceSaleId"]; setPosModalOpen: ReturnType<typeof useOperationsWorkspace>["setPosModalOpen"]; error: ReturnType<typeof useOperationsWorkspace>["error"]; editor: ReturnType<typeof useOperationsWorkspace>["editor"]; confirm: ReturnType<typeof useOperationsWorkspace>["confirm"]; columns: ReturnType<typeof useOperationsWorkspace>["columns"]; rows: ReturnType<typeof useOperationsWorkspace>["rows"]; setSelectedProduct: ReturnType<typeof useOperationsWorkspace>["setSelectedProduct"]; openEntity: ReturnType<typeof useOperationsWorkspace>["openEntity"]; setConfirm: ReturnType<typeof useOperationsWorkspace>["setConfirm"]; setSaleDetailModalSale: ReturnType<typeof useOperationsWorkspace>["setSaleDetailModalSale"]; setActiveReturnSale: ReturnType<typeof useOperationsWorkspace>["setActiveReturnSale"]; toast: ReturnType<typeof useOperationsWorkspace>["toast"]; page: ReturnType<typeof useOperationsWorkspace>["page"]; pageSize: ReturnType<typeof useOperationsWorkspace>["pageSize"]; setPageSize: ReturnType<typeof useOperationsWorkspace>["setPageSize"] }) {
  return (<section className="space-y-5">

    <div className="workspace-list-toolbar workspace-toolbar-card flex flex-wrap items-center justify-between gap-3">

      {view !== "products" && <div className="flex w-full items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">

        <span>{sections.find(section => section.key === view)?.label}</span>

        <span aria-live="polite"><strong className="font-semibold tabular-nums text-slate-800 dark:text-slate-200">{loading ? "…" : total.toLocaleString("es-PE")}</strong> registros encontrados</span>

      </div>}

      <div className="relative">

        {["customers", "products"].includes(view) && (<>

          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />

          <input aria-label="Buscar por nombre o código" placeholder="Buscar por nombre o código" value={search} onChange={event => { setSearch(event.target.value); setPage(0); }} className="w-full sm:w-72 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 py-2 pl-10 pr-3 text-sm outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/15" />

        </>)}

      </div>

      <div className="flex flex-wrap gap-2">

        <IconAction label="Actualizar lista" tone="neutral" onClick={() => setRevision(value => value + 1)} disabled={loading} aria-label="Actualizar"><RefreshCw className={`${iconStyle} ${loading ? "motion-safe:animate-spin" : "motion-safe:group-hover:rotate-90"}`} /></IconAction>



        {view === "products" && can("products:write") && (<button className={buttonStyle} onClick={() => setEditor({ title: "Importación masiva de catálogo", path: "/api/v1/products/import", prepare: v => ({ items: JSON.parse(v.items_json) }), fields: [{ name: "items_json", label: "Catálogo en formato JSON", type: "text" }] })}>

          Importar catálogo

        </button>)}

        {view === "products" && can("products:write") && (<button className={buttonStyle} onClick={() => setEditor({ title: "Actualización masiva de precios", path: "/api/v1/products/bulk-prices", prepare: v => ({ percent_change: Number(v.percent_change || 0), reason: v.reason || "Ajuste masivo" }), fields: [{ name: "percent_change", label: "Variación porcentual (+10 para +10 %, -5 para -5 %)", type: "number" }, { name: "reason", label: "Motivo" }] })}>

          Precios en lote

        </button>)}



        {view === "products" && can("products:write") && (<button className={primaryButtonStyle} onClick={() => setProductDialogOpen(true)}>

          <Plus className={iconStyle} /> Crear producto

        </button>)}

        {view === "sales" && can("sales:write") && (<button className={primaryButtonStyle} disabled={busy} onClick={() => { setPosInitialCustomerId(undefined); setPosSourceSaleId(undefined); setPosModalOpen(true); }}>

          <Plus className={iconStyle} /> Nueva venta

        </button>)}

        {view === "security" && (<button className={buttonStyle} onClick={() => setEditor({ title: "Configurar MFA", fields: [{ name: "password", label: "Contraseña actual", type: "password" }], path: "/api/v1/auth/mfa/setup" })}>

          <ShieldCheck className={iconStyle} /> Configurar MFA

        </button>)}

      </div>

    </div>



    {error && !editor && !confirm && <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">{error}</p>}



    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">

      <div className="table-header-region">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">{sections.find(section => section.key === view)?.label}</caption>
          <thead className="bg-slate-100 text-xs uppercase text-slate-500">
            <tr>
              {columns[view]?.map(([key, label]) => <th key={key} scope="col" className="px-5 py-4">{label}</th>)}
              <th scope="col" className="px-5 py-4 text-right">Acciones</th>
            </tr>
          </thead>
        </table>
      </div>

      <div className="table-scroll-region" tabIndex={0} role="region" aria-label="Listado con desplazamiento">

        {loading && <p role="status" className="p-12 text-center text-sm text-slate-500">Cargando registros…</p>}
        {!loading && rows.length === 0 && <p className="p-12 text-center text-sm text-slate-500">No hay registros para mostrar.</p>}
        {!loading && rows.length > 0 && (
        <table className="w-full text-left text-sm">
          <tbody className="divide-y divide-slate-100">

            {rows.map((row, index) => (<tr key={String(row.id ?? row.sale_id ?? row.session_id ?? index)} className="transition hover:bg-slate-50">

              {columns[view]?.map(([key]) => (<td key={key} className="max-w-xs truncate px-5 py-4 tabular-nums" title={String(row[key] ?? "")}>

                {typeof row[key] === "boolean" ? (row[key] ? "Sí" : "No") : String(row[key] ?? "—")}

              </td>))}

              <td className="px-5 py-4">

                <div className="flex justify-end gap-2">



                  {view === "products" && (<IconAction label="Ficha comercial y variantes" tone="neutral" aria-label={`Ficha de ${row.name}`} onClick={() => setSelectedProduct(row)}><FileText className="h-4 w-4" /></IconAction>)}

                  {(view === "products" && can("products:write")) && (<>

                    <IconAction label="Editar" tone="primary" onClick={() => openEntity(row)} aria-label={`Editar ${row.legal_name ?? row.name}`}><Pencil className="h-4 w-4" /></IconAction>

                    <IconAction label={row.is_active ? "Archivar" : "Restaurar"} tone="danger" aria-label={row.is_active ? "Archivar registro" : "Restaurar registro"} onClick={() => setConfirm({ title: row.is_active ? "Archivar registro" : "Restaurar registro", text: row.is_active ? "El registro dejará de estar disponible para nuevas operaciones. Su historial se conserva." : "El registro volverá a estar disponible para nuevas operaciones.", path: `/api/v1/${view}/${row.id}/${row.is_active ? "archive" : "restore"}`, body: {} })}><Trash2 className="h-4 w-4" /></IconAction>

                  </>)}

                  {view === "sales" && (<IconAction label="Ver detalle completo" tone="neutral" onClick={() => setSaleDetailModalSale(row as unknown as SaleDetailData)}><FileText className="h-4 w-4" /></IconAction>)}

                  {view === "sales" && can("sales:write") && (<IconAction label="Repetir" tone="neutral" onClick={() => { setPosInitialCustomerId(undefined); setPosSourceSaleId(String(row.sale_id)); setPosModalOpen(true); }}><Plus className={iconStyleSm} /></IconAction>)}


                  {view === "sales" && row.status === "confirmed" && can("payments:write") && (<IconAction label="Cobrar" tone="primary" onClick={() => setEditor({ title: "Registrar cobro", path: "/api/v1/payments", values: { sale_id: row.sale_id, currency: row.currency }, fields: [{ name: "amount", label: "Importe", type: "number", value: String(Number(row.total_amount) - Number(row.paid_amount)) }, { name: "payment_method", label: "Método", options: [{ value: "CASH", label: "Efectivo" }, { value: "TRANSFER", label: "Transferencia" }] }, { name: "reference_code", label: "Referencia bancaria", optional: true }] })}><CreditCard className={iconStyleSm} /></IconAction>)}

                  {view === "sales" && ["confirmed", "paid"].includes(String(row.status)) && can("sales:write") && (<IconAction label="Iniciar devolución comercial" tone="neutral" aria-label="Devolver" onClick={() => setActiveReturnSale(row)}><RotateCcw className={iconStyleSm} /></IconAction>)}

                  {view === "sales" && ["draft", "confirmed"].includes(String(row.status)) && Number(row.paid_amount) === 0 && can("sales:cancel") && (<IconAction label="Anular venta" tone="danger" aria-label="Anular venta" onClick={() => setEditor({ title: "Anular venta", path: `/api/v1/sales/${row.sale_id}/cancel`, fields: [{ name: "reason", label: "Motivo de anulación" }] })}><Trash2 className="h-4 w-4" /></IconAction>)}

                  {view === "security" && (<IconAction label="Revocar" tone="danger" onClick={async () => {
                    try {
                      await apiClient.request(`/api/v1/auth/sessions/${row.session_id}`, { method: "DELETE" });
                      if (row.is_current)
                        apiClient.clearTokens();
                      else
                        setRevision(value => value + 1);
                    }
                    catch (failure) {
                      toast.error("No se pudo cerrar la sesión", message(failure));
                    }
                  }}><LogOut className={iconStyleSm} /></IconAction>)}

                </div>

              </td>

            </tr>))}

          </tbody>
        </table>
        )}

      </div>

    </div>

    <TablePagination page={page} pageSize={pageSize} total={total} loading={loading} onPageChange={setPage} onPageSizeChange={size => { setPageSize(size); persistDefaultPageSize(size); setPage(0); }} />

  </section>);
}
