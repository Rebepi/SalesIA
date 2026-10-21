import React from "react";

export interface FormErrorSummaryProps {
  errors: { fieldId: string; message: string }[];
}

export const FormErrorSummary: React.FC<FormErrorSummaryProps> = ({ errors }) => {
  if (errors.length === 0) return null;

  return (
    <div
      role="alert"
      className="rounded-xl border border-rose-500/50 bg-rose-950/40 p-4 text-left mb-4"
    >
      <h4 className="text-sm font-bold text-rose-300">
        Se encontraron {errors.length} errores en el formulario
      </h4>
      <ul className="mt-2 space-y-1 list-disc list-inside text-xs text-rose-200">
        {errors.map((err) => (
          <li key={err.fieldId}>
            <a
              href={`#${err.fieldId}`}
              className="underline hover:text-white transition-colors"
            >
              {err.message}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};
