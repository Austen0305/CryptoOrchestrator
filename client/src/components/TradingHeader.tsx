// Types enforced; temporary ts-nocheck removed.
import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Settings, LogIn, LogOut } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { AuthModal } from "./AuthModal";
import { NotificationCenter } from "./NotificationCenter";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";

interface TradingHeaderProps {
  balance: number;
  connected: boolean;
}

export function TradingHeader({ balance, connected }: TradingHeaderProps) {
  const { isAuthenticated, user, logout } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { toast } = useToast();

  // Open auth modal automatically on auth:expired events
  useEffect(() => {
    const handler = () => {
      // Clear any stale modal state then reopen
      setShowAuthModal(true);
      try {
        toast({ title: 'Session expired', description: 'Please log in again to continue.', variant: 'destructive' });
      } catch (error) {
        // Silently ignore toast errors - toast may not be available in all contexts
      }
    };
    window.addEventListener('auth:expired', handler);
    return () => window.removeEventListener('auth:expired', handler);
  }, []);

  // If user becomes authenticated while modal is open, close it
  useEffect(() => {
    if (isAuthenticated && showAuthModal) setShowAuthModal(false);
  }, [isAuthenticated, showAuthModal]);

  return (
    <header 
      className="border-b-2 border-primary/30 bg-gradient-to-r from-card/98 via-card/95 to-card/98 backdrop-blur-lg flex items-center justify-between px-4 md:px-6 shadow-2xl" 
      style={{ 
        borderBottomWidth: '4px', 
        borderBottomStyle: 'solid',
        borderBottomColor: 'hsl(var(--primary) / 0.4)',
        boxShadow: '0px 12px 24px -6px hsl(220 8% 2% / 0.50), 0px 6px 12px -6px hsl(220 8% 2% / 0.50)', 
        minHeight: '5rem',
        height: '5rem',
        background: 'linear-gradient(135deg, hsl(var(--card) / 0.98), hsl(var(--card) / 0.95), hsl(var(--card) / 0.98))'
      }}
    >
      <div className="flex items-center gap-4 md:gap-6">
        <h1 
          className="text-3xl md:text-4xl font-black" 
          style={{ 
            backgroundImage: 'linear-gradient(135deg, hsl(217 91% 55%), hsl(217 91% 65%), hsl(217 91% 55%))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            textShadow: '0 4px 12px hsl(217 91% 50% / 0.5)',
            fontWeight: 900,
            letterSpacing: '-0.02em'
          }}
        >
          CryptoML
        </h1>
        <Badge 
          variant={connected ? "default" : "secondary"} 
          data-testid="badge-connection"
          className="badge-enhanced"
        >
          <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
          {connected ? "Connected" : "Disconnected"}
        </Badge>
      </div>

      <div className="flex items-center gap-3 md:gap-4">
        <div className="text-right hidden sm:block">
          <p className="text-xs text-muted-foreground font-medium">Total Balance</p>
          <p className="text-base md:text-lg font-mono font-bold text-foreground" data-testid="text-balance">
            ${balance.toLocaleString()}
          </p>
        </div>
        <div className="h-8 w-px bg-border hidden sm:block" />
        {isAuthenticated && <NotificationCenter />}
        <Button 
          variant="ghost" 
          size="icon" 
          data-testid="button-settings" 
          aria-label="Settings"
          className="hover:bg-accent/50"
        >
          <Settings className="h-4 w-4 md:h-5 md:w-5" />
        </Button>
        <ThemeToggle />
        {isAuthenticated ? (
          <div className="flex items-center gap-2">
            <span className="text-xs md:text-sm text-muted-foreground hidden md:inline">
              {user?.username}
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              data-testid="button-logout"
              className="hover:bg-destructive/10 hover:text-destructive"
            >
              <LogOut className="h-4 w-4 md:h-5 md:w-5" />
            </Button>
          </div>
        ) : (
          <>
            <AuthModal isOpen={!isAuthenticated && showAuthModal} onClose={() => setShowAuthModal(false)} />
            <Button
              variant="ghost"
              size="icon"
              data-testid="button-login"
              onClick={() => setShowAuthModal(true)}
              aria-label="Login"
              className="hover:bg-primary/10 hover:text-primary"
            >
              <LogIn className="h-4 w-4 md:h-5 md:w-5" />
            </Button>
          </>
        )}
      </div>
    </header>
  );
}
