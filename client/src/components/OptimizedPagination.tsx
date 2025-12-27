/**
 * Optimized Pagination Component
 * High-performance pagination with keyboard navigation
 */

import React from 'react';
import { Button } from './ui/button';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { useOptimizedPagination } from '@/hooks/useOptimizedPagination';

interface OptimizedPaginationProps {
  totalItems: number;
  itemsPerPage: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  showPageNumbers?: boolean;
  maxPageNumbers?: number;
}

export function OptimizedPagination({
  totalItems,
  itemsPerPage,
  currentPage,
  onPageChange,
  showPageNumbers = true,
  maxPageNumbers = 5,
}: OptimizedPaginationProps) {
  const {
    totalPages,
    hasNextPage,
    hasPreviousPage,
    goToPage,
    nextPage,
    previousPage,
    goToFirstPage,
    goToLastPage,
  } = useOptimizedPagination({
    totalItems,
    itemsPerPage,
    initialPage: currentPage,
  });

  // Calculate page numbers to show
  const pageNumbers = React.useMemo(() => {
    if (!showPageNumbers || totalPages <= 1) return [];

    const pages: number[] = [];
    const half = Math.floor(maxPageNumbers / 2);
    let start = Math.max(1, currentPage - half);
    let end = Math.min(totalPages, start + maxPageNumbers - 1);

    if (end - start < maxPageNumbers - 1) {
      start = Math.max(1, end - maxPageNumbers + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }, [currentPage, totalPages, maxPageNumbers, showPageNumbers]);

  const handlePageChange = (page: number) => {
    goToPage(page);
    onPageChange(page);
  };

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between gap-2">
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            goToFirstPage();
            onPageChange(1);
          }}
          disabled={!hasPreviousPage}
          aria-label="First page"
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            previousPage();
            onPageChange(currentPage - 1);
          }}
          disabled={!hasPreviousPage}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>

      {showPageNumbers && (
        <div className="flex items-center gap-1">
          {pageNumbers.map((page) => (
            <Button
              key={page}
              variant={page === currentPage ? 'default' : 'outline'}
              size="sm"
              onClick={() => handlePageChange(page)}
              aria-label={`Page ${page}`}
              aria-current={page === currentPage ? 'page' : undefined}
            >
              {page}
            </Button>
          ))}
        </div>
      )}

      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            nextPage();
            onPageChange(currentPage + 1);
          }}
          disabled={!hasNextPage}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            goToLastPage();
            onPageChange(totalPages);
          }}
          disabled={!hasNextPage}
          aria-label="Last page"
        >
          <ChevronsRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

