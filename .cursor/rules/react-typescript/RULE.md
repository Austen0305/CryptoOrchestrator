---
description: React 18 and TypeScript frontend development guidelines for CryptoOrchestrator
globs: ["client/**/*.tsx", "client/**/*.ts", "shared/**/*.ts"]
alwaysApply: true
---

# React & TypeScript Development Rules

You are an expert in React 18, TypeScript 5.9+, and modern frontend development for the CryptoOrchestrator platform.

## Core Principles

- **Type Safety**: TypeScript strict mode enabled, avoid `any` type
- **Functional Components**: Use functional components with hooks, never class components
- **React Query**: Use TanStack Query (React Query) for server state management
- **Composition**: Prefer composition over inheritance
- **Performance**: Use React.memo, useMemo, useCallback appropriately

## TypeScript Standards

### Type Definitions
```typescript
// ✅ Good: Explicit types, no 'any'
interface BotConfig {
  id: number;
  name: string;
  strategy: string;
  isActive: boolean;
  createdAt: string;
}

// ✅ Good: Use union types
type TradingMode = 'custodial' | 'non-custodial';

// ✅ Good: Generic types
function useQuery<T>(queryKey: string[]): UseQueryResult<T> {
  // Implementation
}

// ❌ Bad: Using 'any'
function processData(data: any): any {
  return data;
}

// ✅ Good: Use 'unknown' if type is truly unknown
function processData(data: unknown): BotConfig {
  if (isBotConfig(data)) {
    return data;
  }
  throw new Error('Invalid data');
}
```

### TypeScript Configuration
- Strict mode enabled (`strict: true`)
- `noImplicitAny: true`
- `strictNullChecks: true`
- `strictFunctionTypes: true`
- No `any` types allowed (use `unknown` if needed)

## React Patterns

### Component Structure
```typescript
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface TradingBotCardProps {
  botId: number;
  onUpdate?: (bot: BotConfig) => void;
}

export function TradingBotCard({ botId, onUpdate }: TradingBotCardProps) {
  const { data: bot, isLoading, error } = useQuery<BotConfig>({
    queryKey: ['bot', botId],
    queryFn: () => fetchBot(botId),
  });

  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorBoundary error={error} />;
  if (!bot) return null;

  return (
    <div className="bot-card">
      <h2>{bot.name}</h2>
      <p>Strategy: {bot.strategy}</p>
    </div>
  );
}
```

### Hooks Usage
```typescript
// ✅ Good: Custom hooks for reusable logic
function useTradingBot(botId: number) {
  return useQuery({
    queryKey: ['bot', botId],
    queryFn: () => fetchBot(botId),
  });
}

// ✅ Good: useEffect with proper cleanup
useEffect(() => {
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    setPrice(JSON.parse(event.data));
  };
  
  return () => {
    ws.close();
  };
}, [wsUrl]);

// ❌ Bad: Missing cleanup
useEffect(() => {
  const interval = setInterval(() => {
    updatePrice();
  }, 1000);
  // Missing cleanup!
}, []);
```

### State Management
```typescript
// ✅ Good: React Query for server state
const { data, isLoading } = useQuery({
  queryKey: ['portfolio'],
  queryFn: fetchPortfolio,
});

// ✅ Good: Zustand for client state (if needed)
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));

// ✅ Good: Local state for component-specific state
const [isExpanded, setIsExpanded] = useState(false);
```

## Styling with TailwindCSS

### Component Styling
```typescript
// ✅ Good: Use TailwindCSS classes
<div className="flex items-center gap-4 p-4 bg-card rounded-lg shadow-md">
  <h2 className="text-2xl font-bold text-foreground">{title}</h2>
</div>

// ✅ Good: Use shadcn/ui components
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Bot Configuration</CardTitle>
  </CardHeader>
</Card>
```

### Responsive Design
```typescript
// ✅ Good: Responsive Tailwind classes
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {bots.map((bot) => (
    <BotCard key={bot.id} bot={bot} />
  ))}
</div>
```

## React Query Patterns

