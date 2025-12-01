import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import "./i18n";
import { initWebVitals } from "./lib/webVitals";
import { lockScrollForAuthenticatedApp, preventWindowScroll, preventWindowWheel } from "./lib/scrollLock";
import { preventScrollPastContent } from "./lib/preventScrollPast";
import { enableLandingPageScroll } from "./lib/enableLandingPageScroll";
import { initEnhancedStyles } from "./lib/applyEnhancedStyles";

// Helper function to check if we're on the landing page
function isLandingPage() {
  // Check for landing page class or if main-content doesn't exist (landing page)
  const hasLandingClass = document.body?.classList.contains('landing-page-active') ||
                         document.documentElement?.classList.contains('landing-page-active');
  const hasMainContent = !!document.getElementById('main-content');
  
  // It's a landing page if it has the class OR if main-content doesn't exist
  return hasLandingClass || !hasMainContent;
}

// Lock HTML/body to prevent double scrollbars - only when authenticated
if (typeof window !== 'undefined') {
  function removeRechartsElements() {
    // Remove Recharts measurement elements and other problematic elements
    // This is handled by scrollLock utility, but we also do it here for immediate effect
    document.querySelectorAll('#recharts_measurement_span, [id^="recharts_"]').forEach(el => {
      if (el && el.parentNode) {
        try {
          el.remove();
        } catch(e) {
          // Element already removed
        }
      }
    });
    
    // Also hide sr-only elements that are positioned way off-screen
    const vh = window.innerHeight;
    document.querySelectorAll('.sr-only, #cf-help').forEach(el => {
      if (el instanceof HTMLElement) {
        const rect = el.getBoundingClientRect();
        if (rect.bottom > vh + 1000 || rect.top < -1000) {
          el.style.setProperty('display', 'none', 'important');
          el.style.setProperty('position', 'absolute', 'important');
          el.style.setProperty('top', '-9999px', 'important');
          el.style.setProperty('left', '-9999px', 'important');
        }
      }
    });
  }
  
  // Always enable landing page scroll first (run immediately and repeatedly)
  enableLandingPageScroll();
  
  // Track if scroll listeners are already attached (prevent duplicates)
  let scrollListenersAttached = false;
  
  // Scroll and wheel handlers (defined once, reused)
  const scrollHandler = (e: Event) => {
    if (isLandingPage()) return; // Don't prevent on landing page
    
    const target = e.target as HTMLElement;
    const mainContent = document.getElementById('main-content');
    
    // Allow scrolling within main-content - check if target is inside main-content
    if (mainContent) {
      let element: HTMLElement | null = target;
      while (element && element !== document.body) {
        if (element === mainContent || element.id === 'main-content') {
          return; // Allow scrolling
        }
        element = element.parentElement;
      }
    }
    
    // Only prevent scrolling on HTML/body
    preventWindowScroll(e);
  };
  
  const wheelHandler = (e: WheelEvent) => {
    if (isLandingPage()) return; // Don't prevent on landing page
    
    const target = e.target as HTMLElement;
    const mainContent = document.getElementById('main-content');
    
    // Allow scrolling within main-content - check if target is inside main-content
    if (mainContent) {
      let element: HTMLElement | null = target;
      while (element && element !== document.body) {
        if (element === mainContent || element.id === 'main-content') {
          return; // Allow scrolling
        }
        element = element.parentElement;
      }
    }
    
    // Only prevent window scrolling
    preventWindowWheel(e);
  };
  
  // Apply scroll configuration after React renders (wait for DOM)
  function applyScrollConfig() {
    // Always enable landing page scroll first
    enableLandingPageScroll();
    
    // Only apply scroll lock if NOT on landing page
    if (!isLandingPage()) {
      lockScrollForAuthenticatedApp();
      preventScrollPastContent();
      
      // Lock scroll position
      window.scrollTo(0, 0);
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
      
      // Only attach scroll listeners once
      if (!scrollListenersAttached) {
        document.addEventListener('scroll', scrollHandler, { capture: true, passive: false });
        document.addEventListener('wheel', wheelHandler, { capture: true, passive: false });
        scrollListenersAttached = true;
      }
    } else {
      // Landing page - remove listeners if they were attached
      if (scrollListenersAttached) {
        document.removeEventListener('scroll', scrollHandler, { capture: true } as any);
        document.removeEventListener('wheel', wheelHandler, { capture: true } as any);
        scrollListenersAttached = false;
      }
    }
  }
  
  removeRechartsElements();
  
  // Apply on DOM ready (after React renders)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      // Wait a bit for React to render and add classes
      setTimeout(() => {
        applyScrollConfig();
      }, 200);
      removeRechartsElements();
    });
  } else {
    // Already loaded, wait for React
    setTimeout(() => {
      applyScrollConfig();
    }, 200);
  }
  
  // Apply on window load
  window.addEventListener('load', () => {
    setTimeout(() => {
      applyScrollConfig();
    }, 300);
    removeRechartsElements();
  });
  
  // Watch for class changes (landing page toggle)
  const observer = new MutationObserver(() => {
    enableLandingPageScroll();
    setTimeout(() => {
      applyScrollConfig();
    }, 100);
    removeRechartsElements();
  });
  
  if (document.body) {
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ['class'],
      childList: true,
      subtree: true,
    });
  }
  
  if (document.documentElement) {
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });
  }
  
  // Also watch for resize to reapply
  window.addEventListener('resize', () => {
    enableLandingPageScroll();
    if (!isLandingPage()) {
      lockScrollForAuthenticatedApp();
    }
  });
  
  // Periodically ensure correct scroll state (focus on enabling landing page scroll)
  setInterval(() => {
    enableLandingPageScroll();
    if (!isLandingPage()) {
      // Only lock HTML/body scroll, not main-content
      lockScrollForAuthenticatedApp();
      
      // Only lock window scroll position (not main-content scrolling)
      if (window.scrollY !== 0 || document.documentElement.scrollTop !== 0) {
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      }
    }
    removeRechartsElements();
  }, 5000); // Check every 5 seconds
}

