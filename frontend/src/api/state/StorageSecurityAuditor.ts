

export class StorageSecurityAuditor {
  audit(): { isClean: boolean; violations: string[] } {
    const violations: string[] = [];
    if (typeof localStorage === "undefined") {
      return { isClean: true, violations };
    }

    const forbiddenKeys = [
      "access_token",
      "refresh_token",
      "password",
      "secret",
      "pan",
      "card_number"
    ];

    for (let i = 0;i < localStorage.length;i++) {
      const key = localStorage.key(i) || "";
      const lowerKey = key.toLowerCase();
      for (const fk of forbiddenKeys) {
        if (lowerKey.includes(fk)) {
          violations.push(`Clave sensible prohibida encontrada en localStorage: '${key}'`);
        }
      }

      const val = localStorage.getItem(key) || "";
      if (val.length > 200000) {
        violations.push(`Dataset masivo prohibido en localStorage para clave '${key}' (${val.length} bytes)`);
      }

      if (/\b(?:\d{4}[ -]?){3}\d{4}\b/.test(val)) {
        violations.push(`Posible PAN o número de tarjeta detectado en valor de '${key}'`);
      }
    }

    return {
      isClean: violations.length === 0,
      violations
    };
  }
}
