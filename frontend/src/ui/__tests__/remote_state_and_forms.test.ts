import { describe, it, expect, beforeEach } from "vitest";
import {
  buildQueryKey,
  areQueryKeysDistinct,
  createSalesIAQueryClient,
  handleSelectiveInvalidation,
  switchCompanyContext,
  OptimisticMutationManager,
  SequenceGuard,
  FormStateManager,
  AutoSaveQueue,
  DirtyNavigationGuard,
  SessionExpiryManager,
  ConflictResolver,
  OfflinePolicyManager,
  PWAStoragePolicy,
  TabSyncCoordinator,
  ChunkErrorManager,
  MountLifecycleAuditor,
  StorageSecurityAuditor,
  AsyncAccessibilityAnnouncer,
  verifyBackendOperationalError
} from "../../api/remoteState";
import { SalesIAClient } from "../../api/client";
import { moneyStringSchema } from "../schemas/forms";

describe("FAL-031: Remote State Centralization and API Contracts", () => {
  it("verifies SalesIAClient uses environment URL and handles headers safely", () => {
    const client = new SalesIAClient("http://api.enterprise.internal:8000/");
    expect(client.getBaseUrl()).toBe("http://api.enterprise.internal:8000");

    client.setCompanyId("00000000-0000-0000-0000-000000000001");
    expect(client.getCompanyId()).toBe("00000000-0000-0000-0000-000000000001");

    client.setTokens("mock_access", "mock_refresh", "00000000-0000-0000-0000-000000000001");
    expect(client.getAccessToken()).toBe("mock_access");

    client.clearTokens();
    expect(client.getAccessToken()).toBeNull();
    expect(client.getCompanyId()).toBeNull();
  });

  it("verifies switching company purges remote query cache", () => {
    const queryClient = createSalesIAQueryClient();
    queryClient.setQueryData(["sales", "company_1"], { total: 100 });
    expect(queryClient.getQueryData(["sales", "company_1"])).toBeDefined();

    switchCompanyContext(queryClient, "company_2");
    expect(queryClient.getQueryData(["sales", "company_1"])).toBeUndefined();
  });

  it("enforces monetary amounts strictly as string representation", () => {
    expect(moneyStringSchema.safeParse("1250.50").success).toBe(true);
    expect(moneyStringSchema.safeParse("0.00").success).toBe(true);
    expect(moneyStringSchema.safeParse("1250.5055").success).toBe(true);
    expect(moneyStringSchema.safeParse("-50.00").success).toBe(false);
    expect(moneyStringSchema.safeParse(1250.5).success).toBe(false);
  });
});

describe("REG-23: Backend Disconnection Operational Error", () => {
  it("verifies disconnecting backend renders operational error and never fake ready or demo numbers", () => {
    const offlineResult = verifyBackendOperationalError({
      isAvailable: false,
      statusCode: 503,
      errorMessage: "Service Unavailable"
    });

    expect(offlineResult.operationalErrorDisplayed).toBe(true);
    expect(offlineResult.substitutedByReady).toBe(false);
    expect(offlineResult.substitutedByDemoFigures).toBe(false);
    expect(offlineResult.substitutedBySuccessToast).toBe(false);
  });

  it("verifies live backend status is not faked on network 500 failure", () => {
    const serverErrorResult = verifyBackendOperationalError({
      isAvailable: false,
      statusCode: 500,
      errorMessage: "Internal Server Error"
    });

    expect(serverErrorResult.operationalErrorDisplayed).toBe(true);
    expect(serverErrorResult.substitutedByReady).toBe(false);
    expect(serverErrorResult.substitutedBySuccessToast).toBe(false);
  });
});

