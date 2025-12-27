/**
 * Tests for useLocalStorageState hook
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocalStorageState } from '../useLocalStorageState';

describe('useLocalStorageState', () => {
  const key = 'test-key';
  
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('initializes with initial value', () => {
    const { result } = renderHook(() =>
      useLocalStorageState(key, 'initial')
    );
    expect(result.current[0]).toBe('initial');
  });

  it('reads from localStorage if value exists', () => {
    localStorage.setItem(key, JSON.stringify('stored'));
    const { result } = renderHook(() =>
      useLocalStorageState(key, 'initial')
    );
    expect(result.current[0]).toBe('stored');
  });

  it('updates localStorage when value changes', () => {
    const { result } = renderHook(() =>
      useLocalStorageState(key, 'initial')
    );

    act(() => {
      result.current[1]('updated');
    });

    expect(result.current[0]).toBe('updated');
    expect(localStorage.getItem(key)).toBe(JSON.stringify('updated'));
  });

  it('handles function updates', () => {
    const { result } = renderHook(() =>
      useLocalStorageState(key, 0)
    );

    act(() => {
      result.current[1]((prev) => prev + 1);
    });

    expect(result.current[0]).toBe(1);
  });
});

