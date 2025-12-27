import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateFuturesPosition } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import { Loader2, X } from "lucide-react";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const futuresPositionSchema = z.object({
  symbol: z.string().min(1),
  exchange: z.string().min(1),
  side: z.enum(["long", "short"]),
  quantity: z.number().positive(),
  leverage: z.number().int().min(1).max(125),
  trading_mode: z.enum(["paper", "real"]),
  entry_price: z.number().positive().optional(),
  stop_loss_price: z.number().positive().optional(),
  take_profit_price: z.number().positive().optional(),
  name: z.string().max(100).optional(),
});

type FuturesPositionFormData = z.infer<typeof futuresPositionSchema>;

interface FuturesPositionCreatorProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function FuturesPositionCreator({ onSuccess, onCancel }: FuturesPositionCreatorProps) {
  const createPosition = useCreateFuturesPosition();
  const form = useForm<FuturesPositionFormData>({
    resolver: zodResolver(futuresPositionSchema),
    defaultValues: {
      symbol: "BTC/USD",
      exchange: "binance",
      side: "long",
      quantity: 0.1,
      leverage: 10,
      trading_mode: "paper",
    },
  });

  const onSubmit = async (data: FuturesPositionFormData) => {
    try {
      await createPosition.mutateAsync(data);
      toast({ title: "Position Opened", description: "Your futures position has been opened successfully." });
      onSuccess();
      form.reset();
    } catch (error: any) {
      toast({ title: "Error", description: error?.message || "Failed to open position.", variant: "destructive" });
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Open Futures Position</CardTitle>
            <CardDescription>Configure your futures position with leverage</CardDescription>
          </div>
          <Button variant="ghost" size="icon" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField control={form.control} name="name" render={({ field }) => (
              <FormItem>
                <FormLabel>Position Name (Optional)</FormLabel>
                <FormControl><Input placeholder="My Futures Position" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )} />
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="symbol" render={({ field }) => (
                <FormItem>
                  <FormLabel>Symbol</FormLabel>
                  <FormControl><Input placeholder="BTC/USD" {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="exchange" render={({ field }) => (
                <FormItem>
                  <FormLabel>Exchange</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value="binance">Binance</SelectItem>
                      <SelectItem value="kraken">Kraken</SelectItem>
                      <SelectItem value="coinbase">Coinbase</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="side" render={({ field }) => (
                <FormItem>
                  <FormLabel>Side</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value="long">Long</SelectItem>
                      <SelectItem value="short">Short</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="leverage" render={({ field }) => (
                <FormItem>
                  <FormLabel>Leverage</FormLabel>
                  <FormControl>
                    <Input type="number" min={1} max={125} {...field} onChange={(e) => field.onChange(parseInt(e.target.value))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="quantity" render={({ field }) => (
                <FormItem>
                  <FormLabel>Quantity</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.01" {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="trading_mode" render={({ field }) => (
                <FormItem>
                  <FormLabel>Trading Mode</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value="paper">Paper Trading</SelectItem>
                      <SelectItem value="real">Real Trading</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="stop_loss_price" render={({ field }) => (
                <FormItem>
                  <FormLabel>Stop Loss Price (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      {...field}
                      onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                      value={field.value || ""}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="take_profit_price" render={({ field }) => (
                <FormItem>
                  <FormLabel>Take Profit Price (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      {...field}
                      onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                      value={field.value || ""}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
              <Button type="submit" disabled={createPosition.isPending}>
                {createPosition.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Open Position
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

