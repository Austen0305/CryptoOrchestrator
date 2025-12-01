/**
 * Tests for VirtualizedList component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VirtualizedList } from '../VirtualizedList';

describe('VirtualizedList', () => {
  const mockItems = Array.from({ length: 100 }, (_, i) => ({
    id: i,
    name: `Item ${i}`,
  }));

  const renderItem = (item: { id: number; name: string }, index: number) => (
    <div key={item.id} data-testid={`item-${index}`}>
      {item.name}
    </div>
  );

  it('renders empty state when no items', () => {
    render(
      <VirtualizedList
        items={[]}
        itemHeight={50}
        containerHeight={400}
        renderItem={renderItem}
      />
    );
    expect(screen.getByText(/no items/i)).toBeInTheDocument();
  });

  it('renders items within viewport', () => {
    render(
      <VirtualizedList
        items={mockItems.slice(0, 10)}
        itemHeight={50}
        containerHeight={400}
        renderItem={renderItem}
      />
    );
    // Should render visible items
    expect(screen.getByTestId('item-0')).toBeInTheDocument();
  });

  it('handles large lists efficiently', () => {
    const { container } = render(
      <VirtualizedList
        items={mockItems}
        itemHeight={50}
        containerHeight={400}
        renderItem={renderItem}
      />
    );
    // Should only render visible items, not all 100
    const renderedItems = container.querySelectorAll('[data-testid^="item-"]');
    expect(renderedItems.length).toBeLessThan(20); // Only visible + overscan
  });

  it('calls onScroll callback', () => {
    const onScroll = vi.fn();
    const { container } = render(
      <VirtualizedList
        items={mockItems}
        itemHeight={50}
        containerHeight={400}
        renderItem={renderItem}
        onScroll={onScroll}
      />
    );
    
    const scrollContainer = container.querySelector('[class*="overflow-auto"]');
    if (scrollContainer) {
      scrollContainer.scrollTop = 100;
      scrollContainer.dispatchEvent(new Event('scroll'));
      expect(onScroll).toHaveBeenCalled();
    }
  });

  it('renders custom empty state', () => {
    const customEmpty = <div>No data available</div>;
    render(
      <VirtualizedList
        items={[]}
        itemHeight={50}
        containerHeight={400}
        renderItem={renderItem}
        emptyState={customEmpty}
      />
    );
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });
});

