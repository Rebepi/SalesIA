

export class MountLifecycleAuditor {
  private unmountCleanups: (() => void)[] = [];
  private irreversibleMutationsOnMount = 0;

  recordMountEffect(hasIrreversibleMutation: boolean): boolean {
    if (hasIrreversibleMutation) {
      this.irreversibleMutationsOnMount += 1;
      return false;
    }
    return true;
  }

  registerCleanup(cleanupFn: () => void): void {
    this.unmountCleanups.push(cleanupFn);
  }

  unmount(): number {
    const total = this.unmountCleanups.length;
    for (const fn of this.unmountCleanups) {
      try {
        fn();
      } catch { }
    }
    this.unmountCleanups = [];
    return total;
  }

  getViolationsCount(): number {
    return this.irreversibleMutationsOnMount;
  }
}
