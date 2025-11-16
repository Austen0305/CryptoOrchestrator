/**
 * License Manager Component - Manage and activate licenses
 */
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useLicenseTypes, useValidateLicense, useActivateLicense, useMachineId, LicenseStatus } from "@/hooks/useLicensing";
import { Loader2, Key, CheckCircle2, XCircle, Copy, Check } from "lucide-react";
import { toast } from "@/hooks/use-toast";

export function LicenseManager() {
  const [licenseKey, setLicenseKey] = useState("");
  const [validatedLicense, setValidatedLicense] = useState<LicenseStatus | null>(null);
  const [copied, setCopied] = useState(false);
  
  const { data: licenseTypes, isLoading: typesLoading } = useLicenseTypes();
  const { data: machineId } = useMachineId();
  const validateLicense = useValidateLicense();
  const activateLicense = useActivateLicense();

  const handleValidate = async () => {
    if (!licenseKey.trim()) {
      toast({
        title: "Error",
        description: "Please enter a license key",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await validateLicense.mutateAsync({
        license_key: licenseKey,
        machine_id: machineId?.machine_id,
      });
      setValidatedLicense(result);
      
      if (result.valid) {
        toast({
          title: "License Valid",
          description: result.message || "License key is valid",
        });
      } else {
        toast({
          title: "License Invalid",
          description: result.message || "License key is invalid or expired",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to validate license",
        variant: "destructive",
      });
    }
  };

  const handleActivate = async () => {
    if (!licenseKey.trim()) {
      toast({
        title: "Error",
        description: "Please enter a license key",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await activateLicense.mutateAsync({
        license_key: licenseKey,
        machine_id: machineId?.machine_id,
      });
      
      toast({
        title: "License Activated",
        description: `Successfully activated ${result.license_type} license`,
      });
      
      setValidatedLicense(result);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to activate license",
        variant: "destructive",
      });
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({
      title: "Copied",
      description: "License key copied to clipboard",
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">License Management</h2>
        <p className="text-muted-foreground mt-1">
          Activate or validate your license key
        </p>
      </div>

      <Tabs defaultValue="activate" className="space-y-4">
        <TabsList>
          <TabsTrigger value="activate">Activate License</TabsTrigger>
          <TabsTrigger value="validate">Validate License</TabsTrigger>
          <TabsTrigger value="types">License Types</TabsTrigger>
        </TabsList>

        <TabsContent value="activate" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Activate License
              </CardTitle>
              <CardDescription>
                Enter your license key to activate the application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="license-key">License Key</Label>
                <div className="flex gap-2">
                  <Input
                    id="license-key"
                    placeholder="XXXX-XXXX-XXXX-XXXX"
                    value={licenseKey}
                    onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
                  />
                  {licenseKey && (
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleCopy(licenseKey)}
                    >
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  )}
                </div>
              </div>

              {machineId && (
                <div className="space-y-2">
                  <Label>Machine ID</Label>
                  <div className="flex gap-2">
                    <Input value={machineId.machine_id} readOnly />
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleCopy(machineId.machine_id)}
                    >
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              )}

              <Button
                onClick={handleActivate}
                disabled={!licenseKey.trim() || activateLicense.isPending}
                className="w-full"
              >
                {activateLicense.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Activating...
                  </>
                ) : (
                  <>
                    <Key className="h-4 w-4 mr-2" />
                    Activate License
                  </>
                )}
              </Button>

              {validatedLicense && (
                <div className="mt-4 p-4 rounded-lg border bg-muted">
                  <div className="flex items-center gap-2 mb-2">
                    {validatedLicense.valid ? (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500" />
                    )}
                    <span className="font-semibold">
                      {validatedLicense.valid ? "License Active" : "License Invalid"}
                    </span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Type:</span>
                      <Badge>{validatedLicense.license_type}</Badge>
                    </div>
                    {validatedLicense.expires_at && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Expires:</span>
                        <span>{new Date(validatedLicense.expires_at).toLocaleDateString()}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Max Bots:</span>
                      <span>{validatedLicense.max_bots === -1 ? "Unlimited" : validatedLicense.max_bots}</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validate" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Validate License</CardTitle>
              <CardDescription>
                Check if a license key is valid without activating it
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="validate-key">License Key</Label>
                <Input
                  id="validate-key"
                  placeholder="XXXX-XXXX-XXXX-XXXX"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
                />
              </div>

              <Button
                onClick={handleValidate}
                disabled={!licenseKey.trim() || validateLicense.isPending}
                className="w-full"
              >
                {validateLicense.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Validating...
                  </>
                ) : (
                  "Validate License"
                )}
              </Button>

              {validatedLicense && (
                <div className="mt-4 p-4 rounded-lg border bg-muted">
                  <div className="flex items-center gap-2 mb-2">
                    {validatedLicense.valid ? (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500" />
                    )}
                    <span className="font-semibold">
                      {validatedLicense.valid ? "Valid" : "Invalid"}
                    </span>
                  </div>
                  {validatedLicense.message && (
                    <p className="text-sm text-muted-foreground">{validatedLicense.message}</p>
                  )}
                  {validatedLicense.valid && (
                    <div className="mt-2 space-y-1 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Type:</span>
                        <Badge>{validatedLicense.license_type}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Features:</span>
                        <span className="text-right">{validatedLicense.features.length} features</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="types" className="space-y-4">
          {typesLoading ? (
            <Card>
              <CardContent className="py-12">
                <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {licenseTypes?.license_types && Object.entries(licenseTypes.license_types).map(([type, config]) => (
                <Card key={type}>
                  <CardHeader>
                    <CardTitle className="capitalize">{type}</CardTitle>
                    <CardDescription>
                      {config.duration_days ? `${config.duration_days}-day trial` : "No expiration"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Max Bots:</span>
                        <span className="font-medium">
                          {config.max_bots === -1 ? "Unlimited" : config.max_bots}
                        </span>
                      </div>
                      <div>
                        <div className="text-sm font-medium mb-2">Features:</div>
                        <ul className="text-sm text-muted-foreground space-y-1">
                          {config.features.map((feature, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <CheckCircle2 className="h-3 w-3 mt-0.5 text-green-500 flex-shrink-0" />
                              <span>{feature.replace('_', ' ')}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
