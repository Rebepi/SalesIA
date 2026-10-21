export const templates: Record<string, string> = {
  products: "sku,name,category,unit_of_measure,unit_price,unit_cost,tax_rate\r\nPROD-001,Producto de referencia,Categoria general,NIU,100.00,70.00,0.18",
  customers: "code,doc_type,doc_number,legal_name,email\r\nCLI-001,RUC,20000000001,Cliente de referencia,contacto@cliente.test",
  inventory_adjustments: "warehouse_code,product_sku,quantity_delta,reason,unit_cost\r\nALM-01,PROD-001,10,Carga inicial,70.00"
};
