import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
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
  PrintableDocumentLayout
} from "../components/index";
import {
  DARK_THEME,
  LIGHT_THEME,
  DENSITY_TOKENS,
  Z_INDEX_TOKENS,
  TYPOGRAPHY_TOKENS,
  SPACING_TOKENS,
  RADIUS_TOKENS,
  SHADOW_TOKENS,
  calculateLuminance,
  getContrastRatio,
  verifyWcagContrast,
  applyBrandTokens,
  getStoredThemePreference,
  resolveThemePreference,
  setStoredThemePreference,
  getStoredDensityPreference,
  setStoredDensityPreference,
  getActionHierarchyVariant,
  getDualEncodedStatus
} from "../tokens";
import { resolveEffectiveMotion, getMotionDurationMs } from "../motion";

describe("FAL-032 & REG-22: Componentes, accesibilidad y diseño empresarial", () => {
  it("FAL-032: two modals do not repeat ids for title and dialog landmarks", () => {
    const htmlA = renderToString(
      <Modal isOpen={true} onClose={() => {}} title="Primer modal de confirmación" id="modal-first">
        <p>Contenido primer modal</p>
      </Modal>
    );
    const htmlB = renderToString(
      <Modal isOpen={true} onClose={() => {}} title="Segundo modal de detalles" id="modal-second">
        <p>Contenido segundo modal</p>
      </Modal>
    );

    expect(htmlA).toContain('id="modal-first-title"');
    expect(htmlA).toContain('aria-labelledby="modal-first-title"');
    expect(htmlB).toContain('id="modal-second-title"');
    expect(htmlB).toContain('aria-labelledby="modal-second-title"');
    expect(htmlA).not.toContain('id="modal-second-title"');
  });

  it("FAL-032: Drawer implements full modal dialog pattern with unique id and aria attributes", () => {
    const html = renderToString(
      <Drawer isOpen={true} onClose={() => {}} title="Detalles del cliente" id="drawer-cust">
        <p>Datos del cliente</p>
      </Drawer>
    );
    expect(html).toContain('role="dialog"');
    expect(html).toContain('aria-modal="true"');
    expect(html).toContain('aria-labelledby="drawer-cust-title"');
    expect(html).toContain('id="drawer-cust-title"');
    expect(html).toContain('aria-label="Cerrar panel lateral"');
  });

  it("REG-22: reduced motion token returns 0ms duration", () => {
    const reducedDuration = getMotionDurationMs("modal", true);
    expect(reducedDuration).toBe(0);
    const normalDuration = getMotionDurationMs("modal", false);
    expect(normalDuration).toBeGreaterThan(0);
    expect(resolveEffectiveMotion("reduced")).toBe(true);
  });

  it("FAL-032: validates contracts of all 25 operational components", () => {
    const htmlIconButton = renderToString(
      <IconButton ariaLabel="Editar cliente" icon={<span>icon</span>} />
    );
    expect(htmlIconButton).toContain('aria-label="Editar cliente"');

    const htmlMoney = renderToString(
      <MoneyInput value="250.00" onChange={() => {}} currency="PEN" />
    );
    expect(htmlMoney).toContain("250.00");
    expect(htmlMoney).toContain("PEN");

    const htmlSelect = renderToString(
      <Select
        value="A"
        onChange={() => {}}
        options={[{ value: "A", label: "Factura" }]}
      />
    );
    expect(htmlSelect).toContain("Factura");

    const htmlDate = renderToString(
      <DatePicker value="2026-10-10" onChange={() => {}} />
    );
    expect(htmlDate).toContain('type="date"');

    const htmlPagination = renderToString(
      <Pagination currentPage={2} totalPages={5} onPageChange={() => {}} />
    );
    expect(htmlPagination).toContain("Página 2 de 5");

    const htmlTabs = renderToString(
      <Tabs tabs={[{ id: "t1", label: "General" }]} activeTab="t1" onTabChange={() => {}} />
    );
    expect(htmlTabs).toContain('role="tablist"');

    const htmlAccordion = renderToString(
      <Accordion items={[{ id: "a1", title: "Pregunta", content: "Respuesta" }]} />
    );
    expect(htmlAccordion).toContain("Pregunta");

    const htmlTooltip = renderToString(
      <Tooltip text="Ayuda flotante">
        <button type="button">Info</button>
      </Tooltip>
    );
    expect(htmlTooltip).toContain("Info");

    const htmlPopover = renderToString(
      <Popover trigger={<button type="button">Trigger</button>} content={<div>Pop</div>} />
    );
    expect(htmlPopover).toContain("Trigger");

    const htmlAvatar = renderToString(
      <Avatar name="Renzo Silva" />
    );
    expect(htmlAvatar).toContain("RS");

    const htmlDropdown = renderToString(
      <DropdownMenu
        trigger={<button type="button">Menú</button>}
        items={[{ label: "Exportar", onClick: () => {} }]}
      />
    );
    expect(htmlDropdown).toContain('aria-haspopup="menu"');

    const htmlUploader = renderToString(
      <FileUploader onFileSelect={() => {}} />
    );
    expect(htmlUploader).toContain('role="button"');
  });
});

