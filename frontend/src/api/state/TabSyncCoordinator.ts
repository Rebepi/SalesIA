

export class TabSyncCoordinator {
  private tabId: string;
  private channel: BroadcastChannel | null = null;
  private onMessageCallback?: (event: string, payload?: unknown) => void;

  constructor(tabId?: string, onMessage?: (event: string, payload?: unknown) => void) {
    this.tabId = tabId || (typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `tab-${Date.now()}`);
    this.onMessageCallback = onMessage;
    if (typeof BroadcastChannel !== "undefined") {
      try {
        this.channel = new BroadcastChannel("salesia_tab_sync");
        this.channel.onmessage = (evt) => {
          if (evt.data && evt.data.sourceTabId !== this.tabId && this.onMessageCallback) {
            this.onMessageCallback(evt.data.event, evt.data.payload);
          }
        };
      } catch {
        this.channel = null;
      }
    }
  }

  getTabId(): string {
    return this.tabId;
  }

  broadcast(event: "logout" | "company_switch" | "draft_touch", payload?: unknown): void {
    if (this.channel) {
      this.channel.postMessage({
        sourceTabId: this.tabId,
        event,
        payload
      });
    }
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("salesia:tab-sync", {
        detail: { sourceTabId: this.tabId, event, payload }
      }));
    }
  }

  createTabIsolatedDraftKey(baseKey: string): string {
    return `${this.tabId}:${baseKey}`;
  }

  destroy(): void {
    if (this.channel) {
      this.channel.close();
      this.channel = null;
    }
  }
}
