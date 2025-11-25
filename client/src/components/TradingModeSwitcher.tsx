/**
 * Trading Mode Switcher Component
 * Allows users to switch between paper trading and real money trading
 */

import { useTradingMode } from '@/contexts/TradingModeContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { AlertTriangle, CheckCircle2, Settings, Wallet } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';

export function TradingModeSwitcher() {
  const { mode, setMode, isRealMoney, isPaperTrading, canSwitchToRealMoney, checkRealMoneyRequirements } = useTradingMode();
  const { user } = useAuth();
  const [isChecking, setIsChecking] = useState(false);
  const [showDialog, setShowDialog] = useState(false);

  const handleModeSwitch = async (newMode: 'paper' | 'real') => {
    if (newMode === 'real') {
      setIsChecking(true);
      const canSwitch = await checkRealMoneyRequirements();
      setIsChecking(false);

      if (!canSwitch) {
        setShowDialog(true);
        return;
      }

      // Show confirmation dialog
      setShowDialog(true);
    } else {
      // Switching to paper - no confirmation needed
      await setMode('paper', false);
    }
  };

  const handleConfirmRealMoney = async () => {
    setShowDialog(false);
    await setMode('real', true);
  };

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <Label htmlFor="trading-mode" className="text-sm font-medium">
          Trading Mode:
        </Label>
        <div className="flex items-center gap-2">
          <Badge
            variant={isPaperTrading ? 'default' : 'outline'}
            className={isPaperTrading ? 'bg-blue-500' : ''}
          >
            Paper
          </Badge>
          <Switch
            id="trading-mode"
            checked={isRealMoney}
            onCheckedChange={(checked) => handleModeSwitch(checked ? 'real' : 'paper')}
            disabled={isChecking || !user}
          />
          <Badge
            variant={isRealMoney ? 'destructive' : 'outline'}
            className={isRealMoney ? 'bg-red-500' : ''}
          >
            Real Money
          </Badge>
        </div>
      </div>

      {isRealMoney && (
        <Badge variant="destructive" className="animate-pulse">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Live Trading
        </Badge>
      )}

      {isPaperTrading && (
        <Badge variant="secondary">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          Simulated
        </Badge>
      )}

      <AlertDialog open={showDialog} onOpenChange={setShowDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Switch to Real Money Trading?
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <p className="font-semibold text-red-900 dark:text-red-200 mb-2">
                  ⚠️ WARNING: This will enable REAL MONEY trading
                </p>
                <p className="text-sm text-red-800 dark:text-red-300">
                  All trades will be executed using your actual funds on connected exchanges.
                  You could lose money if trades go against you.
                </p>
              </div>

              {!canSwitchToRealMoney && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <p className="font-semibold text-yellow-900 dark:text-yellow-200 mb-2">
                    Requirements Not Met
                  </p>
                  <ul className="text-sm text-yellow-800 dark:text-yellow-300 list-disc list-inside space-y-1">
                    <li>Configure exchange API keys with trading permissions</li>
                    <li>Enable 2FA on your account</li>
                    <li>Verify your email address</li>
                    <li>Accept the terms of service</li>
                  </ul>
                </div>
              )}

              {canSwitchToRealMoney && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <p className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                    Before you proceed:
                  </p>
                  <ul className="text-sm text-blue-800 dark:text-blue-300 list-disc list-inside space-y-1">
                    <li>Test your strategies in paper trading mode first</li>
                    <li>Start with small position sizes</li>
                    <li>Monitor your trades closely</li>
                    <li>Set proper stop-loss and take-profit levels</li>
                    <li>Never risk more than you can afford to lose</li>
                  </ul>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            {canSwitchToRealMoney ? (
              <AlertDialogAction
                onClick={handleConfirmRealMoney}
                className="bg-red-500 hover:bg-red-600 text-white"
              >
                <Wallet className="h-4 w-4 mr-2" />
                Enable Real Money Trading
              </AlertDialogAction>
            ) : (
              <AlertDialogAction
                onClick={() => {
                  setShowDialog(false);
                  // Navigate to settings
                  window.location.href = '/settings';
                }}
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                <Settings className="h-4 w-4 mr-2" />
                Go to Settings
              </AlertDialogAction>
            )}
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

