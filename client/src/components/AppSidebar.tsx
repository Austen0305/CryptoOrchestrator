import {
  LayoutDashboard,
  TrendingUp,
  Bot,
  History,
  BarChart3,
  Settings,
  CircleDollarSign,
  Shield,
  Code,
  Wallet,
  Lock,
  Grid,
  ArrowLeftRight,
  Target,
  LayoutGrid,
  Network,
  Building2,
  FileText,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Link, useLocation } from "wouter";
import { Badge } from "@/components/ui/badge";
import { useBots } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";

const menuItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Trading",
    url: "/trading",
    icon: TrendingUp,
    badge: () => null, // No badge by default
  },
  {
    title: "DEX Trading",
    url: "/dex-trading",
    icon: ArrowLeftRight,
    badge: () => (
      <Badge variant="secondary" className="ml-2 bg-blue-500/10 text-blue-500 border-blue-500/20">
        New
      </Badge>
    ),
  },
  {
    title: "Wallets",
    url: "/wallets",
    icon: Wallet,
  },
  {
    title: "Bots",
    url: "/bots",
    icon: Bot,
    badge: () => {
      const { data: bots } = useBots();
      // BotConfig status is "running" | "stopped" | "paused" (from schema)
      const activeCount = bots?.filter((b) => b.status === "running").length ?? 0;
      return activeCount > 0 ? (
        <Badge variant="default" className="ml-2 bg-green-500">
          {activeCount}
        </Badge>
      ) : null;
    },
  },
  {
    title: "Trading Bots",
    url: "/trading-bots",
    icon: Grid,
  },
  {
    title: "Strategies",
    url: "/strategies",
    icon: Code,
  },
  {
    title: "Analytics",
    url: "/analytics",
    icon: BarChart3,
  },
  {
    title: "Licensing",
    url: "/licensing",
    icon: CircleDollarSign,
  },
  {
    title: "Risk Management",
    url: "/risk",
    icon: Shield,
  },
        {
          title: "SLA Dashboard",
          url: "/sla-dashboard",
          icon: Target,
        },
        {
          title: "Dashboard Builder",
          url: "/dashboard-builder",
          icon: LayoutGrid,
        },
        {
          title: "Trace Visualization",
          url: "/traces",
          icon: Network,
        },
        {
          title: "Treasury Dashboard",
          url: "/treasury",
          icon: Building2,
        },
        {
          title: "Tax Reporting",
          url: "/tax-reporting",
          icon: FileText,
        },
  {
    title: "History",
    url: "/history",
    icon: History,
  },
  {
    title: "Markets",
    url: "/markets",
    icon: CircleDollarSign,
  },
  {
    title: "Wallet",
    url: "/wallet",
    icon: Wallet,
  },
  {
    title: "Staking",
    url: "/staking",
    icon: Lock,
  },
];

const settingsItems = [
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
  },
];

export function AppSidebar() {
  const [location] = useLocation();
  const { user, isAuthenticated } = useAuth();

  // Filter menu items based on user role
  const filteredMenuItems = menuItems.filter((item) => {
    // All items are visible by default
    return true;
  });

  // Add conditional menu items
  const conditionalItems = [];
  
  if (isAuthenticated) {
    conditionalItems.push({
      title: "Developer Analytics",
      url: "/developer/analytics",
      icon: BarChart3,
    });
  }

  if (user?.role === "admin") {
    conditionalItems.push({
      title: "Admin Analytics",
      url: "/admin/analytics",
      icon: Shield,
    });
  }

  const allMenuItems = [...filteredMenuItems, ...conditionalItems];

  return (
    <Sidebar
      className="border-r-2 border-sidebar-border/60 bg-gradient-to-b from-sidebar via-sidebar/98 to-sidebar backdrop-blur-lg shadow-2xl"
      style={{
        borderRightWidth: "4px",
        borderRightStyle: "solid",
        borderRightColor: "hsl(var(--sidebar-border) / 0.7)",
        boxShadow: "8px 0px 16px -6px hsl(220 8% 2% / 0.40)",
        background:
          "linear-gradient(180deg, hsl(var(--sidebar)), hsl(var(--sidebar) / 0.98), hsl(var(--sidebar)))",
      }}
    >
      <SidebarContent className="gap-3">
        <div
          className="p-5 md:p-6 border-b-2 border-sidebar-border/60 bg-gradient-to-r from-sidebar-accent/30 via-sidebar-accent/20 to-transparent"
          style={{ borderBottomWidth: "2px", borderBottomStyle: "solid" }}
        >
          <h1 className="text-lg md:text-xl font-black flex items-center gap-3">
            <span
              className="status-indicator bg-primary rounded-full w-3 h-3 shadow-xl shadow-primary/60 animate-pulse"
              style={{
                width: "12px",
                height: "12px",
                boxShadow: "0 0 12px hsl(217 91% 50% / 0.6), 0 0 24px hsl(217 91% 50% / 0.3)",
              }}
            />
            <span
              className="font-extrabold"
              style={{
                backgroundImage:
                  "linear-gradient(135deg, hsl(var(--foreground)), hsl(var(--foreground) / 0.95), hsl(var(--foreground) / 0.9))",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
                fontWeight: 900,
                fontSize: "1.25rem",
                letterSpacing: "-0.01em",
                textShadow: "0 2px 8px hsl(var(--foreground) / 0.2)",
              }}
            >
              CryptoOrchestrator
            </span>
          </h1>
        </div>

        <SidebarGroup className="px-2">
          <SidebarGroupLabel className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2 mb-2">
            Core
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1">
              {allMenuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={location === item.url}
                    className="rounded-lg transition-all duration-300 hover:bg-sidebar-accent/60 hover:scale-[1.02] active:scale-[0.98] hover:shadow-md border border-transparent hover:border-sidebar-accent/30"
                  >
                    <Link
                      href={item.url}
                      data-testid={`link-${item.title.toLowerCase()}`}
                      className="flex items-center gap-3 font-medium"
                    >
                      <item.icon className="w-4 h-4 md:w-5 md:h-5 flex-shrink-0" />
                      <span className="font-semibold">{item.title}</span>
                      {item.badge?.()}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="px-2 mt-4">
          <SidebarGroupLabel className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2 mb-2">
            Configuration
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1">
              {settingsItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={location === item.url}
                    className="rounded-lg transition-all duration-200 hover:bg-sidebar-accent/50 active:scale-[0.98]"
                  >
                    <Link
                      href={item.url}
                      data-testid={`link-${item.title.toLowerCase()}`}
                      className="flex items-center gap-3"
                    >
                      <item.icon className="w-4 h-4 md:w-5 md:h-5 flex-shrink-0" />
                      <span className="font-medium">{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <div className="p-4 border-t border-sidebar-border text-xs text-muted-foreground bg-sidebar-accent/30">
        <div className="flex items-center gap-2 mb-1">
          <span className="status-indicator w-2 h-2 rounded-full bg-green-500" />
          <span className="font-medium">Connected to Kraken</span>
        </div>
        <div className="text-[10px] opacity-70">
          v{import.meta.env?.VITE_APP_VERSION || "1.0.0"}
        </div>
      </div>
    </Sidebar>
  );
}
