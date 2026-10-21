

export type AutoSaveStatus = "guardando" | "guardado" | "sin_sincronizar";

export class AutoSaveQueue<T> {
  private currentDraft: T;
  private currentVersion = 1;
  private lastSavedVersion = 0;
  private status: AutoSaveStatus = "sin_sincronizar";
  private onSave: (version: number, draft: T) => Promise<boolean>;

  constructor(initialDraft: T, onSave: (version: number, draft: T) => Promise<boolean>) {
    this.currentDraft = JSON.parse(JSON.stringify(initialDraft));
    this.onSave = onSave;
  }

  getStatus(): AutoSaveStatus {
    return this.status;
  }

  getCurrentVersion(): number {
    return this.currentVersion;
  }

  getLastSavedVersion(): number {
    return this.lastSavedVersion;
  }

  getDraft(): T {
    return this.currentDraft;
  }

  updateDraft(updater: (prev: T) => T): void {
    this.currentDraft = updater(this.currentDraft);
    this.currentVersion += 1;
    this.status = "sin_sincronizar";
  }

  async triggerSave(): Promise<boolean> {
    const versionToSave = this.currentVersion;
    const snapshot = JSON.parse(JSON.stringify(this.currentDraft)) as T;
    this.status = "guardando";

    try {
      const ok = await this.onSave(versionToSave, snapshot);
      this.handleSaveResponse(versionToSave, ok);
      return ok;
    } catch {
      this.handleSaveResponse(versionToSave, false);
      return false;
    }
  }

  handleSaveResponse(responseVersion: number, success: boolean): void {
    if (!success) {
      this.status = "sin_sincronizar";
      return;
    }

    if (responseVersion < this.lastSavedVersion) {
      return;
    }

    this.lastSavedVersion = responseVersion;
    if (this.currentVersion === this.lastSavedVersion) {
      this.status = "guardado";
    } else {
      this.status = "sin_sincronizar";
    }
  }
}
