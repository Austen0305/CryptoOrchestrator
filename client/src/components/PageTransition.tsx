/**
 * Page Transition Component
 * Provides smooth page transitions with fade and slide animations
 */

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { prefersReducedMotion } from "@/utils/performance";

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
  variant?: "fade" | "slide" | "scale" | "none";
  duration?: number;
}

export function PageTransition({
  children,
  className,
  variant = "fade",
  duration = 300,
}: PageTransitionProps) {
  const [isVisible, setIsVisible] = useState(false);
  const shouldAnimate = !prefersReducedMotion();

  useEffect(() => {
    // Trigger animation on mount
    if (shouldAnimate) {
      requestAnimationFrame(() => {
        setIsVisible(true);
      });
    } else {
      setIsVisible(true);
    }
  }, [shouldAnimate]);

  if (!shouldAnimate || variant === "none") {
    return <div className={className}>{children}</div>;
  }

  const variants = {
    fade: {
      initial: "opacity-0",
      animate: "opacity-100",
    },
    slide: {
      initial: "opacity-0 translate-y-4",
      animate: "opacity-100 translate-y-0",
    },
    scale: {
      initial: "opacity-0 scale-95",
      animate: "opacity-100 scale-100",
    },
  };

  const variantClasses = variants[variant];

  return (
    <div
      className={cn(
        "transition-all ease-out",
        isVisible ? variantClasses.animate : variantClasses.initial,
        className
      )}
      style={{
        transitionDuration: `${duration}ms`,
      }}
    >
      {children}
    </div>
  );
}

/**
 * Animated Container Component
 * Wraps content with entrance animation
 */
interface AnimatedContainerProps {
  children: React.ReactNode;
  delay?: number;
  className?: string;
  animation?: "fade-in-up" | "fade-in" | "scale-in" | "slide-in-right";
}

export function AnimatedContainer({
  children,
  delay = 0,
  className,
  animation = "fade-in-up",
}: AnimatedContainerProps) {
  const [isVisible, setIsVisible] = useState(false);
  const shouldAnimate = !prefersReducedMotion();

  useEffect(() => {
    if (shouldAnimate) {
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, delay);
      return () => clearTimeout(timer);
    } else {
      setIsVisible(true);
      return undefined;
    }
  }, [delay, shouldAnimate]);

  if (!shouldAnimate) {
    return <div className={className}>{children}</div>;
  }

  const animationClasses = {
    "fade-in-up": "animate-fade-in-up",
    "fade-in": "animate-fade-in",
    "scale-in": "animate-scale-in",
    "slide-in-right": "animate-slide-in-right",
  };

  return (
    <div
      className={cn(
        !isVisible && "opacity-0",
        isVisible && animationClasses[animation],
        className
      )}
    >
      {children}
    </div>
  );
}
