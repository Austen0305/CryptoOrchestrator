import { createFileRoute, Outlet, useRouter } from '@tanstack/react-router'
import { AppSidebar } from '@/components/AppSidebar'
import { TradingHeader } from '@/components/TradingHeader'
import { SidebarProvider } from '@/components/ui/sidebar'
import { useAuth } from '@/hooks/useAuth'
import { usePortfolio } from '@/hooks/useApi'
import { useEffect } from 'react'

export const Route = createFileRoute('/_auth')({
  component: AuthLayout,
})

function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
       router.navigate({ to: '/login' })
    }
  }, [isLoading, isAuthenticated, router])

  const { data: portfolio } = usePortfolio(undefined)

  if (isLoading) return <div className="flex h-screen items-center justify-center">Loading...</div>

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex min-h-screen w-full bg-background text-foreground font-feature-default selection:bg-primary selection:text-black">
        <div className="scanline" />
        <AppSidebar />
        <main className="flex-1 flex flex-col min-h-screen overflow-hidden transition-all duration-300 ease-in-out relative z-0">
           <TradingHeader balance={portfolio?.totalBalance || 0} connected={true} />
           <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4 md:space-y-6 relative z-10 scrollbar-hide">
             <Outlet />
           </div>
        </main>
      </div>
    </SidebarProvider>
  )
}