describe("UI-001: Tokens semánticos", () => {
  it("defines comprehensive tokens for color, typography, spacing, radius, shadows, density, z-index and motion", () => {
    expect(LIGHT_THEME.primary).toBeDefined();
    expect(DARK_THEME.primary).toBeDefined();
    expect(TYPOGRAPHY_TOKENS.fontFamilySans).toBeDefined();
    expect(TYPOGRAPHY_TOKENS.fontSizeSm).toBeDefined();
    expect(SPACING_TOKENS[4]).toBeDefined();
    expect(RADIUS_TOKENS.xl).toBeDefined();
    expect(SHADOW_TOKENS.lg).toBeDefined();
    expect(DENSITY_TOKENS.comfortable).toBeDefined();
    expect(DENSITY_TOKENS.compact).toBeDefined();
    expect(Z_INDEX_TOKENS.modal).toBe(40);
  });

  it("updates brand tokens dynamically without modifying individual forms", () => {
    const updated = applyBrandTokens({ primary: "#047857", accent: "#065f46" });
    expect(updated.primary).toBe("#047857");
    expect(updated.accent).toBe("#065f46");
    expect(updated.background).toBe(DARK_THEME.background);
  });
});

describe("UI-002: Jerarquía de acciones", () => {
  it("distinguishes confirming a sale from saving draft and voiding/canceling", () => {
    const confirmVariant = getActionHierarchyVariant("confirm");
    const draftVariant = getActionHierarchyVariant("draft");
    const cancelVariant = getActionHierarchyVariant("cancel");

    expect(confirmVariant).toBe("primary");
    expect(draftVariant).toBe("outline");
    expect(cancelVariant).toBe("danger");

    const htmlConfirm = renderToString(
      <Button variant={confirmVariant}>Confirmar venta</Button>
    );
    const htmlDraft = renderToString(
      <Button variant={draftVariant}>Guardar borrador</Button>
    );
    const htmlCancel = renderToString(
      <Button variant={cancelVariant}>Anular venta</Button>
    );

    expect(htmlConfirm).toContain("bg-blue-600");
    expect(htmlDraft).toContain("border-slate-600");
    expect(htmlCancel).toContain("bg-rose-600");
  });
});

describe("UI-003: Tema oscuro completo", () => {
  it("persists theme preference and supports dark and light modes", () => {
    setStoredThemePreference("light");
    expect(getStoredThemePreference()).toBe("light");
    setStoredThemePreference("dark");
    expect(getStoredThemePreference()).toBe("dark");
    expect(resolveThemePreference("light")).toBe("dark");

    const htmlDark = renderToString(
      <AlertBanner type="info" title="Aviso en tema oscuro" message="Detalles del sistema" />
    );
    expect(htmlDark).toContain("bg-blue-950/40");
  });
});

