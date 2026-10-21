import { selectorSeed } from "../../../api/selectorSeed";
import * as transporte from "../api/OperationsWorkspace";
import { useListadoClientes } from "../../../features/clientes/hooks/useListadoClientes";
import { FormEvent, ReactNode, startTransition, useEffect, useRef, useState } from "react";
import { apiClient, SearchResultItem, UserProfile } from "../../../api/client";
import { CustomerData } from "../../../features/clientes/editor/CustomerEditorDrawer";
import { SaleDetailData } from "../../../features/ventas/components/SaleDetailModal";
import { useToast } from "../../../ui/toast/ToastContext";
import { useQueryClient } from "@tanstack/react-query";
import { handleSelectiveInvalidation } from "../../../api/remoteState";
import { getDefaultPageSize, getSidebarMode, hydrateRemoteUiPreferences, UI_PREFERENCES_EVENT } from "../../../ui/preferences";
import { ENTITY_CHANGED_EVENT } from "../../../ui/entityEvents";
import { Row } from "../types/OperationsWorkspace";
import { View } from "../types/OperationsWorkspace";
import { Field } from "../types/OperationsWorkspace";
import { Editor } from "../types/OperationsWorkspace";
import { buttonStyle } from "../support/OperationsWorkspace";
import { viewKeys } from "../support/OperationsWorkspace";
import { viewFromUrl } from "../support/OperationsWorkspace";
import { isModuleAuthorized } from "../support/OperationsWorkspace";
import { message } from "../support/OperationsWorkspace";

