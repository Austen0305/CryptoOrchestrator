/**
 * Tests for OptimizedButton component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OptimizedButton } from '../OptimizedButton';

describe('OptimizedButton', () => {
  it('renders button with children', () => {
    render(<OptimizedButton>Click me</OptimizedButton>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    vi.useFakeTimers();
    const handleClick = vi.fn();
    
    render(<OptimizedButton onClick={handleClick}>Click me</OptimizedButton>);
    fireEvent.click(screen.getByRole('button'));
    
    expect(handleClick).not.toHaveBeenCalled();
    vi.advanceTimersByTime(300);
    expect(handleClick).toHaveBeenCalledTimes(1);
    
    vi.useRealTimers();
  });

  it('is disabled when disabled prop is true', () => {
    render(<OptimizedButton disabled>Disabled</OptimizedButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows loading state', () => {
    render(<OptimizedButton loading>Loading</OptimizedButton>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });
});

