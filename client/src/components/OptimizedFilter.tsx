/**
 * Optimized Filter Component
 * High-performance filter with multiple criteria
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Button } from './ui/button';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
import { Filter, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { OptimizedBadge } from './OptimizedBadge';

interface FilterOption {
  value: string;
  label: string;
}

interface FilterGroup {
  id: string;
  label: string;
  options: FilterOption[];
}

interface OptimizedFilterProps {
  groups: FilterGroup[];
  selectedFilters: Record<string, string[]>;
  onFiltersChange: (filters: Record<string, string[]>) => void;
  className?: string;
}

export function OptimizedFilter({
  groups,
  selectedFilters,
  onFiltersChange,
  className,
}: OptimizedFilterProps) {
  const [isOpen, setIsOpen] = useState(false);

  const activeFilterCount = useMemo(() => {
    return Object.values(selectedFilters).reduce(
      (sum, values) => sum + values.length,
      0
    );
  }, [selectedFilters]);

  const handleToggleFilter = useCallback(
    (groupId: string, optionValue: string) => {
      const currentValues = selectedFilters[groupId] || [];
      const newValues = currentValues.includes(optionValue)
        ? currentValues.filter((v) => v !== optionValue)
        : [...currentValues, optionValue];

      onFiltersChange({
        ...selectedFilters,
        [groupId]: newValues,
      });
    },
    [selectedFilters, onFiltersChange]
  );

  const handleClearFilters = useCallback(() => {
    onFiltersChange({});
  }, [onFiltersChange]);

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" className={cn(className)}>
          <Filter className="h-4 w-4 mr-2" />
          Filters
          {activeFilterCount > 0 && (
            <OptimizedBadge variant="default" size="sm" className="ml-2">
              {activeFilterCount}
            </OptimizedBadge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">Filters</h4>
            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearFilters}
                className="h-8"
              >
                <X className="h-3 w-3 mr-1" />
                Clear
              </Button>
            )}
          </div>
          {groups.map((group) => (
            <div key={group.id} className="space-y-2">
              <Label className="text-sm font-medium">{group.label}</Label>
              <div className="space-y-2">
                {group.options.map((option) => {
                  const isSelected = (selectedFilters[group.id] || []).includes(
                    option.value
                  );
                  return (
                    <div key={option.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={`${group.id}-${option.value}`}
                        checked={isSelected}
                        onCheckedChange={() =>
                          handleToggleFilter(group.id, option.value)
                        }
                      />
                      <Label
                        htmlFor={`${group.id}-${option.value}`}
                        className="text-sm font-normal cursor-pointer"
                      >
                        {option.label}
                      </Label>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}

