import React from "react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

export const Breadcrumbs: React.FC<{ items: BreadcrumbItem[] }> = ({ items }) => {
  return (
    <nav aria-label="Ruta de navegación" className="flex items-center text-xs text-slate-400 mb-4">
      <ol className="flex items-center gap-2">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={index} className="flex items-center gap-2">
              {item.href && !isLast ? (
                <a href={item.href} className="hover:text-blue-400 transition-colors">
                  {item.label}
                </a>
              ) : (
                <span aria-current={isLast ? "page" : undefined} className="text-slate-200 font-semibold">
                  {item.label}
                </span>
              )}
              {!isLast && <span className="text-slate-600">/</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
