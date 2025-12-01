/**
 * Lazy Image Component
 * Loads images lazily for better performance
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { LoadingSkeleton } from './LoadingSkeleton';

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  fallback?: string;
  placeholder?: string;
  root?: Element | null;
  rootMargin?: string;
  threshold?: number;
  onLoad?: () => void;
  onError?: () => void;
}

export const LazyImage = React.memo(function LazyImage({
  src,
  alt,
  fallback,
  placeholder,
  root,
  rootMargin = '50px',
  threshold = 0,
  onLoad,
  onError,
  className,
  ...props
}: LazyImageProps) {
  const imgRef = useRef<HTMLImageElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState<string>(placeholder || '');

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setCurrentSrc(src);
            observer.disconnect();
          }
        });
      },
      {
        root,
        rootMargin,
        threshold,
      }
    );

    observer.observe(img);

    return () => observer.disconnect();
  }, [src, root, rootMargin, threshold]);

  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    onLoad?.();
  }, [onLoad]);

  const handleError = useCallback(() => {
    setHasError(true);
    if (fallback) {
      setCurrentSrc(fallback);
    }
    onError?.();
  }, [fallback, onError]);

  return (
    <div className={cn("relative", className)}>
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center">
          <LoadingSkeleton variant="card" className="w-full h-full" />
        </div>
      )}
      <img
        ref={imgRef}
        src={currentSrc}
        alt={alt}
        onLoad={handleLoad}
        onError={handleError}
        className={cn(
          "transition-opacity duration-300",
          isLoaded ? "opacity-100" : "opacity-0",
          className
        )}
        loading="lazy"
        {...props}
      />
    </div>
  );
});

