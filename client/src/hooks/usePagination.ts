/**
 * Pagination Hook
 * Provides pagination state and utilities for data tables and lists
 */

import { useState, useMemo } from 'react';

interface UsePaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
  totalItems?: number;
}

interface PaginationState {
  page: number;
  pageSize: number;
  totalPages: number;
  totalItems: number;
}

interface PaginationControls {
  goToPage: (page: number) => void;
  nextPage: () => void;
  previousPage: () => void;
  setPageSize: (size: number) => void;
  reset: () => void;
}

export function usePagination(options: UsePaginationOptions = {}) {
  const {
    initialPage = 1,
    initialPageSize = 10,
    totalItems = 0,
  } = options;

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(totalItems / pageSize));
  }, [totalItems, pageSize]);

  const paginationState: PaginationState = useMemo(() => ({
    page,
    pageSize,
    totalPages,
    totalItems,
  }), [page, pageSize, totalPages, totalItems]);

  const goToPage = (newPage: number) => {
    setPage(Math.max(1, Math.min(newPage, totalPages)));
  };

  const nextPage = () => {
    if (page < totalPages) {
      setPage(page + 1);
    }
  };

  const previousPage = () => {
    if (page > 1) {
      setPage(page - 1);
    }
  };

  const reset = () => {
    setPage(initialPage);
    setPageSize(initialPageSize);
  };

  const startIndex = useMemo(() => (page - 1) * pageSize, [page, pageSize]);
  const endIndex = useMemo(() => Math.min(startIndex + pageSize, totalItems), [startIndex, pageSize, totalItems]);

  const setPageSizeWithTotal = (size: number) => {
    setPageSize(size);
    // Reset to first page when page size changes
    setPage(1);
  };

  const controls: PaginationControls = {
    goToPage,
    nextPage,
    previousPage,
    setPageSize: setPageSizeWithTotal,
    reset,
  };

  return {
    ...paginationState,
    ...controls,
    startIndex,
    endIndex,
    hasNextPage: page < totalPages,
    hasPreviousPage: page > 1,
  };
}

