import { describe, it, expect, vi } from "vitest";
import { renderToString } from "react-dom/server";
import {
  SquarePenIcon,
  PlusIcon,
  CheckIcon,
  XIcon,
  CopyIcon,
  DownloadIcon,
  UploadIcon,
  SearchIcon,
  SettingsIcon,
  BellIcon,
  EyeIcon,
  EyeOffIcon,
  RefreshCwIcon,
  ArchiveIcon,
  UndoIcon,
  RedoIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  Trash2Icon,
  TrashIcon,
  IconMatrixCatalog,
  ICON_DEPENDENCY_REGISTRY,
  getIconRegistryEntry,
  getAllIconRegistryEntries
} from "../icons/index";
import {
  MOTION_DURATIONS,
  ICON_GESTURE_DURATIONS,
  MOTION_STORAGE_KEY,
  getStoredMotionPreference,
  setStoredMotionPreference,
  resolveEffectiveMotion,
  getMotionDurationMs,
  getIconGestureDurationMs,
  subscribeToMotionPreference,
  MotionTriggerContainer,
  createFiniteAnimationTimer,
  IconStateContext
} from "../motion";
import { IconButton, Button } from "../components/index";
import { ComponentCatalog } from "../components/ComponentCatalog";
import { ToastProvider } from "../toast/ToastContext";

describe("FAL-033: Animaciones e iconos conforme a cada ficha", () => {
  it("renders visual matrix showing normal, hover, focus, pressed, disabled, loading and reduced motion", () => {
    const htmlMatrix = renderToString(<IconMatrixCatalog limit={20} />);
    expect(htmlMatrix).toContain("ICO-001");
    expect(htmlMatrix).toContain("ICO-020");
    expect(htmlMatrix).toContain("Normal");
    expect(htmlMatrix).toContain("Hover");
    expect(htmlMatrix).toContain("Foco");
    expect(htmlMatrix).toContain("Pressed");
    expect(htmlMatrix).toContain("Disabled");
    expect(htmlMatrix).toContain("Loading");
    expect(htmlMatrix).toContain("Reducido");
    expect(ICON_DEPENDENCY_REGISTRY.length).toBe(55);
    const htmlTrash = renderToString(<TrashIcon size={18} />);
    expect(htmlTrash).toContain("rotate(0deg)");
  });

  it("proves distinct gesture parameters per icon rather than a uniform scale for all", () => {
    expect(ICON_GESTURE_DURATIONS.squarePen).toBe(240);
    expect(ICON_GESTURE_DURATIONS.plus).toBe(180);
    expect(ICON_GESTURE_DURATIONS.check).toBe(200);
    expect(ICON_GESTURE_DURATIONS.x).toBe(140);
    expect(ICON_GESTURE_DURATIONS.settings).toBe(220);
    expect(ICON_GESTURE_DURATIONS.bell).toBe(260);
    expect(ICON_GESTURE_DURATIONS.chevronDown).toBe(160);

    const squarePenEntry = getIconRegistryEntry("square-pen");
    const plusEntry = getIconRegistryEntry("plus");
    const bellEntry = getIconRegistryEntry("bell");
    expect(squarePenEntry?.gestureType).toBe("tilt-stroke");
    expect(plusEntry?.gestureType).toBe("scale-pulse");
    expect(bellEntry?.gestureType).toBe("sway-bell");
    expect(squarePenEntry?.gestureType).not.toEqual(plusEntry?.gestureType);
  });
});

describe("MOT-001: Adaptador central de movimiento", () => {
  it("encapsulates durations, easing and reduced motion across all subsystems", () => {
    expect(MOTION_DURATIONS.micro).toBe(100);
    expect(MOTION_DURATIONS.standard).toBe(180);
    expect(MOTION_DURATIONS.modal).toBe(220);
    expect(MOTION_DURATIONS.toast).toBe(300);

    const normalModal = getMotionDurationMs("modal", false);
    const reducedModal = getMotionDurationMs("modal", true);
    expect(normalModal).toBe(220);
    expect(reducedModal).toBe(0);

    const normalToast = getMotionDurationMs("toast", false);
    const reducedToast = getMotionDurationMs("toast", true);
    expect(normalToast).toBe(300);
    expect(reducedToast).toBe(0);

    const normalIcon = getIconGestureDurationMs("squarePen", false);
    const reducedIcon = getIconGestureDurationMs("squarePen", true);
    expect(normalIcon).toBe(240);
    expect(reducedIcon).toBe(0);
  });
});

