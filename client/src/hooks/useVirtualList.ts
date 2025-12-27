/**
 * Virtual List Hook
 * Optimized hook for rendering large lists efficiently
 */

import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useVirtualScroll } from '@/utils/performance';

interface UseVirtualListOptions<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

export function useVirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  overscan = 3,
}: UseVirtualListOptions<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const { visibleItems, totalHeight, offsetY, handleScroll } = useVirtualScroll(
    items,
    itemHeight,
    containerHeight
  );

  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(
    startIndex + Math.ceil(containerHeight / itemHeight) + overscan,
    items.length
  );

  const visibleItemsWithIndex = useMemo(
    () =>
      visibleItems.map((item, index) => ({
        item,
        index: startIndex + index,
      })),
    [visibleItems, startIndex]
  );

  const onScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      setScrollTop(e.currentTarget.scrollTop);
      handleScroll(e);
    },
    [handleScroll]
  );

  return {
    containerRef,
    visibleItems: visibleItemsWithIndex,
    totalHeight,
    offsetY,
    onScroll,
  };
}

