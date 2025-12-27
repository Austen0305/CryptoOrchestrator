import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { useAuth } from '../hooks/useAuth';
import { Eye, EyeOff, Shield, Key } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  const [showPassword, setShowPassword] = useState(false);
  const [showMFASetup, setShowMFASetup] = useState(false);
  const [mfaSecret, setMfaSecret] = useState('');
  const [mfaToken, setMfaToken] = useState('');
  // Captcha disabled; keep refs minimal without unused state noise
  const [mfaQrUrl, setMfaQrUrl] = useState<string | null>(null);

  const {
    login,
    register,
    setupMFA,
    verifyMFA,
    isLoading,
    user,
    error: authError,
  // isAuthenticated unused here
  } = useAuth();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError(null);

      if (activeTab === 'login') {
        const success = await login(formData.email, formData.password);
        if (success && !user?.mfaEnabled) {
          setShowMFASetup(true);
        } else if (success) {
          onClose();
        }
      } else {
        // Extract username from email (default) or use name if provided
        const trimmedName = formData.name?.trim() || '';
        const emailUsername = formData.email.split('@')[0] || 'user';
        const nameParts = trimmedName ? trimmedName.split(/\s+/) : [];
        const firstPart = nameParts.length > 0 ? nameParts[0] : '';
        const username = trimmedName && firstPart
          ? firstPart.toLowerCase().replace(/[^a-z0-9]/g, '') || emailUsername
          : emailUsername;
        
        // Split name into first and last name if provided
        const firstName = nameParts.length > 0 ? nameParts[0] : undefined;
        const lastName = nameParts.length > 1 ? nameParts.slice(1).join(' ') : undefined;
        
        const success = await register(
          formData.email,
          username,
          formData.password,
          firstName,
          lastName
        );
        
        // Wait a moment for authError to update if registration failed
        await new Promise(resolve => setTimeout(resolve, 100));
        
        if (!success) {
          // Registration failed - display error from useAuth hook if available
          const errorMsg = authError || 'Unable to create your account. Please try again.';
          setError(errorMsg);
        } else {
          // Registration successful - close modal and let user proceed
          // MFA setup can be done later from settings
          onClose();
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleMFASetup = async () => {
    try {
      const result = await setupMFA();
      setMfaSecret(result.secret);
      setMfaQrUrl(result.otpauthUrl);
    } catch (err) {
      // Error handled by useAuth hook
    }
  };

  const handleMFAVerify = async () => {
    try {
      await verifyMFA(mfaToken);
      setShowMFASetup(false);
      onClose();
    } catch (err) {
      // Error handled by useAuth hook
    }
  };

  // Captcha currently disabled; variables kept for future feature but not used to satisfy strict mode

  if (showMFASetup) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Setup Two-Factor Authentication
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <Alert>
              <Shield className="h-4 w-4" />
              <AlertDescription>
                Scan the QR code below with your authenticator app, then enter the 6-digit code to enable 2FA.
              </AlertDescription>
            </Alert>

            {mfaSecret && mfaQrUrl && (
              <div className="text-center">
                <div className="bg-white p-4 rounded-lg inline-block">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(mfaQrUrl)}`}
                    alt="MFA QR Code"
                    className="w-48 h-48 mx-auto"
                  />
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Or manually enter: <code className="bg-muted px-1 rounded">{mfaSecret}</code>
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="mfa-token">6-Digit Code</Label>
              <Input
                id="mfa-token"
                type="text"
                placeholder="000000"
                value={mfaToken}
                onChange={(e) => setMfaToken(e.target.value)}
                maxLength={6}
              />
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleMFASetup}
                disabled={loading}
                className="flex-1"
              >
                Generate QR Code
              </Button>
              <Button
                onClick={handleMFAVerify}
                disabled={loading || mfaToken.length !== 6}
                className="flex-1"
              >
                Verify & Enable
              </Button>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            {activeTab === 'login' ? 'Sign In' : 'Create Account'}
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'login' | 'register')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">Login</TabsTrigger>
            <TabsTrigger value="register">Register</TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isLoading || loading}>
                {isLoading || loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="register" className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isLoading || loading}>
                {isLoading || loading ? 'Creating account...' : 'Create Account'}
              </Button>
            </form>
          </TabsContent>
        </Tabs>

        {(error || authError) && (
          <Alert variant="destructive">
            <AlertDescription>{error || authError}</AlertDescription>
          </Alert>
        )}
      </DialogContent>
    </Dialog>
  );
}
