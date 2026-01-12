import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateDCABot } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import { Loader2, X } from "lucide-react";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

const dcaBotSchema = z.object({
  name: z.string().min(1).max(100),
  symbol: z.string().min(1),
  exchange: z.string().min(1),
  total_investment: z.number().positive(),
  order_amount: z.number().positive(),
  interval_minutes: z.number().int().min(1),
  trading_mode: z.enum(["paper", "real"]),
  max_orders: z.number().int().positive().optional(),
  use_martingale: z.boolean(),
  martingale_multiplier: z.number().min(1.0).optional(),
  martingale_max_multiplier: z.number().min(1.0).optional(),
  take_profit_percent: z.number().positive().optional(),
  stop_loss_percent: z.number().positive().optional(),
});

type DCABotFormData = z.infer<typeof dcaBotSchema>;

interface DCABotCreatorProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function DCABotCreator({ onSuccess, onCancel }: DCABotCreatorProps) {
  const createBot = useCreateDCABot();
  const form = useForm<DCABotFormData>({
    resolver: zodResolver(dcaBotSchema as any),
    defaultValues: {
      name: "",
      symbol: "BTC/USD",
      exchange: "binance",
      total_investment: 1000,
      order_amount: 100,
      interval_minutes: 60,
      trading_mode: "paper",
      use_martingale: false,
      martingale_multiplier: 1.5,
      martingale_max_multiplier: 5.0,
    },
  });

  const onSubmit = async (data: DCABotFormData) => {
    try {
      await createBot.mutateAsync(data);
      toast({ title: "DCA Bot Created", description: "Your DCA bot has been created successfully." });
      onSuccess();
      form.reset();
    } catch (error: any) {
      toast({ title: "Error", description: error?.message || "Failed to create DCA bot.", variant: "destructive" });
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Create DCA Bot</CardTitle>
            <CardDescription>Configure your dollar cost averaging bot</CardDescription>
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
                <FormControl><Input placeholder="My DCA Bot" {...field} /></FormControl>
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
              <FormField control={form.control} name="total_investment" render={({ field }) => (
                <FormItem>
                  <FormLabel>Total Investment</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.01" {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="order_amount" render={({ field }) => (
                <FormItem>
                  <FormLabel>Order Amount</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.01" {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </div>
            <FormField control={form.control} name="interval_minutes" render={({ field }) => (
              <FormItem>
                <FormLabel>Interval (minutes)</FormLabel>
                <FormControl>
                  <Input type="number" min={1} {...field} onChange={(e) => field.onChange(parseInt(e.target.value))} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />
            <FormField control={form.control} name="use_martingale" render={({ field }) => (
              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                <div className="space-y-0.5">
                  <FormLabel className="text-base">Use Martingale</FormLabel>
                  <FormDescription>Increase order size after losses</FormDescription>
                </div>
                <FormControl>
                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                </FormControl>
              </FormItem>
            )} />
            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
              <Button type="submit" disabled={createBot.isPending}>
                {createBot.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Bot
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

