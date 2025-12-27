/**
 * Apply enhanced UI styles directly to DOM elements
 * This ensures styles are applied even if CSS is overridden
 */

export function applyEnhancedStyles() {
  // Apply to all cards
  document.querySelectorAll('.shadcn-card, [class*="shadcn-card"]').forEach(card => {
    const el = card as HTMLElement;
    el.style.setProperty('border-width', '3px', 'important');
    el.style.setProperty('border-style', 'solid', 'important');
    el.style.setProperty('border-radius', '1.25rem', 'important');
    el.style.setProperty('box-shadow', '0px 16px 32px -8px rgba(0, 0, 0, 0.5), 0px 8px 16px -8px rgba(0, 0, 0, 0.5)', 'important');
    el.style.setProperty('padding', '1.5rem', 'important');
    el.style.setProperty('transition', 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)', 'important');
  });
  
  // Apply to header
  const header = document.querySelector('header');
  if (header) {
    const el = header as HTMLElement;
    el.style.setProperty('border-bottom-width', '4px', 'important');
    el.style.setProperty('border-bottom-style', 'solid', 'important');
    el.style.setProperty('min-height', '5rem', 'important');
    el.style.setProperty('height', '5rem', 'important');
    el.style.setProperty('box-shadow', '0px 12px 24px -6px rgba(0, 0, 0, 0.5), 0px 6px 12px -6px rgba(0, 0, 0, 0.5)', 'important');
  }
  
  // Apply gradient to h1
  const h1 = document.querySelector('header h1');
  if (h1) {
    const el = h1 as HTMLElement;
    el.style.setProperty('background-image', 'linear-gradient(135deg, hsl(217, 91%, 55%), hsl(217, 91%, 65%), hsl(217, 91%, 55%))', 'important');
    el.style.setProperty('-webkit-background-clip', 'text', 'important');
    el.style.setProperty('-webkit-text-fill-color', 'transparent', 'important');
    el.style.setProperty('background-clip', 'text', 'important');
    el.style.setProperty('font-weight', '900', 'important');
    el.style.setProperty('font-size', 'clamp(1.5rem, 4vw, 2.25rem)', 'important');
    el.style.setProperty('letter-spacing', '-0.02em', 'important');
  }
  
  // Apply to sidebar
  const sidebar = document.querySelector('aside, [data-sidebar]');
  if (sidebar) {
    const el = sidebar as HTMLElement;
    el.style.setProperty('border-right-width', '4px', 'important');
    el.style.setProperty('border-right-style', 'solid', 'important');
    el.style.setProperty('box-shadow', '8px 0px 16px -6px rgba(0, 0, 0, 0.4)', 'important');
  }
  
  // Apply to buttons - enhanced transitions
  document.querySelectorAll('button:not(:disabled)').forEach(button => {
    const el = button as HTMLElement;
    el.style.setProperty('transition', 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)', 'important');
    el.style.setProperty('cursor', 'pointer', 'important');
  });
  
  // Apply to badges - enhanced styling
  document.querySelectorAll('.badge-enhanced, [class*="badge"]').forEach(badge => {
    const el = badge as HTMLElement;
    el.style.setProperty('transition', 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)', 'important');
    el.style.setProperty('font-weight', '600', 'important');
    el.style.setProperty('letter-spacing', '0.025em', 'important');
  });
}

export function initEnhancedStyles() {
  // Apply immediately
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(applyEnhancedStyles, 100);
    });
  } else {
    setTimeout(applyEnhancedStyles, 100);
  }
  
  // Watch for new elements
  const observer = new MutationObserver(() => {
    applyEnhancedStyles();
  });
  
  observer.observe(document.body, { 
    childList: true, 
    subtree: true,
    attributes: true,
    attributeFilter: ['class']
  });
  
  // Reapply periodically to catch dynamically added elements
  setInterval(applyEnhancedStyles, 2000);
  
  // Also apply on window load
  window.addEventListener('load', () => {
    setTimeout(applyEnhancedStyles, 500);
  });
}

