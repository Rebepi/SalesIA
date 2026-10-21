

export class SequenceGuard {
  private latestSeq = 0;
  private currentAbortController: AbortController | null = null;
  private latestQuery = "";

  createSequence(queryText: string): { seq: number; signal: AbortSignal; isLatest: () => boolean } {
    if (this.currentAbortController) {
      this.currentAbortController.abort();
    }
    this.latestSeq += 1;
    const assignedSeq = this.latestSeq;
    this.latestQuery = queryText;
    const controller = new AbortController();
    this.currentAbortController = controller;

    return {
      seq: assignedSeq,
      signal: controller.signal,
      isLatest: () => assignedSeq === this.latestSeq && !controller.signal.aborted
    };
  }

  abortActive(): void {
    if (this.currentAbortController) {
      this.currentAbortController.abort();
      this.currentAbortController = null;
    }
  }

  getLatestQuery(): string {
    return this.latestQuery;
  }

  getLatestSeq(): number {
    return this.latestSeq;
  }
}
