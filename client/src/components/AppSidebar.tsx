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
import { Link, useLocation } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";
import { useBots } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";

const menuItems = [
  {
    title: "Dashboard",
    url: "/dashboard", // Updated route path
    icon: LayoutDashboard,
  },
  // ... (rest of items)

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
  const location = useLocation();
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
      className="border-r-2 border-primary/20 bg-background shadow-none"
    >
      <SidebarContent className="gap-0">
        <div className="p-4 border-b-2 border-primary/20 bg-background">
          <h1 className="text-xl font-black flex items-center gap-3 tracking-tighter uppercase">
            <span className="w-3 h-3 bg-primary animate-pulse shadow-[0_0_10px_#00ff00]" />
            <span className="text-primary drop-shadow-[0_0_5px_rgba(0,255,0,0.5)]">
              Crypto<br/>Orchestrator
            </span>
          </h1>
        </div>

        <SidebarGroup className="px-0 py-2">
          <SidebarGroupLabel className="text-[10px] font-bold text-primary/50 uppercase tracking-[0.2em] px-4 mb-2">
            System Modules
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5 px-2">
              {allMenuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={location.pathname === item.url}
                    className="rounded-none transition-all duration-200 hover:bg-primary/10 hover:text-primary active:bg-primary/20 data-[active=true]:bg-primary data-[active=true]:text-black border border-transparent hover:border-primary/50 data-[active=true]:border-primary"
                  >
                    <Link
                      to={item.url}
                      data-testid={`link-${item.title.toLowerCase()}`}
                      className="flex items-center gap-3 font-mono text-xs uppercase tracking-wide"
                    >
                      <item.icon className="w-4 h-4 flex-shrink-0" />
                      <span className="font-bold">{item.title}</span>
                      {item.badge?.()}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="px-0 py-2 mt-auto">
          <SidebarGroupLabel className="text-[10px] font-bold text-primary/50 uppercase tracking-[0.2em] px-4 mb-2">
            Config
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5 px-2">
              {settingsItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={location.pathname === item.url}
                    className="rounded-none transition-all duration-200 hover:bg-primary/10 hover:text-primary active:bg-primary/20 data-[active=true]:bg-primary data-[active=true]:text-black border border-transparent hover:border-primary/50 data-[active=true]:border-primary"
                  >
                    <Link
                      to={item.url}
                      data-testid={`link-${item.title.toLowerCase()}`}
                      className="flex items-center gap-3 font-mono text-xs uppercase tracking-wide"
                    >
                      <item.icon className="w-4 h-4 flex-shrink-0" />
                      <span className="font-bold">{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <div className="p-4 border-t-2 border-primary/20 text-[10px] text-primary/50 font-mono bg-background">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-1.5 h-1.5 bg-green-500 animate-pulse" />
          <span className="uppercase tracking-widest">System Online</span>
        </div>
        <div className="opacity-70">
          V{import.meta.env?.VITE_APP_VERSION || "1.0.0"} :: EST. 2026
        </div>
      </div>
    </Sidebar>
  );
}
