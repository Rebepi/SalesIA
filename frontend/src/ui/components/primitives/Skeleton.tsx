import React from "react";

export const Skeleton: React.FC<{ className?: string }> = ({ className = "h-4 w-full" }) => (
  <div role="status" className={`animate-pulse bg-slate-800 rounded-lg ${className}`}>
    <span className="sr-only">Cargando contenido...</span>
  </div>
);
