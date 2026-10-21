

export class OfflinePolicyManager {
  private simulatedOnline = true;
  private localDrafts = new Map<string, { data: unknown; expiresAt: number }>();

  setOnline(online: boolean): void {
    this.simulatedOnline = online;
  }

  isOnline(): boolean {
    if (typeof navigator !== "undefined" && typeof navigator.onLine === "boolean") {
      return this.simulatedOnline && navigator.onLine;
    }
    return this.simulatedOnline;
  }

  canRead(isAuthorized: boolean, hasOfflinePolicy: boolean): boolean {
    if (this.isOnline()) return isAuthorized;
    return isAuthorized && hasOfflinePolicy;
  }

  validateWriteOperation(operation: "payment" | "stock_guarantee" | "permission_grant" | "draft_save"): {
    allowed: boolean;
    error?: string;
  } {
    if (this.isOnline()) {
      return { allowed: true };
    }

    if (operation === "payment") {
      return {
        allowed: false,
        error: "Operación rechazada: No se pueden confirmar pagos sin conexión remota garantizada."
      };
    }

    if (operation === "stock_guarantee") {
      return {
        allowed: false,
        error: "Operación rechazada: No se puede reservar ni garantizar inventario en modo offline."
      };
    }

    if (operation === "permission_grant") {
      return {
        allowed: false,
        error: "Operación rechazada: La verificación de permisos vigentes requiere conexión autoritativa."
      };
    }

    return { allowed: true };
  }

  saveMinimalDraft(key: string, data: unknown, ttlMs = 1000 * 60 * 60 * 24): { saved: boolean; expiresAt: number } {
    const expiresAt = Date.now() + ttlMs;
    this.localDrafts.set(key, { data: JSON.parse(JSON.stringify(data)), expiresAt });
    return { saved: true, expiresAt };
  }

  getMinimalDraft<D>(key: string): D | null {
    const entry = this.localDrafts.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      this.localDrafts.delete(key);
      return null;
    }
    return JSON.parse(JSON.stringify(entry.data)) as D;
  }

  purgeExpiredDrafts(): number {
    const now = Date.now();
    let cleaned = 0;
    for (const [key, entry] of this.localDrafts.entries()) {
      if (now > entry.expiresAt) {
        this.localDrafts.delete(key);
        cleaned += 1;
      }
    }
    return cleaned;
  }
}
