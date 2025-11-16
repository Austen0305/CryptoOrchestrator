/**
 * Strategies Page - Main page for strategy management
 */
import React, { useState, Suspense } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Plus, Code, ShoppingBag, History, Play } from "lucide-react";
import { StrategyTemplateLibrary } from "@/components/StrategyTemplateLibrary";
import { useStrategies, Strategy, StrategyTemplate } from "@/hooks/useStrategies";
import { Loader2 } from "lucide-react";

// Lazy load heavy components
const StrategyEditor = React.lazy(() => 
  import("@/components/StrategyEditor").then(m => ({ default: m.StrategyEditor }))
);
const StrategyMarketplace = React.lazy(() => 
  import("@/components/StrategyMarketplace").then(m => ({ default: m.StrategyMarketplace }))
);
const StrategyList = React.lazy(() => 
  import("@/components/StrategyList").then(m => ({ default: m.StrategyList }))
);

export default function Strategies() {
  const [activeTab, setActiveTab] = useState("templates");
  const [selectedTemplate, setSelectedTemplate] = useState<StrategyTemplate | null>(null);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);

  const handleSelectTemplate = (template: StrategyTemplate) => {
    setSelectedTemplate(template);
    setActiveTab("editor");
  };

  const handleEditStrategy = (strategy: Strategy) => {
    setEditingStrategy(strategy);
    setActiveTab("editor");
  };

  const handleCreateNew = () => {
    setSelectedTemplate(null);
    setEditingStrategy(null);
    setActiveTab("editor");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Strategies</h1>
          <p className="text-muted-foreground mt-1">
            Create, manage, and deploy trading strategies
          </p>
        </div>
        <Button onClick={handleCreateNew} className="gap-2">
          <Plus className="h-4 w-4" />
          Create Strategy
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="templates">
            <Code className="h-4 w-4 mr-2" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="my-strategies">
            <History className="h-4 w-4 mr-2" />
            My Strategies
          </TabsTrigger>
          <TabsTrigger value="marketplace">
            <ShoppingBag className="h-4 w-4 mr-2" />
            Marketplace
          </TabsTrigger>
          <TabsTrigger value="editor">
            <Plus className="h-4 w-4 mr-2" />
            Editor
          </TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="space-y-4">
          <Suspense fallback={<Card><CardContent className="py-12"><Loader2 className="h-8 w-8 animate-spin mx-auto" /></CardContent></Card>}>
            <StrategyTemplateLibrary onSelectTemplate={handleSelectTemplate} />
          </Suspense>
        </TabsContent>

        <TabsContent value="my-strategies" className="space-y-4">
          <Suspense fallback={<Card><CardContent className="py-12"><Loader2 className="h-8 w-8 animate-spin mx-auto" /></CardContent></Card>}>
            <StrategyList onEdit={handleEditStrategy} />
          </Suspense>
        </TabsContent>

        <TabsContent value="marketplace" className="space-y-4">
          <Suspense fallback={<Card><CardContent className="py-12"><Loader2 className="h-8 w-8 animate-spin mx-auto" /></CardContent></Card>}>
            <StrategyMarketplace />
          </Suspense>
        </TabsContent>

        <TabsContent value="editor" className="space-y-4">
          <Suspense fallback={<Card><CardContent className="py-12"><Loader2 className="h-8 w-8 animate-spin mx-auto" /></CardContent></Card>}>
            <StrategyEditor
              template={selectedTemplate}
              strategy={editingStrategy}
              onClose={() => setActiveTab("my-strategies")}
            />
          </Suspense>
        </TabsContent>
      </Tabs>
    </div>
  );
}
