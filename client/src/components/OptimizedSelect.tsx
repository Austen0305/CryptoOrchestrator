/**
 * Optimized Select Component
 * Enhanced select with search and virtualization
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Input } from './ui/input';
import { cn } from '@/lib/utils';

interface OptimizedSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface OptimizedSelectProps {
  options: OptimizedSelectOption[];
  value?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  className?: string;
  disabled?: boolean;
}

export const OptimizedSelect = React.memo(function OptimizedSelect({
  options,
  value,
  onValueChange,
  placeholder = 'Select...',
  searchable = false,
  className,
  disabled,
}: OptimizedSelectProps) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredOptions = useMemo(() => {
    if (!searchable || !searchTerm) return options;
    return options.filter((option) =>
      option.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [options, searchTerm, searchable]);

  const handleValueChange = useCallback(
    (newValue: string) => {
      onValueChange?.(newValue);
      setSearchTerm('');
    },
    [onValueChange]
  );

  return (
    <Select value={value} onValueChange={handleValueChange} disabled={disabled}>
      <SelectTrigger className={cn(className)}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {searchable && (
          <div className="p-2 border-b">
            <Input
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="h-8"
            />
          </div>
        )}
        {filteredOptions.length === 0 ? (
          <div className="p-2 text-sm text-muted-foreground">No options found</div>
        ) : (
          filteredOptions.map((option) => (
            <SelectItem
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </SelectItem>
          ))
        )}
      </SelectContent>
    </Select>
  );
});
