/**
 * Mobile Menu Component
 * Bottom navigation for mobile devices with swipe gestures and enhanced touch targets
 */
import React, { useState, useCallback } from "react";
import { Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import {
  Home,
  TrendingUp,
  Wallet,
  Bot,
  Settings,
  Menu,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const navigationItems = [
  { path: "/dashboard", icon: Home, label: "Dashboard" },
  { path: "/trading", icon: TrendingUp, label: "Trading" },
  { path: "/wallets", icon: Wallet, label: "Wallets" },
  { path: "/bots", icon: Bot, label: "Bots" },
  { path: "/settings", icon: Settings, label: "Settings" },
];

export const MobileMenu = React.memo(function MobileMenu() {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const handleLinkClick = useCallback(() => {
    setIsOpen(false);
  }, []);

  return (
    <>
      {/* Bottom Navigation Bar - Mobile Only */}
      <nav 
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-md border-t border-border safe-area-inset-bottom"
        role="navigation"
        aria-label="Mobile navigation"
      >
        <div className="flex items-center justify-around h-16 px-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex flex-col items-center justify-center gap-1 flex-1 min-h-[44px] min-w-[44px] rounded-lg transition-colors touch-manipulation",
                  isActive
                    ? "text-primary bg-primary/10"
                    : "text-muted-foreground active:text-foreground active:bg-muted/50"
                )}
                onClick={handleLinkClick}
                aria-label={item.label}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Hamburger Menu for Tablet */}
      <div className="hidden md:flex lg:hidden">
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild>
            <Button 
              variant="ghost" 
              size="icon"
              className="min-h-[44px] min-w-[44px] touch-manipulation"
              aria-label="Open navigation menu"
            >
              <Menu className="h-6 w-6" aria-hidden="true" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64">
            <nav className="flex flex-col gap-2 mt-8" role="navigation" aria-label="Tablet navigation">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors min-h-[44px] touch-manipulation",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground active:bg-muted active:text-foreground"
                    )}
                    onClick={handleLinkClick}
                    aria-label={item.label}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <Icon className="h-5 w-5" aria-hidden="true" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
});
