/**
 * Accessibility Hooks
 * React hooks for accessibility features
 */

import { useEffect, useCallback, useRef } from 'react';
import { announceToScreenReader, trapFocus } from '@/utils/accessibility';

/**
 * Hook to announce messages to screen readers
 */
export function useScreenReaderAnnounce() {
  return useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    announceToScreenReader(message, priority);
  }, []);
}

/**
 * Hook to trap focus within an element
 */
export function useFocusTrap(enabled: boolean = true) {
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!enabled || !elementRef.current) return;

    const cleanup = trapFocus(elementRef.current);
    return cleanup;
  }, [enabled]);

  return elementRef;
}

/**
 * Hook to manage keyboard navigation
 */
export function useKeyboardNavigation(
  onArrowUp?: () => void,
  onArrowDown?: () => void,
  onEnter?: () => void,
  onEscape?: () => void
) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowUp':
          onArrowUp?.();
          break;
        case 'ArrowDown':
          onArrowDown?.();
          break;
        case 'Enter':
          onEnter?.();
          break;
        case 'Escape':
          onEscape?.();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onArrowUp, onArrowDown, onEnter, onEscape]);
}

/**
 * Combined accessibility hook
 */
export function useAccessibility() {
  return {
    announceToScreenReader: useScreenReaderAnnounce(),
    useFocusTrap,
    useKeyboardNavigation,
  };
}
