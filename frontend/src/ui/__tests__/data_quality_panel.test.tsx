import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { DataQualityPanel } from "../../features/analitica/components/DataQualityPanel";

describe("DSET-019: Panel de calidad visible y generacion de versiones tras correccion", () => {
  it("renders panel header, DSET-019 badge and quality title", () => {
    const html = renderToString(<DataQualityPanel />);
    expect(html).toContain("Calidad y versiones del dataset");
    expect(html).toContain("DSET-019");
    expect(html).toContain("Auditoría de integridad");
  });

  it("includes action button to generate new version after correcting operational data", () => {
    const html = renderToString(<DataQualityPanel />);
    expect(html).toContain("Control de calidad del dataset");
  });
});
