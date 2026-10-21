import { Children, Fragment, cloneElement, isValidElement, useEffect, useRef, useState, type ReactElement, type ReactNode, type TableHTMLAttributes } from "react";
import { TablePagination } from "./TablePagination";
import { getDefaultPageSize, setDefaultPageSize as persistDefaultPageSize, UI_PREFERENCES_EVENT } from "../preferences";

function flattenSections(children: ReactNode): ReactNode[] {
  return Children.toArray(children).flatMap(child =>
    isValidElement<{ children?: ReactNode }>(child) && child.type === Fragment
      ? flattenSections(child.props.children)
      : [child]
  );
}

function flattenRows(children: ReactNode): ReactNode[] {
  return Children.toArray(children).flatMap(child =>
    isValidElement<{ children?: ReactNode }>(child) && child.type === Fragment
      ? flattenRows(child.props.children)
      : [child]
  );
}

export function PaginatedTable({ children, serverPagination, ...props }: TableHTMLAttributes<HTMLTableElement> & { serverPagination?: { page: number; pageSize: number; total: number; onPageChange: (page: number) => void; onPageSizeChange: (size: number) => void } }) {
  const [requestedPage, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(getDefaultPageSize);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sections = flattenSections(children);
  const head = sections.find(child => isValidElement(child) && child.type === "thead") as ReactElement<{ children?: ReactNode }> | undefined;
  const body = sections.find(child => isValidElement(child) && child.type === "tbody") as ReactElement<{ children?: ReactNode }> | undefined;
  const otherSections = sections.filter(child => child !== head && child !== body);
  const rows = flattenRows(body?.props.children);
  const dataRows = rows.filter(row => isValidElement<{ children?: ReactNode }>(row) && row.type === "tr" && !Children.toArray(row.props.children).some(cell => isValidElement<{ colSpan?: number }>(cell) && (cell.props.colSpan || 1) > 1));
  const total = dataRows.length;
  const signature = dataRows.map((row, index) => isValidElement(row) ? String(row.key ?? index) : String(index)).join("|");
  useEffect(() => { setPage(0); }, [signature]);
  useEffect(() => {
    const syncPreferences = () => {
      setPageSize(getDefaultPageSize());
      setPage(0);
    };
    window.addEventListener(UI_PREFERENCES_EVENT, syncPreferences);
    return () => window.removeEventListener(UI_PREFERENCES_EVENT, syncPreferences);
  }, []);
  const page = Math.min(requestedPage, Math.max(0, Math.ceil(total / pageSize) - 1));
  useEffect(() => { if (scrollRef.current) scrollRef.current.scrollTop = 0; }, [page, pageSize, signature]);
  const visible = new Set(dataRows.slice(page * pageSize, (page + 1) * pageSize));
  const dataRowSet = new Set(dataRows);
  let includeGroup = false;
  const pageRows = rows.filter(row => {
    if (dataRowSet.has(row)) includeGroup = visible.has(row);
    return includeGroup;
  });
  return <div className="paginated-table">
    <div className="paginated-table-surface">
      {head && (
        <div className="table-header-region">
          <table {...props}>{otherSections.filter(child => isValidElement(child) && child.type === "colgroup")}{head}</table>
        </div>
      )}
      <div ref={scrollRef} className="table-scroll-region" tabIndex={0} role="region" aria-label={props["aria-label"] || "Tabla con desplazamiento"}>
        <table {...props}>
          {otherSections}
          {body ? cloneElement(body, undefined, !serverPagination && total > pageSize ? pageRows : rows) : null}
        </table>
      </div>
    </div>
    {serverPagination ? <TablePagination {...serverPagination} /> : total > 10 && <TablePagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} onPageSizeChange={size => { setPageSize(size); persistDefaultPageSize(size); setPage(0); }} />}
  </div>;
}