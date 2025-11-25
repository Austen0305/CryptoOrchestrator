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

export function SettingsPanel() {
  const { preferences, updatePreferences, resetPreferences, loading, error } = usePreferences();
  const { theme, setTheme } = useTheme();
  const { t, i18n } = useTranslation();
  const [saving, setSaving] = useState(false);

  const handleThemeChange = async (newTheme: "light" | "dark" | "system") => {
    try {
      await setTheme(newTheme);
    } catch (error) {
      console.error('Failed to update theme:', error);
    }
  };

  const handleNotificationChange = async (type: keyof UserPreferences['notifications'], enabled: boolean) => {
    if (!preferences) return;

    try {
      setSaving(true);
      await updatePreferences({
        notifications: {
          ...preferences.notifications,
          [type]: enabled
        }
      });
    } catch (error) {
      console.error('Failed to update notifications:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleUISettingChange = async (key: string, value: any) => {
    if (!preferences) return;

    try {
      setSaving(true);
      await updatePreferences({
        uiSettings: {
          ...preferences.uiSettings,
          [key]: value
        }
      });
    } catch (error) {
      console.error('Failed to update UI settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleTradingSettingChange = async (key: string, value: any) => {
    if (!preferences) return;

    try {
      setSaving(true);
      await updatePreferences({
        tradingSettings: {
          ...preferences.tradingSettings,
          [key]: value
        }
      });
    } catch (error) {
      console.error('Failed to update trading settings:', error);
    } finally {
      setSaving(false);
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
      console.error('Failed to change language:', error);
    }
  };

  const handleReset = async () => {
    if (confirm(t('common.resetConfirm'))) {
      try {
        setSaving(true);
        await resetPreferences();
      } catch (error) {
        console.error('Failed to reset preferences:', error);
      } finally {
        setSaving(false);
      }
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span className="ml-2">{t('common.loading')}</span>
        </CardContent>
      </Card>
    );
  }

  if (!preferences) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load preferences. Please try refreshing the page.
            </AlertDescription>
          </Alert>
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
              disabled={saving}
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
          {Object.entries(preferences.notifications).map(([type, enabled]) => (
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
                disabled={saving}
              />
            </div>
          ))}
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
              disabled={saving}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="refresh-interval">Refresh Interval (seconds)</Label>
            <Select
              value={preferences.uiSettings.refresh_interval.toString()}
              onValueChange={(value) => handleUISettingChange('refresh_interval', parseInt(value))}
              disabled={!preferences.uiSettings.auto_refresh || saving}
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
              disabled={saving}
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
              disabled={saving}
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
          disabled={saving}
        >
          {t('common.reset')}
        </Button>
      </div>
    </div>
  );
}