export const TOAST_POSITIONS = [
  { value: "bottom-right", label: "Abajo a la derecha" },
  { value: "top-right", label: "Arriba a la derecha" },
  { value: "top-center", label: "Arriba al centro" }
] as const;

export type ToastPosition = typeof TOAST_POSITIONS[number]["value"];
export const TOAST_POSITION_EVENT = "salesia-toast-position-changed";
const STORAGE_KEY = "salesia-toast-position";

export function getToastPosition(): ToastPosition {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return TOAST_POSITIONS.find(position => position.value === stored)?.value ?? "bottom-right";
  } catch {
    return "bottom-right";
  }
}

export function setToastPosition(position: ToastPosition): void {
  try {
    localStorage.setItem(STORAGE_KEY, position);
  } catch {}
  window.dispatchEvent(new CustomEvent(TOAST_POSITION_EVENT, { detail: position }));
}
