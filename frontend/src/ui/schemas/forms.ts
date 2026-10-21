import { z } from "zod";

export const uuidSchema = z
  .string()
  .regex(/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/, "Identificador UUID inválido");

export const moneyStringSchema = z
  .string()
  .regex(/^\d+(\.\d{1,4})?$/, "El importe debe ser una cantidad numérica válida con hasta 4 decimales")
  .refine((val) => Number(val) >= 0, "El importe no puede ser negativo");

export const saleLineItemSchema = z.object({
  product_id: uuidSchema.optional(),
  sku: z.string().min(1, "El SKU es obligatorio"),
  product_name: z.string().min(1, "El nombre del producto es obligatorio"),
  quantity: z.number().int().positive("La cantidad debe ser mayor a 0"),
  unit_price: moneyStringSchema,
  tax_rate: z.string().default("0.18"),
  discount: moneyStringSchema.default("0.00"),
  cost_snapshot: moneyStringSchema.default("0.00")
});

export const createSaleDraftSchema = z.object({
  company_id: uuidSchema.optional(),
  branch_id: uuidSchema,
  customer_id: uuidSchema,
  warehouse_id: uuidSchema.optional(),
  currency: z.string().length(3, "La divisa debe ser de 3 letras").default("USD"),
  is_credit: z.boolean().default(false),
  lines: z.array(saleLineItemSchema).min(1, "Debe agregar al menos una línea a la venta")
});

export const customerFormSchema = z.object({
  legal_name: z.string().min(2, "La razón social o nombre debe tener al menos 2 caracteres"),
  trade_name: z.string().optional(),
  doc_type: z.enum(["DNI", "RUC", "PASSPORT", "OTHER"]),
  doc_number: z.string().min(3, "El número de documento es obligatorio"),
  email: z.string().email("Correo electrónico inválido").optional().or(z.literal("")),
  phone: z.string().optional(),
  address: z.string().optional(),
  credit_limit: moneyStringSchema.default("0.00")
});

export const paymentFormSchema = z.object({
  sale_id: uuidSchema,
  amount: moneyStringSchema,
  payment_method: z.enum(["CASH", "TRANSFER", "CARD", "CREDIT"]),
  currency: z.string().length(3).default("USD"),
  reference_code: z.string().max(128).optional()
});

export const productFormSchema = z.object({
  sku: z.string().min(1, "El SKU es obligatorio"),
  name: z.string().min(1, "El nombre del producto es obligatorio"),
  unit_of_measure: z.string().default("NIU"),
  unit_price: moneyStringSchema,
  tax_rate: z.string().default("0.18"),
  category: z.string().optional(),
  product_type: z.enum(["product", "service", "kit"]).default("product"),
  track_inventory: z.boolean().default(true),
  allow_fractional: z.boolean().default(false)
});

export const pricePreviewLineSchema = z.object({
  product_id: uuidSchema,
  quantity: z.number().positive("La cantidad debe ser positiva")
});

export const pricePreviewSchema = z.object({
  currency: z.string().length(3).default("USD"),
  customer_id: uuidSchema.optional().nullable(),
  lines: z.array(pricePreviewLineSchema).min(1, "Debe incluir al menos una línea")
});

export const categoryFormSchema = z.object({
  code: z.string().min(1, "El código es obligatorio"),
  name: z.string().min(1, "El nombre es obligatorio"),
  parent_id: uuidSchema.optional().nullable()
});

export const unitConversionSchema = z.object({
  from_unit_code: z.string().min(1, "La unidad origen es obligatoria"),
  to_unit_code: z.string().min(1, "La unidad destino es obligatoria"),
  factor: z.number().positive("El factor debe ser mayor a cero")
});

export type SaleLineItemInput = z.infer<typeof saleLineItemSchema>;
export type CreateSaleDraftInput = z.infer<typeof createSaleDraftSchema>;
export type CustomerFormInput = z.infer<typeof customerFormSchema>;
export type PaymentFormInput = z.infer<typeof paymentFormSchema>;
export type ProductFormInput = z.infer<typeof productFormSchema>;
export type PricePreviewInput = z.infer<typeof pricePreviewSchema>;
export type CategoryFormInput = z.infer<typeof categoryFormSchema>;
export type UnitConversionInput = z.infer<typeof unitConversionSchema>;
