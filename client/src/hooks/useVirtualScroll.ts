/**
 * Virtual Scrolling Hook
 * Provides efficient rendering for large lists using virtual scrolling
 */

import { useState, useCallback, useMemo, useRef, useEffect } from 'react';

interface UseVirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
  totalItems: number;
}

interface VirtualScrollResult {
  startIndex: number;
  endIndex: number;
  visibleItems: number[];
  totalHeight: number;
  offsetY: number;
  scrollToIndex: (index: number) => void;
  scrollToTop: () => void;
  scrollToBottom: () => void;
}

export function useVirtualScroll({
  itemHeight,
  containerHeight,
  overscan = 5,
  totalItems,
}: UseVirtualScrollOptions): VirtualScrollResult {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate visible range
  const { startIndex, endIndex, totalHeight, offsetY } = useMemo(() => {
    const visibleStart = Math.floor(scrollTop / itemHeight);
    const visibleEnd = Math.ceil((scrollTop + containerHeight) / itemHeight);
    
    const start = Math.max(0, visibleStart - overscan);
    const end = Math.min(totalItems, visibleEnd + overscan);
    
    return {
      startIndex: start,
      endIndex: end,
      totalHeight: totalItems * itemHeight,
      offsetY: start * itemHeight,
    };
  }, [scrollTop, itemHeight, containerHeight, totalItems, overscan]);

  // Generate visible item indices
  const visibleItems = useMemo(() => {
    return Array.from({ length: endIndex - startIndex }, (_, i) => startIndex + i);
  }, [startIndex, endIndex]);

  // Scroll handlers
  const scrollToIndex = useCallback((index: number) => {
    if (containerRef.current) {
      const targetScrollTop = index * itemHeight;
      containerRef.current.scrollTop = targetScrollTop;
      setScrollTop(targetScrollTop);
    }
  }, [itemHeight]);

  const scrollToTop = useCallback(() => {
    scrollToIndex(0);
  }, [scrollToIndex]);

  const scrollToBottom = useCallback(() => {
    scrollToIndex(Math.max(0, totalItems - 1));
  }, [scrollToIndex, totalItems, itemHeight]);

  // Handle scroll event
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  // Attach scroll handler to container
  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll as unknown as EventListener);
      return () => {
        container.removeEventListener('scroll', handleScroll as unknown as EventListener);
      };
    }
    return undefined;
  }, [handleScroll]);

  return {
    startIndex,
    endIndex,
    visibleItems,
    totalHeight,
    offsetY,
    scrollToIndex,
    scrollToTop,
    scrollToBottom,
  };
}
