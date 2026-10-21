import { describe, expect, it } from "vitest";
import { userProblem } from "../../api/problems";

describe("Mensajes de error accionables", () => {
  it("oculta detalles de SQL y conserva la referencia de diagnóstico", () => {
    const problem = userProblem({ detail: "sqlalchemy IntegrityError SELECT password FROM users" }, 500, "trace-123");
    expect(problem.detail).not.toContain("password");
    expect(problem.detail).not.toContain("sqlalchemy");
    expect(problem.trace_id).toBe("trace-123");
  });
  it("traduce validaciones estructuradas a campos comerciales", () => {
    const problem = userProblem({ detail: [{ loc: ["body", "customer_id"], msg: "UUID invalid" }, { loc: ["body", "amount"], msg: "not positive" }] }, 422);
    expect(problem.detail).toContain("cliente");
    expect(problem.detail).toContain("importe");
    expect(problem.detail).not.toContain("UUID");
  });
  it("conserva conflictos comerciales comprensibles", () => {
    expect(userProblem({ detail: "La cantidad supera el saldo pendiente." }, 409).detail).toBe("La cantidad supera el saldo pendiente.");
  });
});
