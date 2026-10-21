import { userProblem } from "./problems";

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  code?: string;
  detail?: string;
  instance?: string;
  trace_id?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  mfa_code?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  email: string;
  company_id: string;
  role: string;
  permissions: string[];
}

export interface UserProfile {
  user_id: string;
  email: string;
  company_id?: string;
  role: string;
  permissions?: string[];
  full_name?: string;
  phone?: string;
  mfa_enabled?: boolean;
  ui_theme?: string;
  ui_density?: string;
  reduced_motion?: boolean;
  font_scale?: string;
  contrast_mode?: string;
  default_page_size?: number;
  sidebar_mode?: string;
  accessible_tables?: boolean;
  toast_position?: string;
}

export interface DashboardSummaryResponse {
  total_revenue: string;
  orders_count: number;
  active_customers: number;
  active_products: number;
  average_ticket: string;
  currency: string;
}

export interface MeanRequest {
  values: string[];
}

export interface MeanResponse {
  count: number;
  mean: string;
}

export interface MedianRequest {
  values: string[];
}

export interface MedianResponse {
  count: number;
  median: string;
}

export interface CompareRequest {
  label_a: string;
  values_a: string[];
  label_b: string;
  values_b: string[];
}

export interface CompareResponse {
  series_a: { label: string; count: number; mean: string; median: string };
  series_b: { label: string; count: number; mean: string; median: string };
  differences: { delta_mean: string; delta_median: string };
}

export interface SearchResultItem {
  type: "customer" | "product" | "sale" | "order" | "task" | "quotation" | "supplier" | "purchase_order" | "delivery" | "return" | "credit_note" | "payment" | "payable" | "expense" | "lot" | "serial" | "branch" | "warehouse" | "warranty" | "supplier_claim" | "delivery_route" | "delivery_vehicle" | "delivery_window";
  id: string;
  title: string;
  subtitle: string;
}

export interface SearchResponse {
  query: string;
  count: number;
  results: SearchResultItem[];
}

export class SalesIAClient {
  private baseUrl: string;
  private refreshInFlight: Promise<boolean> | null = null;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private companyId: string | null = null;

  private async fetchSafe<T>(url: string, options: RequestInit, consume: (response: Response) => Promise<T>, timeoutMs = 30000): Promise<T> {
    const controller = new AbortController();
    let timedOut = false;
    const cancel = () => controller.abort();
    if (options.signal?.aborted) cancel();
    else options.signal?.addEventListener("abort", cancel, { once: true });
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
    try { return await consume(await fetch(url, { ...options, signal: controller.signal })); }
    catch (failure: unknown) {
      if (options.signal?.aborted) throw failure;
      if (!timedOut && (failure as { name?: string }).name === "AbortError") throw failure;
      const write = !["GET", "HEAD"].includes((options.method || "GET").toUpperCase());
      if (timedOut) throw { type: "about:blank", title: "El servidor no respondió a tiempo", status: 0, code: write ? "RESULT_UNKNOWN" : "REQUEST_TIMEOUT", detail: write ? "Se agotó el tiempo de espera y no se pudo confirmar el resultado. Consulta el estado del documento antes de volver a ejecutar la operación." : "El servidor no respondió a tiempo. Puede estar reiniciándose o temporalmente ocupado. Espera unos segundos y vuelve a consultar." } satisfies ProblemDetails;
      throw { type: "about:blank", title: "Conexión interrumpida", status: 0, code: write ? "RESULT_UNKNOWN" : "OFFLINE", detail: write ? "La conexión se interrumpió y no se pudo confirmar el resultado. Consulta el estado del documento antes de volver a ejecutar la operación." : "No se pudo conectar con el servidor. Revisa tu conexión y utiliza Reintentar." } satisfies ProblemDetails;
    } finally {
      clearTimeout(timer);
      options.signal?.removeEventListener("abort", cancel);
    }
  }

