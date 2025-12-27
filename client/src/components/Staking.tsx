import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TrendingUp, Lock, Unlock, DollarSign } from "lucide-react";
import { useStakingOptions, useMyStakes, useStake, useUnstake, type StakingOption } from "@/hooks/useStaking";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { useToast } from "@/hooks/use-toast";
import { stakeSchema, unstakeSchema, validateAmount, formatCurrencyInput } from "@/lib/validation";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { ZodError } from "zod";

interface Stake {
  asset: string;
  staked_amount: number;
  rewards: {
    asset: string;
    staked_amount: number;
    apy: number;
    daily_rewards: number;
    monthly_rewards: number;
    yearly_rewards: number;
  };
}

export function Staking() {
  const { data: options, isLoading: optionsLoading, error: optionsError, refetch: refetchOptions } = useStakingOptions();
  const { data: myStakes, isLoading: stakesLoading, error: stakesError, refetch: refetchStakes } = useMyStakes();
  const stake = useStake();
  const unstake = useUnstake();
  const { toast } = useToast();
  
  const [showStakeDialog, setShowStakeDialog] = useState(false);
  const [showUnstakeDialog, setShowUnstakeDialog] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState("");
  const [stakeAmount, setStakeAmount] = useState("");
  const [unstakeAmount, setUnstakeAmount] = useState("");
  
  const handleStake = async () => {
    if (!selectedAsset) {
      toast({
        title: "Asset Required",
        description: "Please select an asset to stake",
        variant: "destructive"
      });
      return;
    }
    
    const amount = parseFloat(stakeAmount);
    
    // Validate amount
    const amountValidation = validateAmount(amount, 0.00000001);
    if (!amountValidation.valid) {
      toast({
        title: "Invalid Amount",
        description: amountValidation.error,
        variant: "destructive"
      });
      return;
    }
    
    // Check minimum staking amount
    const selectedOption = options?.options?.find((opt: StakingOption) => opt.asset === selectedAsset);
    if (selectedOption && amount < selectedOption.min_amount) {
      toast({
        title: "Amount Too Small",
        description: `Minimum staking amount is ${selectedOption.min_amount} ${selectedAsset}`,
        variant: "destructive"
      });
      return;
    }
    
    // Validate with schema
    try {
      stakeSchema.parse({
        asset: selectedAsset,
        amount
      });
    } catch (error) {
      const zodError = error instanceof ZodError ? error : null;
      toast({
        title: "Validation Error",
        description: zodError?.issues?.[0]?.message || "Invalid staking data",
        variant: "destructive"
      });
      return;
    }
    
    try {
      await stake.mutateAsync({
        asset: selectedAsset,
        amount
      });
      toast({
        title: "Staking Successful",
        description: `Successfully staked ${stakeAmount} ${selectedAsset}`
      });
      setShowStakeDialog(false);
      setStakeAmount("");
      setSelectedAsset("");
    } catch (error) {
      toast({
        title: "Staking Failed",
        description: error instanceof Error ? error.message : "Failed to stake assets",
        variant: "destructive"
      });
    }
  };
  
  const handleUnstake = async () => {
    if (!selectedAsset) {
      toast({
        title: "Asset Required",
        description: "Please select an asset to unstake",
        variant: "destructive"
      });
      return;
    }
    
    const amount = parseFloat(unstakeAmount);
    
    // Validate amount
    const amountValidation = validateAmount(amount, 0.00000001);
    if (!amountValidation.valid) {
      toast({
        title: "Invalid Amount",
        description: amountValidation.error,
        variant: "destructive"
      });
      return;
    }
    
    // Check available staked amount
    const selectedStake = myStakes?.stakes?.find((s: Stake) => s.asset === selectedAsset);
    if (selectedStake && amount > selectedStake.staked_amount) {
      toast({
        title: "Insufficient Staked Amount",
        description: `Available staked: ${selectedStake.staked_amount} ${selectedAsset}`,
        variant: "destructive"
      });
      return;
    }
    
    // Validate with schema
    try {
      unstakeSchema.parse({
        asset: selectedAsset,
        amount
      });
    } catch (error) {
      const zodError = error instanceof ZodError ? error : null;
      toast({
        title: "Validation Error",
        description: zodError?.issues?.[0]?.message || "Invalid unstaking data",
        variant: "destructive"
      });
      return;
    }
    
    try {
      await unstake.mutateAsync({
        asset: selectedAsset,
        amount
      });
      toast({
        title: "Unstaking Successful",
        description: `Successfully unstaked ${unstakeAmount} ${selectedAsset}`
      });
      setShowUnstakeDialog(false);
      setUnstakeAmount("");
      setSelectedAsset("");
    } catch (error) {
      toast({
        title: "Unstaking Failed",
        description: error instanceof Error ? error.message : "Failed to unstake assets",
        variant: "destructive"
      });
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Staking Options */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Staking Rewards
              </CardTitle>
              <CardDescription>
                Earn passive income by staking your crypto assets
              </CardDescription>
            </div>
            <Dialog open={showStakeDialog} onOpenChange={setShowStakeDialog}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Lock className="h-4 w-4" />
                  Stake Assets
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Stake Assets</DialogTitle>
                  <DialogDescription>
                    Stake your assets to earn rewards
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Asset</label>
                    <Select value={selectedAsset} onValueChange={setSelectedAsset}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select asset" />
                      </SelectTrigger>
                      <SelectContent>
                        {options?.options && Array.isArray(options.options) ? options.options.map((opt: StakingOption) => (
                          <SelectItem key={opt.asset} value={opt.asset}>
                            {opt.asset} - {opt.apy}% APY
                          </SelectItem>
                        )) : null}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Amount</label>
                    <Input
                      type="text"
                      placeholder="0.00"
                      value={stakeAmount}
                      onChange={(e) => {
                        const formatted = formatCurrencyInput(e.target.value);
                        setStakeAmount(formatted);
                      }}
                      min="0"
                      step="0.00000001"
                    />
                    {selectedAsset && options?.options?.find((o: StakingOption) => o.asset === selectedAsset) && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Min: {options.options.find((o: StakingOption) => o.asset === selectedAsset)?.min_amount} {selectedAsset}
                      </p>
                    )}
                  </div>
                  <Button 
                    onClick={handleStake} 
                    className="w-full"
                    disabled={stake.isPending}
                  >
                    {stake.isPending ? "Processing..." : "Stake"}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {optionsLoading ? (
            <LoadingSkeleton count={3} className="h-32 w-full mb-4" />
          ) : optionsError ? (
            <ErrorRetry
              title="Failed to load staking options"
              message={optionsError instanceof Error ? optionsError.message : "An unexpected error occurred."}
              onRetry={() => refetchOptions()}
              error={optionsError as Error}
            />
          ) : options?.options && options.options.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {options?.options && Array.isArray(options.options) ? options.options.map((option: StakingOption) => (
                <Card key={option.asset}>
                  <CardHeader>
                    <CardTitle className="text-lg">{option.asset}</CardTitle>
                    <CardDescription>{option.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">APY</span>
                        <Badge variant="default">{formatPercentage(option.apy)}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Min Amount</span>
                        <span className="text-sm font-medium">{option.min_amount} {option.asset}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )) : null}
            </div>
          ) : (
            <EmptyState
              icon={TrendingUp}
              title="No staking options available"
              description="Staking options are currently unavailable. Please check back later."
            />
          )}
        </CardContent>
      </Card>
      
      {/* My Stakes */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>My Staked Assets</CardTitle>
              <CardDescription>
                View your staked assets and rewards
              </CardDescription>
            </div>
            <Dialog open={showUnstakeDialog} onOpenChange={setShowUnstakeDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="gap-2">
                  <Unlock className="h-4 w-4" />
                  Unstake
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Unstake Assets</DialogTitle>
                  <DialogDescription>
                    Unstake your assets to return them to your trading wallet
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Asset</label>
                    <Select value={selectedAsset} onValueChange={setSelectedAsset}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select asset" />
                      </SelectTrigger>
                      <SelectContent>
                        {myStakes?.stakes?.map((stake: Stake) => (
                          <SelectItem key={stake.asset} value={stake.asset}>
                            {stake.asset} - {stake.staked_amount} staked
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Amount</label>
                    <Input
                      type="text"
                      placeholder="0.00"
                      value={unstakeAmount}
                      onChange={(e) => {
                        const formatted = formatCurrencyInput(e.target.value);
                        setUnstakeAmount(formatted);
                      }}
                      min="0"
                      step="0.00000001"
                    />
                    {selectedAsset && myStakes?.stakes?.find((s: Stake) => s.asset === selectedAsset) && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Available: {myStakes.stakes.find((s: Stake) => s.asset === selectedAsset)?.staked_amount} {selectedAsset}
                      </p>
                    )}
                  </div>
                  <Button 
                    onClick={handleUnstake} 
                    className="w-full"
                    disabled={unstake.isPending}
                  >
                    {unstake.isPending ? "Processing..." : "Unstake"}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {stakesLoading ? (
            <LoadingSkeleton count={5} className="h-12 w-full mb-2" />
          ) : stakesError ? (
            <ErrorRetry
              title="Failed to load staked assets"
              message={stakesError instanceof Error ? stakesError.message : "An unexpected error occurred."}
              onRetry={() => refetchStakes()}
              error={stakesError as Error}
            />
          ) : myStakes?.stakes && myStakes.stakes.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Asset</TableHead>
                  <TableHead>Staked Amount</TableHead>
                  <TableHead>APY</TableHead>
                  <TableHead>Daily Rewards</TableHead>
                  <TableHead>Monthly Rewards</TableHead>
                  <TableHead>Yearly Rewards</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {myStakes?.stakes && Array.isArray(myStakes.stakes) ? myStakes.stakes.map((stake: Stake) => (
                  <TableRow key={stake.asset}>
                    <TableCell className="font-medium">{stake.asset}</TableCell>
                    <TableCell>{stake.staked_amount} {stake.asset}</TableCell>
                    <TableCell>
                      <Badge>{formatPercentage(stake.rewards.apy)}</Badge>
                    </TableCell>
                    <TableCell>{stake.rewards.daily_rewards.toFixed(6)} {stake.asset}</TableCell>
                    <TableCell>{stake.rewards.monthly_rewards.toFixed(6)} {stake.asset}</TableCell>
                    <TableCell className="font-semibold text-green-500">
                      {stake.rewards.yearly_rewards.toFixed(6)} {stake.asset}
                    </TableCell>
                  </TableRow>
                )) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                      No staked assets found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              icon={Lock}
              title="No staked assets yet"
              description="Start staking your assets to earn passive rewards. Select an asset above to get started."
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

