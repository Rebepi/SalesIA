import { SeccionReportesCorporativosYMultiformato } from "../sections/ReportsWorkspaceTab/SeccionReportesCorporativosYMultiformato";
import { SeccionCatalog } from "../sections/ReportsWorkspaceTab/SeccionCatalog";
import { SeccionRuns } from "../sections/ReportsWorkspaceTab/SeccionRuns";
import { SeccionSchedules } from "../sections/ReportsWorkspaceTab/SeccionSchedules";
import { SeccionCompare } from "../sections/ReportsWorkspaceTab/SeccionCompare";
import { SeccionVistaPrevia } from "../sections/ReportsWorkspaceTab/SeccionVistaPrevia";
import { SeccionGenerar } from "../sections/ReportsWorkspaceTab/SeccionGenerar";
import { SeccionNuevaProgramacionDeReporte } from "../sections/ReportsWorkspaceTab/SeccionNuevaProgramacionDeReporte";
import { SeccionVistaDeImpresionOficial } from "../sections/ReportsWorkspaceTab/SeccionVistaDeImpresionOficial";
import { useReportsWorkspaceTab } from "../hooks/useReportsWorkspaceTab";


export function ReportsWorkspaceTab({ canExport = false }: { canExport?: boolean }) {
  const { ConfirmDialogNode, activeTab, setActiveTab, templates, runs, schedules, branding, loading, catalogSearch, setCatalogSearch, selectedArea, setSelectedArea, previewTemplate, setPreviewTemplate, previewData, loadingPreview, launchModalTemplate, setLaunchModalTemplate, launchFormat, setLaunchFormat, launchCurrency, setLaunchCurrency, launchStartDate, setLaunchStartDate, launchEndDate, setLaunchEndDate, launchStatus, setLaunchStatus, launching, createScheduleModal, setCreateScheduleModal, schedTemplateCode, setSchedTemplateCode, schedConfig, setSchedConfig, schedTimezone, setSchedTimezone, schedFormat, setSchedFormat, schedEmails, setSchedEmails, creatingSchedule, compareRunA, setCompareRunA, compareRunB, setCompareRunB, comparisonResult, comparing, favoriteTemplates, setFavoriteTemplates, onlyFavorites, setOnlyFavorites, printableRun, setPrintableRun, loadData, handleOpenPreview, handleOpenLaunch, handleLaunchReport, handleDownloadRun, handleCancelRun, handleRetryRun, handleCreateSchedule, handleDeleteSchedule, handleExecuteScheduleNow, handleCompareRuns, areas, filteredTemplates, isExpired } = useReportsWorkspaceTab({ canExport });
  return (
    <div id="scr-041-reports-workspace" data-testid="scr-041-reports-workspace" className="space-y-6">
      <SeccionReportesCorporativosYMultiformato branding={branding} setActiveTab={setActiveTab} activeTab={activeTab} templates={templates} runs={runs} schedules={schedules} />

      {activeTab === "catalog" && (
        <SeccionCatalog catalogSearch={catalogSearch} setCatalogSearch={setCatalogSearch} areas={areas} setSelectedArea={setSelectedArea} selectedArea={selectedArea} onlyFavorites={onlyFavorites} setOnlyFavorites={setOnlyFavorites} filteredTemplates={filteredTemplates} templates={templates} favoriteTemplates={favoriteTemplates} setFavoriteTemplates={setFavoriteTemplates} handleOpenPreview={handleOpenPreview} canExport={canExport} handleOpenLaunch={handleOpenLaunch} />
      )}

      {activeTab === "runs" && (
        <SeccionRuns loadData={loadData} loading={loading} runs={runs} isExpired={isExpired} canExport={canExport} handleDownloadRun={handleDownloadRun} setPrintableRun={setPrintableRun} handleCancelRun={handleCancelRun} handleRetryRun={handleRetryRun} />
      )}

      {activeTab === "schedules" && (
        <SeccionSchedules loadData={loadData} canExport={canExport} setCreateScheduleModal={setCreateScheduleModal} schedules={schedules} handleExecuteScheduleNow={handleExecuteScheduleNow} handleDeleteSchedule={handleDeleteSchedule} />
      )}

      {activeTab === "compare" && (
        <SeccionCompare compareRunA={compareRunA} setCompareRunA={setCompareRunA} runs={runs} compareRunB={compareRunB} setCompareRunB={setCompareRunB} handleCompareRuns={handleCompareRuns} canExport={canExport} comparing={comparing} comparisonResult={comparisonResult} />
      )}

      {previewTemplate && (
        <SeccionVistaPrevia previewTemplate={previewTemplate} setPreviewTemplate={setPreviewTemplate} loadingPreview={loadingPreview} previewData={previewData} handleOpenLaunch={handleOpenLaunch} />
      )}

      {launchModalTemplate && (
        <SeccionGenerar launchModalTemplate={launchModalTemplate} setLaunchModalTemplate={setLaunchModalTemplate} launchFormat={launchFormat} setLaunchFormat={setLaunchFormat} launchCurrency={launchCurrency} setLaunchCurrency={setLaunchCurrency} launchStartDate={launchStartDate} setLaunchStartDate={setLaunchStartDate} launchEndDate={launchEndDate} setLaunchEndDate={setLaunchEndDate} launchStatus={launchStatus} setLaunchStatus={setLaunchStatus} handleLaunchReport={handleLaunchReport} launching={launching} />
      )}

      {createScheduleModal && (
        <SeccionNuevaProgramacionDeReporte setCreateScheduleModal={setCreateScheduleModal} schedTemplateCode={schedTemplateCode} setSchedTemplateCode={setSchedTemplateCode} templates={templates} schedConfig={schedConfig} setSchedConfig={setSchedConfig} schedTimezone={schedTimezone} setSchedTimezone={setSchedTimezone} schedFormat={schedFormat} setSchedFormat={setSchedFormat} schedEmails={schedEmails} setSchedEmails={setSchedEmails} handleCreateSchedule={handleCreateSchedule} creatingSchedule={creatingSchedule} />
      )}

      {printableRun && (
        <SeccionVistaDeImpresionOficial setPrintableRun={setPrintableRun} branding={branding} printableRun={printableRun} />
      )}
      {ConfirmDialogNode}
    </div>
  );
}
