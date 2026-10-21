export interface ContingencyTable {
  a_and_b: number;
  a_and_not_b: number;
  not_a_and_b: number;
  not_a_and_not_b: number;
  total_a: number;
  total_not_a: number;
  total_b: number;
  total_not_b: number;
  grand_total: number;
}

export interface FormulaCard {
  term: string;
  label: string;
  value: string;
  formula: string;
}

export interface ProbabilityResponse {
  is_defined: boolean;
  reason: string | null;
  sample_space_size: number;
  event_a_count: number;
  event_b_count: number;
  intersection_count: number;
  probability_a: string | null;
  probability_b: string | null;
  probability_intersection: string | null;
  probability_union: string | null;
  probability_complement_a: string | null;
  probability_complement_b: string | null;
  conditional_probability_a_given_b: string | null;
  conditional_probability_b_given_a: string | null;
  direction_labels: Record<string, string>;
  contingency_table: ContingencyTable | null;
  low_sample_warning: boolean;
  warning_message: string | null;
  causality_disclaimer: string;
}

export interface BayesResponse {
  sample_space_size?: number;
  mode?: string;
  prior_a: string;
  likelihood_b_given_a: string;
  likelihood_b_given_not_a: string;
  evidence_b: string;
  posterior_a_given_b: string;
  direct_count_posterior?: string;
  equivalence_verified?: boolean;
  smoothing_enabled?: boolean;
  smoothing_details?: {
    alpha: string;
    smoothed_likelihood_b_given_a: string;
    smoothed_likelihood_b_given_not_a: string;
    smoothed_evidence_b: string;
    smoothed_posterior_a_given_b: string;
    pseudocounts_applied: string;
  } | null;
  contingency_table?: ContingencyTable | null;
  formula_cards?: FormulaCard[];
  low_sample_warning?: boolean;
  warning_message?: string | null;
  interpretation?: string;
  causality_disclaimer: string;
}

export interface HypothesisResponse {
  test_type: string;
  h0_statement: string;
  h1_statement: string;
  sample_1_proportion: string;
  sample_2_proportion: string;
  difference: string;
  z_statistic: string;
  p_value: string;
  confidence_level: string;
  confidence_interval_diff_low: string;
  confidence_interval_diff_high: string;
  expected_value_group_1: string;
  expected_value_group_2: string;
  assumptions_met: boolean;
  decision: string;
  didactic_explanation: string;
}

export interface SavedAnalysis {
  id: string;
  name: string;
  is_simulation: boolean;
  scenario_type: string;
  simulation_label?: string;
  mode: string;
  counts: Record<string, number>;
  probabilities: Record<string, string>;
  created_at: string;
}
