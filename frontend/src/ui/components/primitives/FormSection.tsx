import React from "react";

export interface FormSectionProps {
  title: string;
  description?: string;
  required?: boolean;
  children: React.ReactNode;
}

export const FormSection: React.FC<FormSectionProps> = ({
  title,
  description,
  required = false,
  children
}) => {
  return (
    <section className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-5 text-left mb-5">
      <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-white">{title}</h4>
          {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
        </div>
        <span
          className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${required
            ? "bg-blue-950 text-blue-300 border-blue-800"
            : "bg-slate-800 text-slate-400 border-slate-700"
            }`}
        >
          {required ? "Requerido" : "Opcional"}
        </span>
      </div>
      <div className="space-y-4 pt-1">{children}</div>
    </section>
  );
};
