/**
 * Tests for OptimizedButton component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OptimizedButton } from '../OptimizedButton';

describe('OptimizedButton', () => {
  it('renders button with children', () => {
    render(<OptimizedButton>Click me</OptimizedButton>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    
    render(<OptimizedButton onClick={handleClick}>Click me</OptimizedButton>);
    await user.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
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

