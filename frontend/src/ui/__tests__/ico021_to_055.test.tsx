import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import {
  ChevronRightIcon,
  ChevronLeftIcon,
  CircleHelpIcon,
  CircleCheckIcon,
  ClockIcon,
  CalendarDaysIcon,
  UsersGroupIcon,
  UserPlusIcon,
  CartIcon,
  BoxIcon,
  BoxesIcon,
  CreditCardActionIcon,
  WalletIcon,
  ChartLineIcon,
  ChartColumnIncreasingIcon,
  ChartPieIcon,
  FileTextIcon,
  LogoutActionIcon,
  LockIcon,
  ShieldCheckIcon,
  MoonIcon,
  SunIcon,
  MenuIcon,
  ExternalLinkIcon,
  SendActionIcon,
  AttachFileIcon,
  LinkChainIcon,
  GripVerticalIcon,
  ExpandIcon,
  MinimizeIcon,
  TruckIcon,
  BadgePercentIcon,
  Trash2Icon,
  TrashIcon,
  FallbackCatalogIcon,
  ICON_DEPENDENCY_REGISTRY
} from "../icons/index";

function assertSVGDimensions(html: string, size: number) {
  expect(html).toContain(`width:${size}px`);
  expect(html).toContain(`height:${size}px`);
  expect(html).toContain(`min-width:${size}px`);
  expect(html).toContain(`min-height:${size}px`);
}

