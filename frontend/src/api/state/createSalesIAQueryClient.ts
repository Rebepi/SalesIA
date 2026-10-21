import { QueryClient } from "@tanstack/react-query";

export function createSalesIAQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
        gcTime: 1000 * 60 * 30,
        retry: (failureCount, error: unknown) => {
          if (failureCount >= 2) return false;
          if (error && typeof error === "object" && "status" in error) {
            const status = (error as { status: number }).status;
            if ([400, 401, 403, 404, 409, 422].includes(status)) return false;
          }
          return true;
        },
        refetchOnWindowFocus: false
      }
    }
  });
}
