/**
 * Trading Mode Context
 * Manages paper trading vs real money trading mode
 */

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { apiRequest } from '@/lib/apiClient';
import { toast } from '@/components/ui/use-toast';

type TradingMode = 'paper' | 'real';

interface TradingModeContextType {
  mode: TradingMode;
  setMode: (mode: TradingMode, requireConfirmation?: boolean) => Promise<void>;
  isRealMoney: boolean;
  isPaperTrading: boolean;
  canSwitchToRealMoney: boolean;
  checkRealMoneyRequirements: () => Promise<boolean>;
}

const TradingModeContext = createContext<TradingModeContextType | undefined>(undefined);

interface TradingModeProviderProps {
  children: ReactNode;
}

export function TradingModeProvider({ children }: TradingModeProviderProps) {
  const { user } = useAuth();
  const [mode, setModeState] = useState<TradingMode>('paper');
  const [canSwitchToRealMoney, setCanSwitchToRealMoney] = useState(false);

  // Load trading mode from user preferences
  useEffect(() => {
    const loadTradingMode = async () => {
      try {
        const storedMode = localStorage.getItem('tradingMode') as TradingMode | null;
        if (storedMode && (storedMode === 'paper' || storedMode === 'real')) {
          setModeState(storedMode);
        }

        // Check if user can switch to real money
        if (user) {
          const canSwitch = await checkRealMoneyRequirements();
          setCanSwitchToRealMoney(canSwitch);
        }
      } catch (error) {
        console.error('Failed to load trading mode:', error);
      }
    };

    loadTradingMode();
  }, [user]);

  // Check if user meets requirements for real money trading
  const checkRealMoneyRequirements = useCallback(async (): Promise<boolean> => {
    if (!user) return false;

    try {
      const response = await apiRequest<{
        hasApiKeys: boolean;
        has2FA: boolean;
        hasVerifiedEmail: boolean;
        hasAcceptedTerms: boolean;
      }>('/api/trading/check-real-money-requirements', {
        method: 'GET',
      });

      return (
        response.hasApiKeys &&
        response.has2FA &&
        response.hasVerifiedEmail &&
        response.hasAcceptedTerms
      );
    } catch (error) {
      console.error('Failed to check real money requirements:', error);
      return false;
    }
  }, [user]);

  // Set trading mode with confirmation for real money
  const setMode = useCallback(
    async (newMode: TradingMode, requireConfirmation: boolean = true) => {
      // If switching to real money, check requirements
      if (newMode === 'real' && requireConfirmation) {
        const canSwitch = await checkRealMoneyRequirements();
        if (!canSwitch) {
          toast({
            title: 'Cannot Switch to Real Money Trading',
            description:
              'Please configure exchange API keys, enable 2FA, verify your email, and accept the terms of service.',
            variant: 'destructive',
          });
          return;
        }

        // Show confirmation dialog
        const confirmed = window.confirm(
          '⚠️ WARNING: You are about to switch to REAL MONEY trading.\n\n' +
            'This will execute trades using your actual funds on connected exchanges.\n\n' +
            'Make sure you have:\n' +
            '1. Configured exchange API keys with trading permissions\n' +
            '2. Enabled 2FA on your account\n' +
            '3. Verified your email address\n' +
            '4. Accepted the terms of service\n' +
            '5. Tested your strategies in paper trading mode\n\n' +
            'Do you want to continue?'
        );

        if (!confirmed) {
          return;
        }
      }

      // Update state and localStorage
      setModeState(newMode);
      localStorage.setItem('tradingMode', newMode);

      // Log mode switch for audit
      try {
        await apiRequest('/api/trading/log-mode-switch', {
          method: 'POST',
          body: JSON.stringify({
            mode: newMode,
            timestamp: new Date().toISOString(),
          }),
        });
      } catch (error) {
        console.error('Failed to log mode switch:', error);
      }

      toast({
        title: `Switched to ${newMode === 'real' ? 'Real Money' : 'Paper'} Trading`,
        description:
          newMode === 'real'
            ? 'All trades will now use real funds. Trade carefully!'
            : 'All trades are now simulated. No real funds will be used.',
      });
    },
    [checkRealMoneyRequirements]
  );

  const value: TradingModeContextType = {
    mode,
    setMode,
    isRealMoney: mode === 'real',
    isPaperTrading: mode === 'paper',
    canSwitchToRealMoney,
    checkRealMoneyRequirements,
  };

  return (
    <TradingModeContext.Provider value={value}>
      {children}
    </TradingModeContext.Provider>
  );
}

/**
 * Hook to use trading mode
 */
export function useTradingMode() {
  const context = useContext(TradingModeContext);
  if (!context) {
    throw new Error('useTradingMode must be used within TradingModeProvider');
  }
  return context;
}

