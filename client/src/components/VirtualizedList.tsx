/**
 * Virtualized List Component
 * Efficiently renders large lists using virtual scrolling
 * Reduces DOM nodes and improves performance for large datasets
 */

import React, { useMemo, useRef, useEffect, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
  className?: string;
  onScroll?: (scrollTop: number) => void;
  emptyState?: React.ReactNode;
}

export function VirtualizedList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  className,
  onScroll,
  emptyState,
}: VirtualizedListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  // Calculate visible range
  const { startIndex, endIndex, totalHeight } = useMemo(() => {
    const visibleStart = Math.floor(scrollTop / itemHeight);
    const visibleEnd = Math.ceil((scrollTop + containerHeight) / itemHeight);
    
    const start = Math.max(0, visibleStart - overscan);
    const end = Math.min(items.length, visibleEnd + overscan);
    
    return {
      startIndex: start,
      endIndex: end,
      totalHeight: items.length * itemHeight,
    };
  }, [scrollTop, itemHeight, containerHeight, items.length, overscan]);

  // Visible items
  const visibleItems = useMemo(() => {
    return items.slice(startIndex, endIndex);
  }, [items, startIndex, endIndex]);

  // Handle scroll
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);
    onScroll?.(newScrollTop);
  }, [onScroll]);

  // Scroll to item
  const scrollToItem = useCallback((index: number) => {
    if (scrollElementRef.current) {
      scrollElementRef.current.scrollTop = index * itemHeight;
    }
  }, [itemHeight]);

  if (items.length === 0) {
    return (
      <div className={cn("flex items-center justify-center", className)} style={{ height: containerHeight }}>
        {emptyState || <div className="text-muted-foreground">No items to display</div>}
      </div>
    );
  }

  return (
    <div
      ref={scrollElementRef}
      className={cn("overflow-auto", className)}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            transform: `translateY(${startIndex * itemHeight}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map((item, index) => {
            const actualIndex = startIndex + index;
            return (
              <div
                key={actualIndex}
                style={{ height: itemHeight }}
              >
                {renderItem(item, actualIndex)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Export scrollToItem for external use
export type VirtualizedListRef = {
  scrollToItem: (index: number) => void;
};

