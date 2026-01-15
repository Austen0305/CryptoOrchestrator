import { useAuth } from '@/hooks/useAuth'
import { useEffect } from 'react'
import { useLocation, useNavigate } from '@tanstack/react-router'

export function UserDataLoader({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  
  // This component sits inside AuthProvider creates a bridge 
  // ensuring we don't render the router until we know auth state if needed,
  // or simply letting the router handle the redirects.
  // For now, it's a pass-through that could be expanded.
  
  return <>{children}</>
}
