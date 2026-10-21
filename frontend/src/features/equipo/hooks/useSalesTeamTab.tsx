import * as transporte from "../api/SalesTeamTab";
import { FormEvent, useEffect, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { Row } from "../types/SalesTeamTab";
import { SalesRepItem } from "../types/SalesTeamTab";

export function useSalesTeamTab({ filterByTeam = true }: { filterByTeam?: boolean } = {}) {
  const [serverPage, setServerPage] = useState(0);
  const [serverPageSize, setServerPageSize] = useState(25);
  const [serverTotal, setServerTotal] = useState(0);
  const [reps, setReps] = useState<SalesRepItem[]>([]);

  const [branches, setBranches] = useState<Row[]>([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [period, setPeriod] = useState(() => new Date().toISOString().slice(0, 7));

  const [scopeFilter, setScopeFilter] = useState<"team" | "personal">("team");

  const [selectedTeam, setSelectedTeam] = useState("");

  const [searchTerm, setSearchTerm] = useState("");

  const [repModal, setRepModal] = useState<SalesRepItem | null | "new">(null);

  const [targetModal, setTargetModal] = useState<SalesRepItem | null>(null);

  const [portfolioModal, setPortfolioModal] = useState<{ rep: SalesRepItem; preview: Row | null } | null>(null);

  const [commissionModal, setCommissionModal] = useState<{ rep: SalesRepItem; settlement: Row | null } | null>(null);

  const [busy, setBusy] = useState(false);

  const toast = useToast();

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const teamQuery = filterByTeam && selectedTeam ? `&team=${encodeURIComponent(selectedTeam)}` : "";
      const [repsRes, branchesRes] = await Promise.all([
        transporte.solicitarLoadData({ period, teamQuery, page: filterByTeam ? serverPage : 0, pageSize: filterByTeam ? serverPageSize : 20, search: filterByTeam ? searchTerm : "" }),
        transporte.solicitarLoadData2().catch(() => [])
      ]);
      setReps(repsRes.items);
      setServerTotal(repsRes.count || 0);
      setBranches(branchesRes);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String(err.detail) : "Error al cargar equipo comercial";
      setError(msg);
      toast.error("Error", msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { setServerPage(0); }, [period, selectedTeam, searchTerm]);
  useEffect(() => {
    const timer = window.setTimeout(() => { void loadData(); }, 300);
    return () => window.clearTimeout(timer);
  }, [period, selectedTeam, filterByTeam, serverPage, serverPageSize, searchTerm]);

  async function saveRep(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    const fd = new FormData(e.currentTarget);
    const payload = {
      code: String(fd.get("code") || ""),
      full_name: String(fd.get("full_name") || ""),
      branch_id: fd.get("branch_id") ? String(fd.get("branch_id")) : null,
      team: fd.get("team") ? String(fd.get("team")) : null,
      territory: String(fd.get("territory") || "Principal"),
      monthly_quota: fd.get("monthly_quota") ? String(fd.get("monthly_quota")) : "0",
      is_active: fd.get("is_active") === "true"
    };
    try {
      if (repModal === "new") {
        await transporte.solicitarSaveRep({ payload });
        toast.success("Vendedor creado", "Ficha comercial persistida con éxito.");
      } else if (repModal) {
        await transporte.solicitarSaveRep2({ repModal, payload });
        toast.success("Ficha actualizada", "Cambios persistidos.");
      }
      setRepModal(null);
      loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String(err.detail) : "No se pudo guardar la ficha";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function saveTarget(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!targetModal) return;
    setBusy(true);
    const fd = new FormData(e.currentTarget);
    const payload = {
      representative_id: targetModal.rep_id,
      period: String(fd.get("period") || period),
      target_type: String(fd.get("target_type") || "amount"),
      target_value: String(fd.get("target_value") || "1000"),
      currency: String(fd.get("currency") || "USD"),
      scope: "individual"
    };
    try {
      await transporte.solicitarSaveTarget({ payload });
      toast.success("Meta asignada", "Meta por periodo registrada correctamente.");
      setTargetModal(null);
      loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String(err.detail) : "Error al registrar meta";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function openPortfolio(rep: SalesRepItem) {
    setBusy(true);
    try {
      const preview = await transporte.solicitarOpenPortfolio({ rep });
      setPortfolioModal({ rep, preview });
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String(err.detail) : "Error al obtener cartera";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function executeReassign(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!portfolioModal) return;
    setBusy(true);
    const fd = new FormData(e.currentTarget);
    const targetRepId = String(fd.get("target_rep_id") || "");
    const reason = String(fd.get("reason") || "Reasignación de cartera");
    try {
      await transporte.solicitarExecuteReassign({ portfolioModal, targetRepId, reason });
      toast.success("Cartera reasignada", "Clientes y oportunidades transferidos con auditoría.");
      setPortfolioModal(null);
      loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String(err.detail) : "Error al reasignar";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function openCommissions(rep: SalesRepItem) {
    setBusy(true);
    try {
      const settlement = await transporte.solicitarOpenCommissions({ rep, period });
      setCommissionModal({ rep, settlement });
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String(err.detail) : "Error al calcular liquidación";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function approveCommission() {
    if (!commissionModal?.settlement) return;
    setBusy(true);
    try {
      const res = await transporte.solicitarApproveCommission({ settlement: commissionModal.settlement });
      setCommissionModal(prev => prev ? { ...prev, settlement: { ...prev.settlement, status: res.status } } : null);
      toast.success("Liquidación aprobada", "Aprobación registrada por supervisor autorizado.");
      loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String(err.detail) : "No se pudo aprobar";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  async function payCommission() {
    if (!commissionModal?.settlement) return;
    setBusy(true);
    try {
      const res = await transporte.solicitarPayCommission({ settlement: commissionModal.settlement });
      setCommissionModal(prev => prev ? { ...prev, settlement: { ...prev.settlement, status: res.status } } : null);
      toast.success("Liquidación pagada", "Cierre contable definitivo.");
      loadData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String(err.detail) : "No se pudo pagar";
      toast.error("Error", msg);
    } finally {
      setBusy(false);
    }
  }

  const teams = Array.from(new Set(reps.map(r => r.team).filter(Boolean))) as string[];

  const filteredReps = reps.filter(r => {
    if (searchTerm) {
      const match = r.full_name.toLowerCase().includes(searchTerm.toLowerCase()) || r.code.toLowerCase().includes(searchTerm.toLowerCase());
      if (!match) return false;
    }
    return true;
  });
  const serverPagination = { page: serverPage, pageSize: serverPageSize, total: serverTotal, onPageChange: setServerPage, onPageSizeChange: (size: number) => { setServerPageSize(size); setServerPage(0); } };
  return { serverPagination, reps, branches, loading, error, period, setPeriod, scopeFilter, setScopeFilter, selectedTeam, setSelectedTeam, searchTerm, setSearchTerm, repModal, setRepModal, targetModal, setTargetModal, portfolioModal, setPortfolioModal, commissionModal, setCommissionModal, busy, loadData, saveRep, saveTarget, openPortfolio, executeReassign, openCommissions, approveCommission, payCommission, teams, filteredReps };
}
