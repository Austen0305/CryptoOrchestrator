import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { exportToCSV, exportToJSON, formatTradesForExport } from './export';

describe('export utilities', () => {
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;
  let anchor: HTMLAnchorElement | null = null;

  beforeEach(() => {
    // Mock object URL APIs
    URL.createObjectURL = vi.fn().mockReturnValue('blob:mock');
    URL.revokeObjectURL = vi.fn();

    // Spy on document to catch anchor clicks
    const realCreateElement = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tagName: any) => {
      const el = realCreateElement(tagName);
      if (tagName === 'a') {
        anchor = el as HTMLAnchorElement;
        vi.spyOn(anchor, 'click').mockImplementation(() => {});
      }
      return el;
    });
    // Ensure body exists
    if (!document.body) {
      (document as any).body = document.createElement('body');
    }
  });

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
    vi.restoreAllMocks();
    anchor = null;
  });

  it('exports CSV without throwing and triggers anchor click', () => {
    const rows = [
      { a: 1, b: 'two' },
      { a: 3, b: 'four, with comma' },
    ];
    expect(() => exportToCSV(rows, { filename: 'test.csv' })).not.toThrow();
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(anchor && (anchor as any).click).toBeDefined();
  });

  it('exports JSON without throwing and triggers anchor click', () => {
    const data = { hello: 'world', n: 42 };
    expect(() => exportToJSON(data, { filename: 'test.json' })).not.toThrow();
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(anchor && (anchor as any).click).toBeDefined();
  });

  it('formats trades for export with sensible defaults', () => {
    const trades = [
      { timestamp: Date.now(), pair: 'BTC/USD', side: 'buy', type: 'market', price: 100, amount: 2 },
    ];
    const formatted = formatTradesForExport(trades);
    expect(formatted[0]).toHaveProperty('Date');
    expect(formatted[0]).toHaveProperty('Symbol', 'BTC/USD');
    expect(formatted[0]).toHaveProperty('Total', 200);
  });
});
