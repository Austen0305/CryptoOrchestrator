import { useEffect, useRef } from 'react';

type KeyboardHandler = (event: KeyboardEvent) => void;

export interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  handler: () => void;
  description?: string;
}

/**
 * Hook to register keyboard shortcuts
 * @example
 * useKeyboardShortcut({
 *   key: 's',
 *   ctrl: true,
 *   handler: () => handleSave(),
 *   description: 'Save current view'
 * });
 */
export function useKeyboardShortcut(config: ShortcutConfig) {
  const handlerRef = useRef<() => void>(config.handler);

  useEffect(() => {
    handlerRef.current = config.handler;
  }, [config.handler]);

  useEffect(() => {
    const handleKeyDown: KeyboardHandler = (event) => {
      // Check if all modifiers match
      const ctrlMatch = config.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
      const shiftMatch = config.shift ? event.shiftKey : !event.shiftKey;
      const altMatch = config.alt ? event.altKey : !event.altKey;
      const metaMatch = config.meta ? event.metaKey : !event.metaKey;

      // Check if key matches (case insensitive)
      const keyMatch = event.key.toLowerCase() === config.key.toLowerCase();

      if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
        event.preventDefault();
        handlerRef.current();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [config.key, config.ctrl, config.shift, config.alt, config.meta]);
}

/**
 * Hook to register multiple keyboard shortcuts at once
 */
export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]) {
  shortcuts.forEach((shortcut) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useKeyboardShortcut(shortcut);
  });
}

/**
 * Global keyboard shortcuts for the application
 * Usage: Call this hook once in your main App component
 */
export function useGlobalKeyboardShortcuts(navigate: (path: string) => void) {
  // Navigation shortcuts
  useKeyboardShortcut({
    key: 'h',
    alt: true,
    handler: () => navigate('/'),
    description: 'Go to home/dashboard',
  });

  useKeyboardShortcut({
    key: 'm',
    alt: true,
    handler: () => navigate('/markets'),
    description: 'Go to markets',
  });

  useKeyboardShortcut({
    key: 'b',
    alt: true,
    handler: () => navigate('/bots'),
    description: 'Go to bots',
  });

  useKeyboardShortcut({
    key: 'a',
    alt: true,
    handler: () => navigate('/analytics'),
    description: 'Go to analytics',
  });

  useKeyboardShortcut({
    key: 'r',
    alt: true,
    handler: () => navigate('/risk'),
    description: 'Go to risk management',
  });

  useKeyboardShortcut({
    key: ',',
    alt: true,
    handler: () => navigate('/settings'),
    description: 'Go to settings',
  });

  // Refresh shortcut
  useKeyboardShortcut({
    key: 'r',
    ctrl: true,
    shift: true,
    handler: () => window.location.reload(),
    description: 'Force refresh application',
  });

  // Help shortcuts
  useKeyboardShortcut({
    key: '?',
    shift: true,
    handler: () => {
      // Dispatch custom event to open keyboard shortcuts modal
      window.dispatchEvent(new CustomEvent('open-keyboard-shortcuts-modal'));
    },
    description: 'Show keyboard shortcuts',
  });
}

/**
 * Format keyboard shortcut for display
 */
export function formatShortcut(config: ShortcutConfig): string {
  const parts: string[] = [];

  if (config.ctrl || config.meta) parts.push('Ctrl');
  if (config.shift) parts.push('Shift');
  if (config.alt) parts.push('Alt');
  parts.push(config.key.toUpperCase());

  return parts.join('+');
}

/**
 * List of all available keyboard shortcuts
 */
export const KEYBOARD_SHORTCUTS: ShortcutConfig[] = [
  {
    key: 'k',
    ctrl: true,
    handler: () => {},
    description: 'Open command palette',
  },
  {
    key: 'h',
    alt: true,
    handler: () => {},
    description: 'Go to home/dashboard',
  },
  {
    key: 'm',
    alt: true,
    handler: () => {},
    description: 'Go to markets',
  },
  {
    key: 'b',
    alt: true,
    handler: () => {},
    description: 'Go to bots',
  },
  {
    key: 'a',
    alt: true,
    handler: () => {},
    description: 'Go to analytics',
  },
  {
    key: 'r',
    alt: true,
    handler: () => {},
    description: 'Go to risk management',
  },
  {
    key: ',',
    alt: true,
    handler: () => {},
    description: 'Go to settings',
  },
  {
    key: 'p',
    ctrl: true,
    shift: true,
    handler: () => {},
    description: 'Toggle performance monitor (dev only)',
  },
  {
    key: 'r',
    ctrl: true,
    shift: true,
    handler: () => {},
    description: 'Force refresh application',
  },
  {
    key: '?',
    shift: true,
    handler: () => {},
    description: 'Show keyboard shortcuts help',
  },
];
