import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCreateGridBot } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import { Loader2, X } from "lucide-react";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const gridBotSchema = z.object({
  name: z.string().min(1, "Name is required").max(100, "Name too long"),
  symbol: z.string().min(1, "Symbol is required"),
  exchange: z.string().min(1, "Exchange is required"),
  upper_price: z.number().positive("Upper price must be positive"),
  lower_price: z.number().positive("Lower price must be positive"),
  grid_count: z.number().int().min(2).max(100),
  order_amount: z.number().positive("Order amount must be positive"),
  trading_mode: z.enum(["paper", "real"]),
  grid_spacing_type: z.enum(["arithmetic", "geometric"]),
}).refine((data) => data.upper_price > data.lower_price, {
  message: "Upper price must be greater than lower price",
  path: ["upper_price"],
});

type GridBotFormData = z.infer<typeof gridBotSchema>;

interface GridBotCreatorProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function GridBotCreator({ onSuccess, onCancel }: GridBotCreatorProps) {
  const createBot = useCreateGridBot();
  const form = useForm<GridBotFormData>({
    resolver: zodResolver(gridBotSchema as any),
    defaultValues: {
      name: "",
      symbol: "BTC/USD",
      exchange: "binance",
      upper_price: 50000,
      lower_price: 45000,
      grid_count: 10,
      order_amount: 100,
      trading_mode: "paper",
      grid_spacing_type: "arithmetic",
    },
  });

  const onSubmit = async (data: GridBotFormData) => {
    try {
      await createBot.mutateAsync(data);
      toast({
        title: "Grid Bot Created",
        description: "Your grid trading bot has been created successfully.",
      });
      onSuccess();
      form.reset();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error?.message || "Failed to create grid bot.",
        variant: "destructive",
      });
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Create Grid Trading Bot</CardTitle>
            <CardDescription>
              Configure your grid trading bot to profit from volatility
            </CardDescription>
          </div>
          <Button variant="ghost" size="icon" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Bot Name</FormLabel>
                  <FormControl>
                    <Input placeholder="My Grid Bot" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="symbol"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Trading Symbol</FormLabel>
                    <FormControl>
                      <Input placeholder="BTC/USD" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="exchange"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Exchange</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select exchange" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="binance">Binance</SelectItem>
                        <SelectItem value="kraken">Kraken</SelectItem>
                        <SelectItem value="coinbase">Coinbase</SelectItem>
                        <SelectItem value="kucoin">KuCoin</SelectItem>
                        <SelectItem value="bybit">Bybit</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="lower_price"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Lower Price</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        {...field}
                        onChange={(e) => field.onChange(parseFloat(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="upper_price"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Upper Price</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        {...field}
                        onChange={(e) => field.onChange(parseFloat(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="grid_count"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Grid Levels</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={2}
                        max={100}
                        {...field}
                        onChange={(e) => field.onChange(parseInt(e.target.value))}
                      />
                    </FormControl>
                    <FormDescription>Number of grid levels (2-100)</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="order_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Order Amount</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        {...field}
                        onChange={(e) => field.onChange(parseFloat(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="grid_spacing_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Grid Spacing</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="arithmetic">Arithmetic</SelectItem>
                        <SelectItem value="geometric">Geometric</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="trading_mode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Trading Mode</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="paper">Paper Trading</SelectItem>
                        <SelectItem value="real">Real Trading</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
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