export function useOperationsWorkspace() {
  const [globalSearchOpen, setGlobalSearchOpen] = useState(false);

  const [profile, setProfile] = useState<UserProfile | null>(null);

  const [currentCompany, setCurrentCompany] = useState<Row | null>(null);

  const [branches, setBranches] = useState<Row[]>([]);

  const [activeBranchId, setActiveBranchId] = useState<string>("");

  const [view, setView] = useState<View>(viewFromUrl);

  const [workspaceRows, setRows] = useState<Row[]>([]);

  const [workspaceTotal, setTotal] = useState(0);

  const [page, setPage] = useState(0);

  const [pageSize, setPageSize] = useState(getDefaultPageSize);

  const [search, setSearch] = useState("");

  const [revision, setRevision] = useState(0);

  const [workspaceLoading, setLoading] = useState(false);

  const [busy, setBusy] = useState(false);

  const [workspaceError, setError] = useState("");

  const [editor, setEditor] = useState<Editor | null>(null);

  const [confirm, setConfirm] = useState<{ title: string; text: string; path: string; body: unknown } | null>(null);

  const [paymentConfirm, setPaymentConfirm] = useState<{ amount: string | number; currency: string; customerName: string; documentNumber: string; paymentMethod: string; path: string; body: unknown } | null>(null);

  const [detail, setDetail] = useState<{ title: string; content: ReactNode } | null>(null);

  const [selectedCustomer, setSelectedCustomer] = useState<Row | null>(null);

  const [selectedProduct, setSelectedProduct] = useState<Row | null>(null);

  const [activeReturnSale, setActiveReturnSale] = useState<Row | null>(null);

  const [companySelectorOpen, setCompanySelectorOpen] = useState(false);

  const [onboardingModalOpen, setOnboardingModalOpen] = useState(false);

  const listadoClientes = useListadoClientes({ enabled: view === "customers", page, pageSize, search, revision, onPageChange: setPage, onErrorReset: setError });

  const rows = view === "customers" ? listadoClientes.rows : workspaceRows;

  const total = view === "customers" ? listadoClientes.total : workspaceTotal;

  const loading = view === "customers" ? listadoClientes.loading : workspaceLoading;

  const error = workspaceError || (view === "customers" ? listadoClientes.error : "");

  const [customerDrawerOpen, setCustomerDrawerOpen] = useState(false);

  const [customerToEdit, setCustomerToEdit] = useState<CustomerData | null>(null);

  const [posModalOpen, setPosModalOpen] = useState(false);

  const [productDialogOpen, setProductDialogOpen] = useState(false);

  const [posInitialCustomerId, setPosInitialCustomerId] = useState<string>();

  const [posSourceSaleId, setPosSourceSaleId] = useState<string>();

  const [saleDetailModalSale, setSaleDetailModalSale] = useState<SaleDetailData | null>(null);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => getSidebarMode() === "collapsed");

  const [sidebarHoveredTooltip, setSidebarHoveredTooltip] = useState<{ label: string; top: number } | null>(null);

  const keys = useRef(new Map<string, string>());

  const toast = useToast();

  const queryClient = useQueryClient();

  const can = (permission: string) => isModuleAuthorized(permission, profile?.permissions ?? []);

  useEffect(() => {

    const handleShortcut = (event: KeyboardEvent) => {

      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setGlobalSearchOpen(value => !value); }

    };

    window.addEventListener("keydown", handleShortcut);

    return () => window.removeEventListener("keydown", handleShortcut);

  }, []);

  async function openSearchEntity(item: SearchResultItem) {

    if (item.type === "customer") {

      const customer = await transporte.solicitarOpenSearchEntity({ item });

      navigate("customers");

      setSelectedCustomer(customer);

    } else if (item.type === "product") {

      const product = await transporte.solicitarOpenSearchEntity2({ item });

      navigate("products");

      setSelectedProduct(product);

    } else if (item.type === "sale") {

      const sale = await transporte.solicitarOpenSearchEntity3({ item });

      navigate("sales");

      setSaleDetailModalSale(sale);

    } else if (item.type === "order") {

      await transporte.solicitarOpenSearchEntity4({ item });

      sessionStorage.setItem("salesia_context_order_id", item.id);

      navigate("orders");

      window.dispatchEvent(new Event("salesia:open-order"));

    } else if (item.type === "task") {

      const response = await transporte.solicitarOpenSearchEntity5();

      const task = response.items.find(row => row.id === item.id);

      if (!task) throw { detail: "La tarea no está disponible para tu usuario." };

      navigate("work");

      setDetail({ title: String(task.title), content: <div className="space-y-3 p-5 text-sm"><p>{String(task.description || "Sin descripción")}</p><p>Estado: {String(task.status)}</p><p>Prioridad: {String(task.priority)}</p><p>Vencimiento: {task.due_date ? new Date(String(task.due_date)).toLocaleString("es-PE", { timeZone: "America/Lima" }) : "Sin fecha"}</p><p className="text-xs text-slate-500">Puedes gestionar esta tarea desde Mi trabajo.</p></div> });

    } else {
      await apiClient.request(`/api/v1/business/records/${item.type}/${item.id}`);
      sessionStorage.setItem("salesia_record_context", JSON.stringify({ type: item.type, id: item.id }));
      navigate("records");
      window.dispatchEvent(new Event("salesia:open-record"));
    }

  }

  const [, setNavigationRevision] = useState(0);

  function navigate(next: View, replace = false, evidence?: Record<string, string>) {

    const normalized = next === "security" ? "profile_preferences" : next;

    const url = new URL(window.location.href);

    for (const key of Array.from(url.searchParams.keys())) if (key.startsWith("dashboard_")) url.searchParams.delete(key);
    for (const [key, value] of Object.entries(evidence || {})) url.searchParams.set(key, value);
    url.searchParams.set("view", normalized);
    setNavigationRevision(value => value + 1);

    window.history[replace ? "replaceState" : "pushState"]({ view: normalized }, "", `${url.pathname}${url.search}${url.hash}`);

    startTransition(() => {
      setView(normalized);
    });

    setPage(0);

    setSearch("");

    setError("");

    setSidebarHoveredTooltip(null);

  }

  useEffect(() => {

    const restore = () => {

      const next = viewFromUrl();
      setNavigationRevision(value => value + 1);

      startTransition(() => {
        setView(next);
      });

      setPage(0);

      setSearch("");

      setError("");

    };

    const requestedNavigation = (event: Event) => {

      const request = (event as CustomEvent<{ view?: View; evidence?: Record<string, string> }>).detail;
      const next = request?.view;

      if (next && viewKeys.has(next)) navigate(next, false, request.evidence);

    };

    window.addEventListener("popstate", restore);

    window.addEventListener("salesia:navigate", requestedNavigation);

    return () => {

      window.removeEventListener("popstate", restore);

      window.removeEventListener("salesia:navigate", requestedNavigation);

    };

  }, []);

  useEffect(() => {

    const refreshRelated = () => setRevision(value => value + 1);

    window.addEventListener(ENTITY_CHANGED_EVENT, refreshRelated);

    return () => window.removeEventListener(ENTITY_CHANGED_EVENT, refreshRelated);

  }, []);

  useEffect(() => {

    const syncPreferences = () => {

      setPageSize(getDefaultPageSize());

      setPage(0);

      setSidebarCollapsed(getSidebarMode() === "collapsed");

    };

    window.addEventListener(UI_PREFERENCES_EVENT, syncPreferences);

    return () => window.removeEventListener(UI_PREFERENCES_EVENT, syncPreferences);

  }, []);

  useEffect(() => {

    apiClient.getMe().then(user => { setProfile(user); hydrateRemoteUiPreferences(user); }).catch(failure => setError(message(failure)));

    transporte.solicitarDatos().then(comp => setCurrentCompany(comp)).catch(failure => setError(message(failure)));

    transporte.solicitarDatos2().then(list => {

      setBranches(list);

      if (list.length > 0 && !activeBranchId) setActiveBranchId(String(list[0].branch_id));

    }).catch(failure => setError(message(failure)));

  }, [revision]);

  useEffect(() => {
    if (!activeBranchId || branches.some(branch => String(branch.branch_id) === activeBranchId)) return;
    let active = true;
    void selectorSeed<Row>("branches", { ids: activeBranchId }).then(rows => { if (active && rows.length) setBranches(previous => [...previous, ...rows.filter(row => !previous.some(item => item.branch_id === row.branch_id))]); }).catch(() => undefined);
    return () => { active = false; };
  }, [activeBranchId, branches]);

  useEffect(() => {

    if (["warranties", "records", "payables", "expenses", "customers", "work", "dashboard", "categories", "pricing", "quotations", "orders", "probability", "reports", "organization", "team", "team_targets", "team_rules", "team_assignments", "team_settlements", "inventory", "collaboration", "sales_analytics", "customer_analytics", "datasets", "variables", "statistics", "insights", "analytics_history", "audit", "notifications", "imports", "users_roles", "settings", "settings_branches", "settings_numbering", "settings_rules", "settings_profile", "settings_functions", "settings_calendar", "settings_branding", "settings_appearance", "settings_return_policy", "integrations", "approvals", "health", "profile_preferences", "cash", "cash_movements", "cash_counts", "cash_custody", "cash_petty", "cash_forecast", "refunds", "refunds_settlements", "refunds_credit", "refunds_policy", "receivables"].includes(view)) return;

    if (new URLSearchParams(window.location.search).has("dashboard_evidence")) return;
    const controller = new AbortController();

    setLoading(true); setError(""); setRows([]);

    const path = view === "security" ? "/auth/sessions" : view === "sales" ? `/sales?page=${page + 1}&page_size=${pageSize}` : `/${view}?limit=${pageSize}&offset=${page * pageSize}&search=${encodeURIComponent(search)}`;

    transporte.solicitarDatos3({ path, controller }).then(result => {

      if (controller.signal.aborted) return;

      const items = Array.isArray(result) ? result : result.items;

      const recordCount = Array.isArray(result) ? items.length : result.total_count ?? result.count ?? items.length;

      const lastPage = Math.max(0, Math.ceil(recordCount / pageSize) - 1);

      setTotal(recordCount);

      if (page > lastPage) { setPage(lastPage); return; }

      setRows(view === "security" ? items.slice(page * pageSize, (page + 1) * pageSize) : items);

    }).catch(failure => { if (!controller.signal.aborted) setError(message(failure)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });

    return () => controller.abort();

  }, [view, page, pageSize, search, revision]);

  async function mutate(path: string, body: unknown, method = "POST") {

    const serialized = JSON.stringify(body);

    const fingerprint = `${method}:${path}:${serialized}`;

    if (!keys.current.has(fingerprint)) keys.current.set(fingerprint, crypto.randomUUID());

    const result = await transporte.solicitarMutate({ path, method, serialized, keys, fingerprint });

    keys.current.delete(fingerprint);

    let invalidationType: "confirm_sale" | "inventory_adjustment" | "payment" | "product_update" | undefined;

    if (path.includes("/confirm")) invalidationType = "confirm_sale";

    else if (path.includes("/payments")) invalidationType = "payment";

    else if (path.includes("/inventory")) invalidationType = "inventory_adjustment";

    else if (path.includes("/products")) invalidationType = "product_update";

    if (invalidationType) handleSelectiveInvalidation(queryClient, invalidationType);

    setRevision(value => value + 1);

    return result;

  }

  async function save(event: FormEvent<HTMLFormElement>) {

    event.preventDefault();

    if (!editor || busy) return;

    const values = Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string, string>;

    if (editor.path === "/api/v1/payments") {

      const sale = rows.find(r => r.sale_id === editor.values?.sale_id);

      setPaymentConfirm({

        amount: values.amount || String(editor.values?.amount || "0"),

        currency: String(editor.values?.currency || "USD"),

        customerName: String(sale?.customer_name || sale?.customer_id || "Cliente"),

        documentNumber: String(sale?.number || editor.values?.sale_id || "VENTA"),

        paymentMethod: values.payment_method || "CASH",

        path: editor.path,

        body: {

          ...editor.values,

          amount: values.amount,

          payment_method: values.payment_method,

          reference_code: values.reference_code || undefined

        }

      });

      setEditor(null);

      return;

    }

    setBusy(true); setError("");

    try {

      const body = editor.prepare ? editor.prepare(values) : { ...editor.values, ...Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value === "" ? null : value])) };

      const result = await mutate(editor.path, body, editor.method);

      if (editor.path.endsWith("/mfa/setup")) {

        const factor = result as unknown as { totp_secret: string; provisioning_uri: string; recovery_codes: string[] };

        setDetail({ title: "Configurar autenticador", content: <div className="space-y-4"><p>Añade esta clave a tu autenticador y guarda los códigos de recuperación en un lugar seguro. Cada código se puede usar una sola vez.</p><p className="break-all rounded-xl bg-slate-100 p-4 font-mono text-sm">{factor.totp_secret}</p><ul className="grid grid-cols-2 gap-2 font-mono text-xs">{factor.recovery_codes.map(code => <li key={code} className="break-all rounded bg-slate-100 p-2">{code}</li>)}</ul><button className={buttonStyle} onClick={() => { setDetail(null); setEditor({ title: "Activar MFA", fields: [{ name: "code", label: "Código de seis dígitos" }], path: "/api/v1/auth/mfa/verify" }); }}>Continuar y verificar código</button></div> });

      }

      setEditor(null); toast.success("Cambios guardados", "La operación fue confirmada por el servidor.");

    } catch (failure) { setError(message(failure)); toast.error("No se guardaron los cambios", message(failure)); }

    finally { setBusy(false); }

  }

  async function openEntity(row?: Row) {

    if (view === "customers") {

      setCustomerToEdit(row ? (row as unknown as CustomerData) : null);

      setCustomerDrawerOpen(true);

      return;

    }

    const fields: Field[] = [{ name: "name", label: "Nombre" }, { name: "category", label: "Categoría" }, { name: "unit_price", label: "Precio unitario", type: "number" }, { name: "unit_cost", label: "Costo unitario", type: "number", value: "0" }];

    if (!row) {

      let configuredTax = "0";

      try {

        const settings = await transporte.solicitarOpenEntity();

        configuredTax = String(settings.default_tax_rate ?? "0");

      } catch (failure) {

        toast.error("No se pudo cargar el impuesto configurado", message(failure));

        return;

      }

      fields.unshift({ name: "sku", label: "SKU" }, { name: "unit_of_measure", label: "Unidad de medida", value: "NIU" }, { name: "tax_rate", label: "Tasa de impuesto configurada", type: "number", value: configuredTax });

    }

    setEditor({ title: `${row ? "Editar" : "Crear"} producto`, fields: fields.map(field => ({ ...field, value: row ? String(row[field.name] ?? "") : field.value })), path: `/api/v1/${view}${row ? `/${row.id}` : ""}`, method: row ? "PATCH" : "POST" });

  }

  async function organization(action: "company" | "branch" | "warehouse" | "settings" | "onboarding") {

    try {

      if (action === "onboarding") {

        setOnboardingModalOpen(true);

      } else if (action === "company") {

        const row = await transporte.solicitarOrganization();

        setEditor({ title: "Datos de empresa", path: "/api/v1/companies/current", method: "PATCH", fields: [{ name: "legal_name", label: "Razón social", value: String(row.legal_name) }, { name: "trade_name", label: "Nombre comercial", value: String(row.trade_name) }, { name: "base_currency", label: "Moneda base", value: String(row.base_currency) }] });

      } else if (action === "branch") setEditor({ title: "Crear sucursal", path: "/api/v1/branches", fields: [{ name: "code", label: "Código" }, { name: "name", label: "Nombre" }, { name: "timezone", label: "Zona horaria", value: "America/Lima" }] });

      else if (action === "warehouse") {

        const branchesList = await transporte.solicitarOrganization2();

        setEditor({ title: "Crear almacén", path: "/api/v1/warehouses", fields: [{ name: "branch_id", label: "Sucursal", options: branchesList.filter(row => row.is_active).map(row => ({ value: String(row.branch_id), label: String(row.name) })) }, { name: "code", label: "Código" }, { name: "name", label: "Nombre" }] });

      } else {

        const settings = await transporte.solicitarOrganization3();

        setEditor({

          title: "Configuración comercial",

          path: "/api/v1/companies/current/settings",

          method: "PATCH",

          values: { version: settings.version },

          fields: [

            { name: "default_tax_rate", label: "Impuesto predeterminado (0 = Exonerado, 0.18 = 18 %)", type: "number", value: String(settings.default_tax_rate ?? "0.18") },

            { name: "rounding_mode", label: "Modo de redondeo", options: [{ value: "ROUND_HALF_EVEN", label: "Contable bancario (ROUND_HALF_EVEN)" }, { value: "ROUND_HALF_UP", label: "Estándar (ROUND_HALF_UP)" }] },

            { name: "closed_until", label: "Cierre contable (bloquear ventas hasta)", type: "date", optional: true, value: String(settings.closed_until ?? "") }

          ]

        });

      }

    } catch (failure) { toast.error("No se pudo cargar la configuración", message(failure)); }

  }

  const columns: Record<string, [string, string][]> = {

    customers: [["code", "Código"], ["legal_name", "Cliente"], ["doc_number", "Documento"], ["current_balance", "Saldo"], ["is_active", "Activo"]],

    products: [["sku", "SKU"], ["name", "Producto"], ["category", "Categoría"], ["unit_price", "Precio"], ["is_active", "Activo"]],

    inventory: [["product_id", "Producto"], ["warehouse_id", "Almacén"], ["physical_quantity", "Físico"], ["reserved_quantity", "Reservado"], ["available_quantity", "Disponible"]],

    sales: [["number", "Documento"], ["status", "Estado"], ["currency", "Moneda"], ["total_amount", "Total"], ["paid_amount", "Cobrado"]],

    security: [["user_agent", "Dispositivo"], ["ip_address", "Dirección"], ["created_at", "Inicio"], ["is_current", "Sesión actual"]]

  };
  return { globalSearchOpen, setGlobalSearchOpen, profile, currentCompany, setCurrentCompany, branches, activeBranchId, setActiveBranchId, view, setRows, page, setPage, pageSize, setPageSize, search, setSearch, revision, setRevision, busy, setBusy, setError, editor, setEditor, confirm, setConfirm, paymentConfirm, setPaymentConfirm, detail, setDetail, selectedCustomer, setSelectedCustomer, selectedProduct, setSelectedProduct, activeReturnSale, setActiveReturnSale, companySelectorOpen, setCompanySelectorOpen, onboardingModalOpen, setOnboardingModalOpen, rows, total, loading, error, customerDrawerOpen, setCustomerDrawerOpen, customerToEdit, posModalOpen, setPosModalOpen, productDialogOpen, setProductDialogOpen, posInitialCustomerId, setPosInitialCustomerId, posSourceSaleId, setPosSourceSaleId, saleDetailModalSale, setSaleDetailModalSale, sidebarCollapsed, setSidebarCollapsed, sidebarHoveredTooltip, setSidebarHoveredTooltip, toast, queryClient, can, openSearchEntity, navigate, mutate, save, openEntity, organization, columns };
}