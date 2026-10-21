export const ENTITY_CHANGED_EVENT = "salesia:entity-changed";

export type EntityType = "customer" | "product" | "supplier" | "warehouse" | "location" | "sales_rep" | "carrier" | "contact" | "payment" | "sale";

export interface EntityChangedDetail<T = unknown> {
  type: EntityType;
  entity: T;
}

export function notifyEntityChanged<T>(type: EntityType, entity: T) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<EntityChangedDetail<T>>(ENTITY_CHANGED_EVENT, { detail: { type, entity } }));
}

export function subscribeToEntityChanges<T>(type: EntityType, listener: (entity: T) => void) {
  if (typeof window === "undefined") return () => undefined;
  const handler = (event: Event) => {
    const detail = (event as CustomEvent<EntityChangedDetail<T>>).detail;
    if (detail?.type === type) listener(detail.entity);
  };
  window.addEventListener(ENTITY_CHANGED_EVENT, handler);
  return () => window.removeEventListener(ENTITY_CHANGED_EVENT, handler);
}
