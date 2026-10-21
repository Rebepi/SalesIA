import * as transporte from "../api/OnboardingWizardModal";
import { useState, useEffect, useRef, FormEvent } from "react";
import { Building2, Store, Warehouse, FileText } from "lucide-react";

import { useToast } from "../../../ui/toast/ToastContext";
import { OnboardingWizardModalProps } from "../types/OnboardingWizardModal";
import { OnboardingFormState } from "../types/OnboardingWizardModal";
import { STORAGE_KEY } from "../support/OnboardingWizardModal";

export function useOnboardingWizardModal({ isOpen, onClose, onCompleted }: OnboardingWizardModalProps) {
  const [step, setStep] = useState(1);

  const [formData, setFormData] = useState<OnboardingFormState>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch { }
    return {
      tax_id: "",
      legal_name: "",
      trade_name: "",
      base_currency: "USD",
      branch_code: "PRINCIPAL",
      branch_name: "Sede Principal",
      timezone: "America/Lima",
      warehouse_code: "ALM-01",
      warehouse_name: "Almacén Central",
      series: "F001"
    };
  });

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState("");

  const dialogRef = useRef<HTMLDialogElement>(null);

  const toast = useToast();

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.showModal();
    } else {
      dialogRef.current?.close();
    }
  }, [isOpen]);

  function updateField(key: keyof OnboardingFormState, val: string) {
    setFormData(prev => {
      const updated = { ...prev, [key]: val };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch { }
      return updated;
    });
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (step < 4) {
      setStep(s => s + 1);
      return;
    }
    setBusy(true);
    setError("");
    try {
      const res = await transporte.solicitarHandleSubmit({ formData });
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch { }
      toast.success(
        res.resumed ? "Configuración retomada" : "Alta inicial completada",
        "La empresa y sus recursos operativos han sido configurados correctamente."
      );
      if (onCompleted) onCompleted();
      onClose();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al guardar el asistente";
      setError(msg);
      toast.error("Error en configuración", msg);
    } finally {
      setBusy(false);
    }
  }

  const steps = [
    { num: 1, title: "Empresa", Icon: Building2 },
    { num: 2, title: "Sucursal", Icon: Store },
    { num: 3, title: "Almacén", Icon: Warehouse },
    { num: 4, title: "Series", Icon: FileText }
  ];
  return { step, setStep, formData, busy, error, dialogRef, updateField, handleSubmit, steps };
}
