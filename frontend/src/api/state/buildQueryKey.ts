

export interface QueryKeyOptions {
  companyId: string;
  branchId?: string;
  scope?: string;
  endpoint: string;
  filters?: Record<string, unknown>;
  currency?: string;
  timezone?: string;
  queryVersion?: number;
}

export function buildQueryKey(options: QueryKeyOptions): readonly unknown[] {
  const normCompany = options.companyId.trim();
  const normBranch = (options.branchId || "all").trim();
  const normScope = (options.scope || "global").trim();
  const normEndpoint = options.endpoint.trim();
  const normFilters = options.filters ? JSON.stringify(Object.entries(options.filters).sort(([a], [b]) => a.localeCompare(b))) : "{}";
  const normCurrency = (options.currency || "USD").toUpperCase();
  const normTimezone = options.timezone || "UTC";
  const normVersion = options.queryVersion ?? 1;

  return Object.freeze([
    normCompany,
    normBranch,
    normScope,
    normEndpoint,
    normFilters,
    normCurrency,
    normTimezone,
    normVersion
  ]);
}
