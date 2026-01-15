/**
 * Optimized Data Table Component
 * High-performance data table with sorting, filtering, and pagination
 * Powered by @tanstack/react-table
 */

import React, { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  ColumnDef,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { OptimizedPagination } from './OptimizedPagination';
import { OptimizedSearchInput } from './OptimizedSearchInput';
import { cn } from '@/lib/utils'; // Assuming this exists, or remove if not

// Re-export Column type for compatibility if needed, though simpler to use ColumnDef directly in parent
export type Column<T> = ColumnDef<T>;

interface OptimizedDataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  searchable?: boolean;
  paginated?: boolean;
  itemsPerPage?: number;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  className?: string;
}

export function OptimizedDataTable<T extends Record<string, unknown>>({
  data,
  columns,
  searchable = true,
  paginated = true,
  itemsPerPage = 20,
  onRowClick,
  emptyMessage = 'No data available',
  className,
}: OptimizedDataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: paginated ? getPaginationRowModel() : undefined,
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    initialState: {
        pagination: {
            pageSize: itemsPerPage,
        }
    }
  });

  // Helper to map TanStack rows to the format expected by OptimizedTable or render directly
  // Since OptimizedTable expects its own format, we might need to adapt it OR just implement the table markup here using flexRender.
  // Given OptimizedTable is likely a dumb presentation component, let's see if we can reuse it or if we should inline the table structure for full control.
  // For "High Performance", using flexRender is standard.
  // However, keeping consistent UI with OptimizedTable is good.
  // Let's assume OptimizedTable takes `data` and `columns`. But TanStack handles rendering cells.
  // We should probably INLINE the table rendering here to fully leverage TanStack's features (sorting handlers, etc).
  
  // Actually, checking the previous code, OptimizedTable was used. 
  // If we change to TanStack, we usually render <table><thead>... headers.map ... 
  // Let's implement the table structure directly here to ensure the "High Performance" and "Refactor" goals are met properly.

  return (
    <div className={cn("space-y-4", className)}>
      {searchable && (
        <OptimizedSearchInput
          value={globalFilter ?? ''}
          onChange={(val) => setGlobalFilter(String(val))}
          placeholder="Search..."
          className="max-w-sm"
        />
      )}

      <div className="rounded-md border border-slate-800 bg-slate-900/50 overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-900 text-slate-400 font-medium">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-slate-800">
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    colSpan={header.colSpan}
                    className="h-10 px-4 align-middle [&:has([role=checkbox])]:pr-0 cursor-pointer hover:bg-slate-800/50 transition-colors"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {!header.isPlaceholder && (
                      <div className="flex items-center gap-2">
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        {{
                          asc: ' 🔼',
                          desc: ' 🔽',
                        }[header.column.getIsSorted() as string] ?? null}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="[&_tr:last-child]:border-0 text-slate-300">
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className={cn(
                    "border-b border-slate-800 transition-colors hover:bg-slate-800/50 data-[state=selected]:bg-slate-800",
                    onRowClick && "cursor-pointer"
                  )}
                  onClick={() => onRowClick?.(row.original)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={columns.length}
                  className="h-24 text-center text-slate-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {paginated && table.getPageCount() > 1 && (
        <OptimizedPagination
          totalItems={table.getFilteredRowModel().rows.length}
          itemsPerPage={itemsPerPage}
          currentPage={table.getState().pagination.pageIndex + 1}
          onPageChange={(page) => table.setPageIndex(page - 1)}
        />
      )}
    </div>
  );
}


