import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Bot, Send, Loader2, Sparkles, TrendingUp, DollarSign, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/formatters";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  suggestions?: string[];
  tradeAction?: {
    symbol: string;
    action: "buy" | "sell";
    amount: number;
    price?: number;
  };
}

export function AITradingAssistant() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your AI Trading Assistant. I can help you with trading decisions, portfolio analysis, and strategy suggestions. Try saying: 'Buy $500 of BTC when it dips below $45k' or 'Analyze my portfolio'",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // Use React Query mutation for AI assistant API calls
  const aiAssistantMutation = useMutation({
    mutationFn: async (message: string) => {
      return await apiRequest<{
        content: string;
        suggestions?: string[];
        tradeAction?: Message["tradeAction"];
      }>("/api/ai/assistant", {
        method: "POST",
        body: JSON.stringify({ message }),
      });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to get AI response",
        variant: "destructive",
      });
      // Fallback to local response on error
      const userMessage = input.trim();
      if (userMessage) {
        const response = generateAIResponse(userMessage);
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: response.content,
          timestamp: new Date(),
          suggestions: response.suggestions,
          tradeAction: response.tradeAction,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    },
  });

  const handleSend = async (message?: string) => {
    const userMessage = message || input.trim();
    if (!userMessage) return;

    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    try {
      // Try to call API first, fallback to local response
      const response = await aiAssistantMutation.mutateAsync(userMessage);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.content,
        timestamp: new Date(),
        suggestions: response.suggestions,
        tradeAction: response.tradeAction,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      // Error handling is done in onError callback
      // Fallback to local response
      const response = generateAIResponse(userMessage);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.content,
        timestamp: new Date(),
        suggestions: response.suggestions,
        tradeAction: response.tradeAction,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }
  };

  const generateAIResponse = (
    userInput: string
  ): { content: string; suggestions?: string[]; tradeAction?: Message["tradeAction"] } => {
    const lowerInput = userInput.toLowerCase();

    // Buy order detection
    if (lowerInput.includes("buy") || lowerInput.includes("purchase")) {
      const symbolMatch = userInput.match(/(\w+)\/?(\w+)?/i);
      const amountMatch = userInput.match(/\$?([\d,]+\.?\d*)/);
      const priceMatch = userInput.match(/(?:below|under|when|at)\s*\$?([\d,]+\.?\d*)/i);

      const symbol = symbolMatch
        ? symbolMatch[2]
          ? `${symbolMatch[1] || "BTC"}/${symbolMatch[2]}`
          : symbolMatch[1] || "BTC/USD"
        : "BTC/USD";
      const amount =
        amountMatch && amountMatch[1] ? parseFloat(amountMatch[1].replace(/,/g, "")) : 500;
      const price =
        priceMatch && priceMatch[1] ? parseFloat(priceMatch[1].replace(/,/g, "")) : undefined;

      return {
        content: `I'll help you set up a buy order for ${symbol}${amount ? ` worth ${formatCurrency(amount)}` : ""}${price ? ` when the price drops below ${formatCurrency(price)}` : ""}. Would you like me to create this order now?`,
        suggestions: ["Confirm Order", "Set Alert Instead", "Analyze First"],
        tradeAction: {
          symbol,
          action: "buy",
          amount,
          price,
        },
      };
    }

    // Sell order detection
    if (lowerInput.includes("sell")) {
      return {
        content:
          "I can help you set up a sell order. Please specify the symbol and amount, or I can analyze your portfolio and suggest the best positions to sell.",
        suggestions: ["Show My Positions", "Sell All BTC", "Take Profit 10%"],
      };
    }

    // Portfolio analysis
    if (lowerInput.includes("portfolio") || lowerInput.includes("analyze")) {
      return {
        content:
          "Analyzing your portfolio... Your current allocation shows: BTC 65%, ETH 25%, Other 10%. Risk level: Moderate. Recommendations: Consider diversifying to reduce BTC concentration risk. Your Sharpe ratio is 1.8, which is good. Overall portfolio health: 85/100.",
        suggestions: ["Rebalance Portfolio", "View Detailed Analysis", "Compare to Benchmark"],
      };
    }

    // Price inquiry
    if (lowerInput.includes("price") || lowerInput.includes("how much")) {
      return {
        content:
          "Current prices: BTC/USD: $47,350 (+4.76%), ETH/USD: $2,920 (+2.1%), SOL/USD: $142 (-0.5%). Would you like more details on any specific asset?",
        suggestions: ["BTC Analysis", "ETH Analysis", "Set Price Alert"],
      };
    }

    // Default response
    return {
      content:
        "I understand you're asking about trading. I can help you with:\n- Creating buy/sell orders\n- Analyzing your portfolio\n- Setting price alerts\n- Getting market insights\n- Strategy recommendations\n\nTry saying something like: 'Buy $500 of BTC' or 'Analyze my portfolio'",
      suggestions: ["Show Examples", "View Portfolio", "Market Overview"],
    };
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSend(suggestion);
  };

  const handleTradeAction = (action: Message["tradeAction"]) => {
    if (!action) return;
    // In production, this would open the order entry panel or execute the trade
    alert(
      `Executing ${action.action.toUpperCase()} order: ${action.amount} ${action.symbol}${action.price ? ` at ${formatCurrency(action.price)}` : ""}`
    );
  };

  return (
    <Card className="w-full h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-yellow-500" />
          AI Trading Assistant
        </CardTitle>
        <CardDescription>
          Natural language trading interface - ask me anything about trading
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0">
        {/* Messages */}
        <ScrollArea className="flex-1 pr-4" ref={scrollAreaRef}>
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex gap-3",
                  message.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                )}
                <div
                  className={cn(
                    "rounded-lg px-4 py-2 max-w-[80%]",
                    message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                  )}
                >
                  <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                  {message.suggestions && message.suggestions.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {message.suggestions?.map((suggestion, index) => (
                        <Button
                          key={index}
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          onClick={() => handleSuggestionClick(suggestion)}
                        >
                          {suggestion}
                        </Button>
                      ))}
                    </div>
                  )}
                  {message.tradeAction && (
                    <div className="mt-3 p-3 rounded-md border bg-background/50">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium text-sm">Proposed Trade</div>
                        <Button size="sm" onClick={() => handleTradeAction(message.tradeAction)}>
                          Execute
                        </Button>
                      </div>
                      <div className="text-xs space-y-1">
                        <div>Symbol: {message.tradeAction.symbol}</div>
                        <div>Action: {message.tradeAction.action.toUpperCase()}</div>
                        <div>Amount: {formatCurrency(message.tradeAction.amount)}</div>
                        {message.tradeAction.price && (
                          <div>Trigger Price: {formatCurrency(message.tradeAction.price)}</div>
                        )}
                      </div>
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
                {message.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-medium text-primary-foreground">U</span>
                  </div>
                )}
              </div>
            ))}
            {aiAssistantMutation.isPending && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div className="rounded-lg px-4 py-2 bg-muted">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4 pt-4 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSend("Analyze my portfolio")}
            className="text-xs"
          >
            <DollarSign className="h-3 w-3 mr-1" />
            Analyze Portfolio
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSend("Show market overview")}
            className="text-xs"
          >
            <TrendingUp className="h-3 w-3 mr-1" />
            Market Overview
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSend("What should I trade?")}
            className="text-xs"
          >
            <Sparkles className="h-3 w-3 mr-1" />
            Suggestions
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSend("Show my alerts")}
            className="text-xs"
          >
            <AlertCircle className="h-3 w-3 mr-1" />
            My Alerts
          </Button>
        </div>

        {/* Input */}
        <div className="flex gap-2 mt-4 pt-4 border-t">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask me anything... e.g., 'Buy $500 of BTC when it dips below $45k'"
            className="flex-1"
            disabled={aiAssistantMutation.isPending}
          />
          <Button
            onClick={() => handleSend()}
            disabled={aiAssistantMutation.isPending || !input.trim()}
          >
            {aiAssistantMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