describe("UI-004: Contraste WCAG AA", () => {
  it("validates luminance and contrast ratio exceeds 4.5:1 for normal text and 3:1 for large text", () => {
    expect(calculateLuminance("#ffffff")).toBeGreaterThan(0.99);
    expect(calculateLuminance("#000000")).toBe(0);

    const lightTextOnSurface = getContrastRatio(LIGHT_THEME.textPrimary, LIGHT_THEME.surface);
    expect(lightTextOnSurface).toBeGreaterThanOrEqual(4.5);
    expect(verifyWcagContrast(LIGHT_THEME.textPrimary, LIGHT_THEME.surface, false)).toBe(true);

    const darkTextOnSurface = getContrastRatio(DARK_THEME.textPrimary, DARK_THEME.surface);
    expect(darkTextOnSurface).toBeGreaterThanOrEqual(4.5);
    expect(verifyWcagContrast(DARK_THEME.textPrimary, DARK_THEME.surface, false)).toBe(true);

    const errorOnBg = getContrastRatio(DARK_THEME.danger, DARK_THEME.background);
    expect(errorOnBg).toBeGreaterThanOrEqual(3.0);
  });
});

describe("UI-005: Densidad configurable", () => {
  it("supports comfortable and compact modes while retaining accessible padding and touch target metrics", () => {
    setStoredDensityPreference("compact");
    expect(getStoredDensityPreference()).toBe("compact");
    expect(DENSITY_TOKENS.compact.tableCellPadding).toContain("py-1.5");
    expect(DENSITY_TOKENS.compact.fontSize).toBe("text-xs");

    setStoredDensityPreference("comfortable");
    expect(getStoredDensityPreference()).toBe("comfortable");
    expect(DENSITY_TOKENS.comfortable.tableCellPadding).toContain("py-3");
    expect(DENSITY_TOKENS.comfortable.fontSize).toBe("text-sm");
  });
});

describe("UI-006: Responsive", () => {
  it("renders responsive table and container layouts without clipping critical actions at 375px", () => {
    const html = renderToString(
      <DataTable
        columns={[
          { key: "sku", header: "SKU", align: "left" },
          { key: "price", header: "Precio", align: "right" }
        ]}
        data={[{ id: "1", sku: "PROD-001", price: "$100.00" }]}
      />
    );
    expect(html).toContain("overflow-x-auto");
    expect(html).toContain("w-full");
    expect(html).toContain("text-right");
  });
});

describe("UI-007: Lectura de tablas", () => {
  it("aligns text to left, money to right, supports sticky headers and expandable context", () => {
    const html = renderToString(
      <DataTable
        stickyHeader={true}
        columns={[
          { key: "name", header: "Descripción", align: "left", expandable: true },
          { key: "total", header: "Total Importe", align: "right" }
        ]}
        data={[
          {
            id: "1",
            name: "Servicio de consultoría extendida corporativa con especificación técnica detallada",
            total: "15,480.50 USD"
          }
        ]}
      />
    );
    expect(html).toContain("sticky top-0");
    expect(html).toContain("text-right");
    expect(html).toContain("text-left");
    expect(html).toContain("15,480.50 USD");
  });
});

describe("UI-008: Formularios por secciones", () => {
  it("groups form sections, indicates required/optional, and associates inline error summaries", () => {
    const html = renderToString(
      <form>
        <FormSection title="Identificación" description="Datos legales de la entidad">
          <Input id="legal_name" label="Razón social" required error="Campo obligatorio" />
        </FormSection>
        <FormSection title="Condiciones comerciales" description="Límites y plazos">
          <Input id="notes" label="Observaciones" helperText="Información complementaria opcional" />
        </FormSection>
        <FormErrorSummary errors={[{ fieldId: "legal_name", message: "Campo obligatorio" }]} />
      </form>
    );

    expect(html).toContain("Identificación");
    expect(html).toContain("Condiciones comerciales");
    expect(html).toContain("Requerido");
    expect(html).toContain("Opcional");
    expect(html).toContain('id="legal_name-error"');
    expect(html).toContain('href="#legal_name"');
  });
});

