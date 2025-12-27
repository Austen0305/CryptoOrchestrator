import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateInfinityGrid } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import { Loader2, X } from "lucide-react";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const infinityGridSchema = z.object({
  name: z.string().min(1).max(100),
  symbol: z.string().min(1),
  exchange: z.string().min(1),
  grid_count: z.number().int().min(2).max(100),
  grid_spacing_percent: z.number().positive(),
  order_amount: z.number().positive(),
  trading_mode: z.enum(["paper", "real"]),
  upper_adjustment_percent: z.number().positive().optional(),
  lower_adjustment_percent: z.number().positive().optional(),
});

type InfinityGridFormData = z.infer<typeof infinityGridSchema>;

interface InfinityGridCreatorProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function InfinityGridCreator({ onSuccess, onCancel }: InfinityGridCreatorProps) {
  const createBot = useCreateInfinityGrid();
  const form = useForm<InfinityGridFormData>({
    resolver: zodResolver(infinityGridSchema),
    defaultValues: {
      name: "",
      symbol: "BTC/USD",
      exchange: "binance",
      grid_count: 10,
      grid_spacing_percent: 1.0,
      order_amount: 100,
      trading_mode: "paper",
      upper_adjustment_percent: 5.0,
      lower_adjustment_percent: 5.0,
    },
  });

  const onSubmit = async (data: InfinityGridFormData) => {
    try {
      await createBot.mutateAsync(data);
      toast({ title: "Infinity Grid Created", description: "Your infinity grid has been created successfully." });
      onSuccess();
      form.reset();
    } catch (error: any) {
      toast({ title: "Error", description: error?.message || "Failed to create infinity grid.", variant: "destructive" });
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Create Infinity Grid</CardTitle>
            <CardDescription>Configure your dynamic infinity grid bot</CardDescription>
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
                <FormLabel>Bot Name</FormLabel>
                <FormControl><Input placeholder="My Infinity Grid" {...field} /></FormControl>
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
              <FormField control={form.control} name="grid_count" render={({ field }) => (
                <FormItem>
                  <FormLabel>Grid Levels</FormLabel>
                  <FormControl>
                    <Input type="number" min={2} max={100} {...field} onChange={(e) => field.onChange(parseInt(e.target.value))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="grid_spacing_percent" render={({ field }) => (
                <FormItem>
                  <FormLabel>Grid Spacing (%)</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.1" {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </div>
            <FormField control={form.control} name="order_amount" render={({ field }) => (
              <FormItem>
                <FormLabel>Order Amount</FormLabel>
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
            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
              <Button type="submit" disabled={createBot.isPending}>
                {createBot.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Grid
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

