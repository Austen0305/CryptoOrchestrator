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
import { useBots } from "@/hooks/useBots";

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
    title: "Bots",
    url: "/bots",
    icon: Bot,
    badge: () => {
      const { bots } = useBots();
      const activeCount = bots.filter(b => b.status === 'active').length;
      return activeCount > 0 ? (
        <Badge variant="default" className="ml-2 bg-green-500">
          {activeCount}
        </Badge>
      ) : null;
    },
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
    title: "History",
    url: "/history",
    icon: History,
  },
  {
    title: "Markets",
    url: "/markets",
    icon: CircleDollarSign,
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

  return (
    <Sidebar>
      <SidebarContent>
        <div className="p-4 border-b">
          <h1 className="text-lg font-bold flex items-center gap-2">
            <span className="bg-primary rounded-full w-2 h-2 animate-pulse" />
            CryptoOrchestrator
          </h1>
        </div>
        
        <SidebarGroup>
          <SidebarGroupLabel>Core</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={location === item.url}>
                    <Link href={item.url} data-testid={`link-${item.title.toLowerCase()}`}>
                      <item.icon className="w-5 h-5" />
                      <span>{item.title}</span>
                      {item.badge?.()}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Configuration</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {settingsItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={location === item.url}>
                    <Link href={item.url} data-testid={`link-${item.title.toLowerCase()}`}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      <div className="p-4 border-t text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span>Connected to Kraken</span>
        </div>
        <div className="mt-1">v{import.meta.env?.VITE_APP_VERSION || '1.0.0'}</div>
      </div>
    </Sidebar>
  );
}
