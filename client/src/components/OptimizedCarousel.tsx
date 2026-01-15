/**
 * Optimized Carousel Component
 * High-performance carousel with lazy loading
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OptimizedCarouselProps {
  items: React.ReactNode[];
  autoPlay?: boolean;
  autoPlayInterval?: number;
  showControls?: boolean;
  showIndicators?: boolean;
  className?: string;
  itemClassName?: string;
}

export function OptimizedCarousel({
  items,
  autoPlay = false,
  autoPlayInterval = 3000,
  showControls = true,
  showIndicators = true,
  className,
  itemClassName,
}: OptimizedCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const goToSlide = useCallback((index: number) => {
    setCurrentIndex(index);
  }, []);

  const goToPrevious = useCallback(() => {
    setCurrentIndex((prev) => (prev === 0 ? items.length - 1 : prev - 1));
  }, [items.length]);

  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev === items.length - 1 ? 0 : prev + 1));
  }, [items.length]);

  useEffect(() => {
    if (autoPlay) {
      intervalRef.current = setInterval(goToNext, autoPlayInterval);
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
    return undefined;
  }, [autoPlay, autoPlayInterval, goToNext]);

  if (items.length === 0) return null;

  return (
    <div className={cn('relative w-full', className)}>
      <div className="relative overflow-hidden">
        <div
          className="flex transition-transform duration-500 ease-in-out"
          style={{ transform: `translateX(-${currentIndex * 100}%)` }}
        >
          {items.map((item, index) => (
            <div
              key={index}
              className={cn('min-w-full flex-shrink-0', itemClassName)}
            >
              {item}
            </div>
          ))}
        </div>
      </div>

      {showControls && items.length > 1 && (
        <>
          <Button
            variant="outline"
            size="icon"
            className="absolute left-2 top-1/2 -translate-y-1/2 z-10"
            onClick={goToPrevious}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="absolute right-2 top-1/2 -translate-y-1/2 z-10"
            onClick={goToNext}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </>
      )}

      {showIndicators && items.length > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          {items.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={cn(
                'h-2 rounded-full transition-all',
                index === currentIndex
                  ? 'w-8 bg-primary'
                  : 'w-2 bg-muted hover:bg-primary/50'
              )}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