### Data Fetching
```typescript
// ✅ Good: Query with proper error handling
const { data, isLoading, error } = useQuery({
  queryKey: ['trades', userId],
  queryFn: () => api.getTrades(userId),
  retry: 3,
  staleTime: 30000, // 30 seconds
});

// ✅ Good: Mutations
const mutation = useMutation({
  mutationFn: (data: CreateBotRequest) => api.createBot(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['bots'] });
    toast.success('Bot created successfully');
  },
  onError: (error) => {
    toast.error(error.message);
  },
});
```

### Optimistic Updates
```typescript
const mutation = useMutation({
  mutationFn: updateBot,
  onMutate: async (newBot) => {
    await queryClient.cancelQueries({ queryKey: ['bot', botId] });
    const previousBot = queryClient.getQueryData(['bot', botId]);
    queryClient.setQueryData(['bot', botId], newBot);
    return { previousBot };
  },
  onError: (err, newBot, context) => {
    queryClient.setQueryData(['bot', botId], context?.previousBot);
  },
});
```

## Performance Optimization

### Memoization
```typescript
// ✅ Good: Memoize expensive computations
const expensiveValue = useMemo(() => {
  return calculatePortfolioValue(holdings);
}, [holdings]);

// ✅ Good: Memoize callbacks
const handleUpdate = useCallback((id: number) => {
  updateBot(id);
}, [updateBot]);

// ✅ Good: Memoize components
export const BotCard = React.memo(({ bot }: { bot: BotConfig }) => {
  return <div>{bot.name}</div>;
});
```

## Error Handling

### Error Boundaries
```typescript
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error }: { error: Error }) {
  return (
    <div role="alert">
      <h2>Something went wrong:</h2>
      <pre>{error.message}</pre>
    </div>
  );
}

export function App() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <TradingDashboard />
    </ErrorBoundary>
  );
}
```

### Loading States
```typescript
// ✅ Good: Loading skeleton
if (isLoading) {
  return <LoadingSkeleton />;
}

// ✅ Good: Loading component
const { data, isLoading } = useQuery({
  queryKey: ['portfolio'],
  queryFn: fetchPortfolio,
  placeholderData: previousData, // Keep previous data while loading
});
```

## Form Handling

### React Hook Form with Zod
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const botSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  strategy: z.enum(['grid', 'dca', 'momentum']),
  amount: z.number().positive('Amount must be positive'),
});

type BotFormData = z.infer<typeof botSchema>;

export function BotForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BotFormData>({
    resolver: zodResolver(botSchema),
  });

  const onSubmit = (data: BotFormData) => {
    createBot(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} />
      {errors.name && <span>{errors.name.message}</span>}
      {/* More fields */}
    </form>
  );
}
```

## File Organization

```
client/src/
  components/
    BotCard/
      BotCard.tsx
      BotCard.test.tsx
      index.ts
  hooks/
    useBot.ts
    useTrading.ts
  services/
    api.ts
    botService.ts
  types/
    bot.ts
    trading.ts
  utils/
    formatters.ts
    validators.ts
  pages/
    Dashboard.tsx
    Trading.tsx
```

## Accessibility

```typescript
// ✅ Good: Accessible components
<button
  onClick={handleClick}
  aria-label="Create new trading bot"
  aria-disabled={isLoading}
>
  Create Bot
</button>

// ✅ Good: Keyboard navigation
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  Clickable div
</div>
```

## Testing

```typescript
import { render, screen } from '@testing-library/react';
import { TradingBotCard } from './TradingBotCard';

test('renders bot name', () => {
  const bot = { id: 1, name: 'Test Bot', strategy: 'grid' };
  render(<TradingBotCard bot={bot} />);
  expect(screen.getByText('Test Bot')).toBeInTheDocument();
});
```

## Project-Specific Conventions

- **Path Aliases**: Use `@/*` for `client/src/*` imports
- **Shared Types**: Use `@shared/*` for shared type definitions
- **API Client**: Use centralized API client from `@/lib/api`
- **WebSocket**: Use `reconnecting-websocket` for real-time updates
- **PWA**: Support offline mode with service workers
- **Dark Mode**: Use `next-themes` for theme management
