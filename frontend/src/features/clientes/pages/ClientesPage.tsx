import { IconAction } from "../../../ui/components/primitives/IconAction";
import { Download, FileText, Pencil, Plus, RefreshCw, Search, Trash2 } from "lucide-react";
import { TablePagination } from "../../../ui/components/TablePagination";
import { setDefaultPageSize as persistDefaultPageSize } from "../../../ui/preferences";
import { buttonStyle, iconStyle, primaryButtonStyle } from "../components/estilosListado";
import "../clientes.css";
import { useExportarClientes } from "../hooks/useExportarClientes";
import type { Row } from "../types/clientes";
interface ClientesPageProps {
  rows: Row[];
  total: number;
  loading: boolean;
  search: string;
  page: number;
  pageSize: number;
  error: string;
  editorOpen: boolean;
  confirmationOpen: boolean;
  canWrite: boolean;
  setSearch: (value: string) => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  onRefresh: () => void;
  openEntity: (row?: Row) => void;
  setSelectedCustomer: (row: Row) => void;
  setConfirm: (value: { title: string; text: string; path: string; body: Record<string, unknown> }) => void;
}
const columnas = [["code", "Código"], ["legal_name", "Cliente"], ["doc_number", "Documento"], ["current_balance", "Saldo"], ["is_active", "Activo"]];
export function ClientesPage({ rows, total, loading, search, page, pageSize, error, editorOpen, confirmationOpen, canWrite, setSearch, setPage, setPageSize, onRefresh, openEntity, setSelectedCustomer, setConfirm }: ClientesPageProps) {
  const { exportingCustomers, exportar } = useExportarClientes();
  return (<section className="space-y-5">

    <div className="workspace-list-toolbar workspace-toolbar-card flex flex-wrap items-center justify-between gap-3">

      <div className="relative">

        {(<>

          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />

          <input aria-label="Buscar por nombre o código" placeholder="Buscar por nombre o código" value={search} onChange={event => { setSearch(event.target.value); setPage(0); }} className="w-full sm:w-72 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 py-2 pl-10 pr-3 text-sm outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/15" />

        </>)}

      </div>

      <div className="flex flex-wrap gap-2">

        <IconAction label="Actualizar lista" tone="neutral" onClick={() => onRefresh()} disabled={loading} aria-label="Actualizar"><RefreshCw className={`${iconStyle} ${loading ? "motion-safe:animate-spin" : "motion-safe:group-hover:rotate-90"}`} /></IconAction>

        {(<button className={buttonStyle} disabled={exportingCustomers} onClick={exportar}>

          <Download className={`${iconStyle} ${exportingCustomers ? "animate-pulse" : ""}`} /> {exportingCustomers ? "Preparando descarga…" : "Exportar cartera"}

        </button>)}





        {canWrite && (<button className={primaryButtonStyle} onClick={() => openEntity()}>

          <Plus className={iconStyle} /> Crear cliente

        </button>)}







      </div>

    </div>



    {error && !editorOpen && !confirmationOpen && <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">{error}</p>}



    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">

      <div className="table-scroll-region customers-table-scroll" tabIndex={0} role="region" aria-label="Listado de clientes con desplazamiento">
        <table className="customers-table w-full text-left text-sm">
          <caption className="sr-only">Clientes</caption>
          <colgroup><col style={{ width: "17%" }} /><col style={{ width: "27%" }} /><col style={{ width: "16%" }} /><col style={{ width: "13%" }} /><col style={{ width: "9%" }} /><col style={{ width: "18%" }} /></colgroup>
          <thead className="bg-slate-100 text-xs uppercase text-slate-500">
            <tr>
              {columnas.map(([key, label]) => <th key={key} scope="col" className={`px-5 py-4 ${key === "current_balance" ? "text-right" : key === "is_active" ? "text-center" : ""}`}>{label}</th>)}
              <th scope="col" className="px-5 py-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && <tr><td colSpan={6} role="status" className="p-12 text-center">Cargando registros…</td></tr>}
            {!loading && rows.length === 0 && <tr><td colSpan={6} className="p-12 text-center">No hay registros para mostrar.</td></tr>}

            {!loading && rows.map((row, index) => (<tr key={String(row.id ?? row.sale_id ?? row.session_id ?? index)} className="transition hover:bg-slate-50">

              {columnas?.map(([key]) => (<td key={key} className={`truncate px-5 py-4 tabular-nums ${key === "current_balance" ? "text-right" : key === "is_active" ? "text-center" : ""}`} title={String(row[key] ?? "")}>

                {typeof row[key] === "boolean" ? (row[key] ? "Sí" : "No") : key === "current_balance" ? (row[key] === null ? "Restringido" : Number(row[key] ?? 0).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })) : String(row[key] ?? "—")}

              </td>))}

              <td className="px-5 py-4">

                <div className="flex justify-end gap-2">

                  {(<IconAction label="Ficha comercial completa" tone="neutral" aria-label={`Ficha de ${row.legal_name}`} onClick={() => setSelectedCustomer(row)}><FileText className="h-4 w-4" /></IconAction>)}



                  {(canWrite) && (<>

                    <IconAction label="Editar" tone="primary" onClick={() => openEntity(row)} aria-label={`Editar ${row.legal_name ?? row.name}`}><Pencil className="h-4 w-4" /></IconAction>

                    <IconAction label={row.is_active ? "Archivar" : "Restaurar"} tone="danger" aria-label={row.is_active ? "Archivar registro" : "Restaurar registro"} onClick={() => setConfirm({ title: row.is_active ? "Archivar registro" : "Restaurar registro", text: row.is_active ? "El registro dejará de estar disponible para nuevas operaciones. Su historial se conserva." : "El registro volverá a estar disponible para nuevas operaciones.", path: `/api/v1/${"customers"}/${row.id}/${row.is_active ? "archive" : "restore"}`, body: {} })}><Trash2 className="h-4 w-4" /></IconAction>

                  </>)}















                </div>

              </td>

            </tr>))}

          </tbody>
        </table>
      </div>



    </div>

    <TablePagination page={page} pageSize={pageSize} total={total} loading={loading} onPageChange={setPage} onPageSizeChange={size => { setPageSize(size); persistDefaultPageSize(size); setPage(0); }} />

  </section>);
}
