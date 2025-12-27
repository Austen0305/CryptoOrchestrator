/**
 * Optimized Search Hook
 * Enhanced search with debouncing and filtering
 */

import { useState, useMemo, useCallback } from 'react';
import { useOptimizedDebounce } from './useOptimizedDebounce';

interface UseOptimizedSearchOptions<T> {
  data: T[];
  searchFn: (item: T, searchTerm: string) => boolean;
  debounceMs?: number;
  minSearchLength?: number;
}

export function useOptimizedSearch<T>({
  data,
  searchFn,
  debounceMs = 300,
  minSearchLength = 0,
}: UseOptimizedSearchOptions<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useOptimizedDebounce(searchTerm, { delay: debounceMs });

  const filteredData = useMemo(() => {
    if (!debouncedSearchTerm || debouncedSearchTerm.length < minSearchLength) {
      return data;
    }

    return data.filter((item) => searchFn(item, debouncedSearchTerm));
  }, [data, debouncedSearchTerm, searchFn, minSearchLength]);

  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
  }, []);

  const clearSearch = useCallback(() => {
    setSearchTerm('');
  }, []);

  return {
    searchTerm,
    debouncedSearchTerm,
    filteredData,
    handleSearch,
    clearSearch,
    hasResults: filteredData.length > 0,
    resultCount: filteredData.length,
  };
}