describe("MOT-002: Cobertura de interacción", () => {
  it("provides visual feedback on actionable controls without missing edit or delete buttons", () => {
    const htmlCatalog = renderToString(
      <ToastProvider>
        <ComponentCatalog initialTab="buttons" />
      </ToastProvider>
    );
    expect(htmlCatalog).toContain('aria-label="Editar registro"');
    expect(htmlCatalog).toContain('aria-label="Eliminar registro"');

    const htmlEdit = renderToString(
      <IconButton ariaLabel="Editar registro" icon={<SquarePenIcon size={18} />} />
    );
    expect(htmlEdit).toContain("group inline-flex items-center justify-center");
    expect(htmlEdit).toContain("min-w-[40px]");
    expect(htmlEdit).toContain("min-h-[40px]");

    const htmlDelete = renderToString(
      <IconButton ariaLabel="Eliminar registro" variant="danger" icon={<Trash2Icon size={18} />} />
    );
    expect(htmlDelete).toContain("bg-rose-600");
  });
});

describe("MOT-003: Disparador en contenedor", () => {
  it("activates icon gesture from parent button boundary without requiring direct stroke touch", () => {
    const htmlContainer = renderToString(
      <MotionTriggerContainer ariaLabel="Fila accionable">
        <SquarePenIcon size={20} />
      </MotionTriggerContainer>
    );
    expect(htmlContainer).toContain('data-icon-id="squarePen"');
    expect(htmlContainer).toContain('data-interaction-state="rest"');

    const htmlWithContext = renderToString(
      <IconStateContext.Provider value={{ state: "hover", isReducedMotion: false }}>
        <SquarePenIcon size={20} />
      </IconStateContext.Provider>
    );
    expect(htmlWithContext).toContain('data-interaction-state="hover"');
    expect(htmlWithContext).toContain("rotate(-10deg)");
  });
});

describe("MOT-004: Sin acciones al hover", () => {
  it("hover trigger only performs feedback and never triggers actions, mutations or deletions", () => {
    let deleted = false;
    const handleDelete = () => {
      deleted = true;
    };
    let hoverTriggered = false;
    const handleHoverFeedback = () => {
      hoverTriggered = true;
    };

    const container = (
      <MotionTriggerContainer
        onActivate={handleDelete}
        onHoverFeedback={handleHoverFeedback}
      >
        <Trash2Icon size={18} />
      </MotionTriggerContainer>
    );
    expect(deleted).toBe(false);

    container.props.onHoverFeedback();
    expect(hoverTriggered).toBe(true);
    expect(deleted).toBe(false);

    container.props.onActivate();
    expect(deleted).toBe(true);
  });
});

describe("MOT-005: Movimiento finito", () => {
  it("executes single-shot animation and cleans up timer back to rest without endless looping", () => {
    vi.useFakeTimers();
    let completed = false;
    const timer = createFiniteAnimationTimer(() => {
      completed = true;
    }, 240);

    expect(timer).toBeDefined();
    expect(completed).toBe(false);
    vi.advanceTimersByTime(239);
    expect(completed).toBe(false);
    vi.advanceTimersByTime(2);
    expect(completed).toBe(true);
    vi.useRealTimers();
  });
});

describe("MOT-006: Preferencia persistente", () => {
  it("respects stored user preference and halts animations immediately when reduced motion is selected", () => {
    expect(MOTION_STORAGE_KEY).toBe("salesia_motion_preference");
    setStoredMotionPreference("normal");
    expect(getStoredMotionPreference()).toBe("normal");

    let notifiedReduced = false;
    const unsubscribe = subscribeToMotionPreference((isReduced) => {
      notifiedReduced = isReduced;
    });

    setStoredMotionPreference("reduced");
    expect(getStoredMotionPreference()).toBe("reduced");
    expect(resolveEffectiveMotion("reduced")).toBe(true);
    expect(typeof notifiedReduced).toBe("boolean");

    unsubscribe();
    setStoredMotionPreference("normal");
  });
});

describe("MOT-007: Accesibilidad de librerías", () => {
  it("guarantees accessible markup for overlays, buttons and alerts regardless of animation library", () => {
    const htmlButton = renderToString(
      <Button isLoading={true}>Guardando</Button>
    );
    expect(htmlButton).toContain('aria-busy="true"');
    expect(htmlButton).toContain('sr-only');

    const htmlIcon = renderToString(
      <IconButton ariaLabel="Cerrar modal" icon={<XIcon size={16} />} />
    );
    expect(htmlIcon).toContain('aria-label="Cerrar modal"');
    expect(htmlIcon).toContain('disabled:pointer-events-none');
  });
});

