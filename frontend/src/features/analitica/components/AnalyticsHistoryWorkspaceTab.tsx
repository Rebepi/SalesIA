import "./analytics-history.css";
import { useId } from "react";
import { Panel1 } from "../sections/AnalyticsHistoryWorkspaceTab/Panel1";
import { SeccionComparativaLadoALadoDe } from "../sections/AnalyticsHistoryWorkspaceTab/SeccionComparativaLadoALadoDe";
export type { AnalyticsExecutionRun, AnalyticsHistoryWorkspaceTabProps } from "../types/AnalyticsHistoryWorkspaceTab";
import { useAnalyticsHistoryWorkspaceTab } from "../hooks/useAnalyticsHistoryWorkspaceTab";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { TablePagination } from "../../../ui/components/TablePagination";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { GitCompare, RefreshCw } from "lucide-react";
import { AnalyticsRunDetails } from "./AnalyticsRunDetails";
import type { AnalyticsHistoryWorkspaceTabProps } from "../types/AnalyticsHistoryWorkspaceTab";
export function AnalyticsHistoryWorkspaceTab({ canWrite = true }: AnalyticsHistoryWorkspaceTabProps) {
  const state = useAnalyticsHistoryWorkspaceTab({ canWrite });
  const title = useId();
  const { runs, loading, error, actionError, notice, selectedForCompare, compareModalOpen, setCompareModalOpen, repeatingId, handleRepeatRun, toggleSelectForCompare, runA, runB, clearSelection, refresh, status, setStatus, page, setPage, pageSize, setPageSize, total, detailRun, detailLoading, detailError, showDetail, closeDetail } = state;
  return <div id="scr-040-analytics-history" data-testid="scr-040-analytics-history" className="analytics-history space-y-5">
    <section className="analytics-history-toolbar"><div><h2>Ejecuciones guardadas</h2><p>Selecciona dos registros para comparar sus resultados. Repetir crea una ejecución nueva sobre el dataset conservado.</p></div><div className="analytics-history-controls"><label>Estado<CustomSelect value={status} onChange={event => { setStatus(event.target.value); setPage(0); }}><option value="">Todos los estados</option><option value="completed">Completados</option><option value="processing">En proceso</option><option value="failed">Fallidos</option><option value="cancelled">Cancelados</option></CustomSelect></label><button type="button" onClick={refresh} disabled={loading}><RefreshCw size={16} />Actualizar</button></div></section>
    <div className="analytics-history-selection"><span role="status">{selectedForCompare.length} de 2 ejecuciones seleccionadas</span><div>{selectedForCompare.length > 0 && <button type="button" onClick={clearSelection}>Limpiar selección</button>}<button type="button" className="analytics-history-primary" disabled={selectedForCompare.length !== 2} onClick={() => setCompareModalOpen(true)}><GitCompare size={16} />Comparar ejecuciones</button></div></div>
    {notice && <p role="status" className="analytics-history-notice">{notice}</p>}{actionError && <p role="alert" className="analytics-history-warning">{actionError}</p>}
    {loading && <p role="status">Cargando historial analítico…</p>}
    {error ? <div role="alert" className="analytics-history-warning"><p>No se pudo cargar el historial: {error}</p><button type="button" onClick={refresh}>Reintentar</button></div> : <Panel1 runs={runs} selectedForCompare={selectedForCompare} toggleSelectForCompare={toggleSelectForCompare} canWrite={canWrite} repeatingId={repeatingId} handleRepeatRun={handleRepeatRun} showDetail={showDetail} />}
    {!loading && !error && runs.length === 0 && <p className="analytics-history-empty">{status ? "No hay ejecuciones con este estado." : "Todavía no existen ejecuciones analíticas. Guarda un análisis desde Estadística para verlo aquí."}</p>}
    <TablePagination page={page} pageSize={pageSize} total={total} loading={loading} onPageChange={setPage} onPageSizeChange={size => { setPageSize(size); setPage(0); }} />
    {compareModalOpen && runA && runB && <SeccionComparativaLadoALadoDe setCompareModalOpen={setCompareModalOpen} runA={runA} runB={runB} />}
    {detailRun && <ModalSurface labelledBy={title} onClose={closeDetail} className="analytics-history-modal"><section className="analytics-history-dialog"><header><h2 id={title}>{detailRun.code}</h2><button type="button" onClick={closeDetail}>Cerrar detalle</button></header><div className="analytics-history-dialog-body">{detailLoading && <p role="status">Cargando detalle…</p>}{detailError && <div role="alert" className="analytics-history-warning"><p>{detailError}</p><button type="button" onClick={() => void showDetail(detailRun)}>Reintentar detalle</button></div>}<AnalyticsRunDetails run={detailRun} /></div></section></ModalSurface>}
  </div>;
}
