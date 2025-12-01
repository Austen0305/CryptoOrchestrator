import { useEffect, useState } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';

export function OfflineBanner() {
  const { isConnected } = useWebSocket();
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);

  useEffect(() => {
    const onOnline = () => setIsOnline(true);
    const onOffline = () => setIsOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  if (isOnline && isConnected) return null;

  return (
    <div className="w-full bg-amber-100 dark:bg-amber-900/30 border-b border-amber-300/50 dark:border-amber-800/50 text-amber-900 dark:text-amber-200 text-sm shadow-sm">
      <div className="max-w-screen-2xl mx-auto px-4 py-2.5 flex items-center gap-2.5">
        <WifiOff className="h-4 w-4 flex-shrink-0" />
        <span className="font-medium">
          {isOnline ? 'Reconnecting to live data…' : 'You are offline. Some data may be outdated.'}
        </span>
        <button 
          className="ml-auto inline-flex items-center gap-1.5 text-amber-900 dark:text-amber-100 hover:underline font-medium transition-colors px-2 py-1 rounded-md hover:bg-amber-200/50 dark:hover:bg-amber-800/50" 
          onClick={() => window.location.reload()}
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>
    </div>
  );
}
