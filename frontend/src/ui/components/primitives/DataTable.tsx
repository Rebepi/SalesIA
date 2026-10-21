import React, { useState } from "react";
import { RefreshSyncIcon } from "../../icons/index";
import type { TableColumn } from "./TableColumn";
import { Button } from "./Button";
import { Checkbox } from "./Checkbox";

export interface DataTableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  isLoading?: boolean;
  emptyMessage?: string;
  stickyHeader?: boolean;
  selectedIds?: string[];
  onSelectionChange?: (selectedIds: string[]) => void;
  filteredTotalCount?: number;
  visibleSubtotalAmount?: string;
  hiddenSelectedCount?: number;
  onClearHiddenSelection?: () => void;
}

export function DataTable<T extends { id?: string | number }>({
  columns,
  data,
  isLoading = false,
  emptyMessage = "No se encontraron registros.",
  stickyHeader = false,
  selectedIds = [],
  onSelectionChange,
  filteredTotalCount,
  visibleSubtotalAmount,
  hiddenSelectedCount = 0,
  onClearHiddenSelection
}: DataTableProps<T>) {
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

  const toggleExpand = (rowKey: string) => {
    setExpandedRows((prev) => ({ ...prev, [rowKey]: !prev[rowKey] }));
  };

  const handleToggleRow = (rowId: string) => {
    if (!onSelectionChange) return;
    if (selectedIds.includes(rowId)) {
      onSelectionChange(selectedIds.filter((id) => id !== rowId));
    } else {
      onSelectionChange([...selectedIds, rowId]);
    }
  };

  const handleToggleAllVisible = () => {
    if (!onSelectionChange) return;
    const visibleIds = data.map((r, i) => String(r.id ?? i));
    const allSelected = visibleIds.every((id) => selectedIds.includes(id));
    if (allSelected) {
      onSelectionChange(selectedIds.filter((id) => !visibleIds.includes(id)));
    } else {
      const merged = Array.from(new Set([...selectedIds, ...visibleIds]));
      onSelectionChange(merged);
    }
  };

  const visibleIds = data.map((r, i) => String(r.id ?? i));
  const isAllVisibleSelected =
    visibleIds.length > 0 && visibleIds.every((id) => selectedIds.includes(id));

  return (
    <div className="w-full flex flex-col gap-2">
      {hiddenSelectedCount > 0 && (
        <div
          role="alert"
          className="p-3 bg-amber-950/60 border border-amber-500/40 rounded-xl text-xs text-amber-200 flex items-center justify-between"
        >
          <span>
            {`Advertencia: Hay ${hiddenSelectedCount} fila(s) seleccionada(s) que no son visibles con el filtro actual.`}
          </span>
          {onClearHiddenSelection && (
            <Button size="sm" variant="outline" onClick={onClearHiddenSelection}>
              Limpiar filas ocultas
            </Button>
          )}
        </div>
      )}
      <div className="w-full overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
        <table className="w-full text-left text-sm border-collapse">
          <caption className="sr-only">Tabla de datos de operaciones comerciales</caption>
          <thead
            className={`border-b border-slate-800 bg-slate-950/80 text-slate-400 text-xs uppercase font-semibold ${stickyHeader ? "sticky top-0 z-10 backdrop-blur-md" : ""
              }`}
          >
            <tr>
              {onSelectionChange && (
                <th scope="col" className="py-3 px-4 w-10">
                  <Checkbox
                    checked={isAllVisibleSelected}
                    onChange={handleToggleAllVisible}
                    isTableRowSelection={true}
                    label=""
                  />
                </th>
              )}
              {columns.map((col) => {
                const alignClass =
                  col.align === "right"
                    ? "text-right"
                    : col.align === "center"
                      ? "text-center"
                      : "text-left";
                return (
                  <th key={col.key} scope="col" className={`py-3 px-4 ${alignClass}`}>
                    {col.header}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td
                  colSpan={columns.length + (onSelectionChange ? 1 : 0)}
                  className="py-8 text-center text-slate-400"
                >
                  <RefreshSyncIcon size={24} className="animate-spin mx-auto mb-2 text-blue-400" />
                  Cargando datos...
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (onSelectionChange ? 1 : 0)}
                  className="py-8 text-center text-slate-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, idx) => {
                const rowId = String(row.id ?? idx);
                const isSelected = selectedIds.includes(rowId);
                const isExpanded = !!expandedRows[rowId];
                return (
                  <tr
                    key={rowId}
                    className={`transition-colors ${isSelected ? "bg-blue-950/30" : "hover:bg-slate-800/40"
                      }`}
                  >
                    {onSelectionChange && (
                      <td className="py-3 px-4">
                        <Checkbox
                          checked={isSelected}
                          onChange={() => handleToggleRow(rowId)}
                          isTableRowSelection={true}
                          label=""
                        />
                      </td>
                    )}
                    {columns.map((col) => {
                      const alignClass =
                        col.align === "right"
                          ? "text-right"
                          : col.align === "center"
                            ? "text-center"
                            : "text-left";
                      const cellVal = (row as Record<string, unknown>)[col.key];
                      const content = col.render ? col.render(row) : (cellVal as React.ReactNode);
                      return (
                        <td key={col.key} className={`py-3 px-4 text-slate-200 ${alignClass}`}>
                          {col.expandable ? (
                            <div>
                              <span
                                className={isExpanded ? "" : "line-clamp-1 max-w-xs block"}
                                title={String(cellVal ?? "")}
                              >
                                {content}
                              </span>
                              <button
                                type="button"
                                onClick={() => toggleExpand(rowId)}
                                className="text-xs text-blue-400 hover:text-blue-300 underline mt-0.5"
                              >
                                {isExpanded ? "Mostrar menos" : "Ver detalle"}
                              </button>
                            </div>
                          ) : (
                            content
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
      {(visibleSubtotalAmount !== undefined || filteredTotalCount !== undefined) && (
        <div className="flex items-center justify-between text-xs text-slate-400 px-3 py-1 bg-slate-900/40 rounded-xl border border-slate-800">
          {visibleSubtotalAmount && <span>{`Subtotal visible: ${visibleSubtotalAmount}`}</span>}
          {filteredTotalCount !== undefined && <span>{`Total filtrado: ${filteredTotalCount} registros`}</span>}
        </div>
      )}
    </div>
  );
}
