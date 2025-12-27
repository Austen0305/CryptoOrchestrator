/**
 * Tests for OptimizedCard component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { OptimizedCard } from '../OptimizedCard';

describe('OptimizedCard', () => {
  it('renders card with title and description', () => {
    render(
      <OptimizedCard title="Test Title" description="Test Description">
        Content
      </OptimizedCard>
    );
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders card without title and description', () => {
    render(<OptimizedCard>Content only</OptimizedCard>);
    expect(screen.getByText('Content only')).toBeInTheDocument();
  });

  it('renders card with footer', () => {
    render(
      <OptimizedCard footer={<button>Action</button>}>
        Content
      </OptimizedCard>
    );
    expect(screen.getByText('Action')).toBeInTheDocument();
  });

  it('applies hoverable class when hoverable is true', () => {
    const { container } = render(
      <OptimizedCard hoverable>Content</OptimizedCard>
    );
    expect(container.firstChild).toHaveClass('hover:shadow-lg', 'cursor-pointer');
  });
});