describe("FE-001: Complete Cache Key Structure", () => {
  it("builds deterministic cache keys with company, branch, scope, currency, timezone and version", () => {
    const key1 = buildQueryKey({
      companyId: "empresa-alpha",
      branchId: "branch-lima",
      scope: "sales_rep",
      endpoint: "/api/v1/sales",
      filters: { status: "confirmed", min_total: "100.00" },
      currency: "USD",
      timezone: "America/Lima",
      queryVersion: 2
    });

    const key2 = buildQueryKey({
      companyId: "empresa-beta",
      branchId: "branch-lima",
      scope: "sales_rep",
      endpoint: "/api/v1/sales",
      filters: { status: "confirmed", min_total: "100.00" },
      currency: "USD",
      timezone: "America/Lima",
      queryVersion: 2
    });

    expect(areQueryKeysDistinct(key1, key2)).toBe(true);
    expect(key1[0]).toBe("empresa-alpha");
    expect(key2[0]).toBe("empresa-beta");
  });

  it("prevents two branches of the same company from reusing incompatible query responses", () => {
    const branchAKey = buildQueryKey({
      companyId: "empresa-alpha",
      branchId: "sucursal-norte",
      endpoint: "/api/v1/inventory"
    });

    const branchBKey = buildQueryKey({
      companyId: "empresa-alpha",
      branchId: "sucursal-sur",
      endpoint: "/api/v1/inventory"
    });

    expect(areQueryKeysDistinct(branchAKey, branchBKey)).toBe(true);
  });
});

describe("FE-002: Selective Query Invalidation", () => {
  it("invalidates inventory and sales upon sale confirmation and flags analytics projection delay", () => {
    const queryClient = createSalesIAQueryClient();
    queryClient.setQueryData(["inventory"], [{ sku: "LAPTOP-01", stock: 10 }]);
    queryClient.setQueryData(["sales"], [{ sale_id: "s-1", total: "500" }]);

    const result = handleSelectiveInvalidation(queryClient, "confirm_sale", { entityId: "s-1" });

    expect(result.invalidatedPatterns).toContain("inventory");
    expect(result.invalidatedPatterns).toContain("sales");
    expect(result.invalidatedPatterns).toContain("dashboard");
    expect(result.staleProjection).toBe(true);
    expect(result.authoritativeUpdated).toBe(true);
  });

  it("updates authoritative product detail on product update without breaking unrelated caches", () => {
    const queryClient = createSalesIAQueryClient();
    const result = handleSelectiveInvalidation(queryClient, "product_update", { entityId: "prod-10" });
    expect(result.invalidatedPatterns).toContain("products");
    expect(result.staleProjection).toBe(false);
    expect(result.authoritativeUpdated).toBe(true);
  });
});

describe("FE-003: Limited Optimism and Rollback Policy", () => {
  const manager = new OptimisticMutationManager();

  it("permits optimistic updates for reversible UI preferences and labels", () => {
    expect(manager.isOptimisticAllowed("preferences")).toBe(true);
    expect(manager.isOptimisticAllowed("ui_settings")).toBe(true);
    expect(manager.isOptimisticAllowed("tag_label")).toBe(true);
    expect(manager.isOptimisticAllowed("bookmark")).toBe(true);
  });

  it("strictly forbids optimistic updates for financial payments and final stock deductions", () => {
    expect(manager.isOptimisticAllowed("payment")).toBe(false);
    expect(manager.isOptimisticAllowed("cobro")).toBe(false);
    expect(manager.isOptimisticAllowed("final_stock")).toBe(false);
    expect(manager.isOptimisticAllowed("confirm_sale")).toBe(false);
  });

  it("restores snapshot and reports recovery error without asserting financial success on mutation failure", async () => {
    let rolledBackState: { theme: string } | null = null;
    let currentState = { theme: "light" };

    const result = await manager.execute<{ theme: string }, { theme: string }>({
      operation: "preferences",
      getCurrentState: () => currentState,
      applyOptimistic: (s, vars) => {
        currentState = { ...s, ...vars };
        return currentState;
      },
      mutateFn: async () => {
        throw new Error("Conexión perdida con el servidor");
      },
      onRollback: (snap) => {
        rolledBackState = snap;
        currentState = snap;
      },
      variables: { theme: "dark" }
    });

    expect(result.success).toBe(false);
    expect(rolledBackState).toEqual({ theme: "light" });
    expect(currentState.theme).toBe("light");
    expect(result.error).toContain("Se restableció el estado previo");
  });
});

