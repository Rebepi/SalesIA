import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useState, useEffect, useRef, useMemo } from "react";
import { Search, User, Building2, Check, AlertTriangle, AlertCircle, Plus, X, ChevronDown } from "lucide-react";
import { CustomerItem } from "../types/NewSalePOSModal";
import { apiClient } from "../../../api/client";

interface PosCustomerSelectorProps {
  value: CustomerItem | undefined;
  onChange: (customer: CustomerItem) => void;
  documentType: "RECEIPT" | "INVOICE" | "SALE_NOTE";
  onRequestInvoice?: () => void;
  disabled?: boolean;
}

const RECENT_CUSTOMERS_KEY = "salesia_pos_recent_customers_v1";

export function PosCustomerSelector({
  value,
  onChange,
  documentType,
  onRequestInvoice,
  disabled = false,
}: PosCustomerSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [dbCustomers, setDbCustomers] = useState<CustomerItem[]>([]);
  const recentKey = `${RECENT_CUSTOMERS_KEY}:${apiClient.getCompanyId() || "session"}`;
  const [suggestions, setSuggestions] = useState<CustomerItem[]>([]);
  const [suggestionMode, setSuggestionMode] = useState("recent");
  const [listError, setListError] = useState("");
  const creatingLock = useRef(false);
  const [loading, setLoading] = useState(false);
  const [consultingFiscal, setConsultingFiscal] = useState(false);
  const [fiscalLookupResult, setFiscalLookupResult] = useState<{ legal_name: string; doc_type: string; doc_number: string; address?: string; status?: string } | null>(null);
  const [showInlineCreate, setShowInlineCreate] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState<CustomerItem | null>(null);

  const [createDocType, setCreateDocType] = useState<"DNI" | "RUC" | "CE" | "PASSPORT" | "SIN_DOCUMENTO">("DNI");
  const [createDocNumber, setCreateDocNumber] = useState("");
  const [createLegalName, setCreateLegalName] = useState("");
  const [createAddress, setCreateAddress] = useState("");
  const [createPhone, setCreatePhone] = useState("");
  const [createEmail, setCreateEmail] = useState("");
  const [createConsent, setCreateConsent] = useState(false);
  const [creatingBusy, setCreatingBusy] = useState(false);
  const [createError, setCreateError] = useState("");

  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const isWalkIn = useMemo(() => {
    if (!value) return true;
    return Boolean(value.is_walk_in || value.doc_type === "SIN_DOCUMENTO" || value.legal_name?.toLowerCase().includes("consumidor final"));
  }, [value]);

  const defaultWalkInCustomer = useMemo<CustomerItem>(() => ({
    id: "walk-in-default",
    code: "CLI-CONSUMIDOR-FINAL",
    legal_name: "Consumidor final · Sin identificar",
    doc_type: "SIN_DOCUMENTO",
    doc_number: "",
    is_walk_in: true,
    payment_terms_days: 0,
    credit_limit: "0",
    current_balance: "0",
  }), []);

  function recentIds(): string[] {
    try {
      const stored: unknown = JSON.parse(localStorage.getItem(recentKey) || "[]");
      return Array.isArray(stored) ? stored.filter((id): id is string => typeof id === "string").slice(0, 5) : [];
    } catch { return []; }
  }

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setShowInlineCreate(false);
        setDuplicateWarning(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!isOpen || showInlineCreate) return;
    const controller = new AbortController();
    const focus = window.setTimeout(() => searchInputRef.current?.focus(), 50);
    setLoading(true); setListError(""); setDbCustomers([]); setSuggestions([]);
    const timer = window.setTimeout(async () => {
      try {
        const query = searchTerm.trim();
        if (query) {
          const res = await apiClient.request<{ items: CustomerItem[] }>(`/api/v1/customers?search=${encodeURIComponent(query)}&is_active=true&limit=10`, { signal: controller.signal });
          if (!controller.signal.aborted) setDbCustomers(res.items || []);
        } else {
          const recent = await Promise.all(recentIds().map(id => apiClient.request<CustomerItem>(`/api/v1/customers/${encodeURIComponent(id)}`, { signal: controller.signal }).catch(() => null)));
          if (controller.signal.aborted) return;
          const valid = recent.filter((customer): customer is CustomerItem => Boolean(customer && customer.is_active !== false && customer.doc_type !== "SIN_DOCUMENTO"));
          if (valid.length) { setSuggestions(valid); setSuggestionMode("recent"); }
          else {
            const res = await apiClient.request<{ items: CustomerItem[] }>("/api/v1/customers?order=random&is_active=true&limit=5", { signal: controller.signal });
            if (!controller.signal.aborted) { setSuggestions((res.items || []).slice(0, 5)); setSuggestionMode("random"); }
          }
        }
      } catch { if (!controller.signal.aborted) setListError("No se pudieron cargar los clientes. Vuelve a abrir el selector para reintentar."); }
      finally { if (!controller.signal.aborted) setLoading(false); }
    }, 200);
    return () => { controller.abort(); window.clearTimeout(timer); window.clearTimeout(focus); };
  }, [searchTerm, isOpen, showInlineCreate, recentKey]);

  useEffect(() => {
    const clean = searchTerm.replace(/\D/g, "");
    if (clean.length === 8) {
      setCreateDocType("DNI");
      setCreateDocNumber(clean);
    } else if (clean.length === 11 && (clean.startsWith("10") || clean.startsWith("20"))) {
      setCreateDocType("RUC");
      setCreateDocNumber(clean);
    } else if (searchTerm.trim()) {
      setCreateLegalName(searchTerm.trim());
    }
  }, [searchTerm]);

  function saveToRecent(customer: CustomerItem) {
    if (customer.is_walk_in || customer.doc_type === "SIN_DOCUMENTO") return;
    try {
      const current = recentIds().filter(id => id !== customer.id);
      localStorage.setItem(recentKey, JSON.stringify([customer.id, ...current].slice(0, 5)));
    } catch {
    }
  }

  function handleSelect(customer: CustomerItem) {
    onChange(customer);
    if (onRequestInvoice && (customer.doc_type?.toUpperCase() === "RUC" || customer.doc_number?.replace(/\D/g, "").length === 11)) {
      onRequestInvoice();
    }
    saveToRecent(customer);
    setIsOpen(false);
    setShowInlineCreate(false);
    setSearchTerm("");
    setDuplicateWarning(null);
  }

  async function handleConsultFiscal() {
    const cleanDoc = createDocNumber.trim();
    if (!cleanDoc) return;
    setConsultingFiscal(true);
    setCreateError("");
    try {
      const res = await apiClient.request<{ valid: boolean; provider: string; doc_type: string; doc_number: string }>(
        "/api/v1/customers/fiscal/validate",
        {
          method: "POST",
          body: JSON.stringify({ doc_type: createDocType, doc_number: cleanDoc }),
        }
      );
      if (res.valid) {
        setFiscalLookupResult({ legal_name: "", doc_type: createDocType, doc_number: cleanDoc, status: "Formato del documento válido. Completa el nombre y la dirección." });
      } else { setCreateError("El documento no es válido."); }

    } catch (err: unknown) {
      const errObj = err as { detail?: string; message?: string };
      setCreateError(errObj.detail || errObj.message || "No se pudo validar el documento en el padrón.");
    } finally {
      setConsultingFiscal(false);
    }
  }

  async function handleCreateQuickCustomer(e: React.FormEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (disabled || creatingLock.current) return;
    if (!createLegalName.trim()) {
      setCreateError("El nombre o razón social es obligatorio.");
      return;
    }
    if (documentType === "INVOICE" && (createDocType !== "RUC" || createDocNumber.replace(/\D/g, "").length !== 11)) {
      setCreateError("Para emitir Factura se exige un RUC válido de 11 dígitos.");
      return;
    }
    if (documentType === "INVOICE" && !createAddress.trim()) {
      setCreateError("La dirección fiscal es obligatoria para emitir Factura.");
      return;
    }

    creatingLock.current = true;
    setCreatingBusy(true);
    setCreateError("");

    try {
      if (createDocNumber.trim()) {
        const dupCheck = await apiClient.request<{ is_exact_duplicate: boolean; exact_matches: Array<{ id: string; legal_name: string; doc_number: string }> }>(
          "/api/v1/customers/duplicates/check",
          {
            method: "POST",
            body: JSON.stringify({
              doc_type: createDocType,
              doc_number: createDocNumber.trim(),
              phone: createPhone.trim() || undefined,
              email: createEmail.trim() || undefined,
              legal_name: createLegalName.trim(),
            }),
          }
        ).catch(() => ({ is_exact_duplicate: false, exact_matches: [] }));

        if (dupCheck.is_exact_duplicate && dupCheck.exact_matches.length > 0) {
          const matched = dbCustomers.find(c => c.id === dupCheck.exact_matches[0].id) || {
            id: dupCheck.exact_matches[0].id,
            legal_name: dupCheck.exact_matches[0].legal_name,
            doc_type: createDocType,
            doc_number: dupCheck.exact_matches[0].doc_number,
            code: "CLI-EXISTENTE",
          } as CustomerItem;
          setDuplicateWarning(matched);
          setCreatingBusy(false);
          return;
        }
      }

      const payload = {
        legal_name: createLegalName.trim(),
        doc_type: createDocType,
        doc_number: createDocType === "SIN_DOCUMENTO" ? "SIN_DOCUMENTO" : createDocNumber.trim(),
        address: createAddress.trim() || undefined,
        phone: createPhone.trim() || undefined,
        email: createEmail.trim() || undefined,
        preferred_currency: "USD",
        notes: createConsent ? "Aceptó consentimiento promocional (Ley 29733)" : undefined,
      };

      const res = await apiClient.request<CustomerItem>("/api/v1/customers", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      handleSelect(res);
    } catch (err: unknown) {
      setCreateError(customerError(err));
    } finally {
      setCreatingBusy(false);
      creatingLock.current = false;
    }
  }

  const has11Ruc = createDocType === "RUC" && createDocNumber.replace(/\D/g, "").length === 11;
  const hasLegalName = Boolean(createLegalName.trim());
  const hasAddress = Boolean(createAddress.trim());

  return (
    <div ref={containerRef} className="relative w-full">
      <label className="mb-0.5 block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        Cliente
      </label>

      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(v => !v)}
        className="flex h-[34px] w-full items-center justify-between rounded-xl border border-slate-300 bg-white px-2 py-0.5 text-left text-xs shadow-sm transition hover:border-teal-500 focus:border-teal-600 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
        aria-label="Seleccionar cliente"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-1.5 truncate min-w-0">
          <div className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md ${isWalkIn ? "bg-slate-100 text-slate-600 dark:bg-slate-800" : "bg-teal-50 text-teal-700 dark:bg-teal-950/60"}`}>
            {isWalkIn ? <User className="h-3 w-3" /> : <Building2 className="h-3 w-3" />}
          </div>
          <div className="truncate flex flex-col justify-center min-w-0">
            <span className="block truncate text-[11px] font-semibold text-slate-900 dark:text-slate-100 leading-none">
              {isWalkIn ? "Consumidor final · Sin identificar" : value?.legal_name}
            </span>
            <span className="block truncate font-mono text-[9px] text-slate-500 dark:text-slate-400 leading-none mt-1.5">
              {isWalkIn
                ? "Lista estándar"
                : `${value?.doc_type ? `${value.doc_type} ${value.doc_number || "Sin número"} · ` : ""}${value?.price_list_id ? "Lista asignada" : "Lista estándar"}`}
            </span>
          </div>
        </div>
        <ChevronDown className={`h-3.5 w-3.5 shrink-0 text-slate-400 transition ${isOpen ? "rotate-180 text-teal-600" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full z-50 mt-1.5 w-full min-w-[340px] max-w-[480px] rounded-2xl border border-slate-200 bg-white p-3 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
          <div className="relative mb-2">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchTerm}
              onChange={e => {
                setSearchTerm(e.target.value);
                setShowInlineCreate(false);
                setDuplicateWarning(null);
              }}
              placeholder="Buscar por nombre, RUC, DNI, teléfono o código..."
              className="w-full rounded-xl border border-slate-300 bg-slate-50 py-2 pl-9 pr-8 text-xs outline-none focus:border-teal-600 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm("")}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {duplicateWarning && (
            <div className="mb-2 rounded-xl border border-amber-200 bg-amber-50 p-2.5 text-xs dark:border-amber-900/40 dark:bg-amber-950/30">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
                <div className="flex-1">
                  <p className="font-semibold text-amber-900 dark:text-amber-200">
                    Ya existe un cliente con este documento o teléfono:
                  </p>
                  <p className="font-bold text-slate-900 dark:text-slate-100">{duplicateWarning.legal_name}</p>
                  <p className="font-mono text-[10px] text-slate-500">
                    {duplicateWarning.doc_type} {duplicateWarning.doc_number}
                  </p>
                  <button
                    type="button"
                    onClick={() => handleSelect(duplicateWarning)}
                    className="mt-2 w-full rounded-lg bg-amber-700 py-1 text-center font-bold text-white hover:bg-amber-800"
                  >
                    Usar este cliente existente
                  </button>
                </div>
              </div>
            </div>
          )}

          {!showInlineCreate ? (
            <div className="max-h-[360px] overflow-y-auto space-y-1">
              {listError && <p role="alert" className="p-2 text-xs text-rose-600 dark:text-rose-300">{listError}</p>}
              {!searchTerm && loading && <p role="status" className="p-2 text-xs text-slate-500">Cargando clientes…</p>}
              <button
                type="button"
                onClick={() => handleSelect(defaultWalkInCustomer)}
                className={`flex w-full items-center justify-between rounded-xl p-2.5 text-left transition hover:bg-slate-100 dark:hover:bg-slate-800 ${isWalkIn ? "bg-teal-50 border border-teal-200 dark:bg-teal-950/40 dark:border-teal-800" : "bg-slate-50/60"}`}
              >
                <div className="flex items-center gap-2.5">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-700 text-white">
                    <User className="h-4 w-4" />
                  </div>
                  <div>
                    <strong className="block text-xs text-slate-900 dark:text-slate-100">
                      Consumidor final · Sin identificar
                    </strong>
                    <span className="block text-[10px] text-slate-500 dark:text-slate-400">
                      Boleta o Nota de venta sin exigencia de datos
                    </span>
                  </div>
                </div>
                {isWalkIn && <Check className="h-4 w-4 text-teal-700 dark:text-teal-400" />}
              </button>

              {!searchTerm && suggestions.length > 0 && (
                <div className="pt-2">
                  <span className="block px-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    {suggestionMode === "recent" ? "Clientes recientes" : "Clientes sugeridos al azar"}
                  </span>
                  {suggestions.map(c => (
                    <button
                      key={`recent-${c.id}`}
                      type="button"
                      onClick={() => handleSelect(c)}
                      className="flex w-full items-center justify-between rounded-xl p-2 text-left hover:bg-slate-50 dark:hover:bg-slate-800"
                    >
                      <div className="truncate pr-2">
                        <strong className="block truncate text-xs text-slate-900 dark:text-slate-100">
                          {c.legal_name}
                        </strong>
                        <span className="block font-mono text-[10px] text-slate-500 dark:text-slate-400">
                          {c.doc_type} {c.doc_number || "—"} {c.phone ? `· ${c.phone}` : ""}
                        </span>
                      </div>
                      {c.is_credit_blocked && (
                        <span className="shrink-0 rounded bg-rose-100 px-1.5 py-0.5 text-[9px] font-bold text-rose-800">
                          Bloqueado
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}

              {searchTerm && (
                <div>
                  {loading ? (
                    <p className="py-6 text-center text-xs text-slate-400">Buscando clientes en la organización...</p>
                  ) : dbCustomers.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-slate-200 p-4 text-center dark:border-slate-800">
                      <p className="text-xs text-slate-600 dark:text-slate-300">
                        No encontramos coincidencias para <strong>“{searchTerm}”</strong>.
                      </p>
                      <button
                        type="button"
                        onClick={() => setShowInlineCreate(true)}
                        className="mt-2 inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3 py-1.5 text-xs font-bold text-white hover:bg-teal-800"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        <span>Registrar cliente nuevo</span>
                      </button>
                    </div>
                  ) : (
                    dbCustomers.map(c => (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => handleSelect(c)}
                        className={`flex w-full items-center justify-between rounded-xl p-2 text-left hover:bg-slate-50 dark:hover:bg-slate-800 ${value?.id === c.id ? "bg-teal-50/70 border border-teal-200" : ""}`}
                      >
                        <div className="truncate pr-2">
                          <strong className="block truncate text-xs text-slate-900 dark:text-slate-100">
                            {c.legal_name}
                          </strong>
                          <span className="block font-mono text-[10px] text-slate-500 dark:text-slate-400">
                            {c.doc_type} {c.doc_number || "—"} {c.phone ? `· Tel: ${c.phone}` : ""}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          {c.is_credit_blocked && (
                            <span className="rounded bg-rose-100 px-1.5 py-0.5 text-[9px] font-bold text-rose-800">
                              Bloqueado
                            </span>
                          )}
                          {Number(c.current_balance || 0) > 0 && (
                            <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[9px] font-semibold text-amber-800">
                              Con saldo
                            </span>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              )}

              {(
                <div className="border-t border-slate-100 pt-2 dark:border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowInlineCreate(true)}
                    className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-teal-200 bg-teal-50 py-2 text-xs font-bold text-teal-800 hover:bg-teal-100 dark:border-teal-800 dark:bg-teal-950/40 dark:text-teal-300"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>Registrar cliente nuevo</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleCreateQuickCustomer} className="space-y-3 pt-1">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                  Alta Rápida de Cliente
                </span>
                <button
                  type="button"
                  onClick={() => setShowInlineCreate(false)}
                  className="text-xs text-slate-400 hover:text-slate-600"
                >
                  Volver a búsqueda
                </button>
              </div>

              {createError && (
                <div className="flex items-center gap-1.5 rounded-xl bg-rose-50 p-2 text-[11px] text-rose-800">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{createError}</span>
                </div>
              )}

              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-1">
                  <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">Tipo Doc.</label>
                  <CustomSelect
                    aria-label="Tipo de documento"
                    value={createDocType}
                    onChange={e => { setCreateDocType(e.target.value as typeof createDocType); setFiscalLookupResult(null); }}
                    className="w-full rounded-lg border border-slate-300 bg-white p-1.5 text-xs outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800"
                  >
                    <option value="DNI">DNI</option>
                    <option value="RUC">RUC</option>
                    <option value="CE">Carné Ext.</option>
                    <option value="PASSPORT">Pasaporte</option>
                    <option value="SIN_DOCUMENTO">Sin documento</option>
                  </CustomSelect>
                </div>

                <div className="col-span-2">
                  <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">Número de Documento</label>
                  <div className="flex gap-1.5">
                    <input
                      type="text"
                      aria-label="Número de documento"
                      required={createDocType !== "SIN_DOCUMENTO"}
                      disabled={createDocType === "SIN_DOCUMENTO"}
                      value={createDocNumber}
                      onChange={e => { setCreateDocNumber(e.target.value); setFiscalLookupResult(null); }}
                      placeholder={createDocType === "RUC" ? "11 dígitos" : createDocType === "DNI" ? "8 dígitos" : "Número"}
                      className="flex-1 rounded-lg border border-slate-300 p-1.5 font-mono text-xs outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800"
                    />
                    {(createDocType === "RUC" || createDocType === "DNI") && (
                      <button
                        type="button"
                        disabled={consultingFiscal}
                        onClick={handleConsultFiscal}
                        className="rounded-lg bg-teal-100 px-2 text-[11px] font-bold text-teal-800 hover:bg-teal-200 dark:bg-teal-950/60 dark:text-teal-300"
                      >
                        {consultingFiscal ? "..." : "Validar"}
                      </button>
                    )}
                  </div>
                  {fiscalLookupResult && (
                    <span className="mt-1 block text-[10px] text-emerald-700 dark:text-emerald-400 font-semibold">
                      {fiscalLookupResult.status || "Validado en padrón fiscal"}
                    </span>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">Nombre o Razón Social *</label>
                <input
                  type="text"
                  aria-label="Nombre o razón social"
                  minLength={2}
                  maxLength={255}
                  required
                  value={createLegalName}
                  onChange={e => setCreateLegalName(e.target.value)}
                  placeholder="Ej. Juan Pérez o Distribuidora Norte S.A.C."
                  className="w-full rounded-lg border border-slate-300 p-1.5 text-xs outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">
                  Dirección Fiscal {createDocType === "RUC" ? "*" : "(Opcional)"}
                </label>
                <input
                  type="text"
                  value={createAddress}
                  onChange={e => setCreateAddress(e.target.value)}
                  placeholder="Av. Las Magnolias 123, Lima"
                  className="w-full rounded-lg border border-slate-300 p-1.5 text-xs outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">Teléfono (opcional)</label>
                  <input
                    type="tel"
                    value={createPhone}
                    onChange={e => setCreatePhone(e.target.value)}
                    placeholder="999888777"
                    className="w-full rounded-lg border border-slate-300 p-1.5 text-xs outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">Correo (opcional)</label>
                  <input
                    type="email"
                    value={createEmail}
                    onChange={e => setCreateEmail(e.target.value)}
                    placeholder="cliente@ejemplo.com"
                    className="w-full rounded-lg border border-slate-300 p-1.5 text-xs outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>
              </div>

              <label className="flex items-start gap-2 text-[10px] text-slate-600 dark:text-slate-400">
                <input
                  type="checkbox"
                  checked={createConsent}
                  onChange={e => setCreateConsent(e.target.checked)}
                  className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <span>Acepta recibir promociones y comunicaciones comerciales (Ley N° 29733 de Protección de Datos Personales).</span>
              </label>

              {documentType === "INVOICE" && (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-2 text-[10px] dark:border-slate-800 dark:bg-slate-950">
                  <p className="font-bold text-slate-700 dark:text-slate-300">Requisitos para Factura electrónica:</p>
                  <p className={has11Ruc ? "text-emerald-700" : "text-slate-400"}>
                    {has11Ruc ? "✓" : "✗"} RUC de 11 dígitos
                  </p>
                  <p className={hasLegalName ? "text-emerald-700" : "text-slate-400"}>
                    {hasLegalName ? "✓" : "✗"} Razón social
                  </p>
                  <p className={hasAddress ? "text-emerald-700" : "text-slate-400"}>
                    {hasAddress ? "✓" : "✗"} Dirección fiscal
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setShowInlineCreate(false)}
                  className="flex-1 rounded-xl border border-slate-300 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={creatingBusy || disabled}
                  className="flex-1 rounded-xl bg-teal-700 py-2 text-xs font-bold text-white shadow hover:bg-teal-800 disabled:opacity-50"
                >
                  {creatingBusy ? "Guardando..." : "Guardar y Usar"}
                </button>
              </div>
            </form>
          )}

          <div className="mt-2 border-t border-slate-100 pt-2 text-center dark:border-slate-800">
            <button
              type="button"
              onClick={() => handleSelect(defaultWalkInCustomer)}
              className="text-[11px] font-semibold text-slate-500 hover:text-slate-800 hover:underline dark:text-slate-400"
            >
              Continuar como consumidor final
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
function customerError(cause: unknown): string {
  const detail = (cause as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(value => String(value.msg || "Revisa los datos del cliente")).join("; ");
  if (detail && typeof detail === "object") return String((detail as { rule?: string; message?: string }).rule || (detail as { message?: string }).message || "Revisa los datos del cliente.");
  return "No se pudo registrar el cliente. Revisa los datos e inténtalo nuevamente.";
}
