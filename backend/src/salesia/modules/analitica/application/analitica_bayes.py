from salesia.modules.analitica.application.contracts.probabilidad_bayes import BayesCalculationRequest
from salesia.modules.analitica.application.probabilidad_bayes import post_probability_bayes


def post_analytics_bayes_compat(payload: BayesCalculationRequest):
    return post_probability_bayes(payload)
