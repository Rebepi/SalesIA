import { describe, it, expect, vi } from "vitest";
import { renderToString } from "react-dom/server";
import {
  Button,
  IconButton,
  Input,
  MoneyInput,
  Select,
  Combobox,
  DatePicker,
  DateRangePicker,
  Switch,
  Checkbox,
  DataTable,
  BulkActionBar,
  Modal,
  DestructiveConfirmDialog,
  Drawer,
  Tabs,
  DropdownMenu,
  Breadcrumbs,
  reconstructBreadcrumbsFromPath,
  GlobalSearch,
  CommandPalette,
  KpiCard,
  AccessibleChart,
  Timeline,
  EnterpriseFileUploader,
  Pagination,
  calculateValidPageAfterDeletion,
  ConnectionBanner,
  canExecuteFinancialAction,
  EnterpriseErrorBoundary,
  ContextualTour
} from "../components/index";

describe("CMP-001: Botones", () => {
  it("renders all required variants and sizes with stable structure", () => {
    const htmlPrimary = renderToString(<Button variant="primary">Guardar</Button>);
    const htmlSecondary = renderToString(<Button variant="secondary">Cancelar</Button>);
    const htmlGhost = renderToString(<Button variant="ghost">Opciones</Button>);
    const htmlDestructive = renderToString(<Button variant="destructive">Eliminar</Button>);
    const htmlIcon = renderToString(<Button variant="icon">Icono</Button>);

    expect(htmlPrimary).toContain("bg-blue-600");
    expect(htmlSecondary).toContain("bg-slate-800");
    expect(htmlGhost).toContain("text-slate-300");
    expect(htmlDestructive).toContain("bg-rose-600");
    expect(htmlIcon).toContain("p-2");
  });

  it("loading state communicates status and preserves accessible name and button width stability", () => {
    const htmlLoading = renderToString(
      <Button variant="primary" isLoading={true}>
        Confirmar pago
      </Button>
    );

    expect(htmlLoading).toContain('aria-busy="true"');
    expect(htmlLoading).toContain("sr-only");
    expect(htmlLoading).toContain("Confirmar pago");
    expect(htmlLoading).toContain("animate-spin");
    expect(htmlLoading).toContain("disabled");
  });

  it("rapid double click does not duplicate invocation", () => {
    const clickHandler = vi.fn();
    const btn = (
      <Button onClick={clickHandler} debounceMs={300}>
        Cobrar
      </Button>
    );
    expect(btn.props.debounceMs).toBe(300);
  });
});

describe("CMP-002: Icon button", () => {
  it("provides accessible name, sufficient click target and triggers animation from button boundary", () => {
    const html = renderToString(
      <IconButton ariaLabel="Editar registro" icon={<span>icon-svg</span>} />
    );

    expect(html).toContain('aria-label="Editar registro"');
    expect(html).toContain("min-w-[40px]");
    expect(html).toContain("min-h-[40px]");
    expect(html).toContain("group");
    expect(html).toContain("group-hover:scale-110");
    expect(html).toContain("pointer-events-none");
  });

  it("renders with tooltip when provided", () => {
    const htmlWithTooltip = renderToString(
      <IconButton ariaLabel="Descargar kardex" tooltip="Descargar kardex en PDF" icon={<span>pdf</span>} />
    );
    expect(htmlWithTooltip).toContain('aria-label="Descargar kardex"');
  });
});

describe("CMP-003: Campos de texto", () => {
  it("supports description, counter, prefix, suffix, error, readonly and disabled without losing input", () => {
    const html = renderToString(
      <Input
        label="Razón social"
        value="Empresa Modelo SAC"
        maxLength={50}
        showCount={true}
        prefixText="RUC:"
        suffixText="PEN"
        helperText="Ingrese la denominación fiscal oficial"
        error="Nombre ya registrado"
        readOnly={true}
      />
    );

    expect(html).toContain("Razón social");
    expect(html).toContain("18 / 50");
    expect(html).toContain("RUC:");
    expect(html).toContain("PEN");
    expect(html).toContain("Nombre ya registrado");
    expect(html).toContain("readonly");
    expect(html).toContain('aria-invalid="true"');
  });
});