describe("FE-004: Out of Order Responses and Debounce Protection", () => {
  it("cancels obsolete query and prevents older search text from overwriting newer text", async () => {
    const guard = new SequenceGuard();

    const req1 = guard.createSequence("lap");
    expect(req1.seq).toBe(1);
    expect(req1.signal.aborted).toBe(false);

    const req2 = guard.createSequence("laptop");
    expect(req2.seq).toBe(2);
    expect(req1.signal.aborted).toBe(true);
    expect(req2.signal.aborted).toBe(false);

    expect(req1.isLatest()).toBe(false);
    expect(req2.isLatest()).toBe(true);
    expect(guard.getLatestQuery()).toBe("laptop");
  });
});

describe("FE-005: Form State Machine and Submission Guard", () => {
  it("tracks pristine, dirty, validating, submitting, success and error states", async () => {
    const form = new FormStateManager(
      { legal_name: "Acme", email: "info@acme.com" },
      (vals) => {
        if (!vals.legal_name || vals.legal_name.length < 2) {
          return { legal_name: "El nombre es muy corto" };
        }
        return null;
      }
    );

    expect(form.getStatus()).toBe("pristine");

    form.setValue("legal_name", "A");
    expect(form.getStatus()).toBe("dirty");

    let submitted = false;
    const ok = await form.submit(async () => {
      submitted = true;
    });

    expect(ok).toBe(false);
    expect(submitted).toBe(false);
    expect(form.getStatus()).toBe("error");
    expect(form.getFieldErrors().legal_name).toBe("El nombre es muy corto");

    form.setValue("legal_name", "Acme Corporation SAC");
    const ok2 = await form.submit(async () => {
      submitted = true;
    });

    expect(ok2).toBe(true);
    expect(submitted).toBe(true);
    expect(form.getStatus()).toBe("success");
  });

  it("prevents duplicate submissions on enter key and concurrent clicks", async () => {
    const form = new FormStateManager({ code: "CLI-01" });
    let executionCount = 0;

    const slowSubmit = async () => {
      await new Promise((resolve) => setTimeout(resolve, 20));
      executionCount += 1;
    };

    const firstPromise = form.handleEnterKey({ preventDefault: () => {} }, slowSubmit);
    const secondPromise = form.handleEnterKey({ preventDefault: () => {} }, slowSubmit);

    const [res1, res2] = await Promise.all([firstPromise, secondPromise]);
    expect(res1).toBe(true);
    expect(res2).toBe(false);
    expect(executionCount).toBe(1);
  });
});

describe("FE-006: Auto-Save Queue and Versioning", () => {
  it("preserves latest edition when older save response arrives out of order", async () => {
    let savedOnServer = "";
    const queue = new AutoSaveQueue<{ content: string }>(
      { content: "v1" },
      async (_ver, draft) => {
        savedOnServer = draft.content;
        return true;
      }
    );

    queue.updateDraft(() => ({ content: "edición 2" }));
    expect(queue.getCurrentVersion()).toBe(2);
    expect(queue.getStatus()).toBe("sin_sincronizar");

    await queue.triggerSave();
    expect(queue.getStatus()).toBe("guardado");
    expect(queue.getLastSavedVersion()).toBe(2);
    expect(savedOnServer).toBe("edición 2");

    queue.handleSaveResponse(1, true);
    expect(queue.getLastSavedVersion()).toBe(2);
    expect(queue.getDraft().content).toBe("edición 2");
  });
});

describe("FE-007: Dirty State Navigation and Context Quarantine", () => {
  const guard = new DirtyNavigationGuard();

  it("does not block navigation when form is pristine", () => {
    const check = guard.canLeave(false);
    expect(check.canLeave).toBe(true);
    expect(check.promptRequired).toBe(false);
  });

  it("warns before navigation when form has unsaved modifications", () => {
    const check = guard.canLeave(true);
    expect(check.canLeave).toBe(false);
    expect(check.promptRequired).toBe(true);
  });

  it("quarantines pending cart when user switches company context", () => {
    const initialCart = {
      companyId: "company-alpha",
      items: [{ sku: "P-1", qty: 2 }]
    };

    const result = guard.isolateCompanyCart(initialCart, "company-beta");
    expect(result.quarantined).toBe(true);
    expect(result.safeCart.companyId).toBe("company-beta");
    expect(result.safeCart.items.length).toBe(0);
  });
});

