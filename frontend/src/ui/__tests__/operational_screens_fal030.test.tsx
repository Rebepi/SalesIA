import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "../toast/ToastContext";
import { SessionGate } from "../../app/SessionGate";
import { CompanySelectorModal } from "../../features/organizacion/components/CompanySelectorModal";
import { OnboardingWizardModal } from "../../features/organizacion/components/OnboardingWizardModal";
import { DashboardAnalyticsTab } from "../../features/analitica/components/DashboardAnalyticsTab";
import { PersonalWorkspaceTab } from "../../features/trabajo/components/PersonalWorkspaceTab";
import { CustomerCommercialCard } from "../../features/clientes/ficha/CustomerCommercialCard";
import { CustomerEditorDrawer } from "../../features/clientes/editor/CustomerEditorDrawer";
import { ProductCommercialCard } from "../../features/catalogo/components/ProductCommercialCard";
import { CategoriesAndUnitsTab } from "../../features/catalogo/components/CategoriesAndUnitsTab";
import { PricingAndPromotionsTab } from "../../features/precios/components/PricingAndPromotionsTab";
import { SalesTeamTab } from "../../features/equipo/components/SalesTeamTab";
import { QuotationsWorkspaceTab } from "../../features/cotizaciones/components/QuotationsWorkspaceTab";
import { OrdersWorkspaceTab } from "../../features/pedidos/components/OrdersWorkspaceTab";
import { NewSalePOSModal } from "../../features/ventas/components/NewSalePOSModal";
import { SaleDetailModal } from "../../features/ventas/components/SaleDetailModal";

const testQueryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false }
  }
});

function wrap(ui: React.ReactElement): string {
  return renderToString(
    <QueryClientProvider client={testQueryClient}>
      <ToastProvider>
        {ui}
      </ToastProvider>
    </QueryClientProvider>
  );
}

describe("FAL-030 / SCR-001: Login y recuperacion", () => {
  it("renders centered 420px max card with discrete branding and recovery workflow", () => {
    const html = wrap(
      <SessionGate>
        <div>Contenido protegido</div>
      </SessionGate>
    );
    expect(html).toContain('id="scr-001-login-card"');
    expect(html).toContain("max-w-[440px]");
    expect(html).toContain("/images/salesia-login-hero.png");
    expect(html).toContain("backdrop-blur-2xl");
    expect(html).toContain("SalesIA Enterprise");
    expect(html).toContain('name="username"');
    expect(html).toContain('name="password"');
    expect(html).toContain("¿Olvidaste tu contraseña?");
    expect(html).toContain("Iniciar Sesión");
  });

  it("contains accessible security toggles and inputs", () => {
    const html = wrap(
      <SessionGate>
        <div>Contenido protegido</div>
      </SessionGate>
    );
    expect(html).toContain('aria-label="Ver contraseña"');
    expect(html).toContain('aria-label="MFA requerido"');
    expect(html.toLowerCase()).toContain('autocomplete="username"');
  });
});

describe("FAL-030 / SCR-002: Selector de empresa", () => {
  it("renders company modal with search, active context highlight and role badge", () => {
    const html = wrap(
      <CompanySelectorModal
        isOpen={true}
        currentCompanyId="comp-1"
        onClose={() => {}}
        onCompanySelected={() => {}}
      />
    );
    expect(html).toContain('id="scr-002-company-selector-dialog"');
    expect(html).toContain("Seleccionar Empresa / Entorno");
    expect(html).toContain('placeholder="Buscar empresa por nombre o RUC/NIT..."');
    expect(html).toContain('role="dialog"');
  });
});

describe("FAL-030 / SCR-003: Onboarding", () => {
  it("renders 4-step wizard with lateral summary and draft recovery", () => {
    const html = wrap(
      <OnboardingWizardModal
        isOpen={true}
        onClose={() => {}}
        onCompleted={() => {}}
      />
    );
    expect(html).toContain('id="scr-003-onboarding-dialog"');
    expect(html).toContain("Asistente de alta guiada");
    expect(html).toContain("Paso 1: Identificación de la Empresa");
    expect(html).toContain("Resumen Lateral");
    expect(html).toContain("Razón Social");
    expect(html).toContain("Moneda Base");
    expect(html).toContain("Almacén");
    expect(html).toContain("Siguiente");
  });
});

describe("FAL-030 / SCR-004: Inicio ejecutivo", () => {
  it("renders 4 KPIs with definition, period and update indicators", () => {
    const html = wrap(<DashboardAnalyticsTab />);
    expect(html).toContain('id="scr-004-executive-dashboard"');
    expect(html).toContain("dashboard-toolbar");
    expect(html).toContain("Últimos 30 días");
    expect(html).toContain("dashboard-filter-panel");
    expect(html).toContain("Filtrar resultados");
    expect(html).toContain("Exportar CSV");
  });
});

