import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Keyboard, Search, Navigation, Settings, Zap } from "lucide-react";
import { formatShortcut, KEYBOARD_SHORTCUTS, type ShortcutConfig } from "@/hooks/useKeyboardShortcuts";
import { cn } from "@/lib/utils";

interface KeyboardShortcutsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ShortcutGroup {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  shortcuts: ShortcutConfig[];
}

export function KeyboardShortcutsModal({ open, onOpenChange }: KeyboardShortcutsModalProps) {
  const [searchQuery, setSearchQuery] = useState("");

  // Group shortcuts by category
  const navigationShortcuts: ShortcutConfig[] = KEYBOARD_SHORTCUTS.filter(
    (s) =>
      s.description?.includes("Go to") ||
      s.description?.includes("Navigate") ||
      s.key === "k" // Command palette
  );

  const actionShortcuts: ShortcutConfig[] = KEYBOARD_SHORTCUTS.filter(
    (s) =>
      s.description?.includes("Save") ||
      s.description?.includes("Refresh") ||
      s.description?.includes("Toggle") ||
      s.description?.includes("Force refresh")
  );

  const helpShortcuts: ShortcutConfig[] = KEYBOARD_SHORTCUTS.filter(
    (s) => s.description?.includes("Show") || s.description?.includes("Help")
  );

  const shortcutGroups: ShortcutGroup[] = [
    {
      title: "Navigation",
      icon: Navigation,
      shortcuts: navigationShortcuts,
    },
    {
      title: "Actions",
      icon: Zap,
      shortcuts: actionShortcuts,
    },
    {
      title: "Help",
      icon: Keyboard,
      shortcuts: helpShortcuts,
    },
  ];

  // Filter shortcuts based on search query
  const filteredGroups = shortcutGroups.map((group) => ({
    ...group,
    shortcuts: group.shortcuts.filter(
      (s) =>
        s.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        formatShortcut(s).toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.key.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter((group) => group.shortcuts.length > 0);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </DialogTitle>
          <DialogDescription>
            Use keyboard shortcuts to navigate and interact with the application faster
          </DialogDescription>
        </DialogHeader>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search shortcuts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Shortcuts List */}
        <div className="flex-1 overflow-y-auto mt-4">
          {filteredGroups.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No shortcuts found matching "{searchQuery}"
            </div>
          ) : (
            <Tabs defaultValue={filteredGroups[0]?.title.toLowerCase()} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                {filteredGroups.map((group) => (
                  <TabsTrigger
                    key={group.title}
                    value={group.title.toLowerCase()}
                    className="flex items-center gap-2"
                  >
                    <group.icon className="h-4 w-4" />
                    {group.title}
                  </TabsTrigger>
                ))}
              </TabsList>

              {filteredGroups.map((group) => (
                <TabsContent
                  key={group.title}
                  value={group.title.toLowerCase()}
                  className="mt-4 space-y-2"
                >
                  <div className="grid gap-2">
                    {group.shortcuts.map((shortcut, index) => (
                      <div
                        key={`${shortcut.key}-${index}`}
                        className="flex items-center justify-between p-3 rounded-md border hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex-1">
                          <div className="font-medium text-sm">
                            {shortcut.description || "Keyboard shortcut"}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="font-mono text-xs">
                            {formatShortcut(shortcut)}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          )}
        </div>

        {/* Footer */}
        <div className="mt-4 pt-4 border-t text-sm text-muted-foreground">
          <p>
            Tip: Press <Badge variant="outline" className="mx-1 font-mono">Shift+?</Badge> to open this dialog
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

