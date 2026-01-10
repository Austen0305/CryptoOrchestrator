
# Frontend Execution TODOs

## Phase 3: Dashboard & Core UI
- [ ] **Real-Time Market Data**
  - [ ] Implement WebSocket connection for live price updates in `MarketOverview.tsx`.
  - [ ] Optimize re-renders for high-frequency updates (use `useMemo` / `React.memo`).
- [ ] **Portfolio Visualization**
  - [ ] Create `PortfolioDistribution` chart using Recharts.
  - [ ] Display real-time P&L with color coding (Green/Red).
- [ ] **Trade Management UI**
  - [ ] Build `TradeForm` component with "Buy" and "Sell" tabs.
  - [ ] Integrate `AmountInput` with validation (min/max limits).
  - [ ] Add "Confirm Trade" modal with summary details.

## Phase 4: Advanced Trading Features
- [ ] **Bot Management Interface**
  - [ ] Create `BotList` view with status indicators (Running/Stopped).
  - [ ] Build `BotConfiguration` form (Strategy selection, Risk parameters).
  - [ ] Visualize bot performance history (equity curve).
- [ ] **Wallet Integration**
  - [ ] overhaul `WalletConnect` component for better UX.
  - [ ] Display detailed transaction history with Etherscan links.

- [ ] **Frontend Code Integrity**
  - [ ] **Validation Layer**:
    - [ ] **Zod Integration**: Validate ALL API responses with `zod`. Fail fast if Backend sends non-compliant data (especially Compliance fields).
    - [ ] **Strict Types**: Enable `strict: true` in `tsconfig.json`. No `any` allowed.
  - [ ] **State Management Modernization**:
    - [ ] **Zustand Migration**: Move `TradingModeContext` and `AuthContext` to Zustand stores to prevent app-wide re-renders.
    - [ ] **Persistence**: Use `persist` middleware for User Preferences instead of raw `localStorage` calls.
  - [ ] **UX Polish (2026 Standards)**:
    - [ ] **Skeleton Screens**: Replace generic `PageLoader` spinner with layout-specific skeletons (Sidebar, Header, Content).
    - [ ] **Transitions**: Use `document.startViewTransition` API for seamless page navigations.
  - [ ] **React 19 Upgrades**:
    - [ ] **Actions**: Use `useActionState` for all form submissions (Trade, Auth).
    - [ ] **Compiler**: Ensure Vite is utilizing the React Compiler for auto-memoization.
  - [ ] **Resilience**:
    - [ ] **Error Boundaries**: Wrap major widgets (Chart, TradeForm) in React Error Boundaries to prevent full app crashes.
    - [ ] **Offline Mode**: Handle websocket disconnection gracefully with visual indicator.

- [ ] **Configuration & User Safety**:
  - [ ] **Strict Config Validation**: Validate ALL local settings and environment variables against schemas; reject unsafe or contradictory configurations.
  - [ ] **Human-in-the-Loop**: Track and display explicit human or system approval status for every pending trade.
  - [ ] **Risk Disclosure**: Enforce a one-time mandatory risk disclosure agreement on first launch.

## Phase 6: Mobile Experience (Expo)
- [ ] **Responsive Design**
  - [ ] Ensure all Dashboard widgets stack correctly on mobile.
  - [ ] Optimize touch targets for buttons.
- [ ] **Native Features**
  - [ ] Add Push Notifications (Expo Notifications) via Google Cloud Functions trigger.
  - [ ] Implement Biometric Auth (FaceID).