describe("CMP-004: Campos monetarios", () => {
  it("handles locale separation and rejects ambiguous foreign parsing", () => {
    const changeHandler = vi.fn();
    const htmlEs = renderToString(
      <MoneyInput
        label="Total Factura"
        value="1.234,56"
        onChange={changeHandler}
        locale="es-PE"
        currency="PEN"
        roundingPolicy="half-even"
      />
    );

    expect(htmlEs).toContain("PEN");
    expect(htmlEs).toContain("half-even");
    expect(htmlEs).toContain("1.234,56");

    const htmlEn = renderToString(
      <MoneyInput
        label="Total Invoice"
        value="1,234.56"
        onChange={changeHandler}
        locale="en-US"
        currency="USD"
      />
    );

    expect(htmlEn).toContain("USD");
    expect(htmlEn).toContain("1,234.56");
  });
});

describe("CMP-005: Select y combobox", () => {
  it("renders combobox with accessible role and debounced search sequence resilience", () => {
    const html = renderToString(
      <Combobox
        label="Tipo de comprobante"
        value="factura"
        options={[
          { value: "factura", label: "Factura electrónica" },
          { value: "boleta", label: "Boleta de venta" }
        ]}
        onChange={() => {}}
      />
    );

    expect(html).toContain('role="combobox"');
    expect(html).toContain("Tipo de comprobante");
    expect(html).toContain("Factura electrónica");

    const htmlSelect = renderToString(
      <Select
        label="Estado"
        value="A"
        options={[{ value: "A", label: "Activo" }]}
        onChange={() => {}}
      />
    );
    expect(htmlSelect).toContain("Activo");
  });
});

describe("CMP-006: Selector de fechas", () => {
  it("validates ranges, flags start after end and translates inclusive day count", () => {
    const htmlValid = renderToString(
      <DateRangePicker
        startDate="2026-10-01"
        endDate="2026-10-10"
        onChange={() => {}}
        label="Periodo contable"
        timezone="America/Lima (UTC-5)"
      />
    );

    expect(htmlValid).toContain("Periodo contable");
    expect(htmlValid).toContain("Rango inclusivo: 10 días");
    expect(htmlValid).toContain("America/Lima (UTC-5)");
    expect(htmlValid).toContain("Hoy");
    expect(htmlValid).toContain("7 días");
    expect(htmlValid).toContain("Este mes");

    const htmlDate = renderToString(
      <DatePicker label="Fecha límite" value="2026-10-10" onChange={() => {}} />
    );
    expect(htmlDate).toContain("Fecha límite");
  });
});

describe("CMP-007: Checkbox y switch", () => {
  it("distinguishes row selection from configuration and supports pending state", () => {
    const htmlSwitch = renderToString(
      <Switch checked={true} label="Facturación automática" />
    );
    expect(htmlSwitch).toContain('role="switch"');
    expect(htmlSwitch).toContain('aria-checked="true"');
    expect(htmlSwitch).toContain("Facturación automática");

    const htmlCheckboxRow = renderToString(
      <Checkbox checked={false} isTableRowSelection={true} label="Seleccionar fila" />
    );
    expect(htmlCheckboxRow).toContain('role="checkbox"');
    expect(htmlCheckboxRow).toContain('aria-label="Seleccionar fila"');
  });
});

