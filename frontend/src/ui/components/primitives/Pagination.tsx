import React from "react";
import { ChevronLeftIcon, ChevronRightIcon } from "../../icons/index";
import { Button } from "./Button";

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalRecords?: number;
  pageSize?: number;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  totalRecords,
  pageSize = 25
}) => {
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem =
    totalRecords !== undefined ? Math.min(totalRecords, currentPage * pageSize) : currentPage * pageSize;

  return (
    <nav
      aria-label="Paginación"
      className="flex items-center justify-between py-3 px-4 text-xs text-slate-400 w-full"
    >
      {totalRecords !== undefined ? (
        <span>
          {`Mostrando ${startItem}-${endItem} de ${totalRecords} registros`}
        </span>
      ) : (
        <span />
      )}
      <div className="flex items-center gap-2 ml-auto">
        <Button
          size="sm"
          variant="outline"
          aria-label="Página anterior"
          disabled={currentPage <= 1}
          leftIcon={<ChevronLeftIcon size={14} />}
          onClick={() => onPageChange(currentPage - 1)}
        >
          Anterior
        </Button>
        <span className="font-semibold text-slate-200 px-2" aria-current="page">
          {`Página ${currentPage} de ${Math.max(1, totalPages)}`}
        </span>
        <Button
          size="sm"
          variant="outline"
          aria-label="Página siguiente"
          disabled={currentPage >= totalPages}
          rightIcon={<ChevronRightIcon size={14} />}
          onClick={() => onPageChange(currentPage + 1)}
        >
          Siguiente
        </Button>
      </div>
    </nav>
  );
};
