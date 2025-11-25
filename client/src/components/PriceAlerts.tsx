import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Bell, Plus, Trash2, Edit, Volume2, TrendingUp, TrendingDown, Activity, CheckCircle2, XCircle } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

interface PriceAlert {
  id: string;
  symbol: string;
  condition: "above" | "below" | "change" | "volume";
  targetPrice?: number;
  changePercent?: number;
  volumeThreshold?: number;
  isActive: boolean;
  triggered: boolean;
  createdAt: Date;
  triggeredAt?: Date;
  channels: ("email" | "push" | "sms" | "telegram" | "discord")[];
  sound?: boolean;
}

export function PriceAlerts() {
  const [alerts, setAlerts] = useState<PriceAlert[]>([
    {
      id: "1",
      symbol: "BTC/USD",
      condition: "above",
      targetPrice: 50000,
      isActive: true,
      triggered: false,
      createdAt: new Date(2025, 10, 10),
      channels: ["push", "email"]
    },
    {
      id: "2",
      symbol: "ETH/USD",
      condition: "below",
      targetPrice: 2800,
      isActive: true,
      triggered: false,
      createdAt: new Date(2025, 10, 11),
      channels: ["push"]
    },
    {
      id: "3",
      symbol: "BTC/USD",
      condition: "change",
      changePercent: 5,
      isActive: true,
      triggered: true,
      createdAt: new Date(2025, 10, 8),
      triggeredAt: new Date(2025, 10, 12, 14, 30),
      channels: ["push", "email", "sms"]
    },
    {
      id: "4",
      symbol: "ETH/USD",
      condition: "volume",
      volumeThreshold: 1000000,
      isActive: false,
      triggered: false,
      createdAt: new Date(2025, 10, 5),
      channels: ["push"]
    }
  ]);

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingAlert, setEditingAlert] = useState<PriceAlert | null>(null);

  const activeAlerts = alerts.filter(a => a.isActive && !a.triggered);
  const triggeredAlerts = alerts.filter(a => a.triggered);
  const inactiveAlerts = alerts.filter(a => !a.isActive && !a.triggered);

  const toggleAlert = (id: string) => {
    setAlerts(alerts.map(alert =>
      alert.id === id ? { ...alert, isActive: !alert.isActive } : alert
    ));
  };

  const deleteAlert = (id: string) => {
    setAlerts(alerts.filter(alert => alert.id !== id));
  };

  const getConditionLabel = (alert: PriceAlert) => {
    switch (alert.condition) {
      case "above":
        return `Price above ${alert.targetPrice?.toLocaleString()}`;
      case "below":
        return `Price below ${alert.targetPrice?.toLocaleString()}`;
      case "change":
        return `${alert.changePercent}% change`;
      case "volume":
        return `Volume > ${alert.volumeThreshold?.toLocaleString()}`;
      default:
        return "";
    }
  };

  const getConditionIcon = (condition: string) => {
    switch (condition) {
      case "above":
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case "below":
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      case "change":
        return <Activity className="h-4 w-4 text-blue-500" />;
      case "volume":
        return <Volume2 className="h-4 w-4 text-orange-500" />;
      default:
        return <Bell className="h-4 w-4" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Price Alerts 2.0
            </CardTitle>
            <CardDescription>
              Advanced price alerts with complex conditions and multi-channel notifications
            </CardDescription>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-2" />
                New Alert
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>{editingAlert ? "Edit Alert" : "Create New Alert"}</DialogTitle>
                <DialogDescription>
                  Set up a price alert with complex conditions and notification channels.
                </DialogDescription>
              </DialogHeader>
              <AlertForm
                alert={editingAlert}
                onSave={(alert) => {
                  if (editingAlert) {
                    setAlerts(alerts.map(a => a.id === editingAlert.id ? alert : a));
                  } else {
                    setAlerts([...alerts, { ...alert, id: Date.now().toString(), createdAt: new Date() }]);
                  }
                  setIsDialogOpen(false);
                  setEditingAlert(null);
                }}
                onCancel={() => {
                  setIsDialogOpen(false);
                  setEditingAlert(null);
                }}
              />
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Active Alerts</div>
                  <div className="text-2xl font-bold">{activeAlerts.length}</div>
                </div>
                <Bell className="h-8 w-8 text-blue-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Triggered</div>
                  <div className="text-2xl font-bold">{triggeredAlerts.length}</div>
                </div>
                <CheckCircle2 className="h-8 w-8 text-green-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Inactive</div>
                  <div className="text-2xl font-bold">{inactiveAlerts.length}</div>
                </div>
                <XCircle className="h-8 w-8 text-muted-foreground opacity-50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Active Alerts */}
        {activeAlerts.length > 0 && (
          <div>
            <h3 className="font-semibold mb-3">Active Alerts</h3>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Channels</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {activeAlerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell className="font-medium">{alert.symbol}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getConditionIcon(alert.condition)}
                          <span className="text-sm">{getConditionLabel(alert)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {alert.channels.map(channel => (
                            <Badge key={channel} variant="secondary" className="text-xs">
                              {channel}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {format(alert.createdAt, "MMM dd, yyyy")}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={alert.isActive}
                            onCheckedChange={() => toggleAlert(alert.id)}
                          />
                          <Badge variant="default" className="bg-green-500">Active</Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingAlert(alert);
                              setIsDialogOpen(true);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteAlert(alert.id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {/* Triggered Alerts */}
        {triggeredAlerts.length > 0 && (
          <div>
            <h3 className="font-semibold mb-3">Triggered Alerts</h3>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Triggered</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {triggeredAlerts.map((alert) => (
                    <TableRow key={alert.id} className="bg-green-500/10">
                      <TableCell className="font-medium">{alert.symbol}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getConditionIcon(alert.condition)}
                          <span className="text-sm">{getConditionLabel(alert)}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {alert.triggeredAt ? format(alert.triggeredAt, "MMM dd, yyyy HH:mm") : "N/A"}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteAlert(alert.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {/* Inactive Alerts */}
        {inactiveAlerts.length > 0 && (
          <div>
            <h3 className="font-semibold mb-3">Inactive Alerts</h3>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {inactiveAlerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell className="font-medium">{alert.symbol}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getConditionIcon(alert.condition)}
                          <span className="text-sm">{getConditionLabel(alert)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={alert.isActive}
                            onCheckedChange={() => toggleAlert(alert.id)}
                          />
                          <Badge variant="secondary">Inactive</Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingAlert(alert);
                              setIsDialogOpen(true);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteAlert(alert.id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {alerts.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <Bell className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No alerts set up yet</p>
            <p className="text-sm">Create your first price alert to stay informed</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function AlertForm({ alert, onSave, onCancel }: { alert: PriceAlert | null; onSave: (alert: PriceAlert) => void; onCancel: () => void }) {
  const [symbol, setSymbol] = useState(alert?.symbol || "");
  const [condition, setCondition] = useState<PriceAlert["condition"]>(alert?.condition || "above");
  const [targetPrice, setTargetPrice] = useState(alert?.targetPrice?.toString() || "");
  const [changePercent, setChangePercent] = useState(alert?.changePercent?.toString() || "");
  const [volumeThreshold, setVolumeThreshold] = useState(alert?.volumeThreshold?.toString() || "");
  const [channels, setChannels] = useState<string[]>(alert?.channels || ["push"]);
  const [sound, setSound] = useState(alert?.sound || false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...alert!,
      symbol,
      condition,
      targetPrice: targetPrice ? parseFloat(targetPrice) : undefined,
      changePercent: changePercent ? parseFloat(changePercent) : undefined,
      volumeThreshold: volumeThreshold ? parseFloat(volumeThreshold) : undefined,
      channels: channels as any[],
      sound,
      isActive: alert?.isActive ?? true,
      triggered: alert?.triggered ?? false,
      createdAt: alert?.createdAt || new Date()
    });
  };

  const toggleChannel = (channel: string) => {
    setChannels(prev =>
      prev.includes(channel)
        ? prev.filter(c => c !== channel)
        : [...prev, channel]
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="symbol">Symbol</Label>
        <Input
          id="symbol"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="BTC/USD"
          required
        />
      </div>
      <div>
        <Label htmlFor="condition">Condition</Label>
        <Select value={condition} onValueChange={(value: any) => setCondition(value)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="above">Price Above</SelectItem>
            <SelectItem value="below">Price Below</SelectItem>
            <SelectItem value="change">Price Change %</SelectItem>
            <SelectItem value="volume">Volume Threshold</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {condition === "above" || condition === "below" ? (
        <div>
          <Label htmlFor="targetPrice">Target Price</Label>
          <Input
            id="targetPrice"
            type="number"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
            placeholder="50000"
            required
          />
        </div>
      ) : condition === "change" ? (
        <div>
          <Label htmlFor="changePercent">Change Percentage</Label>
          <Input
            id="changePercent"
            type="number"
            value={changePercent}
            onChange={(e) => setChangePercent(e.target.value)}
            placeholder="5"
            required
          />
        </div>
      ) : (
        <div>
          <Label htmlFor="volumeThreshold">Volume Threshold</Label>
          <Input
            id="volumeThreshold"
            type="number"
            value={volumeThreshold}
            onChange={(e) => setVolumeThreshold(e.target.value)}
            placeholder="1000000"
            required
          />
        </div>
      )}
      <div>
        <Label>Notification Channels</Label>
        <div className="flex flex-wrap gap-2 mt-2">
          {["push", "email", "sms", "telegram", "discord"].map(channel => (
            <Badge
              key={channel}
              variant={channels.includes(channel) ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => toggleChannel(channel)}
            >
              {channel}
            </Badge>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <Label htmlFor="sound">Sound Notification</Label>
        <Switch id="sound" checked={sound} onCheckedChange={setSound} />
      </div>
      <div className="flex gap-2">
        <Button type="submit" className="flex-1">Save Alert</Button>
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}

