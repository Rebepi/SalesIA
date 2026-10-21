import { FORBIDDEN_OPTIMISTIC } from "./FORBIDDEN_OPTIMISTIC";
import { OPTIMISTIC_ALLOWLIST } from "./OPTIMISTIC_ALLOWLIST";

export class OptimisticMutationManager {
  isOptimisticAllowed(operationType: string): boolean {
    const op = operationType.toLowerCase();
    if (FORBIDDEN_OPTIMISTIC.has(op)) return false;
    return OPTIMISTIC_ALLOWLIST.has(op);
  }

  async execute<TState, TVariables>(params: {
    operation: string;
    getCurrentState: () => TState;
    applyOptimistic: (state: TState, variables: TVariables) => TState;
    mutateFn: (variables: TVariables) => Promise<TState>;
    onRollback: (previousSnapshot: TState, error: Error) => void;
    variables: TVariables;
  }): Promise<{ success: boolean; state: TState; error?: string }> {
    if (!this.isOptimisticAllowed(params.operation)) {
      throw new Error(`Actualización optimista denegada para '${params.operation}'. Prohibido en cobros y existencias finales.`);
    }

    const snapshot = JSON.parse(JSON.stringify(params.getCurrentState())) as TState;
    params.applyOptimistic(snapshot, params.variables);

    try {
      const serverResult = await params.mutateFn(params.variables);
      return { success: true, state: serverResult };
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err));
      params.onRollback(snapshot, errorObj);
      return {
        success: false,
        state: snapshot,
        error: "La actualización remota falló. Se restableció el estado previo sin confirmar cambios financieros."
      };
    }
  }
}
