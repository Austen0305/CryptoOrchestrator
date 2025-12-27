/**
 * Responsive Layout Component
 * Handles responsive grid layouts and viewport changes with mobile optimization
 */
import React, { ReactNode, useEffect, useState, useMemo } from "react";
import { cn } from "@/lib/utils";

interface ResponsiveLayoutProps {
  children: ReactNode;
  className?: string;
  columns?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  gap?: "sm" | "md" | "lg";
}

export const ResponsiveLayout = React.memo(function ResponsiveLayout({
  children,
  className,
  columns = { mobile: 1, tablet: 2, desktop: 3 },
  gap = "md",
}: ResponsiveLayoutProps) {
  const gapClasses = useMemo(() => ({
    sm: "gap-2",
    md: "gap-4",
    lg: "gap-6",
  }), []);

  return (
    <div
      className={cn(
        "grid",
        `grid-cols-${columns.mobile || 1}`,
        `sm:grid-cols-${columns.tablet || 2}`,
        `lg:grid-cols-${columns.desktop || 3}`,
        gapClasses[gap],
        className
      )}
      role="grid"
      aria-label="Responsive grid layout"
    >
      {children}
    </div>
  );
});

interface ResponsiveContainerProps {
  children: ReactNode;
  className?: string;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
  padding?: boolean;
}

export const ResponsiveContainer = React.memo(function ResponsiveContainer({
  children,
  className,
  maxWidth = "full",
  padding = true,
}: ResponsiveContainerProps) {
  const maxWidthClasses = useMemo(() => ({
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
    "2xl": "max-w-2xl",
    full: "max-w-full",
  }), []);

  return (
    <div
      className={cn(
        "w-full mx-auto",
        maxWidthClasses[maxWidth],
        padding && "px-4 sm:px-6 lg:px-8 safe-area-inset-left safe-area-inset-right",
        className
      )}
    >
      {children}
    </div>
  );
});

interface ViewportDetectorProps {
  onViewportChange?: (viewport: "mobile" | "tablet" | "desktop") => void;
}

export function useViewport() {
  const [viewport, setViewport] = useState<"mobile" | "tablet" | "desktop">("desktop");

  useEffect(() => {
    const updateViewport = () => {
      const width = window.innerWidth;
      if (width < 640) {
        setViewport("mobile");
      } else if (width < 1024) {
        setViewport("tablet");
      } else {
        setViewport("desktop");
      }
    };

    updateViewport();
    window.addEventListener("resize", updateViewport);
    return () => window.removeEventListener("resize", updateViewport);
  }, []);

  return viewport;
}
