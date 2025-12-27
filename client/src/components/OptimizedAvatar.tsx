/**
 * Optimized Avatar Component
 * High-performance avatar with fallback and lazy loading
 */

import React, { useState } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { User } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OptimizedAvatarProps {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeClasses = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
  xl: 'h-16 w-16',
};

export const OptimizedAvatar = React.memo(function OptimizedAvatar({
  src,
  alt = 'Avatar',
  fallback,
  size = 'md',
  className,
}: OptimizedAvatarProps) {
  const [hasError, setHasError] = useState(false);

  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const displayFallback = fallback || (alt ? getInitials(alt) : '?');

  return (
    <Avatar className={cn(sizeClasses[size], className)}>
      {src && !hasError && (
        <AvatarImage
          src={src}
          alt={alt}
          onError={() => setHasError(true)}
          loading="lazy"
        />
      )}
      <AvatarFallback>
        {displayFallback.length <= 2 ? (
          displayFallback
        ) : (
          <User className={sizeClasses[size]} />
        )}
      </AvatarFallback>
    </Avatar>
  );
});
