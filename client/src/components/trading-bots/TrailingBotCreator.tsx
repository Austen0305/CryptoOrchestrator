import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateTrailingBot } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import { Loader2, X } from "lucide-react";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const trailingBotSchema = z.object({
  name: z.string().min(1).max(100),
  symbol: z.string().min(1),
  exchange: z.string().min(1),
  bot_type: z.enum(["trailing_buy", "trailing_sell"]),
  trailing_percent: z.number().positive(),
  order_amount: z.number().positive(),
  trading_mode: z.enum(["paper", "real"]),
  max_price: z.number().positive().optional(),
  min_price: z.number().positive().optional(),
});

type TrailingBotFormData = z.infer<typeof trailingBotSchema>;

interface TrailingBotCreatorProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function TrailingBotCreator({ onSuccess, onCancel }: TrailingBotCreatorProps) {
  const createBot = useCreateTrailingBot();
  const form = useForm<TrailingBotFormData>({
    resolver: zodResolver(trailingBotSchema),
    defaultValues: {
      name: "",
      symbol: "BTC/USD",
      exchange: "binance",
      bot_type: "trailing_buy",
      trailing_percent: 2.0,
      order_amount: 100,
      trading_mode: "paper",
    },
  });

  const onSubmit = async (data: TrailingBotFormData) => {
    try {
      await createBot.mutateAsync(data);
      toast({ title: "Trailing Bot Created", description: "Your trailing bot has been created successfully." });
      onSuccess();
      form.reset();
    } catch (error: any) {
      toast({ title: "Error", description: error?.message || "Failed to create trailing bot.", variant: "destructive" });
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Create Trailing Bot</CardTitle>
            <CardDescription>Configure your trailing buy/sell bot</CardDescription>
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
                <FormControl><Input placeholder="My Trailing Bot" {...field} /></FormControl>
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
            <FormField control={form.control} name="bot_type" render={({ field }) => (
              <FormItem>
                <FormLabel>Bot Type</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                  <SelectContent>
                    <SelectItem value="trailing_buy">Trailing Buy</SelectItem>
                    <SelectItem value="trailing_sell">Trailing Sell</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )} />
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="trailing_percent" render={({ field }) => (
                <FormItem>
                  <FormLabel>Trailing %</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.1" {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
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
                Create Bot
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

