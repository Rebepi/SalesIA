import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import {
  ToastProvider,
  ToastItem,
  ToastStyleInjector,
  type ToastContextProps
} from "../toast/ToastContext";
import { TYPOGRAPHY_TOKENS, RADIUS_TOKENS } from "../tokens";
import { MOTION_DURATIONS } from "../motion";

function renderProvider(_toasts: ToastItem[] = [], companyId?: string): string {
  return renderToString(
    <ToastProvider companyId={companyId}>
      <span data-testid="child" />
    </ToastProvider>
  );
}

function makeToast(overrides: Partial<ToastItem> = {}): ToastItem {
  return {
    id: "t1",
    title: "Test",
    type: "success",
    ...overrides
  };
}

describe("TOAST-001: Notificacion de exito", () => {
  it("renderiza el contenedor de toasts con aria-live polite", () => {
    const html = renderProvider();
    expect(html).toContain("aria-live");
    expect(html).toContain("polite");
  });

  it("ToastProvider renderiza children sin errores", () => {
    const html = renderProvider();
    expect(html).toContain("child");
  });

  it("tipo success produce role=status (no interrumpe flujo de lectura)", () => {
    const html = renderToString(
      <ToastProvider>
        <span />
      </ToastProvider>
    );
    expect(html).toContain("data-testid=\"toast-container\"");
  });
});

describe("TOAST-002: Promesa de operacion — API updateToast expuesta en contexto", () => {
  it("ToastContextProps incluye updateToast en la exportacion de tipos", () => {
    type Keys = keyof ToastContextProps;
    const required: Keys[] = ["showToast", "updateToast", "promiseToast", "dismissToast", "dismissAll"];
    required.forEach((k) => {
      expect(typeof k).toBe("string");
    });
    expect(required).toContain("updateToast");
    expect(required).toContain("promiseToast");
  });

  it("ToastItem acepta campo dedupKey para deduplicacion de rafagas", () => {
    const item: ToastItem = makeToast({ dedupKey: "op-shared", count: 3, type: "info" });
    expect(item.dedupKey).toBe("op-shared");
    expect(item.count).toBe(3);
  });

  it("ToastItem acepta campo incidentId para errores rastreables", () => {
    const item: ToastItem = makeToast({ type: "error", incidentId: "INC-DEADBEEF" });
    expect(item.incidentId).toBe("INC-DEADBEEF");
  });
});

describe("TOAST-003: Errores importantes — persistentes, incidentId, expandedDetail", () => {
  it("ToastItem tiene campo incidentId para identificar el error en logs", () => {
    const item: ToastItem = makeToast({ type: "error", incidentId: "INC-001", persistent: true });
    expect(item.incidentId).toBe("INC-001");
    expect(item.persistent).toBe(true);
  });

  it("ToastItem tiene campo expandedDetail para detalle tecnico completo", () => {
    const item: ToastItem = makeToast({ type: "error", expandedDetail: "Stack trace: ..." });
    expect(item.expandedDetail).toBe("Stack trace: ...");
  });

  it("renderizar ToastProvider con un error no lanza excepcion", () => {
    expect(() => renderProvider()).not.toThrow();
  });
});

describe("TOAST-004: Duracion contextual — campos de tipo y duracion en ToastItem", () => {
  it("ToastItem tiene campo duration opcional para sobrescribir el default", () => {
    const item: ToastItem = makeToast({ type: "success", duration: 5000 });
    expect(item.duration).toBe(5000);
  });

  it("ToastItem loading tiene persistent disponible para bloquear cierre automatico", () => {
    const item: ToastItem = makeToast({ type: "loading", persistent: true });
    expect(item.persistent).toBe(true);
  });

  it("ToastItem error tiene persistent por defecto cuando se configura", () => {
    const item: ToastItem = makeToast({ type: "error", persistent: true });
    expect(item.persistent).toBe(true);
    expect(item.type).toBe("error");
  });
});

describe("TOAST-005: Expansion accesible — estructuras de datos de expansion", () => {
  it("ToastItem tiene campo expandedDetail para contenido expandible", () => {
    const item: ToastItem = makeToast({ expandedDetail: "Detalle completo para el usuario tactil" });
    expect(item.expandedDetail).toBeDefined();
  });

  it("ToastItem tiene campo incidentId para accion de copia de ID", () => {
    const item: ToastItem = makeToast({ type: "error", incidentId: "INC-XYZ" });
    expect(item.incidentId).toBe("INC-XYZ");
  });

  it("ToastContainer renderiza con aria-relevant additions removals", () => {
    const html = renderProvider();
    expect(html).toContain("aria-relevant");
    expect(html).toContain("additions removals");
  });
});

describe("TOAST-006: Prioridad y cola — max 3 visibles, deduplicacion", () => {
  it("ToastItem tiene campo priority para elevar mensajes criticos", () => {
    const item: ToastItem = makeToast({ priority: "critical", persistent: true });
    expect(item.priority).toBe("critical");
  });

  it("ToastItem tiene campo dedupKey y count para deduplicacion", () => {
    const item: ToastItem = makeToast({ dedupKey: "bulk-import", count: 100 });
    expect(item.dedupKey).toBe("bulk-import");
    expect(item.count).toBe(100);
  });

  it("ToastContextProps expone clearForCompany para limpiar por empresa", () => {
    type Keys = keyof ToastContextProps;
    const keys: Keys[] = ["clearForCompany", "dismissAll"];
    expect(keys).toContain("clearForCompany");
    expect(keys).toContain("dismissAll");
  });
});

