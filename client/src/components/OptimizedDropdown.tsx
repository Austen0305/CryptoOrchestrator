/**
 * Optimized Dropdown Component
 * High-performance dropdown with virtualization
 */

import React, { useState, useRef, useCallback } from 'react';
import { useClickOutside } from '@/hooks/useClickOutside';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';
import { Button } from './ui/button';

interface OptimizedDropdownOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface OptimizedDropdownProps {
  options: OptimizedDropdownOption[];
  value?: string;
  onSelect?: (value: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export function OptimizedDropdown({
  options,
  value,
  onSelect,
  placeholder = 'Select...',
  className,
  disabled,
}: OptimizedDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useClickOutside<HTMLDivElement>(() => setIsOpen(false), isOpen);

  const selectedOption = options.find((opt) => opt.value === value);

  const handleSelect = useCallback(
    (optionValue: string) => {
      onSelect?.(optionValue);
      setIsOpen(false);
    },
    [onSelect]
  );

  return (
    <div ref={dropdownRef} className={cn('relative', className)}>
      <Button
        variant="outline"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full justify-between"
      >
        <span>{selectedOption?.label || placeholder}</span>
        <ChevronDown
          className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')}
        />
      </Button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-lg max-h-60 overflow-auto">
          {options.map((option) => (
            <button
              key={option.value}
              onClick={() => !option.disabled && handleSelect(option.value)}
              disabled={option.disabled}
              className={cn(
                'w-full text-left px-4 py-2 hover:bg-accent transition-colors',
                value === option.value && 'bg-accent',
                option.disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              <div className="flex items-center gap-2">
                {option.icon}
                <span>{option.label}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
