import { apiClient } from "../../../api/client";
import { ProbabilityResponse } from "../types/ProbabilityWorkspaceTab";
import { BayesResponse } from "../types/ProbabilityWorkspaceTab";
import { HypothesisResponse } from "../types/ProbabilityWorkspaceTab";
import { SavedAnalysis } from "../types/ProbabilityWorkspaceTab";

export function solicitarLoadAnalyses() {
  return apiClient.request<SavedAnalysis[]>("/api/v1/probability/analyses");
}

export function solicitarCalculateEmpirical({ sampleSpace, eventACount, eventBCount, intersectionCount, entityUniverse, period }: { sampleSpace: number; eventACount: number; eventBCount: number; intersectionCount: number; entityUniverse: "customers" | "sales"; period: string }) {
  return apiClient.request<ProbabilityResponse>("/api/v1/probability/events", {
    method: "POST",
    body: JSON.stringify({
      sample_space_size: sampleSpace,
      event_a_count: eventACount,
      event_b_count: eventBCount,
      intersection_count: intersectionCount,
      universe_definition: {
        entity: entityUniverse,
        period: period
      }
    })
  });
}

export function solicitarCalculateEmpirical2({ sampleSpace, eventACount, eventBCount, intersectionCount, smoothingEnabled, alphaVal }: { sampleSpace: number; eventACount: number; eventBCount: number; intersectionCount: number; smoothingEnabled: boolean; alphaVal: string }) {
  return apiClient.request<BayesResponse>("/api/v1/probability/bayes", {
    method: "POST",
    body: JSON.stringify({
      sample_space_size: sampleSpace,
      event_a_count: eventACount,
      event_b_count: eventBCount,
      intersection_count: intersectionCount,
      smoothing_enabled: smoothingEnabled,
      alpha: alphaVal
    })
  });
}

export function solicitarCalculateManual({ numberMode, priorA, likelihoodA, evidenceB, smoothingEnabled, alphaVal }: { numberMode: "proportion" | "percentage"; priorA: string; likelihoodA: string; evidenceB: string; smoothingEnabled: boolean; alphaVal: string }) {
  return apiClient.request<BayesResponse>("/api/v1/probability/bayes", {
    method: "POST",
    body: JSON.stringify({
      mode: numberMode,
      prior_a: priorA,
      likelihood_b_given_a: likelihoodA,
      evidence_b: evidenceB,
      smoothing_enabled: smoothingEnabled,
      alpha: alphaVal
    })
  });
}

export function solicitarRunHypothesisTest({ htCount1, htTotal1, htCount2, htTotal2 }: { htCount1: number; htTotal1: number; htCount2: number; htTotal2: number }) {
  return apiClient.request<HypothesisResponse>("/api/v1/probability/hypothesis-test", {
    method: "POST",
    body: JSON.stringify({
      count_1: htCount1,
      total_1: htTotal1,
      count_2: htCount2,
      total_2: htTotal2,
      confidence_level: "0.95"
    })
  });
}

export function solicitarSaveAnalysis({ payload }: { payload: { name: string; mode: "proportion" | "percentage"; counts: { sample_space_size: number; event_a: number; event_b: number; intersection: number; }; probabilities: { prior_a: string; likelihood_b_given_a: string; evidence_b: string; posterior_a_given_b: string; } | { prior_a?: undefined; likelihood_b_given_a?: undefined; evidence_b?: undefined; posterior_a_given_b?: undefined; }; smoothing_enabled: boolean; alpha: string; is_simulation: boolean; scenario_type: string; } }) {
  return apiClient.request("/api/v1/probability/analyses", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function solicitarDuplicateAsSimulation({ baseId, newName, numberMode }: { baseId: string; newName: string; numberMode: "proportion" | "percentage" }) {
  return apiClient.request(`/api/v1/probability/analyses/${baseId}/duplicate-scenario`, {
    method: "POST",
    body: JSON.stringify({
      scenario_name: newName,
      modified_prior_a: numberMode === "percentage" ? "35" : "0.350000",
      modified_likelihood_b_given_a: numberMode === "percentage" ? "45" : "0.450000"
    })
  });
}

export function solicitarRunComparison({ selectedComp1, selectedComp2 }: { selectedComp1: string; selectedComp2: string }) {
  return apiClient.request("/api/v1/probability/scenarios/compare", {
    method: "POST",
    body: JSON.stringify({
      analysis_id_1: selectedComp1,
      analysis_id_2: selectedComp2
    })
  });
}

export interface LiveCountsResponse {
  entity: string;
  period: string;
  condition_a: string;
  condition_b: string;
  sample_space_size: number;
  event_a_count: number;
  event_b_count: number;
  intersection_count: number;
}

export function solicitarLiveCounts({
  entity,
  period,
  conditionA,
  conditionB,
  thresholdAmount,
}: {
  entity: "sales" | "customers";
  period: string;
  conditionA: string;
  conditionB: string;
  thresholdAmount: string;
}) {
  return apiClient.request<LiveCountsResponse>("/api/v1/probability/live-counts", {
    method: "POST",
    body: JSON.stringify({
      entity,
      period,
      condition_a: conditionA,
      condition_b: conditionB,
      threshold_amount: thresholdAmount,
    }),
  });
}

