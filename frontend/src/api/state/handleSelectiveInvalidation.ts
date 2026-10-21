import { QueryClient } from "@tanstack/react-query";

export interface InvalidationResult {
  invalidatedPatterns: string[];
  staleProjection: boolean;
  authoritativeUpdated: boolean;
}

export function handleSelectiveInvalidation(
  queryClient: QueryClient,
  mutationType: "confirm_sale" | "inventory_adjustment" | "payment" | "preferences" | "product_update",
  context?: { companyId?: string; branchId?: string; entityId?: string }
): InvalidationResult {
  const invalidated: string[] = [];
  let staleProjection = false;
  let authoritativeUpdated = false;

  if (context?.entityId) {
    queryClient.invalidateQueries({ queryKey: [mutationType, context.entityId] });
  }

  if (mutationType === "confirm_sale") {
    queryClient.invalidateQueries({ queryKey: ["inventory"] });
    queryClient.invalidateQueries({ queryKey: ["sales"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    invalidated.push("inventory", "sales", "dashboard");
    staleProjection = true;
    authoritativeUpdated = true;
  } else if (mutationType === "inventory_adjustment") {
    queryClient.invalidateQueries({ queryKey: ["inventory"] });
    invalidated.push("inventory");
    staleProjection = true;
    authoritativeUpdated = true;
  } else if (mutationType === "payment") {
    queryClient.invalidateQueries({ queryKey: ["sales"] });
    queryClient.invalidateQueries({ queryKey: ["payments"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    invalidated.push("sales", "payments", "dashboard");
    staleProjection = true;
    authoritativeUpdated = true;
  } else if (mutationType === "preferences") {
    queryClient.invalidateQueries({ queryKey: ["user_preferences"] });
    invalidated.push("user_preferences");
  } else if (mutationType === "product_update") {
    queryClient.invalidateQueries({ queryKey: ["products"] });
    invalidated.push("products");
    authoritativeUpdated = true;
  }

  return {
    invalidatedPatterns: invalidated,
    staleProjection,
    authoritativeUpdated
  };
}
