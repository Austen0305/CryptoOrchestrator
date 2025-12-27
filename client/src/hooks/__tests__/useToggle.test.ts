/**
 * Tests for useToggle hook
 */

import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToggle } from '../useToggle';

describe('useToggle', () => {
  it('initializes with default value', () => {
    const { result } = renderHook(() => useToggle(false));
    expect(result.current[0]).toBe(false);
  });

  it('toggles value', () => {
    const { result } = renderHook(() => useToggle(false));
    
    act(() => {
      result.current[1](); // toggle
    });
    
    expect(result.current[0]).toBe(true);
    
    act(() => {
      result.current[1](); // toggle again
    });
    
    expect(result.current[0]).toBe(false);
  });

  it('sets value directly', () => {
    const { result } = renderHook(() => useToggle(false));
    
    act(() => {
      result.current[2](true); // setToggle
    });
    
    expect(result.current[0]).toBe(true);
    
    act(() => {
      result.current[2](false); // setToggle
    });
    
    expect(result.current[0]).toBe(false);
  });
});

