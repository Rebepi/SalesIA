import * as transporte from "../api/CashRegisterWorkspaceTab";
import { FormEvent, useEffect, useState } from "react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { CashSession } from "../types/CashRegisterWorkspaceTab";
import { CashRegisterWorkspaceTabProps } from "../types/CashRegisterWorkspaceTab";

export function useCashRegisterWorkspaceTab(_props: CashRegisterWorkspaceTabProps) {
  const sessionSection = !_props.section || ["sessions", "movements", "counts"].includes(_props.section);
  const [sessions, setSessions] = useState<CashSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [userId, setUserId] = useState("");
  const sessionsCount = sessions.length;
  const activeSession = sessions.find(row => row.id === selectedSessionId)
    || sessions.find(row => row.user_id === userId && row.status === "open")
    || sessions.find(row => row.status === "open") || sessions[0] || null;

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [revision, setRevision] = useState(0);

  const [branches, setBranches] = useState<{ branch_id: string; name: string; code: string }[]>([]);

  const [currency, setCurrency] = useState("");

  const [modalType, setModalType] = useState<"open_session" | "new_movement" | "blind_count" | "approve_diff" | "close_session" | null>(null);

  const toast = useToast();

  useEffect(() => {
    if (!sessionSection) return;
    setLoading(true);
    setError("");
    const controller = new AbortController();
    Promise.all([
      apiClient.request<CashSession[]>("/api/v1/cash-sessions", { signal: controller.signal }),
      apiClient.getMe()
    ]).then(([rows, profile]) => {
      if (controller.signal.aborted) return;
      setSessions(rows || []);
      setUserId(profile.user_id);
    }).catch(err => {
      if (!controller.signal.aborted) setError(String(err?.detail || "No se pudo obtener el estado de caja."));
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [revision, sessionSection]);

  useEffect(() => {
    if (!sessionSection) return;
    Promise.all([
      transporte.solicitarDatos(),
      transporte.solicitarDatos2()
    ]).then(([branchRows, company]) => { setBranches(branchRows); setCurrency(company.base_currency); }).catch(() => setError("No se pudo cargar la configuración monetaria y de sedes."));
  }, [sessionSection]);

  async function handleOpenSession(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    try {
      await transporte.solicitarHandleOpenSession({ data });
      toast.success("Caja abierta", "Sesión de caja iniciada con éxito.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al abrir caja";
      toast.error("Error", msg);
    }
  }

  async function handleNewMovement(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!activeSession) return;
    const data = new FormData(e.currentTarget);
    try {
      await transporte.solicitarHandleNewMovement({ activeSession, data });
      toast.success("Movimiento registrado", "El saldo de caja fue actualizado.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al registrar movimiento";
      toast.error("Error", msg);
    }
  }

  async function handleBlindCount(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!activeSession) return;
    const data = new FormData(e.currentTarget);
    try {
      const res = await transporte.solicitarHandleBlindCount({ activeSession, data });
      toast.success(
        "Arqueo ciego registrado",
        res.requires_approval
          ? "Existe diferencia entre lo contado y el saldo teórico. Requiere autorización."
          : "Conteo conforme sin descuadre."
      );
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al registrar arqueo";
      toast.error("Error", msg);
    }
  }

  async function handleApproveDifference(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!activeSession) return;
    const data = new FormData(e.currentTarget);
    try {
      await transporte.solicitarHandleApproveDifference({ activeSession, data });
      toast.success("Revisión registrada", String(data.get("decision")) === "reject" ? "El arqueo fue rechazado. El responsable debe repetir el conteo." : "La diferencia fue autorizada.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al justificar diferencia";
      toast.error("Error", msg);
    }
  }

  async function handleCloseSession(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!activeSession) return;
    const data = new FormData(e.currentTarget);
    try {
      await transporte.solicitarHandleCloseSession({ activeSession, data });
      toast.success("Caja cerrada", "Sesión finalizada y bloqueada para nuevos cobros.");
      setModalType(null);
      setRevision(r => r + 1);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al cerrar caja";
      toast.error("Error", msg);
    }
  }
  return { sessions, selectedSessionId: activeSession?.id || "", setSelectedSessionId, revision, sessionsCount, activeSession, loading, error, setRevision, branches, currency: activeSession?.currency || currency, openingCurrency: currency, modalType, setModalType, handleOpenSession, handleNewMovement, handleBlindCount, handleApproveDifference, handleCloseSession };
}
