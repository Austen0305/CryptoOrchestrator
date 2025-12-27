/**
 * Optimized Data Grid Component
 * High-performance data grid with sorting, filtering, and pagination
 */

import React, { useMemo, useState, useCallback } from 'react';
import { OptimizedTable } from './OptimizedTable';
import { OptimizedPagination } from './OptimizedPagination';
import { OptimizedSearch } from './OptimizedSearch';
import { OptimizedFilter } from './OptimizedFilter';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (value: any, row: T) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: string | number;
}

interface OptimizedDataGridProps<T> {
  data: T[];
  columns: Column<T>[];
  pageSize?: number;
  searchable?: boolean;
  filterable?: boolean;
  sortable?: boolean;
  className?: string;
  onRowClick?: (row: T) => void;
}

export function OptimizedDataGrid<T extends Record<string, any>>({
  data,
  columns,
  pageSize = 10,
  searchable = true,
  filterable = true,
  sortable = true,
  className,
  onRowClick,
}: OptimizedDataGridProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);
  const [filters, setFilters] = useState<Record<string, string[]>>({});

  const filterGroups = useMemo(() => {
    if (!filterable) return [];
    return columns
      .filter((col) => col.filterable)
      .map((col) => ({
        id: col.key as string,
        label: col.header,
        options: Array.from(
          new Set(data.map((row) => String(row[col.key])))
        ).map((value) => ({
          value,
          label: value,
        })),
      }));
  }, [columns, data, filterable]);

  const filteredData = useMemo(() => {
    let result = [...data];

    // Apply search
    if (searchTerm) {
      result = result.filter((row) =>
        columns.some((col) => {
          const value = row[col.key];
          return String(value).toLowerCase().includes(searchTerm.toLowerCase());
        })
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([key, values]) => {
      if (values.length > 0) {
        result = result.filter((row) => values.includes(String(row[key])));
      }
    });

    // Apply sorting
    if (sortConfig) {
      result.sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        return sortConfig.direction === 'asc' ? comparison : -comparison;
      });
    }

    return result;
  }, [data, searchTerm, filters, sortConfig, columns]);

  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return filteredData.slice(start, end);
  }, [filteredData, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredData.length / pageSize);

  const handleSort = useCallback(
    (key: string) => {
      if (!sortable) return;
      setSortConfig((prev) => {
        if (prev?.key === key) {
          return prev.direction === 'asc'
            ? { key, direction: 'desc' }
            : null;
        }
        return { key, direction: 'asc' };
      });
    },
    [sortable]
  );

  const tableData = useMemo(() => {
    return paginatedData.map((row) => {
      const cells: Record<string, React.ReactNode> = {};
      columns.forEach((col) => {
        const value = row[col.key];
        cells[col.key as string] = col.render
          ? col.render(value, row)
          : String(value ?? '');
      });
      return cells;
    });
  }, [paginatedData, columns]);

  return (
    <div className={cn('space-y-4', className)}>
      {(searchable || filterable) && (
        <div className="flex gap-2">
          {searchable && (
            <OptimizedSearch
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search..."
              className="flex-1"
            />
          )}
          {filterable && filterGroups.length > 0 && (
            <OptimizedFilter
              groups={filterGroups}
              selectedFilters={filters}
              onFiltersChange={setFilters}
            />
          )}
        </div>
      )}
      <OptimizedTable
        data={tableData}
        columns={columns.map((col) => ({
          key: col.key as string,
          header: col.header,
          sortable: col.sortable && sortable,
        }))}
        onRowClick={onRowClick ? (row) => {
          const index = tableData.findIndex((r) => r === row);
          const item = paginatedData[index];
          if (index >= 0 && item) onRowClick(item);
        } : undefined}
      />
      {totalPages > 1 && (
        <OptimizedPagination
          currentPage={currentPage}
          totalItems={data.length}
          itemsPerPage={pageSize}
          onPageChange={setCurrentPage}
        />
      )}
    </div>
  );
}

