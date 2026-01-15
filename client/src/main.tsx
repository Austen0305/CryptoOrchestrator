import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { WagmiProvider } from 'wagmi'
import { wagmiConfig } from '@/lib/wagmiConfig'
import { routeTree } from './routeTree.gen'
import './index.css'
import './i18n'

// Initialize Query Client with 2026 standard settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      gcTime: 1000 * 60 * 10, // 10 minutes
    },
  },
})

// Create Router instance
const router = createRouter({
  routeTree,
  context: {
    queryClient,
    auth: { isAuthenticated: false }, // Placeholder until AuthProvider context is hooked up
  },
  defaultPreload: 'intent', // "Intent" preloading for perceived performance
  defaultPreloadStaleTime: 0,
})

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

// Render
const rootElement = document.getElementById('root')!
if (!rootElement.innerHTML) {
  const root = createRoot(rootElement)
  root.render(
    <StrictMode>
      <WagmiProvider config={wagmiConfig}>
        <QueryClientProvider client={queryClient}>
           <RouterProvider router={router} />
        </QueryClientProvider>
      </WagmiProvider>
    </StrictMode>,
  )
}
