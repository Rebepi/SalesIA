import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { InfoTooltip } from "../components/InfoTooltip";

describe("InfoTooltip", () => {
  it("expone una descripción accesible y la muestra con puntero o teclado", () => {
    const html = renderToStaticMarkup(
      <InfoTooltip
        title="Ventas netas"
        description="Facturación después de devoluciones aprobadas."
      />
    );

    expect(html).toContain('tabindex="0"');
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Información sobre Ventas netas"');
    expect(html).toContain('aria-describedby="info-tooltip-');
    expect(html).toContain('role="tooltip"');
    expect(html).toContain('aria-hidden="true"');
    expect(html).toContain("Facturación después de devoluciones aprobadas.");
  });
});
