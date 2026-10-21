import { FormEvent, useEffect, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";
import * as fichaApi from "../api/fichaApi";
import type { FichaClienteProps, FichaClienteTab, Row } from "../types/clientes";
export function useFichaCliente({ customerId, onRefresh }: FichaClienteProps) {
  const [tab, setTab] = useState<FichaClienteTab>("overview");

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [customer, setCustomer] = useState<Row | null>(null);

  const [quality, setQuality] = useState<{ score_percentage: number; missing_fields: string[]; alerts: string[]; blocking_purchases: boolean } | null>(null);

  const [contacts, setContacts] = useState<Row[]>([]);

  const [addresses, setAddresses] = useState<Row[]>([]);

  const [terms, setTerms] = useState<Row | null>(null);

  const [statement, setStatement] = useState<{ total_billed: string; total_paid: string; invoices: Row[] } | null>(null);

  const [notes, setNotes] = useState<Row[]>([]);

  const [segments, setSegments] = useState<{ matched_segments: { id: string; name: string }[]; actual_metrics: Row } | null>(null);

  const [timeline, setTimeline] = useState<Row[]>([]);

  const [companyCurrency, setCompanyCurrency] = useState("");

  const [quickPanel, setQuickPanel] = useState<"activity" | "opportunity" | null>(null);

  const [mergeTargetId, setMergeTargetId] = useState("");

  const [mergePreview, setMergePreview] = useState<Row | null>(null);

  const [creditTestAmount, setCreditTestAmount] = useState("1000");

  const [creditTestResult, setCreditTestResult] = useState<{ allowed: boolean; reason: string; available_credit: string } | null>(null);

  const toast = useToast();

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [cRes, qRes, ctRes, adRes, tmRes, stRes, ntRes, sgRes, historyRes, companyRes] = await Promise.all([
        fichaApi.obtener(customerId),
        fichaApi.calidad(customerId),
        fichaApi.contactos(customerId),
        fichaApi.direcciones(customerId),
        fichaApi.condiciones(customerId),
        fichaApi.estadoCuenta(customerId),
        fichaApi.notas(customerId),
        fichaApi.segmentos(customerId),
        fichaApi.historial(customerId),
        fichaApi.empresa()
      ]);
      setCustomer(cRes);
      setQuality(qRes);
      setContacts(ctRes);
      setAddresses(adRes);
      setTerms(tmRes);
      setStatement(stRes);
      setNotes(ntRes);
      setSegments(sgRes);
      setTimeline(historyRes.timeline);
      setCompanyCurrency(companyRes.base_currency);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar la ficha del cliente";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, [customerId]);

  async function handleAddContact(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await fichaApi.crearContacto(customerId, data);
      toast.success("Contacto registrado");
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch {
      toast.error("No se pudo guardar el contacto");
    }
  }

  async function handleDeleteContact(id: string) {
    try {
      await fichaApi.eliminarContacto(customerId, id);
      toast.success("Contacto archivado");
      void loadData();
    } catch {
      toast.error("Error al eliminar contacto");
    }
  }

  async function handleAddAddress(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await fichaApi.crearDireccion(customerId, data);
      toast.success("Dirección registrada");
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch {
      toast.error("No se pudo guardar la dirección");
    }
  }

  async function handleDeleteAddress(id: string) {
    try {
      await fichaApi.eliminarDireccion(customerId, id);
      toast.success("Dirección archivada");
      void loadData();
    } catch {
      toast.error("Error al eliminar dirección");
    }
  }

  async function handleAddNote(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await fichaApi.crearNota(customerId, data);
      toast.success("Nota agregada");
      void loadData();
      (e.target as HTMLFormElement).reset();
    } catch {
      toast.error("No se pudo guardar la nota");
    }
  }

  async function handleQuickActivity(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await fichaApi.crearActividad(customerId, data);
      toast.success("Tarea comercial creada");
      setQuickPanel(null);
      void loadData();
    } catch (requestError: unknown) {
      const detail = requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No se pudo crear la tarea.";
      toast.error("Error al crear la tarea", detail);
    }
  }

  async function handleQuickOpportunity(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      await fichaApi.crearOportunidad(customerId, data, companyCurrency);
      toast.success("Oportunidad creada");
      setQuickPanel(null);
      void loadData();
    } catch (requestError: unknown) {
      const detail = requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No se pudo crear la oportunidad.";
      toast.error("Error al crear la oportunidad", detail);
    }
  }

  async function handleTestCredit() {
    try {
      const res = await fichaApi.evaluarCredito(customerId, creditTestAmount);
      setCreditTestResult(res);
    } catch {
      toast.error("Error en validación de crédito");
    }
  }

  async function handlePreviewMerge() {
    if (!mergeTargetId) return;
    try {
      const res = await fichaApi.previsualizarFusion(customerId, mergeTargetId);
      setMergePreview(res);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al previsualizar fusión";
      toast.error("Error", msg);
    }
  }

  async function handleExecuteMerge() {
    if (!mergeTargetId) return;
    try {
      await fichaApi.fusionar(customerId, mergeTargetId);
      toast.success("Clientes fusionados exitosamente", "Las referencias históricas y saldos fueron integrados.");
      onRefresh();
      void loadData();
      setMergePreview(null);
      setMergeTargetId("");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error en fusión";
      toast.error("Fusión fallida", msg);
    }
  }
  return {
    loadData,
    tab,
    setTab,
    loading,
    error,
    customer,
    quality,
    contacts,
    addresses,
    terms,
    statement,
    notes,
    segments,
    timeline,
    companyCurrency,
    quickPanel,
    setQuickPanel,
    mergeTargetId,
    setMergeTargetId,
    mergePreview,
    setMergePreview,
    creditTestAmount,
    setCreditTestAmount,
    creditTestResult,
    handleAddContact,
    handleDeleteContact,
    handleAddAddress,
    handleDeleteAddress,
    handleAddNote,
    handleQuickActivity,
    handleQuickOpportunity,
    handleTestCredit,
    handlePreviewMerge,
    handleExecuteMerge
  };
}
