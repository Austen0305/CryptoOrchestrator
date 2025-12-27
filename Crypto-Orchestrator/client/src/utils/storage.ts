/**
 * Storage Utilities
 * Enhanced localStorage and sessionStorage with error handling
 */

/**
 * Safe localStorage get
 */
export function getLocalStorage<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue;

  try {
    const item = localStorage.getItem(key);
    if (item === null) return defaultValue;
    return JSON.parse(item) as T;
  } catch (error) {
    console.error(`Failed to get localStorage key "${key}":`, error);
    return defaultValue;
  }
}

/**
 * Safe localStorage set
 */
export function setLocalStorage<T>(key: string, value: T): boolean {
  if (typeof window === 'undefined') return false;

  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.error(`Failed to set localStorage key "${key}":`, error);
    return false;
  }
}

/**
 * Safe localStorage remove
 */
export function removeLocalStorage(key: string): boolean {
  if (typeof window === 'undefined') return false;

  try {
    localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.error(`Failed to remove localStorage key "${key}":`, error);
    return false;
  }
}

/**
 * Safe sessionStorage get
 */
export function getSessionStorage<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue;

  try {
    const item = sessionStorage.getItem(key);
    if (item === null) return defaultValue;
    return JSON.parse(item) as T;
  } catch (error) {
    console.error(`Failed to get sessionStorage key "${key}":`, error);
    return defaultValue;
  }
}

/**
 * Safe sessionStorage set
 */
export function setSessionStorage<T>(key: string, value: T): boolean {
  if (typeof window === 'undefined') return false;

  try {
    sessionStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.error(`Failed to set sessionStorage key "${key}":`, error);
    return false;
  }
}

/**
 * Clear all storage
 */
export function clearStorage(): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.clear();
    sessionStorage.clear();
  } catch (error) {
    console.error('Failed to clear storage:', error);
  }
}