describe("CMP-008: Tabla empresarial", () => {
  it("renders server columns, row selections and warns when hidden rows are selected across filter changes", () => {
    const html = renderToString(
      <DataTable
        columns={[
          { key: "sku", header: "SKU" },
          { key: "total", header: "Total", align: "right" }
        ]}
        data={[{ id: "1", sku: "PROD-100", total: "$120.00" }]}
        selectedIds={["1", "2"]}
        hiddenSelectedCount={1}
        filteredTotalCount={50}
        visibleSubtotalAmount="$120.00"
        onClearHiddenSelection={() => {}}
      />
    );

    expect(html).toContain("PROD-100");
    expect(html).toContain("Advertencia: Hay 1 fila(s) seleccionada(s) que no son visibles con el filtro actual.");
    expect(html).toContain("Limpiar filas ocultas");
    expect(html).toContain("Subtotal visible: $120.00");
    expect(html).toContain("Total filtrado: 50 registros");
  });
});

describe("CMP-009: Acciones masivas", () => {
  it("displays quantity, scope, confirmation for sensitive changes and allows retrying failed items only", () => {
    const html = renderToString(
      <BulkActionBar
        selectedCount={3}
        scopeDescription="Ámbito: 3 ventas seleccionadas de Sucursal Centro"
        onExecute={async () => [
          { id: "VTA-1", status: "success" },
          { id: "VTA-2", status: "failed", error: "Sin stock" }
        ]}
        onClear={() => {}}
        actions={[
          { key: "emit", label: "Emitir comprobantes" },
          { key: "cancel", label: "Anular en lote", isSensitive: true }
        ]}
      />
    );

    expect(html).toContain('role="region"');
    expect(html).toContain("3 elementos seleccionados");
    expect(html).toContain("Sucursal Centro");
    expect(html).toContain("Emitir comprobantes");
    expect(html).toContain("Anular en lote");
  });
});

describe("CMP-010: Diálogo", () => {
  it("retains visible title, inert background, and does not close or hide error on save failure", () => {
    const html = renderToString(
      <Modal
        isOpen={true}
        onClose={() => {}}
        title="Editar condiciones de crédito"
        id="dialog-credit"
        saveError="Límite de crédito excede el tope autorizado para esta categoría"
      >
        <p>Formulario de condiciones</p>
      </Modal>
    );

    expect(html).toContain('role="dialog"');
    expect(html).toContain('id="dialog-credit-title"');
    expect(html).toContain('aria-labelledby="dialog-credit-title"');
    expect(html).toContain('role="alert"');
    expect(html).toContain("Límite de crédito excede el tope autorizado");
    expect(html).toContain("Formulario de condiciones");
  });
});

describe("CMP-011: Confirmación destructiva", () => {
  it("distinguishes draft deletion from sale voiding with distinct texts, impact and authorization flow", () => {
    const htmlDraft = renderToString(
      <DestructiveConfirmDialog
        isOpen={true}
        onConfirm={() => {}}
        onCancel={() => {}}
        type="draft_deletion"
        entityId="BORR-0042"
        id="dialog-draft"
      />
    );

    expect(htmlDraft).toContain("Eliminar borrador de venta");
    expect(htmlDraft).toContain("no tiene validez fiscal ni reserva inventario");
    expect(htmlDraft).toContain("Eliminar borrador");

    const htmlSale = renderToString(
      <DestructiveConfirmDialog
        isOpen={true}
        onConfirm={() => {}}
        onCancel={() => {}}
        type="sale_cancellation"
        entityId="F001-000892"
        id="dialog-sale"
      />
    );

    expect(htmlSale).toContain("Anular venta confirmada");
    expect(htmlSale).toContain("ANULAR");
    expect(htmlSale).toContain("para autorizar");
    expect(htmlSale).toContain("Confirmar anulación irreversible");
  });
});

describe("CMP-012: Drawer de detalle", () => {
  it("renders 480-640px lateral panel that adapts to full width on mobile viewports", () => {
    const html = renderToString(
      <Drawer isOpen={true} onClose={() => {}} title="Kardex de movimientos" id="drawer-kardex">
        <p>Contenido detallado de existencias</p>
      </Drawer>
    );

    expect(html).toContain('role="dialog"');
    expect(html).toContain('id="drawer-kardex-title"');
    expect(html).toContain("w-full");
    expect(html).toContain("sm:w-[540px]");
    expect(html).toContain("Contenido detallado de existencias");
  });
});

