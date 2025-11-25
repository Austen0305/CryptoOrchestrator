/**
 * Exchange API Keys Settings Page
 * Allows users to manage their exchange API keys for real money trading
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { AlertTriangle, CheckCircle2, Plus, Trash2, Eye, EyeOff, Key, Shield, CheckCircle } from 'lucide-react';
import { apiRequest } from '@/lib/queryClient';
import { toast } from '@/components/ui/use-toast';
import { useTradingMode } from '@/contexts/TradingModeContext';
import { ExchangeStatusIndicator } from '@/components/ExchangeStatusIndicator';

interface ExchangeKey {
  id: string;
  exchange: string;
  label: string | null;
  permissions: string | null;
  is_active: boolean;
  is_testnet: boolean;
  is_validated: boolean;
  validated_at: string | null;
  last_used_at: string | null;
  created_at: string | null;
}

const SUPPORTED_EXCHANGES = [
  { name: 'binance', label: 'Binance', testnet: true },
  { name: 'kraken', label: 'Kraken', testnet: false },
  { name: 'coinbase', label: 'Coinbase Pro', testnet: false },
  { name: 'kucoin', label: 'KuCoin', testnet: true },
  { name: 'okx', label: 'OKX', testnet: true },
];

export default function ExchangeKeys() {
  const { checkRealMoneyRequirements } = useTradingMode();
  const [apiKeys, setApiKeys] = useState<ExchangeKey[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState<string | null>(null);
  const [selectedExchange, setSelectedExchange] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const [label, setLabel] = useState('');
  const [isTestnet, setIsTestnet] = useState(false);
  const [showSecrets, setShowSecrets] = useState<{ [key: string]: boolean }>({});

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    setIsLoading(true);
    try {
      const keys = await apiRequest<ExchangeKey[]>('/api/exchange-keys', {
        method: 'GET',
      });
      setApiKeys(keys);
    } catch (error: any) {
      toast({
        title: 'Failed to Load API Keys',
        description: error.message || 'Could not load exchange API keys',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddKey = async () => {
    if (!selectedExchange || !apiKey || !apiSecret) {
      toast({
        title: 'Missing Information',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      await apiRequest('/api/exchange-keys', {
        method: 'POST',
        body: {
          exchange: selectedExchange,
          api_key: apiKey,
          api_secret: apiSecret,
          passphrase: passphrase || undefined,
          label: label || undefined,
          is_testnet: isTestnet,
        },
      });

      toast({
        title: 'API Key Added',
        description: `API key for ${selectedExchange} has been added successfully`,
      });

      // Reset form
      setSelectedExchange('');
      setApiKey('');
      setApiSecret('');
      setPassphrase('');
      setLabel('');
      setIsTestnet(false);
      setShowAddDialog(false);

      // Reload keys
      await loadApiKeys();

      // Recheck requirements
      await checkRealMoneyRequirements();
    } catch (error: any) {
      toast({
        title: 'Failed to Add API Key',
        description: error.message || 'Could not add exchange API key',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleValidateKey = async (exchange: string) => {
    setIsLoading(true);
    try {
      await apiRequest(`/api/exchange-keys/${exchange}/validate`, {
        method: 'POST',
      });

      toast({
        title: 'API Key Validated',
        description: `API key for ${exchange} has been validated successfully`,
      });

      // Reload keys
      await loadApiKeys();

      // Recheck requirements
      await checkRealMoneyRequirements();
    } catch (error: any) {
      toast({
        title: 'Validation Failed',
        description: error.message || 'Could not validate API key',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteKey = async (exchange: string) => {
    setIsLoading(true);
    try {
      await apiRequest(`/api/exchange-keys/${exchange}`, {
        method: 'DELETE',
      });

      toast({
        title: 'API Key Deleted',
        description: `API key for ${exchange} has been deleted`,
      });

      // Reload keys
      await loadApiKeys();
      setShowDeleteDialog(null);

      // Recheck requirements
      await checkRealMoneyRequirements();
    } catch (error: any) {
      toast({
        title: 'Failed to Delete API Key',
        description: error.message || 'Could not delete exchange API key',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Exchange API Keys</h1>
          <p className="text-muted-foreground">
            Manage your exchange API keys for real money trading
          </p>
        </div>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add API Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Exchange API Key</DialogTitle>
              <DialogDescription>
                Enter your exchange API credentials. These will be encrypted and stored securely.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="exchange">Exchange</Label>
                <select
                  id="exchange"
                  value={selectedExchange}
                  onChange={(e) => setSelectedExchange(e.target.value)}
                  className="w-full p-2 border rounded-md"
                >
                  <option value="">Select Exchange</option>
                  {SUPPORTED_EXCHANGES.map((exchange) => (
                    <option key={exchange.name} value={exchange.name}>
                      {exchange.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="label">Label (Optional)</Label>
                <Input
                  id="label"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="My Binance Key"
                />
              </div>
              <div>
                <Label htmlFor="apiKey">API Key *</Label>
                <Input
                  id="apiKey"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter API key"
                />
              </div>
              <div>
                <Label htmlFor="apiSecret">API Secret *</Label>
                <Input
                  id="apiSecret"
                  type="password"
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  placeholder="Enter API secret"
                />
              </div>
              <div>
                <Label htmlFor="passphrase">Passphrase (Optional)</Label>
                <Input
                  id="passphrase"
                  type="password"
                  value={passphrase}
                  onChange={(e) => setPassphrase(e.target.value)}
                  placeholder="Enter passphrase (if required)"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Some exchanges (like Coinbase Pro) require a passphrase
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="testnet"
                  checked={isTestnet}
                  onCheckedChange={setIsTestnet}
                />
                <Label htmlFor="testnet">Testnet/Sandbox</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddKey} disabled={isLoading}>
                {isLoading ? 'Adding...' : 'Add API Key'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            Your exchange API keys are encrypted and stored securely. Only validated keys can be used for real money trading.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading && apiKeys.length === 0 ? (
            <div className="text-center py-8">Loading...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8">
              <Key className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No API keys configured</p>
              <p className="text-sm text-muted-foreground mt-2">
                Add an API key to enable real money trading
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Exchange</TableHead>
                  <TableHead>Label</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Validated</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.exchange.toUpperCase()}</TableCell>
                    <TableCell>{key.label || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={key.is_active ? 'default' : 'secondary'}>
                        {key.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={key.is_testnet ? 'outline' : 'default'}>
                        {key.is_testnet ? 'Testnet' : 'Live'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {key.is_validated ? (
                        <Badge variant="default" className="bg-green-500">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Validated
                        </Badge>
                      ) : (
                        <Badge variant="outline">Not Validated</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {key.last_used_at
                        ? new Date(key.last_used_at).toLocaleDateString()
                        : 'Never'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {!key.is_validated && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleValidateKey(key.exchange)}
                            disabled={isLoading}
                          >
                            Validate
                          </Button>
                        )}
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => setShowDeleteDialog(key.exchange)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete API Key?</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to delete the API key for {key.exchange}?
                                This action cannot be undone.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeleteKey(key.exchange)}
                                className="bg-red-500 hover:bg-red-600"
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Security Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-2">
            <Shield className="h-5 w-5 text-blue-500 mt-0.5" />
            <div>
              <p className="font-semibold">Encryption</p>
              <p className="text-sm text-muted-foreground">
                All API keys are encrypted at rest using industry-standard encryption.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
            <div>
              <p className="font-semibold">Permissions</p>
              <p className="text-sm text-muted-foreground">
                When creating API keys on exchanges, use the minimum permissions required (read, write, trade).
                Never share your API keys with anyone.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5" />
            <div>
              <p className="font-semibold">Validation</p>
              <p className="text-sm text-muted-foreground">
                API keys must be validated before they can be used for real money trading.
                Validation tests the connection to the exchange.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Exchange Status Indicator */}
      <ExchangeStatusIndicator />
    </div>
  );
}

