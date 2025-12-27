/**
 * Optimized Image Component
 * Image component with lazy loading, error handling, and performance optimizations
 */

import React, { useState, useRef, useEffect } from 'react';
import { ImageIcon } from 'lucide-react';

interface OptimizedImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  fallback?: string;
  placeholder?: string;
  lazy?: boolean;
  aspectRatio?: string;
}

export function OptimizedImage({
  src,
  alt,
  fallback,
  placeholder,
  lazy = true,
  aspectRatio,
  className,
  ...props
}: OptimizedImageProps) {
  const [imageSrc, setImageSrc] = useState<string>(placeholder || '');
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(([entry]) => {
      if (entry) {
        setIsIntersecting(entry.isIntersecting);
      }
    }, { threshold: 0.1 });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!lazy || isIntersecting) {
      setImageSrc(src);
    }
  }, [src, lazy, isIntersecting]);

  const handleLoad = () => {
    setIsLoading(false);
    setHasError(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setHasError(true);
    if (fallback) {
      setImageSrc(fallback);
    }
  };

  const containerStyle: React.CSSProperties = {
    aspectRatio: aspectRatio || undefined,
    position: 'relative',
    overflow: 'hidden',
  };

  return (
    <div ref={ref} style={containerStyle} className={className}>
      {isLoading && (
        <div className="absolute inset-0 bg-muted animate-pulse flex items-center justify-center">
          <ImageIcon className="h-8 w-8 text-muted-foreground" />
        </div>
      )}
      {hasError && !fallback && (
        <div className="absolute inset-0 bg-muted flex items-center justify-center">
          <ImageIcon className="h-8 w-8 text-muted-foreground" />
          <span className="sr-only">Failed to load image</span>
        </div>
      )}
      <img
        src={imageSrc || src}
        alt={alt}
        onLoad={handleLoad}
        onError={handleError}
        loading={lazy ? 'lazy' : 'eager'}
        className={`transition-opacity duration-300 ${isLoading ? 'opacity-0' : 'opacity-100'}`}
        {...props}
      />
    </div>
  );
}

