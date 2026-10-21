export function documentoClienteRules(type: string) {
  const numeric = type === "DNI" || type === "RUC";
  const min = type === "DNI" ? 8 : type === "RUC" ? 11 : type === "PASSPORT" || type === "PASAPORTE" ? 6 : 3;
  const max = type === "DNI" ? 8 : type === "RUC" ? 11 : type === "PASSPORT" || type === "PASAPORTE" ? 16 : 32;
  return { min, max, numeric, pattern: numeric ? `[0-9]{${max}}` : type === "PASSPORT" || type === "PASAPORTE" ? "[A-Za-z0-9]{6,16}" : ".{3,32}" };
}

export function limpiarDocumentoCliente(type: string, value: string) {
  const rules = documentoClienteRules(type);
  return (rules.numeric ? value.replace(/\D/g, "") : value).slice(0, rules.max);
}

export function errorDocumentoCliente(type: string, value: string) {
  if (type === "SIN_DOCUMENTO") return "";
  const rules = documentoClienteRules(type);
  return new RegExp(`^(?:${rules.pattern})$`).test(value.trim()) ? "" : rules.numeric ? `${type} debe contener exactamente ${rules.max} dígitos numéricos.` : `El documento debe contener entre ${rules.min} y ${rules.max} caracteres${type === "PASSPORT" ? " alfanuméricos" : ""}.`;
}

export function errorContactoCliente(phone: string, email: string, address = "") {
  if (phone.trim() && !/^\+?[0-9\s\-().]{6,32}$/.test(phone.trim())) return "El teléfono debe tener entre 6 y 32 caracteres y un formato válido, por ejemplo 999888777 o +51 999888777.";
  if (email.trim() && (email.trim().length > 255 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim()))) return "Ingresa un correo electrónico válido de hasta 255 caracteres.";
  if (address.trim() && (address.trim().length < 3 || address.trim().length > 255)) return "La dirección debe tener entre 3 y 255 caracteres.";
  return "";
}
