export interface IntegrationConnector {
  id: string;
  provider_name: string;
  category: string;
  status: "connected" | "error" | "unconfigured";
  last_sync: string | null;
  masked_key: string;
  mode: "test" | "live";
  error_message?: string | null;
  latency_ms?: number;
}

export interface IntegrationsWorkspaceTabProps {
  canWrite?: boolean;
}