// Simple fix to ensure main content area is properly constrained
if (typeof window !== 'undefined') {
  function ensureMainContentScroll() {
    const main = document.getElementById('main-content');
    if (main && !isLandingPage()) {
      // Ensure main content is scrollable and doesn't extend beyond viewport
      const mainStyle = window.getComputedStyle(main);
      const mainRect = main.getBoundingClientRect();
      
      // If main content extends beyond viewport, ensure it's constrained
      if (mainRect.height > window.innerHeight) {
        // Already handled by CSS, but ensure flex is set
        if (mainStyle.flex !== '1 1 0%') {
          main.style.setProperty('flex', '1 1 0%', 'important');
        }
        if (mainStyle.minHeight !== '0px') {
          main.style.setProperty('min-height', '0', 'important');
        }
      }
      
      // Remove excessive padding from last child to prevent scrolling past content
      const lastChild = main.lastElementChild;
      if (lastChild && lastChild instanceof HTMLElement) {
        const lastChildStyle = window.getComputedStyle(lastChild);
        const marginBottom = parseFloat(lastChildStyle.marginBottom);
        if (marginBottom > 100) {
          lastChild.style.setProperty('margin-bottom', '2rem', 'important');
        }
      }
    }
  }
  
  // Run after DOM is ready and after a short delay for React to render
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(ensureMainContentScroll, 500);
    });
  } else {
    setTimeout(ensureMainContentScroll, 500);
  }
  
  // Also run on resize
  window.addEventListener('resize', ensureMainContentScroll);
}

// Register Service Worker only in production
// In development, unregister any existing service workers to prevent caching issues
if (import.meta.env.DEV && 'serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then((registrations) => {
    for (const registration of registrations) {
      registration.unregister().then((success) => {
        if (success) {
          console.log('ServiceWorker unregistered for development');
        }
      });
    }
  });
}

if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  const swUrl = new URL('/sw.js', import.meta.url);
  
  if (swUrl.protocol === 'https:' || location.hostname === 'localhost') {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register(swUrl)
        .then((registration) => {
          console.log('ServiceWorker registration successful:', registration);
        })
        .catch((error) => {
          console.warn('ServiceWorker registration failed:', error);
        });
    });
  }
}

// Initialize Web Vitals tracking
if (typeof window !== 'undefined') {
  initWebVitals();
  // Initialize enhanced UI styles
  initEnhancedStyles();
}

createRoot(document.getElementById("root")!).render(<App />);
