import { describe, it, expect } from "vitest";
import {
  createSaleDraftSchema,
  customerFormSchema,
  paymentFormSchema,
  moneyStringSchema,
  productFormSchema,
  pricePreviewSchema,
  categoryFormSchema,
  unitConversionSchema
} from "../schemas/forms";
import { DARK_THEME, LIGHT_THEME, DENSITY_TOKENS } from "../tokens";

describe("TS-003 and TS-005: Form Validation with Zod Contract", () => {
  it("validates well-formed sale draft schema", () => {
    const validData = {
      branch_id: "00000000-0000-0000-0000-000000000001",
      customer_id: "00000000-0000-0000-0000-000000000002",
      currency: "USD",
      is_credit: false,
      lines: [
        {
          sku: "PROD-1",
          product_name: "Laptop",
          quantity: 2,
          unit_price: "1200.50",
          tax_rate: "0.18",
          discount: "0.00",
          cost_snapshot: "800.00"
        }
      ]
    };

    const parsed = createSaleDraftSchema.safeParse(validData);
    expect(parsed.success).toBe(true);
  });

  it("rejects invalid sale draft with negative or zero quantity", () => {
    const invalidData = {
      branch_id: "00000000-0000-0000-0000-000000000001",
      customer_id: "00000000-0000-0000-0000-000000000002",
      lines: [
        {
          sku: "PROD-1",
          product_name: "Laptop",
          quantity: 0,
          unit_price: "1200.50"
        }
      ]
    };

    const parsed = createSaleDraftSchema.safeParse(invalidData);
    expect(parsed.success).toBe(false);
  });

  it("validates and rejects malformed money strings", () => {
    expect(moneyStringSchema.safeParse("100.50").success).toBe(true);
    expect(moneyStringSchema.safeParse("0.00").success).toBe(true);
    expect(moneyStringSchema.safeParse("999999.9999").success).toBe(true);
    expect(moneyStringSchema.safeParse("-50.00").success).toBe(false);
    expect(moneyStringSchema.safeParse("abc").success).toBe(false);
    expect(moneyStringSchema.safeParse("100.12345").success).toBe(false);
  });

  it("validates customer form schema with document types", () => {
    const validCustomer = {
      legal_name: "Acme Corporation SAC",
      doc_type: "RUC",
      doc_number: "20123456789",
      credit_limit: "5000.00"
    };
    expect(customerFormSchema.safeParse(validCustomer).success).toBe(true);

    const invalidDoc = {
      legal_name: "Acme Corporation SAC",
      doc_type: "INVALID_TYPE",
      doc_number: "20123456789"
    };
    expect(customerFormSchema.safeParse(invalidDoc).success).toBe(false);
  });

  it("validates payment schema methods and currency matching", () => {
    const payment = {
      sale_id: "00000000-0000-0000-0000-000000000001",
      amount: "150.00",
      payment_method: "CASH",
      currency: "USD"
    };
    expect(paymentFormSchema.safeParse(payment).success).toBe(true);
  });
});

describe("TS-012: UI Design Tokens and Theme Consistency", () => {
  it("verifies dark and light theme tokens have all required semantic keys", () => {
    const keys = [
      "background",
      "surface",
      "surfaceSecondary",
      "textPrimary",
      "textSecondary",
      "border",
      "primary",
      "success",
      "warning",
      "danger"
    ] as const;

    for (const key of keys) {
      expect(DARK_THEME[key]).toBeDefined();
      expect(LIGHT_THEME[key]).toBeDefined();
    }
  });

  it("verifies density settings contain consistent operational metrics", () => {
    expect(DENSITY_TOKENS.comfortable.tableRowHeight).toBe("h-12");
    expect(DENSITY_TOKENS.compact.tableRowHeight).toBe("h-9");
    expect(DENSITY_TOKENS.comfortable.buttonPadding).toBeDefined();
    expect(DENSITY_TOKENS.compact.buttonPadding).toBeDefined();
  });
});

describe("FAL-011 and CAT-001 to CAT-021: Catalog and Pricing Contracts", () => {
  it("validates product schema with physical and service properties", () => {
    const validProduct = {
      sku: "PROD-SKU-01",
      name: "Standard Laptop",
      unit_of_measure: "NIU",
      unit_price: "850.00",
      tax_rate: "0.18",
      category: "Hardware",
      product_type: "product" as const,
      track_inventory: true,
      allow_fractional: false
    };
    expect(productFormSchema.safeParse(validProduct).success).toBe(true);

    const validService = {
      sku: "SRV-SUPPORT-01",
      name: "Soporte Anual",
      unit_price: "250.00",
      product_type: "service" as const,
      track_inventory: false
    };
    expect(productFormSchema.safeParse(validService).success).toBe(true);

    const invalidPrice = {
      sku: "PROD-BAD",
      name: "Bad Item",
      unit_price: "-10.00"
    };
    expect(productFormSchema.safeParse(invalidPrice).success).toBe(false);
  });

  it("validates price preview simulation contract and positive quantities", () => {
    const validPreview = {
      currency: "USD",
      customer_id: "00000000-0000-0000-0000-000000000001",
      lines: [
        {
          product_id: "00000000-0000-0000-0000-000000000002",
          quantity: 5
        }
      ]
    };
    expect(pricePreviewSchema.safeParse(validPreview).success).toBe(true);

    const invalidPreviewEmptyLines = {
      currency: "USD",
      lines: []
    };
    expect(pricePreviewSchema.safeParse(invalidPreviewEmptyLines).success).toBe(false);

    const invalidPreviewNegativeQty = {
      currency: "USD",
      lines: [
        {
          product_id: "00000000-0000-0000-0000-000000000002",
          quantity: -1
        }
      ]
    };
    expect(pricePreviewSchema.safeParse(invalidPreviewNegativeQty).success).toBe(false);
  });

  it("validates category hierarchy contract", () => {
    const rootCategory = {
      code: "ELEC",
      name: "Electrónica",
      parent_id: null
    };
    expect(categoryFormSchema.safeParse(rootCategory).success).toBe(true);

    const subCategory = {
      code: "COMP",
      name: "Cómputo",
      parent_id: "00000000-0000-0000-0000-000000000001"
    };
    expect(categoryFormSchema.safeParse(subCategory).success).toBe(true);

    const invalidCategory = {
      code: "",
      name: "Sin Código"
    };
    expect(categoryFormSchema.safeParse(invalidCategory).success).toBe(false);
  });

  it("validates unit conversion contract", () => {
    const validConversion = {
      from_unit_code: "CJ",
      to_unit_code: "NIU",
      factor: 12
    };
    expect(unitConversionSchema.safeParse(validConversion).success).toBe(true);

    const invalidFactor = {
      from_unit_code: "CJ",
      to_unit_code: "NIU",
      factor: -5
    };
    expect(unitConversionSchema.safeParse(invalidFactor).success).toBe(false);
  });
});

