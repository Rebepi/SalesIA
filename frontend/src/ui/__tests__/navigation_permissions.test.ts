import { describe, expect, it } from "vitest";
import { isModuleAuthorized, sections } from "../../app/OperationsWorkspace";

const rolePermissions: Record<string, string[]> = {
  company_admin: sections.map(section => section.permission).filter(permission => permission && permission !== "imports:write"),
  manager: ["customers:read", "customers:write", "products:read", "sales:read", "sales:write", "payments:read", "inventory:read", "analytics:dataset:read", "reports:read", "reports:export", "approvals:manage"],
  salesperson: ["customers:read", "customers:write", "products:read", "sales:read", "sales:write", "payments:read"],
  analyst: ["customers:read", "products:read", "sales:read", "analytics:dataset:read", "reports:read", "reports:export"],
  warehouse: ["products:read", "inventory:read", "inventory:write"],
  cashier: ["sales:read", "payments:read", "payments:write", "cash:register:manage", "reports:read"],
  purchaser: ["products:read", "products:cost:read", "purchases:read", "purchases:write", "inventory:read"],
  auditor: ["customers:read", "products:read", "sales:read", "payments:read", "inventory:read", "purchases:read", "audit:logs:read", "reports:read"],
  platform_admin: ["platform:manage", "operations:manage", "audit:logs:read", "users:manage", "organization:manage"],
};

describe("protección visual de módulos por rol", () => {
  for (const [role, permissions] of Object.entries(rolePermissions)) {
    it(`${role} solo recibe módulos públicos o autorizados`, () => {
      const visible = sections.filter(section => isModuleAuthorized(section.permission, permissions));
      expect(visible.length).toBeGreaterThan(0);
      expect(visible.every(section => !section.permission || isModuleAuthorized(section.permission, permissions))).toBe(true);
      for (const section of sections.filter(section => section.permission && !isModuleAuthorized(section.permission, permissions))) {
        expect(visible).not.toContain(section);
      }
    });
  }
});
