/**
 * Optimized Search Input Component
 * High-performance search input with debouncing
 */

import React from 'react';
import { Input } from './ui/input';
import { Search, X } from 'lucide-react';
import { Button } from './ui/button';
import { useOptimizedDebounce } from '@/hooks/useOptimizedDebounce';
import { cn } from '@/lib/utils';

interface OptimizedSearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onDebouncedChange?: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  className?: string;
  showClearButton?: boolean;
}

export function OptimizedSearchInput({
  value,
  onChange,
  onDebouncedChange,
  placeholder = 'Search...',
  debounceMs = 300,
  className,
  showClearButton = true,
}: OptimizedSearchInputProps) {
  const debouncedValue = useOptimizedDebounce(value, { delay: debounceMs });

  React.useEffect(() => {
    if (onDebouncedChange && debouncedValue !== value) {
      onDebouncedChange(debouncedValue);
    }
  }, [debouncedValue, onDebouncedChange, value]);

  const handleClear = () => {
    onChange('');
  };

  return (
    <div className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="pl-9 pr-9"
      />
      {showClearButton && value && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
          onClick={handleClear}
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