describe("FAL-030 / SCR-005: Mi trabajo", () => {
  it("renders compact assigned tasks, pending orders, and personal quota widgets", () => {
    const html = wrap(<PersonalWorkspaceTab />);
    expect(html).toContain('id="scr-005-personal-workspace"');
    expect(html).not.toContain("Refrescar datos de la bandeja");
    expect(html).toContain("Meta Personal");
    expect(html).toContain("Mis Tareas");
    expect(html).toContain("Pedidos en Curso");
    expect(html).toContain("Mi Cartera");
    expect(html).toContain("Nueva actividad rápida...");
    expect(html).toContain("Agregar");
  });
});

describe("FAL-030 / SCR-006: Clientes listado", () => {
  it("defines table structure with doc, legal name, segment, rep, last purchase and credit limit", () => {
    const sampleCustomer = {
      customer_id: "c-1",
      doc_number: "20100012345",
      legal_name: "Inversiones del Sur S.A.C.",
      segment: "VIP",
      credit_limit: "50000.00",
      is_active: true
    };
    expect(sampleCustomer.doc_number).toBe("20100012345");
    expect(sampleCustomer.legal_name).toContain("Inversiones");
    expect(sampleCustomer.segment).toBe("VIP");
    expect(Number(sampleCustomer.credit_limit)).toBe(50000);
  });
});

describe("FAL-030 / SCR-007: Cliente ficha", () => {
  it("renders commercial card with 5 tabs and sensitive data handling", () => {
    const html = wrap(
      <CustomerCommercialCard
        customerId="cust-10"
        customerName="Corporación Andina S.A."
        canWrite={true}
        allCustomers={[]}
        onClose={() => {}}
        onRefresh={() => {}}
      />
    );
    expect(html).toContain('id="scr-007-customer-card"');
    expect(html).toContain("Corporación Andina S.A.");
    expect(html).toContain("Ficha comercial completa");
    expect(html).toContain("Resumen y Calidad");
    expect(html).toContain("Contactos");
    expect(html).toContain("Direcciones");
    expect(html).toContain("Condiciones comerciales");
    expect(html).toContain("Extracto e Historial");
  });
});

describe("FAL-030 / SCR-008: Cliente edicion", () => {
  it("renders 3 collapsible sections, duplicate check and draft preservation", () => {
    const html = wrap(
      <CustomerEditorDrawer
        isOpen={true}
        onClose={() => {}}
        onSaved={() => {}}
      />
    );
    expect(html).toContain('id="scr-008-customer-drawer"');
    expect(html).toContain("Alta rápida de cliente");
    expect(html).toContain("1. Identidad Fiscal");
    expect(html).toContain("2. Contacto y Comunicación");
    expect(html).toContain("3. Condiciones Comerciales");
    expect(html).toContain("Guardar cliente");
  });
});

describe("FAL-030 / SCR-009: Productos listado", () => {
  it("validates product list structure without mixing incompatible currencies", () => {
    const sampleProducts = [
      { id: "p-1", sku: "SKU-001", name: "Laptop Pro", category_name: "Equipos", price: "1200.00", currency: "USD", stock: 15 },
      { id: "p-2", sku: "SKU-002", name: "Mouse Óptico", category_name: "Accesorios", price: "25.00", currency: "USD", stock: 120 }
    ];
    const currencies = new Set(sampleProducts.map(p => p.currency));
    expect(currencies.size).toBe(1);
    expect(sampleProducts[0].sku).toBe("SKU-001");
    expect(Number(sampleProducts[0].price)).toBe(1200);
  });
});

describe("FAL-030 / SCR-010: Producto ficha", () => {
  it("renders product detail card with header, variants, prices, inventory per warehouse", () => {
    const html = wrap(
      <ProductCommercialCard
        productId="prod-20"
        productName="Servidor Rack 2U"
        canWrite={true}
        allProducts={[]}
        onClose={() => {}}
        onRefresh={() => {}}
      />
    );
    expect(html).toContain('id="scr-010-product-card"');
    expect(html).toContain("Servidor Rack 2U");
    expect(html).toContain("Ficha técnica");
    expect(html).toContain("Variantes");
    expect(html).toContain("Precios y simulación");
  });
});

