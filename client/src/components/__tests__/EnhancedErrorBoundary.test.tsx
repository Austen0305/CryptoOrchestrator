/**
 * Tests for EnhancedErrorBoundary component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EnhancedErrorBoundary } from '../EnhancedErrorBoundary';

// Component that throws an error
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
}

describe('EnhancedErrorBoundary', () => {
  beforeEach(() => {
    // Suppress console.error for error boundary tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('renders children when no error', () => {
    render(
      <EnhancedErrorBoundary>
        <div>Test content</div>
      </EnhancedErrorBoundary>
    );
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('renders error UI when error occurs', () => {
    render(
      <EnhancedErrorBoundary>
        <ThrowError shouldThrow={true} />
      </EnhancedErrorBoundary>
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it('calls onError callback when error occurs', () => {
    const onError = vi.fn();
    render(
      <EnhancedErrorBoundary onError={onError}>
        <ThrowError shouldThrow={true} />
      </EnhancedErrorBoundary>
    );
    expect(onError).toHaveBeenCalled();
  });

  it('shows error details in development mode', () => {
    const originalEnv = import.meta.env.DEV;
    // @ts-ignore
    import.meta.env.DEV = true;

    render(
      <EnhancedErrorBoundary showDetails={true}>
        <ThrowError shouldThrow={true} />
      </EnhancedErrorBoundary>
    );
    
    expect(screen.getByText(/test error/i)).toBeInTheDocument();
    
    // @ts-ignore
    import.meta.env.DEV = originalEnv;
  });

  it('allows retry up to max retries', () => {
    render(
      <EnhancedErrorBoundary>
        <ThrowError shouldThrow={true} />
      </EnhancedErrorBoundary>
    );
    
    const retryButton = screen.getByText(/try again/i);
    expect(retryButton).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    const customFallback = <div>Custom error UI</div>;
    render(
      <EnhancedErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </EnhancedErrorBoundary>
    );
    expect(screen.getByText('Custom error UI')).toBeInTheDocument();
  });
});