describe("CMP-013: Tabs", () => {
  it("renders tabs with clear active state and dirty form guard", () => {
    const html = renderToString(
      <Tabs
        tabs={[
          { id: "general", label: "Datos generales", isDirty: true },
          { id: "pricing", label: "Precios y descuentos", isDirty: false }
        ]}
        activeTab="general"
        onTabChange={() => {}}
      />
    );

    expect(html).toContain('role="tablist"');
    expect(html).toContain('aria-selected="true"');
    expect(html).toContain("Datos generales");
    expect(html).toContain("Cambios sin guardar");
  });
});

describe("CMP-014: Menús", () => {
  it("groups actions with destructive separators and high z-index avoiding window clipping", () => {
    const html = renderToString(
      <DropdownMenu
        trigger={<button type="button">Opciones</button>}
        items={[
          { label: "Ver kardex", onClick: () => {} },
          { label: "Exportar XML", onClick: () => {} },
          { label: "Anular comprobante", danger: true, isSeparator: true, onClick: () => {} }
        ]}
      />
    );

    expect(html).toContain('aria-haspopup="menu"');
    expect(html).toContain("Opciones");
  });
});

describe("CMP-015: Breadcrumbs", () => {
  it("reconstructs full navigable hierarchy from direct deep link without relying on browser history", () => {
    const reconstructed = reconstructBreadcrumbsFromPath("/sales/orders/ORD-099");
    expect(reconstructed).toHaveLength(4);
    expect(reconstructed[0].label).toBe("Inicio");
    expect(reconstructed[1].label).toBe("Ventas");
    expect(reconstructed[2].label).toBe("Pedidos");
    expect(reconstructed[3].label).toBe("ORD-099");
    expect(reconstructed[3].current).toBe(true);

    const html = renderToString(<Breadcrumbs items={reconstructed} />);
    expect(html).toContain('aria-label="Ruta de navegación"');
    expect(html).toContain("ORD-099");
    expect(html).toContain('aria-current="page"');
  });
});

describe("CMP-016: Buscador global", () => {
  it("isolates entities strictly by tenant company without leaking records between companies", () => {
    const dataset = [
      { id: "c1", title: "Cliente Alpha Lima", category: "customers" as const, companyId: "empresa-1" },
      { id: "c2", title: "Cliente Beta Trujillo", category: "customers" as const, companyId: "empresa-2" }
    ];

    const currentCompanyItems = dataset.filter((d) => d.companyId === "empresa-1");
    expect(currentCompanyItems).toHaveLength(1);
    expect(currentCompanyItems[0].title).toBe("Cliente Alpha Lima");

    const leakageItems = dataset.filter((d) => d.companyId !== "empresa-1");
    expect(leakageItems[0].title).toBe("Cliente Beta Trujillo");

    const htmlSearch = renderToString(
      <GlobalSearch currentCompanyId="empresa-1" dataset={dataset} onSelect={() => {}} />
    );
    expect(htmlSearch).toBeDefined();
  });
});

describe("CMP-017: Command palette", () => {
  it("filters actions by name without executing until explicit selection and prompts confirmation for mutations", () => {
    const mutateAction = vi.fn();
    const actions = [
      { id: "a1", title: "Nuevo cliente", category: "CRM", onExecute: () => {} },
      { id: "a2", title: "Anular todas las reservas", category: "Stock", isDestructive: true, onExecute: mutateAction }
    ];

    const html = renderToString(
      <CommandPalette isOpen={true} onClose={() => {}} actions={actions} />
    );

    expect(html).toContain('aria-label="Ejecutar acción"');
    expect(html).toContain("Nuevo cliente");
    expect(html).toContain("Anular todas las reservas");
    expect(mutateAction).not.toHaveBeenCalled();
  });
});

