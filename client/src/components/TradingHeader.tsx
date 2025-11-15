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
      } catch {}
    };
    window.addEventListener('auth:expired', handler);
    return () => window.removeEventListener('auth:expired', handler);
  }, []);

  // If user becomes authenticated while modal is open, close it
  useEffect(() => {
    if (isAuthenticated && showAuthModal) setShowAuthModal(false);
  }, [isAuthenticated, showAuthModal]);

  return (
    <header className="h-16 border-b bg-card flex items-center justify-between px-6">
      <div className="flex items-center gap-6">
        <h1 className="text-xl font-bold">CryptoML</h1>
        <Badge variant={connected ? "default" : "secondary"} data-testid="badge-connection">
          {connected ? "Connected" : "Disconnected"}
        </Badge>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-sm text-muted-foreground">Total Balance</p>
          <p className="text-lg font-mono font-bold" data-testid="text-balance">
            ${balance.toLocaleString()}
          </p>
        </div>
        <div className="h-8 w-px bg-border" />
        {isAuthenticated && <NotificationCenter />}
        <Button variant="ghost" size="icon" data-testid="button-settings" aria-label="Settings">
          <Settings className="h-5 w-5" />
        </Button>
        <ThemeToggle />
        {isAuthenticated ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {user?.username}
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              data-testid="button-logout"
            >
              <LogOut className="h-5 w-5" />
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
            >
              <LogIn className="h-5 w-5" />
            </Button>
          </>
        )}
      </div>
    </header>
  );
}
