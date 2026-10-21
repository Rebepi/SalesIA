

export class DirtyNavigationGuard {
  canLeave(isDirty: boolean): { canLeave: boolean; promptRequired: boolean; message?: string } {
    if (!isDirty) {
      return { canLeave: true, promptRequired: false };
    }
    return {
      canLeave: false,
      promptRequired: true,
      message: "Tienes modificaciones sin guardar. Si sales ahora, se perderán los cambios."
    };
  }

  isolateCompanyCart<C extends { companyId: string; items: unknown[] }>(
    currentCart: C,
    targetCompanyId: string
  ): { safeCart: C; quarantined: boolean } {
    if (currentCart.companyId === targetCompanyId) {
      return { safeCart: currentCart, quarantined: false };
    }
    const emptyCart = {
      ...currentCart,
      companyId: targetCompanyId,
      items: []
    };
    return { safeCart: emptyCart, quarantined: true };
  }
}