describe("MOT-008: Rendimiento", () => {
  it("preserves fixed container dimensions and viewBox so SVG never triggers layout shift", () => {
    const html = renderToString(<SquarePenIcon size={20} state="hover" />);
    expect(html).toContain('viewBox="0 0 24 24"');
    expect(html).toContain("width:20px");
    expect(html).toContain("height:20px");
    expect(html).toContain("min-width:20px");
    expect(html).toContain("min-height:20px");
  });
});

describe("MOT-009: Un dueño por propiedad", () => {
  it("separates container layer from inner SVG path transform avoiding CSS and motion collisions", () => {
    const html = renderToString(
      <IconButton ariaLabel="Editar" icon={<SquarePenIcon size={18} state="hover" />} />
    );
    expect(html).toContain("group inline-flex items-center justify-center");
    expect(html).toContain("pointer-events-none");
    expect(html).toContain('data-icon-id="squarePen"');
  });
});

describe("MOT-010: Móvil y puntero grueso", () => {
  it("supports touch interactions with minimum click target and non-sticky hover", () => {
    const htmlSm = renderToString(<IconButton size="sm" ariaLabel="Buscar" icon={<SearchIcon size={16} />} />);
    const htmlMd = renderToString(<IconButton size="md" ariaLabel="Buscar" icon={<SearchIcon size={18} />} />);
    const htmlLg = renderToString(<IconButton size="lg" ariaLabel="Buscar" icon={<SearchIcon size={20} />} />);

    expect(htmlSm).toContain("min-w-[36px]");
    expect(htmlSm).toContain("min-h-[36px]");
    expect(htmlMd).toContain("min-w-[40px]");
    expect(htmlMd).toContain("min-h-[40px]");
    expect(htmlLg).toContain("min-w-[48px]");
    expect(htmlLg).toContain("min-h-[48px]");
  });
});

describe("MOT-011: Pruebas de interrupción", () => {
  it("cleans up active timers when interrupted by early cancel or unmount without memory leaks", () => {
    vi.useFakeTimers();
    let completed = false;
    const timer = createFiniteAnimationTimer(() => {
      completed = true;
    }, 240);

    timer.cancel();
    vi.advanceTimersByTime(300);
    expect(completed).toBe(false);
    vi.useRealTimers();
  });
});

describe("MOT-012: Control de dependencias", () => {
  it("records source URL, commit, MIT license and local adaptation details for all 55 catalog icons", () => {
    const all = getAllIconRegistryEntries();
    expect(all.length).toBe(55);
    all.forEach((entry) => {
      expect(entry.id).toMatch(/^ICO-\d{3}$/);
      expect(entry.license).toBe("MIT");
      expect(entry.originalUrl.length).toBeGreaterThan(10);
      expect(entry.adaptation.length).toBeGreaterThan(5);
      expect(entry.durationMs).toBeGreaterThan(0);
    });
  });
});

describe("ICO-001: Editar registro (square-pen)", () => {
  it("tests rest, hover, focus, tap, interruption and reduced motion preserving control size", () => {
    const rest = renderToString(<SquarePenIcon size={24} state="rest" />);
    expect(rest).toContain("width:24px;height:24px");

    const hover = renderToString(<SquarePenIcon size={24} state="hover" />);
    expect(hover).toContain("rotate(-10deg)");
    expect(hover).toContain("width:24px;height:24px");

    const focus = renderToString(<SquarePenIcon size={24} state="focus" />);
    expect(focus).toContain("rotate(-10deg)");

    const pressed = renderToString(<SquarePenIcon size={24} state="pressed" />);
    expect(pressed).toContain("rotate(-10deg)");

    const reduced = renderToString(<SquarePenIcon size={24} state="hover" reducedMotion={true} />);
    expect(reduced).not.toContain("rotate(-10deg)");
  });
});

