/**
 * Licensing Page - License management and activation
 */
import { LicenseManager } from "@/components/LicenseManager";
import { PricingPlans } from "@/components/PricingPlans";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Key, CreditCard } from "lucide-react";

export default function Licensing() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Licensing & Billing</h1>
        <p className="text-muted-foreground mt-1">
          Manage your license and subscription
        </p>
      </div>

      <Tabs defaultValue="license" className="space-y-4">
        <TabsList>
          <TabsTrigger value="license">
            <Key className="h-4 w-4 mr-2" />
            License
          </TabsTrigger>
          <TabsTrigger value="pricing">
            <CreditCard className="h-4 w-4 mr-2" />
            Pricing & Plans
          </TabsTrigger>
        </TabsList>

        <TabsContent value="license" className="space-y-4">
          <LicenseManager />
        </TabsContent>

        <TabsContent value="pricing" className="space-y-4">
          <PricingPlans />
        </TabsContent>
      </Tabs>
    </div>
  );
}
