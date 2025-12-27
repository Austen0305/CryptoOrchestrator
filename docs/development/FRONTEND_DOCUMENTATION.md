# CryptoOrchestrator Frontend Documentation

## Architecture Overview

The frontend is built using:

- React + TypeScript for type safety
- Zustand for state management
- React Query for data fetching
- Styled Components for styling
- Framer Motion for animations

## Core Components

### State Management
The global state is managed by Zustand and split into domains:
- Market state (prices, orderbook)
- User state (portfolio, settings)
- Bot state (trading bots, status)
- UI state (loading, errors)

### Real-time Data
WebSocket connections are managed by the WebSocketService:
- Automatic reconnection
- Message queuing
- Error handling
- Connection status monitoring

### Error Handling
Multiple layers of error handling:
1. Global error boundary for React component errors
2. API error handling in data fetches
3. WebSocket connection error handling
4. Form validation errors

### Performance Optimizations
1. React Query for efficient data fetching:
   - Caching
   - Background updates
   - Optimistic updates
   
2. Code splitting:
   - Lazy loading routes
   - Dynamic imports for heavy components

3. Memoization:
   - useMemo for expensive calculations
   - useCallback for stable callbacks
   - memo for pure components

### Mobile Responsiveness
The UI is fully responsive using:
1. Flexbox and Grid layouts
2. Media queries for breakpoints
3. Touch-friendly interactions
4. Collapsible navigation
5. Optimized for different screen sizes

## Component Usage

### ErrorBoundary
```tsx
// Wrap components that might error
<ErrorBoundary>
  <ComponentThatMightError />
</ErrorBoundary>

// With custom fallback
<ErrorBoundary fallback={<CustomError />}>
  <ComponentThatMightError />
</ErrorBoundary>
```

### GlobalLoadingIndicator
```tsx
// In App.tsx
<GlobalLoadingIndicator />

// Setting loading state
useStore.getState().setLoading('marketData', true);
```

### ResponsiveNavigation
```tsx
// In App.tsx
<ResponsiveNavigation />
```

### ConnectionStatus
```tsx
// Show WebSocket connection status
<ConnectionStatus />
```

## State Management Guide

### Using the Store
```tsx
// Reading state
const value = useStore(state => state.someValue);

// Updating state
useStore.getState().setSomeValue(newValue);

// With optimistic updates
queryClient.setQueryData(['key'], optimisticValue);
someAction().then(() => {
  queryClient.invalidateQueries(['key']);
});
```

### WebSocket Integration
```tsx
// Subscribe to market data
useEffect(() => {
  const ws = WebSocketService.getInstance();
  ws.subscribe(['BTC/USD', 'ETH/USD']);
  
  return () => {
    ws.unsubscribe(['BTC/USD', 'ETH/USD']);
  };
}, []);
```

## Best Practices

1. Error Handling:
   - Always wrap potentially unstable components in ErrorBoundary
   - Handle API errors gracefully
   - Show meaningful error messages to users

2. Loading States:
   - Use GlobalLoadingIndicator for full-page loads
   - Use skeleton loaders for component-level loading
   - Show loading progress when possible

3. Data Fetching:
   - Use React Query for REST API calls
   - Handle WebSocket data through global store
   - Implement retry logic for failed requests

4. Performance:
   - Lazy load routes and heavy components
   - Memoize expensive calculations
   - Use windowing for long lists
   - Optimize images and assets

5. Mobile Support:
   - Test on various screen sizes
   - Ensure touch targets are large enough
   - Provide alternative interactions for hover states