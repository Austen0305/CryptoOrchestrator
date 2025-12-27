/**
 * Loading States Component
 * Enhanced loading states with shimmer effects and progress indicators
 */
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface LoadingSkeletonProps {
  className?: string;
  variant?: "default" | "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
  animate?: boolean;
}

export function LoadingSkeleton({
  className,
  variant = "default",
  width,
  height,
  animate = true,
}: LoadingSkeletonProps) {
  const baseClasses = "skeleton-modern rounded";
  
  const variantClasses = {
    default: "",
    text: "h-4",
    circular: "rounded-full",
    rectangular: "rounded-md",
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  if (height) style.height = typeof height === "number" ? `${height}px` : height;

  return (
    <div
      className={cn(baseClasses, variantClasses[variant], !animate && "animate-none", className)}
      style={style}
    />
  );
}

interface ProgressIndicatorProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  variant?: "default" | "success" | "warning" | "danger";
}

export function ProgressIndicator({
  value,
  max = 100,
  className,
  showLabel = false,
  variant = "default",
}: ProgressIndicatorProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const variantClasses = {
    default: "bg-primary",
    success: "bg-green-500",
    warning: "bg-yellow-500",
    danger: "bg-red-500",
  };

  return (
    <div className={cn("space-y-2", className)}>
      {showLabel && (
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Progress</span>
          <span>{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="modern-progress">
        <div
          className={cn("modern-progress-bar", variantClasses[variant])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Spinner({ size = "md", className }: SpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  };

  return (
    <Loader2
      className={cn("animate-spin text-primary", sizeClasses[size], className)}
    />
  );
}

interface LoadingOverlayProps {
  isLoading: boolean;
  children: React.ReactNode;
  spinner?: boolean;
  message?: string;
}

export function LoadingOverlay({ isLoading, children, spinner = true, message }: LoadingOverlayProps) {
  if (!isLoading) return <>{children}</>;

  return (
    <div className="relative">
      <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
        <div className="flex flex-col items-center gap-4">
          {spinner && <Spinner size="lg" />}
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
        </div>
      </div>
      {children}
    </div>
  );
}
