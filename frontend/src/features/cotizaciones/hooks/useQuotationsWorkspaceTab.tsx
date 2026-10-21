import * as transporte from "../api/QuotationsWorkspaceTab";
import { useEffect, useMemo, useState } from "react";
import { requestAllPages } from "../../../api/pagination";
import { apiClient } from "../../../api/client";
import { clearDraft, readDraft, useUnsavedChanges, writeDraft } from "../../../ui/drafts";
import { useToast } from "../../../ui/toast/ToastContext";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { QuotationItem } from "../types/QuotationsWorkspaceTab";
import { CustomerItem } from "../types/QuotationsWorkspaceTab";
import { QuotationLine } from "../types/QuotationsWorkspaceTab";
import { DRAFT_KEY } from "../support/QuotationsWorkspaceTab";
import { EMPTY_LINE } from "../support/QuotationsWorkspaceTab";
import { EMPTY_DRAFT } from "../support/QuotationsWorkspaceTab";

export function useQuotationsWorkspaceTab(_props: {
  canWrite?: boolean;
}) {
  const savedDraft = useMemo(() => readDraft(DRAFT_KEY, EMPTY_DRAFT), []);

  const { confirm, ConfirmDialogNode } = useConfirm();

  const [quotations, setQuotations] = useState<QuotationItem[]>([]);

  const [filterStatus, setFilterStatus] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [showEditor, setShowEditor] = useState(false);

  const [busy, setBusy] = useState(false);

  const [customer, setCustomer] = useState<CustomerItem | undefined>(savedDraft.customer);

  const [warehouses, setWarehouses] = useState<{ warehouse_id: string; name: string; code?: string; branch_id?: string }[]>([]);

  const [branches, setBranches] = useState<{ branch_id: string; name: string; code?: string }[]>([]);

  const [branchId, setBranchId] = useState(savedDraft.branchId);

  const [currency, setCurrency] = useState("");

  const [defaultTaxRate, setDefaultTaxRate] = useState("0");

  const [lines, setLines] = useState<QuotationLine[]>(savedDraft.lines?.length ? savedDraft.lines : [{ ...EMPTY_LINE }]);

  const [validDays, setValidDays] = useState(savedDraft.validDays);

  const [customerDrawerOpen, setCustomerDrawerOpen] = useState(false);

  const [productLineIndex, setProductLineIndex] = useState<number | null>(null);

  const [conversion, setConversion] = useState<QuotationItem | null>(null);

  const [conversionWarehouseId, setConversionWarehouseId] = useState("");

  const [warehouseDialogOpen, setWarehouseDialogOpen] = useState(false);

  const [paymentTerms, setPaymentTerms] = useState(savedDraft.paymentTerms);

  const [deliveryTerms, setDeliveryTerms] = useState(savedDraft.deliveryTerms);

  const [notes, setNotes] = useState(savedDraft.notes);

  const [specialConditions, setSpecialConditions] = useState(savedDraft.specialConditions);

  const [sellerId, setSellerId] = useState(savedDraft.sellerId);

  const [sellers, setSellers] = useState<Array<{ rep_id: string; full_name?: string; name?: string }>>([]);

  const [preview, setPreview] = useState<QuotationItem | null>(null);

  const [sendQuotation, setSendQuotation] = useState<QuotationItem | null>(null);

  const toast = useToast();

  const dirty = Boolean(customer || branchId || lines.some(line => line.product_id));

  useUnsavedChanges(showEditor && dirty);

  useEffect(() => { loadQuotations(); }, [filterStatus]);

  useEffect(() => { if (showEditor) writeDraft(DRAFT_KEY, { customer, branchId, validDays, lines, paymentTerms, deliveryTerms, notes, specialConditions, sellerId }); }, [showEditor, customer, branchId, validDays, lines, paymentTerms, deliveryTerms, notes, specialConditions, sellerId]);

  async function loadQuotations() {
    setLoading(true);
    setError("");
    try {
      const url = filterStatus ? `/api/v1/quotations?status_filter=${filterStatus}` : "/api/v1/quotations";
      const rows = await requestAllPages<QuotationItem[]>(url);
      setQuotations(Array.isArray(rows) ? rows : []);
    } catch (requestError: unknown) {
      setError(requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "Error al cargar cotizaciones");
    } finally { setLoading(false); }
  }

  async function loadContext() {
    try {
      const [warehouseRows, branchRows, company, settings, sellerRows] = await Promise.all([
        transporte.solicitarLoadContext(),
        transporte.solicitarLoadContext2(),
        transporte.solicitarLoadContext3(),
        transporte.solicitarLoadContext4(),
        transporte.solicitarLoadContext5()
      ]);
      setWarehouses(warehouseRows);
      setBranches(branchRows);
      setCurrency(company.base_currency);
      setDefaultTaxRate(String(settings.default_tax_rate || "0"));
      setSellers(sellerRows.items || []);
      if (!branchId && branchRows.length === 1) setBranchId(branchRows[0].branch_id);
    } catch (requestError: unknown) {
      const detail = requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No fue posible cargar sedes, almacenes y moneda.";
      setError(detail);
      toast.error("No se pudo preparar la cotización", detail);
    }
  }

  async function openCreateModal() {
    setShowEditor(true);
    await loadContext();
    const contextualCustomerId = sessionStorage.getItem("salesia_context_customer_id");
    if (contextualCustomerId) {
      try {
        setCustomer(await transporte.solicitarOpenCreateModal({ contextualCustomerId }));
        sessionStorage.removeItem("salesia_context_customer_id");
      } catch {
        toast.warning("Cliente no disponible", "No se pudo recuperar el cliente seleccionado desde su ficha.");
      }
    }
  }

  useEffect(() => {
    if (sessionStorage.getItem("salesia_open_quotation") === "true") {
      sessionStorage.removeItem("salesia_open_quotation");
      void openCreateModal();
    }
  }, []);

  async function requestCloseEditor() {
    if (dirty && !await confirm({ title: "¿Cerrar el editor?", text: "La cotización se conservará como borrador.", confirmLabel: "Cerrar", cancelLabel: "Quedarme" })) return;
    setShowEditor(false);
  }

  async function handleCreateQuotation(event: React.FormEvent) {
    event.preventDefault();
    if (!customer || !branchId || !currency || lines.some(line => !line.product_id)) {
      toast.warning("Datos incompletos", "Selecciona cliente, sede y todos los productos.");
      return;
    }
    setBusy(true);
    try {
      await transporte.solicitarHandleCreateQuotation({ customer, branchId, currency, validDays, paymentTerms, deliveryTerms, notes, specialConditions, sellerId, lines });
      clearDraft(DRAFT_KEY);
      setCustomer(undefined);
      setBranchId("");
      setLines([{ ...EMPTY_LINE }]);
      setValidDays("15");
      setPaymentTerms("30");
      setDeliveryTerms("");
      setNotes("");
      setSpecialConditions("");
      setSellerId("");
      setShowEditor(false);
      toast.success("Cotización creada", "Propuesta registrada con correlativo formal.");
      await loadQuotations();
    } catch (requestError: unknown) {
      toast.error("Error", requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "Error al crear cotización");
    } finally { setBusy(false); }
  }

  async function handleAccept(quotation: QuotationItem) {
    setBusy(true);
    try {
      await transporte.solicitarHandleAccept({ quotation });
      toast.success("Cotización aceptada", `Propuesta ${quotation.quotation_number} lista para convertirse en pedido.`);
      await loadQuotations();
    } catch (requestError: unknown) {
      toast.error("Error", requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "Error al aceptar cotización");
    } finally { setBusy(false); }
  }

  async function openConversion(quotation: QuotationItem) {
    await loadContext();
    setConversion(quotation);
    setConversionWarehouseId("");
  }

  async function handleConvert() {
    if (!conversion || !conversionWarehouseId) {
      toast.warning("Almacén requerido", "Selecciona el almacén que reservará las existencias.");
      return;
    }
    setBusy(true);
    try {
      await transporte.solicitarHandleConvert({ conversion, conversionWarehouseId });
      toast.success("Convertida a pedido", `Se generó el pedido vinculado a ${conversion.quotation_number}.`);
      setConversion(null);
      await loadQuotations();
    } catch (requestError: unknown) {
      toast.error("Error al convertir", requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "Error al convertir cotización");
    } finally { setBusy(false); }
  }

  async function handleNewVersion(quotation: QuotationItem) {
    setBusy(true);
    try {
      const detail = await transporte.solicitarHandleNewVersion({ quotation });
      if (!detail.lines?.length) throw new Error("La cotización no tiene líneas para versionar.");
      await transporte.solicitarHandleNewVersion2({ quotation, lines: detail.lines });
      toast.success("Nueva versión creada", `Se emitió v${quotation.version + 1} de ${quotation.quotation_number}.`);
      await loadQuotations();
    } catch (requestError: unknown) {
      const detail = requestError instanceof Error ? requestError.message : requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "Error al generar nueva versión";
      toast.error("Error al versionar", detail);
    } finally { setBusy(false); }
  }

  async function openPreview(quotation: QuotationItem) {
    try {
      setPreview(await transporte.solicitarOpenPreview({ quotation }));
      await loadQuotations();
    } catch (requestError: unknown) {
      toast.error("Error", requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No se pudo abrir la vista previa.");
    }
  }

  async function downloadPdf(quotation: QuotationItem) {
    try {
      const { blob, filename } = await apiClient.downloadBlob(`/api/v1/quotations/${quotation.quotation_id || quotation.id}/pdf`);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename || `${quotation.quotation_number}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (failure: unknown) {
      toast.error("No se pudo descargar la cotización", String((failure as { detail?: string }).detail || "Revisa la conexión y vuelve a intentar."));
    }
  }

  async function submitSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sendQuotation) return;
    const form = new FormData(event.currentTarget);
    try {
      const result = await transporte.solicitarSubmitSend({ sendQuotation, form });
      if (result.integration_url) window.open(result.integration_url, "_blank", "noopener,noreferrer");
      setSendQuotation(null);
      toast.success(result.integration_url ? "WhatsApp preparado" : "Correo en cola", result.integration_url ? "Completa el envío en WhatsApp. La apertura se registrará cuando el cliente visite el enlace." : "La cotización quedó en la cola de correo. El envío requiere el worker y el proveedor de correo configurados.");
      await loadQuotations();
    } catch (requestError: unknown) {
      toast.error("Error", requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No se pudo enviar la cotización.");
    }
  }
  return { ConfirmDialogNode, quotations, filterStatus, setFilterStatus, loading, error, showEditor, busy, customer, setCustomer, warehouses, setWarehouses, branches, branchId, setBranchId, currency, defaultTaxRate, lines, setLines, validDays, setValidDays, customerDrawerOpen, setCustomerDrawerOpen, productLineIndex, setProductLineIndex, conversion, setConversion, conversionWarehouseId, setConversionWarehouseId, warehouseDialogOpen, setWarehouseDialogOpen, paymentTerms, setPaymentTerms, deliveryTerms, setDeliveryTerms, notes, setNotes, specialConditions, setSpecialConditions, sellerId, setSellerId, sellers, preview, setPreview, sendQuotation, setSendQuotation, loadQuotations, openCreateModal, requestCloseEditor, handleCreateQuotation, handleAccept, openConversion, handleConvert, handleNewVersion, openPreview, downloadPdf, submitSend };
}
