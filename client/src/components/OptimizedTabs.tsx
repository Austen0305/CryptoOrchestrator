/**
 * Optimized Tabs Component
 * High-performance tabs with lazy loading
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { cn } from '@/lib/utils';

interface Tab {
  value: string;
  label: string;
  content: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface OptimizedTabsProps {
  tabs: Tab[];
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  className?: string;
  lazy?: boolean;
}

export function OptimizedTabs({
  tabs,
  defaultValue,
  onValueChange,
  className,
  lazy = true,
}: OptimizedTabsProps) {
  const initialValue = defaultValue || tabs[0]?.value || '';
  const [activeTab, setActiveTab] = useState(initialValue);
  const [loadedTabs, setLoadedTabs] = useState<Set<string>>(
    new Set([initialValue].filter(Boolean))
  );

  const handleValueChange = useCallback(
    (value: string) => {
      setActiveTab(value);
      if (lazy) {
        setLoadedTabs((prev) => new Set([...prev, value]));
      }
      onValueChange?.(value);
    },
    [onValueChange, lazy]
  );

  const activeTabContent = useMemo(() => {
    const tab = tabs.find((t) => t.value === activeTab);
    return tab?.content;
  }, [tabs, activeTab]);

  return (
    <Tabs value={activeTab} onValueChange={handleValueChange} className={cn(className)}>
      <TabsList>
        {tabs.map((tab) => (
          <TabsTrigger
            key={tab.value}
            value={tab.value}
            disabled={tab.disabled}
            className="flex items-center gap-2"
          >
            {tab.icon as any}
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {tabs.map((tab) => {
        if (lazy && !loadedTabs.has(tab.value)) {
          return null;
        }
        return (
          <TabsContent key={tab.value} value={tab.value}>
            {tab.content as any}
          </TabsContent>
        );
      })}
    </Tabs>
  );
}

