import { createRootRouteWithContext, Outlet } from '@tanstack/react-router'
import { QueryClient } from '@tanstack/react-query'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { SidebarProvider } from '@/components/ui/sidebar'
import { Toaster } from '@/components/ui/toaster'

interface RouterContext {
  queryClient: QueryClient
  auth: { isAuthenticated: boolean } // Basic auth context structure
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
})

function RootComponent() {
  return (
    <>
      {/* 
        This is the Shell. 
        In strict TanStack Router, we often move providers UP to main.tsx, 
        and only keep Layout UI here.
      */}
      <div className="min-h-screen bg-background text-foreground font-sans antialiased">
        <Outlet />
        <Toaster />
      </div>
      
      {/* Only show devtools in dev */}
      {import.meta.env.DEV && <TanStackRouterDevtools position="bottom-right" />}
    </>
  )
}
