/**
 * Custom Dashboard Builder
 * User-configurable metric dashboards
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2, Save, LayoutGrid } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";

interface Dashboard {
  id: string;
  name: string;
  description?: string;
  widget_count: number;
  created_at: string;
  updated_at: string;
}

interface DashboardWidget {
  id: string;
  title: string;
  chart_type: string;
  metric_name: string;
  time_range: string;
  position: { x: number; y: number; width: number; height: number };
  config: Record<string, any>;
}

interface DashboardTemplate {
  id: string;
  name: string;
  description?: string;
  widget_count: number;
}

export default function DashboardBuilder() {
  const queryClient = useQueryClient();
  const [selectedDashboard, setSelectedDashboard] = useState<string | null>(null);
  const [dashboardName, setDashboardName] = useState("");
  const [dashboardDescription, setDashboardDescription] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");

  // Fetch user dashboards
  const { data: dashboards, isLoading: dashboardsLoading } = useQuery<Dashboard[]>({
    queryKey: ["/api/observability/dashboards"],
  });

  // Fetch dashboard templates
  const { data: templates, isLoading: templatesLoading } = useQuery<DashboardTemplate[]>({
    queryKey: ["/api/observability/dashboards/templates"],
  });

  // Fetch selected dashboard details
  const { data: dashboardDetails, isLoading: detailsLoading } = useQuery<{
    id: string;
    name: string;
    description?: string;
    widgets: DashboardWidget[];
  }>({
    queryKey: ["/api/observability/dashboards", selectedDashboard],
    enabled: !!selectedDashboard,
  });

  // Create dashboard mutation
  const createDashboard = useMutation({
    mutationFn: async (data: { name: string; description?: string; template_id?: string }) => {
      return apiRequest<Dashboard>("/api/observability/dashboards", {
        method: "POST",
        body: data,
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Dashboard Created",
        description: `Dashboard "${data.name}" created successfully`,
      });
      queryClient.invalidateQueries({ queryKey: ["/api/observability/dashboards"] });
      setSelectedDashboard(data.id);
      setDashboardName("");
      setDashboardDescription("");
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Add widget mutation
  const addWidget = useMutation({
    mutationFn: async (data: {
      dashboard_id: string;
      widget: {
        title: string;
        chart_type: string;
        metric_name: string;
        time_range: string;
        position: { x: number; y: number; width: number; height: number };
        config?: Record<string, any>;
      };
    }) => {
      return apiRequest<{ status: string; widget_id: string }>(
        `/api/observability/dashboards/${data.dashboard_id}/widgets`,
        {
          method: "POST",
          body: data.widget,
        }
      );
    },
    onSuccess: () => {
      toast({
        title: "Widget Added",
        description: "Widget added to dashboard",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/observability/dashboards", selectedDashboard] });
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Delete dashboard mutation
  const deleteDashboard = useMutation({
    mutationFn: async (dashboardId: string) => {
      return apiRequest(`/api/observability/dashboards/${dashboardId}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      toast({
        title: "Dashboard Deleted",
        description: "Dashboard deleted successfully",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/observability/dashboards"] });
      setSelectedDashboard(null);
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleCreateDashboard = () => {
    if (!dashboardName.trim()) {
      toast({
        title: "Error",
        description: "Dashboard name is required",
        variant: "destructive",
      });
      return;
    }

    createDashboard.mutate({
      name: dashboardName,
      description: dashboardDescription || undefined,
      template_id: selectedTemplate || undefined,
    });
  };

  const handleAddWidget = () => {
    if (!selectedDashboard) {
      toast({
        title: "Error",
        description: "Please select a dashboard first",
        variant: "destructive",
      });
      return;
    }

    // Simple widget - in production, this would open a widget configuration dialog
    addWidget.mutate({
      dashboard_id: selectedDashboard,
      widget: {
        title: "New Widget",
        chart_type: "line",
        metric_name: "api_requests",
        time_range: "24h",
        position: { x: 0, y: 0, width: 6, height: 4 },
        config: {},
      },
    });
  };

  if (dashboardsLoading || templatesLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Loading dashboards...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Builder</h1>
          <p className="text-muted-foreground">Create and customize your metric dashboards</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create Dashboard Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Create Dashboard</CardTitle>
            <CardDescription>Create a new custom dashboard</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="dashboard-name">Dashboard Name</Label>
              <Input
                id="dashboard-name"
                value={dashboardName}
                onChange={(e) => setDashboardName(e.target.value)}
                placeholder="My Custom Dashboard"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dashboard-description">Description (Optional)</Label>
              <Textarea
                id="dashboard-description"
                value={dashboardDescription}
                onChange={(e) => setDashboardDescription(e.target.value)}
                placeholder="Dashboard description"
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="template">Template (Optional)</Label>
              <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                <SelectTrigger id="template">
                  <SelectValue placeholder="Select a template" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">None</SelectItem>
                  {templates?.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleCreateDashboard}
              disabled={createDashboard.isPending}
              className="w-full"
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Dashboard
            </Button>
          </CardContent>
        </Card>

        {/* Dashboard List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Your Dashboards</CardTitle>
            <CardDescription>Select a dashboard to edit</CardDescription>
          </CardHeader>
          <CardContent>
            {!dashboards || dashboards.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No dashboards yet. Create one to get started.
              </div>
            ) : (
              <div className="space-y-2">
                {dashboards.map((dashboard) => (
                  <div
                    key={dashboard.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedDashboard === dashboard.id
                        ? "border-primary bg-primary/5"
                        : "hover:bg-muted"
                    }`}
                    onClick={() => setSelectedDashboard(dashboard.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold">{dashboard.name}</h3>
                        {dashboard.description && (
                          <p className="text-sm text-muted-foreground">{dashboard.description}</p>
                        )}
                        <p className="text-xs text-muted-foreground mt-1">
                          {dashboard.widget_count} widgets • Created{" "}
                          {new Date(dashboard.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm("Delete this dashboard?")) {
                            deleteDashboard.mutate(dashboard.id);
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Dashboard Editor */}
      {selectedDashboard && dashboardDetails && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{dashboardDetails.name}</CardTitle>
                <CardDescription>
                  {dashboardDetails.description || "Edit your dashboard widgets"}
                </CardDescription>
              </div>
              <Button onClick={handleAddWidget}>
                <Plus className="mr-2 h-4 w-4" />
                Add Widget
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {dashboardDetails.widgets.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <LayoutGrid className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No widgets yet. Add widgets to build your dashboard.</p>
              </div>
            ) : (
              <div className="grid grid-cols-12 gap-4">
                {dashboardDetails.widgets.map((widget) => (
                  <Card
                    key={widget.id}
                    className="col-span-12 md:col-span-6 lg:col-span-4"
                  >
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">{widget.title}</CardTitle>
                        <Button variant="ghost" size="icon">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">Type:</span>{" "}
                          <span className="font-medium">{widget.chart_type}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Metric:</span>{" "}
                          <span className="font-medium">{widget.metric_name}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Time Range:</span>{" "}
                          <span className="font-medium">{widget.time_range}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