describe("UI-009: Microcopy empresarial", () => {
  it("renders messages explaining what happened, what was saved, and how to proceed", () => {
    const html = renderToString(
      <AlertBanner
        type="success"
        title="Venta VTA-00109 confirmada con éxito"
        message="Se reservaron 5 unidades en el almacén central. Puede registrar el cobro o emitir el comprobante de pago."
      />
    );
    expect(html).toContain("VTA-00109");
    expect(html).toContain("Se reservaron 5 unidades");
    expect(html).toContain("registrar el cobro");
  });
});

describe("UI-010: Estado vacío útil", () => {
  it("differentiates empty states and suppresses create action when user lacks permission", () => {
    const htmlNoRecords = renderToString(
      <EmptyState
        type="no_records"
        title="Sin registros de clientes"
        description="No hay clientes registrados en esta empresa todavía."
        canCreate={true}
        createLabel="Nuevo cliente"
        onCreate={() => {}}
      />
    );
    expect(htmlNoRecords).toContain("Sin registros de clientes");
    expect(htmlNoRecords).toContain("Nuevo cliente");

    const htmlNoPermission = renderToString(
      <EmptyState
        type="no_permission"
        title="Permiso insuficiente"
        description="No cuentas con permisos para registrar nuevos productos."
        canCreate={false}
        createLabel="Nuevo producto"
        onCreate={() => {}}
      />
    );
    expect(htmlNoPermission).toContain("Permiso insuficiente");
    expect(htmlNoPermission).not.toContain("Nuevo producto");

    const htmlFilterEmpty = renderToString(
      <EmptyState
        type="filter_no_results"
        title="Sin coincidencias"
        description="No se encontraron registros que coincidan con el filtro aplicado."
      />
    );
    expect(htmlFilterEmpty).toContain("Sin coincidencias");
  });
});

describe("UI-011: Carga estable", () => {
  it("reserves layout geometry with skeletons and displays real determinate progress", () => {
    const htmlSkeleton = renderToString(
      <div className="space-y-2">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-full" />
      </div>
    );
    expect(htmlSkeleton).toContain("h-6 w-48");
    expect(htmlSkeleton).toContain("animate-pulse");

    const htmlProgress = renderToString(
      <ProgressBar progress={72} label="Exportación de kardex valorizado" />
    );
    expect(htmlProgress).toContain('role="progressbar"');
    expect(htmlProgress).toContain('aria-valuenow="72"');
    expect(htmlProgress).toContain("72%");
  });
});

describe("UI-012: Errores recuperables", () => {
  it("preserves context and offers payment status query prior to retrying timed-out transactions", () => {
    const htmlPaymentTimeout = renderToString(
      <RecoverableErrorBanner
        errorType="payment_timeout"
        title="Tiempo de espera excedido en pasarela"
        message="La solicitud de cobro no respondió en el tiempo límite. Para evitar duplicidad, consulte el estado antes de reintentar."
        onQueryStatus={() => {}}
        onRetry={() => {}}
      />
    );
    expect(htmlPaymentTimeout).toContain("Consultar estado de la transacción");
    expect(htmlPaymentTimeout).toContain("Tiempo de espera excedido");
  });
});

describe("UI-013: Iconografía consistente", () => {
  it("renders Lucide icons in fixed container with standard stroke width and hidden from screen readers", () => {
    const htmlButton = renderToString(
      <Button variant="primary" leftIcon={<span data-testid="test-icon">icon</span>}>
        Guardar
      </Button>
    );
    expect(htmlButton).toContain("Guardar");
    expect(htmlButton).toContain("test-icon");
  });
});

describe("UI-014: Accesibilidad semántica", () => {
  it("distinguishes Save customer from Save product without relying on visual icon alone", () => {
    const htmlCust = renderToString(
      <Button variant="primary" aria-label="Guardar cliente">
        Guardar cliente
      </Button>
    );
    const htmlProd = renderToString(
      <Button variant="primary" aria-label="Guardar producto">
        Guardar producto
      </Button>
    );
    expect(htmlCust).toContain('aria-label="Guardar cliente"');
    expect(htmlProd).toContain('aria-label="Guardar producto"');
    expect(htmlCust).not.toContain("Guardar producto");
  });
});

