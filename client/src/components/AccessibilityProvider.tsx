/**
 * Accessibility Provider
 * Provides comprehensive accessibility features
 */

import { createContext, useContext, useEffect, ReactNode } from "react";

interface AccessibilityContextType {
  announce: (message: string, priority?: "polite" | "assertive") => void;
  skipToContent: () => void;
  reduceMotion: boolean;
  highContrast: boolean;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

interface AccessibilityProviderProps {
  children: ReactNode;
}

export function AccessibilityProvider({ children }: AccessibilityProviderProps) {
  // Check for reduced motion preference
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Check for high contrast preference
  const highContrast = window.matchMedia("(prefers-contrast: high)").matches;

  // Announce messages to screen readers
  const announce = (message: string, priority: "polite" | "assertive" = "polite") => {
    const announcement = document.createElement("div");
    announcement.setAttribute("role", "status");
    announcement.setAttribute("aria-live", priority);
    announcement.setAttribute("aria-atomic", "true");
    announcement.className = "sr-only";
    announcement.textContent = message;

    document.body.appendChild(announcement);

    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  };

  // Skip to main content
  const skipToContent = () => {
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
      mainContent.focus();
      mainContent.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Apply reduced motion styles
  useEffect(() => {
    if (reduceMotion) {
      document.documentElement.classList.add("reduce-motion");
    } else {
      document.documentElement.classList.remove("reduce-motion");
    }
  }, [reduceMotion]);

  // Apply high contrast styles
  useEffect(() => {
    if (highContrast) {
      document.documentElement.classList.add("high-contrast");
    } else {
      document.documentElement.classList.remove("high-contrast");
    }
  }, [highContrast]);

  // Keyboard navigation improvements
  useEffect(() => {
    const handleKeyboardNavigation = (e: KeyboardEvent) => {
      // Escape key to close modals
      if (e.key === "Escape") {
        const activeModal = document.querySelector('[role="dialog"][aria-modal="true"]');
        if (activeModal) {
          const closeButton = activeModal.querySelector(
            'button[aria-label*="close" i], button[aria-label*="Close" i]'
          );
          if (closeButton instanceof HTMLElement) {
            closeButton.click();
          }
        }
      }

      // Tab navigation - trap focus in modals
      if (e.key === "Tab") {
        const activeModal = document.querySelector('[role="dialog"][aria-modal="true"]');
        if (activeModal) {
          const focusableElements = activeModal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          const firstElement = focusableElements[0] as HTMLElement;
          const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    document.addEventListener("keydown", handleKeyboardNavigation);
    return () => document.removeEventListener("keydown", handleKeyboardNavigation);
  }, []);

  const value: AccessibilityContextType = {
    announce,
    skipToContent,
    reduceMotion,
    highContrast,
  };

  return <AccessibilityContext.Provider value={value}>{children}</AccessibilityContext.Provider>;
}

/**
 * Hook to use accessibility features
 */
export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error("useAccessibility must be used within AccessibilityProvider");
  }
  return context;
}
