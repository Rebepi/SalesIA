import { describe, expect, it } from "vitest";
import { getToastDuration } from "../toast/SileoToasts";
import type { ToastItem } from "../toast/ToastContext";

const notification = (patch: Partial<ToastItem> = {}): ToastItem => ({ id: "sample", title: "Cambios guardados", type: "success", ...patch });

describe("Sileo notification lifecycle", () => {
  it("keeps loading and persistent errors visible until explicitly dismissed", () => {
    expect(getToastDuration(notification({ type: "loading", duration: 50 }))).toBeNull();
    expect(getToastDuration(notification({ type: "error" }))).toBeNull();
    expect(getToastDuration(notification({ persistent: true }))).toBeNull();
  });

  it("supports timed errors when callers explicitly opt out of persistence", () => {
    expect(getToastDuration(notification({ type: "error", persistent: false, duration: 2500 }))).toBe(2500);
  });

  it("uses the original contextual durations for success, warning and information", () => {
    expect(getToastDuration(notification())).toBe(4500);
    expect(getToastDuration(notification({ type: "warning" }))).toBe(6000);
    expect(getToastDuration(notification({ type: "info" }))).toBe(6500);
  });

  it("transitions from a persistent operation to a timed success", () => {
    const pending = notification({ type: "loading", persistent: true });
    expect(getToastDuration(pending)).toBeNull();
    expect(getToastDuration({ ...pending, type: "success", persistent: false })).toBe(4500);
  });

  it("treats zero and negative durations as notifications without automatic dismissal", () => {
    expect(getToastDuration(notification({ duration: 0 }))).toBeNull();
    expect(getToastDuration(notification({ duration: -1 }))).toBeNull();
  });
});