  constructor(baseUrl?: string) {
    const metaEnv = typeof import.meta !== "undefined" ? (import.meta as unknown as { env?: Record<string, string> }).env : undefined;
    const defaultUrl = metaEnv?.VITE_API_BASE_URL || metaEnv?.VITE_API_URL || "";
    this.baseUrl = (baseUrl !== undefined ? baseUrl : defaultUrl).replace(/\/$/, "");
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem("salesia_access_token");
      localStorage.removeItem("salesia_refresh_token");
      localStorage.removeItem("salesia_company_id");
    }
    if (typeof sessionStorage !== "undefined") {
      this.accessToken = sessionStorage.getItem("salesia_access_token");
      this.refreshToken = sessionStorage.getItem("salesia_refresh_token");
      this.companyId = sessionStorage.getItem("salesia_company_id");
    }
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/$/, "");
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  getCompanyId(): string | null {
    return this.companyId;
  }

  setCompanyId(companyId: string | null): void {
    this.companyId = companyId;
    if (typeof sessionStorage !== "undefined") {
      if (companyId) {
        sessionStorage.setItem("salesia_company_id", companyId);
      } else {
        sessionStorage.removeItem("salesia_company_id");
      }
    }
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("salesia:company-changed", { detail: { companyId } }));
    }
  }

  setTokens(accessToken: string, refreshToken: string, companyId?: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    if (typeof sessionStorage !== "undefined") {
      sessionStorage.setItem("salesia_access_token", accessToken);
      sessionStorage.setItem("salesia_refresh_token", refreshToken);
      if (companyId) {
        this.companyId = companyId;
        sessionStorage.setItem("salesia_company_id", companyId);
      }
    }
  }

  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.companyId = null;
    if (typeof sessionStorage !== "undefined") {
      sessionStorage.removeItem("salesia_company_id");
      sessionStorage.removeItem("salesia_access_token");
      sessionStorage.removeItem("salesia_refresh_token");
    }
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("salesia:signed-out"));
    }
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>)
    };

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    if (this.companyId) {
      headers["X-Company-Id"] = this.companyId;
    }

    const send = () => this.fetchSafe(url, { ...options, headers }, async response => ({ response, body: response.status === 204 ? "" : await response.text() }));
    let received = await send();

    if (received.response.status === 401 && this.refreshToken && !path.startsWith("/api/v1/auth/login")) {
      const refreshed = await this.rotateRefreshToken();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${this.accessToken}`;
        received = await send();
      }
    }

    const { response, body } = received;
    if (!response.ok) {
      let errorData: ProblemDetails = { type: "about:blank", title: "Error de solicitud", status: response.status, detail: body };
      try {
        errorData = { ...errorData, ...JSON.parse(body) };
      } catch {
        errorData.detail = body || response.statusText;
      }
      throw userProblem(errorData, response.status, response.headers.get("X-Correlation-ID"));
    }

    if (response.status === 204) return undefined as T;
    return JSON.parse(body) as T;
  }

  private rotateRefreshToken(): Promise<boolean> {
    if (!this.refreshInFlight) {
      this.refreshInFlight = this.performRefresh().finally(() => { this.refreshInFlight = null; });
    }
    return this.refreshInFlight;
  }

  private async performRefresh(): Promise<boolean> {
    const { res, body } = await this.fetchSafe(`${this.baseUrl}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: this.refreshToken })
    }, async res => ({ res, body: await res.text() }));
    if (res.ok) {
      const data = JSON.parse(body) as LoginResponse;
      this.setTokens(data.access_token, data.refresh_token, data.company_id);
      return true;
    }
    if (res.status === 401 || res.status === 403) {
      this.clearTokens();
      return false;
    }
    throw userProblem({}, res.status, res.headers.get("X-Correlation-ID"));
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const res = await this.request<LoginResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials)
    });
    this.setTokens(res.access_token, res.refresh_token, res.company_id);
    return res;
  }

  async logout(): Promise<void> {
    try {
      await this.request("/api/v1/auth/logout", {
        method: "POST"
      });
    } catch {
    } finally {
      this.clearTokens();
    }
  }

  async getMe(): Promise<UserProfile> {
    return this.request<UserProfile>("/api/v1/auth/profile");
  }

  async getHealth(): Promise<{ status: string; app: string; version: string }> {
    return this.request("/api/v1/health");
  }

  async getDashboardSummary(): Promise<DashboardSummaryResponse> {
    return this.request<DashboardSummaryResponse>("/api/v1/dashboard/summary");
  }

  async computeMean(values: string[]): Promise<MeanResponse> {
    return this.request<MeanResponse>("/api/v1/statistics/mean", {
      method: "POST",
      body: JSON.stringify({ values })
    });
  }

  async computeMedian(values: string[]): Promise<MedianResponse> {
    return this.request<MedianResponse>("/api/v1/statistics/median", {
      method: "POST",
      body: JSON.stringify({ values })
    });
  }

  async compareSeries(payload: CompareRequest): Promise<CompareResponse> {
    return this.request<CompareResponse>("/api/v1/statistics/compare", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  async search(query: string): Promise<SearchResponse> {
    return this.request<SearchResponse>(`/api/v1/search?q=${encodeURIComponent(query)}`);
  }

  async listCustomers(): Promise<{ items: any[]; total_count: number }> {
    return this.request("/api/v1/customers");
  }

  async listProducts(): Promise<{ items: any[]; total_count: number }> {
    return this.request("/api/v1/products");
  }

  async listInventory(): Promise<{ items: any[]; count: number }> {
    return this.request("/api/v1/inventory");
  }

  async getJob(jobId: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(`/api/v1/jobs/${jobId}`);
  }

  async cancelJob(jobId: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(`/api/v1/jobs/${jobId}/cancel`, {
      method: "POST"
    });
  }

  async downloadBlob(path: string): Promise<{ blob: Blob; filename: string }> {
    const url = `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
    const headers: Record<string, string> = {};
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    if (this.companyId) {
      headers["X-Company-Id"] = this.companyId;
    }
    const { response, blob, body } = await this.fetchSafe(url, { headers }, async response => ({ response, blob: response.ok ? await response.blob() : null, body: response.ok ? "" : await response.text() }), 120000);
    if (!response.ok) {
      let errorData: ProblemDetails = { type: "about:blank", title: "Error de descarga", status: response.status, detail: body };
      try {
        errorData = { ...errorData, ...JSON.parse(body) };
      } catch {
        errorData.detail = body || response.statusText;
      }
      throw userProblem(errorData, response.status, response.headers.get("X-Correlation-ID"));
    }
    const disposition = response.headers.get("Content-Disposition") || "";
    let filename = "reporte";
    const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
    if (filenameMatch && filenameMatch[1]) {
      filename = filenameMatch[1];
    }
    if (blob === null) throw new Error("No se recibió el archivo solicitado.");
    return { blob, filename };
  }
}

export const apiClient = new SalesIAClient();
