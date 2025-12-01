import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/testUtils';
import { OrderEntryPanel } from '../OrderEntryPanel';

describe('OrderEntryPanel', () => {
  it('should render order entry form', () => {
    renderWithProviders(<OrderEntryPanel />);

    expect(screen.getByText(/buy|sell|order/i)).toBeInTheDocument();
  });

  it('should toggle between buy and sell', async () => {
    const user = userEvent.setup();
    renderWithProviders(<OrderEntryPanel />);

    const buyButton = screen.getByRole('button', { name: /buy/i });
    const sellButton = screen.getByRole('button', { name: /sell/i });

    if (buyButton && sellButton) {
      await user.click(buyButton);
      expect(buyButton).toHaveAttribute('aria-selected', 'true');

      await user.click(sellButton);
      expect(sellButton).toHaveAttribute('aria-selected', 'true');
    }
  });

  it('should allow entering amount', async () => {
    const user = userEvent.setup();
    renderWithProviders(<OrderEntryPanel />);

    const amountInput = screen.getByLabelText(/amount|quantity/i);
    
    if (amountInput) {
      await user.type(amountInput, '0.1');
      expect(amountInput).toHaveValue('0.1');
    }
  });

  it('should allow entering price', async () => {
    const user = userEvent.setup();
    renderWithProviders(<OrderEntryPanel />);

    const priceInput = screen.getByLabelText(/price/i);
    
    if (priceInput) {
      await user.type(priceInput, '45000');
      expect(priceInput).toHaveValue('45000');
    }
  });

  it('should have submit button', () => {
    renderWithProviders(<OrderEntryPanel />);

    const submitButton = screen.getByRole('button', { name: /submit|place order|execute/i });
    expect(submitButton).toBeInTheDocument();
  });
});

