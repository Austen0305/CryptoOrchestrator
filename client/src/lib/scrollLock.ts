/**
 * Scroll lock utility to prevent double scrollbars
 * Ensures only main-content scrolls, not html/body
 */

export function lockScrollForAuthenticatedApp() {
  if (typeof window === 'undefined') return;

  const html = document.documentElement;
  const body = document.body;
  const root = document.getElementById('root');
  const main = document.getElementById('main-content');
  const isLanding = body?.classList.contains('landing-page-active') ||
                   html?.classList.contains('landing-page-active') ||
                   !main;

  if (isLanding) {
    // Landing page - allow scrolling by removing all inline styles
    html.style.cssText = '';
    body.style.cssText = '';
    if (root) {
      root.style.cssText = '';
    }
    return;
  }

  // Authenticated app - lock HTML and body
  const vh = window.innerHeight;
  
  // Remove problematic elements FIRST
  function removeProblematicElements() {
    // Remove Recharts measurement elements
    document.querySelectorAll('#recharts_measurement_span, [id^="recharts_"]').forEach(el => {
      try { el.remove(); } catch(e) {}
    });
    
    // Remove/hide sr-only elements positioned way off-screen
    document.querySelectorAll('.sr-only, #cf-help').forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.bottom > vh + 100 || rect.top < -100) {
        try { el.remove(); } catch(e) {
          (el as HTMLElement).style.cssText = 'display: none !important; position: absolute !important; top: -9999px !important; left: -9999px !important;';
        }
      }
    });
  }
  
  removeProblematicElements();
  
  // Use cssText for maximum priority (overrides everything)
  html.style.cssText = `
    height: ${vh}px !important;
    max-height: ${vh}px !important;
    min-height: ${vh}px !important;
    overflow: hidden !important;
    overflow-y: hidden !important;
    overflow-x: hidden !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    position: relative !important;
    box-sizing: border-box !important;
  `;
  
  body.style.cssText = `
    height: ${vh}px !important;
    max-height: ${vh}px !important;
    min-height: ${vh}px !important;
    overflow: hidden !important;
    overflow-y: hidden !important;
    overflow-x: hidden !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    position: relative !important;
    box-sizing: border-box !important;
  `;
  
  // Ensure root is properly constrained
  if (root) {
    root.style.cssText = `
      height: ${vh}px !important;
      max-height: ${vh}px !important;
      overflow: hidden !important;
      position: absolute !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      bottom: 0 !important;
      width: 100% !important;
      box-sizing: border-box !important;
    `;
  }
  
  // Fix main content overscroll-behavior
  if (main) {
    main.style.setProperty('overscroll-behavior', 'contain', 'important');
    main.style.setProperty('overscroll-behavior-y', 'contain', 'important');
    main.style.setProperty('overscroll-behavior-x', 'contain', 'important');
  }
  
  // Lock scroll position
  window.scrollTo(0, 0);
  html.scrollTop = 0;
  body.scrollTop = 0;
}

// Prevent scroll events on HTML/body
export function preventWindowScroll(e: Event) {
  const isLanding = document.body?.classList.contains('landing-page-active') ||
                   document.documentElement?.classList.contains('landing-page-active');
  
  // Allow all scrolling on landing page
  if (isLanding) return;
  
  const target = e.target as HTMLElement;
  const mainContent = document.getElementById('main-content');
  
  // Only prevent scroll on HTML/body, not on main-content or its children
  if (target === document.documentElement || target === document.body) {
    e.preventDefault();
    e.stopPropagation();
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    return false;
  }
  
  // If scrolling would move the window, prevent it (but only if not in main-content)
  if (!mainContent || !mainContent.contains(target)) {
    if (window.scrollY !== 0 || document.documentElement.scrollTop !== 0) {
      window.scrollTo(0, 0);
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    }
  }
}

// Prevent wheel events that would scroll the window
export function preventWindowWheel(e: WheelEvent) {
  const target = e.target as HTMLElement;
  const mainContent = document.getElementById('main-content');
  const isLanding = document.body?.classList.contains('landing-page-active');
  
  // Allow scrolling on landing page
  if (isLanding) return;
  
  // Allow scrolling within main-content or any element inside it
  if (mainContent) {
    // Check if target is main-content or any child of main-content
    let element: HTMLElement | null = target;
    while (element && element !== document.body) {
      if (element === mainContent || element.id === 'main-content') {
        // Allow scrolling within main-content
        return;
      }
      element = element.parentElement;
    }
  }
  
  // Only prevent scrolling if it would scroll the window/document
  // Check if scrolling would affect the window scroll position
  const isAtTop = window.scrollY === 0 && document.documentElement.scrollTop === 0;
  const isAtBottom = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight;
  
  // If we're at boundaries and trying to scroll further, prevent
  if ((isAtTop && e.deltaY < 0) || (isAtBottom && e.deltaY > 0)) {
    e.preventDefault();
    e.stopPropagation();
  }
  
  // Always prevent window scrolling for HTML/body directly
  if (target === document.documentElement || target === document.body) {
    e.preventDefault();
    e.stopPropagation();
  }
}

