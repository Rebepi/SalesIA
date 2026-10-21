export function message(error: unknown) {

  if (error && typeof error === "object" && "detail" in error) {

    if (typeof error.detail === "string") return error.detail;

    if (error.detail && typeof error.detail === "object" && "title" in error.detail) return String(error.detail.title);

  }

  return "No se pudo completar la operación. Revisa la conexión y vuelve a intentar.";

}
