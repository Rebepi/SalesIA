import React, { useState } from "react";
import {
  Button,
  IconButton,
  Input,
  MoneyInput,
  Select,
  DatePicker,
  Modal,
  Drawer,
  DataTable,
  Pagination,
  Tabs,
  Accordion,
  Tooltip,
  Popover,
  Badge,
  Avatar,
  Skeleton,
  ProgressBar,
  AlertBanner,
  KpiCard,
  DropdownMenu,
  ConfirmDialog,
  Switch,
  Checkbox,
  FileUploader,
  EmptyState,
  FormSection,
  FormErrorSummary,
  RecoverableErrorBanner,
  ContextualHelp,
  PrintableDocumentLayout,
  TableColumn
} from "./index";
import {
  CheckCircleIcon,
  CancelXIcon,
  SearchIcon,
  SettingsIcon,
  TagIcon,
  SquarePenIcon,
  Trash2Icon,
  IconMatrixCatalog
} from "../icons/index";
import { useMotion } from "../motion";
import { useToast } from "../toast/ToastContext";
import {
  DARK_THEME,
  LIGHT_THEME,
  DENSITY_TOKENS,
  TYPOGRAPHY_TOKENS,
  SPACING_TOKENS,
  RADIUS_TOKENS,
  SHADOW_TOKENS,
  ThemeMode,
  DensityMode,
  getStoredThemePreference,
  setStoredThemePreference,
  setStoredDensityPreference,
  applyBrandTokens,
  getActionHierarchyVariant,
  getDualEncodedStatus
} from "../tokens";

interface CatalogProduct {
  id: string;
  sku: string;
  name: string;
  unitPrice: string;
  stock: number;
  status: string;
}

const SYNTHETIC_PRODUCTS: CatalogProduct[] = [
  {
    id: "prod-1",
    sku: "LAPTOP-001",
    name: "Laptop ThinkPad T14s AMD Ryzen 7 PRO 32GB RAM SSD 1TB Pantalla Antirreflejo",
    unitPrice: "1,299.99 USD",
    stock: 15,
    status: "approved"
  },
  {
    id: "prod-2",
    sku: "MOUSE-002",
    name: "Mouse Ergonómico Inalámbrico Bluetooth Recargable",
    unitPrice: "49.50 USD",
    stock: 3,
    status: "pending"
  },
  {
    id: "prod-3",
    sku: "MON-003",
    name: "Monitor 27 Pulgadas 4K IPS HDR400 Calibración de Fábrica",
    unitPrice: "389.00 USD",
    stock: 0,
    status: "rejected"
  }
];

export interface ComponentCatalogProps {
  initialTab?: "tokens" | "buttons" | "forms" | "tables" | "modals" | "feedback" | "patterns" | "mobile" | "motion";
}

