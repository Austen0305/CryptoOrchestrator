/**
 * Optimized Search Component
 * High-performance search with debouncing and suggestions
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Input } from './ui/input';
import { Search, X } from 'lucide-react';
import { Button } from './ui/button';
import { useDebouncedCallback } from '@/hooks/useOptimizedDebounce';
import { cn } from '@/lib/utils';

interface OptimizedSearchProps {
  value: string;
  onChange: (value: string) => void;
  onDebouncedChange?: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  suggestions?: string[];
  onSelectSuggestion?: (suggestion: string) => void;
  className?: string;
  showClearButton?: boolean;
}

export function OptimizedSearch({
  value,
  onChange,
  onDebouncedChange,
  placeholder = 'Search...',
  debounceMs = 300,
  suggestions = [],
  onSelectSuggestion,
  className,
  showClearButton = true,
}: OptimizedSearchProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);

  const debouncedOnChange = useDebouncedCallback(
    useCallback(
      (val: string) => {
        onDebouncedChange?.(val);
      },
      [onDebouncedChange]
    ),
    debounceMs
  );

  const filteredSuggestions = useMemo(() => {
    if (!value || !showSuggestions) return [];
    return suggestions.filter((suggestion) =>
      suggestion.toLowerCase().includes(value.toLowerCase())
    );
  }, [suggestions, value, showSuggestions]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      onChange(newValue);
      debouncedOnChange(newValue);
      setShowSuggestions(true);
      setFocusedIndex(-1);
    },
    [onChange, debouncedOnChange]
  );

  const handleClear = useCallback(() => {
    onChange('');
    onDebouncedChange?.('');
    setShowSuggestions(false);
  }, [onChange, onDebouncedChange]);

  const handleSelectSuggestion = useCallback(
    (suggestion: string) => {
      onChange(suggestion);
      onDebouncedChange?.(suggestion);
      onSelectSuggestion?.(suggestion);
      setShowSuggestions(false);
    },
    [onChange, onDebouncedChange, onSelectSuggestion]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setFocusedIndex((prev) =>
          prev < filteredSuggestions.length - 1 ? prev + 1 : prev
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setFocusedIndex((prev) => (prev > 0 ? prev - 1 : -1));
      } else if (e.key === 'Enter' && focusedIndex >= 0) {
        e.preventDefault();
        const suggestion = filteredSuggestions[focusedIndex];
        if (suggestion) {
          handleSelectSuggestion(suggestion);
        }
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
      }
    },
    [filteredSuggestions, focusedIndex, handleSelectSuggestion]
  );

  return (
    <div className={cn('relative', className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="search"
          value={value}
          onChange={handleChange}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="pl-9 pr-9"
        />
        {showClearButton && value && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClear}
            className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-lg max-h-60 overflow-auto">
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={suggestion}
              onClick={() => handleSelectSuggestion(suggestion)}
              className={cn(
                'w-full text-left px-4 py-2 hover:bg-accent transition-colors',
                index === focusedIndex && 'bg-accent'
              )}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