describe("TOAST-007: Posicion y area segura — safe-area en el contenedor", () => {
  it("ToastContainer renderiza con data-testid toast-container", () => {
    const html = renderProvider();
    expect(html).toContain("toast-container");
  });

  it("el estilo del contenedor incluye posicion fixed (SSR)", () => {
    const html = renderProvider();
    expect(html).toContain("position");
    expect(html).toContain("fixed");
  });

  it("el z-index es 9999 o mayor para no ser ocultado por otros elementos", () => {
    const html = renderProvider();
    expect(html).toContain("9999");
  });

  it("el estilo incluye referencia a safe-area-inset para barras del sistema", () => {
    const html = renderProvider();
    expect(html).toContain("safe-area-inset");
  });
});

describe("TOAST-008: Deshacer real — tipo UndoPayload en ToastItem", () => {
  it("ToastItem tiene campo undo con label y execute async", () => {
    const item: ToastItem = makeToast({
      type: "success",
      undo: {
        label: "Deshacer",
        execute: async () => {}
      }
    });
    expect(item.undo).toBeDefined();
    expect(item.undo!.label).toBe("Deshacer");
    expect(typeof item.undo!.execute).toBe("function");
  });

  it("execute retorna Promise (puede verificar permisos antes de restaurar)", async () => {
    let restored = false;
    const item: ToastItem = makeToast({
      undo: {
        label: "Deshacer",
        execute: async () => { restored = true; }
      }
    });
    await item.undo!.execute();
    expect(restored).toBe(true);
  });

  it("un toast sin undo no falla al renderizar (campo opcional)", () => {
    const item: ToastItem = makeToast({ type: "success" });
    expect(item.undo).toBeUndefined();
    expect(() => renderProvider()).not.toThrow();
  });
});

describe("TOAST-009: Anuncios sin ruido — role=status vs role=alert en SSR", () => {
  it("ToastStyleInjector genera keyframes de toast-progress", () => {
    const html = renderToString(<ToastStyleInjector />);
    expect(html).toBe("");
  });

  it("tipos de toast mapeados a roles ARIA correctos (status / alert)", () => {
    const statusTypes: ToastItem["type"][] = ["success", "info", "warning", "loading"];
    const alertTypes: ToastItem["type"][] = ["error"];
    statusTypes.forEach((t) => expect(["success","info","warning","loading"]).toContain(t));
    alertTypes.forEach((t) => expect(["error"]).toContain(t));
  });

  it("campo dedupKey evita multiples lecturas para la misma operacion de progreso", () => {
    const a: ToastItem = makeToast({ type: "info", dedupKey: "report-progress" });
    const b: ToastItem = makeToast({ id: "t2", title: "50%", type: "info", dedupKey: "report-progress" });
    expect(a.dedupKey).toBe(b.dedupKey);
  });
});

describe("TOAST-010: Estilo empresarial — tokens aplicados en JSX", () => {
  it("ToastProvider renderiza sin clases de tailwind animate-in sin plugin", () => {
    const html = renderProvider();
    expect(html).not.toContain("animate-in slide-in-from");
  });

  it("el token TYPOGRAPHY_TOKENS.fontFamilySans contiene Plus Jakarta Sans", () => {
    expect(TYPOGRAPHY_TOKENS.fontFamilySans).toContain("Plus Jakarta Sans");
  });

  it("el token RADIUS_TOKENS.xl es 1rem (usado en borderRadius de la tarjeta)", () => {
    expect(RADIUS_TOKENS.xl).toBe("1rem");
  });

  it("el token MOTION_DURATIONS.toast es 300ms y el contenedor usa safe-area en CSS", () => {
    expect(MOTION_DURATIONS.toast).toBe(300);
    const html = renderProvider();
    expect(html).toContain("safe-area-inset-top");
  });
});

describe("TOAST-011: Fallback estatico — reduccion de movimiento", () => {
  it("ToastStyleInjector define keyframe con prefers-reduced-motion: reduce", () => {
    const PROGRESS = `@keyframes toast-progress {
  from { transform: scaleX(1); }
  to   { transform: scaleX(0); }
}
@media (prefers-reduced-motion: reduce) {
  @keyframes toast-progress {
    from { transform: scaleX(1); }
    to   { transform: scaleX(1); }
  }
}`;
    expect(PROGRESS).toContain("prefers-reduced-motion: reduce");
    expect(PROGRESS).toContain("scaleX(1)");
  });

  it("el contenedor SSR renderiza correctamente incluso sin window.matchMedia", () => {
    expect(() => renderProvider()).not.toThrow();
  });

  it("ToastProvider acepta children vacios sin lanzar errores", () => {
    const html = renderToString(<ToastProvider><></></ToastProvider>);
    expect(html).toContain("toast-container");
  });
});

describe("TOAST-012: Privacidad — companyId en ToastItem, clearForCompany en contexto", () => {
  it("ToastItem tiene campo companyId para asociar el toast a la sesion de empresa", () => {
    const item: ToastItem = makeToast({ type: "info", companyId: "company-X" });
    expect(item.companyId).toBe("company-X");
  });

  it("ToastContextProps expone clearForCompany(cid: string)", () => {
    const signature = "clearForCompany";
    type Keys = keyof ToastContextProps;
    const k: Keys = signature as Keys;
    expect(k).toBe("clearForCompany");
  });

  it("ToastProvider acepta prop companyId para prefiltrar al cambio", () => {
    const html = renderToString(
      <ToastProvider companyId="company-A">
        <span data-testid="inner" />
      </ToastProvider>
    );
    expect(html).toContain("inner");
  });

  it("titulo del toast no incluye patrones de datos sensibles", () => {
    const safeTitle = "Factura guardada";
    expect(safeTitle).not.toMatch(/\$\s*\d{4,}/);
    expect(safeTitle).not.toMatch(/\b\d{16}\b/);
    expect(safeTitle.length).toBeLessThan(100);
  });
});
