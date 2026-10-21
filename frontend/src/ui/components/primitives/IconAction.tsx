import { forwardRef, type ButtonHTMLAttributes } from "react";
import { Tooltip } from "./Tooltip";

type IconActionProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "title"> & {
  label: string;
  tone?: "neutral" | "primary" | "danger";
};

export const IconAction = forwardRef<HTMLButtonElement, IconActionProps>(function IconAction({ label, tone = "neutral", className = "", children, ...props }, ref) {
  const color = tone === "danger"
    ? "text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
    : tone === "primary"
      ? "text-teal-700 hover:bg-teal-50 dark:text-teal-300 dark:hover:bg-teal-950/40"
      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800";
  return <Tooltip text={label} portal>
    <button type="button" aria-label={label} {...props} ref={ref} className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-transparent transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 [&>svg]:h-4 [&>svg]:w-4 ${color} ${className}`}>
      {children}
    </button>
  </Tooltip>;
});
