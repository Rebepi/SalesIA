

export class ChunkErrorManager {
  isChunkLoadError(error: unknown): boolean {
    if (!error) return false;
    const msg = error instanceof Error ? error.message : String(error);
    return (
      msg.includes("Failed to fetch dynamically imported module") ||
      msg.includes("Importing a module script failed") ||
      msg.includes("error loading dynamically imported module") ||
      msg.includes("Loading chunk")
    );
  }

  handleChunkError(error: unknown, reloadFn?: () => void): { handled: boolean; action: "reload" | "fallback" } {
    if (this.isChunkLoadError(error)) {
      if (reloadFn) {
        reloadFn();
        return { handled: true, action: "reload" };
      }
      if (typeof window !== "undefined" && typeof sessionStorage !== "undefined") {
        const lastReload = sessionStorage.getItem("salesia_chunk_reload_ts");
        const now = Date.now();
        if (!lastReload || now - Number(lastReload) > 15000) {
          sessionStorage.setItem("salesia_chunk_reload_ts", String(now));
          if (window.location) {
            window.location.reload();
          }
          return { handled: true, action: "reload" };
        }
      }
      return { handled: true, action: "fallback" };
    }
    return { handled: false, action: "fallback" };
  }

  getRouteErrorDetails(status: number): { title: string; message: string; code: number } {
    if (status === 403) {
      return {
        title: "Acceso denegado",
        message: "No cuentas con permisos suficientes para acceder a este recurso.",
        code: 403
      };
    }
    if (status === 404) {
      return {
        title: "Recurso no encontrado",
        message: "La ruta solicitada no existe o fue trasladada.",
        code: 404
      };
    }
    return {
      title: "Error de aplicación",
      message: "Ocurrió un error inesperado al procesar la ruta.",
      code: status
    };
  }
}
