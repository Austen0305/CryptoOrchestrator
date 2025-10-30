# Design Guidelines: ML-Powered Crypto Trading Platform

## Design Approach

**Selected Approach:** Reference-Based + Design System Hybrid

Drawing inspiration from modern crypto trading platforms (Coinbase Pro, Binance, Kraken Pro) combined with Material Design principles for data-dense enterprise applications. This approach prioritizes information density, real-time data clarity, and rapid decision-making workflows while maintaining visual sophistication.

**Core Design Principles:**
1. **Data First:** Information hierarchy optimized for quick scanning and decision-making
2. **Functional Density:** Maximize useful information without overwhelming users
3. **Professional Polish:** Financial-grade interface that builds trust and credibility
4. **Responsive Performance:** Design assumes real-time updates and fluid interactions

---

## Typography System

**Font Families:**
- Primary: Inter (via Google Fonts) - body text, data displays, labels
- Monospace: JetBrains Mono (via Google Fonts) - prices, numbers, code, API keys

**Type Scale:**
- Hero/Dashboard Title: text-4xl md:text-5xl, font-bold (36-48px)
- Section Headers: text-2xl md:text-3xl, font-semibold (24-30px)
- Card Titles: text-xl, font-semibold (20px)
- Body Text: text-base, font-normal (16px)
- Data Labels: text-sm, font-medium (14px)
- Numerical Data: text-lg md:text-xl, font-mono, font-semibold (18-20px)
- Small Metadata: text-xs, font-medium (12px)

**Special Typography:**
- All price displays: font-mono with tabular-nums
- Percentage changes: font-semibold with explicit + or - prefix
- Timestamps: text-xs, opacity-75

---

## Layout System

**Spacing Primitives:**
Core spacing units: `2, 4, 6, 8, 12, 16, 24` (e.g., p-4, m-8, gap-6)

**Grid Structure:**
```
Container max-widths:
- Dashboard: Full viewport width (w-full) with no container restrictions
- Settings/Forms: max-w-7xl mx-auto
- Modal content: max-w-3xl

Trading Interface Layout:
- Multi-panel grid system: grid-cols-12 gap-4
- Main chart area: col-span-12 lg:col-span-8
- Side panels: col-span-12 lg:col-span-4
- Order book/trades: Split 50/50 or stacked on mobile
```

**Dashboard Structure:**
1. **Top Navigation Bar** (h-16): Logo, market selector, account balance summary, notifications, user menu
2. **Secondary Toolbar** (h-12): Trading pair selector, timeframe controls, quick actions
3. **Main Trading View** (flex-1): 3-column responsive layout
   - Left sidebar (w-80 hidden lg:block): Portfolio, watchlist, recent trades
   - Center panel (flex-1): Primary chart, order entry, position management
   - Right sidebar (w-72 hidden xl:block): Order book, market trades, news feed
4. **Bottom Status Bar** (h-10): Connection status, API status, real-time updates indicator

**Responsive Breakpoints:**
- Mobile: Single column, collapsible panels, bottom sheet modals
- Tablet (md:): 2-column layout, side-by-side charts and order entry
- Desktop (lg:): Full 3-column trading interface
- Large Desktop (xl:): Additional detail panels visible

---

## Component Library

### Navigation & Layout

**Top Navigation:**
- Sticky header with backdrop-blur effect
- Horizontal navigation: inline-flex items-center gap-8
- Icon buttons: w-10 h-10 with hover states
- Balance display: Prominent numerical display with secondary currency conversion

**Sidebar Navigation:**
- Fixed left sidebar (w-64) on desktop
- Collapsible hamburger menu on mobile
- Icon + label navigation items with active state indicators
- Grouped sections: Trading, Analytics, Settings, Help

### Trading Components

**Price Chart Card:**
- Full-height container (min-h-[600px])
- Chart library integration area with padding p-4
- Toolbar above chart: Timeframe pills (1H, 4H, 1D, 1W), indicator toggles, fullscreen
- Chart occupies 90% of card height, tools in remaining space

**Order Entry Panel:**
- Tabbed interface: Market, Limit, Stop-Loss tabs
- Input groups with labels above inputs
- Buy/Sell button pair: Full width, equal split (grid-cols-2 gap-3)
- Quick percentage buttons: 25%, 50%, 75%, 100% of available balance
- Order preview card with calculation breakdown

**Order Book Display:**
- Table layout with fixed column widths
- Three columns: Price (35%), Amount (35%), Total (30%)
- Scrollable tbody with max-h-[400px]
- Spread indicator between buy/sell orders
- Hover state shows order depth

