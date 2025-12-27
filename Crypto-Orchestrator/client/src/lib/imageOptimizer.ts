/**
 * Image Optimizer
 * Provides image optimization utilities
 */

/**
 * Get optimized image URL
 * Supports lazy loading, responsive images, and WebP format
 */
export function getOptimizedImageUrl(
  src: string,
  options: {
    width?: number;
    height?: number;
    quality?: number;
    format?: 'webp' | 'avif' | 'jpg' | 'png';
    lazy?: boolean;
  } = {}
): string {
  const { width, height, quality = 80, format = 'webp' } = options;

  // If using a CDN, add optimization parameters
  if (src.includes('cdn') || src.includes('cloudinary') || src.includes('imgix')) {
    const params = new URLSearchParams();
    if (width) params.set('w', width.toString());
    if (height) params.set('h', height.toString());
    params.set('q', quality.toString());
    params.set('f', format);
    params.set('auto', 'format');
    
    return `${src}?${params.toString()}`;
  }

  return src;
}

/**
 * Preload image
 */
export function preloadImage(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve();
    img.onerror = reject;
    img.src = src;
  });
}

/**
 * Get responsive image sources
 * Returns srcSet for responsive images
 */
export function getResponsiveImageSrc(
  src: string,
  widths: number[] = [320, 640, 768, 1024, 1280, 1920]
): string {
  return widths
    .map((width) => `${getOptimizedImageUrl(src, { width })} ${width}w`)
    .join(', ');
}

