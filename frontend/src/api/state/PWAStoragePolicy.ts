

export class PWAStoragePolicy {
  private static readonly EXCLUDED_ROUTES = [
    "/api/v1/payments",
    "/api/v1/auth",
    "/api/v1/reports/download",
    "/api/v1/customers/export"
  ];

  isCacheableByServiceWorker(url: string): boolean {
    for (const route of PWAStoragePolicy.EXCLUDED_ROUTES) {
      if (url.includes(route)) return false;
    }
    return true;
  }

  purgePrivateStorageOnLogout(): { clearedKeys: string[]; privateCachesCleaned: boolean } {
    const cleared: string[] = [];
    if (typeof localStorage !== "undefined") {
      const keys = Object.keys(localStorage);
      for (const k of keys) {
        if (k.startsWith("salesia_") || k.includes("private") || k.includes("token")) {
          localStorage.removeItem(k);
          cleared.push(k);
        }
      }
    }
    if (typeof sessionStorage !== "undefined") {
      sessionStorage.clear();
      cleared.push("sessionStorage_all");
    }
    return { clearedKeys: cleared, privateCachesCleaned: true };
  }

  validateContractCompatibility(installedVersion: string, requiredVersion: string): boolean {
    const [majA] = installedVersion.split(".");
    const [majB] = requiredVersion.split(".");
    return majA === majB;
  }
}