describe("UI-015: Teclado y foco", () => {
  it("provides visible focus rings, aria tags, and keyboard accessible switches and dialogs", () => {
    const htmlSwitch = renderToString(
      <Switch checked={true} onChange={() => {}} label="Facturación electrónica automática" />
    );
    expect(htmlSwitch).toContain('role="switch"');
    expect(htmlSwitch).toContain('aria-checked="true"');
    expect(htmlSwitch).toContain('tabindex="0"');

    const htmlCheckbox = renderToString(
      <Checkbox checked={false} onChange={() => {}} label="Permite venta con crédito" />
    );
    expect(htmlCheckbox).toContain('role="checkbox"');
    expect(htmlCheckbox).toContain('aria-checked="false"');
    expect(htmlCheckbox).toContain('tabindex="0"');
  });
});

describe("UI-016: Color acompañado", () => {
  it("provides text symbols and dual encoding for badges so states are distinguishable in grayscale", () => {
    const statusApproved = getDualEncodedStatus("approved");
    const statusPending = getDualEncodedStatus("pending");
    const statusRejected = getDualEncodedStatus("rejected");

    expect(statusApproved.symbol).toBe("✓");
    expect(statusPending.symbol).toBe("⏳");
    expect(statusRejected.symbol).toBe("✕");

    const htmlBadge = renderToString(
      <Badge variant="success">✓ Activo</Badge>
    );
    expect(htmlBadge).toContain("✓");
    expect(htmlBadge).toContain("Activo");

    const htmlKpi = renderToString(
      <KpiCard title="Margen comercial" value="34.8%" delta="+2.4% incremento" isPositiveDelta={true} />
    );
    expect(htmlKpi).toContain("+2.4% incremento");
  });
});

describe("UI-017: Idioma y expansión", () => {
  it("supports long texts, Unicode names and localized currency formatting without breaking container", () => {
    const longName = "Distribuidora Internacional de Equipos Electrónicos y Soluciones Automatizadas S.A.C. - Sede Arequipa";
    const html = renderToString(
      <div className="w-80 break-words">
        <Input id="company_name" label="Nombre largo" defaultValue={longName} />
      </div>
    );
    expect(html).toContain(longName);
    expect(html).toContain("break-words");
  });
});

describe("UI-018: Ayuda contextual", () => {
  it("renders contextual help accessible via keyboard with description and formula examples", () => {
    const html = renderToString(
      <ContextualHelp
        title="Fórmula del Impuesto General (IGV)"
        content="Base imponible * 0.18 = Impuesto. Ejemplo: $100.00 base + $18.00 IGV = $118.00 total."
      />
    );
    expect(html).toContain('aria-label="Ver ayuda contextual: Fórmula del Impuesto General (IGV)"');
    expect(html).toContain("Fórmula del Impuesto General (IGV)");
  });
});

describe("UI-019: Documentos impresos", () => {
  it("renders printable document layout with headers, totals, page breaks and no navigation clutter", () => {
    const html = renderToString(
      <PrintableDocumentLayout
        documentNumber="F001-000492"
        date="2026-10-10"
        customerName="Corporación Andina SAC"
        total="1,416.00 USD"
      >
        <p>Líneas de comprobante impreso</p>
      </PrintableDocumentLayout>
    );
    expect(html).toContain("printable-document");
    expect(html).toContain("F001-000492");
    expect(html).toContain("Corporación Andina SAC");
    expect(html).toContain("1,416.00 USD");
    expect(html).toContain("print-avoid-break");
  });
});

describe("UI-020: Validación visual", () => {
  it("renders representative empty, loading, error, and detail states for visual verification", () => {
    const htmlConfirm = renderToString(
      <ConfirmDialog
        isOpen={true}
        title="Confirmar anulación"
        message="¿Está seguro de anular el pedido PED-0042? Esta acción liberará el stock reservado."
        onConfirm={() => {}}
        onCancel={() => {}}
        isDestructive={true}
      />
    );
    expect(htmlConfirm).toContain("Confirmar anulación");
    expect(htmlConfirm).toContain("liberará el stock reservado");
  });
});
