import React from "react";

export interface BadgeProps {
  variant?: "success" | "warning" | "danger" | "info" | "neutral";
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ variant = "neutral", children }) => {
  const variantStyles = {
    success: "bg-emerald-950/80 text-emerald-300 border-emerald-500/30",
    warning: "bg-amber-950/80 text-amber-300 border-amber-500/30",
    danger: "bg-rose-950/80 text-rose-300 border-rose-500/30",
    info: "bg-blue-950/80 text-blue-300 border-blue-500/30",
    neutral: "bg-slate-800 text-slate-300 border-slate-700"
  };
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variantStyles[variant]}`}
    >
      {children}
    </span>
  );
};
