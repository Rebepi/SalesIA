import { QueryClient } from "@tanstack/react-query";
import { apiClient } from "../client";

export function switchCompanyContext(queryClient: QueryClient, newCompanyId: string): void {
  queryClient.clear();
  apiClient.setCompanyId(newCompanyId);
}