export const ComponentCatalog: React.FC<ComponentCatalogProps> = ({ initialTab = "tokens" }) => {
  const toast = useToast();
  const motionCtx = useMotion();

  const [activeTab, setActiveTab] = useState<
    "tokens" | "buttons" | "forms" | "tables" | "modals" | "feedback" | "patterns" | "mobile" | "motion"
  >(initialTab);
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => getStoredThemePreference());
  const [densityMode, setDensityMode] = useState<DensityMode>("comfortable");
  const [inputText, setInputText] = useState("");
  const [moneyValue, setMoneyValue] = useState("150.00");
  const [selectValue, setSelectValue] = useState("option1");
  const [dateValue, setDateValue] = useState("2026-10-10");
  const [switchChecked, setSwitchChecked] = useState(true);
  const [checkboxChecked, setCheckboxChecked] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const toggleTheme = () => {
    const next = themeMode === "dark" ? "light" : "dark";
    setThemeMode(next);
    setStoredThemePreference(next);
  };

  const toggleDensity = () => {
    const next = densityMode === "comfortable" ? "compact" : "comfortable";
    setDensityMode(next);
    setStoredDensityPreference(next);
  };

  const productColumns: TableColumn<CatalogProduct>[] = [
    { key: "sku", header: "SKU", align: "left" },
    {
      key: "name",
      header: "Descripción",
      align: "left",
      expandable: true
    },
    {
      key: "unitPrice",
      header: "Precio Unitario",
      align: "right",
      render: (row) => (
        <span className="font-mono text-emerald-400 font-medium">{row.unitPrice}</span>
      )
    },
    {
      key: "stock",
      header: "Existencias",
      align: "right",
      render: (row) => <span className="font-mono">{row.stock} un.</span>
    },
    {
      key: "status",
      header: "Estado",
      align: "center",
      render: (row) => {
        const dual = getDualEncodedStatus(row.status);
        return (
          <Badge variant={dual.variant}>
            <span>{dual.symbol}</span>
            <span>{dual.text}</span>
          </Badge>
        );
      }
    }
  ];

  const currentTheme = themeMode === "dark" ? DARK_THEME : LIGHT_THEME;

  return (
    <div
      className={`min-h-screen ${
        themeMode === "dark" ? "bg-slate-950 text-slate-100" : "bg-slate-50 text-slate-900"
      } p-6 max-w-7xl mx-auto space-y-8`}
    >
      <header className="border-b border-slate-800 pb-5 flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            Catálogo de Componentes UI y Accesibilidad
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Contratos de los 25 componentes, tokens semánticos, contraste WCAG y diseño responsive.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button size="sm" variant="outline" onClick={toggleTheme}>
            Tema: {themeMode.toUpperCase()}
          </Button>
          <Button size="sm" variant="outline" onClick={toggleDensity}>
            Densidad: {densityMode.toUpperCase()}
          </Button>
          <ContextualHelp
            title="Preferencia de visualización"
            content="Los modos claro/oscuro y cómodo/compacto se almacenan por usuario y no causan destello visual."
          />
        </div>
      </header>

      <nav
        className="flex flex-wrap gap-2 border-b border-slate-800 pb-3"
        aria-label="Secciones del catálogo"
      >
        {(
          [
            "tokens",
            "buttons",
            "forms",
            "tables",
            "modals",
            "feedback",
            "patterns",
            "mobile",
            "motion"
          ] as const
        ).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all focus-visible:ring-2 focus-visible:ring-blue-500 ${
              activeTab === tab
                ? "bg-blue-600 text-white shadow-md shadow-blue-900/30"
                : "bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800"
            }`}
          >
            {tab.toUpperCase()}
          </button>
        ))}
      </nav>

      {activeTab === "tokens" && (
        <section className="space-y-6">
          <h2 className="text-xl font-bold">Tokens Semánticos y Marca</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Paleta Semántica ({themeMode})
              </h3>
              <div className="space-y-2">
                <div
                  className="h-10 rounded-xl flex items-center justify-between px-3 text-xs font-mono font-bold text-white shadow-sm"
                  style={{ backgroundColor: currentTheme.primary }}
                >
                  <span>primary</span>
                  <span>{currentTheme.primary}</span>
                </div>
                <div
                  className="h-10 rounded-xl flex items-center justify-between px-3 text-xs font-mono font-bold text-white shadow-sm"
                  style={{ backgroundColor: currentTheme.success }}
                >
                  <span>success</span>
                  <span>{currentTheme.success}</span>
                </div>
                <div
                  className="h-10 rounded-xl flex items-center justify-between px-3 text-xs font-mono font-bold text-white shadow-sm"
                  style={{ backgroundColor: currentTheme.danger }}
                >
                  <span>danger</span>
                  <span>{currentTheme.danger}</span>
                </div>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="w-full mt-2"
                onClick={() => {
                  applyBrandTokens({ primary: "#047857" });
                  toast.success("Marca actualizada", "Tokens aplicados a toda la UI dinámicamente.");
                }}
              >
                Aplicar Marca Alternativa
              </Button>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Tipografía y Escalas
              </h3>
              <div className="space-y-2 text-xs text-slate-300">
                <p className="font-sans">Sans: {TYPOGRAPHY_TOKENS.fontFamilySans}</p>
                <p className="font-mono">Mono: {TYPOGRAPHY_TOKENS.fontFamilyMono}</p>
                <p>Base: {TYPOGRAPHY_TOKENS.fontSizeBase} · Sm: {TYPOGRAPHY_TOKENS.fontSizeSm}</p>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <TagIcon size={16} />
                Densidad y Espaciado
              </h3>
              <div className="space-y-2 text-xs font-mono text-slate-300">
                <div className="p-2.5 bg-slate-800 rounded-lg">Radius: {RADIUS_TOKENS.lg}</div>
                <div className="p-2.5 bg-slate-800 rounded-xl">Shadow: {SHADOW_TOKENS.md}</div>
                <div className="p-2.5 bg-slate-800 rounded-xl">
                  Row Height: {DENSITY_TOKENS[densityMode].tableRowHeight} · Spacing 4: {SPACING_TOKENS[4]}
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {activeTab === "buttons" && (
        <section className="space-y-6">
          <h2 className="text-xl font-bold">Jerarquía de Acciones y Botones</h2>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
            <div className="space-y-2">
              <h3 className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Jerarquía Operativa de Venta (UI-002)
              </h3>
              <div className="flex flex-wrap gap-3 items-center">
                <Button variant={getActionHierarchyVariant("confirm")}>
                  Confirmar venta (Principal)
                </Button>
                <Button variant={getActionHierarchyVariant("draft")}>
                  Guardar borrador (Secundario)
                </Button>
                <Button variant={getActionHierarchyVariant("cancel")}>
                  Anular venta (Peligro)
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Variantes Estándar y Estados
              </h3>
              <div className="flex flex-wrap gap-3 items-center">
                <Button variant="primary">Principal</Button>
                <Button variant="secondary">Secundario</Button>
                <Button variant="outline">Contorno</Button>
                <Button variant="ghost">Fantasma</Button>
                <Button variant="danger">Peligro</Button>
                <Button variant="primary" disabled>
                  Deshabilitado
                </Button>
                <Button variant="primary" isLoading>
                  Cargando
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Botones con Icono y Etiquetas Accesibles
              </h3>
              <div className="flex flex-wrap gap-3 items-center">
                <IconButton
                  ariaLabel="Buscar registros"
                  icon={<SearchIcon size={18} />}
                  variant="primary"
                />
                <IconButton
                  ariaLabel="Confirmar acción"
                  icon={<CheckCircleIcon size={18} />}
                  variant="secondary"
                />
                <IconButton
                  ariaLabel="Cancelar acción"
                  icon={<CancelXIcon size={18} />}
                  variant="ghost"
                />
                <IconButton
                  ariaLabel="Configuración de parámetros"
                  icon={<SettingsIcon size={18} />}
                  rounded
                  variant="outline"
                />
                <IconButton
                  ariaLabel="Editar registro"
                  icon={<SquarePenIcon size={18} />}
                  variant="outline"
                />
                <IconButton
                  ariaLabel="Eliminar registro"
                  icon={<Trash2Icon size={18} />}
                  variant="danger"
                />
              </div>
            </div>
          </div>
        </section>
      )}

      {activeTab === "forms" && (
        <section className="space-y-6">
          <h2 className="text-xl font-bold">Formularios por Secciones y Entradas Accesibles</h2>
          <FormErrorSummary
            errors={[{ fieldId: "client_name", message: "La razón social es obligatoria." }]}
          />
          <FormSection
            title="Identificación Legal"
            description="Datos del contribuyente o cliente"
            required={true}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="client_name"
                label="Razón Social"
                placeholder="Ej. Distribuidora del Norte S.A.C."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                required={true}
                error={inputText ? undefined : "La razón social es obligatoria."}
              />
              <Input
                id="doc_number"
                label="Número de RUC / DNI"
                placeholder="20123456789"
                helperText="11 dígitos para personas jurídicas"
              />
            </div>
          </FormSection>

          <FormSection
            title="Condiciones Comerciales y Pago"
            description="Parámetros de facturación y crédito"
            required={false}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <MoneyInput
                id="sale_amount"
                label="Importe de venta"
                value={moneyValue}
                onChange={setMoneyValue}
                currency="USD"
              />
              <Select
                id="invoice_type"
                label="Tipo de comprobante"
                value={selectValue}
                onChange={setSelectValue}
                options={[
                  { value: "option1", label: "Factura Electrónica (F001)" },
                  { value: "option2", label: "Boleta Electrónica (B001)" },
                  { value: "option3", label: "Nota de Crédito" }
                ]}
              />
              <DatePicker
                id="sale_date"
                label="Fecha de emisión"
                value={dateValue}
                onChange={setDateValue}
              />
              <div className="flex flex-col gap-3 justify-center pt-2">
                <Switch
                  checked={switchChecked}
                  onChange={setSwitchChecked}
                  label="Emisión electrónica inmediata con Sunat"
                />
                <Checkbox
                  checked={checkboxChecked}
                  onChange={setCheckboxChecked}
                  label="Permite crédito comercial con plazo de 30 días"
                />
              </div>
            </div>
          </FormSection>

          <FormSection title="Documentos Adjuntos" description="Comprobantes y contratos de respaldo">
            <FileUploader
              onFileSelect={(file) => toast.info("Archivo cargado", file.name)}
              acceptedFormats=".pdf,.xlsx,.csv"
            />
          </FormSection>
        </section>
      )}

      {activeTab === "tables" && (
        <section className="space-y-6">
          <h2 className="text-xl font-bold">Lectura de Tablas, Paginación y Expansión</h2>
          <DataTable
            stickyHeader={true}
            columns={productColumns}
            data={SYNTHETIC_PRODUCTS}
          />
          <Pagination
            currentPage={currentPage}
            totalPages={4}
            totalRecords={12}
            onPageChange={setCurrentPage}
          />
        </section>
      )}

      {activeTab === "modals" && (
        <section className="space-y-6">
          <h2 className="text-xl font-bold">Modales, Paneles Laterales y Overlays</h2>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-wrap gap-4">
            <Button onClick={() => setIsModalOpen(true)}>Abrir Modal Accesible</Button>
            <Button variant="secondary" onClick={() => setIsDrawerOpen(true)}>
              Abrir Drawer Lateral
            </Button>
            <Button variant="danger" onClick={() => setIsConfirmOpen(true)}>
              Abrir ConfirmDialog
            </Button>

            <Modal
              id="catalog-demo-modal"
              isOpen={isModalOpen}
              onClose={() => setIsModalOpen(false)}
              title="Confirmación de Operación Comercial"
              footer={
                <div className="flex gap-2">
                  <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
                    Cancelar
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => {
                      setIsModalOpen(false);
                      toast.success("Operación confirmada exitosamente");
                    }}
                  >
                    Aceptar
                  </Button>
                </div>
              }
            >
              <p className="text-sm text-slate-300">
                Este modal gestiona el foco de inicio, trampa Tab/Shift-Tab, cierre por tecla Escape
                y restauración del foco al elemento que lo activó.
              </p>
            </Modal>

            <Drawer
              id="catalog-demo-drawer"
              isOpen={isDrawerOpen}
              onClose={() => setIsDrawerOpen(false)}
              title="Ficha Técnica del Producto"
            >
              <div className="space-y-4 text-sm text-slate-200">
                <p>Detalle ampliado de inventario y reservas.</p>
                <div className="p-3 bg-slate-950 rounded-xl font-mono text-xs">
                  SKU: LAPTOP-001
                </div>
              </div>
            </Drawer>

            <ConfirmDialog
              id="catalog-demo-confirm"
              isOpen={isConfirmOpen}
              title="Confirmar Anulación"
              message="¿Está seguro de anular la transacción? Los movimientos de almacén se revertirán."
              confirmLabel="Anular"
              isDestructive={true}
              onConfirm={() => {
                setIsConfirmOpen(false);
                toast.warning("Operación anulada");
              }}
              onCancel={() => setIsConfirmOpen(false)}
            />
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
              Navegación por Pestañas y Acordeones
            </h3>
            <Tabs
              activeTab="tab1"
              onTabChange={() => {}}
              tabs={[
                { id: "tab1", label: "Información General" },
                { id: "tab2", label: "Movimientos Contables" },
                { id: "tab3", label: "Auditoría de Cambios" }
              ]}
            />
            <Accordion
              items={[
                {
                  id: "item1",
                  title: "¿Cómo se calculan los impuestos en ventas mixtas?",
                  content: "Los productos exonerados tienen tasa 0.00 y los gravados aplican 18%."
                },
                {
                  id: "item2",
                  title: "¿Qué ocurre con el stock reservado tras una anulación?",
                  content: "El stock se reintegra de forma atómica e inmediata al inventario disponible."
                }
              ]}
            />
          </div>
        </section>
      )}

      {activeTab === "feedback" && (
        <section className="space-y-6">
          <h2 className="text-xl font-bold">Feedback, Alertas y Errores Recuperables</h2>
          <div className="space-y-4">
            <AlertBanner
              type="success"
              title="Comprobante F001-00492 emitido con éxito"
              message="Se registró el asiento contable y se actualizó el stock. Puede registrar el cobro ahora."
            />
            <RecoverableErrorBanner
              errorType="payment_timeout"
              title="Tiempo de espera en pasarela de pagos"
              message="No se recibió respuesta inmediata del procesador bancario. Consulte el estado de la transacción antes de intentar un nuevo cobro."
              onQueryStatus={() => toast.info("Consultando estado...", "ID transacción: TX-84920")}
              onRetry={() => toast.warning("Reintentando cobro...")}
            />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <KpiCard
                title="Ventas Totales"
                value="$14,890.00"
                delta="+8.4% incremento"
                isPositiveDelta={true}
              />
              <KpiCard
                title="Devoluciones"
                value="$240.00"
                delta="-1.2% reducción"
                isPositiveDelta={false}
              />
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
                <span className="text-xs font-semibold uppercase text-slate-400">Progreso y Skeletons</span>
                <ProgressBar progress={85} label="Sincronización Sunat" />
                <Skeleton className="h-2 w-full mt-2" />
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-wrap items-center gap-4">
              <Avatar name="Admin SalesIA" size="md" />
              <Tooltip text="Información de acceso rápido">
                <Button size="sm" variant="ghost">Tooltip Hover/Focus</Button>
              </Tooltip>
              <Popover
                trigger={<Button size="sm" variant="outline">Filtros Popover</Button>}
                content={<p className="text-xs text-slate-300">Contenido emergente accesible</p>}
              />
              <DropdownMenu
                trigger={<Button size="sm" variant="secondary">Más Opciones</Button>}
                items={[{ label: "Descargar informe", onClick: () => {} }]}
              />
            </div>
          </div>
        </section>
      )}

      {activeTab === "patterns" && (
        <section className="space-y-6">
          <h2 className="text-xl font-bold">Patrones Empresariales: Estados Vacíos e Impresión</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <EmptyState
              type="no_records"
              title="Sin comprobantes registrados"
              description="Aún no se han registrado comprobantes para este periodo fiscal."
              canCreate={true}
              createLabel="Registrar comprobante"
              onCreate={() => toast.info("Acción de crear")}
            />
            <EmptyState
              type="no_permission"
              title="Acceso restringido a reportes"
              description="Su perfil de usuario no cuenta con privilegios para emitir reportes contables."
              canCreate={false}
            />
          </div>
          <PrintableDocumentLayout
            documentNumber="F001-000492"
            date="2026-10-10"
            customerName="Corporación Tecnológica del Sur S.A.C."
            total="1,416.00 USD"
          >
            <p className="text-sm text-slate-700">
              Detalle de items impresos según plantilla corporativa A4/Carta sin menús ni controles
              interactivos en papel.
            </p>
          </PrintableDocumentLayout>
        </section>
      )}

      {activeTab === "mobile" && (
        <section className="space-y-6">
          <h2 className="text-xl font-bold">Simulación Responsive en Dispositivo Móvil (375 px)</h2>
          <p className="text-slate-400 text-sm">
            Validación de reflujo visual sin recorte de botones ni desbordamiento horizontal.
          </p>
          <div className="mx-auto w-[375px] border-4 border-slate-700 rounded-3xl p-4 bg-slate-900 space-y-4 shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center border-b border-slate-800 pb-2">
              <span className="text-xs font-bold text-white">Venta Móvil (375 px)</span>
              <Badge variant="success">✓ Activo</Badge>
            </div>
            <Input label="Buscar cliente o SKU" placeholder="Buscar..." />
            <div className="flex gap-2">
              <Button size="sm" variant="primary" className="flex-1">
                Confirmar
              </Button>
              <Button size="sm" variant="outline" className="flex-1">
                Borrador
              </Button>
            </div>
            <DataTable
              columns={[
                { key: "sku", header: "SKU", align: "left" },
                { key: "unitPrice", header: "Total", align: "right" }
              ]}
              data={SYNTHETIC_PRODUCTS}
            />
          </div>
        </section>
      )}

      {activeTab === "motion" && (
        <section className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-xl font-bold text-white">Matriz de Iconos Animados y Contrato de Movimiento (FAL-033)</h2>
              <p className="text-xs text-slate-400">
                55 fichas ICO verificadas: normal, hover, foco, pressed, disabled, loading y movimiento reducido.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-300 font-medium">Modo Movimiento:</span>
              <Button
                size="sm"
                variant={motionCtx.isReducedMotion ? "outline" : "primary"}
                onClick={() => {
                  motionCtx.setMotionMode("normal");
                  toast.info("Movimiento normal activado", "Gestos semánticos completos activos.");
                }}
              >
                Normal
              </Button>
              <Button
                size="sm"
                variant={motionCtx.isReducedMotion ? "primary" : "outline"}
                onClick={() => {
                  motionCtx.setMotionMode("reduced");
                  toast.info("Movimiento reducido activado", "Animaciones canceladas inmediatamente sin desajustes.");
                }}
              >
                Reducido
              </Button>
            </div>
          </div>
          <IconMatrixCatalog limit={55} />
        </section>
      )}
    </div>
  );
};
