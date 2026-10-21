import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { CustomSelect } from "../components/CustomSelect";

describe("CustomSelect", () => {
  it("keeps named values and validation in the form while exposing a custom combobox", () => {
    const html = renderToStaticMarkup(<CustomSelect id="currency" name="currency" defaultValue="PEN" required aria-label="Moneda"><option value="USD">Dólares</option><option value="PEN">Soles</option></CustomSelect>);
    expect(html).toContain('name="currency"');
    expect(html).toContain('value="PEN" selected=""');
    expect(html).toContain('role="combobox"');
    expect(html).toContain('aria-required="true"');
    expect(html).toContain('aria-hidden="true"');
    expect(html).toContain('type="button"');
  });

  it("preserves disabled choices and associates the visible control with its error", () => {
    const html = renderToStaticMarkup(<CustomSelect id="branch" disabled aria-invalid="true" aria-describedby="branch-error"><option value="closed" disabled>Sede cerrada</option></CustomSelect>);
    expect(html).toContain('id="branch"');
    expect(html).toContain('aria-describedby="branch-error"');
    expect(html).toContain('aria-invalid="true"');
    expect(html).toContain('value="closed" disabled=""');
    expect(html).toMatch(/<button[^>]*disabled=""/);
  });
});
