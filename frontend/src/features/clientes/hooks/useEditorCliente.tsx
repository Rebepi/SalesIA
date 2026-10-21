import { FormEvent, useEffect, useRef, useState } from "react";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { clearDraft, readDraft, useUnsavedChanges, writeDraft } from "../../../ui/drafts";
import { notifyEntityChanged } from "../../../ui/entityEvents";
import { useToast } from "../../../ui/toast/ToastContext";
import * as editorApi from "../api/editorApi";
import type { CustomerData, CustomerEditorDrawerProps } from "../types/clientes";
const DRAFT_KEY = "salesia_customer_editor_draft";

export function useEditorCliente({ isOpen, initialData, onClose, onSaved }: CustomerEditorDrawerProps) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [formData, setFormData] = useState<CustomerData>({
    code: "",
    legal_name: "",
    doc_type: "RUC",
    doc_number: "",
    email: "",
    phone: "",
    credit_limit: "0"
  });

  const [busy, setBusy] = useState(false);

  const [validating, setValidating] = useState(false);

  const [duplicateWarning, setDuplicateWarning] = useState("");

  const [duplicateCandidates, setDuplicateCandidates] = useState<CustomerData[]>([]);

  const [fiscalStatus, setFiscalStatus] = useState("");

  const [error, setError] = useState("");

  const [isDirty, setIsDirty] = useState(false);

  const toast = useToast();

  const validationRequest = useRef(0);

  useUnsavedChanges(isOpen && isDirty);

  useEffect(() => {
    if (!isOpen) return;
    validationRequest.current += 1;
    setValidating(false);
    setError("");
    setDuplicateWarning("");
    setDuplicateCandidates([]);
    setFiscalStatus("");
    if (initialData) {
      setFormData({
        id: initialData.id,
        code: initialData.code || "",
        legal_name: initialData.legal_name || "",
        doc_type: initialData.doc_type || "RUC",
        doc_number: initialData.doc_number || "",
        email: initialData.email || "",
        phone: initialData.phone || "",
        credit_limit: initialData.credit_limit || "0"
      });
      setIsDirty(false);
    } else {
      try {
        const draft = readDraft<CustomerData | null>(DRAFT_KEY, null);
        if (draft) {
          setFormData(draft);
          setIsDirty(true);
        } else {
          setFormData({
            code: "",
            legal_name: "",
            doc_type: "RUC",
            doc_number: "",
            email: "",
            phone: "",
            credit_limit: "0"
          });
          setIsDirty(false);
        }
      } catch {
        setFormData({
          code: "",
          legal_name: "",
          doc_type: "RUC",
          doc_number: "",
          email: "",
          phone: "",
          credit_limit: "0"
        });
      }
    }
  }, [isOpen, initialData]);

  function handleChange(field: keyof CustomerData, value: string) {
    if (field === "doc_type") { validationRequest.current += 1; setValidating(false); setDuplicateWarning(""); setFiscalStatus(""); }
    setIsDirty(true);
    setFormData(prev => {
      const next = { ...prev, [field]: value };
      if (!initialData) {
        try {
          writeDraft(DRAFT_KEY, next);
        } catch { }
      }
      return next;
    });
  }

  async function checkDuplicateDoc(docNum: string) {
    const request = ++validationRequest.current;
    setFiscalStatus("");
    setDuplicateWarning("");
    if (!docNum || docNum.length < 8) { setValidating(false); return; }
    setValidating(true);
    setDuplicateWarning("");
    setError("");
    try {
      const res = await editorApi.buscarDocumento(docNum);
      if (request !== validationRequest.current) return;
      const existing = res.items?.find(c => c.doc_number === docNum && c.id !== initialData?.id);
      if (existing) {
        setDuplicateWarning(`Ya existe un cliente (${existing.legal_name}) con el documento ${docNum}.`);
      }
      const expectedLength = formData.doc_type === "RUC" ? 11 : formData.doc_type === "DNI" ? 8 : 0;
      if (expectedLength && docNum.length === expectedLength) {
        const fiscal = await editorApi.validarDocumento(docNum, formData);
        if (request !== validationRequest.current) return;
        setFiscalStatus(fiscal.external_lookup_ready ? `Documento validado para consulta con ${fiscal.provider}.` : "Documento validado localmente.");
      } else {
        setFiscalStatus("");
      }
    } catch (requestError: unknown) {
      if (request !== validationRequest.current) return;
      const detail = requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No se pudo validar si el documento ya existe.";
      setError(detail);
      toast.warning("Validación de duplicados no disponible", detail);
    } finally {
      if (request === validationRequest.current) setValidating(false);
    }
  }

  async function chooseDuplicate(candidate: CustomerData) {
    if (!candidate.id) return;
    setBusy(true);
    try {
      const existing = await editorApi.obtenerExistente(candidate);
      onSaved(existing);
      onClose();
    } catch {
      toast.error("No se pudo abrir el cliente existente");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (busy || validating) return;
    setBusy(true);
    setError("");
    try {
      const isEdit = Boolean(initialData?.id);
      if (!isEdit) {
        const duplicateResult = await editorApi.comprobarDuplicados(formData);
        const candidates = [...duplicateResult.exact_matches, ...duplicateResult.potential_matches];
        if (candidates.length) {
          setDuplicateCandidates(candidates);
          setDuplicateWarning(duplicateResult.is_exact_duplicate ? "Ya existe un cliente con el mismo documento. Usa el registro existente o combínalo desde la ficha 360." : "Encontramos clientes similares por correo, teléfono o razón social. Revisa antes de crear otro registro.");
          setBusy(false);
          return;
        }
      }
      const path = isEdit ? `/api/v1/customers/${initialData!.id}` : "/api/v1/customers";
      const method = isEdit ? "PATCH" : "POST";
      const saved = await editorApi.guardar(formData, path, method);
      try {
        clearDraft(DRAFT_KEY);
      } catch { }
      toast.success(
        isEdit ? "Cliente actualizado" : "Cliente registrado",
        `Ficha comercial guardada para ${formData.legal_name}.`
      );
      notifyEntityChanged("customer", saved);
      onSaved(saved);
      onClose();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al guardar cliente";
      setError(msg);
      toast.error("Error al guardar", msg);
    } finally {
      setBusy(false);
    }
  }

  async function handleClose() {
    if (busy) return;
    if (isDirty && !await confirm({ title: "¿Cerrar el editor?", text: "Hay cambios sin guardar. El borrador se conservará.", confirmLabel: "Cerrar", cancelLabel: "Quedarme" })) {
      return;
    }
    onClose();
  }
  return {
    ConfirmDialogNode,
    formData,
    busy,
    validating,
    duplicateWarning,
    duplicateCandidates,
    fiscalStatus,
    error,
    handleChange,
    checkDuplicateDoc,
    chooseDuplicate,
    handleSubmit,
    handleClose
  };
}
