import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bell, Settings, User } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

interface TradingHeaderProps {
  balance: number;
  connected: boolean;
}

export function TradingHeader({ balance, connected }: TradingHeaderProps) {
  return (
    <header className="h-16 border-b bg-card flex items-center justify-between px-6">
      <div className="flex items-center gap-6">
        <h1 className="text-xl font-bold">CryptoML</h1>
        <Badge variant={connected ? "default" : "secondary"} data-testid="badge-connection">
          {connected ? "Connected" : "Disconnected"}
        </Badge>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-sm text-muted-foreground">Total Balance</p>
          <p className="text-lg font-mono font-bold" data-testid="text-balance">
            ${balance.toLocaleString()}
          </p>
        </div>
        <div className="h-8 w-px bg-border" />
        <Button variant="ghost" size="icon" data-testid="button-notifications">
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" data-testid="button-settings">
          <Settings className="h-5 w-5" />
        </Button>
        <ThemeToggle />
        <Button variant="ghost" size="icon" data-testid="button-profile">
          <User className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
