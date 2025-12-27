/**
 * Tax Reporting
 * Multi-jurisdiction tax reporting and configuration
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  Download,
  Globe,
  Calculator,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  AlertCircle,
  Calendar,
} from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { toast } from "@/hooks/use-toast";

interface Jurisdiction {
  code: string;
  name: string;
  currency: string;
  long_term_threshold_days: number;
  tax_year_start: string;
  tax_free_threshold: number;
  short_term_rate: number;
  long_term_rate: number;
}

interface TaxCalculation {
  jurisdiction: string;
  gain_loss: number;
  taxable_amount: number;
  tax_rate: number;
  tax_amount: number;
  is_long_term: boolean;
  tax_free_threshold: number;
}

interface TaxYear {
  jurisdiction: string;
  date: string;
  tax_year: number;
  tax_year_start: string;
  tax_year_end: string;
}

export default function TaxReporting() {
  const queryClient = useQueryClient();
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>("US");
  const [taxYear, setTaxYear] = useState<number>(new Date().getFullYear());
  const [gainLoss, setGainLoss] = useState<string>("");
  const [isLongTerm, setIsLongTerm] = useState<boolean>(false);

  // Fetch supported jurisdictions
  const { data: jurisdictions, isLoading: jurisdictionsLoading } = useQuery<{
    jurisdictions: Jurisdiction[];
    count: number;
  }>({
    queryKey: ["/api/tax/jurisdictions"],
  });

  // Fetch tax year for selected jurisdiction
  const { data: taxYearData } = useQuery<TaxYear>({
    queryKey: ["/api/tax/jurisdictions", selectedJurisdiction, "tax-year"],
    enabled: false, // Will be enabled when needed
  });

  // Calculate tax mutation
  const calculateTax = useMutation({
    mutationFn: async (data: { jurisdiction: string; gain_loss: number; is_long_term: boolean; tax_year?: number }) => {
      return apiRequest<TaxCalculation>(
        `/api/tax/jurisdictions/${data.jurisdiction}/calculate-tax?gain_loss=${data.gain_loss}&is_long_term=${data.is_long_term}&tax_year=${data.tax_year || taxYear}`,
        {
          method: "POST",
        }
      );
    },
    onSuccess: (data) => {
      toast({
        title: "Tax Calculated",
        description: `Tax liability: ${formatCurrency(data.tax_amount)}`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Export to accounting system mutation
  const exportToAccounting = useMutation({
    mutationFn: async (data: { system: string; tax_year: number }) => {
      return apiRequest(`/api/tax/export/accounting/${data.system}?tax_year=${data.tax_year}&format=csv`, {
        method: "GET",
      });
    },
    onSuccess: (data, variables) => {
      // Create download link
      const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
      const blob = new Blob([dataStr], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${variables.system}_export_${variables.tax_year}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Export Successful",
        description: `Exported to ${variables.system}`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Export Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Export to tax software mutation
  const exportToTaxSoftware = useMutation({
    mutationFn: async (data: { software: string; tax_year: number; tax_data: any }) => {
      const endpoint = data.software === "taxact" ? "/api/tax/export/taxact" : "/api/tax/export/turbotax";
      return apiRequest(endpoint, {
        method: "POST",
        body: {
          tax_year: data.tax_year,
          tax_data: data.tax_data,
        },
      });
    },
    onSuccess: (data, variables) => {
      toast({
        title: "Export Successful",
        description: `Exported to ${variables.software}`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Export Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const handleCalculateTax = () => {
    if (!gainLoss || isNaN(Number(gainLoss))) {
      toast({
        title: "Error",
        description: "Please enter a valid gain/loss amount",
        variant: "destructive",
      });
      return;
    }

    calculateTax.mutate({
      jurisdiction: selectedJurisdiction,
      gain_loss: Number(gainLoss),
      is_long_term: isLongTerm,
      tax_year: taxYear,
    });
  };

  const selectedJurisdictionData = jurisdictions?.jurisdictions.find(
    (j) => j.code === selectedJurisdiction
  );

  if (jurisdictionsLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Loading tax jurisdictions...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tax Reporting</h1>
          <p className="text-muted-foreground">Multi-jurisdiction tax calculation and reporting</p>
        </div>
      </div>

      <Tabs defaultValue="calculator" className="space-y-4">
        <TabsList>
          <TabsTrigger value="calculator">Tax Calculator</TabsTrigger>
          <TabsTrigger value="jurisdictions">Jurisdictions</TabsTrigger>
          <TabsTrigger value="exports">Exports</TabsTrigger>
        </TabsList>

        <TabsContent value="calculator" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tax Calculator */}
            <Card>
              <CardHeader>
                <CardTitle>Tax Calculator</CardTitle>
                <CardDescription>Calculate tax liability for a specific jurisdiction</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="jurisdiction">Jurisdiction</Label>
                  <Select value={selectedJurisdiction} onValueChange={setSelectedJurisdiction}>
                    <SelectTrigger id="jurisdiction">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {jurisdictions?.jurisdictions.map((j) => (
                        <SelectItem key={j.code} value={j.code}>
                          {j.name} ({j.code})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="taxYear">Tax Year</Label>
                  <Input
                    id="taxYear"
                    type="number"
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    min={2020}
                    max={2100}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gainLoss">Gain/Loss Amount</Label>
                  <Input
                    id="gainLoss"
                    type="number"
                    value={gainLoss}
                    onChange={(e) => setGainLoss(e.target.value)}
                    placeholder="Enter gain or loss amount"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="holdingPeriod">Holding Period</Label>
                  <Select
                    value={isLongTerm ? "long" : "short"}
                    onValueChange={(value) => setIsLongTerm(value === "long")}
                  >
                    <SelectTrigger id="holdingPeriod">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="short">Short-term (less than threshold)</SelectItem>
                      <SelectItem value="long">Long-term (meets threshold)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button onClick={handleCalculateTax} disabled={calculateTax.isPending} className="w-full">
                  <Calculator className="mr-2 h-4 w-4" />
                  Calculate Tax
                </Button>
              </CardContent>
            </Card>

            {/* Tax Calculation Result */}
            <Card>
              <CardHeader>
                <CardTitle>Calculation Result</CardTitle>
                <CardDescription>Tax liability breakdown</CardDescription>
              </CardHeader>
              <CardContent>
                {calculateTax.data ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-muted/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">Gain/Loss</span>
                        <span className="font-semibold">
                          {calculateTax.data.gain_loss >= 0 ? (
                            <span className="text-green-600 flex items-center gap-1">
                              <TrendingUp className="h-4 w-4" />
                              {formatCurrency(calculateTax.data.gain_loss)}
                            </span>
                          ) : (
                            <span className="text-red-600 flex items-center gap-1">
                              <TrendingDown className="h-4 w-4" />
                              {formatCurrency(calculateTax.data.gain_loss)}
                            </span>
                          )}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">Taxable Amount</span>
                        <span className="font-semibold">{formatCurrency(calculateTax.data.taxable_amount)}</span>
                      </div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">Tax Rate</span>
                        <span className="font-semibold">{calculateTax.data.tax_rate}%</span>
                      </div>
                      <div className="pt-2 border-t">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">Tax Liability</span>
                          <span className="text-2xl font-bold">{formatCurrency(calculateTax.data.tax_amount)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        {calculateTax.data.is_long_term ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-yellow-500" />
                        )}
                        <span>
                          {calculateTax.data.is_long_term ? "Long-term" : "Short-term"} holding
                        </span>
                      </div>
                      {calculateTax.data.tax_free_threshold > 0 && (
                        <div className="text-muted-foreground">
                          Tax-free threshold: {formatCurrency(calculateTax.data.tax_free_threshold)}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Enter values and click "Calculate Tax" to see results
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="jurisdictions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Supported Jurisdictions</CardTitle>
              <CardDescription>
                {jurisdictions?.count || 0} jurisdictions supported
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!jurisdictions || jurisdictions.jurisdictions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No jurisdictions found</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {jurisdictions.jurisdictions.map((jurisdiction) => (
                    <Card key={jurisdiction.code} className="cursor-pointer hover:bg-muted/50">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{jurisdiction.name}</CardTitle>
                          <Badge variant="outline">{jurisdiction.code}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Currency:</span>
                          <span className="font-medium">{jurisdiction.currency}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Long-term threshold:</span>
                          <span className="font-medium">{jurisdiction.long_term_threshold_days} days</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Tax-free threshold:</span>
                          <span className="font-medium">
                            {jurisdiction.tax_free_threshold > 0
                              ? formatCurrency(jurisdiction.tax_free_threshold)
                              : "None"}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Short-term rate:</span>
                          <span className="font-medium">{jurisdiction.short_term_rate}%</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Long-term rate:</span>
                          <span className="font-medium">{jurisdiction.long_term_rate}%</span>
                        </div>
                        <div className="pt-2 border-t">
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Calendar className="h-3 w-3" />
                            <span>Tax year: {jurisdiction.tax_year_start}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="exports" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Accounting System Exports */}
            <Card>
              <CardHeader>
                <CardTitle>Accounting System Exports</CardTitle>
                <CardDescription>Export tax data to accounting software</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="exportTaxYear">Tax Year</Label>
                  <Input
                    id="exportTaxYear"
                    type="number"
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    min={2020}
                    max={2100}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="accountingSystem">Accounting System</Label>
                  <Select
                    onValueChange={(value) => {
                      exportToAccounting.mutate({
                        system: value,
                        tax_year: taxYear,
                      });
                    }}
                  >
                    <SelectTrigger id="accountingSystem">
                      <SelectValue placeholder="Select system" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quickbooks">QuickBooks (IIF)</SelectItem>
                      <SelectItem value="xero">Xero (CSV)</SelectItem>
                      <SelectItem value="csv_generic">Generic CSV</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  onClick={() => {
                    // Trigger export
                  }}
                  disabled={exportToAccounting.isPending}
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export to Accounting System
                </Button>
              </CardContent>
            </Card>

            {/* Tax Software Exports */}
            <Card>
              <CardHeader>
                <CardTitle>Tax Software Exports</CardTitle>
                <CardDescription>Export tax data to tax preparation software</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="taxSoftwareYear">Tax Year</Label>
                  <Input
                    id="taxSoftwareYear"
                    type="number"
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    min={2020}
                    max={2100}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="taxSoftware">Tax Software</Label>
                  <Select
                    onValueChange={(value) => {
                      exportToTaxSoftware.mutate({
                        software: value,
                        tax_year: taxYear,
                        tax_data: {}, // Would include actual tax data
                      });
                    }}
                  >
                    <SelectTrigger id="taxSoftware">
                      <SelectValue placeholder="Select software" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="taxact">TaxAct</SelectItem>
                      <SelectItem value="turbotax">TurboTax</SelectItem>
                      <SelectItem value="hr_block">H&R Block</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  onClick={() => {
                    // Trigger export
                  }}
                  disabled={exportToTaxSoftware.isPending}
                  className="w-full"
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Export to Tax Software
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
