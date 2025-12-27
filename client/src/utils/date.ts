/**
 * Date Utilities
 * Common date formatting and manipulation functions
 */

/**
 * Format date relative to now
 */
export function formatRelativeTime(date: Date | string | number): string {
  const now = new Date();
  const then = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  const diff = now.getTime() - then.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const weeks = Math.floor(days / 7);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);

  if (years > 0) return `${years} year${years > 1 ? 's' : ''} ago`;
  if (months > 0) return `${months} month${months > 1 ? 's' : ''} ago`;
  if (weeks > 0) return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
  if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  return 'Just now';
}

/**
 * Check if date is today
 */
export function isToday(date: Date | string | number): boolean {
  const today = new Date();
  const checkDate = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  
  return (
    today.getDate() === checkDate.getDate() &&
    today.getMonth() === checkDate.getMonth() &&
    today.getFullYear() === checkDate.getFullYear()
  );
}

/**
 * Check if date is yesterday
 */
export function isYesterday(date: Date | string | number): boolean {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const checkDate = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  
  return (
    yesterday.getDate() === checkDate.getDate() &&
    yesterday.getMonth() === checkDate.getMonth() &&
    yesterday.getFullYear() === checkDate.getFullYear()
  );
}

/**
 * Get start of day
 */
export function startOfDay(date: Date = new Date()): Date {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * Get end of day
 */
export function endOfDay(date: Date = new Date()): Date {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return d;
}

