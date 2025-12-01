/**
 * Prevents scrolling past content in main-content area
 * Simplified - only prevents overscroll at boundaries, allows normal scrolling
 */

export function preventScrollPastContent() {
  if (typeof window === 'undefined') return;
  
  const main = document.getElementById('main-content');
  if (!main) return;
  
  // Only prevent wheel events at strict boundaries - allow normal scrolling everywhere else
  main.addEventListener('wheel', (e) => {
    const currentScrollTop = main.scrollTop;
    const scrollHeight = main.scrollHeight;
    const clientHeight = main.clientHeight;
    const maxScroll = Math.max(0, scrollHeight - clientHeight);
    
    // Only prevent if we're at the exact boundary
    const atBottom = currentScrollTop >= maxScroll - 1;
    const atTop = currentScrollTop <= 1;
    
    // If at bottom and scrolling down, prevent overscroll
    if (atBottom && e.deltaY > 0) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
    
    // If at top and scrolling up, prevent overscroll  
    if (atTop && e.deltaY < 0) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
    
    // Allow all other scrolling - don't interfere
  }, { passive: false });
  
  // Handle touch events for mobile (only prevent at boundaries)
  let touchStartY = 0;
  main.addEventListener('touchstart', (e) => {
    touchStartY = e.touches[0].clientY;
  }, { passive: true });
  
  main.addEventListener('touchmove', (e) => {
    const currentScrollTop = main.scrollTop;
    const scrollHeight = main.scrollHeight;
    const clientHeight = main.clientHeight;
    const maxScroll = scrollHeight - clientHeight;
    const touchY = e.touches[0].clientY;
    const deltaY = touchStartY - touchY;
    
    // Only prevent if at boundaries and trying to scroll beyond
    if (currentScrollTop >= maxScroll && deltaY < 0) {
      e.preventDefault();
      return false;
    }
    
    if (currentScrollTop <= 0 && deltaY > 0) {
      e.preventDefault();
      return false;
    }
  }, { passive: false });
}
