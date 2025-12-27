/**
 * Tax Reporting Dashboard Component
 * Displays tax summaries, gain/loss reports, and Form 8949 generation
 */

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  FileText,
  Download,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Calendar,
  DollarSign,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { useTaxSummary, useForm8949, useTaxLossHarvesting } from "@/hooks/useTaxReporting";

export function TaxReportingDashboard() {
  const { toast } = useToast();
  const [taxYear, setTaxYear] = useState<number>(new Date().getFullYear() - 1);
  const [costBasisMethod, setCostBasisMethod] = useState<string>("fifo");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("");

  // React Query hooks
  const { data: taxSummary, isLoading: summaryLoading } = useTaxSummary(
    selectedSymbol || undefined,
    undefined,
    undefined
  );
  const { data: form8949, isLoading: formLoading } = useForm8949(taxYear, costBasisMethod);
  const { data: lossHarvesting, isLoading: harvestingLoading } = useTaxLossHarvesting(
    selectedSymbol || "BTC",
    50000, // Current price - would come from market data
    0.1
  );

  const handleExportForm8949 = async (format: "csv" | "json") => {
    try {
      const response = await fetch(
        `/api/tax/form-8949/export?tax_year=${taxYear}&method=${costBasisMethod}&format=${format}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
          },
        }
      );

      if (format === "csv") {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `form8949_${taxYear}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `form8949_${taxYear}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }

      toast({
        title: "Export Successful",
        description: `Form 8949 exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: error instanceof Error ? error.message : "Failed to export Form 8949",
        variant: "destructive",
      });
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Tax Reporting Dashboard
          </CardTitle>
          <CardDescription>
            View tax summaries, generate Form 8949, and identify tax-loss harvesting opportunities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="summary" className="w-full">
            <TabsList>
              <TabsTrigger value="summary">Tax Summary</TabsTrigger>
              <TabsTrigger value="form8949">Form 8949</TabsTrigger>
              <TabsTrigger value="loss-harvesting">Tax-Loss Harvesting</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="space-y-4">
              {summaryLoading ? (
                <LoadingSkeleton height="300px" />
              ) : taxSummary ? (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Short-Term Gains</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                          {formatCurrency(taxSummary.short_term.gains)}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Short-Term Losses</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-600">
                          {formatCurrency(taxSummary.short_term.losses)}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Long-Term Gains</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                          {formatCurrency(taxSummary.long_term.gains)}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Long-Term Losses</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-600">
                          {formatCurrency(taxSummary.long_term.losses)}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Net Gain/Loss</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-4xl font-bold">
                        {taxSummary.net_gain_loss >= 0 ? (
                          <span className="text-green-600">
                            {formatCurrency(taxSummary.net_gain_loss)}
                          </span>
                        ) : (
                          <span className="text-red-600">
                            {formatCurrency(taxSummary.net_gain_loss)}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground mt-2">
                        Total Proceeds: {formatCurrency(taxSummary.total_proceeds)} | Total Cost
                        Basis: {formatCurrency(taxSummary.total_cost_basis)}
                      </div>
                    </CardContent>
                  </Card>

                  {taxSummary.wash_sales.count > 0 && (
                    <Card className="border-yellow-500">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-yellow-600">
                          <AlertTriangle className="h-5 w-5" />
                          Wash Sale Warning
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p>
                          {taxSummary.wash_sales.count} wash sale(s) detected. Total adjustment:{" "}
                          {formatCurrency(taxSummary.wash_sales.total_adjustment)}
                        </p>
                      </CardContent>
                    </Card>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No tax data available
                </div>
              )}
            </TabsContent>

            <TabsContent value="form8949" className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="space-y-2">
                  <Label>Tax Year</Label>
                  <Input
                    type="number"
                    value={taxYear}
                    onChange={(e) => setTaxYear(parseInt(e.target.value) || new Date().getFullYear())}
                    min={2020}
                    max={new Date().getFullYear()}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Cost Basis Method</Label>
                  <Select value={costBasisMethod} onValueChange={setCostBasisMethod}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fifo">FIFO</SelectItem>
                      <SelectItem value="lifo">LIFO</SelectItem>
                      <SelectItem value="average">Average</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end gap-2">
                  <Button onClick={() => handleExportForm8949("csv")} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Export CSV
                  </Button>
                  <Button onClick={() => handleExportForm8949("json")} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Export JSON
                  </Button>
                </div>
              </div>

              {formLoading ? (
                <LoadingSkeleton height="400px" />
              ) : form8949 ? (
                <div className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>{form8949.part_i.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Description</TableHead>
                            <TableHead>Date Acquired</TableHead>
                            <TableHead>Date Sold</TableHead>
                            <TableHead>Proceeds</TableHead>
                            <TableHead>Cost Basis</TableHead>
                            <TableHead>Gain/(Loss)</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {form8949.part_i.rows.map((row: any, index: number) => (
                            <TableRow key={index}>
                              <TableCell>{row.description}</TableCell>
                              <TableCell>{row.date_acquired}</TableCell>
                              <TableCell>{row.date_sold}</TableCell>
                              <TableCell>{formatCurrency(row.proceeds)}</TableCell>
                              <TableCell>{formatCurrency(row.cost_basis)}</TableCell>
                              <TableCell>
                                {row.gain_loss >= 0 ? (
                                  <span className="text-green-600">
                                    {formatCurrency(row.gain_loss)}
                                  </span>
                                ) : (
                                  <span className="text-red-600">
                                    {formatCurrency(row.gain_loss)}
                                  </span>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>{form8949.part_ii.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Description</TableHead>
                            <TableHead>Date Acquired</TableHead>
                            <TableHead>Date Sold</TableHead>
                            <TableHead>Proceeds</TableHead>
                            <TableHead>Cost Basis</TableHead>
                            <TableHead>Gain/(Loss)</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {form8949.part_ii.rows.map((row: any, index: number) => (
                            <TableRow key={index}>
                              <TableCell>{row.description}</TableCell>
                              <TableCell>{row.date_acquired}</TableCell>
                              <TableCell>{row.date_sold}</TableCell>
                              <TableCell>{formatCurrency(row.proceeds)}</TableCell>
                              <TableCell>{formatCurrency(row.cost_basis)}</TableCell>
                              <TableCell>
                                {row.gain_loss >= 0 ? (
                                  <span className="text-green-600">
                                    {formatCurrency(row.gain_loss)}
                                  </span>
                                ) : (
                                  <span className="text-red-600">
                                    {formatCurrency(row.gain_loss)}
                                  </span>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No Form 8949 data available for {taxYear}
                </div>
              )}
            </TabsContent>

            <TabsContent value="loss-harvesting" className="space-y-4">
              {harvestingLoading ? (
                <LoadingSkeleton height="300px" />
              ) : lossHarvesting && lossHarvesting.opportunities.length > 0 ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Tax-Loss Harvesting Opportunities</CardTitle>
                    <CardDescription>
                      Lots that are at a loss and could be sold to realize tax losses
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Purchase Date</TableHead>
                          <TableHead>Quantity</TableHead>
                          <TableHead>Cost Basis</TableHead>
                          <TableHead>Current Value</TableHead>
                          <TableHead>Unrealized Loss</TableHead>
                          <TableHead>Loss %</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {lossHarvesting.opportunities.map((opp: any, index: number) => (
                          <TableRow key={index}>
                            <TableCell>
                              {new Date(opp.purchase_date).toLocaleDateString()}
                            </TableCell>
                            <TableCell>{opp.quantity.toFixed(6)}</TableCell>
                            <TableCell>{formatCurrency(opp.cost_basis)}</TableCell>
                            <TableCell>{formatCurrency(opp.current_value)}</TableCell>
                            <TableCell className="text-red-600">
                              {formatCurrency(opp.unrealized_loss)}
                            </TableCell>
                            <TableCell className="text-red-600">
                              {formatPercent(opp.loss_percent)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No tax-loss harvesting opportunities found
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
