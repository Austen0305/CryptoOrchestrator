import { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'wouter';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import {
  Home,
  Bot,
  BarChart3,
  Shield,
  Settings,
  CircleDollarSign,
  Search,
  Moon,
  Sun,
  Globe,
  FileDown,
} from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import { useTranslation } from 'react-i18next';

interface Command {
  id: string;
  label: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  action: () => void;
  keywords?: string[];
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [, setLocation] = useLocation();
    const { setTheme } = useTheme();
  const { i18n } = useTranslation();

  // Toggle command palette with Cmd+K or Ctrl+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const navigate = useCallback((path: string) => {
    setLocation(path);
    setOpen(false);
  }, [setLocation]);

  const commands: Command[] = [
    // Navigation
    {
      id: 'nav-dashboard',
      label: 'Go to Dashboard',
      description: 'View your trading dashboard',
      icon: Home,
      action: () => navigate('/'),
      keywords: ['home', 'overview'],
    },
    {
      id: 'nav-markets',
      label: 'Go to Markets',
      description: 'Browse cryptocurrency markets',
      icon: CircleDollarSign,
      action: () => navigate('/markets'),
      keywords: ['trading', 'pairs', 'crypto'],
    },
    {
      id: 'nav-bots',
      label: 'Go to Bots',
      description: 'Manage trading bots',
      icon: Bot,
      action: () => navigate('/bots'),
      keywords: ['automation', 'strategies'],
    },
    {
      id: 'nav-analytics',
      label: 'Go to Analytics',
      description: 'View trading analytics',
      icon: BarChart3,
      action: () => navigate('/analytics'),
      keywords: ['stats', 'performance', 'charts'],
    },
    {
      id: 'nav-risk',
      label: 'Go to Risk Management',
      description: 'Monitor portfolio risk',
      icon: Shield,
      action: () => navigate('/risk'),
      keywords: ['safety', 'protection'],
    },
    {
      id: 'nav-settings',
      label: 'Go to Settings',
      description: 'Adjust preferences',
      icon: Settings,
      action: () => navigate('/settings'),
      keywords: ['config', 'preferences'],
    },

    // Theme actions
    {
      id: 'theme-light',
      label: 'Switch to Light Theme',
      icon: Sun,
      action: () => {
        setTheme('light');
        setOpen(false);
      },
      keywords: ['appearance', 'bright'],
    },
    {
      id: 'theme-dark',
      label: 'Switch to Dark Theme',
      icon: Moon,
      action: () => {
        setTheme('dark');
        setOpen(false);
      },
      keywords: ['appearance', 'night'],
    },

    // Language actions
    {
      id: 'lang-en',
      label: 'Switch to English',
      icon: Globe,
      action: () => {
        i18n.changeLanguage('en');
        setOpen(false);
      },
      keywords: ['language'],
    },
    {
      id: 'lang-es',
      label: 'Switch to Spanish',
      icon: Globe,
      action: () => {
        i18n.changeLanguage('es');
        setOpen(false);
      },
      keywords: ['language', 'español'],
    },
    {
      id: 'lang-ar',
      label: 'Switch to Arabic',
      icon: Globe,
      action: () => {
        i18n.changeLanguage('ar');
        setOpen(false);
      },
      keywords: ['language', 'عربي'],
    },

    // Quick actions
    {
      id: 'action-export-trades',
      label: 'Export Trade History',
      description: 'Download trades as CSV',
      icon: FileDown,
      action: () => {
        // Will implement export functionality
        // Note: This is a placeholder action, will be implemented later
        setOpen(false);
      },
      keywords: ['download', 'csv', 'data'],
    },
    {
      id: 'action-search-markets',
      label: 'Search Markets',
      description: 'Find trading pairs',
      icon: Search,
      action: () => navigate('/markets'),
      keywords: ['find', 'crypto', 'pairs'],
    },
  ];

  const navigationCommands = commands.filter((cmd) => cmd.id.startsWith('nav-'));
  const themeCommands = commands.filter((cmd) => cmd.id.startsWith('theme-'));
  const languageCommands = commands.filter((cmd) => cmd.id.startsWith('lang-'));
  const actionCommands = commands.filter((cmd) => cmd.id.startsWith('action-'));

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        <CommandGroup heading="Navigation">
          {navigationCommands.map((command) => (
            <CommandItem
              key={command.id}
              onSelect={command.action}
              className="cursor-pointer"
            >
              <command.icon className="mr-2 h-4 w-4" />
              <div className="flex-1">
                <div>{command.label}</div>
                {command.description && (
                  <div className="text-xs text-muted-foreground">
                    {command.description}
                  </div>
                )}
              </div>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Quick Actions">
          {actionCommands.map((command) => (
            <CommandItem
              key={command.id}
              onSelect={command.action}
              className="cursor-pointer"
            >
              <command.icon className="mr-2 h-4 w-4" />
              <div className="flex-1">
                <div>{command.label}</div>
                {command.description && (
                  <div className="text-xs text-muted-foreground">
                    {command.description}
                  </div>
                )}
              </div>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Appearance">
          {themeCommands.map((command) => (
            <CommandItem
              key={command.id}
              onSelect={command.action}
              className="cursor-pointer"
            >
              <command.icon className="mr-2 h-4 w-4" />
              <span>{command.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Language">
          {languageCommands.map((command) => (
            <CommandItem
              key={command.id}
              onSelect={command.action}
              className="cursor-pointer"
            >
              <command.icon className="mr-2 h-4 w-4" />
              <span>{command.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>

      <div className="border-t p-2 text-xs text-muted-foreground text-center">
        Press{' '}
        <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium">
          <span className="text-xs">⌘</span>K
        </kbd>{' '}
        to toggle
      </div>
    </CommandDialog>
  );
}

// Hook to use command palette programmatically
export function useCommandPalette() {
  // Hook for future programmatic control
  return {};
}