**Portfolio Summary Cards:**
- Grid layout: grid-cols-1 md:grid-cols-2 xl:grid-cols-4
- Each card: p-6, rounded-lg border
- Metric structure: Label (text-sm) → Large number (text-3xl font-mono) → Change indicator (text-sm)
- Mini sparkline chart in top-right corner (w-20 h-10)

### Data Display Components

**Market Data Table:**
- Sticky header row
- Sortable columns with arrow indicators
- Row hover state with subtle elevation
- Columns: Symbol, Price, 24h Change, Volume, Market Cap, Actions
- Favorite/star icon in first column
- Action buttons: Trade, Add to Watchlist

**Trade History List:**
- Timeline-style layout with connecting lines
- Each entry: timestamp, pair, type (buy/sell), amount, price, status
- Filtering toolbar above list
- Infinite scroll or pagination at bottom

**Performance Analytics:**
- Multi-metric dashboard: grid-cols-2 lg:grid-cols-3 gap-6
- KPI cards with icon, label, value, trend indicator
- Line charts for historical performance (h-48)
- Win rate visualization with circular progress indicator

### Forms & Controls

**Strategy Configuration:**
- Accordion-style sections for different strategy parameters
- Slider inputs with value display and min/max labels
- Toggle switches for enable/disable options
- Validation feedback inline with inputs
- Save/Reset buttons at bottom: sticky footer on long forms

**Bot Control Panel:**
- Status card showing running state with pulse animation
- Start/Stop/Restart button group
- Logs viewer: Fixed height (h-96), monospace font, dark background, auto-scroll toggle
- Configuration quick edit: Key parameters as cards with inline editing

### Modals & Overlays

**Trade Confirmation Modal:**
- Centered overlay: max-w-md
- Order summary with all details in table format
- Risk warnings if applicable
- Confirm/Cancel buttons with loading states
- Close on backdrop click with animation

**Settings Panel:**
- Slide-in from right: w-full md:w-96
- Tabbed sections: Account, Trading, Notifications, API
- Form groups with clear section headers
- Apply/Cancel sticky footer

---

## Page Layouts

### Main Trading Dashboard
**Structure:**
- Header (h-16): Global nav
- Sub-header (h-14): Trading controls
- Main area (flex-1): 3-column grid as described above
- No traditional hero section - immediate data display

**Key Features:**
- Live price ticker scrolling horizontally in sub-header
- Chart takes center stage with maximum real estate
- Quick trade buttons always visible
- Real-time balance updates in header

### Analytics Dashboard
**Structure:**
- Page header: Title + date range selector (h-20)
- KPI summary: 4-column grid of metric cards
- Performance charts: 2-column grid (grid-cols-1 lg:grid-cols-2)
- Trade history table: Full width below charts
- Export buttons in top-right of sections

### Bot Management Page
**Structure:**
- Page title + Add New Bot button (h-16)
- Bot cards grid: grid-cols-1 md:grid-cols-2 xl:grid-cols-3
- Each card shows: Status, performance, quick controls
- Click card for detailed configuration modal

### Market Overview
**Structure:**
- Search bar + filters (h-16)
- Featured markets: Horizontal scroll carousel of large cards (h-32 each)
- All markets table: Sortable, filterable, paginated
- Sidebar: Trending, Top Gainers, Top Losers widgets

---

## Images

**No hero image required.** This is a data-dense application where immediate access to trading information takes priority.

**Icon Usage:**
- Status indicators: 24x24px icons from Heroicons
- Navigation: 20x20px icons
- Action buttons: 16x16px icons
- Chart overlays: 14x14px icons

**Avatar/Profile:**
- User avatar in top-right: w-8 h-8, rounded-full
- Bot avatars in management: w-12 h-12, rounded-lg

---

## Interaction Patterns

**Real-time Updates:**
- Price changes: Flash animation on update (subtle pulse)
- Order fills: Toast notification from bottom-right
- Balance changes: Number count-up animation

**Loading States:**
- Skeleton screens for initial data load
- Inline spinners for button actions
- Progress bars for long-running operations (backtesting)

**Empty States:**
- No trades: Centered illustration + "Start trading" CTA
- No watchlist: Prompt to add markets with search
- No data: Helpful message with link to documentation

---

## Accessibility & Responsiveness

**Mobile Optimization:**
- Bottom navigation for primary actions
- Swipeable panels for order book/trades
- Simplified chart with tap-to-expand
- Full-screen mode for critical actions

**Desktop Enhancements:**
- Keyboard shortcuts for quick trading (display in tooltips)
- Multi-monitor support considerations (detachable panels)
- High information density without clutter

**Critical Usability:**
- All numerical inputs validated with helpful error messages
- Confirmation dialogs for irreversible actions
- Clear distinction between paper trading and live trading modes
- API key fields: Password input type with show/hide toggle