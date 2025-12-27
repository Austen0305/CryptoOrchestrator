import React, { useState } from 'react';
import type { UserPreferences } from '@shared/types';
import { usePreferences } from '../hooks/usePreferences';
import { useTheme } from './ThemeProvider';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { AlertCircle, Palette, Bell, Monitor, RefreshCw, Languages } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';
import { useTranslation } from 'react-i18next';
import { changeLanguage } from '../i18n';
import { LoadingSkeleton } from './LoadingSkeleton';
import { ErrorRetry } from './ErrorRetry';
import logger from '@/lib/logger';

export function SettingsPanel() {
  const { preferences, updatePreferences, resetPreferences, loading, error, refetch } = usePreferences();
  const { theme, setTheme } = useTheme();
  const { t, i18n } = useTranslation();

  const handleThemeChange = async (newTheme: "light" | "dark" | "system") => {
    try {
      await setTheme(newTheme);
    } catch (error) {
      logger.error('Failed to update theme', { error });
    }
  };

  const handleNotificationChange = async (type: keyof UserPreferences['notifications'], enabled: boolean) => {
    if (!preferences) return;

    try {
      await updatePreferences({
        notifications: {
          ...preferences.notifications,
          [type]: enabled
        }
      });
    } catch (error) {
      logger.error('Failed to update notifications', { error });
    }
  };

  const handleUISettingChange = async (key: string, value: string | number | boolean) => {
    if (!preferences) return;

    try {
      await updatePreferences({
        uiSettings: {
          ...preferences.uiSettings,
          [key]: value
        }
      });
    } catch (error) {
      logger.error('Failed to update UI settings', { error });
    }
  };

  const handleTradingSettingChange = async (key: string, value: string | number | boolean) => {
    if (!preferences) return;

    try {
      await updatePreferences({
        tradingSettings: {
          ...preferences.tradingSettings,
          [key]: value
        }
      });
    } catch (error) {
      logger.error('Failed to update trading settings', { error });
    }
  };

  const handleLanguageChange = async (newLanguage: string) => {
    try {
      await changeLanguage(newLanguage);
      // Also update preferences if language preference exists
      if (preferences) {
        await updatePreferences({
          uiSettings: {
            ...preferences.uiSettings,
            language: newLanguage
          }
        });
      }
    } catch (error) {
      logger.error('Failed to change language', { error });
    }
  };

  const handleReset = async () => {
    if (confirm(t('common.resetConfirm'))) {
      try {
        await resetPreferences();
      } catch (error) {
        logger.error('Failed to reset preferences', { error });
      }
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Settings</CardTitle>
          <CardDescription>Loading preferences...</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton count={5} className="h-16 w-full mb-4" />
        </CardContent>
      </Card>
    );
  }

  if (error || !preferences) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load preferences"
            message={error || "Preferences could not be loaded. Please try refreshing the page."}
            onRetry={() => refetch()}
            error={error ? new Error(error) : new Error("Failed to load preferences")}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Language Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Languages className="h-5 w-5" />
            {t('settings.language')}
          </CardTitle>
          <CardDescription>
            Choose your preferred language
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="language">{t('settings.language')}</Label>
            <Select value={i18n.language} onValueChange={handleLanguageChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="es">Español</SelectItem>
                <SelectItem value="ar">العربية</SelectItem>
                <SelectItem value="fr">Français</SelectItem>
                <SelectItem value="de">Deutsch</SelectItem>
                <SelectItem value="ja">日本語</SelectItem>
                <SelectItem value="zh">中文</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Theme Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            {t('settings.appearance')}
          </CardTitle>
          <CardDescription>
            Customize the look and feel of your interface
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="theme">{t('settings.theme')}</Label>
            <Select value={theme} onValueChange={handleThemeChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Compact Mode</Label>
              <p className="text-sm text-muted-foreground">
                Use a more compact layout
              </p>
            </div>
            <Switch
              checked={preferences.uiSettings.compact_mode}
              onCheckedChange={(checked) => handleUISettingChange('compact_mode', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            {t('settings.notifications')}
          </CardTitle>
          <CardDescription>
            Choose which notifications you'd like to receive
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {preferences?.notifications && typeof preferences.notifications === 'object' ? Object.entries(preferences.notifications).map(([type, enabled]) => (
            <div key={type} className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="capitalize">{type.replace('_', ' ')}</Label>
                <p className="text-sm text-muted-foreground">
                  Receive notifications for {type.replace('_', ' ')} events
                </p>
              </div>
              <Switch
                checked={enabled}
                onCheckedChange={(checked) => handleNotificationChange(type as keyof typeof preferences.notifications, checked)}
              />
            </div>
          )) : (
            <div className="text-sm text-muted-foreground py-4">No notification preferences available</div>
          )}
        </CardContent>
      </Card>

      {/* UI Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Interface
          </CardTitle>
          <CardDescription>
            Configure interface behavior and display options
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto Refresh</Label>
              <p className="text-sm text-muted-foreground">
                Automatically refresh data at regular intervals
              </p>
            </div>
            <Switch
              checked={preferences.uiSettings.auto_refresh}
              onCheckedChange={(checked) => handleUISettingChange('auto_refresh', checked)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="refresh-interval">Refresh Interval (seconds)</Label>
            <Select
              value={preferences.uiSettings.refresh_interval.toString()}
              onValueChange={(value) => handleUISettingChange('refresh_interval', parseInt(value))}
              disabled={!preferences.uiSettings.auto_refresh}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="15">15 seconds</SelectItem>
                <SelectItem value="30">30 seconds</SelectItem>
                <SelectItem value="60">1 minute</SelectItem>
                <SelectItem value="300">5 minutes</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="chart-period">Default Chart Period</Label>
            <Select
              value={preferences.uiSettings.default_chart_period}
              onValueChange={(value) => handleUISettingChange('default_chart_period', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1m">1 Minute</SelectItem>
                <SelectItem value="5m">5 Minutes</SelectItem>
                <SelectItem value="15m">15 Minutes</SelectItem>
                <SelectItem value="1H">1 Hour</SelectItem>
                <SelectItem value="4H">4 Hours</SelectItem>
                <SelectItem value="1D">1 Day</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Trading Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Trading</CardTitle>
          <CardDescription>
            Configure trading preferences and defaults
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Order Confirmations</Label>
              <p className="text-sm text-muted-foreground">
                Require confirmation before placing orders
              </p>
            </div>
            <Switch
              checked={preferences.tradingSettings.confirm_orders}
              onCheckedChange={(checked) => handleTradingSettingChange('confirm_orders', checked)}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Show Fees</Label>
              <p className="text-sm text-muted-foreground">
                Display trading fees in order details
              </p>
            </div>
            <Switch
              checked={preferences.tradingSettings.show_fees}
              onCheckedChange={(checked) => handleTradingSettingChange('show_fees', checked)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="order-type">Default Order Type</Label>
            <Select
              value={preferences.tradingSettings.default_order_type}
              onValueChange={(value) => handleTradingSettingChange('default_order_type', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="market">Market</SelectItem>
                <SelectItem value="limit">Limit</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Separator />

      <div className="flex justify-end">
        <Button
          variant="destructive"
          onClick={handleReset}
        >
          {t('common.reset')}
        </Button>
      </div>
    </div>
  );
}