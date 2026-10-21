import * as transporte from "../api/InsightsEnterpriseView";
import { useEffect, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { InsightActionDraft } from "../types/InsightsEnterpriseView";
import { InsightItem } from "../types/InsightsEnterpriseView";
import { InsightsEnterpriseViewProps } from "../types/InsightsEnterpriseView";

export function useInsightsEnterpriseView({ insights, onStatusChange, onBulkRead, onFeedback }: InsightsEnterpriseViewProps) {
  const [remoteInsights, setRemoteInsights] = useState<InsightItem[]>([]);

  const [loading, setLoading] = useState(insights === undefined);

  const [loadError, setLoadError] = useState<string | null>(null);

  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");

  const [selectedStatus, setSelectedStatus] = useState<string>("all");

  const [activeEvidenceModal, setActiveEvidenceModal] = useState<InsightItem | null>(null);

  const [activeActionModal, setActiveActionModal] = useState<{ insight: InsightItem; action: InsightActionDraft } | null>(null);

  const [feedbackFeedbackId, setFeedbackFeedbackId] = useState<string | null>(null);

  const [feedbackComment, setFeedbackComment] = useState<string>("");

  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const [actionsOpen, setActionsOpen] = useState(false);

  const [revision, setRevision] = useState(0);

  const [isSubmitting, setIsSubmitting] = useState(false);

  const toast = useToast();

  const displayedInsights = insights ?? remoteInsights;

  useEffect(() => {
    if (insights !== undefined) {
      setLoading(false);
      return;
    }
    let active = true;
    transporte.solicitarDatos()
      .then((response) => {
        if (active) {
          setRemoteInsights(response.items || []);
          setLoadError(null);
        }
      })
      .catch((failure: unknown) => {
        if (active) setLoadError(String((failure as { detail?: string }).detail || failure));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [insights, revision]);

  const filteredInsights = displayedInsights.filter((item) => {
    const snoozed = Boolean(item.snoozed_until && new Date(item.snoozed_until).getTime() > Date.now());
    if (selectedStatus === "snoozed") return snoozed;
    if (snoozed) return false;
    if (selectedSeverity !== "all" && item.severity !== selectedSeverity) {
      return false;
    }
    if (selectedStatus !== "all" && item.status !== selectedStatus) {
      return false;
    }
    return true;
  });

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return "bg-rose-100 text-rose-800 border-rose-300";
      case "high":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "medium":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "low":
      default:
        return "bg-slate-100 text-slate-700 border-slate-300";
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "new":
      case "pending":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "in_review":
      case "acknowledged":
        return "bg-sky-100 text-sky-800 border-sky-200";
      case "resolved":
      case "actioned":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "dismissed":
        return "bg-gray-100 text-gray-700 border-gray-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const handleBulkReadClick = async () => {
    setIsSubmitting(true);
    try {
      if (onBulkRead) {
        await onBulkRead();
      } else {
        const response = await transporte.solicitarHandleBulkReadClick();
        setRemoteInsights((current) => current.map((item) => item.status === "new" || item.status === "pending" ? { ...item, status: "read" } : item));
        toast.success("Insights actualizados", `${response.marked_read_count} alertas fueron marcadas como leídas.`);
      }
    } catch (failure: unknown) {
      toast.error("No se pudieron actualizar los insights", String((failure as { detail?: string }).detail || failure));
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitFeedback = async (insightId: string, helpful: boolean) => {
    try {
      if (onFeedback) {
        await onFeedback(insightId, helpful, feedbackComment);
      } else {
        await transporte.solicitarSubmitFeedback({ insightId, helpful, feedbackComment });
      }
      setFeedbackFeedbackId(null);
      setFeedbackComment("");
      toast.success("Respuesta registrada", "La retroalimentación quedó vinculada al insight.");
    } catch (failure: unknown) {
      toast.error("No se pudo registrar la respuesta", String((failure as { detail?: string }).detail || failure));
    }
  };

  const changeStatus = async (insightId: string, status: string, reason: string) => {
    try {
      if (onStatusChange) {
        await onStatusChange(insightId, status, reason);
      } else {
        await transporte.solicitarChangeStatus({ insightId, status, reason });
        setRemoteInsights((current) => current.map((item) => item.id === insightId ? { ...item, status } : item));
      }
      toast.success("Estado actualizado", "El cambio quedó registrado en el ciclo de vida del insight.");
    } catch (failure: unknown) {
      toast.error("No se pudo actualizar el estado", String((failure as { detail?: string }).detail || failure));
    }
  };

  const prepareAction = async () => {
    if (!activeActionModal) return;
    setIsSubmitting(true);
    try {
      await transporte.solicitarPrepareAction({ activeActionModal });
      toast.success("Borrador preparado", "La acción está lista para la confirmación manual autorizada.");
      setActiveActionModal(null);
    } catch (failure: unknown) {
      toast.error("No se pudo preparar el borrador", String((failure as { detail?: string }).detail || failure));
    } finally {
      setIsSubmitting(false);
    }
  };
  return { loading, loadError, selectedSeverity, setSelectedSeverity, selectedStatus, setSelectedStatus, activeEvidenceModal, setActiveEvidenceModal, activeActionModal, setActiveActionModal, feedbackFeedbackId, setFeedbackFeedbackId, feedbackComment, setFeedbackComment, selectedIds, setSelectedIds, actionsOpen, setActionsOpen, setRevision, isSubmitting, toast, displayedInsights, filteredInsights, getSeverityBadgeClass, getStatusBadgeClass, handleBulkReadClick, submitFeedback, changeStatus, prepareAction };
}