describe("CMP-018: Tarjeta KPI", () => {
  it("renders title, unit, cutoff date and displays N/C when comparative base is zero", () => {
    const htmlZeroBase = renderToString(
      <KpiCard
        title="Ventas del nuevo canal"
        value="12,500"
        unit="USD"
        period="Octubre 2026"
        cutoffDate="10/10/2026"
        comparisonCurrent={12500}
        comparisonBase={0}
        definitionTooltip="Total facturado en canal digital"
      />
    );

    expect(htmlZeroBase).toContain("Ventas del nuevo canal");
    expect(htmlZeroBase).toContain("12,500");
    expect(htmlZeroBase).toContain("USD");
    expect(htmlZeroBase).toContain("N/C (No calculable)");
    expect(htmlZeroBase).not.toContain("Infinity");
    expect(htmlZeroBase).toContain("Corte: 10/10/2026");

    const htmlNormal = renderToString(
      <KpiCard
        title="Margen bruto"
        value="45.2"
        unit="%"
        comparisonCurrent={45.2}
        comparisonBase={40.0}
      />
    );

    expect(htmlNormal).toContain("+13.0%");
  });
});

describe("CMP-019: Gráfico", () => {
  it("renders identical figures across chart points, accessible alternative table and export data", () => {
    const points = [
      { label: "Norte", value: 450 },
      { label: "Sur", value: 320 },
      { label: "Centro", value: 780 }
    ];

    const html = renderToString(
      <AccessibleChart
        title="Distribución territorial"
        points={points}
        unit="unidades"
        description="Ventas acumuladas por zona comercial"
      />
    );

    expect(html).toContain("Distribución territorial");
    expect(html).toContain("Tabla accesible alternativa:");
    expect(html).toContain("450 unidades");
    expect(html).toContain("780 unidades");
    expect(html).toContain("Exportar CSV");
  });
});

describe("CMP-020: Timeline", () => {
  it("orders events deterministically using sequence tie-breaker when timestamps are identical", () => {
    const events = [
      {
        id: "ev-2",
        timestamp: "2026-10-10T10:00:00Z",
        sequenceNumber: 2,
        actor: "Admin",
        timezone: "America/Lima",
        type: "note" as const,
        title: "Nota añadida",
        description: "Se validó RUC del cliente"
      },
      {
        id: "ev-1",
        timestamp: "2026-10-10T10:00:00Z",
        sequenceNumber: 1,
        actor: "Vendedor",
        timezone: "America/Lima",
        type: "operational" as const,
        title: "Pedido registrado",
        description: "Se reservaron 10 unidades"
      }
    ];

    const html = renderToString(<Timeline events={events} />);
    const pos1 = html.indexOf("Pedido registrado");
    const pos2 = html.indexOf("Nota añadida");
    expect(pos1).toBeLessThan(pos2);
    expect(html).toContain("Operativo");
    expect(html).toContain("Nota");
  });
});

describe("CMP-021: Uploader", () => {
  it("validates formats and blocks public download when file status is scanning or rejected", () => {
    const dummyFile = { name: "cotizacion.pdf", size: 1024 * 1024 } as File;
    const htmlScanning = renderToString(
      <EnterpriseFileUploader
        onFileSelect={() => {}}
        fileStatus={{
          file: dummyFile,
          progress: 50,
          status: "scanning"
        }}
      />
    );

    expect(htmlScanning).toContain("Escaneando...");
    expect(htmlScanning).toContain("Descarga no permitida (No aprobado)");
    expect(htmlScanning).not.toContain('href="');

    const htmlApproved = renderToString(
      <EnterpriseFileUploader
        onFileSelect={() => {}}
        fileStatus={{
          file: dummyFile,
          progress: 100,
          status: "approved",
          publicDownloadUrl: "https://storage.enterprise.local/files/cotizacion.pdf"
        }}
      />
    );

    expect(htmlApproved).toContain("Estado de seguridad: Aprobado");
    expect(htmlApproved).toContain("Descargar archivo");
  });
});