describe("FE-008: Expired Session and Sensitive Action Protection", () => {
  it("intercepts 401, preserves draft, and strictly forbids auto-resubmitting payments", () => {
    const expiry = new SessionExpiryManager();
    const sensitiveDraft = {
      sale_id: "00000000-0000-0000-0000-000000000001",
      amount: "250.00",
      payment_method: "CARD"
    };

    const outcome = expiry.handleUnauthorized({
      currentDraft: sensitiveDraft,
      isSensitivePayment: true
    });

    expect(outcome.sessionExpired).toBe(true);
    expect(outcome.draftPreserved).toBe(true);
    expect(outcome.autoResubmitPaymentAllowed).toBe(false);

    const restored = expiry.restorePreservedDraft<typeof sensitiveDraft>();
    expect(restored?.amount).toBe("250.00");
  });
});

describe("FE-009: Edit Conflict Resolution", () => {
  it("detects differences between local and remote fields and backs up local data on reload", () => {
    const local = { name: "Local Laptop", price: "900.00", stock: "15" };
    const remote = { name: "Remote Laptop", price: "950.00", stock: "15" };

    const resolver = new ConflictResolver(local, remote);
    const diffs = resolver.getDifferences();

    expect(diffs.length).toBe(2);
    expect(diffs.map((d) => d.field)).toContain("name");
    expect(diffs.map((d) => d.field)).toContain("price");

    const reloadResult = resolver.resolve("recargar");
    expect(reloadResult.result.price).toBe("950.00");
    expect(reloadResult.backedUpLocal.price).toBe("900.00");
    expect(reloadResult.message).toContain("Tu trabajo local se respaldó");
  });

  it("re-applies specific local fields over remote version", () => {
    const local = { name: "Mi Nombre Editado", price: "800.00" };
    const remote = { name: "Nombre Servidor", price: "850.00" };

    const resolver = new ConflictResolver(local, remote);
    const result = resolver.resolve("reaplicar", { reapplyFields: ["name"] });

    expect(result.result.name).toBe("Mi Nombre Editado");
    expect(result.result.price).toBe("850.00");
  });
});

describe("FE-010: Offline Mode Policy", () => {
  const offline = new OfflinePolicyManager();

  beforeEach(() => {
    offline.setOnline(false);
  });

  it("allows read access only if authorized and offline policy is enabled", () => {
    expect(offline.canRead(true, true)).toBe(true);
    expect(offline.canRead(true, false)).toBe(false);
    expect(offline.canRead(false, true)).toBe(false);
  });

  it("strictly rejects financial payments, stock guarantees, and permissions without connection", () => {
    const paymentCheck = offline.validateWriteOperation("payment");
    expect(paymentCheck.allowed).toBe(false);
    expect(paymentCheck.error).toContain("No se pueden confirmar pagos sin conexión");

    const stockCheck = offline.validateWriteOperation("stock_guarantee");
    expect(stockCheck.allowed).toBe(false);
    expect(stockCheck.error).toContain("No se puede reservar ni garantizar inventario");

    const permCheck = offline.validateWriteOperation("permission_grant");
    expect(permCheck.allowed).toBe(false);
    expect(permCheck.error).toContain("La verificación de permisos vigentes requiere conexión");
  });

  it("stores minimal drafts with expiration TTL and purges expired drafts", () => {
    offline.saveMinimalDraft("draft_1", { note: "test" }, 10);
    expect(offline.getMinimalDraft("draft_1")).toBeDefined();

    return new Promise<void>((resolve) => {
      setTimeout(() => {
        expect(offline.getMinimalDraft("draft_1")).toBeNull();
        resolve();
      }, 20);
    });
  });
});