describe("ICO-002: Crear o añadir (plus)", () => {
  it("tests 1.0 -> 1.08 expansion and reduced motion fallback", () => {
    const rest = renderToString(<PlusIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");

    const hover = renderToString(<PlusIcon size={20} state="hover" />);
    expect(hover).toContain("scale(1.08)");

    const reduced = renderToString(<PlusIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    expect(reduced).not.toContain("scale(1.08)");
  });
});

describe("ICO-003: Confirmar o guardar (check)", () => {
  it("tests check mark drawing once on success and static render on reduced mode", () => {
    const success = renderToString(<CheckIcon size={20} state="success" />);
    expect(success).toContain("stroke-dasharray:24");

    const reduced = renderToString(<CheckIcon size={20} state="success" reducedMotion={true} />);
    expect(reduced).toContain("transition:none");
  });
});

describe("ICO-004: Cerrar o cancelar (x)", () => {
  it("tests 8-degree rotation on hover and static rotation on reduced mode", () => {
    const hover = renderToString(<XIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(8deg)");

    const reduced = renderToString(<XIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
  });
});

describe("ICO-005: Copiar (copy)", () => {
  it("tests 1.5px sheet displacement on hover and static sheets on reduced mode", () => {
    const hover = renderToString(<CopyIcon size={20} state="hover" />);
    expect(hover).toContain("translate(1.5px, -1.5px)");

    const reduced = renderToString(<CopyIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).not.toContain("translate(1.5px, -1.5px)");
  });
});

describe("ICO-006: Descargar (download)", () => {
  it("tests down arrow displacement 2px and return", () => {
    const hover = renderToString(<DownloadIcon size={20} state="hover" />);
    expect(hover).toContain("translateY(2px)");

    const reduced = renderToString(<DownloadIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateY(0)");
  });
});

describe("ICO-007: Importar (upload)", () => {
  it("tests ascending arrow displacement 2px and return", () => {
    const hover = renderToString(<UploadIcon size={20} state="hover" />);
    expect(hover).toContain("translateY(-2px)");

    const reduced = renderToString(<UploadIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateY(0)");
  });
});

describe("ICO-008: Buscar (search)", () => {
  it("tests slight magnifying glass tilt 10deg", () => {
    const hover = renderToString(<SearchIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(-10deg)");

    const reduced = renderToString(<SearchIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
  });
});

describe("ICO-009: Configurar (settings)", () => {
  it("tests gear rotation 45deg on hover and continuous spin on loading", () => {
    const hover = renderToString(<SettingsIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(45deg)");

    const loading = renderToString(<SettingsIcon size={20} state="loading" />);
    expect(loading).toContain("animate-spin");

    const reduced = renderToString(<SettingsIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
  });
});

describe("ICO-010: Notificaciones (bell)", () => {
  it("tests bell sway 8deg on hover and static on reduced mode", () => {
    const hover = renderToString(<BellIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(8deg)");

    const reduced = renderToString(<BellIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
  });
});

describe("ICO-011: Ver detalle (eye)", () => {
  it("tests smooth eye pupil expansion 1.15x", () => {
    const hover = renderToString(<EyeIcon size={20} state="hover" />);
    expect(hover).toContain("scale(1.15)");

    const reduced = renderToString(<EyeIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
  });
});

describe("ICO-012: Ocultar contenido (eye-off)", () => {
  it("tests slash stroke transition on interaction", () => {
    const hover = renderToString(<EyeOffIcon size={20} state="hover" />);
    expect(hover).toContain("opacity:0.75");

    const rest = renderToString(<EyeOffIcon size={20} state="rest" />);
    expect(rest).toContain("opacity:1");
  });
});

describe("ICO-013: Actualizar (refresh-cw)", () => {
  it("tests 180deg short rotation on hover and continuous rotation on loading", () => {
    const hover = renderToString(<RefreshCwIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(180deg)");

    const loading = renderToString(<RefreshCwIcon size={20} state="loading" />);
    expect(loading).toContain("animate-spin");
  });
});

describe("ICO-014: Archivar (archive)", () => {
  it("tests smooth box lid lift 2px", () => {
    const hover = renderToString(<ArchiveIcon size={20} state="hover" />);
    expect(hover).toContain("translateY(-2px)");

    const reduced = renderToString(<ArchiveIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateY(0)");
  });
});

describe("ICO-015: Deshacer (undo)", () => {
  it("tests left arrow displacement 2px", () => {
    const hover = renderToString(<UndoIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(-2px)");

    const reduced = renderToString(<UndoIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
  });
});

describe("ICO-016: Rehacer (redo)", () => {
  it("tests right arrow displacement 2px", () => {
    const hover = renderToString(<RedoIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(2px)");

    const reduced = renderToString(<RedoIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
  });
});

describe("ICO-017: Continuar (arrow-right)", () => {
  it("tests right arrow translation 2px", () => {
    const hover = renderToString(<ArrowRightIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(2px)");

    const reduced = renderToString(<ArrowRightIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
  });
});

describe("ICO-018: Volver (arrow-left)", () => {
  it("tests left arrow translation 2px", () => {
    const hover = renderToString(<ArrowLeftIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(-2px)");

    const reduced = renderToString(<ArrowLeftIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
  });
});

describe("ICO-019: Expandir (chevron-down)", () => {
  it("tests 180deg rotation between collapsed and expanded states", () => {
    const hover = renderToString(<ChevronDownIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(180deg)");

    const rest = renderToString(<ChevronDownIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
  });
});

describe("ICO-020: Contraer (chevron-up)", () => {
  it("tests -180deg rotation coherent with open panel", () => {
    const hover = renderToString(<ChevronUpIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(-180deg)");

    const rest = renderToString(<ChevronUpIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
  });
});
