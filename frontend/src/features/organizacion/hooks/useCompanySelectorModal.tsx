import * as transporte from "../api/CompanySelectorModal";
import { useState, useEffect, useRef } from "react";
import { apiClient } from "../../../api/client";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "../../../ui/toast/ToastContext";
import { CompanyMembership } from "../types/CompanySelectorModal";
import { CompanySelectorModalProps } from "../types/CompanySelectorModal";

export function useCompanySelectorModal({ isOpen, currentCompanyId, onClose, onCompanySelected }: CompanySelectorModalProps) {
  const [companies, setCompanies] = useState<CompanyMembership[]>([]);

  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [switching, setSwitching] = useState<string | null>(null);

  const dialogRef = useRef<HTMLDialogElement>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);

  const queryClient = useQueryClient();

  const toast = useToast();

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.showModal();
      searchInputRef.current?.focus();
      loadCompanies();
    } else {
      dialogRef.current?.close();
    }
  }, [isOpen]);

  async function loadCompanies() {
    setLoading(true);
    setError("");
    try {
      const [current, profile] = await Promise.all([
        transporte.solicitarLoadCompanies(),
        apiClient.getMe()
      ]);
      const currentId = String(current.id || currentCompanyId || "");
      if (!currentId || !current.legal_name || !current.tax_id) throw new Error("La empresa activa no devolvió una identidad completa.");
      const availableCompanies: CompanyMembership[] = [
        {
          company_id: currentId,
          legal_name: String(current.legal_name),
          trade_name: current.trade_name ? String(current.trade_name) : undefined,
          tax_id: String(current.tax_id),
          role: profile.role,
          is_active: current.is_active !== false,
          is_current: true
        }
      ];
      setCompanies(availableCompanies);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "Error al cargar organizaciones";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelect(company: CompanyMembership) {
    if (!company.is_active) {
      toast.error("Membresía inactiva", "No puedes acceder a una empresa con membresía vencida.");
      return;
    }
    setSwitching(company.company_id);
    try {
      queryClient.clear();
      onCompanySelected(company);
      toast.success("Empresa seleccionada", `Contexto cambiado a ${company.legal_name}`);
      onClose();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "detail" in err ? String((err as { detail: unknown }).detail) : "No se pudo cambiar de empresa";
      toast.error("Error de contexto", msg);
    } finally {
      setSwitching(null);
    }
  }

  const filtered = companies.filter(c =>
    c.legal_name.toLowerCase().includes(search.toLowerCase()) ||
    c.tax_id.includes(search) ||
    (c.trade_name && c.trade_name.toLowerCase().includes(search.toLowerCase()))
  );
  return { search, setSearch, loading, error, switching, dialogRef, searchInputRef, loadCompanies, handleSelect, filtered };
}
