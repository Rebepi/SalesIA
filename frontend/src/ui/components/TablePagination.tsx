import { ChevronLeft, ChevronRight } from "lucide-react";
import { CustomSelect } from "./CustomSelect";

export function TablePagination({ page, pageSize, total, loading = false, onPageChange, onPageSizeChange }: { page: number; pageSize: number; total: number; loading?: boolean; onPageChange: (page: number) => void; onPageSizeChange: (size: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const visiblePages = Array.from(new Set([0, page - 1, page, page + 1, pages - 1])).filter(index => index >= 0 && index < pages).sort((a, b) => a - b);
  return <nav aria-label="Paginación de la tabla" className="table-pagination">
    <span className="pagination-range" aria-live="polite">{total === 0 ? 0 : page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} de {total.toLocaleString("es-PE")} registros</span>
    <div className="table-pagination-controls">
      <span className="pagination-size-label">Filas por página</span>
      <CustomSelect aria-label="Filas por página" value={pageSize} disabled={loading} onChange={event => onPageSizeChange(Number(event.target.value))}>{[10, 25, 50, 100].map(size => <option key={size} value={size}>{size}</option>)}</CustomSelect>
      <button type="button" aria-label="Página anterior" disabled={loading || page <= 0} onClick={() => onPageChange(page - 1)}><ChevronLeft size={16}/></button>
      <span className="pagination-page-summary">Página {page + 1} de {pages}</span>
      <div className="pagination-pages">{visiblePages.map((index, position) => <span key={index} className="pagination-page-item">
        {position > 0 && index - visiblePages[position - 1] > 1 && <span className="pagination-ellipsis">…</span>}
        <button type="button" aria-label={`Ir a página ${index + 1}`} aria-current={index === page ? "page" : undefined} disabled={loading} onClick={() => onPageChange(index)}>{index + 1}</button>
      </span>)}</div>
      <button type="button" aria-label="Página siguiente" disabled={loading || page >= pages - 1} onClick={() => onPageChange(page + 1)}><ChevronRight size={16}/></button>
    </div>
  </nav>;
}
