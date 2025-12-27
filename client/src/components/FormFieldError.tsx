/**
 * Form Field Error Component
 * Provides consistent error display for form fields with smooth animations
 */

import React from "react";
import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface FormFieldErrorProps {
  error?: string;
  className?: string;
  showIcon?: boolean;
  animate?: boolean;
}

export const FormFieldError = React.memo(function FormFieldError({
  error,
  className,
  showIcon = true,
  animate = true,
}: FormFieldErrorProps) {
  if (!error) return null;

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 text-sm text-destructive mt-1",
        animate && "animate-fade-in",
        className
      )}
      role="alert"
      aria-live="polite"
    >
      {showIcon && (
        <AlertCircle
          className="h-3.5 w-3.5 flex-shrink-0 animate-pulse"
          aria-hidden="true"
        />
      )}
      <span>{error}</span>
    </div>
  );
});

