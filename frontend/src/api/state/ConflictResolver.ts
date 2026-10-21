

export type ConflictAction = "recargar" | "copiar" | "reaplicar";

export class ConflictResolver<T extends Record<string, unknown>> {
  private localData: T;
  private remoteData: T;

  constructor(localData: T, remoteData: T) {
    this.localData = JSON.parse(JSON.stringify(localData));
    this.remoteData = JSON.parse(JSON.stringify(remoteData));
  }

  getDifferences(): { field: string; localValue: unknown; remoteValue: unknown }[] {
    const diffs: { field: string; localValue: unknown; remoteValue: unknown }[] = [];
    const allKeys = Array.from(new Set([...Object.keys(this.localData), ...Object.keys(this.remoteData)]));

    for (const key of allKeys) {
      const localVal = this.localData[key];
      const remoteVal = this.remoteData[key];
      if (JSON.stringify(localVal) !== JSON.stringify(remoteVal)) {
        diffs.push({ field: key, localValue: localVal, remoteValue: remoteVal });
      }
    }
    return diffs;
  }

  resolve(
    action: ConflictAction,
    options?: { reapplyFields?: (keyof T)[] }
  ): {
    result: T;
    backedUpLocal: T;
    message: string;
  } {
    const backedUp = JSON.parse(JSON.stringify(this.localData)) as T;

    if (action === "recargar") {
      return {
        result: JSON.parse(JSON.stringify(this.remoteData)) as T,
        backedUpLocal: backedUp,
        message: "Versión remota cargada. Tu trabajo local se respaldó en memoria para evitar pérdida accidental."
      };
    }

    if (action === "copiar") {
      return {
        result: backedUp,
        backedUpLocal: backedUp,
        message: "Copia local conservada para pegar o comparar."
      };
    }

    const merged = JSON.parse(JSON.stringify(this.remoteData)) as T;
    const fieldsToApply = options?.reapplyFields || (Object.keys(this.localData) as (keyof T)[]);
    for (const field of fieldsToApply) {
      if (field in this.localData) {
        merged[field] = this.localData[field];
      }
    }

    return {
      result: merged,
      backedUpLocal: backedUp,
      message: "Campos locales reaplicados sobre la versión remota autorizada."
    };
  }
}
