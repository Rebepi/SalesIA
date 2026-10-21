import * as transporte from "../api/NewSalePOSModal";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { clearDraft, readDraft, writeDraft } from "../../../ui/drafts";
import { useToast } from "../../../ui/toast/ToastContext";
import { RemoteEntityOption } from "../../../ui/components/RemoteEntitySelect";
import { CheckoutPayment } from "../components/PosPaymentEditor";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { CustomerItem } from "../types/NewSalePOSModal";
import { ProductItem } from "../types/NewSalePOSModal";
import { SaleCartLine } from "../types/NewSalePOSModal";
import { SerialItem } from "../types/NewSalePOSModal";
import { WarehouseItem } from "../types/NewSalePOSModal";
import { BranchItem } from "../types/NewSalePOSModal";
import { PricingResult } from "../types/NewSalePOSModal";
import { SalesRepItem } from "../types/NewSalePOSModal";
import { NewSalePOSModalProps } from "../types/NewSalePOSModal";
import { DRAFT_KEY } from "../support/NewSalePOSModal";
import { EMPTY_DRAFT } from "../support/NewSalePOSModal";
import { PosHoldSale, getHoldSales, saveHoldSale, deleteHoldSale, getAllowCreditSalesConfig } from "../support/posHoldSales";

export function useNewSalePOSModal({ isOpen, onClose, onSaleCreated, initialCustomerId, sourceSaleId: propSourceSaleId }: NewSalePOSModalProps) {
  const [activeSourceSaleId, setActiveSourceSaleId] = useState<string | undefined>(propSourceSaleId);

  useEffect(() => {
    if (isOpen) {
      const fromSession = typeof sessionStorage !== "undefined" ? sessionStorage.getItem("salesia_retake_sale_id") || sessionStorage.getItem("salesia_repeat_sale_id") || undefined : undefined;
      const targetId = propSourceSaleId || fromSession;
      if (targetId) {
        setActiveSourceSaleId(targetId);
      }
    }
  }, [isOpen, propSourceSaleId]);

  const initialDraft = useMemo(() => readDraft(DRAFT_KEY, EMPTY_DRAFT), []);

  const { confirm, ConfirmDialogNode } = useConfirm();

  const [customer, setCustomer] = useState<CustomerItem | undefined>(initialDraft.customer);

  const [warehouseId, setWarehouseId] = useState(initialDraft.warehouseId);

  const [isCredit, setIsCredit] = useState(initialDraft.isCredit);
  const [allowCreditSales, setAllowCreditSales] = useState<boolean>(() => getAllowCreditSalesConfig());

  useEffect(() => {
    if (isOpen) {
      setAllowCreditSales(getAllowCreditSalesConfig());
    }
  }, [isOpen]);

  useEffect(() => {
    const handleCreditConfigChange = (e: Event) => {
      const customEvent = e as CustomEvent<{ allowed: boolean }>;
      if (customEvent.detail && typeof customEvent.detail.allowed === "boolean") {
        setAllowCreditSales(customEvent.detail.allowed);
      } else {
        setAllowCreditSales(getAllowCreditSalesConfig());
      }
    };
    window.addEventListener("salesia:allow-credit-changed", handleCreditConfigChange);
    return () => window.removeEventListener("salesia:allow-credit-changed", handleCreditConfigChange);
  }, []);

  useEffect(() => {
    if (!allowCreditSales && isCredit) {
      setIsCredit(false);
    }
  }, [allowCreditSales, isCredit]);

  const [documentType, setDocumentType] = useState<"RECEIPT" | "INVOICE" | "SALE_NOTE">(initialDraft.documentType || "RECEIPT");

  const [cart, setCart] = useState<SaleCartLine[]>(initialDraft.cart);

  const [couponCode, setCouponCode] = useState(initialDraft.couponCode || "");

  const [notes, setNotes] = useState(initialDraft.notes || "");

  const [deliveryAddress, setDeliveryAddress] = useState(initialDraft.deliveryAddress || "");

  const [internalObservations, setInternalObservations] = useState(initialDraft.internalObservations || "");

  const [exchangeRate, setExchangeRate] = useState(initialDraft.exchangeRate || "1");

  const [salesRepId, setSalesRepId] = useState(initialDraft.salesRepId || "");

  const [salesReps, setSalesReps] = useState<SalesRepItem[]>([]);

  const [pricing, setPricing] = useState<Record<string, PricingResult>>({});

  const [pricingBusy, setPricingBusy] = useState(false);

  const [priceDetailsOpen, setPriceDetailsOpen] = useState(false);

  const [checkoutPayments, setCheckoutPayments] = useState<CheckoutPayment[]>([]);

  const [availableSerials, setAvailableSerials] = useState<Record<string, SerialItem[]>>({});

  const [paymentsValid, setPaymentsValid] = useState(false);

  const [sourceStatus, setSourceStatus] = useState<string>();

  const [sourceVersion, setSourceVersion] = useState<number>();

  const [warehouses, setWarehouses] = useState<WarehouseItem[]>([]);

  const [branches, setBranches] = useState<BranchItem[]>([]);

  const [currency, setCurrency] = useState("");

  const [defaultTaxRate, setDefaultTaxRate] = useState("0");

  const [roundingMode, setRoundingMode] = useState("ROUND_HALF_EVEN");

  const [taxIncluded, setTaxIncluded] = useState(false);

  const [boletaDniThreshold, setBoletaDniThreshold] = useState(700);

  const [search, setSearch] = useState("");

  const [products, setProducts] = useState<ProductItem[]>([]);

  const [productTotal, setProductTotal] = useState(0);

  const [productOffset, setProductOffset] = useState(0);

  const [productsBusy, setProductsBusy] = useState(false);

  const [contextBusy, setContextBusy] = useState(false);

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState("");
  const [catalogError, setCatalogError] = useState("");
  const [pricingError, setPricingError] = useState("");
  const [pricingRevision, setPricingRevision] = useState(0);

  const [customerDrawerOpen, setCustomerDrawerOpen] = useState(false);

  const [completed, setCompleted] = useState(false);

  const [tabFilter, setTabFilter] = useState<"ALL" | "FAVORITES" | "TOP_SELLERS">("ALL");

  const [onlyInStock, setOnlyInStock] = useState(false);

  const [viewMode, setViewMode] = useState<"GRID" | "LIST">("GRID");

  const [categoryFilter, setCategoryFilter] = useState("");

  const [brandFilter, setBrandFilter] = useState("");

  const [retryCount, setRetryCount] = useState(0);

  const [holdSales, setHoldSales] = useState<PosHoldSale[]>(() => getHoldSales());
  const [holdModalOpen, setHoldModalOpen] = useState(false);
  const [holdLabelDialogOpen, setHoldLabelDialogOpen] = useState(false);
  const [holdLabelDefault, setHoldLabelDefault] = useState("");

  useEffect(() => {
    if (!isOpen) return;
    setHoldSales(getHoldSales());
    const timer = window.setInterval(() => {
      setHoldSales(getHoldSales());
    }, 15000);
    return () => window.clearInterval(timer);
  }, [isOpen]);

  const dialogRef = useRef<HTMLDialogElement>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);

  const idempotencyKeyRef = useRef(crypto.randomUUID());

  const toast = useToast();

  const isDirty = Boolean(customer || warehouseId || cart.length || isCredit || documentType !== "RECEIPT" || couponCode || notes || deliveryAddress || internalObservations);

  useEffect(() => {
    if (!isOpen) return;
    const handleReloadKey = async (event: KeyboardEvent) => {
      if (event.key === "F5" || (event.ctrlKey && (event.key === "r" || event.key === "R"))) {
        if (isDirty && !completed) {
          event.preventDefault();
          const ok = await confirm({
            title: "¿Quieres volver a cargar el sitio web?",
            text: "Es posible que los cambios no se guarden.",
            confirmLabel: "Volver a cargar",
            cancelLabel: "Cancelar",
            danger: true,
          });
          if (ok) {
            window.location.reload();
          }
        }
      }
    };
    window.addEventListener("keydown", handleReloadKey);
    return () => window.removeEventListener("keydown", handleReloadKey);
  }, [isOpen, isDirty, completed, confirm]);

  useEffect(() => {
    if (!isOpen) {
      dialogRef.current?.close();
      return;
    }
    setCompleted(false);
    idempotencyKeyRef.current = crypto.randomUUID();
    dialogRef.current?.showModal();
    loadContext();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || completed) return;
    writeDraft(DRAFT_KEY, { customer, warehouseId, isCredit, documentType, cart, couponCode, notes, deliveryAddress, internalObservations, exchangeRate, salesRepId });
  }, [isOpen, completed, customer, warehouseId, isCredit, documentType, cart, couponCode, notes, deliveryAddress, internalObservations, exchangeRate, salesRepId]);

  useEffect(() => {
    if (!isOpen || !cart.length) {
      setPricing({});
      setPricingError("");
      setPricingBusy(false);
      return;
    }
    const controller = new AbortController();
    setPricingBusy(true);
    setPricingError("");
    const timer = window.setTimeout(async () => {
      setPricingBusy(true);
      try {
        const rows = await Promise.all(
          cart
            .filter(line => !line.is_free_concept)
            .map(line => transporte.solicitarDatos({ controller, line, customer, couponCode }))
        );
        if (!controller.signal.aborted) {
          setPricing(Object.fromEntries(rows.map(row => [row.product_id, row])));
          setPricingError("");
        }
      } catch (requestError: unknown) {
        if (!controller.signal.aborted && (requestError as { name?: string })?.name !== "AbortError") {
          setPricing({});
          setPricingError(requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No se pudo calcular el precio comercial.");
        }
      } finally {
        if (!controller.signal.aborted) setPricingBusy(false);
      }
    }, 300);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [isOpen, cart, customer?.id, couponCode, pricingRevision]);

  useEffect(() => {
    if (!isOpen || !warehouseId) return;
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setProductsBusy(true);
      setCatalogError("");
      try {
        const params = new URLSearchParams({ warehouse_id: warehouseId, limit: "30", offset: String(productOffset) });
        if (search.trim()) params.set("search", search.trim());
        const response = await transporte.solicitarDatos2({ params, controller });
        if (!controller.signal.aborted) { setProducts(response.items || []); setProductTotal(response.total_count || 0); setCatalogError(""); }
      } catch (requestError: unknown) {
        if (!controller.signal.aborted && (requestError as { name?: string })?.name !== "AbortError") {
          setCatalogError("No se pudo consultar la disponibilidad de productos.");
        }
      } finally {
        if (!controller.signal.aborted) setProductsBusy(false);
      }
    }, 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [isOpen, warehouseId, search, productOffset, retryCount]);

  useEffect(() => {
    if (!isOpen || !warehouseId) return;
    const serializedProducts = cart.filter(line => line.product.has_serials);
    if (!serializedProducts.length) return;
    let active = true;
    Promise.all(serializedProducts.map(async line => {
      const response = await transporte.solicitarDatos3({ warehouseId, line });
      return [line.product.id, response.items.filter(item => item.status === "IN_STOCK")] as const;
    })).then(rows => {
      if (active) setAvailableSerials(previous => ({ ...previous, ...Object.fromEntries(rows) }));
    }).catch(() => {
      if (active) setError("No se pudieron consultar las series disponibles de los productos seleccionados.");
    });
    return () => { active = false; };
  }, [isOpen, warehouseId, cart.map(line => line.product.id).join("|")]);

  async function loadContext() {
    setContextBusy(true);
    setError("");
    try {
      const [companyResult, settingsResult, warehouseResult, branchResult, walkInResult, repResult] = await Promise.allSettled([
        transporte.solicitarLoadContext(),
        transporte.solicitarLoadContext2(),
        transporte.solicitarLoadContext3(),
        transporte.solicitarLoadContext4(),
        transporte.solicitarLoadContext5(),
        transporte.solicitarLoadContext6()
      ]);
      if (companyResult.status === "fulfilled") setCurrency(companyResult.value.base_currency);
      if (settingsResult.status === "fulfilled") {
        setDefaultTaxRate(String(settingsResult.value.default_tax_rate || "0"));
        setRoundingMode(settingsResult.value.rounding_mode || "ROUND_HALF_EVEN");
        setTaxIncluded(Boolean(settingsResult.value.tax_included_in_price));
        if (settingsResult.value.boleta_dni_threshold) {
          setBoletaDniThreshold(Number(settingsResult.value.boleta_dni_threshold));
        }
      }
      if (warehouseResult.status === "fulfilled") {
        const list = warehouseResult.value;
        setWarehouses(list);
        const userAssigned = localStorage.getItem("salesia_assigned_warehouse_id");
        const lastUsed = localStorage.getItem("salesia_last_pos_warehouse_id");
        const foundUser = list.find(w => w.warehouse_id === userAssigned);
        const foundMain = list.find(w => w.name?.toLowerCase().includes("principal") || w.name?.toLowerCase().includes("venta"));
        const foundLast = list.find(w => w.warehouse_id === lastUsed);
        const auto = foundUser || foundMain || foundLast || (list.length > 0 ? list[0] : null);
        if (auto) {
          setWarehouseId(auto.warehouse_id);
          localStorage.setItem("salesia_last_pos_warehouse_id", auto.warehouse_id);
        }
      }
      if (branchResult.status === "fulfilled") setBranches(branchResult.value);
      if (walkInResult.status === "fulfilled" && (!customer || customer.id === "walk-in-default")) {
        setCustomer(walkInResult.value);
      }
      if (repResult.status === "fulfilled") {
        setSalesReps(repResult.value.items.map(rep => ({ id: rep.rep_id, full_name: rep.full_name, code: rep.code })));
      }
      if (initialCustomerId) {
        const initCust = await transporte.solicitarLoadContext7({ initialCustomerId });
        setCustomer(initCust);
        if (initCust.doc_type?.toUpperCase() === "RUC" || initCust.doc_number?.replace(/\D/g, "").length === 11) {
          setDocumentType("INVOICE");
        }
      }
      const targetSourceId = activeSourceSaleId || propSourceSaleId || (typeof sessionStorage !== "undefined" ? sessionStorage.getItem("salesia_retake_sale_id") || sessionStorage.getItem("salesia_repeat_sale_id") || undefined : undefined);
      if (targetSourceId) {
        const source = await transporte.solicitarLoadContext8({ sourceSaleId: targetSourceId });
        const sourceCustomer = await transporte.solicitarLoadContext9({ source });
        const productRows = await Promise.all(source.lines.map(async line => {
          const available = await transporte.solicitarDatos4({ source, line });
          const product = available.items.find(item => item.id === line.product_id);
          if (!product) throw new Error(`El producto ${line.sku} ya no está disponible. Revisa la venta de origen antes de repetirla.`);
          return product ? { product, quantity: Number(line.quantity), serialNumbers: line.serial_numbers || [] } : null;
        }));
        setCustomer(sourceCustomer);
        setWarehouseId(source.warehouse_id);
        setDocumentType(source.document_type);
        setIsCredit(source.is_credit);
        setExchangeRate(source.exchange_rate || "1");
        setNotes(source.notes || "");
        setDeliveryAddress(source.delivery_address || "");
        setInternalObservations(source.internal_observations || "");
        setCouponCode(source.coupon_code || "");
        setSalesRepId(source.sales_rep_id || "");
        setSourceStatus(source.status);
        setSourceVersion(source.version);
        setCart(productRows.filter(Boolean) as SaleCartLine[]);
        setActiveSourceSaleId(targetSourceId);
        if (typeof sessionStorage !== "undefined") {
          sessionStorage.removeItem("salesia_retake_sale_id");
          sessionStorage.removeItem("salesia_repeat_sale_id");
        }
      }
      const requiredFailure = [companyResult, settingsResult, warehouseResult, branchResult].find(item => item.status === "rejected");
      if (requiredFailure?.status === "rejected") throw requiredFailure.reason;
      window.setTimeout(() => searchInputRef.current?.focus(), 0);
    } catch (requestError: unknown) {
      const detail = requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : requestError instanceof Error ? requestError.message : "No fue posible cargar la configuración necesaria.";
      setError(detail);
      toast.error("No se pudo preparar la venta", detail);
    } finally {
      setContextBusy(false);
    }
  }

  function handleWarehouseChange(newWarehouseId: string) {
    setWarehouseId(newWarehouseId);
    setProductOffset(0);
    localStorage.setItem("salesia_last_pos_warehouse_id", newWarehouseId);
    if (cart.length > 0 && newWarehouseId) {
      Promise.all(cart.map(async line => {
        if (!line.product.track_inventory || line.is_free_concept) return line;
        try {
          const res = await transporte.solicitarDatos4({
            source: { warehouse_id: newWarehouseId } as any,
            line: { sku: line.product.sku } as any
          });
          const match = res.items.find(p => p.id === line.product.id || p.sku === line.product.sku);
          return {
            ...line,
            product: {
              ...line.product,
              available_quantity: match ? match.available_quantity : "0"
            }
          };
        } catch {
          return line;
        }
      })).then(updated => setCart(updated));
    }
  }

  async function selectCustomer(custParam: string | CustomerItem, option?: RemoteEntityOption<CustomerItem>) {
    if (!custParam) {
      setCustomer(undefined);
      setIsCredit(false);
      return;
    }
    const prevPriceList = customer?.price_list_id;
    let selected: CustomerItem;
    if (typeof custParam === "object") {
      selected = custParam;
    } else {
      if (option?.data.is_walk_in) {
        selected = option.data;
      } else {
        try {
          selected = await transporte.solicitarSelectCustomer({ value: custParam });
        } catch {
          selected = option ? option.data : ({ id: custParam, legal_name: "Cliente", doc_type: "DNI", doc_number: "", code: "CLI" } as CustomerItem);
        }
      }
    }
    if (selected.id === "walk-in-default") {
      try { selected = await transporte.solicitarLoadContext5(); }
      catch { setError("No se pudo preparar el consumidor final. Vuelve a seleccionarlo antes de continuar."); return; }
    }
    setCustomer(selected);
    const cleanDoc = selected.doc_number?.replace(/\D/g, "") || "";
    if (selected.doc_type?.toUpperCase() === "RUC" || cleanDoc.length === 11) {
      setDocumentType("INVOICE");
    } else if (documentType !== "SALE_NOTE") {
      setDocumentType("RECEIPT");
    }
    if (selected.is_walk_in) {
      setIsCredit(false);
    }
    if (cart.length > 0 && prevPriceList !== selected.price_list_id) {
      toast.info("Lista de precios", "Se actualizaron las tarifas para los productos en la canasta según el cliente.");
    }
  }

  function addProduct(product: ProductItem) {
    const available = Number(product.available_quantity || 0);
    const existing = cart.find(item => item.product.id === product.id);
    const nextQuantity = (existing?.quantity || 0) + 1;
    if (product.track_inventory && nextQuantity > available) {
      toast.warning("Existencias insuficientes", `${product.name} tiene ${available} ${product.unit_of_measure} disponibles.`);
      return;
    }
    setCart(previous => existing ? previous.map(item => item.product.id === product.id ? { ...item, quantity: nextQuantity } : item) : [...previous, { product, quantity: 1, serialNumbers: [] }]);
    setSearch("");
  }

  function handleSearchKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Enter" || !search.trim()) return;
    event.preventDefault();
    const exact = products.find(product => product.sku.toLocaleLowerCase() === search.trim().toLocaleLowerCase() || (product.barcode && product.barcode.toLowerCase() === search.trim().toLowerCase()));
    if (exact) addProduct(exact); else if (products.length === 1) addProduct(products[0]); else toast.info("Selecciona un producto", "Hay varios resultados disponibles.");
  }

  function updateQuantity(productId: string, delta: number) {
    setCart(previous => previous.flatMap(item => {
      if (item.product.id !== productId) return [item];
      const quantity = item.quantity + delta;
      if (quantity <= 0) return [];
      const available = Number(item.product.available_quantity || 0);
      if (item.product.track_inventory && !item.is_free_concept && quantity > available) {
        toast.warning("Existencias insuficientes", `Máximo disponible: ${available} ${item.product.unit_of_measure}.`);
        return [item];
      }
      return [{ ...item, quantity, serialNumbers: item.serialNumbers?.slice(0, quantity) }];
    }));
  }

  function updateLineQuantityDirect(productId: string, quantity: number) {
    if (quantity <= 0) {
      setCart(prev => prev.filter(l => l.product.id !== productId));
      return;
    }
    setCart(prev => prev.map(l => {
      if (l.product.id !== productId) return l;
      const available = Number(l.product.available_quantity || 0);
      if (l.product.track_inventory && !l.is_free_concept && quantity > available) {
        toast.warning("Existencias insuficientes", `Disponible: ${available} ${l.product.unit_of_measure}`);
        return { ...l, quantity: available };
      }
      return { ...l, quantity };
    }));
  }

  function updateLineNote(productId: string, note: string) {
    setCart(prev => prev.map(l => l.product.id === productId ? { ...l, note } : l));
  }

  function addFreeConcept(line: SaleCartLine) {
    setCart(prev => [...prev, line]);
    toast.success("Concepto libre agregado", line.product.name);
  }

  function updateSerials(productId: string, values: string[]) {
    setCart(previous => previous.map(line => line.product.id === productId ? { ...line, serialNumbers: values } : line));
  }

  const totals = useMemo(() => cart.reduce((result, line) => {
    if (line.is_free_concept) {
      const price = Number(line.unit_price || line.product.unit_price || 0);
      const sub = price * line.quantity;
      const taxRate = Number(line.product.tax_rate || 0.18);
      const tax = taxIncluded ? sub - (sub / (1 + taxRate)) : sub * taxRate;
      const net = taxIncluded ? sub / (1 + taxRate) : sub;
      const total = net + tax;
      return {
        subtotal: result.subtotal + net,
        tax: result.tax + tax,
        total: result.total + total,
        discount: result.discount
      };
    }
    const resolved = pricing[line.product.id];
    if (resolved) return { subtotal: result.subtotal + Number(resolved.subtotal), tax: result.tax + Number(resolved.tax_amount), total: result.total + Number(resolved.total_estimated), discount: result.discount + Number(resolved.discount_applied) };
    const base = line.quantity * Number(line.product.unit_price || 0);
    const rate = Number(line.product.tax_rate || defaultTaxRate || 0);
    const net = taxIncluded ? base / (1 + rate) : base;
    const tax = taxIncluded ? base - net : base * rate;
    return { subtotal: result.subtotal + net, tax: result.tax + tax, total: result.total + net + tax, discount: result.discount };
  }, { subtotal: 0, tax: 0, total: 0, discount: 0 }), [cart, pricing, defaultTaxRate, taxIncluded]);

  const selectedWarehouse = warehouses.find(item => item.warehouse_id === warehouseId);

  const selectedBranch = branches.find(item => item.branch_id === selectedWarehouse?.branch_id);

  const balance = Number(customer?.current_balance || 0);

  const creditLimit = Number(customer?.credit_limit || 0);

  const creditAvailable = Math.max(0, creditLimit - balance);

  const creditUnavailable = Boolean(customer?.is_walk_in || customer?.is_credit_blocked || (isCredit && totals.total > creditAvailable));

  const isRucCustomer = Boolean(customer && (customer.doc_type?.toUpperCase() === "RUC" || customer.doc_number?.replace(/\D/g, "").length === 11));

  const showRucBoletaNotice = isRucCustomer && documentType === "RECEIPT";

  const confirmBlockerReason = useMemo(() => {
    if (!selectedWarehouse) {
      return "No tienes un almacén asignado. Pide a un administrador que te lo configure.";
    }
    if (!cart.length) {
      return "Falta agregar productos a la venta.";
    }
    if (!customer || customer.id === "walk-in-default") return "Selecciona un cliente válido o vuelve a elegir Consumidor final.";
    if (pricingBusy) return "Espera a que termine la verificación de precios.";
    if (pricingError) return "No se pudieron verificar los precios. Reintenta el cálculo antes de confirmar.";
    if (documentType === "INVOICE") {
      const cleanRuc = customer?.doc_number?.replace(/\D/g, "") || "";
      if (customer?.is_walk_in || cleanRuc.length !== 11) {
        return "Para Factura se requiere cliente con RUC de 11 dígitos, razón social y dirección fiscal.";
      }
    }
    if (documentType === "RECEIPT" && totals.total >= boletaDniThreshold) {
      const cleanDoc = customer?.doc_number?.replace(/\D/g, "") || "";
      if (customer?.is_walk_in || cleanDoc.length < 8) {
        return `Para este monto (${currency} ${totals.total.toFixed(2)}) se necesita identificar al comprador con DNI.`;
      }
    }
    if (isCredit && !allowCreditSales) {
      return "Las ventas a crédito están desactivadas en la configuración comercial.";
    }
    if (isCredit && customer?.is_walk_in) {
      return "La condición de Crédito comercial requiere un cliente registrado con crédito aprobado.";
    }
    if (isCredit && creditUnavailable) {
      return customer?.is_credit_blocked
        ? `Crédito bloqueado: ${customer?.credit_block_reason || "revisión comercial requerida."}`
        : "El importe de la venta supera el crédito comercial disponible.";
    }
    const invalidStockLine = cart.find(line => line.product.track_inventory && !line.is_free_concept && line.quantity > Number(line.product.available_quantity || 0));
    if (invalidStockLine) {
      return `Stock insuficiente para ${invalidStockLine.product.name} (Disponible: ${invalidStockLine.product.available_quantity}).`;
    }
    if (!isCredit) {
      const paid = checkoutPayments.reduce((sum, p) => sum + (Number(p.amount) || 0), 0);
      const pending = Math.max(0, totals.total - paid);
      if (pending > 0.005) {
        return "Falta registrar el pago del saldo pendiente para completar la venta.";
      }
      if (!paymentsValid) {
        return null;
      }
    }
    return null;
  }, [selectedWarehouse, cart, documentType, customer, totals.total, boletaDniThreshold, currency, isCredit, allowCreditSales, creditUnavailable, paymentsValid, checkoutPayments, pricingError, pricingBusy]);

  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      if (onlyInStock && p.track_inventory && Number(p.available_quantity || 0) <= 0) {
        return false;
      }
      if (categoryFilter && p.category_name && p.category_name !== categoryFilter) {
        return false;
      }
      if (brandFilter && p.brand_name && p.brand_name !== brandFilter) {
        return false;
      }
      return true;
    });
  }, [products, onlyInStock, categoryFilter, brandFilter]);

  const availableCategories = useMemo(() => {
    const set = new Set<string>();
    products.forEach(p => { if (p.category_name) set.add(p.category_name); });
    return Array.from(set);
  }, [products]);

  const availableBrands = useMemo(() => {
    const set = new Set<string>();
    products.forEach(p => { if (p.brand_name) set.add(p.brand_name); });
    return Array.from(set);
  }, [products]);

  const handlePaymentsChange = useCallback((payments: CheckoutPayment[], valid: boolean) => {
    setCheckoutPayments(payments);
    setPaymentsValid(valid);
  }, []);

  async function requestClose() {
    if (!completed && isDirty && !await confirm({ title: "¿Deseas cerrar?", text: "La venta tiene cambios sin confirmar. El borrador se conservará para continuar después.", confirmLabel: "Cerrar", cancelLabel: "Quedarme" })) return;
    if (typeof sessionStorage !== "undefined") {
      sessionStorage.removeItem("salesia_retake_sale_id");
      sessionStorage.removeItem("salesia_repeat_sale_id");
    }
    onClose();
  }

  async function confirmSale() {
    if (confirmBlockerReason) {
      toast.warning("Validación requerida", confirmBlockerReason);
      return;
    }
    if (!isCredit && !paymentsValid) {
      toast.warning("Validación requerida", "Completa la información de los medios de pago.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const targetSaleId = activeSourceSaleId || propSourceSaleId;
      const resumeExisting = Boolean(targetSaleId && sourceStatus === "draft" && sourceVersion);
      const response = await transporte.solicitarConfirmSale({ resumeExisting, sourceSaleId: targetSaleId, idempotencyKeyRef, customer: customer!, warehouseId, selectedWarehouse: selectedWarehouse!, currency, isCredit, documentType, couponCode, notes, deliveryAddress, internalObservations, exchangeRate, salesRepId, sourceVersion, cart });
      const saleId = String(response.sale_id || response.id);
      await transporte.solicitarConfirmSale2({ saleId, isCredit, response });
      if (!isCredit) {
        for (const payment of checkoutPayments) {
          if (payment.amount <= 0) continue;
          await transporte.solicitarConfirmSale3({ saleId, payment, currency, exchangeRate });
        }
      }
      setCompleted(true);
      clearDraft(DRAFT_KEY);
      if (typeof sessionStorage !== "undefined") {
        sessionStorage.removeItem("salesia_retake_sale_id");
        sessionStorage.removeItem("salesia_repeat_sale_id");
      }
      toast.success("Venta registrada", isCredit ? "La venta quedó confirmada a crédito." : "La venta y sus cobros quedaron registrados.");
      onSaleCreated(saleId, false);
      onClose();
    } catch (requestError: unknown) {
      const detail = requestError && typeof requestError === "object" && "detail" in requestError ? String((requestError as { detail: unknown }).detail) : "No se pudo registrar la venta.";
      setError(detail);
      toast.error("Error al registrar", detail);
    } finally {
      setBusy(false);
    }
  }

  function suspendSale() {
    if (!cart.length) {
      toast.warning("Canasta vacía", "Agrega al menos un producto a la canasta para poner la venta en espera.");
      return;
    }
    const suggested = customer?.legal_name || "";
    setHoldLabelDefault(suggested);
    setHoldLabelDialogOpen(true);
  }

  function confirmSuspend(label: string) {
    setHoldLabelDialogOpen(false);
    saveHoldSale({
      label,
      customer,
      warehouseId,
      selectedWarehouse,
      currency,
      isCredit,
      documentType,
      couponCode,
      notes,
      deliveryAddress,
      internalObservations,
      exchangeRate,
      salesRepId,
      cart,
      totals
    });
    setCart([]);
    setCustomer(undefined);
    setNotes("");
    setDeliveryAddress("");
    setInternalObservations("");
    setCouponCode("");
    clearDraft(DRAFT_KEY);
    setHoldSales(getHoldSales());
    toast.success("Venta en espera guardada", `"${label || "Sin nombre"}" quedó guardada. Puedes atender al siguiente cliente.`);
  }

  async function retakeHoldSale(hold: PosHoldSale) {
    if (cart.length > 0) {
      const ok = await confirm({
        title: "¿Reemplazar canasta actual?",
        text: "Actualmente tienes productos en la canasta. ¿Deseas reemplazarlos por los de la venta en espera?",
        confirmLabel: "Sí, retomar",
        cancelLabel: "Cancelar"
      });
      if (!ok) return;
    }
    setCustomer(hold.customer);
    if (hold.warehouseId) setWarehouseId(hold.warehouseId);
    setDocumentType(hold.documentType);
    setIsCredit(hold.isCredit);
    setCart(hold.cart);
    setNotes(hold.notes || "");
    setDeliveryAddress(hold.deliveryAddress || "");
    setInternalObservations(hold.internalObservations || "");
    setCouponCode(hold.couponCode || "");
    if (hold.exchangeRate) setExchangeRate(hold.exchangeRate);
    if (hold.salesRepId) setSalesRepId(hold.salesRepId);
    deleteHoldSale(hold.id);
    setHoldSales(getHoldSales());
    setHoldModalOpen(false);
    toast.info("Venta retomada", "Se cargaron los productos en el mostrador.");
  }

  function discardHoldSale(id: string) {
    deleteHoldSale(id);
    setHoldSales(getHoldSales());
    toast.success("Venta descartada", "La venta en espera fue eliminada.");
  }

  return {
    ConfirmDialogNode,
    catalogError,
    pricingError,
    retryPricing: () => setPricingRevision(value => value + 1),
    customer,
    setCustomer,
    warehouseId,
    setWarehouseId: handleWarehouseChange,
    isCredit,
    setIsCredit,
    allowCreditSales,
    documentType,
    setDocumentType,
    cart,
    setCart,
    couponCode,
    setCouponCode,
    notes,
    setNotes,
    deliveryAddress,
    setDeliveryAddress,
    internalObservations,
    setInternalObservations,
    exchangeRate,
    setExchangeRate,
    salesRepId,
    setSalesRepId,
    salesReps,
    pricing,
    pricingBusy,
    priceDetailsOpen,
    setPriceDetailsOpen,
    availableSerials,
    paymentsValid,
    warehouses,
    setWarehouses,
    branches,
    currency,
    defaultTaxRate,
    roundingMode,
    taxIncluded,
    boletaDniThreshold,
    showRucBoletaNotice,
    search,
    setSearch,
    products: filteredProducts,
    productTotal,
    productOffset,
    setProductOffset,
    productsBusy,
    contextBusy,
    busy,
    error,
    customerDrawerOpen,
    setCustomerDrawerOpen,
    dialogRef,
    searchInputRef,
    selectCustomer,
    addProduct,
    handleSearchKeyDown,
    updateQuantity,
    updateLineQuantityDirect,
    updateLineNote,
    addFreeConcept,
    updateSerials,
    totals,
    selectedWarehouse,
    selectedBranch,
    balance,
    creditAvailable,
    creditUnavailable,
    handlePaymentsChange,
    requestClose,
    confirmSale,
    suspendSale,
    holdSales,
    holdModalOpen,
    setHoldModalOpen,
    holdLabelDialogOpen,
    setHoldLabelDialogOpen,
    holdLabelDefault,
    confirmSuspend,
    retakeHoldSale,
    discardHoldSale,
    confirmBlockerReason,
    tabFilter,
    setTabFilter,
    onlyInStock,
    setOnlyInStock,
    viewMode,
    setViewMode,
    categoryFilter,
    setCategoryFilter,
    brandFilter,
    setBrandFilter,
    availableCategories,
    availableBrands,
    retryLoadProducts: () => setRetryCount(v => v + 1),
  };
}