describe("ICO-021: Siguiente (chevron-right)", () => {
  it("translates 2px right on hover, returns to rest, no animation when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<ChevronRightIcon size={20} state="rest" />);
    expect(rest).toContain("translateX(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<ChevronRightIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(2px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<ChevronRightIcon size={20} state="focus" />);
    expect(focus).toContain("translateX(2px)");

    const pressed = renderToString(<ChevronRightIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateX(2px)");

    const disabled = renderToString(<ChevronRightIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");
    assertSVGDimensions(disabled, 20);

    const reduced = renderToString(<ChevronRightIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-022: Anterior (chevron-left)", () => {
  it("translates 2px left on hover, returns to rest, no animation when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<ChevronLeftIcon size={20} state="rest" />);
    expect(rest).toContain("translateX(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<ChevronLeftIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(-2px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<ChevronLeftIcon size={20} state="focus" />);
    expect(focus).toContain("translateX(-2px)");

    const pressed = renderToString(<ChevronLeftIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateX(-2px)");

    const disabled = renderToString(<ChevronLeftIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<ChevronLeftIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-023: Ayuda (circle-help)", () => {
  it("pulses question mark 1.08x on hover, scale 1 at rest, no pulse when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<CircleHelpIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<CircleHelpIcon size={20} state="hover" />);
    expect(hover).toContain("scale(1.08)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<CircleHelpIcon size={20} state="focus" />);
    expect(focus).toContain("scale(1.08)");

    const pressed = renderToString(<CircleHelpIcon size={20} state="pressed" />);
    expect(pressed).toContain("scale(1.08)");

    const disabled = renderToString(<CircleHelpIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<CircleHelpIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-024: Exito (circle-check)", () => {
  it("draws check via stroke-dasharray on success, transition:none when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<CircleCheckIcon size={20} state="rest" />);
    expect(rest).toContain("stroke-dasharray");
    assertSVGDimensions(rest, 20);

    const success = renderToString(<CircleCheckIcon size={20} state="success" />);
    expect(success).toContain("stroke-dasharray");
    assertSVGDimensions(success, 20);

    const hover = renderToString(<CircleCheckIcon size={20} state="hover" />);
    expect(hover).toContain("stroke-dasharray");

    const disabled = renderToString(<CircleCheckIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<CircleCheckIcon size={20} state="success" reducedMotion={true} />);
    expect(reduced).toContain("transition:none");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-025: Historial o pendiente (clock)", () => {
  it("rotates hand 45deg on hover, stays at 0deg at rest, no rotation when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<ClockIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<ClockIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(45deg)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<ClockIcon size={20} state="focus" />);
    expect(focus).toContain("rotate(45deg)");

    const pressed = renderToString(<ClockIcon size={20} state="pressed" />);
    expect(pressed).toContain("rotate(45deg)");

    const disabled = renderToString(<ClockIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<ClockIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-026: Elegir periodo (calendar-days)", () => {
  it("dims calendar cells opacity:0.7 on hover, opacity:1 at rest, no dim when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<CalendarDaysIcon size={20} state="rest" />);
    expect(rest).toContain("opacity:1");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<CalendarDaysIcon size={20} state="hover" />);
    expect(hover).toContain("opacity:0.7");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<CalendarDaysIcon size={20} state="focus" />);
    expect(focus).toContain("opacity:0.7");

    const pressed = renderToString(<CalendarDaysIcon size={20} state="pressed" />);
    expect(pressed).toContain("opacity:0.7");

    const disabled = renderToString(<CalendarDaysIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<CalendarDaysIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("opacity:1");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-027: Clientes o equipo (users)", () => {
  it("separates second silhouette 1px right on hover, stays at 0 at rest, no shift when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<UsersGroupIcon size={20} state="rest" />);
    expect(rest).toContain("translateX(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<UsersGroupIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(1px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<UsersGroupIcon size={20} state="focus" />);
    expect(focus).toContain("translateX(1px)");

    const pressed = renderToString(<UsersGroupIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateX(1px)");

    const disabled = renderToString(<UsersGroupIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<UsersGroupIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-028: Invitar o agregar persona (user-plus)", () => {
  it("pulses plus sign 1.15x on hover, scale 1 at rest, no pulse when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<UserPlusIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<UserPlusIcon size={20} state="hover" />);
    expect(hover).toContain("scale(1.15)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<UserPlusIcon size={20} state="focus" />);
    expect(focus).toContain("scale(1.15)");

    const pressed = renderToString(<UserPlusIcon size={20} state="pressed" />);
    expect(pressed).toContain("scale(1.15)");

    const disabled = renderToString(<UserPlusIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<UserPlusIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-029: Carrito (cart)", () => {
  it("shifts cart 2px right on hover, no shift at rest, no shift when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<CartIcon size={20} state="rest" />);
    expect(rest).toContain("translateX(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<CartIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(2px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<CartIcon size={20} state="focus" />);
    expect(focus).toContain("translateX(2px)");

    const pressed = renderToString(<CartIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateX(2px)");

    const disabled = renderToString(<CartIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<CartIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-030: Producto (box)", () => {
  it("lifts box lid 1.5px on hover, no lift at rest, no lift when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<BoxIcon size={20} state="rest" />);
    expect(rest).toContain("translateY(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<BoxIcon size={20} state="hover" />);
    expect(hover).toContain("translateY(-1.5px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<BoxIcon size={20} state="focus" />);
    expect(focus).toContain("translateY(-1.5px)");

    const pressed = renderToString(<BoxIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateY(-1.5px)");

    const disabled = renderToString(<BoxIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<BoxIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateY(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-031: Inventario (boxes)", () => {
  it("scales group 1.05x on hover, scale 1 at rest, no scale when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<BoxesIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<BoxesIcon size={20} state="hover" />);
    expect(hover).toContain("scale(1.05)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<BoxesIcon size={20} state="focus" />);
    expect(focus).toContain("scale(1.05)");

    const pressed = renderToString(<BoxesIcon size={20} state="pressed" />);
    expect(pressed).toContain("scale(1.05)");

    const disabled = renderToString(<BoxesIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<BoxesIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-032: Cobrar (credit-card)", () => {
  it("shifts stripe 1px right on hover, no shift at rest, no shift when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<CreditCardActionIcon size={20} state="rest" />);
    expect(rest).toContain("translateX(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<CreditCardActionIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(1px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<CreditCardActionIcon size={20} state="focus" />);
    expect(focus).toContain("translateX(1px)");

    const pressed = renderToString(<CreditCardActionIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateX(1px)");

    const disabled = renderToString(<CreditCardActionIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<CreditCardActionIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-033: Caja y saldo (wallet)", () => {
  it("opens wallet flap 1px up on hover, no lift at rest, no lift when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<WalletIcon size={20} state="rest" />);
    expect(rest).toContain("translateY(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<WalletIcon size={20} state="hover" />);
    expect(hover).toContain("translateY(-1px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<WalletIcon size={20} state="focus" />);
    expect(focus).toContain("translateY(-1px)");

    const pressed = renderToString(<WalletIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateY(-1px)");

    const disabled = renderToString(<WalletIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<WalletIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateY(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-034: Tendencia (chart-line)", () => {
  it("has stroke-dasharray on trend line, transition:none when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<ChartLineIcon size={20} state="rest" />);
    expect(rest).toContain("stroke-dasharray");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<ChartLineIcon size={20} state="hover" />);
    expect(hover).toContain("stroke-dasharray");
    assertSVGDimensions(hover, 20);

    const disabled = renderToString(<ChartLineIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<ChartLineIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("transition:none");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-035: Comparar ventas (chart-column-increasing)", () => {
  it("grows tallest bar scaleY(1.15) on hover, scaleY(1) at rest, no scale when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<ChartColumnIncreasingIcon size={20} state="rest" />);
    expect(rest).toContain("scaleY(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<ChartColumnIncreasingIcon size={20} state="hover" />);
    expect(hover).toContain("scaleY(1.15)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<ChartColumnIncreasingIcon size={20} state="focus" />);
    expect(focus).toContain("scaleY(1.15)");

    const pressed = renderToString(<ChartColumnIncreasingIcon size={20} state="pressed" />);
    expect(pressed).toContain("scaleY(1.15)");

    const disabled = renderToString(<ChartColumnIncreasingIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<ChartColumnIncreasingIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scaleY(1)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-036: Participacion (chart-pie)", () => {
  it("rotates pie segment 15deg on hover, 0deg at rest, no rotation when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<ChartPieIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<ChartPieIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(15deg)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<ChartPieIcon size={20} state="focus" />);
    expect(focus).toContain("rotate(15deg)");

    const pressed = renderToString(<ChartPieIcon size={20} state="pressed" />);
    expect(pressed).toContain("rotate(15deg)");

    const disabled = renderToString(<ChartPieIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<ChartPieIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-037: Documento (file-text)", () => {
  it("dims inner lines opacity:0.7 on hover, opacity:1 at rest, no dim when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<FileTextIcon size={20} state="rest" />);
    expect(rest).toContain("opacity:1");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<FileTextIcon size={20} state="hover" />);
    expect(hover).toContain("opacity:0.7");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<FileTextIcon size={20} state="focus" />);
    expect(focus).toContain("opacity:0.7");

    const pressed = renderToString(<FileTextIcon size={20} state="pressed" />);
    expect(pressed).toContain("opacity:0.7");

    const disabled = renderToString(<FileTextIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<FileTextIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("opacity:1");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-038: Cerrar sesion (logout)", () => {
  it("shifts exit arrow 2px right on hover, no shift at rest, no shift when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<LogoutActionIcon size={20} state="rest" />);
    expect(rest).toContain("translateX(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<LogoutActionIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(2px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<LogoutActionIcon size={20} state="focus" />);
    expect(focus).toContain("translateX(2px)");

    const pressed = renderToString(<LogoutActionIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateX(2px)");

    const disabled = renderToString(<LogoutActionIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<LogoutActionIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-039: Bloqueo (lock)", () => {
  it("lifts shackle arc 1.5px on hover, no lift at rest, no lift when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<LockIcon size={20} state="rest" />);
    expect(rest).toContain("translateY(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<LockIcon size={20} state="hover" />);
    expect(hover).toContain("translateY(-1.5px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<LockIcon size={20} state="focus" />);
    expect(focus).toContain("translateY(-1.5px)");

    const pressed = renderToString(<LockIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateY(-1.5px)");

    const disabled = renderToString(<LockIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<LockIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateY(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-040: Seguridad (shield-check)", () => {
  it("draws inner check via stroke-dasharray on success/hover, transition:none when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<ShieldCheckIcon size={20} state="rest" />);
    expect(rest).toContain("stroke-dasharray");
    assertSVGDimensions(rest, 20);

    const success = renderToString(<ShieldCheckIcon size={20} state="success" />);
    expect(success).toContain("stroke-dasharray");
    assertSVGDimensions(success, 20);

    const hover = renderToString(<ShieldCheckIcon size={20} state="hover" />);
    expect(hover).toContain("stroke-dasharray");

    const disabled = renderToString(<ShieldCheckIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<ShieldCheckIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("transition:none");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-041: Tema oscuro (moon)", () => {
  it("rotates moon 15deg on hover, 0deg at rest, no rotation when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<MoonIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<MoonIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(15deg)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<MoonIcon size={20} state="focus" />);
    expect(focus).toContain("rotate(15deg)");

    const pressed = renderToString(<MoonIcon size={20} state="pressed" />);
    expect(pressed).toContain("rotate(15deg)");

    const disabled = renderToString(<MoonIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<MoonIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-042: Tema claro (sun)", () => {
  it("rotates sun rays 45deg on hover, 0deg at rest, no rotation when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<SunIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<SunIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(45deg)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<SunIcon size={20} state="focus" />);
    expect(focus).toContain("rotate(45deg)");

    const pressed = renderToString(<SunIcon size={20} state="pressed" />);
    expect(pressed).toContain("rotate(45deg)");

    const disabled = renderToString(<SunIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<SunIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-043: Menu principal (menu)", () => {
  it("shifts middle bar 1.5px on hover, no shift at rest, no shift when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<MenuIcon size={20} state="rest" />);
    expect(rest).toContain("translateX(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<MenuIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(1.5px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<MenuIcon size={20} state="focus" />);
    expect(focus).toContain("translateX(1.5px)");

    const pressed = renderToString(<MenuIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateX(1.5px)");

    const disabled = renderToString(<MenuIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<MenuIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-044: Abrir recurso externo (external-link)", () => {
  it("shifts arrow 1.5px northeast on hover, no shift when reduced, SVG dimensions fixed", () => {
    const hover = renderToString(<ExternalLinkIcon size={20} state="hover" />);
    expect(hover).toContain("translate(1.5px, -1.5px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<ExternalLinkIcon size={20} state="focus" />);
    expect(focus).toContain("translate(1.5px, -1.5px)");

    const pressed = renderToString(<ExternalLinkIcon size={20} state="pressed" />);
    expect(pressed).toContain("translate(1.5px, -1.5px)");

    const disabled = renderToString(<ExternalLinkIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<ExternalLinkIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).not.toContain("translate(1.5px, -1.5px)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-045: Enviar (send)", () => {
  it("launches paper plane on hover, no launch when reduced, SVG dimensions fixed", () => {
    const hover = renderToString(<SendActionIcon size={20} state="hover" />);
    expect(hover).toContain("translate(1.5px, -1px) rotate(5deg)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<SendActionIcon size={20} state="focus" />);
    expect(focus).toContain("translate(1.5px, -1px) rotate(5deg)");

    const pressed = renderToString(<SendActionIcon size={20} state="pressed" />);
    expect(pressed).toContain("translate(1.5px, -1px) rotate(5deg)");

    const disabled = renderToString(<SendActionIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<SendActionIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).not.toContain("translate(1.5px, -1px) rotate(5deg)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-046: Adjuntar (attach-file)", () => {
  it("rotates paperclip 10deg on hover, 0deg at rest, no rotation when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<AttachFileIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<AttachFileIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(10deg)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<AttachFileIcon size={20} state="focus" />);
    expect(focus).toContain("rotate(10deg)");

    const pressed = renderToString(<AttachFileIcon size={20} state="pressed" />);
    expect(pressed).toContain("rotate(10deg)");

    const disabled = renderToString(<AttachFileIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<AttachFileIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-047: Vincular (link)", () => {
  it("compresses chain scale(0.96) on hover, scale(1) at rest, no scale when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<LinkChainIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<LinkChainIcon size={20} state="hover" />);
    expect(hover).toContain("scale(0.96)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<LinkChainIcon size={20} state="focus" />);
    expect(focus).toContain("scale(0.96)");

    const pressed = renderToString(<LinkChainIcon size={20} state="pressed" />);
    expect(pressed).toContain("scale(0.96)");

    const disabled = renderToString(<LinkChainIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<LinkChainIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-048: Reordenar (grip-vertical)", () => {
  it("scales dots 1.1x on hover, scale(1) at rest, no scale when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<GripVerticalIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<GripVerticalIcon size={20} state="hover" />);
    expect(hover).toContain("scale(1.1)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<GripVerticalIcon size={20} state="focus" />);
    expect(focus).toContain("scale(1.1)");

    const pressed = renderToString(<GripVerticalIcon size={20} state="pressed" />);
    expect(pressed).toContain("scale(1.1)");

    const disabled = renderToString(<GripVerticalIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<GripVerticalIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-049: Ampliar (expand)", () => {
  it("expands arrows 1.08x on hover, scale(1) at rest, no scale when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<ExpandIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<ExpandIcon size={20} state="hover" />);
    expect(hover).toContain("scale(1.08)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<ExpandIcon size={20} state="focus" />);
    expect(focus).toContain("scale(1.08)");

    const pressed = renderToString(<ExpandIcon size={20} state="pressed" />);
    expect(pressed).toContain("scale(1.08)");

    const disabled = renderToString(<ExpandIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<ExpandIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-050: Reducir (minimize)", () => {
  it("converges arrows scale(0.92) on hover, scale(1) at rest, no scale when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<MinimizeIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<MinimizeIcon size={20} state="hover" />);
    expect(hover).toContain("scale(0.92)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<MinimizeIcon size={20} state="focus" />);
    expect(focus).toContain("scale(0.92)");

    const pressed = renderToString(<MinimizeIcon size={20} state="pressed" />);
    expect(pressed).toContain("scale(0.92)");

    const disabled = renderToString(<MinimizeIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<MinimizeIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-051: Entrega (truck)", () => {
  it("moves truck 2px right on hover, no move at rest, no move when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<TruckIcon size={20} state="rest" />);
    expect(rest).toContain("translateX(0)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<TruckIcon size={20} state="hover" />);
    expect(hover).toContain("translateX(2px)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<TruckIcon size={20} state="focus" />);
    expect(focus).toContain("translateX(2px)");

    const pressed = renderToString(<TruckIcon size={20} state="pressed" />);
    expect(pressed).toContain("translateX(2px)");

    const disabled = renderToString(<TruckIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<TruckIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("translateX(0)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-052: Descuento (badge-percent)", () => {
  it("tilts badge 10deg on hover, 0deg at rest, no tilt when reduced, SVG dimensions fixed", () => {
    const rest = renderToString(<BadgePercentIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<BadgePercentIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(10deg)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<BadgePercentIcon size={20} state="focus" />);
    expect(focus).toContain("rotate(10deg)");

    const pressed = renderToString(<BadgePercentIcon size={20} state="pressed" />);
    expect(pressed).toContain("rotate(10deg)");

    const disabled = renderToString(<BadgePercentIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<BadgePercentIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-053: Eliminar con tachito (trash-2)", () => {
  it("lifts lid -18deg on hover without deleting, no lift when reduced, SVG dimensions fixed", () => {
    let deleted = false;

    const rest = renderToString(<Trash2Icon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<Trash2Icon size={20} state="hover" />);
    expect(hover).toContain("rotate(-18deg)");
    assertSVGDimensions(hover, 20);
    expect(deleted).toBe(false);

    const focus = renderToString(<Trash2Icon size={20} state="focus" />);
    expect(focus).toContain("rotate(-18deg)");

    const pressed = renderToString(<Trash2Icon size={20} state="pressed" />);
    expect(pressed).toContain("rotate(-18deg)");

    const disabled = renderToString(<Trash2Icon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<Trash2Icon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("rotate(0deg)");
    assertSVGDimensions(reduced, 20);
  });
});

describe("ICO-054: Eliminar con tachito simple (trash)", () => {
  it("shakes can 4deg on hover, 0deg at rest, no shake when reduced, both trash variants respect reduced motion equally, SVG dimensions fixed", () => {
    const rest = renderToString(<TrashIcon size={20} state="rest" />);
    expect(rest).toContain("rotate(0deg)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<TrashIcon size={20} state="hover" />);
    expect(hover).toContain("rotate(4deg)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<TrashIcon size={20} state="focus" />);
    expect(focus).toContain("rotate(4deg)");

    const pressed = renderToString(<TrashIcon size={20} state="pressed" />);
    expect(pressed).toContain("rotate(4deg)");

    const disabled = renderToString(<TrashIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reducedTrash = renderToString(<TrashIcon size={20} state="hover" reducedMotion={true} />);
    expect(reducedTrash).toContain("rotate(0deg)");
    assertSVGDimensions(reducedTrash, 20);

    const reducedTrash2 = renderToString(<Trash2Icon size={20} state="hover" reducedMotion={true} />);
    expect(reducedTrash2).toContain("rotate(0deg)");
    assertSVGDimensions(reducedTrash2, 20);
  });
});

describe("ICO-055: Iconos no incluidos en el catalogo (fallback)", () => {
  it("registers fallback with source URL, gesture, duration and all states; scale(1.05) on hover, no scale when reduced, SVG dimensions fixed", () => {
    const entry = ICON_DEPENDENCY_REGISTRY.find((e) => e.id === "ICO-055");
    expect(entry).toBeDefined();
    expect(entry!.originalUrl.length).toBeGreaterThan(10);
    expect(entry!.adaptation.length).toBeGreaterThan(5);
    expect(entry!.durationMs).toBeGreaterThan(0);
    expect(entry!.gestureType).toBeTruthy();
    expect(entry!.license).toBe("MIT");

    const rest = renderToString(<FallbackCatalogIcon size={20} state="rest" />);
    expect(rest).toContain("scale(1)");
    assertSVGDimensions(rest, 20);

    const hover = renderToString(<FallbackCatalogIcon size={20} state="hover" />);
    expect(hover).toContain("scale(1.05)");
    assertSVGDimensions(hover, 20);

    const focus = renderToString(<FallbackCatalogIcon size={20} state="focus" />);
    expect(focus).toContain("scale(1.05)");

    const pressed = renderToString(<FallbackCatalogIcon size={20} state="pressed" />);
    expect(pressed).toContain("scale(1.05)");

    const disabled = renderToString(<FallbackCatalogIcon size={20} state="disabled" />);
    expect(disabled).toContain("opacity-40");

    const reduced = renderToString(<FallbackCatalogIcon size={20} state="hover" reducedMotion={true} />);
    expect(reduced).toContain("scale(1)");
    assertSVGDimensions(reduced, 20);
  });
});
