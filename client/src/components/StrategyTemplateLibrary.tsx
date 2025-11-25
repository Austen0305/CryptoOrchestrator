/**
 * Strategy Template Library Component
 * Displays all available strategy templates organized by category
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useStrategyTemplates, StrategyTemplate } from "@/hooks/useStrategies";
import { Loader2, Brain, TrendingUp, Zap, Sparkles, Code2 } from "lucide-react";
import { useState } from "react";

interface StrategyTemplateLibraryProps {
  onSelectTemplate?: (template: StrategyTemplate) => void;
}

const categoryIcons = {
  technical: TrendingUp,
  ml: Brain,
  hybrid: Sparkles,
};

const categoryColors = {
  technical: "bg-blue-500",
  ml: "bg-purple-500",
  hybrid: "bg-green-500",
};

export function StrategyTemplateLibrary({ onSelectTemplate }: StrategyTemplateLibraryProps) {
  const { data: allTemplates, isLoading } = useStrategyTemplates();
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  // Get templates by category
  const technicalTemplates = allTemplates?.filter((t) => t.category === "technical") || [];
  const mlTemplates = allTemplates?.filter((t) => t.category === "ml") || [];
  const hybridTemplates = allTemplates?.filter((t) => t.category === "hybrid") || [];

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  const renderTemplateCard = (template: StrategyTemplate) => {
    const CategoryIcon = categoryIcons[template.category as keyof typeof categoryIcons] || Code2;
    const categoryColor = categoryColors[template.category as keyof typeof categoryColors] || "bg-gray-500";

    return (
      <Card key={template.strategy_type} className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${categoryColor} text-white`}>
                <CategoryIcon className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-lg">{template.name}</CardTitle>
                <Badge variant="outline" className="mt-1">
                  {template.strategy_type.toUpperCase()}
                </Badge>
              </div>
            </div>
          </div>
          <CardDescription className="mt-2">{template.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Category:</span>
              <Badge variant="secondary">{template.category}</Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Timeframe:</span>
              <span className="font-medium">{template.config.timeframe || "N/A"}</span>
            </div>
            {template.config.stop_loss_pct && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Stop Loss:</span>
                <span className="font-medium">{template.config.stop_loss_pct}%</span>
              </div>
            )}
            {template.config.take_profit_pct && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Take Profit:</span>
                <span className="font-medium">{template.config.take_profit_pct}%</span>
              </div>
            )}
            {onSelectTemplate && (
              <Button
                className="w-full mt-4"
                onClick={() => onSelectTemplate(template)}
              >
                Use Template
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Strategy Templates</h2>
        <p className="text-muted-foreground mt-1">
          Choose from built-in strategy templates or create your own
        </p>
      </div>

      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList>
          <TabsTrigger value="all">All ({allTemplates?.length || 0})</TabsTrigger>
          <TabsTrigger value="technical">Technical ({technicalTemplates.length})</TabsTrigger>
          <TabsTrigger value="ml">ML ({mlTemplates.length})</TabsTrigger>
          <TabsTrigger value="hybrid">Hybrid ({hybridTemplates.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allTemplates?.map(renderTemplateCard)}
          </div>
        </TabsContent>

        <TabsContent value="technical" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {technicalTemplates.map(renderTemplateCard)}
          </div>
        </TabsContent>

        <TabsContent value="ml" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mlTemplates.map(renderTemplateCard)}
          </div>
        </TabsContent>

        <TabsContent value="hybrid" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {hybridTemplates.map(renderTemplateCard)}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
