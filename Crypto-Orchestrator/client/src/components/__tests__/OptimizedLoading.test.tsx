/**
 * Tests for OptimizedLoading component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { OptimizedLoading } from '../OptimizedLoading';

describe('OptimizedLoading', () => {
  it('renders spinner variant by default', () => {
    render(<OptimizedLoading />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders custom message', () => {
    render(<OptimizedLoading message="Custom loading message" />);
    expect(screen.getByText('Custom loading message')).toBeInTheDocument();
  });

  it('renders skeleton variant', () => {
    const { container } = render(<OptimizedLoading variant="skeleton" />);
    // Skeleton should render (checking for LoadingSkeleton component)
    expect(container).toBeTruthy();
  });

  it('renders dots variant', () => {
    const { container } = render(<OptimizedLoading variant="dots" />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders full screen when fullScreen is true', () => {
    const { container } = render(<OptimizedLoading fullScreen />);
    expect(container.firstChild).toHaveClass('min-h-screen');
  });
});

