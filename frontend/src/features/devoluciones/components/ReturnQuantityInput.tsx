import { useEffect, useRef } from "react";

interface Props {
  value: number;
  max: number;
  allowFractions: boolean;
  label: string;
  onChange: (quantity: number) => void;
}

export function ReturnQuantityInput(props: Props) {
  const input = useRef<HTMLInputElement>(null);
  const latest = useRef(props);
  latest.current = props;

  function adjust(direction: number) {
    const current = latest.current;
    const next = Math.max(0, Math.min(current.max, Math.round((current.value + direction) * 1000000) / 1000000));
    latest.current = { ...current, value: next };
    current.onChange(next);
  }

  useEffect(() => {
    const element = input.current;
    if (!element) return;
    function wheel(event: WheelEvent) {
      if (event.ctrlKey || event.deltaY === 0 || element?.matches(":disabled") || element?.readOnly) return;
      event.preventDefault();
      event.stopPropagation();
      adjust(event.deltaY < 0 ? 1 : -1);
    }
    element.addEventListener("wheel", wheel, { passive: false });
    return () => element.removeEventListener("wheel", wheel);
  }, []);

  return <input ref={input} type="number" step={props.allowFractions ? "any" : 1} aria-label={props.label} min="0" max={props.max} value={props.value}
    onKeyDown={event => {
      if (event.key === "ArrowUp" || event.key === "ArrowDown") {
        event.preventDefault();
        adjust(event.key === "ArrowUp" ? 1 : -1);
      }
    }}
    onChange={event => props.onChange(Number(event.target.value))}
    className="w-20 rounded-lg border border-slate-300 px-2 py-1 text-center font-medium outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" />;
}
