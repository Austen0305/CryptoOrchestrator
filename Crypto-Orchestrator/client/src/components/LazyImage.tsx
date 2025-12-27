/**
 * Lazy Image Component
 * Loads images lazily for better performance with WebP/AVIF support
 */

import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { LoadingSkeleton } from './LoadingSkeleton';
import { 
  generateBlurPlaceholder, 
  getOptimizedImageUrl, 
  getBestImageFormat,
  generateSrcSet 
} from '@/utils/imageOptimization';
import { useIntersectionObserver } from '@/hooks/useIntersectionObserver';

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
  useWebP?: boolean;
  useSrcSet?: boolean;
  widths?: number[];
}

export const LazyImage = React.memo(function LazyImage({
  src,
  alt,
  fallback,
  placeholder,
  root,
  rootMargin = '50px',
  threshold = 0.1,
  onLoad,
  onError,
  className,
  useWebP = true,
  useSrcSet = false,
  widths = [320, 640, 960, 1280, 1920],
  ...props
}: LazyImageProps) {
  const imgRef = useRef<HTMLImageElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [bestFormat, setBestFormat] = useState<'webp' | 'avif' | 'jpg' | 'png'>('jpg');
  const [currentSrc, setCurrentSrc] = useState<string>(placeholder || generateBlurPlaceholder());

  // Use intersection observer hook
  const [observerRef, hasIntersected] = useIntersectionObserver({
    threshold,
    root,
    rootMargin,
    triggerOnce: true,
  });

  // Determine best image format
  useEffect(() => {
    if (useWebP && hasIntersected) {
      getBestImageFormat().then(setBestFormat);
    }
  }, [useWebP, hasIntersected]);

  // Update image source when intersection occurs
  useEffect(() => {
    if (hasIntersected && src) {
      const optimizedSrc = useWebP ? getOptimizedImageUrl(src, bestFormat) : src;
      setCurrentSrc(optimizedSrc);
    }
  }, [hasIntersected, src, useWebP, bestFormat]);

  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    onLoad?.();
  }, [onLoad]);

  const handleError = useCallback(() => {
    if (fallback && currentSrc !== fallback) {
      setCurrentSrc(fallback);
      setHasError(false);
    } else {
      setHasError(true);
      onError?.();
    }
  }, [fallback, currentSrc, onError]);

  // Generate srcset if enabled
  const srcSet = useMemo(() => {
    if (useSrcSet && hasIntersected && src) {
      const baseUrl = useWebP ? getOptimizedImageUrl(src, bestFormat) : src;
      return generateSrcSet(baseUrl, widths);
    }
    return undefined;
  }, [useSrcSet, hasIntersected, src, useWebP, bestFormat, widths]);

  // Combine refs
  useEffect(() => {
    if (imgRef.current && observerRef.current) {
      // Both refs point to the same element
      if (imgRef.current !== observerRef.current) {
        (observerRef as React.MutableRefObject<HTMLElement>).current = imgRef.current;
      }
    }
  }, [observerRef]);

  return (
    <div className={cn("relative", className)}>
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/50">
          <LoadingSkeleton variant="card" className="w-full h-full" />
        </div>
      )}
      <img
        ref={(node) => {
          // Update imgRef using a mutable ref pattern
          (imgRef as React.MutableRefObject<HTMLImageElement | null>).current = node;
          if (node && observerRef) {
            (observerRef as React.MutableRefObject<HTMLElement | null>).current = node;
          }
        }}
        src={currentSrc}
        srcSet={srcSet}
        sizes={useSrcSet ? "(max-width: 640px) 320px, (max-width: 960px) 640px, (max-width: 1280px) 960px, 1280px" : undefined}
        alt={alt}
        onLoad={handleLoad}
        onError={handleError}
        className={cn(
          "transition-opacity duration-300",
          isLoaded ? "opacity-100" : "opacity-0",
          className
        )}
        loading="lazy"
        decoding="async"
        {...props}
      />
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for memo
  return (
    prevProps.src === nextProps.src &&
    prevProps.alt === nextProps.alt &&
    prevProps.className === nextProps.className
  );
});

