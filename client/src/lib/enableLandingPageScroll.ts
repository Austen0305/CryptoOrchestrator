/**
 * Force enable scrolling on landing pages
 * This is called to ensure landing pages can always scroll
 */

export function enableLandingPageScroll() {
  if (typeof window === 'undefined') return;
  
  const isLanding = document.body?.classList.contains('landing-page-active') ||
                   document.documentElement?.classList.contains('landing-page-active');
  
  if (!isLanding) return;
  
  const html = document.documentElement;
  const body = document.body;
  const root = document.getElementById('root');
  
  // Remove ALL inline styles that might block scrolling
  html.style.cssText = '';
  body.style.cssText = '';
  if (root) {
    root.style.cssText = '';
  }
  
  // Ensure scrolling is explicitly enabled
  html.style.setProperty('overflow-y', 'auto', 'important');
  html.style.setProperty('height', 'auto', 'important');
  body.style.setProperty('overflow-y', 'auto', 'important');
  body.style.setProperty('height', 'auto', 'important');
}

