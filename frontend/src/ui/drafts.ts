import { useEffect, useRef, useState } from "react";

function scopedKey(key: string) {
  const company = sessionStorage.getItem("salesia_company_id") || "anonymous";
  let user = "anonymous";
  try {
    const payload = sessionStorage.getItem("salesia_access_token")?.split(".")[1];
    if (payload) user = String(JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/"))).sub || user);
  } catch { user = "anonymous"; }
  return `${company}:${user}:${key}`;
}

export function readDraft<T>(key: string, fallback: T): T {
  if (typeof sessionStorage === "undefined") return fallback;
  try {
    const raw = sessionStorage.getItem(scopedKey(key));
    return raw ? { ...fallback, ...JSON.parse(raw) } : fallback;
  } catch {
    return fallback;
  }
}

export function writeDraft<T>(key: string, value: T) {
  if (typeof sessionStorage === "undefined") return;
  sessionStorage.setItem(scopedKey(key), JSON.stringify(value));
}

export function clearDraft(key: string) {
  if (typeof sessionStorage === "undefined") return;
  sessionStorage.removeItem(scopedKey(key));
}

export function useUnsavedChanges(_isDirty: boolean) {
}

export function useSaveState(duration = 1800) {
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const timer = useRef<number>();
  function update(next: "saving" | "saved" | "error") {
    window.clearTimeout(timer.current);
    setState(next);
    if (next === "saved") timer.current = window.setTimeout(() => setState("idle"), duration);
  }
  useEffect(() => () => window.clearTimeout(timer.current), []);
  return { state, update };
}