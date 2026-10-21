import { ReturnPolicyPanel } from "../features/devoluciones/components/ReturnPolicyPanel";
import { useState, useEffect } from "react";
import { OperatingAreaNotice, OperatingProfileProvider, OperatingSection } from "../features/organizacion/components/OperatingProfileContext";
import { WarrantyWorkspace } from "../features/garantias/components/WarrantyWorkspace";
import { BusinessRecordsWorkspace } from "../features/operaciones/components/BusinessRecordsWorkspace";
import { FinancialManagementWorkspace } from "../features/finanzas/components/FinancialManagementWorkspace";
import { Panel1 } from "./workspace/sections/OperationsWorkspace/Panel1";
import { Panel2 } from "./workspace/sections/OperationsWorkspace/Panel2";
import { Panel3 } from "./workspace/sections/OperationsWorkspace/Panel3";
import { Panel4 } from "./workspace/sections/OperationsWorkspace/Panel4";
import { Panel5 } from "./workspace/sections/OperationsWorkspace/Panel5";
import { Panel6 } from "./workspace/sections/OperationsWorkspace/Panel6";
export { sections } from "./workspace/support/OperationsWorkspace";
export { isModuleAuthorized } from "./workspace/support/OperationsWorkspace";
import { useOperationsWorkspace } from "./workspace/hooks/useOperationsWorkspace";
import { ClientesPage } from "../features/clientes/pages/ClientesPage";
import { VentasPage } from "../features/ventas/pages/VentasPage";
import { NavbarHeaderProvider } from "../ui/components/NavbarSectionHeader";
import "../ui/workspace.css";
import { Suspense } from "react";
import { EnterpriseErrorBoundary } from "../ui/components/primitives/EnterpriseErrorBoundary";
import { AppNavbar, NavView } from "../ui/components/AppNavbar";
import { ShieldCheck } from "lucide-react";
import { apiClient, SearchResultItem } from "../api/client";
import { GlobalEntitySearch } from "../features/busqueda/components/GlobalEntitySearch";
import { DashboardEvidencePanel, hasDashboardEvidence } from "../features/analitica/components/DashboardEvidencePanel";
import { DashboardAnalyticsTab } from "../features/analitica/components/DashboardAnalyticsTab";
import { ProbabilityWorkspaceTab } from "../features/analitica/components/ProbabilityWorkspaceTab";
import { CustomerCommercialCard } from "../features/clientes/ficha/CustomerCommercialCard";
import { ProductCommercialCard } from "../features/catalogo/components/ProductCommercialCard";
import { QuickProductDialog } from "../features/catalogo/components/QuickProductDialog";
import { SalesTeamTab } from "../features/equipo/components/SalesTeamTab";
import { CollaborationWorkspaceTab } from "../features/trabajo/components/CollaborationWorkspaceTab";
import { PaymentConfirmationModal } from "../features/ventas/components/PaymentConfirmationModal";
import { ReturnWizardModal } from "../features/devoluciones/components/ReturnWizardModal";
import { CompanySelectorModal } from "../features/organizacion/components/CompanySelectorModal";
import { OnboardingWizardModal } from "../features/organizacion/components/OnboardingWizardModal";
import { PersonalWorkspaceTab } from "../features/trabajo/components/PersonalWorkspaceTab";
import { CustomerEditorDrawer } from "../features/clientes/editor/CustomerEditorDrawer";
import { CategoriesAndUnitsTab } from "../features/catalogo/components/CategoriesAndUnitsTab";
import { PricingAndPromotionsTab } from "../features/precios/components/PricingAndPromotionsTab";
import { QuotationsWorkspaceTab } from "../features/cotizaciones/components/QuotationsWorkspaceTab";
import { OrdersWorkspaceTab } from "../features/pedidos/components/OrdersWorkspaceTab";
import { NewSalePOSModal } from "../features/ventas/components/NewSalePOSModal";
import { SaleDetailModal } from "../features/ventas/components/SaleDetailModal";
import { AccountsReceivableTab } from "../features/cuentas_cobrar/components/AccountsReceivableTab";
import { CashRegisterWorkspaceTab } from "../features/caja/components/CashRegisterWorkspaceTab";
import { RefundsWorkspaceTab } from "../features/devoluciones/components/RefundsWorkspaceTab";
import { SalesAnalyticsTab } from "../features/analitica/components/SalesAnalyticsTab";
import { CustomerAnalyticsTab } from "../features/clientes/analitica/CustomerAnalyticsTab";
import { DataQualityPanel } from "../features/analitica/components/DataQualityPanel";
import { VariablesDictionaryTab } from "../features/analitica/components/VariablesDictionaryTab";
import { StatisticalEngineWorkspaceTab } from "../features/analitica/components/StatisticalEngineWorkspaceTab";
import { InsightsEnterpriseView } from "../features/insights/components/InsightsEnterpriseView";
import { AnalyticsHistoryWorkspaceTab } from "../features/analitica/components/AnalyticsHistoryWorkspaceTab";
import { AuditWorkspaceTab } from "../features/auditoria/components/AuditWorkspaceTab";
import { NotificationsWorkspaceTab } from "../features/notificaciones/components/NotificationsWorkspaceTab";
import { Row } from "./workspace/types/OperationsWorkspace";
import { View } from "./workspace/types/OperationsWorkspace";
import { ReportsWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { InventoryWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { ImportsWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { UsersAndRolesWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { CompanySettingsWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { IntegrationsWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { ApprovalsInboxWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { SystemHealthSupportWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { UserProfilePreferencesWorkspaceTab } from "./workspace/support/OperationsWorkspace";
import { TabFallback } from "./workspace/support/OperationsWorkspace";
import { buttonStyle } from "./workspace/support/OperationsWorkspace";
import { sections } from "./workspace/support/OperationsWorkspace";
import { message } from "./workspace/support/OperationsWorkspace";
import { Dialog } from "./workspace/support/OperationsWorkspace";

export function OperationsWorkspace() {
const { globalSearchOpen, setGlobalSearchOpen, profile, currentCompany, setCurrentCompany, branches, activeBranchId, setActiveBranchId, view, setRows, page, setPage, pageSize, setPageSize, search, setSearch, revision, setRevision, busy, setBusy, setError, editor, setEditor, confirm, setConfirm, paymentConfirm, setPaymentConfirm, detail, setDetail, selectedCustomer, setSelectedCustomer, selectedProduct, setSelectedProduct, activeReturnSale, setActiveReturnSale, companySelectorOpen, setCompanySelectorOpen, onboardingModalOpen, setOnboardingModalOpen, rows, total, loading, error, customerDrawerOpen, setCustomerDrawerOpen, customerToEdit, posModalOpen, setPosModalOpen, productDialogOpen, setProductDialogOpen, posInitialCustomerId, setPosInitialCustomerId, posSourceSaleId, setPosSourceSaleId, saleDetailModalSale, setSaleDetailModalSale, sidebarCollapsed, setSidebarCollapsed, sidebarHoveredTooltip, setSidebarHoveredTooltip, toast, queryClient, can, openSearchEntity, navigate, mutate, save, openEntity, organization, columns } = useOperationsWorkspace();
  const [dashboardAllBranches, setDashboardAllBranches] = useState(false);
  useEffect(() => { setDashboardAllBranches(false); }, [activeBranchId, profile?.company_id]);
  const changeOperationalBranch = async (id: string) => {

              try {

                await mutate("/api/v1/organization/context/switch", { branch_id: id });

                setActiveBranchId(id);
                setDashboardAllBranches(false);

                setRows([]);

                setPage(0);

                setSearch("");

                queryClient.clear();

                toast.info("Sede cambiada", "Contexto actualizado e invalidación de caché aplicada.");

              } catch (err) {

                toast.error("Error al cambiar sede", message(err));

              }

            };

  const selectDashboardBranch = (id: string) => {
    if (!id) setDashboardAllBranches(true);
    else { setDashboardAllBranches(false); if (id !== activeBranchId) void changeOperationalBranch(id); }
  };

return (

    <OperatingProfileProvider companyId={profile?.company_id || ""}><NavbarHeaderProvider view={view}>

      <div

        className={`min-h-screen lg:grid ${sidebarCollapsed ? "lg:grid-cols-[72px_1fr]" : "lg:grid-cols-[260px_1fr]"} transition-all duration-200 text-slate-900`}

        style={{ background: "var(--sb-page-bg)" }}

      >

        <aside

          style={{

            background: "var(--sb-bg)",

            borderRight: "1px solid var(--sb-border)",

            fontFamily: "'Inter', sans-serif",

            width: sidebarCollapsed ? "72px" : "260px",

            overscrollBehavior: "contain",

          }}

          className="flex flex-col lg:sticky lg:top-0 lg:h-screen transition-all duration-200 select-none overflow-x-hidden overscroll-contain"

        >

          {sidebarCollapsed ? (

            <div style={{ borderBottom: "1px solid var(--sb-border)" }} className="flex h-16 items-center justify-center px-2">

              <div

                style={{ background: "var(--sb-active)" }}

                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl shadow-xs"

              >

                <ShieldCheck className="h-6 w-6 text-white" />

              </div>

            </div>

          ) : (

            <div style={{ borderBottom: "1px solid var(--sb-border)" }} className="flex h-16 items-center gap-3.5 px-5">

              <div

                style={{ background: "var(--sb-active)" }}

                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl shadow-xs"

              >

                <ShieldCheck className="h-6 w-6 text-white" />

              </div>

              <div className="leading-tight truncate">

                <p style={{ color: "var(--sb-text)" }} className="text-base font-bold tracking-tight">SalesIA</p>

                <p style={{ color: "var(--sb-muted)" }} className="text-[11px] font-semibold uppercase tracking-[0.16em]">Enterprise</p>

              </div>

            </div>

          )}

          <Panel1 setSidebarHoveredTooltip={setSidebarHoveredTooltip} sidebarCollapsed={sidebarCollapsed} can={can} view={view} navigate={navigate} />

          <Panel2 sidebarCollapsed={sidebarCollapsed} setSidebarCollapsed={setSidebarCollapsed} setSidebarHoveredTooltip={setSidebarHoveredTooltip} />

        </aside>

        <div className={`flex flex-col min-w-0 ${view === "users_roles" || view === "sales" ? "h-screen max-h-screen overflow-hidden" : ""}`}>

          <AppNavbar

            view={view as NavView}

            viewLabel={sections.find(s => s.key === view)?.label ?? ""}

            onNavigate={(v: NavView) => navigate(v as View)}

            permissions={profile?.permissions ?? []}

            email={profile?.email ?? ""}

            role={profile?.role ?? ""}

            companyName={String(currentCompany?.legal_name || currentCompany?.trade_name || "")}

            branches={branches as Array<{ branch_id?: string; name?: string; code?: string; is_active?: boolean }>}

            activeBranchId={activeBranchId}

            onBranchChange={changeOperationalBranch}
            comparativeAllBranches={view === "dashboard" && dashboardAllBranches}

            onOpenCompanySelector={() => setCompanySelectorOpen(true)}

            onLogout={() => void apiClient.logout()}

            onOpenSearch={() => setGlobalSearchOpen(true)}

          />

          <GlobalEntitySearch open={globalSearchOpen} onClose={() => setGlobalSearchOpen(false)} onSelect={openSearchEntity} />

          <main data-workspace={view} className={`min-w-0 flex-1 ${view === "users_roles" || view === "inventory" || view === "sales" ? "p-3 sm:p-4 lg:px-5 lg:pt-3 lg:pb-3 flex flex-col min-h-0 h-[calc(100vh-64px)] max-h-[calc(100vh-64px)] overflow-hidden w-full" : view === "dashboard" ? "px-5 pb-5 pt-3 lg:px-8 lg:pb-8 lg:pt-3" : "p-5 lg:p-8"} ${view !== "work" && view !== "dashboard" ? "enterprise-workspace" : ""}`}>

            <EnterpriseErrorBoundary fallbackTitle="Error al cargar la sección"><OperatingAreaNotice view={view} />
              <OperatingSection view={view}>{operatingAllowed => <Suspense fallback={<TabFallback />}>
                {hasDashboardEvidence(view) ? <DashboardEvidencePanel onBack={() => navigate("dashboard")} onOpenModule={() => navigate(view)} /> : view === "work" ? (

              <PersonalWorkspaceTab

                branchId={activeBranchId}

                branches={branches as Array<{ branch_id?: string; name?: string; code?: string; timezone?: string }>}

                baseCurrency={String(currentCompany?.base_currency || "USD")}

                onOpenResource={(type, id) => {
                  if (!["customer", "product", "sale", "order", "task"].includes(type)) return;
                  void openSearchEntity({ type: type as SearchResultItem["type"], id, title: "Registro relacionado", subtitle: "" }).catch(failure => toast.error("Registro no disponible", message(failure)));
                }}
                onNavigate={(target) => navigate(target as View)}

              />

            ) :

              view === "dashboard" ? <DashboardAnalyticsTab branchContext={{ operationalBranchId: activeBranchId, allBranches: dashboardAllBranches, onSelectBranch: selectDashboardBranch }} /> :

                view === "categories" ? <CategoriesAndUnitsTab canWrite={operatingAllowed && can("products:write")} /> :

                  view === "pricing" ? <PricingAndPromotionsTab canWrite={operatingAllowed && can("products:write")} /> :

                    view === "quotations" ? <QuotationsWorkspaceTab canWrite={operatingAllowed && can("sales:write")} /> :

                      view === "orders" ? <OrdersWorkspaceTab canWrite={operatingAllowed && can("sales:write")} /> :

                        view === "probability" ? <ProbabilityWorkspaceTab /> :

                          view === "reports" ? <Suspense fallback={<TabFallback />}><ReportsWorkspaceTab canExport={can("reports:export")} /></Suspense> :

                            (view === "team" || view === "team_targets" || view === "team_rules" || view === "team_assignments" || view === "team_settlements") ? <SalesTeamTab section={view === "team" ? "team" : view === "team_targets" ? "targets" : view === "team_rules" ? "rules" : view === "team_assignments" ? "assignments" : "settlements"} /> :

                              view === "inventory" ? <Suspense fallback={<TabFallback />}><InventoryWorkspaceTab canWrite={operatingAllowed && can("inventory:write")} /></Suspense> :

                                view === "warranties" ? <WarrantyWorkspace canWrite={operatingAllowed && can("sales:write")} /> : view === "records" ? <BusinessRecordsWorkspace canConfigure={can("organization:manage")} storageScope={`${profile?.company_id || ""}:${profile?.user_id || ""}`} /> : view === "payables" || view === "expenses" ? <FinancialManagementWorkspace mode={view} permissions={profile?.permissions || []} userId={profile?.user_id} /> : view === "receivables" ? <AccountsReceivableTab canWrite={operatingAllowed && can("payments:write")} /> :

                                  (view === "cash" || view === "cash_movements" || view === "cash_counts" || view === "cash_custody" || view === "cash_petty" || view === "cash_forecast") ? <CashRegisterWorkspaceTab section={view === "cash_movements" ? "movements" : view === "cash_counts" ? "counts" : view === "cash_custody" ? "custody" : view === "cash_petty" ? "petty" : view === "cash_forecast" ? "forecast" : "sessions"} canWrite={operatingAllowed && can("cash:register:manage")} currentBranchId={activeBranchId} /> :

                                    (view === "refunds" || view === "refunds_settlements" || view === "refunds_credit") ? <RefundsWorkspaceTab section={view === "refunds_settlements" ? "settlements" : view === "refunds_credit" ? "credit" : "refunds"} onNavigate={section => navigate(section === "settlements" ? "refunds_settlements" : section === "credit" ? "refunds_credit" : section === "policy" ? "settings_return_policy" : "refunds")} canWrite={operatingAllowed && can("payments:write")} /> :

                                      view === "collaboration" ? <CollaborationWorkspaceTab canApprove={can("approvals:manage")} /> :

                                        view === "sales_analytics" ? <SalesAnalyticsTab canWrite={operatingAllowed && can("sales:write")} /> :

                                          view === "customer_analytics" ? <CustomerAnalyticsTab canWrite={operatingAllowed && can("customers:write")} /> :

                                            view === "datasets" ? <DataQualityPanel /> :

                                              view === "variables" ? <VariablesDictionaryTab canWrite={operatingAllowed && can("analytics:dataset:read")} /> :

                                                view === "statistics" ? <StatisticalEngineWorkspaceTab canWrite={operatingAllowed && can("analytics:calculate")} /> :

                                                  view === "insights" ? <InsightsEnterpriseView /> :

                                                    view === "analytics_history" ? <AnalyticsHistoryWorkspaceTab canWrite={operatingAllowed && can("analytics:dataset:read")} /> :

                                                      view === "audit" ? <AuditWorkspaceTab canWrite={operatingAllowed && can("audit:logs:export")} /> :

                                                        view === "notifications" ? <NotificationsWorkspaceTab canWrite={true} userPermissions={profile?.permissions || []} onNavigate={(target) => navigate(target as View)} /> :

                                                          view === "imports" ? <Suspense fallback={<TabFallback />}><ImportsWorkspaceTab permissions={profile?.permissions || []} /></Suspense> :

                                                            view === "users_roles" ? <Suspense fallback={<TabFallback />}><UsersAndRolesWorkspaceTab canWrite={operatingAllowed && can("users:manage")} currentUserRole={profile?.role || "sales_rep"} /></Suspense> :

                                                              (view === "settings_return_policy" || view === "refunds_policy") ? <ReturnPolicyPanel standalone canWrite={operatingAllowed} /> : (view === "settings" || view === "settings_branches" || view === "settings_numbering" || view === "settings_rules" || view === "settings_profile" || view === "settings_functions" || view === "settings_calendar" || view === "settings_branding" || view === "settings_appearance") ? <Suspense fallback={<TabFallback />}><CompanySettingsWorkspaceTab section={view === "settings_branches" ? "branches" : view === "settings_numbering" ? "numbering" : view === "settings_rules" ? "rules" : view === "settings_profile" ? "profile" : view === "settings_functions" ? "functions" : view === "settings_calendar" ? "calendar" : view === "settings_branding" ? "branding" : view === "settings_appearance" ? "appearance" : "company"} canWrite={operatingAllowed && can("organization:manage")} /></Suspense> :

                                                                view === "integrations" ? <Suspense fallback={<TabFallback />}><IntegrationsWorkspaceTab canWrite={operatingAllowed && can("operations:manage")} /></Suspense> :

                                                                  view === "approvals" ? <Suspense fallback={<TabFallback />}><ApprovalsInboxWorkspaceTab canWrite={operatingAllowed && can("approvals:manage")} /></Suspense> :

                                                                    view === "health" ? <Suspense fallback={<TabFallback />}><SystemHealthSupportWorkspaceTab isTechAdmin={can("operations:manage")} /></Suspense> :

                                                                      view === "profile_preferences" ? <Suspense fallback={<TabFallback />}><UserProfilePreferencesWorkspaceTab /></Suspense> :

                                                                        view === "organization" ? (

                                                                          <Panel3 organization={organization} />

                                                                        ) : (
                                                                           (view === "customers" ? <ClientesPage rows={rows} total={total} loading={loading} search={search} page={page} pageSize={pageSize} error={error} editorOpen={Boolean(editor)} confirmationOpen={Boolean(confirm)} canWrite={operatingAllowed && can("customers:write")} setSearch={setSearch} setPage={setPage} setPageSize={setPageSize} onRefresh={() => setRevision(value => value + 1)} openEntity={openEntity} setSelectedCustomer={setSelectedCustomer} setConfirm={setConfirm} /> : view === "sales" ? <VentasPage key={window.location.search} canReadCosts={can("products:cost:read")} branches={branches as Array<{ branch_id?: string; name: string }>} canWrite={operatingAllowed && can("sales:write")} canCancel={can("sales:write")} onOpenNewSale={(saleId?: string) => { if (typeof saleId === "string") { setPosSourceSaleId(saleId); } else { setPosSourceSaleId(undefined); } setPosModalOpen(true); }} onOpenDetail={(sale) => setSaleDetailModalSale(sale as unknown as typeof saleDetailModalSale)} currency={(currentCompany as unknown as { currency?: string })?.currency || "PEN"} revision={revision} /> : <Panel4 view={view} loading={loading} total={total} search={search} setSearch={setSearch} setPage={setPage} setRevision={setRevision} can={can} setEditor={setEditor} setProductDialogOpen={setProductDialogOpen} busy={busy} setPosInitialCustomerId={setPosInitialCustomerId} setPosSourceSaleId={setPosSourceSaleId} setPosModalOpen={setPosModalOpen} error={error} editor={editor} confirm={confirm} columns={columns} rows={rows} setSelectedProduct={setSelectedProduct} openEntity={openEntity} setConfirm={setConfirm} setSaleDetailModalSale={setSaleDetailModalSale} setActiveReturnSale={setActiveReturnSale} toast={toast} page={page} pageSize={pageSize} setPageSize={setPageSize} />)
                                                                        )}
              </Suspense>}</OperatingSection>
            </EnterpriseErrorBoundary>

          </main>

          {editor && (

            <Panel5 editor={editor} busy={busy} setEditor={setEditor} setError={setError} save={save} error={error} />

          )}

          {confirm && (

            <Dialog title={confirm.title} close={() => { if (!busy) setConfirm(null); }}>

              <div className="space-y-5 p-6">

                <p className="text-sm leading-relaxed text-slate-600">{confirm.text}</p>

                {error && <p role="alert" className="text-sm text-red-700">{error}</p>}

                <div className="flex justify-end gap-3">

                  <button className={buttonStyle} disabled={busy} onClick={() => setConfirm(null)}>Volver</button>

                  <button disabled={busy} className="inline-flex items-center justify-center gap-2 rounded-xl bg-teal-600 hover:bg-teal-500 active:bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white shadow-md transition active:scale-95 disabled:opacity-50" onClick={async () => { setBusy(true); setError(""); try { await mutate(confirm.path, confirm.body); setConfirm(null); toast.success("Operación confirmada"); } catch (failure) { setError(message(failure)); } finally { setBusy(false); } }}>

                    {busy ? "Procesando…" : "Confirmar"}

                  </button>

                </div>

              </div>

            </Dialog>

          )}

          {paymentConfirm && (

            <PaymentConfirmationModal

              isOpen={Boolean(paymentConfirm)}

              amount={paymentConfirm.amount}

              currency={paymentConfirm.currency}

              customerName={paymentConfirm.customerName}

              documentNumber={paymentConfirm.documentNumber}

              paymentMethod={paymentConfirm.paymentMethod}

              onClose={() => setPaymentConfirm(null)}

              onConfirm={async () => {

                const res = await mutate(paymentConfirm.path, paymentConfirm.body);

                toast.success("Cobro confirmado", "La operación fue confirmada por el servidor.");

                return { status: String(res.status || "confirmed") };

              }}

            />

          )}

          {activeReturnSale && (

            <ReturnWizardModal

              isOpen={Boolean(activeReturnSale)}

              onClose={() => setActiveReturnSale(null)}

              saleId={String(activeReturnSale.sale_id ?? activeReturnSale.id)}

              documentNumber={String(activeReturnSale.number || activeReturnSale.series || "VENTA")}

              customerName={String(activeReturnSale.customer_name || activeReturnSale.customer_id || "Cliente")}

              warehouseId={String(activeReturnSale.warehouse_id || "")}

              onSuccess={() => { setRevision(value => value + 1); }}

            />

          )}

          {detail && (

            <Dialog title={detail.title} close={() => setDetail(null)}>

              <div className="p-6 text-sm text-slate-700">{detail.content}</div>

            </Dialog>

          )}

          {selectedCustomer && (

            <CustomerCommercialCard

              customerId={String(selectedCustomer.id)}

              customerName={String(selectedCustomer.legal_name)}

              canWrite={can("customers:write")}

              allCustomers={rows}

              onClose={() => setSelectedCustomer(null)}

              onRefresh={() => setRevision(value => value + 1)}

              onAction={(action, resourceId) => {

                const customerId = String(selectedCustomer.id);

                if (action === "sale" || action === "repeat") {

                  setPosInitialCustomerId(customerId);

                  setPosSourceSaleId(resourceId);

                  setSelectedCustomer(null);

                  setPosModalOpen(true);

                  return;

                }

                sessionStorage.setItem("salesia_context_customer_id", customerId);

                if (action === "quotation") sessionStorage.setItem("salesia_open_quotation", "true");

                if (action === "order") sessionStorage.setItem("salesia_open_order", "true");

                setSelectedCustomer(null);

                navigate(action === "quotation" ? "quotations" : action === "order" ? "orders" : "receivables");

              }}

            />

          )}

          {selectedProduct && (

            <ProductCommercialCard

              productId={String(selectedProduct.id)}

              productName={String(selectedProduct.name)}

              canWrite={can("products:write")}

              allProducts={rows}

              onClose={() => setSelectedProduct(null)}

              onRefresh={() => setRevision(value => value + 1)}

            />

          )}

          <CompanySelectorModal

            isOpen={companySelectorOpen}

            currentCompanyId={currentCompany ? String(currentCompany.id) : undefined}

            onClose={() => setCompanySelectorOpen(false)}

            onCompanySelected={comp => {

              setCurrentCompany(comp as unknown as Row);

              setRevision(r => r + 1);

            }}

          />

          <OnboardingWizardModal

            isOpen={onboardingModalOpen}

            onClose={() => setOnboardingModalOpen(false)}

            onCompleted={() => {

              setRevision(r => r + 1);

            }}

          />

          <CustomerEditorDrawer

            isOpen={customerDrawerOpen}

            initialData={customerToEdit}

            onClose={() => setCustomerDrawerOpen(false)}

            onSaved={() => {

              setRevision(r => r + 1);

            }}

          />

          <NewSalePOSModal

            isOpen={posModalOpen}

            initialCustomerId={posInitialCustomerId}

            sourceSaleId={posSourceSaleId}

            onClose={() => { setPosModalOpen(false); setPosInitialCustomerId(undefined); setPosSourceSaleId(undefined); }}

            onSaleCreated={(saleId, isDraft) => {

              setRevision(r => r + 1);

              if (!isDraft) {
                setSaleDetailModalSale({ id: saleId, status: "confirmed", currency: String(currentCompany?.base_currency || ""), total_amount: "0", paid_amount: "0" });
              }

            }}

          />

          <QuickProductDialog

            isOpen={productDialogOpen}

            currency={String(currentCompany?.base_currency || "USD")}

            defaultTaxRate={String(currentCompany?.default_tax_rate || "0.18")}

            onClose={() => setProductDialogOpen(false)}

            onCreated={() => { setProductDialogOpen(false); setRevision(value => value + 1); }}

          />

          <SaleDetailModal

            sale={saleDetailModalSale}

            canWrite={can("sales:write")}

            onClose={() => setSaleDetailModalSale(null)}

            onConfirmSale={async id => {

              try {

                await mutate(`/api/v1/sales/${id}/confirm`, { is_credit_sale: false });

                toast.success("Venta confirmada");

                setSaleDetailModalSale(null);

              } catch (e) {

                toast.error("Error", message(e));

              }

            }}

            onOpenPayment={s => {

              setSaleDetailModalSale(null);

              setEditor({

                title: "Registrar cobro",

                path: "/api/v1/payments",

                values: { sale_id: s.id, currency: s.currency },

                fields: [

                  { name: "amount", label: "Importe", type: "number", value: String(Number(s.total_amount) - Number(s.paid_amount)) },

                  { name: "payment_method", label: "Método", options: [{ value: "CASH", label: "Efectivo" }, { value: "TRANSFER", label: "Transferencia" }] },

                  { name: "reference_code", label: "Referencia bancaria", optional: true }

                ]

              });

            }}

            onOpenReturn={s => {

              setSaleDetailModalSale(null);

              setActiveReturnSale(s as unknown as Row);

            }}

            onCancelSale={async id => {

              try {

                await mutate(`/api/v1/sales/${id}/cancel`, { reason: "Cancelado desde panel de detalle" });

                toast.success("Venta anulada");

                setSaleDetailModalSale(null);

              } catch (e) {

                toast.error("Error", message(e));

              }

            }}

          />

        </div>

        {sidebarCollapsed && sidebarHoveredTooltip && (

          <Panel6 sidebarHoveredTooltip={sidebarHoveredTooltip} />

        )}

      </div>

    </NavbarHeaderProvider></OperatingProfileProvider>

  );
}
