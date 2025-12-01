import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTranslation } from "react-i18next";
import { useTheme } from "@/components/ThemeProvider";
import { Save, Bell, Shield, Palette, Globe, Key, FileText, LogOut } from "lucide-react";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/useAuth";
import ExchangeKeys from "./ExchangeKeys";
import { AuditLogViewer } from "@/components/AuditLogViewer";
import { Wallet } from "@/components/Wallet";
import { PaymentMethods } from "@/components/PaymentMethods";
import { CryptoTransfer } from "@/components/CryptoTransfer";
import { Staking } from "@/components/Staking";

export default function Settings() {
  const { i18n } = useTranslation();
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const { logout } = useAuth();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);

  const handleSave = () => {
    toast({
      title: "Settings Saved",
      description: "Your preferences have been updated successfully.",
    });
  };

  return (
    <div className="space-y-6 w-full min-h-0">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Settings</h1>
        <p className="text-muted-foreground text-base">
          Manage your account preferences and application settings
        </p>
      </div>

      <Tabs defaultValue="general" className="space-y-4 min-h-0">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="trading">Trading</TabsTrigger>
          <TabsTrigger value="exchange-keys">
            <Key className="h-4 w-4 mr-2" />
            Exchange Keys
          </TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="wallet">Wallet</TabsTrigger>
          <TabsTrigger value="payment-methods">Payment Methods</TabsTrigger>
          <TabsTrigger value="crypto-transfer">Crypto Transfer</TabsTrigger>
          <TabsTrigger value="staking">Staking</TabsTrigger>
          <TabsTrigger value="audit-logs">
            <FileText className="h-4 w-4 mr-2" />
            Audit Logs
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          <Card className="border-blue-500 border rounded-xl bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5" />
                Appearance
              </CardTitle>
              <CardDescription>
                Customize the look and feel of the application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="theme">Theme</Label>
                <Select value={theme} onValueChange={setTheme}>
                  <SelectTrigger id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <Select value={i18n.language} onValueChange={(lang) => i18n.changeLanguage(lang)}>
                  <SelectTrigger id="language">
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

          <Card className="border-blue-500 border rounded-xl bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5" />
                Regional Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Select defaultValue="utc">
                  <SelectTrigger id="timezone">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="utc">UTC</SelectItem>
                    <SelectItem value="est">Eastern Time (EST)</SelectItem>
                    <SelectItem value="pst">Pacific Time (PST)</SelectItem>
                    <SelectItem value="cet">Central European Time (CET)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="currency">Display Currency</Label>
                <Select defaultValue="usd">
                  <SelectTrigger id="currency">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="usd">USD ($)</SelectItem>
                    <SelectItem value="eur">EUR (€)</SelectItem>
                    <SelectItem value="gbp">GBP (£)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trading" className="space-y-4">
          <Card className="border-blue-500 border rounded-xl bg-card">
            <CardHeader>
              <CardTitle>Trading Preferences</CardTitle>
              <CardDescription>
                Configure your default trading settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="default-pair">Default Trading Pair</Label>
                <Select defaultValue="btc-usd">
                  <SelectTrigger id="default-pair">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="btc-usd">BTC/USD</SelectItem>
                    <SelectItem value="eth-usd">ETH/USD</SelectItem>
                    <SelectItem value="sol-usd">SOL/USD</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="risk-level">Default Risk Level (%)</Label>
                <Input id="risk-level" type="number" defaultValue="1.0" step="0.1" min="0.1" max="5.0" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="stop-loss">Default Stop Loss (%)</Label>
                <Input id="stop-loss" type="number" defaultValue="2.0" step="0.1" min="0.5" max="10.0" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="take-profit">Default Take Profit (%)</Label>
                <Input id="take-profit" type="number" defaultValue="5.0" step="0.1" min="1.0" max="20.0" />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Confirm Trades</Label>
                  <p className="text-sm text-muted-foreground">
                    Require confirmation before executing trades
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="exchange-keys">
          <ExchangeKeys />
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <Card className="border-blue-500 border rounded-xl bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Control when and how you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive alerts for important events
                  </p>
                </div>
                <Switch checked={notificationsEnabled} onCheckedChange={setNotificationsEnabled} />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Sound Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Play sound for notifications
                  </p>
                </div>
                <Switch checked={soundEnabled} onCheckedChange={setSoundEnabled} disabled={!notificationsEnabled} />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Trade Execution</Label>
                  <p className="text-sm text-muted-foreground">
                    Notify when trades are executed
                  </p>
                </div>
                <Switch defaultChecked disabled={!notificationsEnabled} />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Bot Status Changes</Label>
                  <p className="text-sm text-muted-foreground">
                    Notify when bots start or stop
                  </p>
                </div>
                <Switch defaultChecked disabled={!notificationsEnabled} />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Market Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Notify on significant market movements
                  </p>
                </div>
                <Switch disabled={!notificationsEnabled} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-4">
          <Card className="border-blue-500 border rounded-xl bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Security Settings
              </CardTitle>
              <CardDescription>
                Manage your account security and API keys
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api-key">Kraken API Key</Label>
                <Input id="api-key" type="password" placeholder="Enter your API key" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="api-secret">Kraken API Secret</Label>
                <Input id="api-secret" type="password" placeholder="Enter your API secret" />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Two-Factor Authentication</Label>
                  <p className="text-sm text-muted-foreground">
                    Add an extra layer of security
                  </p>
                </div>
                <Switch />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Session Timeout</Label>
                  <p className="text-sm text-muted-foreground">
                    Auto-logout after inactivity
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>

          <Card className="border-destructive/50 rounded-xl bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <LogOut className="w-5 h-5" />
                Account Actions
              </CardTitle>
              <CardDescription>
                Sign out of your account
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                variant="destructive"
                size="lg"
                onClick={async () => {
                  await logout();
                  toast({
                    title: "Logged Out",
                    description: "You have been successfully logged out.",
                  });
                }}
                className="w-full gap-2"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="wallet">
          <Wallet />
        </TabsContent>
        <TabsContent value="payment-methods">
          <PaymentMethods />
        </TabsContent>
        <TabsContent value="crypto-transfer">
          <CryptoTransfer />
        </TabsContent>
        <TabsContent value="staking">
          <Staking />
        </TabsContent>
        <TabsContent value="audit-logs">
          <AuditLogViewer />
        </TabsContent>
      </Tabs>

      <div className="flex justify-end">
        <Button onClick={handleSave} size="lg" className="gap-2">
          <Save className="w-4 h-4" />
          Save All Settings
        </Button>
      </div>
    </div>
  );
}
