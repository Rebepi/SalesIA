import * as transporte from "../api/ProbabilityWorkspaceTab";

import { useEffect, useState } from "react";



import { useToast } from "../../../ui/toast/ToastContext";

import { ProbabilityResponse } from "../types/ProbabilityWorkspaceTab";

import { BayesResponse } from "../types/ProbabilityWorkspaceTab";

import { HypothesisResponse } from "../types/ProbabilityWorkspaceTab";

import { SavedAnalysis } from "../types/ProbabilityWorkspaceTab";



export function useProbabilityWorkspaceTab() {

  const toast = useToast();



  const [activeMode, setActiveMode] = useState<"empirical" | "manual">("empirical");



  const [numberMode, setNumberMode] = useState<"proportion" | "percentage">("proportion");



  const [entityUniverse, setEntityUniverse] = useState<"sales" | "customers">("customers");



  const [period, setPeriod] = useState<string>("30d");



  const [sampleSpace, setSampleSpace] = useState<number>(1000);



  const [eventACount, setEventACount] = useState<number>(200);



  const [eventBCount, setEventBCount] = useState<number>(120);



  const [intersectionCount, setIntersectionCount] = useState<number>(60);



  const [priorA, setPriorA] = useState<string>("0.20");



  const [likelihoodA, setLikelihoodA] = useState<string>("0.30");



  const [evidenceB, setEvidenceB] = useState<string>("0.12");



  const [smoothingEnabled, setSmoothingEnabled] = useState<boolean>(false);



  const [alphaVal, setAlphaVal] = useState<string>("1.0");



  const [probResult, setProbResult] = useState<ProbabilityResponse | null>(null);



  const [bayesResult, setBayesResult] = useState<BayesResponse | null>(null);



  const [hypoResult, setHypoResult] = useState<HypothesisResponse | null>(null);



  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([]);



  const [analysisName, setAnalysisName] = useState<string>("");



  const [loading, setLoading] = useState<boolean>(false);



  const [errorMsg, setErrorMsg] = useState<string>("");



  const [htCount1, setHtCount1] = useState<number>(65);



  const [htTotal1, setHtTotal1] = useState<number>(100);



  const [htCount2, setHtCount2] = useState<number>(45);



  const [htTotal2, setHtTotal2] = useState<number>(100);



  const [selectedComp1, setSelectedComp1] = useState<string>("");



  const [selectedComp2, setSelectedComp2] = useState<string>("");



  const [compareResult, setCompareResult] = useState<any>(null);



  const [conditionA, setConditionA] = useState<string>("with_balance");



  const [conditionB, setConditionB] = useState<string>("high_amount");



  const [thresholdAmount, setThresholdAmount] = useState<string>("200");



  const [syncing, setSyncing] = useState<boolean>(false);



  useEffect(() => {

    loadAnalyses();

  }, []);



  async function loadAnalyses() {

    try {

      const data = await transporte.solicitarLoadAnalyses();

      setSavedAnalyses(data);

      if (data.length >= 2) {

        setSelectedComp1(data[0].id);

        setSelectedComp2(data[1].id);

      }

    } catch {

      setErrorMsg("");

    }

  }



  async function syncLiveCounts() {

    setSyncing(true);

    setErrorMsg("");

    try {

      const res = await transporte.solicitarLiveCounts({

        entity: entityUniverse,

        period,

        conditionA,

        conditionB,

        thresholdAmount,

      });

      setSampleSpace(res.sample_space_size);

      setEventACount(res.event_a_count);

      setEventBCount(res.event_b_count);

      setIntersectionCount(res.intersection_count);

      setActiveMode("empirical");

      toast.success(

        "Datos sincronizados",

        `Universo: ${res.sample_space_size} · A: ${res.event_a_count} · B: ${res.event_b_count} · A∩B: ${res.intersection_count}`

      );

    } catch (err: any) {

      setErrorMsg(err.detail || "No se pudieron obtener los conteos operacionales.");

    } finally {

      setSyncing(false);

    }

  }



  async function calculateEmpirical() {

    setLoading(true);

    setErrorMsg("");

    try {

      const probRes = await transporte.solicitarCalculateEmpirical({ sampleSpace, eventACount, eventBCount, intersectionCount, entityUniverse, period });

      setProbResult(probRes);



      if (sampleSpace > 0 && eventBCount > 0 && eventACount > 0) {

        const bayesRes = await transporte.solicitarCalculateEmpirical2({ sampleSpace, eventACount, eventBCount, intersectionCount, smoothingEnabled, alphaVal });

        setBayesResult(bayesRes);

      } else {

        setBayesResult(null);

      }

    } catch (err: any) {

      setErrorMsg(err.detail || "Error en el cálculo probabilístico empírico.");

    } finally {

      setLoading(false);

    }

  }



  async function calculateManual() {

    setLoading(true);

    setErrorMsg("");

    try {

      const bayesRes = await transporte.solicitarCalculateManual({ numberMode, priorA, likelihoodA, evidenceB, smoothingEnabled, alphaVal });

      setBayesResult(bayesRes);

    } catch (err: any) {

      setErrorMsg(err.detail || "Error en el cálculo bayesiano manual.");

    } finally {

      setLoading(false);

    }

  }



  async function runHypothesisTest() {

    setLoading(true);

    setErrorMsg("");

    try {

      const res = await transporte.solicitarRunHypothesisTest({ htCount1, htTotal1, htCount2, htTotal2 });

      setHypoResult(res);

      toast.success("Prueba completada", `Z=${res.z_statistic}, p-valor=${res.p_value}`);

    } catch (err: any) {

      setErrorMsg(err.detail || "Error en la prueba de hipótesis.");

    } finally {

      setLoading(false);

    }

  }



  async function saveAnalysis() {

    if (!analysisName.trim()) {

      toast.error("Nombre requerido", "Indica un nombre para persistir el análisis.");

      return;

    }

    setLoading(true);

    try {

      const payload = {

        name: analysisName.trim(),

        mode: numberMode,

        counts: {

          sample_space_size: sampleSpace,

          event_a: eventACount,

          event_b: eventBCount,

          intersection: intersectionCount

        },

        probabilities: bayesResult ? {

          prior_a: bayesResult.prior_a,

          likelihood_b_given_a: bayesResult.likelihood_b_given_a,

          evidence_b: bayesResult.evidence_b,

          posterior_a_given_b: bayesResult.posterior_a_given_b

        } : {},

        smoothing_enabled: smoothingEnabled,

        alpha: alphaVal,

        is_simulation: false,

        scenario_type: "observed"

      };

      await transporte.solicitarSaveAnalysis({ payload });

      toast.success("Análisis guardado", "El análisis quedó persistido con entradas y redondeo exactos.");

      setAnalysisName("");

      loadAnalyses();

    } catch (err: any) {

      toast.error("Error al guardar", err.detail || "No se pudo guardar el análisis.");

    } finally {

      setLoading(false);

    }

  }



  async function duplicateAsSimulation(baseId: string) {

    setLoading(true);

    try {

      const newName = `Simulación ${new Date().toLocaleTimeString("es-PE")}`;

      await transporte.solicitarDuplicateAsSimulation({ baseId, newName, numberMode });

      toast.success("Escenario duplicado", "Se creó un escenario etiquetado como Simulación Hipotética.");

      loadAnalyses();

    } catch (err: any) {

      toast.error("Error al duplicar", err.detail || "No se pudo duplicar el escenario.");

    } finally {

      setLoading(false);

    }

  }



  async function runComparison() {

    if (!selectedComp1 || !selectedComp2) return;

    setLoading(true);

    try {

      const res = await transporte.solicitarRunComparison({ selectedComp1, selectedComp2 });

      setCompareResult(res);

    } catch (err: any) {

      toast.error("Error al comparar", err.detail || "No se pudieron comparar los escenarios.");

    } finally {

      setLoading(false);

    }

  }

  return { activeMode, setActiveMode, numberMode, setNumberMode, entityUniverse, setEntityUniverse, period, setPeriod, sampleSpace, setSampleSpace, eventACount, setEventACount, eventBCount, setEventBCount, intersectionCount, setIntersectionCount, priorA, setPriorA, likelihoodA, setLikelihoodA, evidenceB, setEvidenceB, smoothingEnabled, setSmoothingEnabled, alphaVal, setAlphaVal, probResult, bayesResult, hypoResult, savedAnalyses, analysisName, setAnalysisName, loading, errorMsg, htCount1, setHtCount1, htTotal1, setHtTotal1, htCount2, setHtCount2, htTotal2, setHtTotal2, selectedComp1, setSelectedComp1, selectedComp2, setSelectedComp2, compareResult, conditionA, setConditionA, conditionB, setConditionB, thresholdAmount, setThresholdAmount, syncing, syncLiveCounts, calculateEmpirical, calculateManual, runHypothesisTest, saveAnalysis, duplicateAsSimulation, runComparison };

}