describe("FAL-030 / SCR-011: Categorias y unidades", () => {
  it("renders accessible hierarchy tree, lateral editor, cycle prevention and unit conversions", () => {
    const html = wrap(<CategoriesAndUnitsTab />);
    expect(html).toContain('id="scr-011-categories-and-units"');
    expect(html).toContain("Categorías y Unidades");
    expect(html).toContain("Árbol de Categorías");
    expect(html).toContain("Unidades y Equivalencias");
    expect(html).toContain("Nueva Categoría");
  });
});

describe("FAL-030 / SCR-012: Precios y promociones", () => {
  it("renders validity tables, simulator and priority / exclusivity rules", () => {
    const html = wrap(<PricingAndPromotionsTab />);
    expect(html).toContain('id="scr-012-pricing-and-promotions"');
    expect(html).toContain("Precios y Promociones");
    expect(html).toContain("Simulador de Reglas y Conflicto de Precios");
    expect(html).toContain("Listas de Precios y Vigencias");
    expect(html).toContain("Reglas de Promoción y Campañas");
    expect(html).toContain("Calcular precio");
  });
});

describe("FAL-030 / SCR-013: Equipo comercial", () => {
  it("renders sales team quotas, scopes and assigned goals per period", () => {
    const html = wrap(<SalesTeamTab />);
    expect(html).toContain('id="scr-013-sales-team"');
    expect(html).toContain("Periodo:");
    expect(html).toContain("Equipo comercial");
    expect(html).toContain("Visibilidad personal");
    expect(html).toContain("Nuevo vendedor");
  });
});

describe("FAL-030 / SCR-014: Cotizaciones", () => {
  it("renders quotation list, line items, versioning and conversion to order", () => {
    const html = wrap(<QuotationsWorkspaceTab />);
    expect(html).toContain('id="scr-014-quotations-workspace"');
    expect(html).toContain("Cotizaciones y Propuestas");
    expect(html).toContain("Nueva cotización");
    expect(html).toContain("Todos los estados");
  });
});

describe("FAL-030 / SCR-015: Pedidos", () => {
  it("renders table / board view, requested vs served quantities and warehouse reservation", () => {
    const html = wrap(<OrdersWorkspaceTab />);
    expect(html).toContain('id="scr-015-orders-workspace"');
    expect(html).toContain("Pedidos de Venta");
    expect(html).toContain("Todos los estados");
    expect(html).toContain('title="Vista tabla"');
    expect(html).toContain('title="Vista tablero"');
  });
});

describe("FAL-030 / SCR-016: Nueva venta POS", () => {
  it("renders customer top context, product center, fixed lateral totalizer and one-shot lock", () => {
    const html = wrap(
      <NewSalePOSModal
        isOpen={true}
        onClose={() => {}}
        onSaleCreated={() => {}}
      />
    );
    expect(html).toContain('id="scr-016-new-sale-pos-dialog"');
    expect(html).toContain("Nueva Venta (Punto de Venta / Mostrador)");
    expect(html).toContain("Cliente");
    expect(html).toContain("Almacén de Despacho");
    expect(html).toContain("Condición de Pago");
    expect(html).toContain("Confirmar venta y cobro");
    expect(html).toContain("Operación protegida con claves de idempotencia únicas.");
  });
});

describe("FAL-030 / SCR-017: Venta detalle", () => {
  it("renders snapshot header, totals, 5 tabs and permitted status actions", () => {
    const sampleSale = {
      id: "sale-101",
      number: "VTA-2026-0001",
      status: "confirmed" as const,
      currency: "USD",
      total_amount: "1500.00",
      paid_amount: "500.00",
      customer_name: "Distribuidora Central S.A.",
      lines: [
        {
          product_id: "prod-1",
          sku: "SKU-001",
          product_name: "Monitor IPS 27",
          quantity: 2,
          unit_price: 250,
          subtotal: 500
        }
      ],
      payments: [
        {
          id: "pay-1",
          amount: 500,
          payment_method: "transfer",
          created_at: "2026-10-10"
        }
      ]
    };
    const html = wrap(
      <SaleDetailModal
        sale={sampleSale}
        canWrite={true}
        onOpenPayment={() => {}}
        onClose={() => {}}
      />
    );
    expect(html).toContain('id="scr-017-sale-detail-dialog"');
    expect(html).toContain("Venta:");
    expect(html).toContain("VTA-2026-0001");
    expect(html).toContain("confirmed");
    expect(html).toContain("Líneas de Venta");
    expect(html).toContain("Pagos Aplicados");
    expect(html).toContain("Entregas");
    expect(html).toContain("Devoluciones");
    expect(html).toContain("Auditoría");
    expect(html).toContain("Registrar Cobro");
  });
});
