import { apiClient, SalesIAClient } from "../client";

export class SessionExpiryManager {
  private client: SalesIAClient;
  private preservedDraft: unknown = null;
  private sessionExpired = false;

  constructor(client: SalesIAClient = apiClient) {
    this.client = client;
  }

  getClient(): SalesIAClient {
    return this.client;
  }

  handleUnauthorized(options: {
    currentDraft?: unknown;
    isSensitivePayment?: boolean;
  }): {
    sessionExpired: boolean;
    draftPreserved: boolean;
    autoResubmitPaymentAllowed: boolean;
  } {
    this.sessionExpired = true;
    if (options.currentDraft !== undefined) {
      this.preservedDraft = JSON.parse(JSON.stringify(options.currentDraft));
    }

    return {
      sessionExpired: true,
      draftPreserved: this.preservedDraft !== null,
      autoResubmitPaymentAllowed: false
    };
  }

  isSessionExpired(): boolean {
    return this.sessionExpired;
  }

  restorePreservedDraft<D>(): D | null {
    if (!this.preservedDraft) return null;
    return JSON.parse(JSON.stringify(this.preservedDraft)) as D;
  }

  clearPreservedDraft(): void {
    this.preservedDraft = null;
    this.sessionExpired = false;
  }
}
