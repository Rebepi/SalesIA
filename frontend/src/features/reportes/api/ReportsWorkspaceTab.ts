import { apiClient } from "../../../api/client";
import { ReportScheduleConfig } from "../components/ReportScheduleBuilder";
import { ReportTemplate } from "../types/ReportsWorkspaceTab";
import { ReportRunItem } from "../types/ReportsWorkspaceTab";
import { ReportScheduleItem } from "../types/ReportsWorkspaceTab";
import { ReportPreviewData } from "../types/ReportsWorkspaceTab";
import { ReportComparisonResult } from "../types/ReportsWorkspaceTab";
import { CorporateBranding } from "../types/ReportsWorkspaceTab";
import { CollectionResponse } from "../types/ReportsWorkspaceTab";

export function solicitarLoadData() {
  return apiClient.request<CollectionResponse<ReportTemplate>>("/api/v1/reports");
}

export function solicitarLoadData2() {
  return apiClient.request<CollectionResponse<ReportRunItem>>("/api/v1/report-runs");
}

export function solicitarLoadData3() {
  return apiClient.request<CollectionResponse<ReportScheduleItem>>("/api/v1/report-schedules");
}

export function solicitarLoadData4() {
  return apiClient.request<CorporateBranding>("/api/v1/reports/branding");
}

export function solicitarLoadData5() {
  return apiClient.request<{ base_currency: string }>("/api/v1/companies/current");
}

export function solicitarDatos() {
  return apiClient.request<CollectionResponse<ReportRunItem>>("/api/v1/report-runs");
}

export function solicitarHandleOpenPreview({ template }: { template: ReportTemplate }) {
  return apiClient.request<ReportPreviewData>(`/api/v1/reports/preview?template_code=${template.code}`);
}

export function solicitarHandleLaunchReport({ payload }: { payload: Record<string, unknown> }) {
  return apiClient.request<ReportRunItem>("/api/v1/report-runs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function solicitarHandleCancelRun({ runId }: { runId: string }) {
  return apiClient.request(`/api/v1/report-runs/${runId}/cancel`, { method: "POST" });
}

export function solicitarHandleRetryRun({ runId }: { runId: string }) {
  return apiClient.request<ReportRunItem>(`/api/v1/report-runs/${runId}/retry`, { method: "POST" });
}

export function solicitarHandleCreateSchedule({ schedTemplateCode, schedConfig, schedTimezone, schedFormat, emailsList }: { schedTemplateCode: string; schedConfig: ReportScheduleConfig; schedTimezone: string; schedFormat: string; emailsList: string[] }) {
  return apiClient.request("/api/v1/report-schedules", {
    method: "POST",
    body: JSON.stringify({
      report_type: schedTemplateCode,
      schedule: schedConfig,
      timezone: schedTimezone,
      format: schedFormat,
      recipients: emailsList
    })
  });
}

export function solicitarHandleDeleteSchedule({ scheduleId }: { scheduleId: string }) {
  return apiClient.request(`/api/v1/report-schedules/${scheduleId}`, { method: "DELETE" });
}

export function solicitarHandleExecuteScheduleNow({ scheduleId }: { scheduleId: string }) {
  return apiClient.request<ReportRunItem>(`/api/v1/report-schedules/${scheduleId}/execute`, { method: "POST" });
}

export function solicitarHandleCompareRuns({ compareRunA, compareRunB }: { compareRunA: string; compareRunB: string }) {
  return apiClient.request<ReportComparisonResult>("/api/v1/reports/compare", {
    method: "POST",
    body: JSON.stringify({
      run_id_1: compareRunA,
      run_id_2: compareRunB
    })
  });
}
