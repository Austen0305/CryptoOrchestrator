/**
 * Animated Card Component
 * Card with hover effects, tilt animations, and gradient borders
 */
import { ReactNode } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface AnimatedCardProps {
  children: ReactNode;
  className?: string;
  title?: string;
  description?: string;
  variant?: "default" | "glass" | "gradient-border" | "tilt";
  hoverEffect?: "lift" | "glow" | "scale" | "none";
}

export function AnimatedCard({
  children,
  className,
  title,
  description,
  variant = "default",
  hoverEffect = "lift",
}: AnimatedCardProps) {
  const variantClasses = {
    default: "",
    glass: "glass-premium",
    "gradient-border": "border-gradient-animated",
    tilt: "card-interactive",
  };

  const hoverClasses = {
    none: "",
    lift: "hover-lift",
    glow: "glow-on-hover",
    scale: "hover:scale-105 transition-transform duration-300",
  };

  return (
    <Card
      className={cn(
        "transition-all duration-300",
        variantClasses[variant],
        hoverClasses[hoverEffect],
        className
      )}
    >
      {(title || description) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      <CardContent>{children}</CardContent>
    </Card>
  );
}
