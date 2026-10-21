import * as transporte from "../api/ApprovalsInboxWorkspaceTab";
import { useEffect, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";

import { ApprovalRequestItem } from "../types/ApprovalsInboxWorkspaceTab";

import { ApprovalsInboxWorkspaceTabProps } from "../types/ApprovalsInboxWorkspaceTab";
import { toApprovalItem } from "../support/ApprovalsInboxWorkspaceTab";

export function useApprovalsInboxWorkspaceTab({ canWrite = true }: ApprovalsInboxWorkspaceTabProps) {
  const [approvals, setApprovals] = useState<ApprovalRequestItem[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const [rejectionModalItem, setRejectionModalItem] = useState<ApprovalRequestItem | null>(null);

  const [rejectionReason, setRejectionReason] = useState<string>("");

  const [versionConflictItem, setVersionConflictItem] = useState<ApprovalRequestItem | null>(null);

  const toast = useToast();

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    transporte.solicitarDatos()
      .then((response) => {
        if (active && response.items) {
          setApprovals(response.items.map(toApprovalItem));
        }
      })
      .catch((failure: unknown) => {
        if (active) setError(String((failure as { detail?: string }).detail || failure));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const handleApprove = async (item: ApprovalRequestItem) => {
    if (!canWrite || saving || item.status !== "pending") return;
    if (item.document_changed || item.document_version !== item.server_document_version) {
      setVersionConflictItem(item);
      toast.error(
        "Aprobación abortada por conflicto de versión",
        "El documento fue modificado en el servidor mientras se revisaba. Revisa la versión actual."
      );
      return;
    }

    setSaving(true);
    try {
      const decision = await transporte.solicitarHandleApprove({ item });
      setVersionConflictItem(null);
      const response = await transporte.solicitarDatos();
      setApprovals(response.items.map(toApprovalItem));
      toast.success(decision.status === "approved" ? "Solicitud aprobada" : "Decisión registrada", decision.status === "approved" ? `La operación ${item.code} fue autorizada.` : "La solicitud continúa pendiente de otras decisiones o etapas.");
    } catch (failure: unknown) {
      const status = (failure as { status?: number }).status;
      if (status === 409) setVersionConflictItem(item);
      toast.error("No se pudo aprobar", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canWrite || saving || !rejectionModalItem) return;
    if (!rejectionReason.trim()) {
      toast.error("Motivo obligatorio", "Debes ingresar un motivo para rechazar la solicitud.");
      return;
    }

    setSaving(true);
    try {
      await transporte.solicitarHandleConfirmReject({ rejectionModalItem, rejectionReason });
      setApprovals((prev) => prev.map((approval) => approval.id === rejectionModalItem.id ? { ...approval, status: "rejected" } : approval));
      toast.info("Solicitud rechazada", `La operación ${rejectionModalItem.code} fue rechazada con motivo registrado.`);
      setRejectionModalItem(null);
      setRejectionReason("");
    } catch (failure: unknown) {
      toast.error("No se pudo rechazar", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const pendingApprovals = approvals.filter((a) => a.status === "pending");
  return { approvals, loading, error, rejectionModalItem, setRejectionModalItem, rejectionReason, setRejectionReason, versionConflictItem, setVersionConflictItem, saving, handleApprove, handleConfirmReject, pendingApprovals };
}
