from salesia.modules.analitica.application.contracts.experimentos import ABExperimentRequest
from salesia.modules.analitica.domain.advanced import evaluate_ab_experiment


def post_ab_test(payload: ABExperimentRequest):
    return evaluate_ab_experiment(payload.events, is_randomized=payload.is_randomized)
