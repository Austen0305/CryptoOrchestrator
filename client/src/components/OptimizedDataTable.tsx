/**
 * Optimized Data Table Component
 * High-performance data table with sorting, filtering, and pagination
 */

import React, { useMemo, useState, useCallback } from 'react';
import { OptimizedTable } from './OptimizedTable';
import { OptimizedPagination } from './OptimizedPagination';
import { OptimizedSearchInput } from './OptimizedSearchInput';
import { useOptimizedPagination } from '@/hooks/useOptimizedPagination';
import { useOptimizedSearch } from '@/hooks/useOptimizedSearch';

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (value: unknown, row: T) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
}

interface OptimizedDataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  searchable?: boolean;
  paginated?: boolean;
  itemsPerPage?: number;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

export function OptimizedDataTable<T extends Record<string, unknown>>({
  data,
  columns,
  searchable = true,
  paginated = true,
  itemsPerPage = 20,
  onRowClick,
  emptyMessage = 'No data available',
}: OptimizedDataTableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);

  // Search functionality
  const { filteredData, handleSearch, searchTerm } = useOptimizedSearch({
    data,
    searchFn: (item, term) => {
      return Object.values(item).some((value) =>
        String(value).toLowerCase().includes(term.toLowerCase())
      );
    },
    minSearchLength: 0,
  });

  // Pagination
  const {
    currentPage: paginatedPage,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
  } = useOptimizedPagination({
    totalItems: filteredData.length,
    itemsPerPage,
    initialPage: currentPage,
  });

  const paginatedData = useMemo(() => {
    if (!paginated) return filteredData;
    return filteredData.slice(startIndex, endIndex);
  }, [filteredData, startIndex, endIndex, paginated]);

  return (
    <div className="space-y-4">
      {searchable && (
        <OptimizedSearchInput
          value={searchTerm}
          onChange={handleSearch}
          placeholder="Search..."
          className="max-w-sm"
        />
      )}

      <OptimizedTable
        data={paginatedData}
        columns={columns}
        onRowClick={onRowClick}
        emptyMessage={emptyMessage}
      />

      {paginated && totalPages > 1 && (
        <OptimizedPagination
          totalItems={filteredData.length}
          itemsPerPage={itemsPerPage}
          currentPage={paginatedPage}
          onPageChange={goToPage}
        />
      )}
    </div>
  );
}