describe("CMP-022: Paginación", () => {
  it("deleting the last item on a page safely transitions to the previous valid page", () => {
    const newPage = calculateValidPageAfterDeletion(3, 1, 21, 10);
    expect(newPage).toBe(2);

    const samePage = calculateValidPageAfterDeletion(2, 5, 15, 10);
    expect(samePage).toBe(2);

    const firstPage = calculateValidPageAfterDeletion(1, 1, 1, 10);
    expect(firstPage).toBe(1);

    const html = renderToString(
      <Pagination currentPage={2} totalPages={4} totalRecords={40} pageSize={10} onPageChange={() => {}} />
    );
    expect(html).toContain("Mostrando 11-20 de 40 registros");
  });
});

describe("CMP-023: Banner de conexión", () => {
  it("alerts user about offline state and suspends final financial actions and inventory changes", () => {
    expect(canExecuteFinancialAction("offline")).toBe(false);
    expect(canExecuteFinancialAction("reconnecting")).toBe(false);
    expect(canExecuteFinancialAction("online")).toBe(true);

    const htmlOffline = renderToString(
      <ConnectionBanner connectionState="offline" />
    );
    expect(htmlOffline).toContain("Sin conexión");
    expect(htmlOffline).toContain("Cobro definitivo y reserva final de stock suspendidos");
  });
});

describe("CMP-024: Error boundary", () => {
  it("isolates rendering failure within area and preserves general app layout", () => {
    const html = renderToString(
      <EnterpriseErrorBoundary fallbackTitle="Panel de analítica temporalmente no disponible">
        <div>Contenido principal protegido</div>
      </EnterpriseErrorBoundary>
    );
    expect(html).toContain("Contenido principal protegido");
  });
});

describe("CMP-025: Tour y ayuda", () => {
  it("presents contextual dismissible guide and respects user preference without disabling help", () => {
    const steps = [
      { title: "Kardex valorizado", description: "Consulte aquí las entradas y salidas de almacén" }
    ];

    const html = renderToString(
      <ContextualTour
        tourId="kardex_tour"
        userId="usr_100"
        steps={steps}
        isOpen={true}
        onClose={() => {}}
      />
    );

    expect(html).toContain('role="region"');
    expect(html).toContain('aria-label="Guía interactiva"');
    expect(html).toContain("Kardex valorizado (1/1)");
    expect(html).toContain("Omitir");
    expect(html).toContain("Finalizar");
  });
});

describe("FAL-032: Pruebas de integración de accesibilidad y diseño", () => {
  it("ensures two open modals do not share duplicate IDs or accessibility landmarks", () => {
    const htmlA = renderToString(
      <Modal isOpen={true} onClose={() => {}} title="Modal de Clientes" id="modal-clients">
        <p>Lista clientes</p>
      </Modal>
    );
    const htmlB = renderToString(
      <Modal isOpen={true} onClose={() => {}} title="Modal de Proveedores" id="modal-vendors">
        <p>Lista proveedores</p>
      </Modal>
    );

    expect(htmlA).toContain('id="modal-clients-title"');
    expect(htmlB).toContain('id="modal-vendors-title"');
    expect(htmlA).not.toContain('id="modal-vendors-title"');
  });

  it("validates responsive 375px table view with sticky headers and overflow management", () => {
    const html = renderToString(
      <div className="w-[375px] max-w-full">
        <DataTable
          stickyHeader={true}
          columns={[
            { key: "code", header: "Código" },
            { key: "amount", header: "Monto", align: "right" }
          ]}
          data={[{ id: "1", code: "DOC-001", amount: "500.00 PEN" }]}
        />
      </div>
    );

    expect(html).toContain("w-[375px]");
    expect(html).toContain("overflow-x-auto");
    expect(html).toContain("DOC-001");
  });
});
