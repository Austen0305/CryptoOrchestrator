/**
 * Tests for OptimizedInput component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OptimizedInput } from '../OptimizedInput';

describe('OptimizedInput', () => {
  it('renders input with label', () => {
    render(<OptimizedInput id="test" label="Test Label" />);
    expect(screen.getByLabelText('Test Label')).toBeInTheDocument();
  });

  it('shows error message when error prop is provided', () => {
    render(<OptimizedInput id="test" label="Test" error="This is an error" />);
    expect(screen.getByText('This is an error')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
  });

  it('shows helper text when provided', () => {
    render(<OptimizedInput id="test" label="Test" helperText="Helper text" />);
    expect(screen.getByText('Helper text')).toBeInTheDocument();
  });

  it('calls onChange when input value changes', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();
    
    render(<OptimizedInput id="test" onChange={handleChange} />);
    const input = screen.getByRole('textbox');
    
    await user.type(input, 'test');
    expect(handleChange).toHaveBeenCalled();
  });

  it('debounces onDebouncedChange callback', async () => {
    vi.useFakeTimers();
    const handleDebouncedChange = vi.fn();
    const user = userEvent.setup({ delay: null });
    
    render(
      <OptimizedInput
        id="test"
        onDebouncedChange={handleDebouncedChange}
        debounceMs={300}
      />
    );
    
    const input = screen.getByRole('textbox');
    await user.type(input, 'test');
    
    expect(handleDebouncedChange).not.toHaveBeenCalled();
    
    vi.advanceTimersByTime(300);
    await waitFor(() => {
      expect(handleDebouncedChange).toHaveBeenCalledWith('test');
    });
    
    vi.useRealTimers();
  });
});