describe("FE-011: PWA Shell Caching and Privacy Purge Policy", () => {
  const pwa = new PWAStoragePolicy();

  it("excludes sensitive API routes and private downloads from service worker cache", () => {
    expect(pwa.isCacheableByServiceWorker("/api/v1/payments")).toBe(false);
    expect(pwa.isCacheableByServiceWorker("/api/v1/auth/login")).toBe(false);
    expect(pwa.isCacheableByServiceWorker("/api/v1/reports/download/rep-1")).toBe(false);
    expect(pwa.isCacheableByServiceWorker("/assets/index.js")).toBe(true);
    expect(pwa.isCacheableByServiceWorker("/index.html")).toBe(true);
  });

  it("purges private storage upon logout", () => {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("salesia_access_token", "secret_token");
      localStorage.setItem("salesia_private_cache", "private_data");
    }

    const outcome = pwa.purgePrivateStorageOnLogout();
    expect(outcome.privateCachesCleaned).toBe(true);
  });

  it("verifies contract compatibility across app upgrades", () => {
    expect(pwa.validateContractCompatibility("1.0.0", "1.2.0")).toBe(true);
    expect(pwa.validateContractCompatibility("1.0.0", "2.0.0")).toBe(false);
  });
});

describe("FE-012: Cross-Tab Coordination and Draft Isolation", () => {
  it("isolates drafts by tab ID so multiple tabs do not corrupt sales without version control", () => {
    const tabA = new TabSyncCoordinator("tab-alpha");
    const tabB = new TabSyncCoordinator("tab-beta");

    const draftKeyA = tabA.createTabIsolatedDraftKey("sale_draft");
    const draftKeyB = tabB.createTabIsolatedDraftKey("sale_draft");

    expect(draftKeyA).toBe("tab-alpha:sale_draft");
    expect(draftKeyB).toBe("tab-beta:sale_draft");
    expect(draftKeyA).not.toBe(draftKeyB);

    tabA.destroy();
    tabB.destroy();
  });
});

describe("FE-013: Chunk Load Error Recovery and Route Handlers", () => {
  const chunkMgr = new ChunkErrorManager();

  it("identifies dynamic import chunk errors and initiates recovery", () => {
    const chunkError = new Error("Failed to fetch dynamically imported module: /assets/ChunkX.js");
    expect(chunkMgr.isChunkLoadError(chunkError)).toBe(true);

    let reloadTriggered = false;
    const handled = chunkMgr.handleChunkError(chunkError, () => {
      reloadTriggered = true;
    });

    expect(handled.handled).toBe(true);
    expect(reloadTriggered).toBe(true);
  });

  it("provides user-friendly messaging for 403 and 404 route errors", () => {
    const error403 = chunkMgr.getRouteErrorDetails(403);
    expect(error403.title).toBe("Acceso denegado");
    expect(error403.code).toBe(403);

    const error404 = chunkMgr.getRouteErrorDetails(404);
    expect(error404.title).toBe("Recurso no encontrado");
    expect(error404.code).toBe(404);
  });
});

describe("FE-014: Component Rendering and Mount Idempotence", () => {
  it("prohibits irreversible mutations during component mount", () => {
    const auditor = new MountLifecycleAuditor();

    const mountSafe = auditor.recordMountEffect(false);
    expect(mountSafe).toBe(true);
    expect(auditor.getViolationsCount()).toBe(0);

    const mountUnsafe = auditor.recordMountEffect(true);
    expect(mountUnsafe).toBe(false);
    expect(auditor.getViolationsCount()).toBe(1);
  });

  it("executes registered cleanup callbacks on unmount", () => {
    const auditor = new MountLifecycleAuditor();
    let cleanedTimer = false;
    let cleanedListener = false;

    auditor.registerCleanup(() => {
      cleanedTimer = true;
    });
    auditor.registerCleanup(() => {
      cleanedListener = true;
    });

    const count = auditor.unmount();
    expect(count).toBe(2);
    expect(cleanedTimer).toBe(true);
    expect(cleanedListener).toBe(true);
  });
});

describe("FE-015: Browser Storage Security Audit", () => {
  it("verifies localStorage does not contain reusable credentials or cardholder data", () => {
    const auditor = new StorageSecurityAuditor();
    const result = auditor.audit();
    expect(result.isClean).toBe(true);
    expect(result.violations.length).toBe(0);
  });
});

describe("FE-016: Asynchronous Accessibility Announcer", () => {
  it("announces remote status politely without stealing active focus", () => {
    const announcer = new AsyncAccessibilityAnnouncer();
    const outcome = announcer.announce("Sincronización de existencias completada");

    expect(outcome.message).toBe("Sincronización de existencias completada");
    expect(outcome.politeRegionCount).toBe(1);
    expect(outcome.focusPreserved).toBe(true);
  });
});
