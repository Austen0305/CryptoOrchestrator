/**
 * Optimized Input Component
 * Enhanced input with validation, debouncing, and accessibility
 */

import React, { useCallback, useRef, useEffect } from 'react';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { useDebounce } from '@/utils/performance';
import { cn } from '@/lib/utils';

interface OptimizedInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  debounceMs?: number;
  onDebouncedChange?: (value: string) => void;
  helperText?: string;
}

export const OptimizedInput = React.memo(function OptimizedInput({
  label,
  error,
  debounceMs = 300,
  onDebouncedChange,
  helperText,
  onChange,
  className,
  ...props
}: OptimizedInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const debouncedOnChange = useDebounce(
    useCallback(
      (value: string) => {
        onDebouncedChange?.(value);
      },
      [onDebouncedChange]
    ),
    debounceMs
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange?.(e);
      debouncedOnChange(e.target.value);
    },
    [onChange, debouncedOnChange]
  );

  return (
    <div className="space-y-2">
      {label && (
        <Label htmlFor={props.id} className={error ? 'text-destructive' : ''}>
          {label}
        </Label>
      )}
      <Input
        ref={inputRef}
        {...props}
        onChange={handleChange}
        className={cn(error && 'border-destructive', className)}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${props.id}-error` : helperText ? `${props.id}-helper` : undefined}
      />
      {error && (
        <p id={`${props.id}-error`} className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${props.id}-helper`} className="text-sm text-muted-foreground">
          {helperText}
        </p>
      )}
    </div>
  );
});
