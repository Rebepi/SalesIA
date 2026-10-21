

export type ConnectionState = "online" | "reconnecting" | "offline" | "stale_data";

export function canExecuteFinancialAction(connectionState: ConnectionState): boolean {
  return connectionState === "online";
}
