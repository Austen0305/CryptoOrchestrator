/**
 * Intersection Observer Hook
 * React hook for Intersection Observer API
 */

import { useEffect, useRef, useState, RefObject } from 'react';

interface UseIntersectionObserverOptions extends IntersectionObserverInit {
  triggerOnce?: boolean;
}

export function useIntersectionObserver<T extends HTMLElement = HTMLElement>(
  options: UseIntersectionObserverOptions = {}
): [RefObject<T>, boolean] {
  const { triggerOnce = false, ...observerOptions } = options;
  const elementRef = useRef<T>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(([entry]) => {
      if (!entry) return;
      const isIntersecting = entry.isIntersecting;
      setIsIntersecting(isIntersecting);

      if (triggerOnce && isIntersecting && !hasTriggeredRef.current) {
        hasTriggeredRef.current = true;
        observer.disconnect();
      }
    }, observerOptions);

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [observerOptions, triggerOnce]);

  return [elementRef, isIntersecting];
}
